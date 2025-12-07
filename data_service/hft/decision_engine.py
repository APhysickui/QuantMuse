"""Interface layer for the QuantMuse C++ high-frequency decision engine.

The dashboard / pipelines work primarily in Python for research-friendly
iteration, but the execution layer described in `IMPROVEMENT_PLAN.md`
requires a low-latency C++ component.  This module loads the shared
library (if available) and exposes a Pythonic API with a safe fallback so
that research workflows stay functional even when the native binary is
missing on a developer laptop.
"""

from __future__ import annotations

import ctypes
import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HFTDecisionResult:
    """Container for high-frequency decision outputs."""

    weights: Dict[str, float]
    latency_ms: Optional[float]
    source: str  # "cpp" or "python-fallback"
    timestamp: Optional[object] = None


class HFTDecisionEngine:
    """Bridge to the native C++ execution/decision module."""

    def __init__(
        self,
        library_paths: Optional[Iterable[str]] = None,
        enabled: bool = True,
        fallback_mix: float = 0.35,
    ) -> None:
        self.enabled = enabled
        self.fallback_mix = fallback_mix
        self._lib = None
        self._decide_fn = None
        self.library_paths = list(library_paths or self._default_paths())
        if self.enabled:
            self._lib = self._load_library()
            self._configure_signature()

    def _default_paths(self) -> Iterable[str]:
        env_path = os.environ.get("QUANTMUSE_HFT_LIB")
        candidates = []
        if env_path:
            candidates.append(env_path)
        candidates.extend(
            [
                "libquantmuse_hft.dylib",
                "libquantmuse_hft.so",
                "quantmuse_hft.dll",
            ]
        )
        return candidates

    def _load_library(self) -> Optional[ctypes.CDLL]:
        for path in self.library_paths:
            try:
                lib = ctypes.CDLL(path)
                logger.info("Loaded QuantMuse HFT engine: %s", path)
                return lib
            except OSError:
                continue
        logger.warning(
            "QuantMuse HFT C++ library not found. "
            "Falling back to Python signal refinement."
        )
        return None

    def _configure_signature(self) -> None:
        if self._lib is None:
            return
        try:
            decide_fn = self._lib.decide_orders
        except AttributeError:
            logger.warning(
                "C++ library missing `decide_orders` symbol. Fallback will be used."
            )
            return

        decide_fn.argtypes = [
            ctypes.POINTER(ctypes.c_double),  # alpha scores
            ctypes.POINTER(ctypes.c_double),  # base weights
            ctypes.c_size_t,  # length
            ctypes.POINTER(ctypes.c_double),  # output weights
        ]
        decide_fn.restype = ctypes.c_int
        self._decide_fn = decide_fn

    def refine_weights(
        self,
        timestamp,
        alpha_vector: Dict[str, float],
        base_weights: Dict[str, float],
        aggressiveness: float = 0.3,
    ) -> HFTDecisionResult:
        """Blend factor-driven weights with HFT refinements."""

        if not self.enabled or not alpha_vector:
            return HFTDecisionResult(
                weights=base_weights,
                latency_ms=None,
                source="python-fallback",
                timestamp=timestamp,
            )

        keys = list(alpha_vector.keys())
        alpha_arr = np.array([float(alpha_vector[k]) for k in keys], dtype=float)
        base_arr = np.array([float(base_weights.get(k, 0.0)) for k in keys], dtype=float)

        start = time.perf_counter()
        used_cpp = False
        refined_arr: Optional[np.ndarray] = None

        if self._decide_fn is not None:
            refined_arr = self._call_cpp(alpha_arr, base_arr)
            used_cpp = refined_arr is not None

        if refined_arr is None:
            refined_arr = self._python_refine(alpha_arr, base_arr, aggressiveness)

        latency_ms = (time.perf_counter() - start) * 1000.0
        weights = {k: float(v) for k, v in zip(keys, refined_arr)}
        return HFTDecisionResult(
            weights=weights,
            latency_ms=latency_ms,
            source="cpp" if used_cpp else "python-fallback",
            timestamp=timestamp,
        )

    def _call_cpp(
        self,
        alpha_arr: np.ndarray,
        base_arr: np.ndarray,
    ) -> Optional[np.ndarray]:
        if self._decide_fn is None:
            return None
        n = len(alpha_arr)
        if n == 0:
            return None
        alpha_c = (ctypes.c_double * n)(*alpha_arr.tolist())
        base_c = (ctypes.c_double * n)(*base_arr.tolist())
        out_c = (ctypes.c_double * n)()
        status = self._decide_fn(alpha_c, base_c, ctypes.c_size_t(n), out_c)
        if status != 0:
            logger.warning("C++ HFT engine returned status %s, fallback engaged.", status)
            return None
        refined = np.ctypeslib.as_array(out_c, shape=(n,)).copy()
        if not np.isfinite(refined).all():
            return None
        norm = np.sum(np.abs(refined))
        if norm > 0:
            refined = refined / norm
        return refined

    def _python_refine(
        self,
        alpha_arr: np.ndarray,
        base_arr: np.ndarray,
        aggressiveness: float,
    ) -> np.ndarray:
        """Fallback: fast numpy logic approximating HFT adjustment."""

        adjusted_alpha = alpha_arr.copy()
        std = adjusted_alpha.std()
        if std > 1e-8:
            adjusted_alpha = (adjusted_alpha - adjusted_alpha.mean()) / (std + 1e-8)
        alpha_norm = np.sum(np.abs(adjusted_alpha)) or 1.0
        adjusted_alpha = adjusted_alpha / alpha_norm

        base_norm = np.sum(np.abs(base_arr)) or 1.0
        base_normalized = base_arr / base_norm

        mix = np.clip(self.fallback_mix + aggressiveness * 0.25, 0.0, 1.0)
        blended = (1.0 - mix) * base_normalized + mix * adjusted_alpha

        norm = np.sum(np.abs(blended)) or 1.0
        return blended / norm

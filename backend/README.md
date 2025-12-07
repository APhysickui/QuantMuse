# QuantMuse C++ Backend (Experimental)

This `backend/` directory contains an **experimental** C++17 trading engine prototype.
It is **not** wired into the main Python `data_service/` pipeline yet and is **not
currently guaranteed to compile or run end‑to‑end**.

## What This Folder Represents

- A low‑latency core engine design:
  - `TradingEngine` main loop (`src/main.cpp`)
  - `Strategy` / `MovingAverageStrategy` (`include/strategy.hpp`, `src/strategy.cpp`)
  - `RiskManager` (`include/risk_manager.hpp`, `src/risk_manager.cpp`)
  - `OrderExecutor` (`include/order_executor.hpp`, `src/order_executor.cpp`)
  - Shared domain types (`include/common/types.hpp`)
- A planned bridge to the Python layer via **pybind11** in `DataLoader`
  (`include/data_loader.hpp`, `src/data_loader.cpp`), intended to call
  `data_service` fetchers from C++.

## Current Status

- The code reflects the **target architecture**, but there are known issues:
  - Header / implementation mismatches (e.g. extra members and methods in
    `RiskManager` implementation that are not declared in the header).
  - Namespace and include inconsistencies in `main.cpp` and `data_loader.hpp`.
  - The pybind11 bridge assumes specific Python interfaces (e.g. methods on
    `YahooFetcher`) that differ from the current Python implementation.
- Unit tests under `backend/tests/` are therefore also **experimental** and
  may not compile without additional fixes.

## How To Treat This Module

- For now, **consider `backend/` as design documentation plus prototype code**, not
  as a production component.
- The main, supported pipeline lives in the Python package `data_service/` and is
  what the FastAPI API and Streamlit dashboard use.

## Suggested Future Work

If you decide to invest in the C++ engine, the recommended order is:

1. **Make it compile cleanly**
   - Add the missing `namespace py = pybind11;` alias to headers that use `py::`.
   - Align `RiskManager` header and implementation (declare `current_prices_` and
     `updateCurrentPrices` or remove them from the implementation).
   - Fix namespace usage in `main.cpp` (use `trading::` qualifiers or a using
     declaration).

2. **Define a clean C++ ↔ Python boundary**
   - Introduce a dedicated Python adapter class rather than calling concrete
     fetchers like `YahooFetcher` directly from C++.
   - Agree on a minimal data structure for passing OHLCV and indicators across
     the boundary.

3. **Only after that, integrate with the Python system**
   - Expose the C++ engine to Python via pybind11 or a thin C API.
   - Let `data_service` choose between the pure‑Python engine and the C++ core
     based on configuration.

Until those steps are done, the safest assumption is: **`backend/` is
experimental and optional. The Python layer is the source of truth.**

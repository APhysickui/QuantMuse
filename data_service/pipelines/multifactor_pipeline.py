"""Multi-factor strategy pipeline using Yahoo Finance data.

This module implements a simple cross-sectional multi-factor strategy
based on:

- Momentum (60d price return)
- Volatility (annualized)
- Market cap
- PE ratio
- ROE

Rebalancing frequency: monthly.

It is designed to be called from the dashboard or API layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd
import logging

from data_service.backtest import BacktestEngine
from data_service.factors import FactorCalculator
from data_service.fetchers import YahooFetcher
from data_service.hft import HFTDecisionEngine

logger = logging.getLogger(__name__)


@dataclass
class MultiFactorConfig:
    """Configuration for multi-factor scoring and backtest."""

    lookback_days: int = 60
    top_n: int = 10
    commission_rate: float = 0.001
    factor_weights: Optional[Dict[str, float]] = None
    slippage_bps: float = 2.0
    impact_coefficient: float = 0.05
    max_position_per_symbol: float = 0.15
    max_portfolio_turnover: float = 0.65
    liquidity_buffer: float = 0.15
    hft_aggressiveness: float = 0.35

    def get_factor_weights(self) -> Dict[str, float]:
        # Default weights if none are provided
        if self.factor_weights is not None:
            return self.factor_weights
        return {
            # price momentum (higher better)
            "momentum_60d": 0.3,
            # PE (lower better => negative weight)
            "pe_ratio": -0.2,
            # ROE (higher better)
            "roe": 0.2,
            # volatility (lower better)
            "price_volatility": -0.15,
            # market cap (中大市值更稳定，这里略偏好大市值)
            "market_cap": 0.15,
        }


def _fetch_price_panel(
    yahoo_fetcher: YahooFetcher,
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
) -> pd.DataFrame:
    """Fetch daily close prices for given symbols from Yahoo.

    Returns
    -------
    price_df: DataFrame
        index = date, columns = symbols, values = close price.
    """

    series_list = []
    for sym in symbols:
        try:
            df = yahoo_fetcher.fetch_historical_data(
                symbol=sym,
                start_time=start_date,
                end_time=end_date,
                interval="1d",
            )
            if df.empty or "close" not in df.columns:
                continue
            s = df["close"].rename(sym)
            series_list.append(s)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch data for %s: %s", sym, exc)
            continue

    if not series_list:
        return pd.DataFrame()

    price_df = pd.concat(series_list, axis=1).dropna(how="all")
    # 丢掉全部为 NaN 的列
    price_df = price_df.dropna(axis=1, how="all")
    return price_df


def _fetch_fundamentals(
    yahoo_fetcher: YahooFetcher,
    symbols: List[str],
) -> Dict[str, Dict[str, float]]:
    """Fetch simple fundamental data (market_cap, PE, ROE) from Yahoo.

    Returns a mapping: symbol -> { 'market_cap': ..., 'pe_ratio': ..., 'roe': ... }
    """

    info_map: Dict[str, Dict[str, float]] = {}

    for sym in symbols:
        try:
            info = yahoo_fetcher.get_company_info(sym)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch company info for %s: %s", sym, exc)
            continue

        fundamentals: Dict[str, float] = {}
        if info is None:
            continue

        mc = info.get("market_cap")
        if mc is not None:
            fundamentals["market_cap"] = float(mc)

        pe = info.get("pe_ratio")
        if pe is not None:
            fundamentals["pe_ratio"] = float(pe)

        # yfinance 里 ROE 有时在 returnOnEquity 字段，get_company_info 没直接给，但预留一下
        roe = info.get("roe")
        if roe is not None:
            fundamentals["roe"] = float(roe)

        if fundamentals:
            info_map[sym] = fundamentals

    return info_map


def run_multifactor_strategy(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    initial_capital: float,
    yahoo_fetcher: YahooFetcher,
    factor_calculator: Optional[FactorCalculator],
    backtest_engine: BacktestEngine,
    config: Optional[MultiFactorConfig] = None,
    hft_engine: Optional[HFTDecisionEngine] = None,
) -> Dict[str, Any]:
    """Run a cross-sectional multi-factor strategy with monthly rebalancing.

    Parameters
    ----------
    symbols : list of str
        Candidate symbols.
    start_date, end_date : datetime
        Backtest period.
    initial_capital : float
        Initial portfolio value.
    yahoo_fetcher : YahooFetcher
        Data source for prices & fundamentals.
    factor_calculator : FactorCalculator or None
        Currently not heavily used; placeholder for future extension.
    backtest_engine : BacktestEngine
        Used only for its initial_capital / commission configuration; core
        portfolio logic is implemented here directly for simplicity.
    config : MultiFactorConfig, optional
        Factor weights, lookback window, top_n etc.

    Returns
    -------
    Dict[str, Any]
        Keys compatible with dashboard: 'total_return', 'sharpe_ratio',
        'max_drawdown', 'win_rate', 'total_trades', 'equity_curve',
        plus 'selected_symbols' and 'factor_scores'.
    """

    if config is None:
        config = MultiFactorConfig()

    # 统一处理日期（Streamlit 可能给 date 对象）
    if not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())

    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")

    # 1) 获取价格数据
    price_df = _fetch_price_panel(yahoo_fetcher, symbols, start_date, end_date)
    if price_df.empty or price_df.shape[1] == 0:
        logger.warning("No price data available for multi-factor strategy")
        return {}

    # 保证有足够的数据来计算动量
    if len(price_df) <= config.lookback_days + 5:
        logger.warning("Not enough history for lookback=%d", config.lookback_days)
        return {}

    # 2) 获取简单基本面数据
    fundamentals = _fetch_fundamentals(yahoo_fetcher, list(price_df.columns))

    # 3) 计算日收益
    returns = price_df.pct_change().dropna()

    # 4) 以每月第一个交易日作为调仓日
    monthly_first = price_df.resample("M").first().index
    rebal_dates = [d for d in monthly_first if d in returns.index]
    if len(rebal_dates) == 0:
        logger.warning("No monthly rebalancing dates found in given period")
        return {}

    factor_weights = config.get_factor_weights()
    factor_snapshots: List[Dict[str, Any]] = []
    ic_records: List[Dict[str, float]] = []
    hft_orders: List[Dict[str, Any]] = []
    hft_latency_ms: List[float] = []
    hft_cpp_hits = 0

    # 每个调仓日上的权重矩阵
    weights = pd.DataFrame(0.0, index=returns.index, columns=returns.columns)

    for d in rebal_dates:
        loc = returns.index.get_loc(d)
        start_loc = loc - config.lookback_days
        if start_loc <= 0:
            continue

        window_prices = price_df.iloc[start_loc:loc]
        window_returns = returns.iloc[start_loc:loc]

        # 动量：过去 lookback_days 收益
        momentum = (window_prices.iloc[-1] / window_prices.iloc[0] - 1.0) * 100.0

        # 波动率：年化
        vol = window_returns.std() * np.sqrt(252.0) * 100.0

        # 取当前截面可用的 symbol
        available_syms = window_prices.columns

        # 构造因子矩阵：index = symbol, columns = factor names
        factor_mat = pd.DataFrame(index=available_syms)
        factor_mat["momentum_60d"] = momentum.reindex(available_syms)
        factor_mat["price_volatility"] = vol.reindex(available_syms)

        # 加入基本面因子
        mc_list = []
        pe_list = []
        roe_list = []
        for sym in available_syms:
            info = fundamentals.get(sym, {})
            mc_list.append(info.get("market_cap", np.nan))
            pe_list.append(info.get("pe_ratio", np.nan))
            roe_list.append(info.get("roe", np.nan))
        factor_mat["market_cap"] = mc_list
        factor_mat["pe_ratio"] = pe_list
        factor_mat["roe"] = roe_list

        # 对每个因子做 z-score 标准化
        z_mat = pd.DataFrame(index=factor_mat.index)
        for name in factor_weights.keys():
            if name not in factor_mat.columns:
                continue
            col = factor_mat[name].astype(float)
            if col.notna().sum() < 3:
                z_mat[name] = 0.0
                continue
            mean = col.mean()
            std = col.std(ddof=0)
            if std <= 0:
                z_mat[name] = 0.0
            else:
                z_mat[name] = (col - mean) / std

        if z_mat.empty:
            continue

        # 按权重组合因子得分
        score = pd.Series(0.0, index=z_mat.index)
        for fname, w in factor_weights.items():
            if fname in z_mat.columns:
                score = score.add(w * z_mat[fname].fillna(0.0), fill_value=0.0)

        score = score.replace([np.inf, -np.inf], np.nan).dropna()
        if score.empty:
            continue

        ranked = score.sort_values(ascending=False)
        top_n = min(config.top_n, len(ranked))
        selected = ranked.head(top_n).index

        factor_snapshots.append(
            {
                "date": d,
                "selected": list(selected),
                "scores": ranked.to_dict(),
            }
        )

        # 记录等权重并加入持仓和流动性限制
        w = pd.Series(0.0, index=returns.columns)
        if len(selected) > 0:
            max_weight = min(config.max_position_per_symbol, 1.0)
            base_weight = min(1.0 / len(selected), max_weight)
            w.loc[selected] = base_weight
            if w.sum() > 0:
                w = w / w.sum()
            w = w * (1.0 - config.liquidity_buffer)

        # 可选：调用 C++ 高频决策模块优化权重
        if hft_engine is not None and len(ranked) > 0:
            decision = hft_engine.refine_weights(
                timestamp=d.to_pydatetime() if hasattr(d, "to_pydatetime") else d,
                alpha_vector=ranked.to_dict(),
                base_weights=w.to_dict(),
                aggressiveness=config.hft_aggressiveness,
            )
            refined = pd.Series(decision.weights).reindex(w.index).fillna(0.0)
            if refined.abs().sum() > 0:
                refined = refined / refined.abs().sum()
            w = refined
            if decision.latency_ms is not None:
                hft_latency_ms.append(decision.latency_ms)
            if decision.source == "cpp":
                hft_cpp_hits += 1
            top_preview = refined.sort_values(ascending=False).head(3).to_dict()
            hft_orders.append(
                {
                    "timestamp": decision.timestamp or d,
                    "engine": decision.source,
                    "latency_ms": decision.latency_ms,
                    "top_symbols": {sym: float(val) for sym, val in top_preview.items()},
                }
            )

        # 记录 IC
        future_horizon = max(5, config.lookback_days // 3)
        future_end = min(len(returns), loc + future_horizon)
        if future_end - loc >= 5:
            future_ret = (1.0 + returns.iloc[loc:future_end]).prod() - 1.0
            future_ret = future_ret.reindex(ranked.index).dropna()
            if not future_ret.empty:
                aligned = pd.DataFrame(
                    {"score": ranked.reindex(future_ret.index), "future_return": future_ret}
                ).dropna()
                if len(aligned) >= 3:
                    ic = aligned["score"].corr(aligned["future_return"], method="spearman")
                    if ic is not None and not np.isnan(ic):
                        ic_records.append({"date": d, "ic": float(ic)})

        weights.loc[d] = w

    # 如果所有调仓日都没有选出权重，直接返回空
    if (weights.sum(axis=1) == 0).all():
        logger.warning("No non-zero weights generated in multi-factor strategy")
        return {}

    # 将权重向前填充，代表持仓直到下一次调仓
    weights = weights.sort_index().ffill().shift(1).fillna(0.0)

    # 计算组合收益（扣除交易成本与冲击）
    gross_ret = (weights * returns).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1).clip(upper=config.max_portfolio_turnover)
    trading_cost = (
        config.commission_rate * turnover
        + (config.slippage_bps / 10000.0) * turnover
        + config.impact_coefficient * (turnover**2)
    )
    port_ret = gross_ret - trading_cost

    # 用 BacktestEngine 的初始资金配置
    backtest_engine.initial_capital = float(initial_capital)
    backtest_engine.commission_rate = float(config.commission_rate)

    equity = initial_capital * (1.0 + port_ret).cumprod()
    equity_df = pd.DataFrame({"equity": equity})

    if equity_df.empty:
        return {}

    # 绩效指标
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    days = (equity_df.index[-1] - equity_df.index[0]).days or 1
    annualized_return = (1.0 + total_return) ** (365.0 / days) - 1.0
    vol = float(port_ret.std() * np.sqrt(252.0)) if len(port_ret) > 1 else 0.0
    sharpe_ratio = float(annualized_return / vol) if vol > 0 else 0.0

    peak = equity_df["equity"].cummax()
    drawdown = (equity_df["equity"] - peak) / peak
    max_drawdown = float(drawdown.min())

    win_rate = float((port_ret > 0).mean()) if len(port_ret) > 0 else 0.0

    # 近似交易次数: 每次调仓买入+卖出
    num_rebals = int((weights.diff().abs().sum(axis=1) > 1e-6).sum())
    total_trades = int(num_rebals * config.top_n * 2)

    # 记录最后一次调仓的因子得分，方便前端展示
    nonzero_idx = weights.index[weights.sum(axis=1) > 0]
    last_selected: List[str] = []
    if len(nonzero_idx) > 0:
        last_nonzero_date = nonzero_idx.max()
        last_weights = weights.loc[last_nonzero_date]
        last_selected = list(last_weights[last_weights > 0].index)

    # 简单返回得分信息: 此处只返回最后一次的 score（用 price_df 的最后窗口再算一次即可）
    factor_score_map: Dict[str, float] = {}
    try:
        # 末尾窗口用于展示（不影响回测结果）
        window_prices = price_df.iloc[-config.lookback_days - 1 :]
        window_returns = window_prices.pct_change().dropna()
        momentum = (window_prices.iloc[-1] / window_prices.iloc[0] - 1.0) * 100.0
        vol_last = window_returns.std() * np.sqrt(252.0) * 100.0

        factor_mat_last = pd.DataFrame(index=price_df.columns)
        factor_mat_last["momentum_60d"] = momentum
        factor_mat_last["price_volatility"] = vol_last
        mc_list = []
        pe_list = []
        roe_list = []
        for sym in price_df.columns:
            info = fundamentals.get(sym, {})
            mc_list.append(info.get("market_cap", np.nan))
            pe_list.append(info.get("pe_ratio", np.nan))
            roe_list.append(info.get("roe", np.nan))
        factor_mat_last["market_cap"] = mc_list
        factor_mat_last["pe_ratio"] = pe_list
        factor_mat_last["roe"] = roe_list

        z_last = pd.DataFrame(index=factor_mat_last.index)
        for name in factor_weights.keys():
            if name not in factor_mat_last.columns:
                continue
            col = factor_mat_last[name].astype(float)
            if col.notna().sum() < 3:
                z_last[name] = 0.0
                continue
            mean = col.mean()
            std = col.std(ddof=0)
            if std <= 0:
                z_last[name] = 0.0
            else:
                z_last[name] = (col - mean) / std

        score_last = pd.Series(0.0, index=z_last.index)
        for fname, w in factor_weights.items():
            if fname in z_last.columns:
                score_last = score_last.add(w * z_last[fname].fillna(0.0), fill_value=0.0)

        factor_score_map = score_last.to_dict()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to compute final factor scores snapshot: %s", exc)

    ic_series = (
        pd.Series({rec["date"]: rec["ic"] for rec in ic_records}).sort_index()
        if ic_records
        else pd.Series(dtype=float)
    )
    factor_metrics = {
        "ic_mean": float(ic_series.mean()) if not ic_series.empty else None,
        "ic_ir": float(ic_series.mean() / ic_series.std(ddof=0) * np.sqrt(12.0))
        if not ic_series.empty and ic_series.std(ddof=0) > 0
        else None,
        "samples": int(len(ic_series)),
        "ic_series": ic_series,
        "factor_snapshots": factor_snapshots[-5:],
    }

    decision_info: Optional[Dict[str, Any]] = None
    if hft_orders:
        valid_latency = [lat for lat in hft_latency_ms if lat is not None]
        latency_series = pd.Series(valid_latency) if valid_latency else pd.Series(dtype=float)
        decision_info = {
            "orders": hft_orders,
            "latency_ms_avg": float(latency_series.mean()) if not latency_series.empty else None,
            "latency_ms_p95": float(latency_series.quantile(0.95)) if len(latency_series) > 1 else None,
            "cpp_hit_ratio": float(hft_cpp_hits / len(hft_orders)),
        }

    return {
        "total_return": total_return,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "equity_curve": equity_df,
        "last_selected_symbols": last_selected,
        "factor_scores": factor_score_map,
        "factor_weights": factor_weights,
        "factor_metrics": factor_metrics,
        "decision_engine": decision_info,
    }

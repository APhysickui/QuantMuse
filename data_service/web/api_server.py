#!/usr/bin/env python3
"""
FastAPI Web Server for Trading System
Provides RESTful API endpoints for web management interface
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn
import logging
from datetime import datetime, timedelta
import asyncio
import json
import pandas as pd

# Import our trading system modules
try:
    from ..backtest import BacktestEngine, PerformanceAnalyzer
    from ..factors import FactorCalculator, FactorScreener, FactorBacktest
    from ..strategies import StrategyRegistry
    from ..ai import LLMIntegration, NLPProcessor, SentimentFactorCalculator
    from ..fetchers import YahooFetcher, BinanceFetcher
    from ..storage import DatabaseManager
    from ..utils import Logger
except ImportError as e:
    logging.error(f"Failed to import trading modules: {e}")

# Pydantic models for API requests/responses
class StrategyRequest(BaseModel):
    strategy_name: str
    symbols: List[str]
    parameters: Dict[str, Any]
    start_date: str
    end_date: str
    initial_capital: float = 100000.0

class BacktestRequest(BaseModel):
    strategy_config: StrategyRequest
    commission_rate: float = 0.001
    rebalance_frequency: str = "daily"

class FactorAnalysisRequest(BaseModel):
    symbols: List[str]
    factors: List[str]
    start_date: str
    end_date: str

class AIAnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "sentiment"  # sentiment, news, market_analysis

class SystemStatusResponse(BaseModel):
    status: str
    uptime: str
    active_strategies: int
    total_trades: int
    system_metrics: Dict[str, Any]

class APIServer:
    """FastAPI server for trading system web interface"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="Trading System API",
            description="RESTful API for trading system management",
            version="1.0.0"
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize trading system components
        self._initialize_components()
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify actual origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Mount static files for frontend
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    def _initialize_components(self):
        """Initialize trading system components"""
        # Core quantitative components
        try:
            self.backtest_engine = BacktestEngine()
            self.performance_analyzer = PerformanceAnalyzer()
            self.factor_calculator = FactorCalculator()
            self.factor_screener = FactorScreener()
            self.factor_backtest = FactorBacktest()
            self.strategy_registry = StrategyRegistry()
            self.yahoo_fetcher = YahooFetcher()
            self.binance_fetcher = BinanceFetcher()
            self.db_manager = DatabaseManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {e}")
            return

        # Optional AI / NLP components
        self.llm_integration = None
        self.nlp_processor = None
        self.sentiment_calculator = None
        try:
            self.llm_integration = LLMIntegration()
            self.nlp_processor = NLPProcessor()
            self.sentiment_calculator = SentimentFactorCalculator()
        except Exception as e:
            self.logger.warning(f"AI components not fully initialized: {e}")

        self.logger.info("Trading system components initialized successfully")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve the main dashboard page"""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Trading System Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdn.jsdelivr.net/npm/boxicons@2.0.7/css/boxicons.min.css" rel="stylesheet">
            </head>
            <body>
                <div id="app"></div>
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
                <script src="/static/js/app.js"></script>
            </body>
            </html>
            """
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/system/status")
        async def get_system_status():
            """Get system status and metrics"""
            try:
                # Get system metrics
                metrics = {
                    "cpu_usage": 45.2,
                    "memory_usage": 2.3,
                    "active_connections": 12,
                    "api_calls_per_min": 156
                }
                
                return SystemStatusResponse(
                    status="running",
                    uptime="2 days, 5 hours, 30 minutes",
                    active_strategies=3,
                    total_trades=1250,
                    system_metrics=metrics
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/strategies")
        async def get_available_strategies():
            """Get list of available strategies"""
            try:
                strategies = [
                    {"name": "Momentum Strategy", "description": "Price momentum based strategy"},
                    {"name": "Value Strategy", "description": "Value investing strategy"},
                    {"name": "Mean Reversion", "description": "Mean reversion strategy"},
                    {"name": "Multi-Factor", "description": "Multi-factor strategy"},
                    {"name": "Risk Parity", "description": "Risk parity strategy"},
                    {"name": "Sector Rotation", "description": "Sector rotation strategy"}
                ]
                return {"strategies": strategies}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/backtest/run")
        async def run_backtest(request: BacktestRequest):
            """Run strategy backtest using Yahoo Finance data and BacktestEngine"""
            try:
                cfg = request.strategy_config
                symbols = cfg.symbols
                self.logger.info(f"Running backtest for strategy: {cfg.strategy_name} on {symbols}")

                # Parse dates
                start_date = datetime.fromisoformat(cfg.start_date)
                end_date = datetime.fromisoformat(cfg.end_date)

                # Fetch historical data for each symbol
                price_series = []
                for sym in symbols:
                    df = self.yahoo_fetcher.fetch_historical_data(
                        symbol=sym,
                        start_time=start_date,
                        end_time=end_date,
                        interval='1d',
                    )
                    if df.empty or 'close' not in df.columns:
                        continue
                    series = df['close'].rename(sym)
                    price_series.append(series)

                if not price_series:
                    raise ValueError("No historical data available for requested symbols")

                price_df = pd.concat(price_series, axis=1).dropna()

                # Configure backtest engine
                self.backtest_engine.initial_capital = float(cfg.initial_capital)
                self.backtest_engine.commission_rate = float(request.commission_rate)

                def strategy_func(data: pd.DataFrame, engine, symbols_param):
                    """Simple equal-weight buy & hold strategy for demo purposes"""
                    if data.empty:
                        return
                    symbols_local = [s for s in symbols_param if s in data.columns]
                    if not symbols_local:
                        return

                    first_idx = data.index[0]
                    last_idx = data.index[-1]
                    first_ts = first_idx.to_pydatetime() if hasattr(first_idx, 'to_pydatetime') else first_idx
                    last_ts = last_idx.to_pydatetime() if hasattr(last_idx, 'to_pydatetime') else last_idx

                    n = len(symbols_local)
                    capital_per_symbol = engine.initial_capital / n
                    first_row = data.iloc[0]

                    # Buy equally-weighted portfolio on first day
                    for sym in symbols_local:
                        price = float(first_row[sym])
                        if price <= 0:
                            continue
                        qty = capital_per_symbol / price
                        engine.place_order(sym, 'buy', qty, price, first_ts)

                    # Sell everything on last day
                    last_row = data.iloc[-1]
                    for sym in symbols_local:
                        pos = engine.positions.get(sym)
                        if not pos or pos.quantity <= 0:
                            continue
                        price = float(last_row[sym])
                        engine.place_order(sym, 'sell', pos.quantity, price, last_ts)

                results = self.backtest_engine.run_backtest(
                    price_df,
                    strategy_func,
                    {'symbols_param': symbols},
                )

                equity_curve = results.get('equity_curve')
                equity_payload = []
                if isinstance(equity_curve, pd.DataFrame) and not equity_curve.empty:
                    for ts, row in equity_curve.iterrows():
                        equity_payload.append({
                            'date': ts.strftime('%Y-%m-%d'),
                            'value': float(row['total_value']),
                        })

                payload = {
                    'strategy_name': cfg.strategy_name,
                    'symbols': symbols,
                    'total_return': results.get('total_return', 0.0),
                    'annualized_return': results.get('annualized_return', 0.0),
                    'sharpe_ratio': results.get('sharpe_ratio', 0.0),
                    'max_drawdown': results.get('max_drawdown', 0.0),
                    'win_rate': results.get('win_rate', 0.0),
                    'total_trades': results.get('total_trades', 0),
                    'equity_curve': equity_payload,
                }

                return {"status": "success", "results": payload}

            except Exception as e:
                self.logger.error(f"Backtest failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/factors/analyze")
        async def analyze_factors(request: FactorAnalysisRequest):
            """Analyze factor performance"""
            try:
                self.logger.info(f"Analyzing factors: {request.factors}")
                
                # Generate sample factor analysis results
                results = {
                    "factors": request.factors,
                    "performance": {
                        "momentum": {"ic": 0.15, "ir": 1.2, "win_rate": 0.58},
                        "value": {"ic": 0.12, "ir": 1.0, "win_rate": 0.52},
                        "quality": {"ic": 0.10, "ir": 0.8, "win_rate": 0.48}
                    },
                    "correlation_matrix": [
                        [1.0, 0.2, 0.1],
                        [0.2, 1.0, 0.3],
                        [0.1, 0.3, 1.0]
                    ]
                }
                
                return {"status": "success", "results": results}
                
            except Exception as e:
                self.logger.error(f"Factor analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/ai/analyze")
        async def analyze_with_ai(request: AIAnalysisRequest):
            """Analyze text using AI"""
            try:
                self.logger.info(f"AI analysis request: {request.analysis_type}")
                
                if request.analysis_type == "sentiment":
                    # Use NLP processor for sentiment analysis
                    processed = self.nlp_processor.preprocess_text(request.text)
                    result = {
                        "sentiment": processed.sentiment_label,
                        "confidence": processed.sentiment_score,
                        "keywords": processed.keywords[:5],
                        "topics": processed.topics
                    }
                else:
                    # Use LLM for other analysis types
                    result = {
                        "analysis": "AI analysis result",
                        "confidence": 0.85,
                        "recommendations": ["Sample recommendation 1", "Sample recommendation 2"]
                    }
                
                return {"status": "success", "results": result}
                
            except Exception as e:
                self.logger.error(f"AI analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/market/data/{symbol}")
        async def get_market_data(symbol: str, period: str = "1y"):
            """Get market data for symbol using Yahoo Finance when possible"""
            try:
                # Map simple period strings to days
                period_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365}
                days = period_map.get(period, 365)
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=days)

                try:
                    df = self.yahoo_fetcher.fetch_historical_data(
                        symbol=symbol,
                        start_time=start_dt,
                        end_time=end_dt,
                        interval='1d',
                    )
                    if df.empty:
                        raise ValueError("Empty data")
                    data = [
                        {"date": idx.strftime('%Y-%m-%d'), "price": float(row['close'])}
                        for idx, row in df.iterrows()
                    ]
                except Exception:
                    # Fallback to simple synthetic series if live data fails
                    dates = []
                    prices = []
                    current_date = end_dt - timedelta(days=days)
                    for i in range(min(days, 252)):
                        dates.append(current_date.strftime('%Y-%m-%d'))
                        prices.append(100 + i * 0.1 + (i % 10) * 0.5)
                        current_date += timedelta(days=1)
                    data = [
                        {"date": d, "price": p}
                        for d, p in zip(dates, prices)
                    ]

                return {"symbol": symbol, "data": data}

            except Exception as e:
                self.logger.error(f"Failed to get market data: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/portfolio/status")
        async def get_portfolio_status():
            """Get current portfolio status"""
            try:
                return {
                    "total_value": 125000.0,
                    "cash": 25000.0,
                    "positions": [
                        {"symbol": "AAPL", "quantity": 100, "value": 15000.0, "pnl": 1500.0},
                        {"symbol": "GOOGL", "quantity": 50, "value": 5000.0, "pnl": 500.0},
                        {"symbol": "MSFT", "quantity": 75, "value": 20000.0, "pnl": 2000.0}
                    ],
                    "daily_pnl": 1250.0,
                    "total_pnl": 4000.0
                }
                
            except Exception as e:
                self.logger.error(f"Failed to get portfolio status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/trades/recent")
        async def get_recent_trades(limit: int = 20):
            """Get recent trades"""
            try:
                # Generate sample trade data
                trades = []
                for i in range(limit):
                    trades.append({
                        "id": f"trade_{i}",
                        "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                        "symbol": ["AAPL", "GOOGL", "MSFT"][i % 3],
                        "side": "buy" if i % 2 == 0 else "sell",
                        "quantity": 100 + i * 10,
                        "price": 150.0 + i * 0.5,
                        "status": "filled"
                    })
                
                return {"trades": trades}
                
            except Exception as e:
                self.logger.error(f"Failed to get recent trades: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self, debug: bool = False):
        """Run the FastAPI server"""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=debug,
            log_level="info"
        )

def main():
    """Main function to run the API server"""
    server = APIServer()
    server.run(debug=True)

if __name__ == "__main__":
    main() 
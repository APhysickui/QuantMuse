#!/usr/bin/env python3
"""
Trading System Dashboard
A comprehensive Streamlit dashboard for trading system visualization
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from data_service.backtest import BacktestEngine, PerformanceAnalyzer
    from data_service.factors import FactorCalculator, FactorBacktest
    from data_service.strategies import StrategyRegistry
    from data_service.ai import NLPProcessor, SentimentFactorCalculator
    # 使用绝对导入路径
    from data_service.fetchers import YahooFetcher
    from data_service.pipelines.multifactor_pipeline import run_multifactor_strategy
    from data_service.dashboard.charts import ChartGenerator
    from data_service.dashboard.widgets import DashboardWidgets
    from data_service.hft import HFTDecisionEngine
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.info("Please install required dependencies: pip install -e .[ai,visualization]")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingDashboard:
    """Main trading dashboard application"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator()
        self.widgets = DashboardWidgets()
        self.performance_analyzer = PerformanceAnalyzer()
        self.backtest_engine = BacktestEngine()
        self.factor_calculator = FactorCalculator()
        self.factor_backtest = FactorBacktest()
        self.nlp_processor = NLPProcessor()
        self.sentiment_calculator = SentimentFactorCalculator()
        self.yahoo_fetcher = YahooFetcher()
        self.hft_engine = HFTDecisionEngine()
        # 默认语言为中文, 可在侧边栏切换
        self.lang = 'zh'
        self.translations = {
            'header_title': {'zh': '量化交易看板', 'en': 'Trading System Dashboard'},
            'tab_performance': {'zh': '绩效分析', 'en': 'Performance Analysis'},
            'tab_backtest': {'zh': '策略回测', 'en': 'Strategy Backtest'},
            'tab_market': {'zh': '市场数据', 'en': 'Market Data'},
            'tab_ai': {'zh': 'AI 分析', 'en': 'AI Analysis'},
            'tab_system': {'zh': '系统状态', 'en': 'System Status'},
            'sidebar_title': {'zh': '控制面板', 'en': 'Dashboard Controls'},
            'date_range': {'zh': '日期范围', 'en': 'Date Range'},
            'start_date': {'zh': '开始日期', 'en': 'Start Date'},
            'end_date': {'zh': '结束日期', 'en': 'End Date'},
            'strategy': {'zh': '策略', 'en': 'Strategy'},
            'symbols': {'zh': '标的', 'en': 'Symbols'},
            'market': {'zh': '市场', 'en': 'Market'},
            'capital': {'zh': '初始资金', 'en': 'Initial Capital ($)'},
        }
        
    def _t(self, key):
        """Simple i18n helper"""
        return self.translations.get(key, {}).get(self.lang, key)


    def run(self):
        """Run the dashboard application"""
        st.set_page_config(
            page_title="Trading System Dashboard",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.6rem;
            color: #ffffff;
            text-align: center;
            margin-bottom: 2rem;
            padding: 1.2rem;
            border-radius: 0.75rem;
            background: linear-gradient(90deg, #1f77b4 0%, #0d6efd 50%, #6610f2 100%);
        }
        .metric-card {
            background-color: #ffffff;
            padding: 1rem 1.2rem;
            border-radius: 0.75rem;
            box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(15, 23, 42, 0.06);
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fb;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown(f'<h1 class="main-header">📈 {self._t("header_title")}</h1>', unsafe_allow_html=True)
        
        # Sidebar
        self._create_sidebar()
        
        # Main content
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 " + self._t('tab_performance'),
            "🎯 " + self._t('tab_backtest'),
            "📈 " + self._t('tab_market'),
            "🤖 " + self._t('tab_ai'),
            "⚙️ " + self._t('tab_system'),
        ])

        with tab1:
            self._show_performance_analysis()
        
        with tab2:
            self._show_strategy_backtest()
        
        with tab3:
            self._show_market_data()
        
        with tab4:
            self._show_ai_analysis()
        
        with tab5:
            self._show_system_status()
    
    def _create_sidebar(self):
        """Create sidebar with controls"""
        # Language switch
        lang_choice = st.sidebar.radio("Language / 语言", ["中文", "English"], index=0)
        self.lang = 'zh' if lang_choice == "中文" else 'en'
        st.session_state['lang'] = self.lang

        st.sidebar.title("🎛️ " + self._t('sidebar_title'))

        # Date range selector
        st.sidebar.subheader("📅 " + self._t('date_range'))
        start_date = st.sidebar.date_input(
            self._t('start_date'),
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now(),
        )
        end_date = st.sidebar.date_input(
            self._t('end_date'),
            value=datetime.now(),
            max_value=datetime.now(),
        )

        # Market selector
        st.sidebar.subheader("🌍 " + self._t('market'))
        market_options = {
            'US Tech': ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"],
            'US Index/ETF': ["SPY", "QQQ", "DIA", "IWM", "XLK", "XLF", "XLE"],
            'HK': ["0700.HK", "0939.HK", "1299.HK", "1398.HK"],
            'CN A-shares': ["600519.SS", "601318.SS", "600036.SS"],
        }
        market = st.sidebar.selectbox("Market", list(market_options.keys()))
        available_symbols = market_options.get(market, market_options['US Tech'])

        # Strategy selector
        st.sidebar.subheader("🎯 " + self._t('strategy'))
        strategy_options = ["Momentum Strategy", "Value Strategy", "Mean Reversion", "Custom"]
        selected_strategy = st.sidebar.selectbox("Select Strategy", strategy_options)

        # Symbols selector
        st.sidebar.subheader("📈 " + self._t('symbols'))
        symbols = st.sidebar.multiselect(
            "Select Symbols",
            available_symbols,
            default=available_symbols[:3],
        )

        # Initial capital
        st.sidebar.subheader("💰 " + self._t('capital'))
        initial_capital = st.sidebar.number_input(
            self._t('capital'),
            min_value=1000,
            max_value=1000000,
            value=100000,
            step=10000,
        )

        # Store in session state
        st.session_state.update({
            'start_date': start_date,
            'end_date': end_date,
            'selected_strategy': selected_strategy,
            'symbols': symbols,
            'initial_capital': initial_capital,
        })
    
    def _show_performance_analysis(self):
        """Show performance analysis tab"""
        lang = getattr(self, 'lang', 'zh')
        header = "📊 绩效分析" if lang == 'zh' else "📊 Performance Analysis"
        st.header(header)
        
        # Generate sample data for demonstration
        sample_data = self._generate_sample_performance_data()
        
        # Labels
        if lang == 'zh':
            label_tr = "总收益"
            label_sr = "夏普比率"
            label_dd = "最大回撤"
            label_wr = "胜率"
            table_title = "📋 详细绩效指标"
        else:
            label_tr = "Total Return"
            label_sr = "Sharpe Ratio"
            label_dd = "Max Drawdown"
            label_wr = "Win Rate"
            table_title = "📋 Detailed Performance Metrics"
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label_tr,
                f"{sample_data['total_return']:.2%}",
                f"{sample_data['total_return_delta']:+.2%}"
            )
        
        with col2:
            st.metric(
                label_sr,
                f"{sample_data['sharpe_ratio']:.2f}",
                f"{sample_data['sharpe_delta']:+.2f}"
            )
        
        with col3:
            st.metric(
                label_dd,
                f"{sample_data['max_drawdown']:.2%}",
                f"{sample_data['drawdown_delta']:+.2%}"
            )
        
        with col4:
            st.metric(
                label_wr,
                f"{sample_data['win_rate']:.1%}",
                f"{sample_data['win_rate_delta']:+.1%}"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Equity Curve")
            equity_fig = self.chart_generator.create_equity_curve(sample_data['equity_data'])
            st.plotly_chart(equity_fig, use_container_width=True)
        
        with col2:
            st.subheader("📉 Drawdown Analysis")
            drawdown_fig = self.chart_generator.create_drawdown_chart(sample_data['drawdown_data'])
            st.plotly_chart(drawdown_fig, use_container_width=True)
        
        # Additional charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Returns Distribution")
            returns_fig = self.chart_generator.create_returns_distribution(sample_data['returns'])
            st.plotly_chart(returns_fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Rolling Metrics")
            rolling_fig = self.chart_generator.create_rolling_metrics(sample_data['returns'])
            st.plotly_chart(rolling_fig, use_container_width=True)
        
        # Performance table
        st.subheader(table_title)
        metrics_df = pd.DataFrame([
            [label_tr, f"{sample_data['total_return']:.2%}"],
            ["Annualized Return", f"{sample_data['annualized_return']:.2%}"],
            ["Volatility", f"{sample_data['volatility']:.2%}"],
            [label_sr, f"{sample_data['sharpe_ratio']:.2f}"],
            ["Sortino Ratio", f"{sample_data['sortino_ratio']:.2f}"],
            [label_dd, f"{sample_data['max_drawdown']:.2%}"],
            ["Calmar Ratio", f"{sample_data['calmar_ratio']:.2f}"],
            [label_wr, f"{sample_data['win_rate']:.1%}"],
            ["Profit Factor", f"{sample_data['profit_factor']:.2f}"],
            ["Total Trades", str(sample_data['total_trades'])],
        ], columns=["Metric", "Value"])
        
        st.dataframe(metrics_df, use_container_width=True)
    
    def _show_strategy_backtest(self):
        """Show strategy backtest tab"""
        st.header("🎯 Strategy Backtest")

        # Read shared settings from sidebar
        symbols = st.session_state.get('symbols', ["AAPL", "GOOGL", "MSFT"])
        start_date = st.session_state.get('start_date', datetime.now() - timedelta(days=365))
        end_date = st.session_state.get('end_date', datetime.now())
        initial_capital = st.session_state.get('initial_capital', 100000)

        # Strategy configuration
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⚙️ Strategy Parameters")

            strategy_type = st.selectbox(
                "Strategy Type",
                [
                    "Buy & Hold",
                    "Simple Momentum",
                    "Simple Mean Reversion",
                    "Hybrid Multi-Factor (Python + C++ HFT)",
                ],
            )

            # Parameters for momentum / mean reversion
            lookback_days = 60
            top_n = 3
            if strategy_type in (
                "Simple Momentum",
                "Simple Mean Reversion",
                "Hybrid Multi-Factor (Python + C++ HFT)",
            ):
                lookback_days = st.slider("Lookback Window (days)", 20, 252, 60, 5)
                top_n = st.slider("Top N symbols", 1, max(1, len(symbols) or 1), min(10, max(1, len(symbols) or 1)))

            # Factor weights for multi-factor strategy
            factor_weights = None
            if strategy_type == "Hybrid Multi-Factor (Python + C++ HFT)":
                st.markdown(
                    "Adjust factor weights (positive = prefer high, negative = prefer low). "
                    "C++ 高频模块会在此基础上进行毫秒级决策优化。"
                )
                w_mom = st.slider("Momentum (60d) weight", -1.0, 1.0, 0.3, 0.05)
                w_vol = st.slider("Volatility weight", -1.0, 1.0, -0.15, 0.05)
                w_mc = st.slider("Market Cap weight", -1.0, 1.0, 0.15, 0.05)
                w_pe = st.slider("PE ratio weight", -1.0, 1.0, -0.2, 0.05)
                w_roe = st.slider("ROE weight", -1.0, 1.0, 0.2, 0.05)
                factor_weights = {
                    'momentum_60d': w_mom,
                    'price_volatility': w_vol,
                    'market_cap': w_mc,
                    'pe_ratio': w_pe,
                    'roe': w_roe,
                }

        with col2:
            st.subheader("📊 Backtest Settings")

            # Commission rate
            commission_rate = st.slider("Commission Rate (%)", 0.0, 1.0, 0.1, 0.01) / 100
            slippage_bps = 2.0
            impact_coeff = 0.05
            hft_aggr = 0.35
            if strategy_type == "Hybrid Multi-Factor (Python + C++ HFT)":
                slippage_bps = st.slider("Slippage (bps)", 0.0, 15.0, 2.0, 0.5)
                impact_coeff = st.slider("Market Impact Coefficient", 0.0, 0.5, 0.05, 0.01)
                hft_aggr = st.slider("C++ HFT Aggressiveness", 0.0, 1.0, 0.35, 0.05)

        # Run backtest button
        if st.button("🚀 Run Backtest", type="primary"):
            with st.spinner("Running backtest with Yahoo Finance data..."):
                if strategy_type == "Buy & Hold":
                    results = self._run_simple_backtest_pipeline(
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=initial_capital,
                        commission_rate=commission_rate,
                    )
                elif strategy_type == "Simple Momentum":
                    results = self._run_momentum_backtest_pipeline(
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=initial_capital,
                        commission_rate=commission_rate,
                        lookback_days=lookback_days,
                        top_n=top_n,
                        reverse=False,
                    )
                elif strategy_type == "Simple Mean Reversion":
                    results = self._run_momentum_backtest_pipeline(
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=initial_capital,
                        commission_rate=commission_rate,
                        lookback_days=lookback_days,
                        top_n=top_n,
                        reverse=True,
                    )
                elif strategy_type == "Hybrid Multi-Factor (Python + C++ HFT)":
                    from data_service.pipelines.multifactor_pipeline import MultiFactorConfig, run_multifactor_strategy

                    cfg = MultiFactorConfig(
                        lookback_days=lookback_days,
                        top_n=top_n,
                        commission_rate=commission_rate,
                        factor_weights=factor_weights,
                        slippage_bps=slippage_bps,
                        impact_coefficient=impact_coeff,
                        hft_aggressiveness=hft_aggr,
                    )

                    results = run_multifactor_strategy(
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=initial_capital,
                        yahoo_fetcher=self.yahoo_fetcher,
                        factor_calculator=self.factor_calculator,
                        backtest_engine=self.backtest_engine,
                        config=cfg,
                        hft_engine=self.hft_engine,
                    )
                else:
                    results = None

                if not results:
                    st.error("Backtest failed or no data available for the selected symbols.")
                else:
                    self._display_backtest_results(results)

    def _show_market_data(self):
        """Show market data tab"""
        st.header("📈 Market Data")

        # Symbol selector
        symbol = st.selectbox("Select Symbol", st.session_state.get('symbols', ['AAPL']))

        # Timeframe selector
        timeframe = st.selectbox("Timeframe", ["3M", "6M", "1Y"], index=2)

        # Map timeframe to days
        days_map = {"3M": 90, "6M": 180, "1Y": 365}
        days = days_map.get(timeframe, 365)

        # Fetch real market data using Yahoo Finance, fallback to sample on failure
        try:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days)
            df = self.yahoo_fetcher.fetch_historical_data(
                symbol=symbol,
                start_time=start_dt,
                end_time=end_dt,
                interval='1d',
            )
            market_data = df[['open', 'high', 'low', 'close', 'volume']].copy()
        except Exception:
            market_data = self._generate_sample_market_data(symbol)

        # Price chart
        st.subheader(f"📊 {symbol} Price Chart")
        price_fig = self.chart_generator.create_real_time_price_chart(market_data, symbol)
        st.plotly_chart(price_fig, use_container_width=True)

        # Technical indicators
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Technical Indicators")

            # RSI
            rsi_data = self._calculate_rsi(market_data['close'])
            rsi_fig = go.Figure()
            rsi_fig.add_trace(go.Scatter(x=market_data.index, y=rsi_data, name='RSI'))
            rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", name="Overbought")
            rsi_fig.add_hline(y=30, line_dash="dash", line_color="green", name="Oversold")
            rsi_fig.update_layout(title="RSI", height=300)
            st.plotly_chart(rsi_fig, use_container_width=True)

        with col2:
            st.subheader("📊 Volume Analysis")

            # Volume chart
            volume_fig = go.Figure()
            volume_fig.add_trace(go.Bar(
                x=market_data.index,
                y=market_data['volume'],
                name='Volume',
                marker_color='rgba(0, 128, 255, 0.6)',
            ))
            volume_fig.update_layout(title="Trading Volume", height=300)
            st.plotly_chart(volume_fig, use_container_width=True)

        # Market statistics
        st.subheader("📋 Market Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Current Price", f"${market_data['close'].iloc[-1]:.2f}")

        with col2:
            daily_return = (market_data['close'].iloc[-1] / market_data['close'].iloc[-2] - 1) * 100
            st.metric("Daily Return", f"{daily_return:.2f}%")

        with col3:
            volatility = market_data['close'].pct_change().std() * np.sqrt(252) * 100
            st.metric("Volatility", f"{volatility:.2f}%")

        with col4:
            avg_volume = market_data['volume'].mean()
            st.metric("Avg Volume", f"{avg_volume:,.0f}")
    
    def _show_ai_analysis(self):
        """Show AI analysis tab"""
        st.header("🤖 AI Analysis")
        
        # NLP Analysis
        st.subheader("📝 Sentiment Analysis")
        
        # Text input for analysis
        text_input = st.text_area(
            "Enter financial news or text for sentiment analysis:",
            value="Apple's quarterly earnings exceeded expectations, driving stock price higher by 5%! 🚀",
            height=100
        )
        
        if st.button("🔍 Analyze Sentiment"):
            with st.spinner("Analyzing sentiment..."):
                # Process text
                processed = self.nlp_processor.preprocess_text(text_input)
                
                # Display results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Sentiment", processed.sentiment_label)
                
                with col2:
                    st.metric("Confidence", f"{processed.sentiment_score:.3f}")
                
                with col3:
                    st.metric("Keywords", ", ".join(processed.keywords[:3]))
                
                # Show detailed analysis
                st.subheader("📊 Detailed Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Cleaned Text:**")
                    st.write(processed.cleaned_text)
                    
                    st.write("**Topics:**")
                    st.write(", ".join(processed.topics))
                
                with col2:
                    st.write("**Language:**")
                    st.write(processed.language)
                    
                    st.write("**All Keywords:**")
                    st.write(", ".join(processed.keywords))
        
        # Factor Analysis
        st.subheader("📈 Factor Analysis")
        
        # Factor selection
        factors = st.multiselect(
            "Select Factors to Analyze",
            ["Momentum", "Value", "Quality", "Size", "Volatility", "Sentiment"],
            default=["Momentum", "Value"]
        )
        
        if st.button("📊 Analyze Factors"):
            with st.spinner("Analyzing factors..."):
                # Generate sample factor data
                factor_data = self._generate_sample_factor_data()
                
                # Display factor performance
                st.subheader("📊 Factor Performance")
                
                # Factor performance table
                factor_perf_df = pd.DataFrame([
                    ["Momentum", 0.15, 0.08, 1.88, 0.65],
                    ["Value", 0.12, 0.06, 2.00, 0.58],
                    ["Quality", 0.10, 0.05, 2.00, 0.52],
                    ["Size", 0.08, 0.07, 1.14, 0.45],
                ], columns=["Factor", "Return", "Volatility", "Sharpe", "IC"])
                
                st.dataframe(factor_perf_df, use_container_width=True)
                
                # Factor correlation heatmap
                st.subheader("🔥 Factor Correlation")
                correlation_data = np.random.rand(4, 4)
                correlation_data = (correlation_data + correlation_data.T) / 2
                np.fill_diagonal(correlation_data, 1)
                
                corr_fig = px.imshow(
                    correlation_data,
                    labels=dict(x="Factor", y="Factor", color="Correlation"),
                    x=["Momentum", "Value", "Quality", "Size"],
                    y=["Momentum", "Value", "Quality", "Size"],
                    color_continuous_scale="RdBu",
                    aspect="auto"
                )
                st.plotly_chart(corr_fig, use_container_width=True)
    
    def _show_system_status(self):
        """Show system status tab"""
        st.header("⚙️ System Status")
        
        # System metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("CPU Usage", "45%", "5%")
        
        with col2:
            st.metric("Memory Usage", "2.3 GB", "0.2 GB")
        
        with col3:
            st.metric("Active Connections", "12", "2")
        
        with col4:
            st.metric("API Calls/min", "156", "23")
        
        # System health
        st.subheader("🏥 System Health")
        
        # Health indicators
        health_data = {
            "Database Connection": "✅ Healthy",
            "API Services": "✅ Healthy", 
            "Data Feeds": "✅ Healthy",
            "Strategy Engine": "✅ Healthy",
            "Risk Management": "✅ Healthy",
            "Order Execution": "⚠️ Warning",
            "Cache System": "✅ Healthy"
        }
        
        for service, status in health_data.items():
            if "✅" in status:
                st.success(f"{service}: {status}")
            elif "⚠️" in status:
                st.warning(f"{service}: {status}")
            else:
                st.error(f"{service}: {status}")
        
        # Recent logs
        st.subheader("📋 Recent Logs")
        
        logs = [
            ("2024-01-15 10:30:15", "INFO", "Strategy execution completed successfully"),
            ("2024-01-15 10:29:45", "INFO", "Market data updated for AAPL, GOOGL, MSFT"),
            ("2024-01-15 10:29:30", "WARNING", "High latency detected in order execution"),
            ("2024-01-15 10:28:15", "INFO", "Risk check passed for new order"),
            ("2024-01-15 10:27:30", "INFO", "Sentiment analysis completed for 50 news articles")
        ]
        
        log_df = pd.DataFrame(logs, columns=["Timestamp", "Level", "Message"])
        st.dataframe(log_df, use_container_width=True)
    
    def _run_simple_backtest_pipeline(self, symbols, start_date, end_date, initial_capital, commission_rate):
        """Run a simple buy-and-hold backtest using Yahoo Finance data."""
        try:
            if not symbols:
                return None

            # Normalize dates (Streamlit date_input gives date objects)
            from datetime import datetime as _dt
            if hasattr(start_date, 'year') and not isinstance(start_date, _dt):
                start_dt = _dt.combine(start_date, _dt.min.time())
            else:
                start_dt = start_date
            if hasattr(end_date, 'year') and not isinstance(end_date, _dt):
                end_dt = _dt.combine(end_date, _dt.min.time())
            else:
                end_dt = end_date

            price_series = []
            for sym in symbols:
                df = self.yahoo_fetcher.fetch_historical_data(
                    symbol=sym,
                    start_time=start_dt,
                    end_time=end_dt,
                    interval='1d',
                )
                if df.empty or 'close' not in df.columns:
                    continue
                series = df['close'].rename(sym)
                price_series.append(series)

            if not price_series:
                return None

            import pandas as _pd
            price_df = _pd.concat(price_series, axis=1).dropna()

            # Configure backtest engine
            self.backtest_engine.initial_capital = float(initial_capital)
            self.backtest_engine.commission_rate = float(commission_rate)

            def strategy_func(data, engine, symbols_param):
                if data.empty:
                    return
                symbols_local = [s for s in symbols_param if s in data.columns]
                if not symbols_local:
                    return

                first_idx = data.index[0]
                last_idx = data.index[-1]
                first_ts = getattr(first_idx, 'to_pydatetime', lambda: first_idx)()
                last_ts = getattr(last_idx, 'to_pydatetime', lambda: last_idx)()

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
            if isinstance(equity_curve, _pd.DataFrame) and not equity_curve.empty:
                equity_data = equity_curve[['total_value']].rename(columns={'total_value': 'equity'})
            else:
                equity_data = _pd.DataFrame()

            return {
                'total_return': results.get('total_return', 0.0),
                'sharpe_ratio': results.get('sharpe_ratio', 0.0),
                'max_drawdown': results.get('max_drawdown', 0.0),
                'win_rate': results.get('win_rate', 0.0),
                'total_trades': results.get('total_trades', 0),
                'equity_curve': equity_data,
            }
        except Exception as exc:
            logger.error(f"Dashboard backtest pipeline error: {exc}")
            return None


    def _generate_sample_performance_data(self):
        """Generate sample performance data for demonstration"""
        dates = pd.date_range(start='2023-01-01', end='2024-01-15', freq='D')
        np.random.seed(42)
        
        # Generate equity curve
        returns = np.random.normal(0.0005, 0.02, len(dates))
        equity = 100000 * np.cumprod(1 + returns)
        equity_data = pd.DataFrame({'equity': equity}, index=dates)
        
        # Calculate metrics
        total_return = (equity[-1] / equity[0] - 1)
        annualized_return = total_return * 252 / len(dates)
        volatility = np.std(returns) * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Convert numpy array to pandas Series for expanding calculations
        equity_series = pd.Series(equity)
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        
        return {
            'equity_data': equity_data,
            'drawdown_data': drawdown,
            'returns': pd.Series(returns, index=dates),
            'total_return': total_return,
            'total_return_delta': 0.05,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sharpe_delta': 0.1,
            'sortino_ratio': sharpe_ratio * 1.1,
            'max_drawdown': drawdown.min(),
            'drawdown_delta': 0.02,
            'calmar_ratio': annualized_return / abs(drawdown.min()) if drawdown.min() != 0 else 0,
            'win_rate': 0.58,
            'win_rate_delta': 0.03,
            'profit_factor': 1.45,
            'total_trades': 156
        }
    
    def _generate_sample_backtest_results(self):
        """Generate sample backtest results"""
        return {
            'total_return': 0.25,
            'sharpe_ratio': 1.8,
            'max_drawdown': -0.12,
            'win_rate': 0.65,
            'total_trades': 89,
            'equity_curve': self._generate_sample_performance_data()['equity_data']
        }
    
    def _generate_sample_market_data(self, symbol):
        """Generate sample market data"""
        dates = pd.date_range(start='2023-01-01', end='2024-01-15', freq='D')
        np.random.seed(42)
        
        # Generate price data
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = 100 * np.cumprod(1 + returns)
        
        # Generate volume data
        volume = np.random.lognormal(10, 0.5, len(dates))
        
        return pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
            'close': prices,
            'volume': volume
        }, index=dates)
    
    def _generate_sample_factor_data(self):
        """Generate sample factor data"""
        return pd.DataFrame({
            'momentum': np.random.normal(0, 1, 100),
            'value': np.random.normal(0, 1, 100),
            'quality': np.random.normal(0, 1, 100),
            'size': np.random.normal(0, 1, 100)
        })
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _display_backtest_results(self, results):
        """Display backtest results"""
        st.success("✅ Backtest completed successfully!")
        
        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{results['total_return']:.2%}")
        
        with col2:
            st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
        
        with col3:
            st.metric("Max Drawdown", f"{results['max_drawdown']:.2%}")
        
        with col4:
            st.metric("Win Rate", f"{results['win_rate']:.1%}")
        
        # Equity curve
        st.subheader("📈 Backtest Results")
        equity_fig = self.chart_generator.create_equity_curve(results['equity_curve'])
        st.plotly_chart(equity_fig, use_container_width=True)

        # Final investment conclusion / 最终结论
        tr = results.get('total_return', 0.0)
        sr = results.get('sharpe_ratio', 0.0)
        dd = results.get('max_drawdown', 0.0)
        wr = results.get('win_rate', 0.0)

        lang = getattr(self, 'lang', 'zh')
        title = '📌 最终结论' if lang == 'zh' else '📌 Final Conclusion'
        st.subheader(title)

        if tr > 0.30 and sr > 1.5 and dd > -0.25 and wr > 0.60:
            text = ('综合表现优秀，适合继续投资或适度加仓。'
                    if lang == 'zh'
                    else 'Strong overall performance; suitable to continue investing or even increase exposure.')
            st.success(text)
        elif tr > 0.05 and sr > 0.7 and dd > -0.35 and wr > 0.50:
            text = ('表现尚可，建议小仓位持有，并密切观察风险。'
                    if lang == 'zh'
                    else 'Acceptable performance; consider holding a small position and monitor risk.')
            st.info(text)
        else:
            text = ('风险收益比不理想，不建议继续投资或应考虑减仓。'
                    if lang == 'zh'
                    else 'Risk/return profile is not attractive; avoid new investments or reduce exposure.')
            st.warning(text)

        label_metrics = '关键指标' if lang == 'zh' else 'Key metrics'
        st.write(
            f"{label_metrics}: Total Return {tr:.2%}, Sharpe {sr:.2f}, Max Drawdown {dd:.2%}, Win Rate {wr:.1%}"
        )

        factor_metrics = results.get('factor_metrics')
        if factor_metrics:
            with st.expander("🧠 因子诊断 / Factor Diagnostics", expanded=False):
                ic_mean = factor_metrics.get('ic_mean')
                ic_ir = factor_metrics.get('ic_ir')
                samples = factor_metrics.get('samples')
                st.write(f"IC Mean: {ic_mean:.4f}" if ic_mean is not None else "IC Mean: n/a")
                st.write(f"IC IR: {ic_ir:.2f}" if ic_ir is not None else "IC IR: n/a")
                st.write(f"Samples: {samples}")
                ic_series = factor_metrics.get('ic_series')
                ic_chart = None
                if hasattr(ic_series, 'dropna'):
                    ic_chart = ic_series.dropna()
                elif isinstance(ic_series, dict):
                    ic_chart = pd.Series(ic_series).dropna()
                if ic_chart is not None and len(ic_chart) > 0:
                    st.line_chart(ic_chart.rename("IC"))
                snapshots = factor_metrics.get('factor_snapshots') or []
                if snapshots:
                    snapshot_df = pd.DataFrame([
                        {
                            'date': snap.get('date'),
                            'top_symbols': ", ".join(snap.get('selected', [])[:5]),
                        }
                        for snap in snapshots
                    ])
                    st.dataframe(snapshot_df, use_container_width=True)

        decision_info = results.get('decision_engine')
        if decision_info:
            with st.expander("⚡ C++ 高频决策引擎", expanded=False):
                st.write(
                    f"Avg latency: {decision_info.get('latency_ms_avg'):.2f} ms"
                    if decision_info.get('latency_ms_avg') is not None else "Avg latency: n/a"
                )
                st.write(
                    f"P95 latency: {decision_info.get('latency_ms_p95'):.2f} ms"
                    if decision_info.get('latency_ms_p95') is not None else "P95 latency: n/a"
                )
                cpp_ratio = decision_info.get('cpp_hit_ratio')
                if cpp_ratio is not None:
                    st.write(f"C++ execution hit ratio: {cpp_ratio:.1%}")
                orders = decision_info.get('orders') or []
                if orders:
                    orders_df = pd.DataFrame([
                        {
                            'timestamp': order.get('timestamp'),
                            'engine': order.get('engine'),
                            'latency_ms': order.get('latency_ms'),
                            'top_symbols': ", ".join(
                                f"{sym}:{weight:.2f}" for sym, weight in (order.get('top_symbols') or {}).items()
                            ),
                        }
                        for order in orders[-5:]
                    ])
                    st.dataframe(orders_df, use_container_width=True)

    def _run_momentum_backtest_pipeline(self, symbols, start_date, end_date,
                                         initial_capital, commission_rate,
                                         lookback_days=60, top_n=3, reverse=False):
        """Cross-sectional momentum / mean-reversion backtest using Yahoo data.
    
        reverse=False: 选取收益/风险比最高的动量组合（多头）
        reverse=True : 选取跌幅最大的组合（简单均值回归，多头反弹）
        """
        try:
            if not symbols:
                return None
    
            from datetime import datetime as _dt
            # Normalize dates (Streamlit date_input gives date objects)
            if hasattr(start_date, 'year') and not isinstance(start_date, _dt):
                start_dt = _dt.combine(start_date, _dt.min.time())
            else:
                start_dt = start_date
            if hasattr(end_date, 'year') and not isinstance(end_date, _dt):
                end_dt = _dt.combine(end_date, _dt.min.time())
            else:
                end_dt = end_date
    
            import pandas as _pd
            import numpy as _np
    
            # Fetch price panel
            series_list = []
            for sym in symbols:
                try:
                    df = self.yahoo_fetcher.fetch_historical_data(
                        symbol=sym,
                        start_time=start_dt,
                        end_time=end_dt,
                        interval='1d',
                    )
                    if df.empty or 'close' not in df.columns:
                        continue
                    s = df['close'].rename(sym)
                    series_list.append(s)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Momentum pipeline: failed to fetch %s: %s", sym, exc)
                    continue
    
            if not series_list:
                return None
    
            price_df = _pd.concat(series_list, axis=1).dropna(how='all')
            price_df = price_df.dropna(axis=1, how='all')
            if price_df.shape[1] == 0:
                return None
    
            max_window = max(20, lookback_days)
            if len(price_df) <= max_window + 5:
                return None
    
            returns = price_df.pct_change().dropna()
    
            # Monthly rebalancing dates
            monthly_first = price_df.resample('M').first().index
            rebal_dates = [d for d in monthly_first if d in returns.index]
            if not rebal_dates:
                return None
    
            weights = _pd.DataFrame(0.0, index=returns.index, columns=returns.columns)
    
            for d in rebal_dates:
                loc = returns.index.get_loc(d)
                start_loc = loc - lookback_days
                if start_loc <= 0:
                    continue
                window = returns.iloc[start_loc:loc]
                if window.empty:
                    continue
    
                # cumulative return over lookback window (absolute momentum)
                mom = (1.0 + window).prod() - 1.0
                mom = mom.dropna()
                if mom.empty:
                    continue
    
                # annualized volatility as risk measure
                vol = window.std() * _np.sqrt(252.0)
                vol = vol.reindex(mom.index).dropna()
                if vol.empty:
                    continue
    
                # align
                common_idx = mom.index.intersection(vol.index)
                mom = mom.loc[common_idx]
                vol = vol.loc[common_idx]
    
                if mom.empty:
                    continue
    
                # Absolute momentum filter
                if not reverse:
                    mom = mom[mom > 0]
                else:
                    mom = mom[mom < 0]
    
                if mom.empty:
                    continue
    
                # Risk filter: drop extremely volatile names (top 10% vol)
                vol = vol.loc[mom.index]
                vol_threshold = vol.quantile(0.9)
                valid = vol <= vol_threshold
                mom = mom[valid]
                vol = vol[valid]
    
                if mom.empty:
                    continue
    
                # Score: risk-adjusted momentum for momentum strategy,
                # plain losers for mean reversion.
                if not reverse:
                    score = mom / vol.replace(0, _np.nan)
                    score = score.replace([_np.inf, -_np.inf], _np.nan).dropna()
                    if score.empty:
                        continue
                    ranked = score.sort_values(ascending=False)
                else:
                    # mean reversion: pick biggest losers with acceptable vol
                    ranked = mom.sort_values(ascending=True)
    
                n_pick = min(top_n, len(ranked))
                selected = ranked.head(n_pick).index
    
                w = _pd.Series(0.0, index=returns.columns)
                if len(selected) > 0:
                    w.loc[selected] = 1.0 / len(selected)
                weights.loc[d] = w
    
            if (weights.sum(axis=1) == 0).all():
                return None
    
            weights = weights.sort_index().ffill().shift(1).fillna(0.0)
            port_ret = (weights * returns).sum(axis=1)
    
            # Build equity curve
            equity = initial_capital * (1.0 + port_ret).cumprod()
            equity_df = _pd.DataFrame({'equity': equity})
            if equity_df.empty:
                return None
    
            total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
            days = (equity_df.index[-1] - equity_df.index[0]).days or 1
            annualized_return = (1.0 + total_return) ** (365.0 / days) - 1.0
            vol_p = float(port_ret.std() * (_np.sqrt(252.0))) if len(port_ret) > 1 else 0.0
            sharpe_ratio = float(annualized_return / vol_p) if vol_p > 0 else 0.0
    
            peak = equity_df['equity'].cummax()
            drawdown = (equity_df['equity'] - peak) / peak
            max_drawdown = float(drawdown.min())
    
            win_rate = float((port_ret > 0).mean()) if len(port_ret) > 0 else 0.0
    
            num_rebals = int((weights.diff().abs().sum(axis=1) > 1e-6).sum())
            total_trades = int(num_rebals * top_n * 2)
    
            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'equity_curve': equity_df,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Dashboard momentum backtest pipeline error: {exc}")
            return None


def main():
    """Main function to run the dashboard"""
    try:
        dashboard = TradingDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Error running dashboard: {e}")
        logger.exception("Dashboard error")

if __name__ == "__main__":
    main() 

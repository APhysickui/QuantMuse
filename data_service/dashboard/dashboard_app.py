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
    from data_service.dashboard.charts import ChartGenerator
    from data_service.dashboard.widgets import DashboardWidgets
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
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown('<h1 class="main-header">📈 Trading System Dashboard</h1>', unsafe_allow_html=True)
        
        # Sidebar
        self._create_sidebar()
        
        # Main content
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Performance Analysis", 
            "🎯 Strategy Backtest", 
            "📈 Market Data", 
            "🤖 AI Analysis", 
            "⚙️ System Status"
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
        st.sidebar.title("🎛️ Dashboard Controls")
        
        # Date range selector
        st.sidebar.subheader("📅 Date Range")
        start_date = st.sidebar.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now()
        )
        end_date = st.sidebar.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )
        
        # Strategy selector
        st.sidebar.subheader("🎯 Strategy")
        strategy_options = ["Momentum Strategy", "Value Strategy", "Mean Reversion", "Custom"]
        selected_strategy = st.sidebar.selectbox("Select Strategy", strategy_options)
        
        # Symbols selector
        st.sidebar.subheader("📈 Symbols")
        symbols = st.sidebar.multiselect(
            "Select Symbols",
            ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"],
            default=["AAPL", "GOOGL", "MSFT"]
        )
        
        # Initial capital
        st.sidebar.subheader("💰 Capital")
        initial_capital = st.sidebar.number_input(
            "Initial Capital ($)",
            min_value=1000,
            max_value=1000000,
            value=100000,
            step=10000
        )
        
        # Store in session state
        st.session_state.update({
            'start_date': start_date,
            'end_date': end_date,
            'selected_strategy': selected_strategy,
            'symbols': symbols,
            'initial_capital': initial_capital
        })
    
    def _show_performance_analysis(self):
        """Show performance analysis tab"""
        st.header("📊 Performance Analysis")
        
        # Generate sample data for demonstration
        sample_data = self._generate_sample_performance_data()
        
        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Return",
                f"{sample_data['total_return']:.2%}",
                f"{sample_data['total_return_delta']:+.2%}"
            )
        
        with col2:
            st.metric(
                "Sharpe Ratio",
                f"{sample_data['sharpe_ratio']:.2f}",
                f"{sample_data['sharpe_delta']:+.2f}"
            )
        
        with col3:
            st.metric(
                "Max Drawdown",
                f"{sample_data['max_drawdown']:.2%}",
                f"{sample_data['drawdown_delta']:+.2%}"
            )
        
        with col4:
            st.metric(
                "Win Rate",
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
        st.subheader("📋 Detailed Performance Metrics")
        metrics_df = pd.DataFrame([
            ["Total Return", f"{sample_data['total_return']:.2%}"],
            ["Annualized Return", f"{sample_data['annualized_return']:.2%}"],
            ["Volatility", f"{sample_data['volatility']:.2%}"],
            ["Sharpe Ratio", f"{sample_data['sharpe_ratio']:.2f}"],
            ["Sortino Ratio", f"{sample_data['sortino_ratio']:.2f}"],
            ["Max Drawdown", f"{sample_data['max_drawdown']:.2%}"],
            ["Calmar Ratio", f"{sample_data['calmar_ratio']:.2f}"],
            ["Win Rate", f"{sample_data['win_rate']:.1%}"],
            ["Profit Factor", f"{sample_data['profit_factor']:.2f}"],
            ["Total Trades", str(sample_data['total_trades'])],
        ], columns=["Metric", "Value"])
        
        st.dataframe(metrics_df, use_container_width=True)
    
    def _show_strategy_backtest(self):
        """Show strategy backtest tab"""
        st.header("🎯 Strategy Backtest")
        
        # Strategy configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ Strategy Parameters")
            
            # Strategy type
            strategy_type = st.selectbox(
                "Strategy Type",
                ["Momentum", "Mean Reversion", "Value", "Multi-Factor"]
            )
            
            # Parameters based on strategy type
            if strategy_type == "Momentum":
                lookback_period = st.slider("Lookback Period", 5, 252, 20)
                momentum_threshold = st.slider("Momentum Threshold", 0.01, 0.10, 0.05, 0.01)
            elif strategy_type == "Mean Reversion":
                lookback_period = st.slider("Lookback Period", 5, 252, 20)
                reversion_threshold = st.slider("Reversion Threshold", 1.0, 3.0, 2.0, 0.1)
            elif strategy_type == "Value":
                pe_ratio_max = st.slider("Max P/E Ratio", 10, 50, 25)
                pb_ratio_max = st.slider("Max P/B Ratio", 1, 10, 3)
            else:  # Multi-Factor
                momentum_weight = st.slider("Momentum Weight", 0.0, 1.0, 0.5, 0.1)
                value_weight = st.slider("Value Weight", 0.0, 1.0, 0.3, 0.1)
                quality_weight = st.slider("Quality Weight", 0.0, 1.0, 0.2, 0.1)
        
        with col2:
            st.subheader("📊 Backtest Settings")
            
            # Commission rate
            commission_rate = st.slider("Commission Rate (%)", 0.0, 1.0, 0.1, 0.01) / 100
            
            # Rebalancing frequency
            rebalance_freq = st.selectbox(
                "Rebalancing Frequency",
                ["Daily", "Weekly", "Monthly", "Quarterly"]
            )
            
            # Position sizing
            position_size = st.slider("Position Size (%)", 1, 100, 10)
        
        # Run backtest button
        if st.button("🚀 Run Backtest", type="primary"):
            with st.spinner("Running backtest..."):
                # Generate sample backtest results
                backtest_results = self._generate_sample_backtest_results()
                
                # Display results
                self._display_backtest_results(backtest_results)
    
    def _show_market_data(self):
        """Show market data tab"""
        st.header("📈 Market Data")
        
        # Symbol selector
        symbol = st.selectbox("Select Symbol", st.session_state.get('symbols', ['AAPL']))
        
        # Timeframe selector
        timeframe = st.selectbox("Timeframe", ["1D", "1W", "1M", "3M", "6M", "1Y"])
        
        # Generate sample market data
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
                marker_color='rgba(0, 128, 255, 0.6)'
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
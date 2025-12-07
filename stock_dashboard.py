#!/usr/bin/env python3
"""
QuantMuse 股票数据可视化网站
专为股票数据分析设计的Streamlit仪表板
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from data_service.fetchers.yahoo_fetcher import YahooFetcher
except ImportError:
    st.warning("无法导入YahooFetcher，将使用yfinance直接获取数据")
    YahooFetcher = None

# 页面配置
st.set_page_config(
    page_title="QuantMuse 股票分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .positive {
        color: #28a745;
        font-weight: bold;
    }
    .negative {
        color: #dc3545;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stSelectbox > div > div > div {
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

class StockDashboard:
    """股票分析仪表板主类"""

    def __init__(self):
        self.popular_stocks = {
            'AAPL': '苹果公司',
            'MSFT': '微软公司',
            'GOOGL': '谷歌(Alphabet)',
            'AMZN': '亚马逊',
            'TSLA': '特斯拉',
            'NVDA': '英伟达',
            'META': 'Meta(Facebook)',
            'JPM': '摩根大通',
            'JNJ': '强生公司',
            'V': 'Visa',
            'UNH': '联合健康',
            'WMT': '沃尔玛',
            'PG': '宝洁',
            'MA': '万事达',
            'HD': '家得宝',
            'DIS': '迪士尼',
            'NFLX': '网飞',
            'CRM': 'Salesforce',
            'ADBE': 'Adobe',
            'PYPL': 'PayPal'
        }

        # 行业分类
        self.sectors = {
            '科技股': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'NFLX', 'CRM', 'ADBE'],
            '金融股': ['JPM', 'V', 'MA', 'PYPL'],
            '消费股': ['AMZN', 'WMT', 'PG', 'HD', 'DIS'],
            '医疗股': ['JNJ', 'UNH'],
            '汽车股': ['TSLA']
        }

        if YahooFetcher:
            self.fetcher = YahooFetcher()
        else:
            self.fetcher = None

    def run(self):
        """运行主应用"""
        # 标题
        st.markdown('<h1 class="main-header">📈 QuantMuse 股票分析平台</h1>', unsafe_allow_html=True)

        # 侧边栏控制
        self._create_sidebar()

        # 主要内容区域
        self._create_main_content()

    def _create_sidebar(self):
        """创建侧边栏控制界面"""
        st.sidebar.title("🎛️ 分析控制面板")

        # 股票选择
        st.sidebar.subheader("📈 选择股票")

        # 选择方式：单只股票或行业
        analysis_type = st.sidebar.radio(
            "分析类型",
            ["单只股票分析", "行业对比分析", "自定义股票组合"]
        )

        if analysis_type == "单只股票分析":
            # 单只股票分析
            selected_symbol = st.sidebar.selectbox(
                "选择股票",
                list(self.popular_stocks.keys()),
                format_func=lambda x: f"{x} - {self.popular_stocks[x]}"
            )
            symbols = [selected_symbol]

        elif analysis_type == "行业对比分析":
            # 行业分析
            selected_sector = st.sidebar.selectbox(
                "选择行业",
                list(self.sectors.keys())
            )
            symbols = self.sectors[selected_sector]

        else:
            # 自定义组合
            symbols = st.sidebar.multiselect(
                "选择多只股票",
                list(self.popular_stocks.keys()),
                default=['AAPL', 'MSFT', 'GOOGL'],
                format_func=lambda x: f"{x} - {self.popular_stocks[x]}"
            )

        # 时间范围
        st.sidebar.subheader("📅 时间范围")
        time_range = st.sidebar.selectbox(
            "选择时间范围",
            ["1个月", "3个月", "6个月", "1年", "2年", "5年", "自定义"]
        )

        if time_range == "自定义":
            start_date = st.sidebar.date_input(
                "开始日期",
                value=datetime.now() - timedelta(days=365)
            )
            end_date = st.sidebar.date_input(
                "结束日期",
                value=datetime.now()
            )
        else:
            time_mapping = {
                "1个月": 30,
                "3个月": 90,
                "6个月": 180,
                "1年": 365,
                "2年": 730,
                "5年": 1825
            }
            days = time_mapping[time_range]
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

        # 技术指标选择
        st.sidebar.subheader("🔧 技术指标")
        show_ma = st.sidebar.checkbox("移动平均线", True)
        show_rsi = st.sidebar.checkbox("RSI指标", True)
        show_macd = st.sidebar.checkbox("MACD指标", True)
        show_bollinger = st.sidebar.checkbox("布林带", False)
        show_volume = st.sidebar.checkbox("成交量", True)

        # 存储到session state
        st.session_state.update({
            'analysis_type': analysis_type,
            'symbols': symbols,
            'start_date': start_date,
            'end_date': end_date,
            'show_ma': show_ma,
            'show_rsi': show_rsi,
            'show_macd': show_macd,
            'show_bollinger': show_bollinger,
            'show_volume': show_volume
        })

    def _create_main_content(self):
        """创建主要内容区域"""
        symbols = st.session_state.get('symbols', ['AAPL'])

        if not symbols:
            st.warning("请至少选择一只股票进行分析")
            return

        # 获取数据
        with st.spinner("正在获取股票数据..."):
            stock_data = self._fetch_stock_data(symbols)

        if not stock_data:
            st.error("无法获取股票数据，请检查网络连接或稍后重试")
            return

        # 创建标签页
        if len(symbols) == 1:
            # 单只股票详细分析
            self._show_single_stock_analysis(symbols[0], stock_data[symbols[0]])
        else:
            # 多只股票对比分析
            self._show_multiple_stocks_analysis(symbols, stock_data)

    def _fetch_stock_data(self, symbols):
        """获取股票数据"""
        stock_data = {}
        start_date = st.session_state.get('start_date')
        end_date = st.session_state.get('end_date')

        progress_bar = st.progress(0)

        for i, symbol in enumerate(symbols):
            try:
                if self.fetcher:
                    # 使用QuantMuse fetcher
                    df = self.fetcher.fetch_historical_data(
                        symbol=symbol,
                        start_time=start_date,
                        end_time=end_date
                    )
                    # 重命名列以匹配yfinance格式
                    if 'adj close' in df.columns:
                        df = df.rename(columns={'adj close': 'Adj Close'})
                    df.columns = [col.title() for col in df.columns]
                else:
                    # 直接使用yfinance
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(start=start_date, end=end_date)

                if not df.empty:
                    stock_data[symbol] = df

                progress_bar.progress((i + 1) / len(symbols))

            except Exception as e:
                st.error(f"获取 {symbol} 数据失败: {str(e)}")

        progress_bar.empty()
        return stock_data

    def _show_single_stock_analysis(self, symbol, df):
        """显示单只股票详细分析"""
        st.header(f"📊 {symbol} - {self.popular_stocks.get(symbol, '')} 详细分析")

        # 基本信息和指标
        self._show_stock_metrics(symbol, df)

        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs(["📈 价格图表", "🔧 技术指标", "📊 统计分析", "📈 对比基准"])

        with tab1:
            self._show_price_charts(symbol, df)

        with tab2:
            self._show_technical_indicators(symbol, df)

        with tab3:
            self._show_statistical_analysis(symbol, df)

        with tab4:
            self._show_benchmark_comparison(symbol, df)

    def _show_multiple_stocks_analysis(self, symbols, stock_data):
        """显示多只股票对比分析"""
        st.header(f"📊 多股票对比分析 ({len(symbols)} 只股票)")

        # 显示所有股票的基本指标
        self._show_comparison_metrics(symbols, stock_data)

        # 创建标签页
        tab1, tab2, tab3 = st.tabs(["📈 价格对比", "📊 收益率分析", "🔗 相关性分析"])

        with tab1:
            self._show_price_comparison(symbols, stock_data)

        with tab2:
            self._show_returns_analysis(symbols, stock_data)

        with tab3:
            self._show_correlation_analysis(symbols, stock_data)

    def _show_stock_metrics(self, symbol, df):
        """显示股票基本指标"""
        if df.empty:
            st.warning(f"没有 {symbol} 的数据")
            return

        # 计算基本指标
        current_price = df['Close'].iloc[-1]
        start_price = df['Close'].iloc[0]
        total_return = (current_price - start_price) / start_price

        # 获取公司信息
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', 'N/A')
            dividend_yield = info.get('dividendYield', 0)
        except:
            market_cap = 'N/A'
            pe_ratio = 'N/A'
            dividend_yield = 'N/A'

        # 显示指标
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "当前价格",
                f"${current_price:.2f}",
                f"{total_return:+.2%}"
            )

        with col2:
            volatility = df['Close'].pct_change().std() * np.sqrt(252)
            st.metric("年化波动率", f"{volatility:.2%}")

        with col3:
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                if market_cap >= 1e12:
                    cap_str = f"${market_cap/1e12:.1f}T"
                elif market_cap >= 1e9:
                    cap_str = f"${market_cap/1e9:.1f}B"
                else:
                    cap_str = f"${market_cap/1e6:.1f}M"
            else:
                cap_str = "N/A"
            st.metric("市值", cap_str)

        with col4:
            st.metric("市盈率", f"{pe_ratio}" if pe_ratio != 'N/A' else "N/A")

        with col5:
            if isinstance(dividend_yield, (int, float)):
                div_str = f"{dividend_yield:.2%}"
            else:
                div_str = "N/A"
            st.metric("股息收益率", div_str)

    def _show_price_charts(self, symbol, df):
        """显示价格图表"""
        st.subheader("📈 股价走势图")

        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(f'{symbol} 股价走势', '成交量'),
            row_width=[0.7, 0.3]
        )

        # 价格线
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['Close'],
                name='收盘价',
                line=dict(color='#1f77b4', width=2)
            ),
            row=1, col=1
        )

        # 移动平均线
        if st.session_state.get('show_ma', True):
            ma5 = df['Close'].rolling(window=5).mean()
            ma20 = df['Close'].rolling(window=20).mean()
            ma50 = df['Close'].rolling(window=50).mean()

            fig.add_trace(
                go.Scatter(x=df.index, y=ma5, name='MA5',
                          line=dict(color='orange', width=1)),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df.index, y=ma20, name='MA20',
                          line=dict(color='red', width=1)),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df.index, y=ma50, name='MA50',
                          line=dict(color='purple', width=1)),
                row=1, col=1
            )

        # 布林带
        if st.session_state.get('show_bollinger', False):
            bb_middle = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)

            fig.add_trace(
                go.Scatter(x=df.index, y=bb_upper, name='布林带上轨',
                          line=dict(color='gray', dash='dash')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df.index, y=bb_lower, name='布林带下轨',
                          line=dict(color='gray', dash='dash'),
                          fill='tonexty', fillcolor='rgba(128,128,128,0.1)'),
                row=1, col=1
            )

        # 成交量
        if st.session_state.get('show_volume', True):
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='成交量',
                    marker_color='rgba(0, 128, 255, 0.6)'
                ),
                row=2, col=1
            )

        fig.update_layout(
            height=700,
            title=f"{symbol} 技术分析图表",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

    def _show_technical_indicators(self, symbol, df):
        """显示技术指标"""
        col1, col2 = st.columns(2)

        with col1:
            if st.session_state.get('show_rsi', True):
                st.subheader("📊 RSI 相对强弱指标")
                rsi = self._calculate_rsi(df['Close'])

                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI'))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",
                                 annotation_text="超买线(70)")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green",
                                 annotation_text="超卖线(30)")
                fig_rsi.update_layout(title="RSI指标", height=400, yaxis_range=[0, 100])
                st.plotly_chart(fig_rsi, use_container_width=True)

                # 当前RSI值和信号
                current_rsi = rsi.iloc[-1]
                if current_rsi > 70:
                    st.warning(f"当前RSI: {current_rsi:.2f} - 可能超买")
                elif current_rsi < 30:
                    st.success(f"当前RSI: {current_rsi:.2f} - 可能超卖")
                else:
                    st.info(f"当前RSI: {current_rsi:.2f} - 正常范围")

        with col2:
            if st.session_state.get('show_macd', True):
                st.subheader("📈 MACD 指标")
                macd_line, macd_signal, macd_histogram = self._calculate_macd(df['Close'])

                fig_macd = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.1,
                    subplot_titles=('MACD线', 'MACD直方图'),
                    row_heights=[0.7, 0.3]
                )

                fig_macd.add_trace(
                    go.Scatter(x=df.index, y=macd_line, name='MACD'),
                    row=1, col=1
                )
                fig_macd.add_trace(
                    go.Scatter(x=df.index, y=macd_signal, name='信号线'),
                    row=1, col=1
                )
                fig_macd.add_trace(
                    go.Bar(x=df.index, y=macd_histogram, name='MACD直方图'),
                    row=2, col=1
                )

                fig_macd.update_layout(title="MACD指标", height=400)
                st.plotly_chart(fig_macd, use_container_width=True)

    def _show_statistical_analysis(self, symbol, df):
        """显示统计分析"""
        st.subheader("📊 统计分析")

        # 收益率分析
        returns = df['Close'].pct_change().dropna()

        col1, col2 = st.columns(2)

        with col1:
            # 收益率分布直方图
            fig_hist = px.histogram(
                returns,
                nbins=50,
                title="日收益率分布",
                labels={'value': '日收益率', 'count': '频数'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            # 滚动波动率
            rolling_vol = returns.rolling(window=30).std() * np.sqrt(252)
            fig_vol = go.Figure()
            fig_vol.add_trace(
                go.Scatter(x=rolling_vol.index, y=rolling_vol, name='30天滚动波动率')
            )
            fig_vol.update_layout(title="滚动波动率", yaxis_title="年化波动率")
            st.plotly_chart(fig_vol, use_container_width=True)

        # 统计指标表格
        st.subheader("📋 统计指标")

        stats_data = {
            '指标': [
                '平均日收益率', '标准差', '年化收益率', '年化波动率',
                '夏普比率', '最大回撤', '偏度', '峰度'
            ],
            '数值': [
                f"{returns.mean():.4f}",
                f"{returns.std():.4f}",
                f"{returns.mean() * 252:.2%}",
                f"{returns.std() * np.sqrt(252):.2%}",
                f"{(returns.mean() * 252) / (returns.std() * np.sqrt(252)):.2f}",
                f"{self._calculate_max_drawdown(df['Close']):.2%}",
                f"{returns.skew():.2f}",
                f"{returns.kurtosis():.2f}"
            ]
        }

        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)

    def _show_benchmark_comparison(self, symbol, df):
        """显示与基准的对比"""
        st.subheader("📈 与基准对比")

        # 选择基准
        benchmark = st.selectbox(
            "选择基准指数",
            ["SPY", "QQQ", "^GSPC", "^DJI", "^IXIC"],
            format_func=lambda x: {
                "SPY": "SPY (标普500ETF)",
                "QQQ": "QQQ (纳斯达克100ETF)",
                "^GSPC": "标普500指数",
                "^DJI": "道琼斯指数",
                "^IXIC": "纳斯达克指数"
            }.get(x, x)
        )

        # 获取基准数据
        try:
            benchmark_ticker = yf.Ticker(benchmark)
            benchmark_df = benchmark_ticker.history(
                start=st.session_state.get('start_date'),
                end=st.session_state.get('end_date')
            )

            if not benchmark_df.empty:
                # 标准化价格进行对比
                stock_normalized = (df['Close'] / df['Close'].iloc[0] - 1) * 100
                benchmark_normalized = (benchmark_df['Close'] / benchmark_df['Close'].iloc[0] - 1) * 100

                fig_compare = go.Figure()
                fig_compare.add_trace(
                    go.Scatter(x=stock_normalized.index, y=stock_normalized,
                              name=f'{symbol} 收益率', line=dict(color='blue'))
                )
                fig_compare.add_trace(
                    go.Scatter(x=benchmark_normalized.index, y=benchmark_normalized,
                              name=f'{benchmark} 收益率', line=dict(color='red'))
                )
                fig_compare.update_layout(
                    title=f"{symbol} vs {benchmark} 收益率对比",
                    yaxis_title="累计收益率 (%)",
                    height=500
                )
                st.plotly_chart(fig_compare, use_container_width=True)

                # 对比指标
                stock_return = stock_normalized.iloc[-1] / 100
                benchmark_return = benchmark_normalized.iloc[-1] / 100
                alpha = stock_return - benchmark_return

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"{symbol} 总收益", f"{stock_return:.2%}")
                with col2:
                    st.metric(f"{benchmark} 总收益", f"{benchmark_return:.2%}")
                with col3:
                    st.metric("Alpha (超额收益)", f"{alpha:+.2%}")

        except Exception as e:
            st.error(f"无法获取基准数据: {str(e)}")

    def _show_comparison_metrics(self, symbols, stock_data):
        """显示多股票对比指标"""
        st.subheader("📊 股票对比指标")

        metrics_data = []

        for symbol in symbols:
            if symbol in stock_data and not stock_data[symbol].empty:
                df = stock_data[symbol]
                current_price = df['Close'].iloc[-1]
                start_price = df['Close'].iloc[0]
                total_return = (current_price - start_price) / start_price
                volatility = df['Close'].pct_change().std() * np.sqrt(252)

                metrics_data.append({
                    '股票代码': symbol,
                    '公司名称': self.popular_stocks.get(symbol, ''),
                    '当前价格': f"${current_price:.2f}",
                    '总收益率': f"{total_return:.2%}",
                    '年化波动率': f"{volatility:.2%}",
                    '最大回撤': f"{self._calculate_max_drawdown(df['Close']):.2%}"
                })

        if metrics_data:
            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(metrics_df, use_container_width=True)

    def _show_price_comparison(self, symbols, stock_data):
        """显示价格对比图表"""
        st.subheader("📈 标准化价格走势对比")

        fig = go.Figure()

        for symbol in symbols:
            if symbol in stock_data and not stock_data[symbol].empty:
                df = stock_data[symbol]
                # 标准化为百分比变化
                normalized = (df['Close'] / df['Close'].iloc[0] - 1) * 100

                fig.add_trace(
                    go.Scatter(
                        x=normalized.index,
                        y=normalized,
                        name=f"{symbol} - {self.popular_stocks.get(symbol, '')}",
                        mode='lines'
                    )
                )

        fig.update_layout(
            title="股票价格走势对比 (标准化)",
            xaxis_title="日期",
            yaxis_title="累计收益率 (%)",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

    def _show_returns_analysis(self, symbols, stock_data):
        """显示收益率分析"""
        st.subheader("📊 收益率分析")

        # 计算所有股票的日收益率
        returns_data = {}
        for symbol in symbols:
            if symbol in stock_data and not stock_data[symbol].empty:
                returns = stock_data[symbol]['Close'].pct_change().dropna()
                returns_data[symbol] = returns

        if returns_data:
            returns_df = pd.DataFrame(returns_data)

            col1, col2 = st.columns(2)

            with col1:
                # 收益率分布箱线图
                fig_box = go.Figure()
                for symbol in returns_df.columns:
                    fig_box.add_trace(
                        go.Box(y=returns_df[symbol] * 100, name=symbol)
                    )
                fig_box.update_layout(
                    title="日收益率分布对比",
                    yaxis_title="日收益率 (%)"
                )
                st.plotly_chart(fig_box, use_container_width=True)

            with col2:
                # 滚动相关性热力图
                correlation = returns_df.corr()
                fig_corr = px.imshow(
                    correlation,
                    title="股票相关性矩阵",
                    color_continuous_scale='RdBu',
                    aspect="auto"
                )
                st.plotly_chart(fig_corr, use_container_width=True)

    def _show_correlation_analysis(self, symbols, stock_data):
        """显示相关性分析"""
        st.subheader("🔗 相关性分析")

        # 提取收盘价
        prices_data = {}
        for symbol in symbols:
            if symbol in stock_data and not stock_data[symbol].empty:
                prices_data[symbol] = stock_data[symbol]['Close']

        if len(prices_data) >= 2:
            prices_df = pd.DataFrame(prices_data)
            returns_df = prices_df.pct_change().dropna()

            # 相关性矩阵
            correlation = returns_df.corr()

            # 热力图
            fig_heatmap = px.imshow(
                correlation,
                labels=dict(color="相关系数"),
                title="股票收益率相关性热力图",
                color_continuous_scale='RdBu',
                aspect="auto",
                text_auto=True
            )
            fig_heatmap.update_traces(texttemplate='%{z:.2f}', textfont_size=12)
            st.plotly_chart(fig_heatmap, use_container_width=True)

            # 相关性表格
            st.subheader("📋 相关性矩阵")
            st.dataframe(correlation.round(3), use_container_width=True)

            # 分析说明
            st.subheader("📝 相关性分析说明")
            st.write("""
            - **相关系数范围**: -1 到 1
            - **接近1**: 正相关，两只股票同向变动
            - **接近-1**: 负相关，两只股票反向变动
            - **接近0**: 无明显相关性
            """)

    def _calculate_rsi(self, prices, period=14):
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal).mean()
        macd_histogram = macd_line - macd_signal
        return macd_line, macd_signal, macd_histogram

    def _calculate_max_drawdown(self, prices):
        """计算最大回撤"""
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return drawdown.min()

def main():
    """主函数"""
    try:
        dashboard = StockDashboard()
        dashboard.run()

        # 添加页脚
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>📈 QuantMuse 股票分析平台 | 基于 Streamlit 构建</p>
            <p>数据来源: Yahoo Finance | 仅供学习和研究使用</p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"应用运行错误: {str(e)}")
        st.info("请检查网络连接或刷新页面重试")

if __name__ == "__main__":
    main()
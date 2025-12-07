#!/usr/bin/env python3
"""
QuantMuse 专业股票分析平台 - 完整版
集成量化因子分析、预测判断和专业评分系统
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
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 页面配置
st.set_page_config(
    page_title="QuantMuse 专业股票分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        background: linear-gradient(45deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .score-excellent {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .score-good {
        background: linear-gradient(45deg, #17a2b8, #6f42c1);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .score-fair {
        background: linear-gradient(45deg, #ffc107, #fd7e14);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .score-poor {
        background: linear-gradient(45deg, #dc3545, #e83e8c);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .factor-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .prediction-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class ComprehensiveStockAnalyzer:
    """完整的股票分析器"""

    def __init__(self):
        # 扩展的股票列表 - 按市值分类
        self.stock_universe = {
            '超大盘股 (>$500B)': {
                'AAPL': '苹果公司',
                'MSFT': '微软公司',
                'GOOGL': '谷歌(Alphabet)',
                'AMZN': '亚马逊',
                'NVDA': '英伟达',
                'META': 'Meta(Facebook)',
                'TSLA': '特斯拉',
                'BRK-B': '伯克希尔哈撒韦'
            },
            '大盘股 ($100B-$500B)': {
                'JPM': '摩根大通',
                'JNJ': '强生公司',
                'V': 'Visa',
                'UNH': '联合健康',
                'WMT': '沃尔玛',
                'PG': '宝洁',
                'MA': '万事达',
                'HD': '家得宝',
                'NFLX': '网飞',
                'DIS': '迪士尼',
                'CRM': 'Salesforce',
                'ADBE': 'Adobe',
                'PYPL': 'PayPal',
                'INTC': '英特尔',
                'PFE': '辉瑞',
                'KO': '可口可乐',
                'PEP': '百事可乐'
            },
            '中盘股 ($10B-$100B)': {
                'BABA': '阿里巴巴',
                'COST': '好市多',
                'AVGO': '博通',
                'ORCL': '甲骨文',
                'TXN': '德州仪器',
                'QCOM': '高通',
                'AMT': '美国铁塔',
                'LOW': '劳氏',
                'SBUX': '星巴克',
                'MDT': '美敦力',
                'GILD': '吉利德科学',
                'ISRG': '直觉外科',
                'INTU': 'Intuit',
                'AMAT': '应用材料',
                'ADI': '亚德诺',
                'MU': '美光科技',
                'LRCX': '拉姆研究',
                'KLAC': 'KLA科技'
            },
            '小盘成长股 ($1B-$10B)': {
                'ROKU': 'Roku流媒体',
                'TDOC': 'Teladoc远程医疗',
                'ZM': 'Zoom视频',
                'PTON': 'Peloton健身',
                'PLTR': 'Palantir数据',
                'SNOW': 'Snowflake云计算',
                'CRWD': 'CrowdStrike网络安全',
                'OKTA': 'Okta身份管理',
                'TWLO': 'Twilio通讯',
                'SQ': 'Square支付',
                'SHOP': 'Shopify电商',
                'UBER': 'Uber出行',
                'LYFT': 'Lyft出行',
                'DOCU': 'DocuSign电子签名',
                'ZS': 'Zscaler云安全'
            }
        }

        # 行业分类
        self.sectors = {
            '科技股': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'NFLX', 'CRM', 'ADBE', 'INTC', 'ORCL', 'QCOM'],
            '金融股': ['JPM', 'V', 'MA', 'PYPL'],
            '消费股': ['AMZN', 'WMT', 'PG', 'HD', 'DIS', 'COST', 'LOW', 'SBUX'],
            '医疗股': ['JNJ', 'UNH', 'PFE', 'MDT', 'GILD', 'ISRG'],
            '云计算': ['MSFT', 'AMZN', 'CRM', 'SNOW', 'OKTA'],
            '新兴科技': ['TSLA', 'PLTR', 'CRWD', 'ZS', 'TWLO'],
            '消费科技': ['AAPL', 'META', 'NFLX', 'ROKU', 'ZM', 'UBER']
        }

    def calculate_comprehensive_factors(self, df, symbol):
        """计算全面的量化因子"""
        factors = {}

        if df.empty or len(df) < 252:
            return factors

        try:
            current_price = df['Close'].iloc[-1]
            prices = df['Close']
            volumes = df['Volume']

            # 1. 动量因子
            factors['momentum_20d'] = self._calculate_momentum(prices, 20)
            factors['momentum_60d'] = self._calculate_momentum(prices, 60)
            factors['momentum_252d'] = self._calculate_momentum(prices, 252)
            factors['relative_strength'] = self._calculate_rsi(prices)

            # 2. 技术因子
            factors['rsi'] = self._calculate_rsi(prices)
            factors['macd_signal'] = self._calculate_macd_signal(prices)
            factors['bollinger_position'] = self._calculate_bollinger_position(prices)
            factors['ma_signal'] = self._calculate_ma_signal(prices)

            # 3. 波动率因子
            factors['volatility_20d'] = self._calculate_volatility(prices, 20)
            factors['volatility_60d'] = self._calculate_volatility(prices, 60)
            factors['price_stability'] = self._calculate_price_stability(prices)

            # 4. 成交量因子
            factors['volume_trend'] = self._calculate_volume_trend(volumes)
            factors['volume_price_trend'] = self._calculate_volume_price_trend(prices, volumes)

            # 5. 趋势因子
            factors['trend_strength'] = self._calculate_trend_strength(prices)
            factors['support_resistance'] = self._calculate_support_resistance(prices)

            # 6. 获取基本面数据
            fundamental_factors = self._get_fundamental_factors(symbol)
            factors.update(fundamental_factors)

        except Exception as e:
            st.warning(f"计算因子时出错: {str(e)}")

        return factors

    def _calculate_momentum(self, prices, period):
        """计算动量因子"""
        if len(prices) < period:
            return 0
        return (prices.iloc[-1] / prices.iloc[-period] - 1) * 100

    def _calculate_rsi(self, prices, period=14):
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50

    def _calculate_macd_signal(self, prices):
        """计算MACD信号"""
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()

        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]

        if current_macd > current_signal:
            return 1  # 买入信号
        elif current_macd < current_signal:
            return -1  # 卖出信号
        else:
            return 0  # 中性

    def _calculate_bollinger_position(self, prices, period=20):
        """计算布林带位置"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = ma + (2 * std)
        lower = ma - (2 * std)

        current_price = prices.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]

        # 返回价格在布林带中的相对位置 (0-100)
        position = (current_price - current_lower) / (current_upper - current_lower) * 100
        return min(max(position, 0), 100)

    def _calculate_ma_signal(self, prices):
        """计算移动平均信号"""
        ma5 = prices.rolling(window=5).mean().iloc[-1]
        ma20 = prices.rolling(window=20).mean().iloc[-1]
        ma50 = prices.rolling(window=50).mean().iloc[-1]
        current_price = prices.iloc[-1]

        score = 0
        if current_price > ma5:
            score += 1
        if current_price > ma20:
            score += 1
        if current_price > ma50:
            score += 1
        if ma5 > ma20:
            score += 1
        if ma20 > ma50:
            score += 1

        return score  # 0-5分

    def _calculate_volatility(self, prices, period):
        """计算波动率"""
        returns = prices.pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252) * 100
        return volatility.iloc[-1] if not volatility.empty else 0

    def _calculate_price_stability(self, prices, period=30):
        """计算价格稳定性"""
        if len(prices) < period:
            return 0

        recent_prices = prices.tail(period)
        volatility = recent_prices.pct_change().std()
        return max(0, 100 - volatility * 1000)  # 转换为0-100分

    def _calculate_volume_trend(self, volumes, period=20):
        """计算成交量趋势"""
        if len(volumes) < period * 2:
            return 0

        recent_avg = volumes.tail(period).mean()
        previous_avg = volumes.tail(period * 2).head(period).mean()

        return (recent_avg / previous_avg - 1) * 100

    def _calculate_volume_price_trend(self, prices, volumes):
        """计算量价关系"""
        if len(prices) < 2 or len(volumes) < 2:
            return 0

        price_change = prices.pct_change()
        volume_change = volumes.pct_change()

        correlation = price_change.corr(volume_change)
        return correlation * 100 if not pd.isna(correlation) else 0

    def _calculate_trend_strength(self, prices, period=20):
        """计算趋势强度"""
        if len(prices) < period:
            return 0

        # 使用线性回归计算趋势强度
        x = np.arange(len(prices.tail(period)))
        y = prices.tail(period).values

        correlation = np.corrcoef(x, y)[0, 1]
        return abs(correlation) * 100 if not pd.isna(correlation) else 0

    def _calculate_support_resistance(self, prices, period=50):
        """计算支撑阻力强度"""
        if len(prices) < period:
            return 50

        current_price = prices.iloc[-1]
        recent_prices = prices.tail(period)

        # 计算当前价格相对于近期区间的位置
        price_min = recent_prices.min()
        price_max = recent_prices.max()

        position = (current_price - price_min) / (price_max - price_min) * 100
        return position

    def _get_fundamental_factors(self, symbol):
        """获取基本面因子"""
        factors = {}

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # 估值因子
            factors['pe_ratio'] = info.get('trailingPE', 0)
            factors['pb_ratio'] = info.get('priceToBook', 0)
            factors['ps_ratio'] = info.get('priceToSalesTrailing12Months', 0)
            factors['ev_ebitda'] = info.get('enterpriseToEbitda', 0)

            # 财务质量因子
            factors['roe'] = info.get('returnOnEquity', 0)
            factors['roa'] = info.get('returnOnAssets', 0)
            factors['profit_margin'] = info.get('profitMargins', 0)
            factors['debt_to_equity'] = info.get('debtToEquity', 0)

            # 分红和收益
            factors['dividend_yield'] = info.get('dividendYield', 0)
            factors['payout_ratio'] = info.get('payoutRatio', 0)

            # 成长因子
            factors['revenue_growth'] = info.get('revenueGrowth', 0)
            factors['earnings_growth'] = info.get('earningsGrowth', 0)

            # 市场因子
            factors['market_cap'] = info.get('marketCap', 0)
            factors['beta'] = info.get('beta', 1)

        except Exception as e:
            st.warning(f"获取基本面数据时出错: {str(e)}")

        return factors

    def calculate_comprehensive_score(self, factors):
        """计算综合评分"""
        scores = {}

        # 动量评分 (0-100)
        momentum_score = 0
        if 'momentum_20d' in factors:
            momentum_score += min(max(factors['momentum_20d'], -50), 50) + 50  # 标准化到0-100
        if 'momentum_60d' in factors:
            momentum_score += min(max(factors['momentum_60d'], -100), 100) / 2 + 50
        scores['momentum'] = momentum_score / 2

        # 技术评分 (0-100)
        technical_score = 0
        if 'rsi' in factors:
            # RSI在30-70之间得分较高
            rsi = factors['rsi']
            if 30 <= rsi <= 70:
                technical_score += 80
            elif rsi > 70:
                technical_score += max(0, 100 - (rsi - 70) * 2)
            else:
                technical_score += max(0, rsi / 30 * 80)

        if 'ma_signal' in factors:
            technical_score += factors['ma_signal'] * 20  # 0-5分 -> 0-100分

        if 'macd_signal' in factors:
            technical_score += (factors['macd_signal'] + 1) * 50  # -1,0,1 -> 0,50,100

        scores['technical'] = technical_score / 3

        # 估值评分 (0-100) - 越低越好
        valuation_score = 50  # 默认中性
        if 'pe_ratio' in factors and factors['pe_ratio'] > 0:
            pe = factors['pe_ratio']
            if pe < 15:
                valuation_score = 90
            elif pe < 25:
                valuation_score = 70
            elif pe < 35:
                valuation_score = 50
            else:
                valuation_score = 30
        scores['valuation'] = valuation_score

        # 质量评分 (0-100)
        quality_score = 50
        if 'roe' in factors and factors['roe']:
            roe = factors['roe'] * 100  # 转换为百分比
            quality_score = min(max(roe * 5, 0), 100)  # ROE > 20%得满分
        scores['quality'] = quality_score

        # 综合评分
        total_score = (
            scores['momentum'] * 0.3 +
            scores['technical'] * 0.3 +
            scores['valuation'] * 0.2 +
            scores['quality'] * 0.2
        )

        scores['total'] = total_score
        return scores

    def generate_prediction(self, factors, scores):
        """生成预测判断"""
        total_score = scores.get('total', 50)

        # 基于综合评分给出预测
        if total_score >= 80:
            prediction = "强烈买入"
            confidence = "高"
            reason = "综合评分优秀，动量强劲，技术指标积极"
            color_class = "score-excellent"
        elif total_score >= 65:
            prediction = "买入"
            confidence = "中高"
            reason = "综合评分良好，多数指标积极"
            color_class = "score-good"
        elif total_score >= 45:
            prediction = "持有"
            confidence = "中等"
            reason = "综合评分中性，建议观望"
            color_class = "score-fair"
        elif total_score >= 30:
            prediction = "谨慎"
            confidence = "中低"
            reason = "综合评分偏弱，存在下行风险"
            color_class = "score-fair"
        else:
            prediction = "回避"
            confidence = "高"
            reason = "综合评分较差，建议回避"
            color_class = "score-poor"

        return {
            'prediction': prediction,
            'confidence': confidence,
            'reason': reason,
            'score': total_score,
            'color_class': color_class
        }

def main():
    """主函数"""
    analyzer = ComprehensiveStockAnalyzer()

    # 标题
    st.markdown('<h1 class="main-header">📊 QuantMuse 专业股票分析平台</h1>', unsafe_allow_html=True)

    # 功能介绍
    st.markdown("""
    <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 1rem; border-radius: 15px; margin-bottom: 2rem;'>
        <h3>🚀 集成量化因子分析 | 🎯 专业预测判断 | 📈 全面技术指标</h3>
        <p>涵盖80+股票，6大量化因子，智能评分系统</p>
    </div>
    """, unsafe_allow_html=True)

    # 侧边栏
    st.sidebar.title("🎛️ 专业分析控制台")

    # 股票选择方式
    selection_method = st.sidebar.radio(
        "选择分析方式",
        ["按市值分类选择", "按行业分类选择", "直接输入股票代码"]
    )

    selected_symbol = None

    if selection_method == "按市值分类选择":
        market_cap_category = st.sidebar.selectbox(
            "选择市值分类",
            list(analyzer.stock_universe.keys())
        )

        stocks_in_category = analyzer.stock_universe[market_cap_category]
        selected_symbol = st.sidebar.selectbox(
            f"选择{market_cap_category}股票",
            list(stocks_in_category.keys()),
            format_func=lambda x: f"{x} - {stocks_in_category[x]}"
        )

    elif selection_method == "按行业分类选择":
        sector = st.sidebar.selectbox(
            "选择行业分类",
            list(analyzer.sectors.keys())
        )

        stocks_in_sector = analyzer.sectors[sector]
        # 获取股票名称
        all_stocks = {}
        for category in analyzer.stock_universe.values():
            all_stocks.update(category)

        selected_symbol = st.sidebar.selectbox(
            f"选择{sector}股票",
            stocks_in_sector,
            format_func=lambda x: f"{x} - {all_stocks.get(x, x)}"
        )

    else:  # 直接输入
        selected_symbol = st.sidebar.text_input(
            "输入股票代码",
            value="AAPL",
            help="输入美股代码，如: AAPL, MSFT, GOOGL"
        ).upper()

    # 时间范围
    time_range = st.sidebar.selectbox(
        "分析时间范围",
        ["3个月", "6个月", "1年", "2年", "3年"]
    )

    time_mapping = {"3个月": 90, "6个月": 180, "1年": 365, "2年": 730, "3年": 1095}
    days = time_mapping[time_range]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 分析选项
    st.sidebar.subheader("🔬 分析选项")
    show_factors = st.sidebar.checkbox("显示量化因子分析", True)
    show_prediction = st.sidebar.checkbox("显示预测判断", True)
    show_technical = st.sidebar.checkbox("显示技术分析", True)
    show_comparison = st.sidebar.checkbox("显示基准对比", False)

    if not selected_symbol:
        st.warning("请选择一只股票进行分析")
        return

    # 获取股票名称
    all_stocks = {}
    for category in analyzer.stock_universe.values():
        all_stocks.update(category)
    stock_name = all_stocks.get(selected_symbol, selected_symbol)

    # 主分析区域
    st.header(f"📈 {selected_symbol} - {stock_name} 专业分析报告")

    # 获取数据
    with st.spinner(f"正在获取 {selected_symbol} 的数据和进行量化分析..."):
        try:
            ticker = yf.Ticker(selected_symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                st.error("❌ 无法获取股票数据，请检查股票代码")
                return

            # 计算量化因子
            factors = analyzer.calculate_comprehensive_factors(df, selected_symbol)

            # 计算评分
            scores = analyzer.calculate_comprehensive_score(factors)

            # 生成预测
            prediction = analyzer.generate_prediction(factors, scores)

        except Exception as e:
            st.error(f"❌ 数据获取失败: {str(e)}")
            return

    # 显示基本信息和核心指标
    current_price = df['Close'].iloc[-1]
    start_price = df['Close'].iloc[0]
    total_return = (current_price - start_price) / start_price

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("当前价格", f"${current_price:.2f}")
    with col2:
        st.metric("期间收益", f"{total_return:+.2%}")
    with col3:
        st.metric("最高价", f"${df['High'].max():.2f}")
    with col4:
        st.metric("最低价", f"${df['Low'].min():.2f}")
    with col5:
        avg_volume = df['Volume'].mean()
        st.metric("平均成交量", f"{avg_volume:,.0f}")

    # 预测判断卡片
    if show_prediction:
        st.markdown(f"""
        <div class="prediction-card">
            <h2>🎯 量化预测判断</h2>
            <div style="font-size: 2rem; margin: 1rem 0;">
                <span class="{prediction['color_class']}">{prediction['prediction']}</span>
            </div>
            <p style="font-size: 1.2rem;"><strong>综合评分:</strong> {prediction['score']:.1f}/100</p>
            <p style="font-size: 1.1rem;"><strong>置信度:</strong> {prediction['confidence']}</p>
            <p style="font-size: 1rem;"><strong>分析理由:</strong> {prediction['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

    # 创建标签页
    if show_factors or show_technical:
        tabs = []
        if show_technical:
            tabs.append("📈 技术分析")
        if show_factors:
            tabs.append("🔬 量化因子")
        if show_comparison:
            tabs.append("📊 基准对比")
        tabs.append("📋 详细数据")

        if len(tabs) > 1:
            tab_objects = st.tabs(tabs)
            tab_index = 0

            if show_technical:
                with tab_objects[tab_index]:
                    show_technical_analysis(df, selected_symbol)
                tab_index += 1

            if show_factors:
                with tab_objects[tab_index]:
                    show_factor_analysis(factors, scores)
                tab_index += 1

            if show_comparison:
                with tab_objects[tab_index]:
                    show_benchmark_comparison(df, selected_symbol)
                tab_index += 1

            with tab_objects[tab_index]:
                show_detailed_data(df, factors)
        else:
            if show_technical:
                show_technical_analysis(df, selected_symbol)
            if show_factors:
                show_factor_analysis(factors, scores)

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📊 QuantMuse 专业股票分析平台 | 基于量化因子分析和机器学习</p>
        <p>数据来源: Yahoo Finance | 仅供学习研究使用，不构成投资建议</p>
    </div>
    """, unsafe_allow_html=True)

def show_technical_analysis(df, symbol):
    """显示技术分析"""
    st.subheader("📈 专业技术分析")

    # 价格图表
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} 价格走势', 'RSI指标', 'MACD指标', '成交量'),
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )

    # 价格和移动平均线
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='收盘价', line=dict(color='#1f77b4', width=2)), row=1, col=1)

    ma5 = df['Close'].rolling(window=5).mean()
    ma20 = df['Close'].rolling(window=20).mean()
    ma50 = df['Close'].rolling(window=50).mean()

    fig.add_trace(go.Scatter(x=df.index, y=ma5, name='MA5', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', line=dict(color='red', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ma50, name='MA50', line=dict(color='purple', width=1)), row=1, col=1)

    # 布林带
    bb_middle = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    bb_upper = bb_middle + (bb_std * 2)
    bb_lower = bb_middle - (bb_std * 2)

    fig.add_trace(go.Scatter(x=df.index, y=bb_upper, name='布林带上轨',
                            line=dict(color='gray', dash='dash'), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bb_lower, name='布林带下轨',
                            line=dict(color='gray', dash='dash'), fill='tonexty',
                            fillcolor='rgba(128,128,128,0.1)', showlegend=False), row=1, col=1)

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    fig.add_trace(go.Scatter(x=df.index, y=rsi, name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    histogram = macd - signal

    fig.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='red')), row=3, col=1)
    fig.add_trace(go.Bar(x=df.index, y=histogram, name='Histogram', marker_color='green', showlegend=False), row=3, col=1)

    # 成交量
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量',
                        marker_color='rgba(0, 128, 255, 0.6)', showlegend=False), row=4, col=1)

    fig.update_layout(height=800, title=f"{symbol} 完整技术分析")
    st.plotly_chart(fig, use_container_width=True)

def show_factor_analysis(factors, scores):
    """显示量化因子分析"""
    st.subheader("🔬 量化因子深度分析")

    # 评分概览
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        momentum_score = scores.get('momentum', 50)
        st.markdown(f"""
        <div class="factor-card">
            <h4>📈 动量评分</h4>
            <h2>{momentum_score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        technical_score = scores.get('technical', 50)
        st.markdown(f"""
        <div class="factor-card">
            <h4>🔧 技术评分</h4>
            <h2>{technical_score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        valuation_score = scores.get('valuation', 50)
        st.markdown(f"""
        <div class="factor-card">
            <h4>💰 估值评分</h4>
            <h2>{valuation_score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        quality_score = scores.get('quality', 50)
        st.markdown(f"""
        <div class="factor-card">
            <h4>⭐ 质量评分</h4>
            <h2>{quality_score:.1f}/100</h2>
        </div>
        """, unsafe_allow_html=True)

    # 详细因子分析
    st.subheader("📊 详细因子数据")

    # 动量因子
    st.write("**📈 动量因子**")
    momentum_data = {
        '因子': ['20日动量', '60日动量', '252日动量', 'RSI'],
        '数值': [
            f"{factors.get('momentum_20d', 0):.2f}%",
            f"{factors.get('momentum_60d', 0):.2f}%",
            f"{factors.get('momentum_252d', 0):.2f}%",
            f"{factors.get('rsi', 50):.1f}"
        ],
        '评级': [
            '🟢 强势' if factors.get('momentum_20d', 0) > 5 else '🔴 弱势' if factors.get('momentum_20d', 0) < -5 else '🟡 中性',
            '🟢 强势' if factors.get('momentum_60d', 0) > 10 else '🔴 弱势' if factors.get('momentum_60d', 0) < -10 else '🟡 中性',
            '🟢 强势' if factors.get('momentum_252d', 0) > 20 else '🔴 弱势' if factors.get('momentum_252d', 0) < -20 else '🟡 中性',
            '🟢 中性' if 30 <= factors.get('rsi', 50) <= 70 else '🔴 极端' if factors.get('rsi', 50) > 80 or factors.get('rsi', 50) < 20 else '🟡 偏离'
        ]
    }
    st.dataframe(pd.DataFrame(momentum_data), use_container_width=True)

    # 基本面因子
    if any(k in factors for k in ['pe_ratio', 'pb_ratio', 'roe', 'debt_to_equity']):
        st.write("**💰 基本面因子**")
        fundamental_data = {
            '因子': [],
            '数值': [],
            '评级': []
        }

        if 'pe_ratio' in factors and factors['pe_ratio']:
            fundamental_data['因子'].append('市盈率(PE)')
            fundamental_data['数值'].append(f"{factors['pe_ratio']:.1f}")
            pe = factors['pe_ratio']
            if pe < 15:
                fundamental_data['评级'].append('🟢 便宜')
            elif pe < 25:
                fundamental_data['评级'].append('🟡 合理')
            else:
                fundamental_data['评级'].append('🔴 昂贵')

        if 'pb_ratio' in factors and factors['pb_ratio']:
            fundamental_data['因子'].append('市净率(PB)')
            fundamental_data['数值'].append(f"{factors['pb_ratio']:.1f}")
            pb = factors['pb_ratio']
            if pb < 2:
                fundamental_data['评级'].append('🟢 便宜')
            elif pb < 4:
                fundamental_data['评级'].append('🟡 合理')
            else:
                fundamental_data['评级'].append('🔴 昂贵')

        if 'roe' in factors and factors['roe']:
            fundamental_data['因子'].append('净资产收益率(ROE)')
            fundamental_data['数值'].append(f"{factors['roe']*100:.1f}%")
            roe = factors['roe'] * 100
            if roe > 15:
                fundamental_data['评级'].append('🟢 优秀')
            elif roe > 10:
                fundamental_data['评级'].append('🟡 良好')
            else:
                fundamental_data['评级'].append('🔴 一般')

        if fundamental_data['因子']:
            st.dataframe(pd.DataFrame(fundamental_data), use_container_width=True)

def show_benchmark_comparison(df, symbol):
    """显示基准对比"""
    st.subheader("📊 基准指数对比")

    benchmark = st.selectbox(
        "选择基准指数",
        ["SPY", "QQQ", "^GSPC", "^DJI"],
        format_func=lambda x: {
            "SPY": "标普500 ETF",
            "QQQ": "纳斯达克100 ETF",
            "^GSPC": "标普500指数",
            "^DJI": "道琼斯指数"
        }.get(x, x)
    )

    try:
        benchmark_ticker = yf.Ticker(benchmark)
        benchmark_df = benchmark_ticker.history(start=df.index[0], end=df.index[-1])

        if not benchmark_df.empty:
            # 标准化收益率
            stock_returns = (df['Close'] / df['Close'].iloc[0] - 1) * 100
            benchmark_returns = (benchmark_df['Close'] / benchmark_df['Close'].iloc[0] - 1) * 100

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=stock_returns.index, y=stock_returns,
                                   name=f'{symbol}', line=dict(color='blue', width=2)))
            fig.add_trace(go.Scatter(x=benchmark_returns.index, y=benchmark_returns,
                                   name=benchmark, line=dict(color='red', width=2)))

            fig.update_layout(
                title=f"{symbol} vs {benchmark} 收益率对比",
                yaxis_title="累计收益率 (%)",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            # 对比指标
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{symbol} 总收益", f"{stock_returns.iloc[-1]:.2f}%")
            with col2:
                st.metric(f"{benchmark} 总收益", f"{benchmark_returns.iloc[-1]:.2f}%")
            with col3:
                alpha = stock_returns.iloc[-1] - benchmark_returns.iloc[-1]
                st.metric("Alpha (超额收益)", f"{alpha:+.2f}%")

    except Exception as e:
        st.error(f"无法获取基准数据: {str(e)}")

def show_detailed_data(df, factors):
    """显示详细数据"""
    st.subheader("📋 详细数据表")

    # 最近价格数据
    st.write("**最近价格数据**")
    st.dataframe(df.tail(10).round(2), use_container_width=True)

    # 因子数据下载
    if factors:
        factor_df = pd.DataFrame([factors]).T
        factor_df.columns = ['数值']
        factor_df.index.name = '因子名称'

        st.write("**量化因子数据**")
        st.dataframe(factor_df, use_container_width=True)

        # 下载按钮
        csv = df.to_csv()
        st.download_button(
            label="📥 下载价格数据 (CSV)",
            data=csv,
            file_name=f"{st.session_state.get('selected_symbol', 'stock')}_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
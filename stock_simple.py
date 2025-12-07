#!/usr/bin/env python3
"""
QuantMuse 股票分析网站 - 简化版本
测试版本，确保基本功能正常运行
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(
    page_title="QuantMuse 股票分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
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
    }
</style>
""", unsafe_allow_html=True)

def main():
    """主函数"""
    # 标题
    st.markdown('<h1 class="main-header">📈 QuantMuse 股票分析平台</h1>', unsafe_allow_html=True)

    # 测试连接
    st.success("🎉 网站连接成功！")

    # 侧边栏
    st.sidebar.title("🎛️ 股票选择")

    # 热门股票列表
    popular_stocks = {
        'AAPL': '苹果公司',
        'MSFT': '微软公司',
        'GOOGL': '谷歌',
        'TSLA': '特斯拉',
        'NVDA': '英伟达',
        'META': 'Meta'
    }

    # 股票选择
    selected_symbol = st.sidebar.selectbox(
        "选择股票进行分析",
        list(popular_stocks.keys()),
        format_func=lambda x: f"{x} - {popular_stocks[x]}"
    )

    # 时间范围选择
    time_range = st.sidebar.selectbox(
        "选择时间范围",
        ["1个月", "3个月", "6个月", "1年"]
    )

    time_mapping = {"1个月": 30, "3个月": 90, "6个月": 180, "1年": 365}
    days = time_mapping[time_range]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 显示选中的股票信息
    st.header(f"📊 {selected_symbol} - {popular_stocks[selected_symbol]} 分析")

    # 获取数据按钮
    if st.button("🚀 获取股票数据", type="primary"):
        with st.spinner(f"正在获取 {selected_symbol} 的数据..."):
            try:
                # 获取股票数据
                ticker = yf.Ticker(selected_symbol)
                df = ticker.history(start=start_date, end=end_date)

                if df.empty:
                    st.error("❌ 无法获取股票数据")
                    return

                st.success(f"✅ 成功获取 {len(df)} 天的数据！")

                # 基本指标
                current_price = df['Close'].iloc[-1]
                start_price = df['Close'].iloc[0]
                total_return = (current_price - start_price) / start_price

                # 显示指标
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("当前价格", f"${current_price:.2f}")

                with col2:
                    st.metric("总收益率", f"{total_return:+.2%}")

                with col3:
                    high_price = df['High'].max()
                    st.metric("期间最高价", f"${high_price:.2f}")

                with col4:
                    low_price = df['Low'].min()
                    st.metric("期间最低价", f"${low_price:.2f}")

                # 价格图表
                st.subheader("📈 股价走势图")

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines',
                    name='收盘价',
                    line=dict(color='#1f77b4', width=2)
                ))

                # 添加移动平均线
                ma20 = df['Close'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=ma20,
                    mode='lines',
                    name='20日均线',
                    line=dict(color='orange', width=1)
                ))

                fig.update_layout(
                    title=f"{selected_symbol} 股价走势",
                    xaxis_title="日期",
                    yaxis_title="价格 ($)",
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)

                # 成交量图表
                st.subheader("📊 成交量分析")

                fig_vol = go.Figure()
                fig_vol.add_trace(go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='成交量',
                    marker_color='rgba(0, 128, 255, 0.6)'
                ))

                fig_vol.update_layout(
                    title=f"{selected_symbol} 成交量",
                    xaxis_title="日期",
                    yaxis_title="成交量",
                    height=400
                )

                st.plotly_chart(fig_vol, use_container_width=True)

                # 数据表格
                st.subheader("📋 最近数据")
                st.dataframe(df.tail(10).round(2), use_container_width=True)

                # 下载数据
                csv = df.to_csv()
                st.download_button(
                    label="📥 下载CSV数据",
                    data=csv,
                    file_name=f"{selected_symbol}_stock_data.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"❌ 获取数据时出错: {str(e)}")
                st.info("💡 请检查网络连接或稍后重试")

    # 功能说明
    else:
        st.info("👆 请点击上方按钮获取股票数据")

        st.subheader("🌟 网站功能")
        col1, col2 = st.columns(2)

        with col1:
            st.write("📈 **数据功能**")
            st.write("• 实时股票价格")
            st.write("• 历史数据分析")
            st.write("• 技术指标计算")
            st.write("• 成交量分析")

        with col2:
            st.write("🔧 **分析工具**")
            st.write("• 价格走势图表")
            st.write("• 移动平均线")
            st.write("• 数据下载功能")
            st.write("• 交互式图表")

    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📈 QuantMuse 股票分析平台 | 基于 Streamlit 构建</p>
        <p>数据来源: Yahoo Finance | 仅供学习研究使用</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
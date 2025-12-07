#!/usr/bin/env python3
"""
股票数据分析教程
QuantMuse股票版 - 从加密货币扩展到股票市场
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from data_service.fetchers.yahoo_fetcher import YahooFetcher
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def get_stock_data_basic():
    """基础股票数据获取 - 使用yfinance直接方式"""
    print("📈 方法1: 直接使用yfinance获取股票数据")
    print("="*50)

    # 热门股票列表
    popular_stocks = {
        'AAPL': '苹果公司',
        'MSFT': '微软公司',
        'GOOGL': '谷歌(Alphabet)',
        'AMZN': '亚马逊',
        'TSLA': '特斯拉',
        'NVDA': '英伟达',
        'META': 'Meta(Facebook)',
        'JPM': '摩根大通',
        'JNJ': '强生公司',
        'V': 'Visa'
    }

    print("🔥 热门美股列表:")
    for symbol, name in popular_stocks.items():
        print(f"  {symbol}: {name}")

    # 选择一只股票进行分析
    stock_symbol = 'AAPL'  # 苹果公司
    print(f"\n📊 开始分析: {stock_symbol} - {popular_stocks[stock_symbol]}")

    # 获取过去一年的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    try:
        # 直接使用yfinance获取数据
        stock = yf.Ticker(stock_symbol)
        df = stock.history(start=start_date, end=end_date)

        print(f"✅ 成功获取 {len(df)} 天的股票数据")
        print(f"📅 数据范围: {df.index[0].strftime('%Y-%m-%d')} 到 {df.index[-1].strftime('%Y-%m-%d')}")

        # 显示基本信息
        print(f"\n💰 当前股价: ${df['Close'].iloc[-1]:.2f}")
        print(f"📈 最高价: ${df['High'].max():.2f}")
        print(f"📉 最低价: ${df['Low'].min():.2f}")
        print(f"📊 平均价: ${df['Close'].mean():.2f}")

        # 获取公司基本信息
        info = stock.info
        print(f"\n🏢 公司信息:")
        print(f"  公司全名: {info.get('longName', 'N/A')}")
        print(f"  行业: {info.get('industry', 'N/A')}")
        print(f"  市值: ${info.get('marketCap', 0):,}")
        print(f"  市盈率: {info.get('trailingPE', 'N/A')}")

        return df, stock_symbol

    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return None, None

def get_stock_data_with_fetcher():
    """使用QuantMuse的YahooFetcher获取股票数据"""
    print("\n🏗️ 方法2: 使用QuantMuse YahooFetcher")
    print("="*50)

    try:
        # 使用QuantMuse的fetcher
        fetcher = YahooFetcher()

        # 获取苹果股票数据
        symbol = 'AAPL'
        df = fetcher.fetch_historical_data(
            symbol=symbol,
            start_time=datetime.now() - timedelta(days=365),
            end_time=datetime.now()
        )

        print(f"✅ 通过QuantMuse Fetcher获取 {len(df)} 天数据")

        # 获取公司信息
        company_info = fetcher.get_company_info(symbol)
        print(f"\n🏢 公司信息 (通过Fetcher):")
        for key, value in company_info.items():
            print(f"  {key}: {value}")

        return df

    except Exception as e:
        print(f"❌ Fetcher获取失败: {e}")
        return None

def analyze_multiple_stocks():
    """多只股票对比分析"""
    print("\n📊 方法3: 多只股票对比分析")
    print("="*50)

    # 科技股组合
    tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    stock_names = {
        'AAPL': '苹果',
        'MSFT': '微软',
        'GOOGL': '谷歌',
        'AMZN': '亚马逊',
        'META': 'Meta'
    }

    print(f"🔬 分析科技股组合: {', '.join(tech_stocks)}")

    # 获取所有股票数据
    all_data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    for symbol in tech_stocks:
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_date, end=end_date)
            all_data[symbol] = df['Close']
            print(f"✅ {symbol}({stock_names[symbol]}): {len(df)} 天数据")
        except Exception as e:
            print(f"❌ {symbol} 获取失败: {e}")

    if not all_data:
        print("❌ 没有成功获取任何股票数据")
        return None

    # 合并数据
    combined_df = pd.DataFrame(all_data)

    # 计算涨跌幅
    print(f"\n📈 过去一年涨跌幅:")
    for symbol in combined_df.columns:
        if len(combined_df[symbol].dropna()) > 0:
            start_price = combined_df[symbol].dropna().iloc[0]
            end_price = combined_df[symbol].dropna().iloc[-1]
            change_pct = (end_price - start_price) / start_price * 100
            print(f"  {symbol}({stock_names[symbol]}): {change_pct:.2f}%")

    # 计算相关性
    correlation = combined_df.corr()
    print(f"\n🔗 股票相关性矩阵:")
    print(correlation.round(3))

    return combined_df

def technical_analysis(df, symbol):
    """技术分析指标"""
    print(f"\n🔧 技术分析: {symbol}")
    print("="*40)

    if df is None or df.empty:
        print("❌ 没有数据进行技术分析")
        return None

    # 计算技术指标
    df_analysis = df.copy()

    # 1. 移动平均线
    df_analysis['MA5'] = df_analysis['Close'].rolling(window=5).mean()
    df_analysis['MA20'] = df_analysis['Close'].rolling(window=20).mean()
    df_analysis['MA50'] = df_analysis['Close'].rolling(window=50).mean()

    # 2. 相对强弱指标 (RSI)
    delta = df_analysis['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_analysis['RSI'] = 100 - (100 / (1 + rs))

    # 3. 布林带
    df_analysis['BB_middle'] = df_analysis['Close'].rolling(window=20).mean()
    bb_std = df_analysis['Close'].rolling(window=20).std()
    df_analysis['BB_upper'] = df_analysis['BB_middle'] + (bb_std * 2)
    df_analysis['BB_lower'] = df_analysis['BB_middle'] - (bb_std * 2)

    # 4. MACD
    exp1 = df_analysis['Close'].ewm(span=12).mean()
    exp2 = df_analysis['Close'].ewm(span=26).mean()
    df_analysis['MACD'] = exp1 - exp2
    df_analysis['MACD_signal'] = df_analysis['MACD'].ewm(span=9).mean()

    # 显示最新指标
    latest = df_analysis.iloc[-1]
    print(f"📊 最新技术指标:")
    print(f"  当前价格: ${latest['Close']:.2f}")
    print(f"  MA5: ${latest['MA5']:.2f}")
    print(f"  MA20: ${latest['MA20']:.2f}")
    print(f"  MA50: ${latest['MA50']:.2f}")
    print(f"  RSI: {latest['RSI']:.2f}")
    print(f"  MACD: {latest['MACD']:.4f}")

    # 简单的交易信号
    print(f"\n🚦 交易信号分析:")

    # 移动平均信号
    if latest['Close'] > latest['MA20']:
        print("  🟢 价格高于MA20，短期趋势向好")
    else:
        print("  🔴 价格低于MA20，短期趋势偏弱")

    # RSI信号
    if latest['RSI'] > 70:
        print("  ⚠️ RSI > 70，可能超买")
    elif latest['RSI'] < 30:
        print("  📈 RSI < 30，可能超卖")
    else:
        print("  📊 RSI正常范围")

    # 布林带信号
    if latest['Close'] > latest['BB_upper']:
        print("  ⚠️ 价格突破布林带上轨，注意回调风险")
    elif latest['Close'] < latest['BB_lower']:
        print("  📈 价格跌破布林带下轨，可能反弹机会")

    return df_analysis

def create_visualization(df, symbol):
    """创建股票图表可视化"""
    print(f"\n📈 创建图表: {symbol}")
    print("="*40)

    if df is None or df.empty:
        print("❌ 没有数据创建图表")
        return

    try:
        # 创建子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'{symbol} 股票技术分析图表', fontsize=16)

        # 1. 价格和移动平均线
        ax1.plot(df.index, df['Close'], label='收盘价', alpha=0.7)
        if 'MA5' in df.columns:
            ax1.plot(df.index, df['MA5'], label='MA5', alpha=0.8)
        if 'MA20' in df.columns:
            ax1.plot(df.index, df['MA20'], label='MA20', alpha=0.8)
        ax1.set_title('价格走势图')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. 成交量
        ax2.bar(df.index, df['Volume'], alpha=0.6, color='orange')
        ax2.set_title('成交量')
        ax2.grid(True, alpha=0.3)

        # 3. RSI
        if 'RSI' in df.columns:
            ax3.plot(df.index, df['RSI'])
            ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线')
            ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线')
            ax3.set_title('RSI 相对强弱指标')
            ax3.set_ylim(0, 100)
            ax3.legend()
            ax3.grid(True, alpha=0.3)

        # 4. MACD
        if 'MACD' in df.columns and 'MACD_signal' in df.columns:
            ax4.plot(df.index, df['MACD'], label='MACD', alpha=0.8)
            ax4.plot(df.index, df['MACD_signal'], label='Signal', alpha=0.8)
            ax4.bar(df.index, df['MACD'] - df['MACD_signal'],
                   alpha=0.3, label='Histogram')
            ax4.set_title('MACD')
            ax4.legend()
            ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存图表
        filename = f'{symbol}_stock_analysis.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"✅ 图表已保存: {filename}")

        # 显示图表（如果在支持的环境中）
        # plt.show()
        plt.close()

    except Exception as e:
        print(f"❌ 创建图表失败: {e}")

def main():
    """主函数"""
    print("🎯 QuantMuse 股票数据分析教程")
    print("从加密货币扩展到股票市场分析")
    print("="*60)

    try:
        # 方法1: 基础股票数据获取
        df, symbol = get_stock_data_basic()

        # 方法2: 使用QuantMuse Fetcher
        df_fetcher = get_stock_data_with_fetcher()

        # 方法3: 多股票对比
        multi_stocks_df = analyze_multiple_stocks()

        if df is not None:
            # 技术分析
            df_with_indicators = technical_analysis(df, symbol)

            # 创建可视化
            if df_with_indicators is not None:
                create_visualization(df_with_indicators, symbol)

            # 保存数据
            df.to_csv(f'{symbol}_stock_data.csv')
            print(f"\n💾 {symbol} 数据已保存到 '{symbol}_stock_data.csv'")

        if multi_stocks_df is not None:
            multi_stocks_df.to_csv('tech_stocks_comparison.csv')
            print(f"💾 科技股对比数据已保存到 'tech_stocks_comparison.csv'")

        print("\n🎉 股票数据分析完成！")
        print("\n💡 你学会了:")
        print("  ✅ 如何获取美股实时和历史数据")
        print("  ✅ 如何使用QuantMuse的YahooFetcher")
        print("  ✅ 如何进行多股票对比分析")
        print("  ✅ 如何计算技术分析指标")
        print("  ✅ 如何生成交易信号")
        print("  ✅ 如何创建专业股票图表")

        print("\n🚀 下一步可以:")
        print("  📈 尝试分析不同行业的股票")
        print("  🔧 学习更多技术指标")
        print("  🤖 结合AI分析新闻情感")
        print("  💼 构建股票投资组合")

    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
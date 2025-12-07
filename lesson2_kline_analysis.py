#!/usr/bin/env python3
"""
第二课：学习K线数据和数据结构
K线 = 蜡烛图，是金融分析的基础
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# 设置中文字体，这样图表可以显示中文
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def get_ohlcv_data(symbol="bitcoin", days=30):
    """
    获取OHLCV数据 (Open, High, Low, Close, Volume)
    这是量化分析的标准数据格式！
    """
    print(f"📈 正在获取 {symbol} 过去 {days} 天的OHLCV数据...")
    
    # CoinGecko的OHLC端点
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/ohlc"
    params = {
        'vs_currency': 'usd',
        'days': days
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # 转换为DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)
        
        print(f"✅ 成功获取 {len(df)} 条K线数据")
        return df
        
    except Exception as e:
        print(f"❌ 获取OHLCV数据失败: {e}")
        return None

def explain_ohlcv(df):
    """
    解释OHLCV数据的含义
    这是理解K线的关键！
    """
    print("\n📚 什么是OHLCV数据？")
    print("="*50)
    
    if df is None or df.empty:
        print("❌ 没有数据")
        return
    
    # 取最新一根K线作为例子
    latest = df.iloc[-1]
    
    print(f"📊 最新K线数据解释（{df.index[-1].strftime('%Y-%m-%d')}）:")
    print(f"  🟢 Open (开盘价):  ${latest['open']:,.2f}")
    print(f"       ↪ 这一天开始交易时的价格")
    
    print(f"  🔴 High (最高价):  ${latest['high']:,.2f}")  
    print(f"       ↪ 这一天交易中的最高价格")
    
    print(f"  🔵 Low (最低价):   ${latest['low']:,.2f}")
    print(f"       ↪ 这一天交易中的最低价格")
    
    print(f"  ⚪ Close (收盘价): ${latest['close']:,.2f}")
    print(f"       ↪ 这一天结束交易时的价格")
    
    # 计算涨跌
    daily_change = latest['close'] - latest['open']
    daily_change_pct = (daily_change / latest['open']) * 100
    
    if daily_change > 0:
        print(f"  📈 当日涨跌: +${daily_change:,.2f} (+{daily_change_pct:.2f}%)")
        print(f"       ↪ 绿色K线（阳线）- 收盘价高于开盘价")
    else:
        print(f"  📉 当日涨跌: ${daily_change:,.2f} ({daily_change_pct:.2f}%)")
        print(f"       ↪ 红色K线（阴线）- 收盘价低于开盘价")
    
    # K线形态分析
    body_size = abs(latest['close'] - latest['open'])  # 实体大小
    total_range = latest['high'] - latest['low']       # 总范围
    upper_shadow = latest['high'] - max(latest['open'], latest['close'])  # 上影线
    lower_shadow = min(latest['open'], latest['close']) - latest['low']   # 下影线
    
    print(f"\n📏 K线形态分析:")
    print(f"  实体大小: ${body_size:,.2f} ({body_size/total_range*100:.1f}%)")
    print(f"  上影线长度: ${upper_shadow:,.2f}")
    print(f"  下影线长度: ${lower_shadow:,.2f}")
    
    # 判断K线类型
    if body_size / total_range > 0.6:
        print(f"  📊 形态判断: 大实体K线 - 趋势明确")
    elif body_size / total_range < 0.3:
        print(f"  📊 形态判断: 小实体K线 - 震荡整理")
    else:
        print(f"  📊 形态判断: 中等实体K线 - 正常交易")

def calculate_basic_indicators(df):
    """
    计算基础技术指标
    这是技术分析的入门！
    """
    print("\n🔧 计算基础技术指标...")
    
    if df is None or df.empty:
        return df
    
    # 1. 简单移动平均线 (SMA - Simple Moving Average)
    df['SMA_5'] = df['close'].rolling(window=5).mean()   # 5日均线
    df['SMA_10'] = df['close'].rolling(window=10).mean()  # 10日均线
    df['SMA_20'] = df['close'].rolling(window=20).mean()  # 20日均线
    
    print("✅ 移动平均线计算完成")
    print("   SMA_5 = 5日移动平均（短期趋势）")
    print("   SMA_10 = 10日移动平均（中期趋势）") 
    print("   SMA_20 = 20日移动平均（长期趋势）")
    
    # 2. 价格通道 (布林带的简化版)
    df['Price_Mean'] = df['close'].rolling(window=20).mean()
    df['Price_Std'] = df['close'].rolling(window=20).std()
    df['Upper_Band'] = df['Price_Mean'] + (df['Price_Std'] * 2)
    df['Lower_Band'] = df['Price_Mean'] - (df['Price_Std'] * 2)
    
    print("✅ 价格通道计算完成")
    print("   Upper_Band = 上轨（阻力位）")
    print("   Lower_Band = 下轨（支撑位）")
    
    # 3. 每日收益率
    df['Daily_Return'] = df['close'].pct_change() * 100
    
    print("✅ 收益率计算完成")
    print("   Daily_Return = 每日价格变化百分比")
    
    return df

def analyze_trends(df):
    """
    趋势分析 - 这是交易决策的基础
    """
    print("\n📈 趋势分析...")
    
    if df is None or df.empty or len(df) < 20:
        print("❌ 数据不足，无法分析趋势")
        return
    
    latest = df.iloc[-1]
    
    # 移动平均线趋势分析
    print("📊 移动平均线分析:")
    
    if not pd.isna(latest['SMA_5']) and not pd.isna(latest['SMA_10']) and not pd.isna(latest['SMA_20']):
        sma5 = latest['SMA_5']
        sma10 = latest['SMA_10'] 
        sma20 = latest['SMA_20']
        current_price = latest['close']
        
        print(f"  当前价格: ${current_price:,.2f}")
        print(f"  5日均线:  ${sma5:,.2f}")
        print(f"  10日均线: ${sma10:,.2f}")
        print(f"  20日均线: ${sma20:,.2f}")
        
        # 判断趋势
        if sma5 > sma10 > sma20 and current_price > sma5:
            trend = "🚀 强烈上升趋势"
            print(f"  {trend} - 短中长期均线多头排列")
        elif sma5 < sma10 < sma20 and current_price < sma5:
            trend = "📉 强烈下降趋势"
            print(f"  {trend} - 短中长期均线空头排列")
        elif current_price > sma20:
            trend = "📈 上升趋势"
            print(f"  {trend} - 价格在长期均线之上")
        elif current_price < sma20:
            trend = "📉 下降趋势"  
            print(f"  {trend} - 价格在长期均线之下")
        else:
            trend = "➡️ 震荡趋势"
            print(f"  {trend} - 价格在均线附近震荡")
    
    # 价格位置分析
    if not pd.isna(latest['Upper_Band']) and not pd.isna(latest['Lower_Band']):
        upper = latest['Upper_Band']
        lower = latest['Lower_Band']
        price = latest['close']
        
        print(f"\n📏 价格位置分析:")
        print(f"  上轨: ${upper:,.2f}")
        print(f"  下轨: ${lower:,.2f}")
        
        position = (price - lower) / (upper - lower)
        print(f"  价格位置: {position:.1%}")
        
        if position > 0.8:
            print(f"  💡 判断: 价格接近上轨，可能超买")
        elif position < 0.2:
            print(f"  💡 判断: 价格接近下轨，可能超卖")
        else:
            print(f"  💡 判断: 价格在正常区间")
    
    # 波动性分析
    recent_returns = df['Daily_Return'].dropna().tail(10)
    volatility = recent_returns.std()
    
    print(f"\n📊 波动性分析:")
    print(f"  近10日波动率: {volatility:.2f}%")
    
    if volatility > 5:
        print("  💡 高波动性 - 风险较大，也意味着机会较多")
    elif volatility < 2:
        print("  💡 低波动性 - 相对稳定，适合保守投资")
    else:
        print("  💡 中等波动性 - 正常的市场波动")

def create_simple_chart(df):
    """
    创建简单的价格图表
    """
    print("\n📊 生成价格图表...")
    
    if df is None or df.empty:
        print("❌ 没有数据可绘图")
        return
    
    try:
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 上图：价格和移动平均线
        ax1.plot(df.index, df['close'], label='收盘价', linewidth=2, color='black')
        ax1.plot(df.index, df['SMA_5'], label='5日均线', color='red', alpha=0.8)
        ax1.plot(df.index, df['SMA_10'], label='10日均线', color='blue', alpha=0.8)
        ax1.plot(df.index, df['SMA_20'], label='20日均线', color='green', alpha=0.8)
        
        # 添加价格通道
        if 'Upper_Band' in df.columns:
            ax1.fill_between(df.index, df['Upper_Band'], df['Lower_Band'], 
                           alpha=0.2, color='gray', label='价格通道')
        
        ax1.set_title('比特币价格走势与移动平均线', fontsize=14)
        ax1.set_ylabel('价格 (USD)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 下图：每日收益率
        colors = ['red' if x < 0 else 'green' for x in df['Daily_Return'].fillna(0)]
        ax2.bar(df.index, df['Daily_Return'], color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax2.set_title('每日收益率', fontsize=14)
        ax2.set_ylabel('收益率 (%)')
        ax2.set_xlabel('日期')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('btc_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("✅ 图表已保存为 'btc_analysis.png'")
        
    except Exception as e:
        print(f"❌ 绘图失败: {e}")

def main():
    """
    主函数：K线数据分析学习
    """
    print("🎯 量化交易学习第二课：K线数据分析")
    print("="*60)
    
    # 步骤1：获取K线数据
    df = get_ohlcv_data("bitcoin", 30)
    
    if df is None:
        print("❌ 无法获取数据，程序结束")
        return
    
    # 步骤2：解释OHLCV概念
    explain_ohlcv(df)
    
    # 步骤3：计算技术指标
    df = calculate_basic_indicators(df)
    
    # 步骤4：趋势分析
    analyze_trends(df)
    
    # 步骤5：保存数据
    df.to_csv('btc_ohlcv_data.csv')
    print(f"\n💾 完整数据已保存到 'btc_ohlcv_data.csv'")
    
    # 步骤6：显示数据表格
    print(f"\n📋 数据表格预览（最近5天）:")
    print(df[['open', 'high', 'low', 'close', 'SMA_5', 'SMA_20', 'Daily_Return']].tail().round(2))
    
    # 步骤7：生成图表（可选）
    try:
        create_simple_chart(df)
    except Exception as e:
        print(f"⚠️ 图表生成跳过: {e}")
    
    print("\n🎉 恭喜！你完成了K线数据分析学习！")
    print("\n💡 你现在理解了:")
    print("  1. OHLCV数据的含义（开高低收成交量）")
    print("  2. K线的基本形态和意义")
    print("  3. 移动平均线的计算和作用")
    print("  4. 价格通道和支撑阻力概念")
    print("  5. 趋势判断的基本方法")
    print("  6. 波动性分析")

if __name__ == "__main__":
    main()
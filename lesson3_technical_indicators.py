#!/usr/bin/env python3
"""
第三课：技术指标计算详解
手把手教你计算每一个技术指标！
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_prices():
    """
    生成简单的价格数据用于学习计算
    """
    print("📊 生成示例价格数据...")
    
    # 简单的价格序列，便于手工验证计算
    prices = [100, 102, 101, 105, 107, 106, 108, 110, 109, 112, 
              115, 113, 116, 118, 117, 120, 119, 121, 123, 122]
    
    dates = pd.date_range(start='2024-01-01', periods=len(prices), freq='D')
    df = pd.DataFrame({'close': prices}, index=dates)
    
    print(f"✅ 生成了 {len(df)} 天的价格数据")
    print("原始价格序列:")
    for i, (date, price) in enumerate(zip(df.index, df['close'])):
        print(f"  第{i+1:2d}天 ({date.strftime('%m-%d')}): ${price}")
    
    return df

def learn_simple_moving_average(df):
    """
    详细学习移动平均线计算
    这是最基础也是最重要的指标！
    """
    print(f"\n📚 第一个指标：简单移动平均线 (SMA)")
    print("="*60)
    
    print("💡 移动平均线是什么？")
    print("   就是把过去N天的价格加起来，然后除以N天")
    print("   比如5日均线 = (今天+昨天+前天+大前天+大大前天) ÷ 5")
    
    # 手工计算5日移动平均
    print(f"\n🧮 让我们手工计算5日移动平均线：")
    
    prices = df['close'].tolist()
    sma5_manual = []
    
    for i in range(len(prices)):
        if i < 4:  # 前4天数据不足，无法计算5日均线
            sma5_manual.append(None)
            print(f"第{i+1:2d}天: 数据不足，无法计算5日均线")
        else:
            # 取前5天的价格
            last_5_prices = prices[i-4:i+1]
            sma_value = sum(last_5_prices) / 5
            sma5_manual.append(sma_value)
            
            print(f"第{i+1:2d}天: ({'+'.join(map(str, last_5_prices))}) ÷ 5 = {sma_value:.2f}")
    
    # 用pandas计算对比
    df['SMA5_manual'] = sma5_manual
    df['SMA5_pandas'] = df['close'].rolling(window=5).mean()
    
    print(f"\n✅ 对比手工计算和pandas计算：")
    print(df[['close', 'SMA5_manual', 'SMA5_pandas']].tail(10).round(2))
    
    print(f"\n💡 移动平均线的意义：")
    print("  📈 价格在均线之上 → 可能是上涨趋势")
    print("  📉 价格在均线之下 → 可能是下跌趋势")
    print("  ⚡ 价格穿越均线 → 可能是买卖信号")

def learn_exponential_moving_average(df):
    """
    学习指数移动平均线 - 更重视最新数据
    """
    print(f"\n📚 第二个指标：指数移动平均线 (EMA)")
    print("="*60)
    
    print("💡 EMA和SMA的区别：")
    print("  SMA: 所有天数权重相同")
    print("  EMA: 最新的数据权重更大，对价格变化更敏感")
    
    print(f"\n🧮 EMA计算公式：")
    print("  EMA_today = α × Price_today + (1-α) × EMA_yesterday")
    print("  其中 α = 2 ÷ (N+1)，N是周期")
    
    # 手工计算5日EMA
    alpha = 2 / (5 + 1)  # α = 2/(5+1) = 0.333
    print(f"  对于5日EMA，α = 2÷(5+1) = {alpha:.3f}")
    
    prices = df['close'].tolist()
    ema5_manual = []
    
    print(f"\n🧮 手工计算5日EMA：")
    
    for i, price in enumerate(prices):
        if i == 0:
            # 第一天EMA等于价格本身
            ema_value = price
            ema5_manual.append(ema_value)
            print(f"第{i+1:2d}天: EMA = {price} (初始值)")
        else:
            # EMA = α × 今日价格 + (1-α) × 昨日EMA
            ema_value = alpha * price + (1 - alpha) * ema5_manual[i-1]
            ema5_manual.append(ema_value)
            print(f"第{i+1:2d}天: EMA = {alpha:.3f}×{price} + {1-alpha:.3f}×{ema5_manual[i-1]:.2f} = {ema_value:.2f}")
    
    # 用pandas计算对比
    df['EMA5_manual'] = ema5_manual
    df['EMA5_pandas'] = df['close'].ewm(span=5).mean()
    
    print(f"\n✅ 对比手工计算和pandas计算：")
    print(df[['close', 'EMA5_manual', 'EMA5_pandas']].tail(5).round(2))
    
    print(f"\n💡 EMA的特点：")
    print("  🚀 对价格变化反应更快")
    print("  ⚡ 更适合捕捉短期趋势变化")
    print("  🎯 常用于快速交易信号")

def learn_rsi_calculation(df):
    """
    详细学习RSI计算 - 最重要的超买超卖指标
    """
    print(f"\n📚 第三个指标：RSI相对强弱指数")
    print("="*60)
    
    print("💡 RSI是什么？")
    print("  测量价格上涨力量和下跌力量的对比")
    print("  RSI > 70 → 超买（可能要下跌）")
    print("  RSI < 30 → 超卖（可能要上涨）")
    
    print(f"\n🧮 RSI计算步骤：")
    print("  1. 计算每日价格变化")
    print("  2. 分别统计上涨幅度和下跌幅度") 
    print("  3. 计算平均上涨幅度和平均下跌幅度")
    print("  4. RS = 平均上涨 ÷ 平均下跌")
    print("  5. RSI = 100 - (100 ÷ (1 + RS))")
    
    prices = df['close'].tolist()
    
    # 步骤1：计算价格变化
    price_changes = []
    for i in range(len(prices)):
        if i == 0:
            price_changes.append(0)  # 第一天没有变化
        else:
            change = prices[i] - prices[i-1]
            price_changes.append(change)
    
    print(f"\n📊 步骤1 - 每日价格变化：")
    for i in range(min(10, len(prices))):
        if i == 0:
            print(f"第{i+1:2d}天: 价格{prices[i]:6.0f}, 变化: -- ")
        else:
            print(f"第{i+1:2d}天: 价格{prices[i]:6.0f}, 变化: {price_changes[i]:+5.0f}")
    
    # 步骤2：分离上涨和下跌
    gains = []
    losses = []
    
    for change in price_changes:
        if change > 0:
            gains.append(change)
            losses.append(0)
        elif change < 0:
            gains.append(0)
            losses.append(abs(change))  # 下跌用正数表示
        else:
            gains.append(0)
            losses.append(0)
    
    print(f"\n📊 步骤2 - 分离上涨和下跌：")
    for i in range(min(10, len(prices))):
        print(f"第{i+1:2d}天: 上涨{gains[i]:5.0f}, 下跌{losses[i]:5.0f}")
    
    # 步骤3：计算14日RSI
    period = 14
    rsi_values = []
    
    print(f"\n📊 步骤3 - 计算{period}日RSI：")
    
    for i in range(len(prices)):
        if i < period:
            rsi_values.append(None)  # 数据不足
            if i < 5:  # 只显示前几天
                print(f"第{i+1:2d}天: 数据不足")
        else:
            # 计算过去14天的平均上涨和下跌
            recent_gains = gains[i-period+1:i+1]
            recent_losses = losses[i-period+1:i+1]
            
            avg_gain = sum(recent_gains) / period
            avg_loss = sum(recent_losses) / period
            
            if avg_loss == 0:
                rsi = 100  # 没有下跌，RSI = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
            
            if i < period + 3:  # 只显示前几个计算结果
                print(f"第{i+1:2d}天: 平均上涨{avg_gain:.2f}, 平均下跌{avg_loss:.2f}, RS={rs:.2f}, RSI={rsi:.1f}")
    
    # 对比pandas计算
    def calculate_rsi_pandas(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    df['RSI_manual'] = rsi_values
    df['RSI_pandas'] = calculate_rsi_pandas(df['close'])
    
    print(f"\n✅ 最近RSI值：")
    print(df[['close', 'RSI_manual', 'RSI_pandas']].tail(5).round(2))

def learn_macd_calculation(df):
    """
    学习MACD指标计算 - 趋势跟踪指标
    """
    print(f"\n📚 第四个指标：MACD指标")
    print("="*60)
    
    print("💡 MACD是什么？")
    print("  Moving Average Convergence Divergence")
    print("  通过两条EMA的差值来判断趋势变化")
    
    print(f"\n🧮 MACD计算公式：")
    print("  1. MACD线 = EMA12 - EMA26")
    print("  2. 信号线 = MACD线的EMA9")
    print("  3. 柱状图 = MACD线 - 信号线")
    
    # 计算EMA12和EMA26
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    
    # 计算MACD线
    macd_line = ema12 - ema26
    
    # 计算信号线
    signal_line = macd_line.ewm(span=9).mean()
    
    # 计算柱状图
    histogram = macd_line - signal_line
    
    df['EMA12'] = ema12
    df['EMA26'] = ema26  
    df['MACD'] = macd_line
    df['Signal'] = signal_line
    df['Histogram'] = histogram
    
    print(f"\n📊 MACD计算示例（最近5天）：")
    macd_data = df[['close', 'EMA12', 'EMA26', 'MACD', 'Signal', 'Histogram']].tail(5).round(3)
    print(macd_data)
    
    print(f"\n💡 MACD信号解读：")
    print("  📈 MACD线上穿信号线 → 金叉（买入信号）")
    print("  📉 MACD线下穿信号线 → 死叉（卖出信号）")
    print("  📊 柱状图变化 → 趋势强弱变化")

def learn_bollinger_bands(df):
    """
    学习布林带计算 - 价格通道指标
    """
    print(f"\n📚 第五个指标：布林带")
    print("="*60)
    
    print("💡 布林带是什么？")
    print("  基于移动平均线和标准差的价格通道")
    print("  用来判断价格是否偏离正常范围")
    
    print(f"\n🧮 布林带计算公式：")
    print("  中轨 = 20日移动平均线")
    print("  上轨 = 中轨 + (2 × 20日标准差)")
    print("  下轨 = 中轨 - (2 × 20日标准差)")
    
    period = 20
    
    # 计算中轨（移动平均）
    middle_band = df['close'].rolling(window=period).mean()
    
    # 计算标准差
    std_dev = df['close'].rolling(window=period).std()
    
    # 计算上轨和下轨
    upper_band = middle_band + (2 * std_dev)
    lower_band = middle_band - (2 * std_dev)
    
    df['BB_Middle'] = middle_band
    df['BB_Upper'] = upper_band
    df['BB_Lower'] = lower_band
    df['BB_Width'] = upper_band - lower_band
    
    # 计算价格在布林带中的位置
    df['BB_Position'] = (df['close'] - lower_band) / (upper_band - lower_band)
    
    print(f"\n📊 布林带示例（最近5天）：")
    bb_data = df[['close', 'BB_Upper', 'BB_Middle', 'BB_Lower', 'BB_Position']].tail(5).round(2)
    print(bb_data)
    
    print(f"\n💡 布林带交易信号：")
    print("  📈 价格触及下轨 → 可能超卖，关注反弹")
    print("  📉 价格触及上轨 → 可能超买，注意回调") 
    print("  📊 价格位置 > 80% → 接近上轨")
    print("  📊 价格位置 < 20% → 接近下轨")

def create_technical_summary(df):
    """
    创建技术指标总结
    """
    print(f"\n📋 技术指标计算总结")
    print("="*60)
    
    latest = df.iloc[-1]
    
    print(f"📊 最新数据 ({df.index[-1].strftime('%Y-%m-%d')}):")
    print(f"  价格: ${latest['close']:.2f}")
    
    if 'SMA5_pandas' in df.columns and not pd.isna(latest['SMA5_pandas']):
        print(f"  SMA5: ${latest['SMA5_pandas']:.2f}")
    
    if 'EMA5_pandas' in df.columns and not pd.isna(latest['EMA5_pandas']):
        print(f"  EMA5: ${latest['EMA5_pandas']:.2f}")
    
    if 'RSI_pandas' in df.columns and not pd.isna(latest['RSI_pandas']):
        rsi = latest['RSI_pandas']
        print(f"  RSI: {rsi:.1f}", end="")
        if rsi > 70:
            print(" (超买)")
        elif rsi < 30:
            print(" (超卖)")
        else:
            print(" (正常)")
    
    if 'MACD' in df.columns and not pd.isna(latest['MACD']):
        print(f"  MACD: {latest['MACD']:.3f}")
        print(f"  Signal: {latest['Signal']:.3f}")
    
    if 'BB_Position' in df.columns and not pd.isna(latest['BB_Position']):
        position = latest['BB_Position']
        print(f"  布林带位置: {position:.1%}", end="")
        if position > 0.8:
            print(" (接近上轨)")
        elif position < 0.2:
            print(" (接近下轨)")
        else:
            print(" (正常区间)")

def main():
    """
    主函数：技术指标计算详解课程
    """
    print("🎯 量化交易学习第三课：技术指标计算详解")
    print("="*60)
    print("💡 今天我们要学会每个指标的计算原理！")
    
    # 生成示例数据
    df = generate_sample_prices()
    
    # 逐个学习每个指标
    learn_simple_moving_average(df)
    learn_exponential_moving_average(df)
    learn_rsi_calculation(df)
    learn_macd_calculation(df)
    learn_bollinger_bands(df)
    
    # 生成总结
    create_technical_summary(df)
    
    # 保存完整数据
    df.to_csv('technical_indicators_detailed.csv')
    print(f"\n💾 详细计算数据已保存到 'technical_indicators_detailed.csv'")
    
    # 显示完整数据表
    print(f"\n📋 完整数据表（最近5天）：")
    key_cols = ['close', 'SMA5_pandas', 'EMA5_pandas', 'RSI_pandas', 'MACD', 'BB_Position']
    available_cols = [col for col in key_cols if col in df.columns]
    print(df[available_cols].tail(5).round(3))
    
    print(f"\n🎉 恭喜！你完成了技术指标计算学习！")
    print(f"\n💡 你现在完全理解了：")
    print("  1. 简单移动平均线(SMA)的计算原理")
    print("  2. 指数移动平均线(EMA)的计算原理")
    print("  3. RSI相对强弱指标的完整计算过程")
    print("  4. MACD指标的计算和信号含义")
    print("  5. 布林带价格通道的计算方法")
    print("  6. 每个指标的交易信号含义")
    print(f"\n🚀 下一步：我们将学习如何将这些指标组合成交易策略！")

if __name__ == "__main__":
    main()
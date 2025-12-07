#!/usr/bin/env python3
"""
第二课：学习K线数据和数据结构（使用模拟数据）
K线 = 蜡烛图，是金融分析的基础
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_kline_data(days=30):
    """
    生成模拟的K线数据用于学习
    这样我们就不依赖外部API了
    """
    print(f"📈 生成 {days} 天的模拟K线数据...")
    
    # 创建日期范围
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         end=datetime.now(), freq='D')
    
    # 模拟比特币价格数据
    np.random.seed(42)  # 固定随机种子，确保结果可重复
    
    # 从110000开始，模拟价格波动
    base_price = 110000
    price_changes = np.random.normal(0, 0.02, len(dates))  # 每日2%的标准波动
    
    prices = [base_price]
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # 生成OHLCV数据
    data = []
    for i, (date, close_price) in enumerate(zip(dates, prices)):
        # 为每一天生成开高低收数据
        open_price = prices[i-1] if i > 0 else close_price
        
        # 高低价在开收价基础上随机波动
        daily_volatility = abs(np.random.normal(0, 0.01))
        high_price = max(open_price, close_price) * (1 + daily_volatility)
        low_price = min(open_price, close_price) * (1 - daily_volatility)
        
        # 模拟成交量
        volume = np.random.uniform(20000, 50000)
        
        data.append({
            'open': open_price,
            'high': high_price, 
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    print(f"✅ 成功生成 {len(df)} 条K线数据")
    return df

def explain_ohlcv(df):
    """
    详细解释OHLCV数据的含义
    """
    print("\n📚 什么是OHLCV数据？")
    print("="*50)
    
    if df is None or df.empty:
        print("❌ 没有数据")
        return
    
    # 取最新一根K线作为例子
    latest = df.iloc[-1]
    latest_date = df.index[-1].strftime('%Y-%m-%d')
    
    print(f"📊 最新K线数据详解（{latest_date}）:")
    print()
    print("🔵 OHLC四个价格的含义：")
    print(f"  🟢 Open (开盘价):  ${latest['open']:,.2f}")
    print(f"       ↪ 这一天第一笔交易的价格")
    
    print(f"  🔴 High (最高价):  ${latest['high']:,.2f}")
    print(f"       ↪ 这一天所有交易中的最高价格")
    
    print(f"  🔵 Low (最低价):   ${latest['low']:,.2f}")
    print(f"       ↪ 这一天所有交易中的最低价格")
    
    print(f"  ⚪ Close (收盘价): ${latest['close']:,.2f}")
    print(f"       ↪ 这一天最后一笔交易的价格")
    
    print(f"  📊 Volume (成交量): {latest['volume']:,.0f}")
    print(f"       ↪ 这一天的总交易数量")
    
    # 计算涨跌幅
    daily_change = latest['close'] - latest['open']
    daily_change_pct = (daily_change / latest['open']) * 100
    
    print(f"\n📈 价格变化分析:")
    if daily_change > 0:
        print(f"  涨跌: +${daily_change:,.2f} (+{daily_change_pct:.2f}%)")
        print(f"  📊 这是一根绿色K线（阳线）- 多头占优")
    elif daily_change < 0:
        print(f"  涨跌: ${daily_change:,.2f} ({daily_change_pct:.2f}%)")
        print(f"  📊 这是一根红色K线（阴线）- 空头占优")
    else:
        print(f"  涨跌: $0.00 (0.00%)")
        print(f"  📊 这是一根十字星K线 - 多空平衡")
    
    # K线实体和影线分析
    print(f"\n📏 K线形态分析:")
    body_size = abs(latest['close'] - latest['open'])              # 实体大小
    total_range = latest['high'] - latest['low']                   # 总范围  
    upper_shadow = latest['high'] - max(latest['open'], latest['close'])    # 上影线
    lower_shadow = min(latest['open'], latest['close']) - latest['low']     # 下影线
    
    print(f"  实体大小: ${body_size:,.2f} ({body_size/total_range*100:.1f}%)")
    print(f"  上影线: ${upper_shadow:,.2f} ({upper_shadow/total_range*100:.1f}%)")
    print(f"  下影线: ${lower_shadow:,.2f} ({lower_shadow/total_range*100:.1f}%)")
    print(f"  全日波动: ${total_range:,.2f}")
    
    # 形态判断
    if body_size / total_range > 0.7:
        print(f"  💡 大实体K线 - 趋势性明确，交易活跃")
    elif body_size / total_range < 0.3:
        print(f"  💡 小实体K线 - 犹豫不决，可能变盘")
    else:
        print(f"  💡 中等实体K线 - 正常交易状态")
    
    if upper_shadow / total_range > 0.4:
        print(f"  💡 长上影线 - 上方抛压较重")
    
    if lower_shadow / total_range > 0.4:
        print(f"  💡 长下影线 - 下方支撑较强")

def calculate_technical_indicators(df):
    """
    计算基础技术指标 - 这是技术分析的核心
    """
    print(f"\n🔧 计算技术指标...")
    
    if df is None or df.empty:
        return df
    
    # 1. 移动平均线系统
    df['MA5'] = df['close'].rolling(window=5).mean()      # 5日移动平均
    df['MA10'] = df['close'].rolling(window=10).mean()    # 10日移动平均
    df['MA20'] = df['close'].rolling(window=20).mean()    # 20日移动平均
    
    print("✅ 移动平均线系统:")
    print("  MA5  = 5日移动平均（短期趋势指标）")
    print("  MA10 = 10日移动平均（中期趋势指标）")
    print("  MA20 = 20日移动平均（长期趋势指标）")
    
    # 2. 布林带（价格通道）
    df['BB_Middle'] = df['close'].rolling(window=20).mean()
    df['BB_Std'] = df['close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)  # 上轨
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)  # 下轨
    
    print("✅ 布林带指标:")
    print("  BB_Upper = 上轨（压力位，价格很难突破）")
    print("  BB_Lower = 下轨（支撑位，价格很难跌破）")
    print("  BB_Middle = 中轨（20日移动平均）")
    
    # 3. 相对强弱指标 (RSI)
    def calculate_rsi(prices, period=14):
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    df['RSI'] = calculate_rsi(df['close'])
    
    print("✅ RSI相对强弱指标:")
    print("  RSI > 70 = 超买区域（可能下跌）")
    print("  RSI < 30 = 超卖区域（可能上涨）")
    print("  30 < RSI < 70 = 正常区域")
    
    # 4. 每日收益率和波动率
    df['Daily_Return'] = df['close'].pct_change() * 100
    df['Volatility'] = df['Daily_Return'].rolling(window=10).std()
    
    print("✅ 收益率和波动率:")
    print("  Daily_Return = 每日价格变化百分比")
    print("  Volatility = 10日收益率标准差（风险度量）")
    
    return df

def analyze_market_signals(df):
    """
    分析市场信号 - 这是交易决策的核心
    """
    print(f"\n📊 市场信号分析...")
    
    if df is None or df.empty or len(df) < 20:
        print("❌ 数据不足，无法进行信号分析")
        return
    
    latest = df.iloc[-1]
    yesterday = df.iloc[-2] if len(df) > 1 else latest
    
    current_price = latest['close']
    
    print(f"📈 当前市场状况 ({df.index[-1].strftime('%Y-%m-%d')}):")
    print(f"  当前价格: ${current_price:,.2f}")
    
    # 1. 移动平均线信号
    print(f"\n🔍 移动平均线信号:")
    if not pd.isna(latest['MA5']) and not pd.isna(latest['MA10']) and not pd.isna(latest['MA20']):
        ma5, ma10, ma20 = latest['MA5'], latest['MA10'], latest['MA20']
        
        print(f"  MA5:  ${ma5:,.2f}")
        print(f"  MA10: ${ma10:,.2f}")  
        print(f"  MA20: ${ma20:,.2f}")
        
        # 多头排列
        if ma5 > ma10 > ma20 and current_price > ma5:
            print("  📈 信号: 强烈看涨（多头排列）")
            print("    ↪ 短中长期均线呈多头排列，价格在均线之上")
            signal_strength = "强烈看涨"
        # 空头排列  
        elif ma5 < ma10 < ma20 and current_price < ma5:
            print("  📉 信号: 强烈看跌（空头排列）")
            print("    ↪ 短中长期均线呈空头排列，价格在均线之下")
            signal_strength = "强烈看跌"
        # 黄金交叉
        elif (latest['MA5'] > latest['MA10'] and 
              yesterday['MA5'] <= yesterday['MA10'] and
              not pd.isna(yesterday['MA5'])):
            print("  🚀 信号: 黄金交叉（买入信号）")
            print("    ↪ 短期均线突破中期均线，可能开始上涨")
            signal_strength = "看涨"
        # 死亡交叉
        elif (latest['MA5'] < latest['MA10'] and 
              yesterday['MA5'] >= yesterday['MA10'] and
              not pd.isna(yesterday['MA5'])):
            print("  💀 信号: 死亡交叉（卖出信号）") 
            print("    ↪ 短期均线跌破中期均线，可能开始下跌")
            signal_strength = "看跌"
        else:
            print("  ➡️ 信号: 震荡整理（观望）")
            signal_strength = "中性"
    
    # 2. 布林带信号
    print(f"\n📏 布林带信号:")
    if not pd.isna(latest['BB_Upper']) and not pd.isna(latest['BB_Lower']):
        bb_upper, bb_lower = latest['BB_Upper'], latest['BB_Lower']
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
        
        print(f"  上轨: ${bb_upper:,.2f}")
        print(f"  下轨: ${bb_lower:,.2f}")
        print(f"  价格位置: {bb_position:.1%}")
        
        if bb_position > 0.8:
            print("  ⚠️  信号: 价格接近上轨（可能超买，注意回调）")
        elif bb_position < 0.2:
            print("  💡 信号: 价格接近下轨（可能超卖，关注反弹）")
        elif 0.4 < bb_position < 0.6:
            print("  ✅信号: 价格在中轨附近（正常区域）")
        else:
            print("  📊 信号: 价格在正常波动范围内")
    
    # 3. RSI信号
    print(f"\n⚡ RSI信号:")
    if not pd.isna(latest['RSI']):
        rsi = latest['RSI']
        print(f"  当前RSI: {rsi:.1f}")
        
        if rsi > 70:
            print("  🔴 信号: 超买区域（考虑减仓）")
            print("    ↪ 价格可能已经涨得过高，注意风险")
        elif rsi < 30:
            print("  🟢 信号: 超卖区域（考虑建仓）")
            print("    ↪ 价格可能已经跌得过低，关注机会")
        elif 30 <= rsi <= 70:
            print("  ⚪ 信号: 正常区域（可正常交易）")
        
        # RSI背离（更高级的信号）
        if len(df) >= 5:
            recent_rsi = df['RSI'].tail(5)
            recent_price = df['close'].tail(5)
            if (recent_price.iloc[-1] > recent_price.iloc[0] and 
                recent_rsi.iloc[-1] < recent_rsi.iloc[0]):
                print("  ⚠️ 注意: 可能存在顶背离（价涨RSI跌）")
            elif (recent_price.iloc[-1] < recent_price.iloc[0] and 
                  recent_rsi.iloc[-1] > recent_rsi.iloc[0]):
                print("  💡 注意: 可能存在底背离（价跌RSI涨）")
    
    # 4. 成交量信号
    print(f"\n📊 成交量信号:")
    avg_volume = df['volume'].tail(10).mean()
    current_volume = latest['volume']
    volume_ratio = current_volume / avg_volume
    
    print(f"  当前成交量: {current_volume:,.0f}")
    print(f"  平均成交量: {avg_volume:,.0f}")
    print(f"  成交量比率: {volume_ratio:.2f}x")
    
    if volume_ratio > 1.5:
        print("  📈 放量（成交活跃，关注突破）")
    elif volume_ratio < 0.7:
        print("  📉 缩量（成交清淡，缺乏动力）")
    else:
        print("  ➡️ 正常成交量")

def generate_summary_report(df):
    """
    生成总结报告
    """
    print(f"\n📋 数据分析总结报告")
    print("="*50)
    
    if df is None or df.empty:
        return
    
    # 基础统计
    latest = df.iloc[-1]
    first = df.iloc[0]
    period_return = (latest['close'] / first['close'] - 1) * 100
    
    print(f"📊 统计周期: {df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')} ({len(df)}天)")
    print(f"📈 期间涨跌: {period_return:+.2f}%")
    print(f"📊 最高价: ${df['high'].max():,.2f}")
    print(f"📊 最低价: ${df['low'].min():,.2f}")
    print(f"📊 平均价: ${df['close'].mean():,.2f}")
    
    # 波动性分析
    if 'Daily_Return' in df.columns:
        volatility = df['Daily_Return'].std()
        print(f"📊 日收益波动率: {volatility:.2f}%")
        
        if volatility > 4:
            risk_level = "高风险"
        elif volatility < 2:
            risk_level = "低风险"
        else:
            risk_level = "中等风险"
        print(f"📊 风险等级: {risk_level}")
    
    # 趋势总结
    if not pd.isna(latest['MA5']) and not pd.isna(latest['MA20']):
        if latest['close'] > latest['MA20']:
            trend = "上升趋势"
        else:
            trend = "下降趋势"
        print(f"📊 当前趋势: {trend}")

def main():
    """
    主函数：完整的K线分析学习课程
    """
    print("🎯 量化交易学习第二课：K线数据深度分析")
    print("="*60)
    
    # 步骤1：生成样本数据
    df = generate_sample_kline_data(30)
    
    # 步骤2：详细解释OHLCV概念  
    explain_ohlcv(df)
    
    # 步骤3：计算技术指标
    df = calculate_technical_indicators(df)
    
    # 步骤4：分析市场信号
    analyze_market_signals(df)
    
    # 步骤5：生成总结报告
    generate_summary_report(df)
    
    # 步骤6：保存完整数据
    df.to_csv('complete_kline_analysis.csv')
    print(f"\n💾 完整分析数据已保存到 'complete_kline_analysis.csv'")
    
    # 步骤7：显示关键数据
    print(f"\n📋 关键指标一览（最近5天）:")
    key_columns = ['close', 'MA5', 'MA20', 'RSI', 'Daily_Return']
    display_data = df[key_columns].tail(5).round(2)
    print(display_data)
    
    print(f"\n🎉 恭喜！你完成了K线数据深度分析！")
    print(f"\n💡 你现在掌握了:")
    print("  1. OHLCV数据的完整含义和重要性")
    print("  2. K线形态分析（实体、影线、涨跌）")  
    print("  3. 移动平均线系统和趋势判断")
    print("  4. 布林带和价格通道概念")
    print("  5. RSI超买超卖信号识别")
    print("  6. 成交量分析和量价配合")
    print("  7. 综合信号分析和交易决策基础")
    print(f"\n🚀 下一步：我们将学习如何将这些信号转化为交易策略！")

if __name__ == "__main__":
    main()
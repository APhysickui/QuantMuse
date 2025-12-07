#!/usr/bin/env python3
"""
第四课：量化因子概念详解
从技术指标升级到量化因子！
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def explain_factor_concept():
    """
    详细解释什么是量化因子
    """
    print("🎯 什么是量化因子？")
    print("="*60)
    
    print("💡 因子 vs 技术指标的区别：")
    print()
    print("📊 技术指标（我们刚学的）：")
    print("  ↪ RSI、MACD、移动平均线等")
    print("  ↪ 主要用于判断买卖时机")
    print("  ↪ 通常是价格和成交量的变换")
    print()
    print("🔬 量化因子（更高级）：")
    print("  ↪ 能够预测股票未来收益的变量")
    print("  ↪ 基于学术研究和实证检验")
    print("  ↪ 可以用来构建投资组合")
    print("  ↪ 包含基本面、技术面、另类数据")
    print()
    
    print("🏗️ 因子的分类体系：")
    print("┌─ 动量因子 (Momentum)")
    print("│  ├─ 价格动量: 过去N天涨跌幅")
    print("│  ├─ 成交量动量: 成交量变化")
    print("│  └─ 相对强度: 相对市场表现")
    print("│")
    print("├─ 价值因子 (Value)")  
    print("│  ├─ 市盈率 (P/E): 价格/每股收益")
    print("│  ├─ 市净率 (P/B): 价格/每股净资产")
    print("│  └─ 股息率: 股息/股价")
    print("│")
    print("├─ 质量因子 (Quality)")
    print("│  ├─ ROE: 净资产收益率")
    print("│  ├─ ROA: 总资产收益率")
    print("│  └─ 负债率: 负债/资产")
    print("│")
    print("├─ 规模因子 (Size)")
    print("│  └─ 市值: 股价×股票数量")
    print("│")
    print("├─ 波动率因子 (Volatility)")
    print("│  ├─ 历史波动率")
    print("│  ├─ Beta系数")
    print("│  └─ 最大回撤")
    print("│")
    print("└─ 技术因子 (Technical)")
    print("   ├─ RSI、MACD等技术指标")
    print("   ├─ 量价关系")
    print("   └─ 形态识别")

def generate_multi_stock_data():
    """
    生成多只股票的数据用于因子分析
    """
    print(f"\n📊 生成多只股票数据...")
    
    # 创建5只模拟股票，30天数据
    stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    
    np.random.seed(42)  # 固定随机种子
    
    # 为每只股票生成不同特征的数据
    stock_data = {}
    
    for i, stock in enumerate(stocks):
        # 不同股票有不同的基础价格和波动特征
        base_price = 100 + i * 50  # AAPL=100, GOOGL=150, MSFT=200, TSLA=250, NVDA=300
        volatility = 0.02 + i * 0.005  # 不同的波动率
        trend = -0.001 + i * 0.0005  # 不同的趋势
        
        prices = [base_price]
        volumes = []
        
        for day in range(29):
            # 价格随机游走 + 趋势
            daily_return = np.random.normal(trend, volatility)
            new_price = prices[-1] * (1 + daily_return)
            prices.append(new_price)
            
            # 成交量与价格变化相关
            volume_base = 1000000 + i * 500000
            volume_multiplier = 1 + abs(daily_return) * 10  # 价格波动大时成交量大
            volume = volume_base * volume_multiplier * np.random.uniform(0.8, 1.2)
            volumes.append(volume)
        
        volumes.append(volumes[-1])  # 最后一天的成交量
        
        # 生成OHLC数据
        ohlc_data = []
        for j, close_price in enumerate(prices):
            if j == 0:
                open_price = close_price
            else:
                open_price = prices[j-1]
            
            high_price = max(open_price, close_price) * np.random.uniform(1.0, 1.02)
            low_price = min(open_price, close_price) * np.random.uniform(0.98, 1.0)
            
            ohlc_data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volumes[j]
            })
        
        df = pd.DataFrame(ohlc_data, index=dates)
        df['stock'] = stock
        stock_data[stock] = df
    
    print(f"✅ 生成了{len(stocks)}只股票，每只{len(dates)}天的数据")
    
    # 显示数据样本
    print(f"\n📋 数据样本（最新5天）：")
    for stock in stocks:
        latest_price = stock_data[stock]['close'].iloc[-1]
        first_price = stock_data[stock]['close'].iloc[0]
        total_return = (latest_price / first_price - 1) * 100
        print(f"  {stock}: 最新价格 ${latest_price:.2f}, 期间收益 {total_return:+.1f}%")
    
    return stock_data

def calculate_momentum_factors(stock_data):
    """
    计算动量因子 - 这是最重要的因子类别之一
    """
    print(f"\n🚀 计算动量因子")
    print("="*60)
    
    print("💡 动量效应是什么？")
    print("  → 过去表现好的股票，未来一段时间内可能继续表现好")
    print("  → 这是学术界发现的最稳健的市场异象之一")
    print()
    
    factor_data = {}
    
    for stock, df in stock_data.items():
        print(f"📊 计算 {stock} 的动量因子...")
        
        factors = {}
        
        # 1. 价格动量 - 不同期间的收益率
        factors['momentum_5d'] = (df['close'].iloc[-1] / df['close'].iloc[-6] - 1) * 100
        factors['momentum_10d'] = (df['close'].iloc[-1] / df['close'].iloc[-11] - 1) * 100
        factors['momentum_20d'] = (df['close'].iloc[-1] / df['close'].iloc[-21] - 1) * 100
        
        print(f"  价格动量:")
        print(f"    5日动量:  {factors['momentum_5d']:+6.2f}%")
        print(f"    10日动量: {factors['momentum_10d']:+6.2f}%")
        print(f"    20日动量: {factors['momentum_20d']:+6.2f}%")
        
        # 2. 动量加速度 - 动量的变化
        if len(df) >= 20:
            momentum_recent = (df['close'].iloc[-1] / df['close'].iloc[-11] - 1) * 100  # 最近10天
            momentum_earlier = (df['close'].iloc[-11] / df['close'].iloc[-21] - 1) * 100  # 之前10天
            factors['momentum_acceleration'] = momentum_recent - momentum_earlier
            print(f"    动量加速度: {factors['momentum_acceleration']:+6.2f}%")
        
        # 3. 成交量动量 - 成交量的变化
        recent_volume = df['volume'].tail(5).mean()
        earlier_volume = df['volume'].head(10).mean()
        factors['volume_momentum'] = (recent_volume / earlier_volume - 1) * 100
        print(f"  成交量动量: {factors['volume_momentum']:+6.2f}%")
        
        # 4. 量价配合度 - 成交量和价格变化的一致性
        price_changes = df['close'].pct_change().tail(10)
        volume_changes = df['volume'].pct_change().tail(10)
        factors['price_volume_correlation'] = price_changes.corr(volume_changes)
        print(f"  量价相关性: {factors['price_volume_correlation']:6.3f}")
        
        # 5. 波动率调整动量 - 用波动率调整的动量
        returns = df['close'].pct_change().tail(20)
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        factors['volatility_adjusted_momentum'] = factors['momentum_20d'] / (volatility * 100)
        print(f"  波动率调整动量: {factors['volatility_adjusted_momentum']:6.3f}")
        
        factor_data[stock] = factors
        print()
    
    return factor_data

def calculate_technical_factors(stock_data):
    """
    将技术指标转化为因子
    """
    print(f"⚡ 计算技术因子")
    print("="*60)
    
    print("💡 技术因子：将技术指标标准化为因子")
    print("  → RSI偏离中性值的程度")
    print("  → 价格相对移动平均线的位置")
    print("  → 布林带位置等")
    print()
    
    technical_factors = {}
    
    for stock, df in stock_data.items():
        print(f"📊 计算 {stock} 的技术因子...")
        
        factors = {}
        
        # 计算技术指标
        df['SMA5'] = df['close'].rolling(5).mean()
        df['SMA20'] = df['close'].rolling(20).mean()
        
        # RSI
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        df['RSI'] = calculate_rsi(df['close'])
        
        # 布林带
        df['BB_Middle'] = df['close'].rolling(20).mean()
        df['BB_Std'] = df['close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + 2 * df['BB_Std']
        df['BB_Lower'] = df['BB_Middle'] - 2 * df['BB_Std']
        
        latest = df.iloc[-1]
        
        # 1. RSI因子 - RSI偏离中性值50的程度
        if not pd.isna(latest['RSI']):
            factors['rsi_factor'] = (latest['RSI'] - 50) / 50  # 标准化到[-1, 1]
            print(f"  RSI因子: {factors['rsi_factor']:6.3f} (RSI={latest['RSI']:.1f})")
        
        # 2. 价格位置因子 - 价格相对移动平均线的位置
        if not pd.isna(latest['SMA20']):
            factors['price_position'] = (latest['close'] / latest['SMA20'] - 1) * 100
            print(f"  价格位置: {factors['price_position']:+6.2f}% (相对20日均线)")
        
        # 3. 趋势强度因子 - 短期均线相对长期均线
        if not pd.isna(latest['SMA5']) and not pd.isna(latest['SMA20']):
            factors['trend_strength'] = (latest['SMA5'] / latest['SMA20'] - 1) * 100
            print(f"  趋势强度: {factors['trend_strength']:+6.2f}% (5日均线 vs 20日均线)")
        
        # 4. 布林带位置因子
        if not pd.isna(latest['BB_Upper']) and not pd.isna(latest['BB_Lower']):
            bb_width = latest['BB_Upper'] - latest['BB_Lower']
            bb_position = (latest['close'] - latest['BB_Lower']) / bb_width
            factors['bollinger_position'] = (bb_position - 0.5) * 2  # 标准化到[-1, 1]
            print(f"  布林带位置: {factors['bollinger_position']:6.3f} (位置={bb_position:.1%})")
        
        technical_factors[stock] = factors
        print()
    
    return technical_factors

def analyze_factor_effectiveness(momentum_factors, technical_factors, stock_data):
    """
    分析因子的有效性
    """
    print(f"📈 因子有效性分析")
    print("="*60)
    
    print("💡 什么是因子有效性？")
    print("  → 因子值与未来收益的相关性")
    print("  → 因子能否区分好股票和坏股票")
    print("  → 因子的预测能力")
    print()
    
    # 计算每只股票的未来收益（这里用总收益代替）
    stock_returns = {}
    for stock, df in stock_data.items():
        total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        stock_returns[stock] = total_return
    
    print("📊 股票收益表现：")
    sorted_stocks = sorted(stock_returns.items(), key=lambda x: x[1], reverse=True)
    for i, (stock, ret) in enumerate(sorted_stocks):
        print(f"  第{i+1}名: {stock} {ret:+6.2f}%")
    
    print(f"\n🔍 分析因子与收益的关系：")
    
    # 分析动量因子
    print(f"\n📊 动量因子分析：")
    momentum_20d = {stock: factors.get('momentum_20d', 0) for stock, factors in momentum_factors.items()}
    
    print("  20日动量因子排名:")
    sorted_momentum = sorted(momentum_20d.items(), key=lambda x: x[1], reverse=True)
    for i, (stock, momentum) in enumerate(sorted_momentum):
        returns = stock_returns[stock]
        print(f"    第{i+1}名: {stock} 动量={momentum:+6.2f}%, 收益={returns:+6.2f}%")
    
    # 计算因子IC (Information Coefficient) - 因子与收益的相关系数
    momentum_values = [momentum_factors[stock].get('momentum_20d', 0) for stock in stock_returns.keys()]
    return_values = [stock_returns[stock] for stock in stock_returns.keys()]
    
    momentum_ic = np.corrcoef(momentum_values, return_values)[0, 1]
    print(f"\n💡 20日动量因子IC: {momentum_ic:.3f}")
    
    if abs(momentum_ic) > 0.5:
        print("  → 因子效果很好！")
    elif abs(momentum_ic) > 0.2:
        print("  → 因子效果不错")
    else:
        print("  → 因子效果一般")
    
    # 分析技术因子
    print(f"\n📊 技术因子分析：")
    rsi_factors = {stock: factors.get('rsi_factor', 0) for stock, factors in technical_factors.items()}
    
    print("  RSI因子排名:")
    sorted_rsi = sorted(rsi_factors.items(), key=lambda x: x[1], reverse=True)
    for i, (stock, rsi) in enumerate(sorted_rsi):
        returns = stock_returns[stock]
        print(f"    第{i+1}名: {stock} RSI因子={rsi:+6.3f}, 收益={returns:+6.2f}%")
    
    rsi_values = [technical_factors[stock].get('rsi_factor', 0) for stock in stock_returns.keys()]
    rsi_ic = np.corrcoef(rsi_values, return_values)[0, 1]
    print(f"\n💡 RSI因子IC: {rsi_ic:.3f}")

def create_factor_summary_table(momentum_factors, technical_factors, stock_data):
    """
    创建因子汇总表
    """
    print(f"\n📋 因子汇总表")
    print("="*60)
    
    # 创建汇总DataFrame
    summary_data = []
    
    for stock in stock_data.keys():
        row = {'股票': stock}
        
        # 添加收益数据
        df = stock_data[stock]
        total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        row['总收益%'] = total_return
        
        # 添加动量因子
        if stock in momentum_factors:
            row['动量20日%'] = momentum_factors[stock].get('momentum_20d', np.nan)
            row['成交量动量%'] = momentum_factors[stock].get('volume_momentum', np.nan)
            row['波动调整动量'] = momentum_factors[stock].get('volatility_adjusted_momentum', np.nan)
        
        # 添加技术因子
        if stock in technical_factors:
            row['RSI因子'] = technical_factors[stock].get('rsi_factor', np.nan)
            row['价格位置%'] = technical_factors[stock].get('price_position', np.nan)
            row['趋势强度%'] = technical_factors[stock].get('trend_strength', np.nan)
        
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.set_index('股票')
    
    print(summary_df.round(2))
    
    # 保存数据
    summary_df.to_csv('factor_analysis_summary.csv')
    print(f"\n💾 因子分析结果已保存到 'factor_analysis_summary.csv'")
    
    return summary_df

def main():
    """
    主函数：量化因子概念学习
    """
    print("🎯 量化交易学习第四课：量化因子概念详解")
    print("="*60)
    print("🚀 从技术指标升级到量化因子！")
    
    # 1. 解释因子概念
    explain_factor_concept()
    
    # 2. 生成多股票数据
    stock_data = generate_multi_stock_data()
    
    # 3. 计算动量因子
    momentum_factors = calculate_momentum_factors(stock_data)
    
    # 4. 计算技术因子
    technical_factors = calculate_technical_factors(stock_data)
    
    # 5. 分析因子有效性
    analyze_factor_effectiveness(momentum_factors, technical_factors, stock_data)
    
    # 6. 创建汇总表
    summary_df = create_factor_summary_table(momentum_factors, technical_factors, stock_data)
    
    print(f"\n🎉 恭喜！你完成了量化因子概念学习！")
    print(f"\n💡 你现在理解了：")
    print("  1. 因子与技术指标的本质区别")
    print("  2. 动量因子的计算和含义")  
    print("  3. 技术因子的标准化方法")
    print("  4. 因子有效性的评估方法")
    print("  5. 因子IC（信息系数）的概念")
    print("  6. 多因子分析的基本框架")
    print(f"\n🚀 下一步：我们将用这些因子构建真正的量化策略！")

if __name__ == "__main__":
    main()
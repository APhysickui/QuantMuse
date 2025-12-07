#!/usr/bin/env python3
"""
我的第一个量化交易示例
让我们从最简单的开始！
"""

import sys
import os
# 添加项目路径，让Python能找到data_service模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import pandas as pd
from datetime import datetime

def get_btc_price():
    """
    第一个函数：获取比特币当前价格
    这里我们直接使用最简单的免费API
    """
    print("🚀 正在获取比特币价格...")
    
    # 这是一个完全免费的API，不需要任何注册或密钥
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    
    try:
        # 发送HTTP请求获取数据
        response = requests.get(url)
        data = response.json()  # 将返回的JSON转换为Python字典
        
        # 提取比特币价格
        btc_price = data['bitcoin']['usd']
        print(f"✅ 比特币当前价格: ${btc_price:,}")
        
        return btc_price
    
    except Exception as e:
        print(f"❌ 获取价格失败: {e}")
        return None

def get_simple_data():
    """
    第二个函数：获取简单的历史数据
    我们来看看数据长什么样
    """
    print("\n📊 正在获取简单历史数据...")
    
    # 获取过去7天的比特币价格数据
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # 数据结构解释：
        # data['prices'] = [[时间戳, 价格], [时间戳, 价格], ...]
        # 时间戳是毫秒级的Unix时间戳
        
        prices = data['prices']  # 获取价格数据
        print(f"✅ 获取到 {len(prices)} 条价格记录")
        
        # 让我们看看数据长什么样
        print("\n🔍 数据样本（前3条）：")
        for i, (timestamp, price) in enumerate(prices[:3]):
            # 将时间戳转换为可读时间
            time_readable = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {i+1}. 时间: {time_readable}, 价格: ${price:,.2f}")
            
        return prices
    
    except Exception as e:
        print(f"❌ 获取历史数据失败: {e}")
        return None

def create_dataframe(prices):
    """
    第三个函数：将数据转换为DataFrame
    DataFrame是pandas的数据表格，非常方便分析
    """
    print("\n📋 正在创建数据表格...")
    
    if not prices:
        print("❌ 没有价格数据")
        return None
    
    # 创建DataFrame - 这是数据分析的基础
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    
    # 转换时间戳为datetime对象
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # 设置datetime为索引，这样更方便按时间分析
    df.set_index('datetime', inplace=True)
    
    # 删除原始timestamp列，我们不再需要它
    df.drop('timestamp', axis=1, inplace=True)
    
    print(f"✅ 创建了包含 {len(df)} 行数据的表格")
    print("\n📊 数据表格预览：")
    print(df.head())  # 显示前5行
    
    return df

def simple_analysis(df):
    """
    第四个函数：简单的数据分析
    这里我们学习最基础的分析概念
    """
    print("\n📈 开始简单分析...")
    
    if df is None or df.empty:
        print("❌ 没有数据可分析")
        return
    
    # 1. 基本统计信息
    current_price = df['price'].iloc[-1]  # 最新价格
    highest_price = df['price'].max()     # 最高价
    lowest_price = df['price'].min()      # 最低价
    avg_price = df['price'].mean()        # 平均价
    
    print(f"💰 当前价格: ${current_price:,.2f}")
    print(f"📈 最高价格: ${highest_price:,.2f}")
    print(f"📉 最低价格: ${lowest_price:,.2f}")
    print(f"📊 平均价格: ${avg_price:,.2f}")
    
    # 2. 价格变化
    first_price = df['price'].iloc[0]     # 第一个价格
    price_change = current_price - first_price
    price_change_percent = (price_change / first_price) * 100
    
    print(f"\n📍 期间价格变化:")
    print(f"  绝对变化: ${price_change:,.2f}")
    print(f"  百分比变化: {price_change_percent:.2f}%")
    
    # 3. 简单的移动平均（这是技术分析的基础）
    # 移动平均 = 过去N天价格的平均值
    df['MA_24h'] = df['price'].rolling(window=24).mean()  # 24小时移动平均
    
    current_ma = df['MA_24h'].iloc[-1]
    if not pd.isna(current_ma):
        print(f"\n📊 24小时移动平均: ${current_ma:,.2f}")
        
        # 价格与移动平均的关系（这是交易信号的基础）
        if current_price > current_ma:
            print("🟢 当前价格高于移动平均线（可能是上涨趋势）")
        else:
            print("🔴 当前价格低于移动平均线（可能是下跌趋势）")

def main():
    """
    主函数：按步骤执行我们的学习
    """
    print("🎯 欢迎来到量化交易学习第一课！")
    print("="*50)
    
    # 步骤1：获取当前价格
    current_price = get_btc_price()
    
    # 步骤2：获取历史数据
    historical_prices = get_simple_data()
    
    # 步骤3：创建数据表格
    df = create_dataframe(historical_prices)
    
    # 步骤4：简单分析
    simple_analysis(df)
    
    print("\n🎉 恭喜！你完成了第一个量化分析！")
    print("\n💡 你学会了:")
    print("  1. 如何获取实时价格数据")
    print("  2. 如何获取历史数据")
    print("  3. 如何创建和查看数据表格")
    print("  4. 如何进行基本的价格分析")
    print("  5. 什么是移动平均线")
    
    # 保存数据（可选）
    if df is not None:
        df.to_csv('my_first_btc_data.csv')
        print(f"\n💾 数据已保存到 'my_first_btc_data.csv'")

if __name__ == "__main__":
    main()
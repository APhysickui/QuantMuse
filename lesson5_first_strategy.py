#!/usr/bin/env python3
"""
第五课：构建你的第一个量化策略
将因子转化为真正的交易策略！
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SimpleQuantStrategy:
    """
    简单量化策略类
    基于动量因子的股票选择策略
    """
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}  # 当前持仓
        self.trades = []     # 交易记录
        self.portfolio_history = []  # 投资组合历史
        
        print(f"🎯 初始化量化策略")
        print(f"  初始资金: ${initial_capital:,}")
        print(f"  策略类型: 动量因子选股策略")

    def generate_extended_stock_data(self, days=60):
        """
        生成更长时间的股票数据用于策略回测
        """
        print(f"\n📊 生成 {days} 天的股票数据用于回测...")
        
        stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX']
        dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
        
        np.random.seed(42)
        stock_data = {}
        
        for i, stock in enumerate(stocks):
            # 不同股票的特征参数
            base_price = 100 + i * 30
            daily_trend = -0.0005 + i * 0.0003  # 不同的长期趋势
            volatility = 0.015 + i * 0.002      # 不同的波动率
            
            prices = [base_price]
            volumes = []
            
            for day in range(days - 1):
                # 模拟更真实的价格走势
                random_shock = np.random.normal(0, volatility)
                trend_component = daily_trend
                
                # 添加一些周期性和突发事件
                cycle_component = 0.002 * np.sin(day * 2 * np.pi / 20)  # 20天周期
                
                # 偶发的突发事件
                if np.random.random() < 0.05:  # 5%概率的突发事件
                    shock = np.random.normal(0, 0.03)  # 更大的波动
                else:
                    shock = 0
                
                total_return = trend_component + cycle_component + random_shock + shock
                new_price = prices[-1] * (1 + total_return)
                prices.append(max(new_price, 0.1))  # 防止负价格
            
            # 生成成交量
            for day in range(days):
                base_volume = 1000000 + i * 200000
                volume_volatility = 0.3
                daily_volume = base_volume * (1 + np.random.normal(0, volume_volatility))
                volumes.append(max(daily_volume, 100000))
            
            # 生成OHLC数据
            ohlc_data = []
            for j, close_price in enumerate(prices):
                if j == 0:
                    open_price = close_price
                else:
                    open_price = prices[j-1] * (1 + np.random.normal(0, 0.005))
                
                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
                
                ohlc_data.append({
                    'open': max(open_price, 0.1),
                    'high': max(high_price, 0.1),
                    'low': max(low_price, 0.1),
                    'close': max(close_price, 0.1),
                    'volume': volumes[j]
                })
            
            df = pd.DataFrame(ohlc_data, index=dates)
            df['symbol'] = stock
            stock_data[stock] = df
        
        print(f"✅ 成功生成 {len(stocks)} 只股票，每只 {days} 天的数据")
        return stock_data

    def calculate_all_factors(self, stock_data):
        """
        为所有股票计算因子
        """
        print(f"\n🔬 计算所有股票的量化因子...")
        
        factor_data = {}
        
        for stock, df in stock_data.items():
            factors = {}
            
            # 1. 动量因子
            if len(df) >= 21:
                factors['momentum_5d'] = (df['close'].iloc[-1] / df['close'].iloc[-6] - 1) * 100
                factors['momentum_10d'] = (df['close'].iloc[-1] / df['close'].iloc[-11] - 1) * 100
                factors['momentum_20d'] = (df['close'].iloc[-1] / df['close'].iloc[-21] - 1) * 100
            
            # 2. 技术因子
            if len(df) >= 20:
                # RSI
                def calculate_rsi(prices, period=14):
                    delta = prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    return rsi
                
                rsi = calculate_rsi(df['close']).iloc[-1]
                if not pd.isna(rsi):
                    factors['rsi'] = rsi
                    factors['rsi_factor'] = (rsi - 50) / 50  # 标准化
                
                # 移动平均
                sma_20 = df['close'].rolling(20).mean().iloc[-1]
                if not pd.isna(sma_20):
                    factors['price_to_sma20'] = (df['close'].iloc[-1] / sma_20 - 1) * 100
            
            # 3. 波动率因子
            if len(df) >= 20:
                returns = df['close'].pct_change().tail(20)
                volatility = returns.std() * np.sqrt(252)  # 年化波动率
                factors['volatility'] = volatility * 100
            
            # 4. 成交量因子
            if len(df) >= 15:
                recent_volume = df['volume'].tail(5).mean()
                earlier_volume_start = max(0, len(df) - 15)
                earlier_volume_end = max(5, len(df) - 10)
                earlier_volume = df['volume'].iloc[earlier_volume_start:earlier_volume_end].mean()
                if earlier_volume > 0:
                    factors['volume_ratio'] = recent_volume / earlier_volume
            
            factor_data[stock] = factors
        
        print(f"✅ 完成所有股票因子计算")
        return factor_data

    def generate_trading_signals(self, factor_data):
        """
        基于因子生成交易信号
        这是策略的核心！
        """
        print(f"\n🎯 生成交易信号...")
        
        signals = {}
        
        # 收集所有股票的主要因子
        momentum_scores = {}
        technical_scores = {}
        
        for stock, factors in factor_data.items():
            # 1. 动量得分 (权重: 40%)
            momentum_score = 0
            if 'momentum_20d' in factors:
                momentum_score += factors['momentum_20d'] * 0.6  # 20日动量权重60%
            if 'momentum_10d' in factors:
                momentum_score += factors['momentum_10d'] * 0.4  # 10日动量权重40%
            
            momentum_scores[stock] = momentum_score
            
            # 2. 技术得分 (权重: 30%)
            technical_score = 0
            if 'rsi_factor' in factors:
                # RSI在30-70之间比较好，过高过低都扣分
                rsi = factors['rsi']
                if 30 <= rsi <= 70:
                    technical_score += 5
                elif rsi > 70:
                    technical_score -= abs(rsi - 70) * 0.2  # 超买扣分
                elif rsi < 30:
                    technical_score += (30 - rsi) * 0.3    # 超卖加分
            
            if 'price_to_sma20' in factors:
                # 价格相对均线的位置
                price_pos = factors['price_to_sma20']
                if price_pos > 0:
                    technical_score += min(price_pos * 0.5, 10)  # 上涨趋势加分，但有上限
                
            technical_scores[stock] = technical_score
        
        # 3. 计算综合得分
        composite_scores = {}
        for stock in factor_data.keys():
            # 标准化各个得分
            momentum_norm = momentum_scores.get(stock, 0) / 10  # 归一化
            technical_norm = technical_scores.get(stock, 0) / 10
            
            # 综合得分
            composite_score = (momentum_norm * 0.6 + technical_norm * 0.4)
            composite_scores[stock] = composite_score
        
        # 4. 生成信号
        sorted_stocks = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
        
        print(f"📊 股票综合得分排名:")
        for i, (stock, score) in enumerate(sorted_stocks):
            momentum = momentum_scores.get(stock, 0)
            technical = technical_scores.get(stock, 0)
            print(f"  第{i+1}名: {stock} 综合:{score:6.2f} (动量:{momentum:+6.1f}%, 技术:{technical:6.1f})")
        
        # 选择前3名作为买入信号，后2名作为卖出信号
        buy_signals = [stock for stock, _ in sorted_stocks[:3]]
        sell_signals = [stock for stock, _ in sorted_stocks[-2:]]
        
        print(f"\n🎯 交易信号生成:")
        print(f"  🟢 买入信号: {', '.join(buy_signals)}")
        print(f"  🔴 卖出信号: {', '.join(sell_signals)}")
        
        return {
            'buy': buy_signals,
            'sell': sell_signals,
            'scores': composite_scores,
            'rankings': sorted_stocks
        }

    def execute_trades(self, signals, stock_data, trading_date):
        """
        执行交易
        """
        print(f"\n💼 执行交易 ({trading_date.strftime('%Y-%m-%d')})...")
        
        buy_signals = signals['buy']
        sell_signals = signals['sell']
        
        # 1. 先执行卖出操作
        for stock in sell_signals:
            if stock in self.positions:
                shares = self.positions[stock]['shares']
                current_price = stock_data[stock]['close'].iloc[-1]
                sell_value = shares * current_price
                
                # 记录交易
                trade = {
                    'date': trading_date,
                    'stock': stock,
                    'action': 'SELL',
                    'shares': shares,
                    'price': current_price,
                    'value': sell_value,
                    'reason': '因子得分较低'
                }
                self.trades.append(trade)
                
                # 更新资金和持仓
                self.current_capital += sell_value
                buy_price = self.positions[stock]['price']
                profit = (current_price - buy_price) * shares
                
                print(f"  🔴 卖出 {stock}: {shares}股 @ ${current_price:.2f}, 盈亏: ${profit:+,.0f}")
                
                del self.positions[stock]
        
        # 2. 然后执行买入操作
        if buy_signals:
            available_capital = self.current_capital * 0.9  # 保留10%现金
            capital_per_stock = available_capital / len(buy_signals)
            
            for stock in buy_signals:
                if stock not in self.positions:  # 避免重复持有
                    current_price = stock_data[stock]['close'].iloc[-1]
                    shares = int(capital_per_stock / current_price)
                    
                    if shares > 0:
                        buy_value = shares * current_price
                        
                        # 记录交易
                        trade = {
                            'date': trading_date,
                            'stock': stock,
                            'action': 'BUY',
                            'shares': shares,
                            'price': current_price,
                            'value': buy_value,
                            'reason': '因子得分较高'
                        }
                        self.trades.append(trade)
                        
                        # 更新资金和持仓
                        self.current_capital -= buy_value
                        self.positions[stock] = {
                            'shares': shares,
                            'price': current_price,
                            'date': trading_date
                        }
                        
                        print(f"  🟢 买入 {stock}: {shares}股 @ ${current_price:.2f}, 投入: ${buy_value:,.0f}")
        
        print(f"  💰 剩余现金: ${self.current_capital:,.0f}")

    def calculate_portfolio_value(self, stock_data):
        """
        计算当前投资组合价值
        """
        cash = self.current_capital
        positions_value = 0
        
        for stock, position in self.positions.items():
            current_price = stock_data[stock]['close'].iloc[-1]
            stock_value = position['shares'] * current_price
            positions_value += stock_value
        
        total_value = cash + positions_value
        return {
            'total': total_value,
            'cash': cash,
            'positions': positions_value,
            'return': (total_value / self.initial_capital - 1) * 100
        }

    def run_backtest(self, start_date='2024-01-20', end_date='2024-02-29'):
        """
        运行策略回测
        这是策略验证的关键步骤！
        """
        print(f"\n🚀 开始策略回测")
        print(f"  回测期间: {start_date} 至 {end_date}")
        print("="*60)
        
        # 生成数据
        stock_data = self.generate_extended_stock_data(60)
        
        # 模拟定期调仓（每10天调仓一次）
        rebalance_dates = pd.date_range(start=start_date, end=end_date, freq='10D')
        
        for i, rebalance_date in enumerate(rebalance_dates):
            print(f"\n📅 第{i+1}次调仓 - {rebalance_date.strftime('%Y-%m-%d')}")
            
            # 更新数据到当前日期（模拟实际交易中的数据获取）
            current_data = {}
            for stock, df in stock_data.items():
                # 假设我们只能看到当前日期之前的数据
                days_from_start = (rebalance_date - pd.Timestamp('2024-01-01')).days
                if days_from_start < len(df):
                    current_data[stock] = df.iloc[:days_from_start+1]
                else:
                    current_data[stock] = df
            
            # 计算因子
            factor_data = self.calculate_all_factors(current_data)
            
            # 生成交易信号
            signals = self.generate_trading_signals(factor_data)
            
            # 执行交易
            self.execute_trades(signals, current_data, rebalance_date)
            
            # 计算组合价值
            portfolio_value = self.calculate_portfolio_value(current_data)
            self.portfolio_history.append({
                'date': rebalance_date,
                'total_value': portfolio_value['total'],
                'cash': portfolio_value['cash'],
                'positions_value': portfolio_value['positions'],
                'return': portfolio_value['return']
            })
            
            print(f"📊 投资组合价值: ${portfolio_value['total']:,.0f} (收益率: {portfolio_value['return']:+.1f}%)")

    def analyze_performance(self):
        """
        分析策略表现
        """
        print(f"\n📈 策略表现分析")
        print("="*60)
        
        if not self.portfolio_history:
            print("❌ 没有回测数据")
            return
        
        # 转换为DataFrame便于分析
        perf_df = pd.DataFrame(self.portfolio_history)
        
        # 基本统计
        final_value = perf_df['total_value'].iloc[-1]
        total_return = (final_value / self.initial_capital - 1) * 100
        
        print(f"💰 资金表现:")
        print(f"  初始资金: ${self.initial_capital:,}")
        print(f"  最终价值: ${final_value:,.0f}")
        print(f"  总收益率: {total_return:+.2f}%")
        
        # 计算最大回撤
        perf_df['peak'] = perf_df['total_value'].expanding().max()
        perf_df['drawdown'] = (perf_df['total_value'] - perf_df['peak']) / perf_df['peak'] * 100
        max_drawdown = perf_df['drawdown'].min()
        
        print(f"\n📉 风险指标:")
        print(f"  最大回撤: {max_drawdown:.2f}%")
        
        # 交易统计
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        
        print(f"\n💼 交易统计:")
        print(f"  总交易次数: {len(self.trades)}")
        print(f"  买入次数: {len(buy_trades)}")
        print(f"  卖出次数: {len(sell_trades)}")
        
        # 当前持仓
        print(f"\n📋 当前持仓:")
        if self.positions:
            total_position_value = 0
            for stock, position in self.positions.items():
                print(f"  {stock}: {position['shares']}股 @ ${position['price']:.2f}")
                total_position_value += position['shares'] * position['price']
            print(f"  持仓总价值: ${total_position_value:,.0f}")
        else:
            print("  无持仓")
        
        print(f"  现金: ${self.current_capital:,.0f}")
        
        # 显示表现曲线
        print(f"\n📊 净值曲线:")
        for i, record in enumerate(self.portfolio_history):
            date_str = record['date'].strftime('%m-%d')
            value = record['total_value']
            ret = record['return']
            print(f"  {date_str}: ${value:8,.0f} ({ret:+6.1f}%)")

def main():
    """
    主函数：完整的量化策略实战
    """
    print("🎯 量化交易学习第五课：构建完整量化策略")
    print("="*60)
    print("🚀 我们要构建一个基于多因子的股票选择策略！")
    
    # 创建策略实例
    strategy = SimpleQuantStrategy(initial_capital=100000)
    
    # 运行回测
    strategy.run_backtest()
    
    # 分析表现
    strategy.analyze_performance()
    
    # 保存交易记录
    if strategy.trades:
        trades_df = pd.DataFrame(strategy.trades)
        trades_df.to_csv('strategy_trades.csv', index=False)
        print(f"\n💾 交易记录已保存到 'strategy_trades.csv'")
    
    # 保存组合历史
    if strategy.portfolio_history:
        portfolio_df = pd.DataFrame(strategy.portfolio_history)
        portfolio_df.to_csv('portfolio_history.csv', index=False)
        print(f"💾 组合历史已保存到 'portfolio_history.csv'")
    
    print(f"\n🎉 恭喜！你完成了第一个量化策略的构建和回测！")
    print(f"\n💡 你现在掌握了:")
    print("  1. 多因子模型的构建方法")
    print("  2. 交易信号的生成逻辑")
    print("  3. 投资组合的构建和调仓")
    print("  4. 策略回测的完整流程")
    print("  5. 交易执行和资金管理")
    print("  6. 策略表现的评估方法")
    print(f"\n🚀 下一步：我们将深入分析策略的风险收益特征！")

if __name__ == "__main__":
    main()
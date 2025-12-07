#!/usr/bin/env python3
"""
第六课：深度分析你的量化策略表现
让你真正看懂策略的优劣！
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.style as style
from datetime import datetime, timedelta

# =================================================================
# == 第五课核心代码：SimpleQuantStrategy (稍作修改以支持分析) ==
# =================================================================
class SimpleQuantStrategy:
    """
    简单量化策略类
    基于动量因子的股票选择策略 (来自第五课)
    """
    
    def __init__(self, initial_capital=100000, all_stock_data=None):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_history = []
        self.all_stock_data = all_stock_data  # 存储所有历史数据

        print(f"🎯 初始化量化策略")
        print(f"  初始资金: ${initial_capital:,}")
        print(f"  策略类型: 动量因子选股策略")

    def generate_extended_stock_data(self, days=60):
        print(f"\n📊 生成 {days} 天的股票数据用于回测...")
        stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX']
        dates = pd.date_range(start='2024-01-01', periods=days, freq='D')
        np.random.seed(42)
        stock_data = {}
        for i, stock in enumerate(stocks):
            base_price = 100 + i * 30
            daily_trend = -0.0005 + i * 0.0003
            volatility = 0.015 + i * 0.002
            prices = [base_price]
            for day in range(days - 1):
                random_shock = np.random.normal(0, volatility)
                trend_component = daily_trend
                cycle_component = 0.002 * np.sin(day * 2 * np.pi / 20)
                if np.random.random() < 0.05: shock = np.random.normal(0, 0.03)
                else: shock = 0
                total_return = trend_component + cycle_component + random_shock + shock
                new_price = prices[-1] * (1 + total_return)
                prices.append(max(new_price, 0.1))
            df = pd.DataFrame({'close': prices}, index=dates)
            df['symbol'] = stock
            stock_data[stock] = df
        print(f"✅ 成功生成 {len(stocks)} 只股票，每只 {days} 天的数据")
        self.all_stock_data = stock_data
        return stock_data

    def calculate_all_factors(self, stock_data):
        factor_data = {}
        for stock, df in stock_data.items():
            factors = {}
            if len(df) >= 21:
                factors['momentum_10d'] = (df['close'].iloc[-1] / df['close'].iloc[-11] - 1) * 100
                factors['momentum_20d'] = (df['close'].iloc[-1] / df['close'].iloc[-21] - 1) * 100
            if len(df) >= 20:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                if not pd.isna(rsi.iloc[-1]):
                    factors['rsi'] = rsi.iloc[-1]
                sma_20 = df['close'].rolling(20).mean().iloc[-1]
                if not pd.isna(sma_20):
                    factors['price_to_sma20'] = (df['close'].iloc[-1] / sma_20 - 1) * 100
            factor_data[stock] = factors
        return factor_data

    def generate_trading_signals(self, factor_data):
        momentum_scores = {}
        technical_scores = {}
        for stock, factors in factor_data.items():
            momentum_score = 0
            if 'momentum_20d' in factors: momentum_score += factors['momentum_20d'] * 0.6
            if 'momentum_10d' in factors: momentum_score += factors['momentum_10d'] * 0.4
            momentum_scores[stock] = momentum_score
            technical_score = 0
            if 'rsi' in factors:
                rsi = factors['rsi']
                if 30 <= rsi <= 70: technical_score += 5
                elif rsi > 70: technical_score -= abs(rsi - 70) * 0.2
                elif rsi < 30: technical_score += (30 - rsi) * 0.3
            if 'price_to_sma20' in factors:
                price_pos = factors['price_to_sma20']
                if price_pos > 0: technical_score += min(price_pos * 0.5, 10)
            technical_scores[stock] = technical_score
        
        composite_scores = {}
        for stock in factor_data.keys():
            momentum_norm = momentum_scores.get(stock, 0) / 10
            technical_norm = technical_scores.get(stock, 0) / 10
            composite_scores[stock] = (momentum_norm * 0.6 + technical_norm * 0.4)
        
        sorted_stocks = sorted(composite_scores.items(), key=lambda x: x[1], reverse=True)
        buy_signals = [stock for stock, _ in sorted_stocks[:3]]
        sell_signals = [stock for stock, _ in sorted_stocks[-2:]]
        
        return {'buy': buy_signals, 'sell': sell_signals }

    def execute_trades(self, signals, stock_data, trading_date):
        print(f"\n💼 执行交易 ({trading_date.strftime('%Y-%m-%d')})...")
        for stock in signals['sell']:
            if stock in self.positions:
                shares = self.positions[stock]['shares']
                current_price = stock_data[stock]['close'].iloc[-1]
                sell_value = shares * current_price
                buy_price = self.positions[stock]['price']
                profit = (current_price - buy_price) * shares
                trade = {'date': trading_date, 'stock': stock, 'action': 'SELL', 'shares': shares, 'price': current_price, 'pnl': profit}
                self.trades.append(trade)
                self.current_capital += sell_value
                print(f"  🔴 卖出 {stock}: {shares}股 @ ${current_price:.2f}, 盈亏: ${profit:+,.0f}")
                del self.positions[stock]

        if signals['buy']:
            available_capital = self.current_capital * 0.9
            capital_per_stock = available_capital / len(signals['buy'])
            for stock in signals['buy']:
                if stock not in self.positions:
                    current_price = stock_data[stock]['close'].iloc[-1]
                    shares = int(capital_per_stock / current_price)
                    if shares > 0:
                        buy_value = shares * current_price
                        trade = {'date': trading_date, 'stock': stock, 'action': 'BUY', 'shares': shares, 'price': current_price, 'pnl': 0}
                        self.trades.append(trade)
                        self.current_capital -= buy_value
                        self.positions[stock] = {'shares': shares, 'price': current_price, 'date': trading_date}
                        print(f"  🟢 买入 {stock}: {shares}股 @ ${current_price:.2f}, 投入: ${buy_value:,.0f}")
        print(f"  💰 剩余现金: ${self.current_capital:,.0f}")

    def calculate_portfolio_value(self, stock_data, date):
        cash = self.current_capital
        positions_value = 0
        for stock, position in self.positions.items():
            current_price = stock_data[stock]['close'].loc[date]
            positions_value += position['shares'] * current_price
        total_value = cash + positions_value
        return {'total': total_value, 'cash': cash, 'positions': positions_value}

    def run_backtest(self, start_date='2024-01-20', end_date='2024-02-29'):
        print(f"\n🚀 开始策略回测")
        print(f"  回测期间: {start_date} 至 {end_date}")
        print("="*60)
        
        self.generate_extended_stock_data(60)
        
        rebalance_dates = pd.date_range(start=start_date, end=end_date, freq='10D')
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # 每日记录净值
        for date in all_dates:
            if date < rebalance_dates[0]: continue

            # 如果是调仓日，则执行交易
            if date in rebalance_dates:
                current_data_for_factors = {stk: df.loc[:date] for stk, df in self.all_stock_data.items()}
                factor_data = self.calculate_all_factors(current_data_for_factors)
                signals = self.generate_trading_signals(factor_data)
                self.execute_trades(signals, current_data_for_factors, date)

            # 每天更新和记录组合价值
            current_data_for_value = {stk: df for stk, df in self.all_stock_data.items()}
            portfolio_value = self.calculate_portfolio_value(current_data_for_value, date)
            self.portfolio_history.append({
                'date': date,
                'total_value': portfolio_value['total'],
                'cash': portfolio_value['cash'],
                'positions_value': portfolio_value['positions'],
            })
            if date in rebalance_dates:
                 print(f"📊 投资组合价值: ${portfolio_value['total']:,.0f} (收益率: {(portfolio_value['total']/self.initial_capital - 1)*100:+.1f}%)")

# =======================================================
# == 第六课新内容：StrategyAnalyzer ==
# =======================================================
class StrategyAnalyzer:
    """
    专业的策略表现分析器
    """
    def __init__(self, strategy):
        """
        用一个已运行的策略实例来初始化分析器
        """
        print("\n\n🔬 初始化策略分析器...")
        if not strategy.portfolio_history:
            raise ValueError("策略尚未运行或没有生成历史数据！")
        
        self.strategy = strategy
        self.perf_df = pd.DataFrame(strategy.portfolio_history).set_index('date')
        self.trades_df = pd.DataFrame(strategy.trades)
        
        # 准备分析所需数据
        self.perf_df['returns'] = self.perf_df['total_value'].pct_change()
        self.perf_df.dropna(inplace=True)
        
        self.periods_per_year = 365 / 10 # 假设每年365天，每10天调仓一次
        
        print("✅ 分析器准备就绪，已加载策略数据。")

    def _create_benchmark(self):
        """
        创建一个等权重基准，用于对比
        """
        print("⚖️ 创建等权重基准...")
        start_date = self.perf_df.index[0]
        end_date = self.perf_df.index[-1]
        
        # 获取所有股票在回测期间的价格数据
        all_prices = []
        for stock, df in self.strategy.all_stock_data.items():
            # 确保索引是datetime对象
            df.index = pd.to_datetime(df.index)
            # 筛选在回测期间的数据
            prices_in_period = df.loc[start_date:end_date]['close'].rename(stock)
            all_prices.append(prices_in_period)
        
        # 合并所有股票的价格
        prices_df = pd.concat(all_prices, axis=1)
        
        # 计算每日的等权重组合回报率
        benchmark_returns = prices_df.pct_change().mean(axis=1)
        
        # 计算基准的累计净值
        benchmark_nav = (1 + benchmark_returns).cumprod() * self.strategy.initial_capital
        benchmark_nav[start_date] = self.strategy.initial_capital # 确保起始值一致
        benchmark_nav = benchmark_nav.sort_index()
        
        self.perf_df['benchmark_returns'] = benchmark_returns
        self.perf_df['benchmark_value'] = benchmark_nav
        self.perf_df.ffill(inplace=True) # 向前填充周末等缺失的数据

    def calculate_metrics(self):
        """
        计算所有核心性能指标
        """
        print("🧮 计算核心性能指标...")
        metrics = {}
        
        # 1. 总体回报
        total_return = (self.perf_df['total_value'].iloc[-1] / self.perf_df['total_value'].iloc[0]) - 1
        annualized_return = (1 + total_return) ** (365 / len(self.perf_df)) - 1
        metrics['Total Return'] = f"{total_return:.2%}"
        metrics['Annualized Return'] = f"{annualized_return:.2%}"

        # 2. 波动率
        annualized_volatility = self.perf_df['returns'].std() * np.sqrt(self.periods_per_year)
        metrics['Annualized Volatility'] = f"{annualized_volatility:.2%}"

        # 3. 夏普比率 (假设无风险利率为0)
        sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility != 0 else 0
        metrics['Sharpe Ratio'] = f"{sharpe_ratio:.2f}"

        # 4. 最大回撤
        self.perf_df['peak'] = self.perf_df['total_value'].cummax()
        self.perf_df['drawdown'] = (self.perf_df['total_value'] - self.perf_df['peak']) / self.perf_df['peak']
        max_drawdown = self.perf_df['drawdown'].min()
        metrics['Max Drawdown'] = f"{max_drawdown:.2%}"

        # 5. Calmar 比率
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        metrics['Calmar Ratio'] = f"{calmar_ratio:.2f}"

        # 6. 索提诺比率 (只考虑下行风险)
        downside_returns = self.perf_df['returns'][self.perf_df['returns'] < 0]
        downside_std = downside_returns.std() * np.sqrt(self.periods_per_year)
        sortino_ratio = annualized_return / downside_std if downside_std != 0 else 0
        metrics['Sortino Ratio'] = f"{sortino_ratio:.2f}"
        
        # 7. 交易统计
        sell_trades = self.trades_df[self.trades_df['action'] == 'SELL']
        if not sell_trades.empty:
            win_trades = sell_trades[sell_trades['pnl'] > 0]
            metrics['Win Rate'] = f"{len(win_trades) / len(sell_trades):.2%}"
            metrics['Profit Factor'] = f"{sell_trades[sell_trades['pnl'] > 0]['pnl'].sum() / abs(sell_trades[sell_trades['pnl'] < 0]['pnl'].sum()):.2f}"
        else:
            metrics['Win Rate'] = "N/A"
            metrics['Profit Factor'] = "N/A"
            
        self.metrics = metrics
        return metrics

    def display_summary(self):
        """
        用一个漂亮的表格打印性能总结
        """
        print("\n" + "="*60)
        print("               策略表现评估报告")
        print("="*60)
        
        summary = pd.Series(self.metrics).to_string()
        print(summary)
        print("="*60)

    def plot_performance(self):
        """
        绘制策略表现图表
        """
        print("📊 正在生成可视化图表...")
        style.use('seaborn-v0_8-darkgrid')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        
        # 图1: 净值曲线 vs 基准
        ax1.set_title('Strategy Equity Curve vs. Benchmark', fontsize=16)
        ax1.plot(self.perf_df.index, self.perf_df['total_value'], label='Strategy', color='royalblue', linewidth=2)
        ax1.plot(self.perf_df.index, self.perf_df['benchmark_value'], label='Benchmark (Equal Weight)', color='gray', linestyle='--')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True)
        
        # 图2: 回撤图
        ax2.set_title('Drawdown', fontsize=14)
        ax2.fill_between(self.perf_df.index, self.perf_df['drawdown'] * 100, 0, color='indianred', alpha=0.5)
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Date')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('strategy_analysis.png', dpi=150, bbox_inches='tight')
        print("📊 图表已保存为 strategy_analysis.png")
        plt.close()

    def run_analysis(self):
        """
        运行完整的分析流程
        """
        self._create_benchmark()
        self.calculate_metrics()
        self.display_summary()
        self.plot_performance()

def main():
    """
    主函数：结合策略回测与深度分析
    """
    print("🎯 量化交易学习第六课：深度策略表现分析")
    print("="*60)
    print("🚀 首先，我们像第五课一样运行策略回测...")
    
    # 1. 创建并运行策略
    strategy = SimpleQuantStrategy(initial_capital=100000)
    strategy.run_backtest()
    
    print("\n\n✅ 策略回测完成！现在进入深度分析环节...")
    
    # 2. 使用分析器分析策略
    try:
        analyzer = StrategyAnalyzer(strategy)
        analyzer.run_analysis()
        print("\n🎉 恭喜！你完成了专业的策略表现分析！")
        print("\n💡 你现在掌握了:")
        print("  1. 如何计算夏普比率、最大回撤等关键指标")
        print("  2. 如何创建基准并进行对比")
        print("  3. 如何用图表清晰地展示策略的净值曲线和风险")
        print("  4. 构建一个标准化的分析流程，可用于评估任何策略")
        print("\n🚀 下一步：我们将学习如何优化策略参数！")

    except ValueError as e:
        print(f"\n❌ 分析失败: {e}")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    main()
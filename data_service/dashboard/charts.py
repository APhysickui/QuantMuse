import plotly.graph_objects as go
import plotly.express as px
import plotly.subplots as sp
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

class ChartGenerator:
    """Generate interactive charts for trading dashboard"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def create_equity_curve(self, equity_data: pd.DataFrame, 
                           benchmark_data: Optional[pd.DataFrame] = None) -> go.Figure:
        """Create equity curve chart"""
        # 使用绝对导入路径
        try:
            from data_service.dashboard.widgets import DashboardWidgets
            self.widgets = DashboardWidgets()
        except ImportError as e:
            self.logger.warning(f"无法导入DashboardWidgets: {e}")
            self.widgets = None
        """Create equity curve chart"""
        fig = go.Figure()
        
        # Add strategy equity curve
        fig.add_trace(go.Scatter(
            x=equity_data.index,
            y=equity_data['equity'],
            mode='lines',
            name='Strategy',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='<b>Date:</b> %{x}<br>' +
                         '<b>Equity:</b> $%{y:,.2f}<br>' +
                         '<extra></extra>'
        ))
        
        # Add benchmark if provided
        if benchmark_data is not None:
            fig.add_trace(go.Scatter(
                x=benchmark_data.index,
                y=benchmark_data['equity'],
                mode='lines',
                name='Benchmark',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                hovertemplate='<b>Date:</b> %{x}<br>' +
                             '<b>Benchmark:</b> $%{y:,.2f}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            title='Equity Curve',
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def create_drawdown_chart(self, drawdown_data: pd.Series) -> go.Figure:
        """Create drawdown chart"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=drawdown_data.index,
            y=drawdown_data.values * 100,  # Convert to percentage
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(255, 0, 0, 0.3)',
            line=dict(color='red', width=2),
            name='Drawdown',
            hovertemplate='<b>Date:</b> %{x}<br>' +
                         '<b>Drawdown:</b> %{y:.2f}%<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title='Drawdown Analysis',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            hovermode='x unified',
            template='plotly_white',
            height=300
        )
        
        return fig
    
    def create_returns_distribution(self, returns: pd.Series) -> go.Figure:
        """Create returns distribution histogram"""
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=returns.values * 100,  # Convert to percentage
            nbinsx=30,
            name='Returns',
            marker_color='#1f77b4',
            opacity=0.7,
            hovertemplate='<b>Return:</b> %{x:.2f}%<br>' +
                         '<b>Frequency:</b> %{y}<br>' +
                         '<extra></extra>'
        ))
        
        # Add normal distribution overlay
        mu = returns.mean() * 100
        sigma = returns.std() * 100
        x_norm = np.linspace(returns.min() * 100, returns.max() * 100, 100)
        y_norm = len(returns) * (returns.max() - returns.min()) / 30 * \
                 (1 / (sigma * np.sqrt(2 * np.pi))) * \
                 np.exp(-0.5 * ((x_norm - mu) / sigma) ** 2)
        
        fig.add_trace(go.Scatter(
            x=x_norm,
            y=y_norm,
            mode='lines',
            name='Normal Distribution',
            line=dict(color='red', width=2),
            hovertemplate='<b>Return:</b> %{x:.2f}%<br>' +
                         '<b>Density:</b> %{y:.2f}<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title='Returns Distribution',
            xaxis_title='Daily Returns (%)',
            yaxis_title='Frequency',
            template='plotly_white',
            height=300
        )
        
        return fig
    
    def create_rolling_metrics(self, returns: pd.Series, 
                              window: int = 252) -> go.Figure:
        """Create rolling Sharpe ratio and volatility chart"""
        fig = sp.make_subplots(
            rows=2, cols=1,
            subplot_titles=('Rolling Sharpe Ratio', 'Rolling Volatility'),
            vertical_spacing=0.1
        )
        
        # Calculate rolling metrics
        rolling_sharpe = returns.rolling(window).mean() / returns.rolling(window).std() * np.sqrt(252)
        rolling_vol = returns.rolling(window).std() * np.sqrt(252) * 100
        
        # Sharpe ratio
        fig.add_trace(
            go.Scatter(
                x=rolling_sharpe.index,
                y=rolling_sharpe.values,
                mode='lines',
                name='Sharpe Ratio',
                line=dict(color='#1f77b4', width=2),
                hovertemplate='<b>Date:</b> %{x}<br>' +
                             '<b>Sharpe:</b> %{y:.3f}<br>' +
                             '<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Volatility
        fig.add_trace(
            go.Scatter(
                x=rolling_vol.index,
                y=rolling_vol.values,
                mode='lines',
                name='Volatility',
                line=dict(color='#ff7f0e', width=2),
                hovertemplate='<b>Date:</b> %{x}<br>' +
                             '<b>Volatility:</b> %{y:.2f}%<br>' +
                             '<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title=f'Rolling Metrics ({window}-day window)',
            template='plotly_white',
            height=500,
            showlegend=False
        )
        
        return fig
    
    def create_trade_analysis(self, trades: pd.DataFrame) -> go.Figure:
        """Create trade analysis chart"""
        fig = sp.make_subplots(
            rows=2, cols=2,
            subplot_titles=('Trade P&L Distribution', 'Cumulative P&L', 
                          'Trade Duration', 'Win/Loss Ratio'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "pie"}]]
        )
        
        # Trade P&L distribution
        fig.add_trace(
            go.Histogram(
                x=trades['pnl'],
                nbinsx=20,
                name='P&L Distribution',
                marker_color='#1f77b4',
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Cumulative P&L
        cumulative_pnl = trades['pnl'].cumsum()
        fig.add_trace(
            go.Scatter(
                x=trades.index,
                y=cumulative_pnl,
                mode='lines',
                name='Cumulative P&L',
                line=dict(color='#2ca02c', width=2)
            ),
            row=1, col=2
        )
        
        # Trade duration
        fig.add_trace(
            go.Histogram(
                x=trades['duration'],
                nbinsx=15,
                name='Duration',
                marker_color='#ff7f0e',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Win/Loss pie chart
        wins = (trades['pnl'] > 0).sum()
        losses = (trades['pnl'] <= 0).sum()
        
        fig.add_trace(
            go.Pie(
                labels=['Wins', 'Losses'],
                values=[wins, losses],
                marker_colors=['#2ca02c', '#d62728'],
                name='Win/Loss'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title='Trade Analysis',
            template='plotly_white',
            height=600,
            showlegend=False
        )
        
        return fig
    
    def create_factor_analysis(self, factor_data: pd.DataFrame, 
                              factor_returns: pd.Series) -> go.Figure:
        """Create factor analysis chart"""
        fig = sp.make_subplots(
            rows=2, cols=2,
            subplot_titles=('Factor Performance', 'Factor Correlation', 
                          'Factor Returns', 'Factor Weights'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Factor performance over time
        for factor in factor_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=factor_data.index,
                    y=factor_data[factor],
                    mode='lines',
                    name=factor,
                    line=dict(width=2)
                ),
                row=1, col=1
            )
        
        # Factor correlation heatmap
        corr_matrix = factor_data.corr()
        fig.add_trace(
            go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0
            ),
            row=1, col=2
        )
        
        # Factor returns
        fig.add_trace(
            go.Bar(
                x=factor_returns.index,
                y=factor_returns.values,
                name='Factor Returns',
                marker_color='#1f77b4'
            ),
            row=2, col=1
        )
        
        # Factor weights (assuming equal weights for demo)
        weights = pd.Series([1/len(factor_data.columns)] * len(factor_data.columns), 
                           index=factor_data.columns)
        fig.add_trace(
            go.Pie(
                labels=weights.index,
                values=weights.values,
                name='Factor Weights'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title='Factor Analysis',
            template='plotly_white',
            height=600,
            showlegend=False
        )
        
        return fig
    
    def create_real_time_price_chart(self, price_data: pd.DataFrame, 
                                   symbol: str) -> go.Figure:
        """Create real-time price chart (candlestick)"""
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=price_data.index,
            open=price_data['open'],
            high=price_data['high'],
            low=price_data['low'],
            close=price_data['close'],
            name=symbol,
            increasing_line_color='#2ca02c',
            decreasing_line_color='#d62728'
        ))
        
        fig.update_layout(
            title=f'{symbol} Price Chart',
            xaxis_title='Time',
            yaxis_title='Price ($)',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def create_order_flow_chart(self, orders: pd.DataFrame) -> go.Figure:
        """Create order flow chart"""
        fig = go.Figure()
        
        # Buy orders
        buy_orders = orders[orders['side'] == 'buy']
        if not buy_orders.empty:
            fig.add_trace(go.Scatter(
                x=buy_orders['timestamp'],
                y=buy_orders['price'],
                mode='markers',
                name='Buy Orders',
                marker=dict(
                    color='green',
                    size=8,
                    symbol='triangle-up'
                ),
                hovertemplate='<b>Time:</b> %{x}<br>' +
                             '<b>Price:</b> $%{y:.2f}<br>' +
                             '<b>Quantity:</b> %{text}<br>' +
                             '<extra></extra>',
                text=buy_orders['quantity']
            ))
        
        # Sell orders
        sell_orders = orders[orders['side'] == 'sell']
        if not sell_orders.empty:
            fig.add_trace(go.Scatter(
                x=sell_orders['timestamp'],
                y=sell_orders['price'],
                mode='markers',
                name='Sell Orders',
                marker=dict(
                    color='red',
                    size=8,
                    symbol='triangle-down'
                ),
                hovertemplate='<b>Time:</b> %{x}<br>' +
                             '<b>Price:</b> $%{y:.2f}<br>' +
                             '<b>Quantity:</b> %{text}<br>' +
                             '<extra></extra>',
                text=sell_orders['quantity']
            ))
        
        fig.update_layout(
            title='Order Flow',
            xaxis_title='Time',
            yaxis_title='Price ($)',
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def create_performance_summary(self, metrics: Dict[str, float]) -> go.Figure:
        """Create performance metrics summary"""
        # Create a table-like visualization
        fig = go.Figure()
        
        # Prepare data for display
        metric_names = list(metrics.keys())
        metric_values = list(metrics.values())
        
        # Format values based on metric type
        formatted_values = []
        for name, value in metrics.items():
            if 'return' in name.lower() or 'ratio' in name.lower():
                formatted_values.append(f"{value:.2%}")
            elif 'drawdown' in name.lower():
                formatted_values.append(f"{value:.2%}")
            elif 'trades' in name.lower():
                formatted_values.append(f"{int(value)}")
            else:
                formatted_values.append(f"{value:.4f}")
        
        fig.add_trace(go.Table(
            header=dict(
                values=['Metric', 'Value'],
                fill_color='#1f77b4',
                font=dict(color='white', size=14),
                align='left'
            ),
            cells=dict(
                values=[metric_names, formatted_values],
                fill_color='white',
                font=dict(size=12),
                align='left',
                height=30
            )
        ))
        
        fig.update_layout(
            title='Performance Summary',
            template='plotly_white',
            height=400
        )
        
        return fig 
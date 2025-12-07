import pandas as pd
import numpy as np
from typing import Dict
import logging
from dataclasses import dataclass

from data_service.utils.exceptions import ProcessingError


@dataclass
class MarketAnalysis:
    """市场分析结果"""
    indicators: Dict[str, pd.Series]  # 技术指标
    statistics: Dict[str, float]      # 统计数据
    signals: Dict[str, bool]          # 交易信号


class DataProcessor:
    """数据处理服务"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.required_columns = ['open', 'high', 'low', 'close', 'volume']

    def process_market_data(self, df: pd.DataFrame) -> MarketAnalysis:
        """处理市场数据"""
        # 验证数据
        self._validate_data(df)

        # 计算技术指标
        indicators = self._calculate_indicators(df)

        # 计算统计数据
        statistics = self._calculate_statistics(df)

        # 生成交易信号
        signals = self._generate_signals(df, indicators)

        return MarketAnalysis(
            indicators=indicators,
            statistics=statistics,
            signals=signals
        )

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算技术指标"""
        indicators: Dict[str, pd.Series] = {}

        # MA
        indicators['MA5'] = df['close'].rolling(5).mean()
        indicators['MA10'] = df['close'].rolling(10).mean()
        indicators['MA20'] = df['close'].rolling(20).mean()

        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        indicators['MACD'] = exp1 - exp2
        indicators['Signal'] = indicators['MACD'].ewm(span=9, adjust=False).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        indicators['BB_middle'] = df['close'].rolling(20).mean()
        std = df['close'].rolling(20).std()
        indicators['BB_upper'] = indicators['BB_middle'] + (std * 2)
        indicators['BB_lower'] = indicators['BB_middle'] - (std * 2)

        return indicators

    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算统计数据"""
        return {
            'daily_return': df['close'].pct_change().mean(),
            'volatility': df['close'].pct_change().std() * np.sqrt(252),
            'current_price': df['close'].iloc[-1],
            'volume': df['volume'].iloc[-1],
            'high_52w': df['high'].rolling(252).max().iloc[-1],
            'low_52w': df['low'].rolling(252).min().iloc[-1],
        }

    def _generate_signals(self, df: pd.DataFrame,
                          indicators: Dict[str, pd.Series]) -> Dict[str, bool]:
        """生成交易信号"""
        return {
            'golden_cross': indicators['MA5'].iloc[-1] > indicators['MA20'].iloc[-1]
            and indicators['MA5'].iloc[-2] <= indicators['MA20'].iloc[-2],
            'death_cross': indicators['MA5'].iloc[-1] < indicators['MA20'].iloc[-1]
            and indicators['MA5'].iloc[-2] >= indicators['MA20'].iloc[-2],
            'overbought': indicators['RSI'].iloc[-1] > 70,
            'oversold': indicators['RSI'].iloc[-1] < 30,
            'macd_bullish': indicators['MACD'].iloc[-1] > indicators['Signal'].iloc[-1],
            'macd_bearish': indicators['MACD'].iloc[-1] < indicators['Signal'].iloc[-1],
        }

    def _validate_data(self, df: pd.DataFrame) -> None:
        """验证数据完整性，失败时抛出 ProcessingError"""
        if df.empty:
            raise ProcessingError("Empty dataframe provided")

        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ProcessingError(f"Missing required columns: {missing_columns}")

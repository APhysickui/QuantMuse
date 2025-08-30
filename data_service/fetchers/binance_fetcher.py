from binance.spot import Spot
from datetime import datetime
import pandas as pd
import logging
from typing import Optional, Dict, Any, Callable
from ..utils.exceptions import DataFetchError

class BinanceFetcher:
    """Binance数据获取器"""
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None,
                 use_proxy: bool = True,
                 proxy_host: str = "127.0.0.1",
                 proxy_port: str = "7890"):
        """
        初始化Binance客户端
        :param api_key: Binance API key (可选)
        :param api_secret: Binance API secret (可选)
        :param use_proxy: 是否使用代理
        :param proxy_host: 代理主机地址
        :param proxy_port: 代理端口
        """
        self.logger = logging.getLogger(__name__)
        try:
            # 配置代理
            proxies = None
            if use_proxy:
                proxy_url = f"http://{proxy_host}:{proxy_port}"
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }
                self.logger.info(f"Using proxy: {proxy_url}")

            # 初始化客户端
            self.client = Spot(
                api_key=api_key, 
                api_secret=api_secret,
                proxies=proxies
            )
            self.logger.info("Binance fetcher initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Binance client: {str(e)}")
            raise

    def fetch_historical_data(
        self,
        symbol: str = "BTCUSDT",  # 注意：symbol格式变更为 BTCUSDT
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        获取历史K线数据
        :param symbol: 交易对
        :param interval: K线间隔
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param limit: 返回的K线数量
        :return: DataFrame包含OHLCV数据
        """
        try:
            # 转换时间格式
            start_str = int(start_time.timestamp() * 1000) if start_time else None
            end_str = int(end_time.timestamp() * 1000) if end_time else None
            
            # 获取K线数据
            klines = self.client.klines(
                symbol=symbol,
                interval=interval,
                startTime=start_str,
                endTime=end_str,
                limit=limit
            )
            
            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # 处理数据类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_columns] = df[numeric_columns].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            self.logger.info(f"Successfully fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {str(e)}")
            raise DataFetchError(f"Failed to fetch historical data: {str(e)}")

    def get_order_book(self, symbol: str = "BTCUSDT", limit: int = 100) -> Dict:
        """
        获取订单簿数据
        :param symbol: 交易对
        :param limit: 订单簿深度
        :return: 订单簿数据
        """
        try:
            depth = self.client.depth(symbol=symbol, limit=limit)
            return {
                'bids': [[float(price), float(qty)] for price, qty in depth['bids']],
                'asks': [[float(price), float(qty)] for price, qty in depth['asks']]
            }
        except Exception as e:
            self.logger.error(f"Error fetching order book: {str(e)}")
            raise DataFetchError(f"Failed to fetch order book: {str(e)}")

    def get_recent_trades(self, symbol: str = "BTCUSDT", limit: int = 100) -> pd.DataFrame:
        """
        获取最近成交
        :param symbol: 交易对
        :param limit: 返回的成交数量
        :return: 最近成交数据
        """
        try:
            trades = self.client.trades(symbol=symbol, limit=limit)
            df = pd.DataFrame(trades)
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            df['price'] = df['price'].astype(float)
            df['qty'] = df['qty'].astype(float)
            return df
        except Exception as e:
            self.logger.error(f"Error fetching recent trades: {str(e)}")
            raise DataFetchError(f"Failed to fetch recent trades: {str(e)}")

    def get_current_price(self, symbol: str = "BTCUSDT") -> float:
        """
        获取当前价格
        :param symbol: 交易对
        :return: 当前价格
        """
        try:
            ticker = self.client.ticker_price(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            self.logger.error(f"Error fetching current price: {str(e)}")
            raise DataFetchError(f"Failed to fetch current price: {str(e)}")
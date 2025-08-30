import requests
import pandas as pd
from datetime import datetime
import logging
from typing import Optional, Dict, Any

class CoinGeckoFetcher:
    """CoinGecko数据获取器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 CoinGecko 客户端
        :param api_key: CoinGecko API Key (可选,但某些端点需要)
        """
        self.logger = logging.getLogger(__name__)
        # 使用普通 API URL（适用于Demo API Key）
        self.base_url = "https://api.coingecko.com/api/v3"
        self.api_key = api_key
        
        # 使用正确的 Demo API key 参数名
        self.api_params = {"x_cg_demo_api_key": api_key} if api_key else {}
        
        if api_key:
            self.logger.info("初始化 CoinGecko API with Demo key")
        
    def get_current_price(self, symbol: str = "BTC") -> float:
        """
        获取当前价格
        :param symbol: 货币符号 (BTC, ETH 等)
        :return: 当前价格 (USD)
        """
        try:
            # 转换符号格式
            coin_id = self._convert_symbol_to_id(symbol)
            
            # 构建API请求
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd"
            }
            # 添加 API key 到查询参数
            params.update(self.api_params)
            
            # 记录完整的请求URL和参数（用于调试）
            self.logger.debug(f"请求URL: {url}")
            self.logger.debug(f"请求参数: {params}")
            
            # 发送请求
            response = requests.get(url, params=params)
            
            # 详细的错误处理
            if response.status_code == 401:
                self.logger.error("API认证失败。请检查：1. API Key是否正确 2. 是否有访问该端点的权限")
                raise Exception(f"API认证失败：{response.text}")
            elif response.status_code == 429:
                self.logger.error("超出API调用限制")
                raise Exception(f"超出API调用限制：{response.text}")
            elif response.status_code != 200:
                self.logger.error(f"API请求失败，状态码：{response.status_code}")
                raise Exception(f"API请求失败：{response.text}")
            
            # 如果请求成功，解析JSON响应
            data = response.json()
            
            # 提取价格
            price = data[coin_id]["usd"]
            self.logger.info(f"Successfully fetched current price for {symbol}: ${price}")
            return price
            
        except Exception as e:
            self.logger.error(f"Error fetching current price: {str(e)}")
            raise
    
    def fetch_historical_data(
        self,
        symbol: str = "BTC",
        days: str = "2",  # 必须在2-90天之间才能获取小时级数据
        limit_hours: Optional[int] = 24,  # 可选：限制返回最近几个小时的数据
        max_retries: int = 3  # 添加重试次数参数
    ) -> pd.DataFrame:
        """
        获取历史价格数据
        :param symbol: 货币符号
        :param days: 获取天数(必须在2-90之间才能获取小时级数据)
        :param limit_hours: 可选，限制只返回最近N小时的数据
        :param max_retries: 最大重试次数
        :return: DataFrame包含价格和交易量数据
        """
        """
        获取历史价格数据
        :param symbol: 货币符号
        :param days: 获取天数
        :param interval: 时间间隔 (hourly/daily)
        :return: DataFrame包含价格和交易量数据
        """
        try:
            # 转换符号格式
            coin_id = self._convert_symbol_to_id(symbol)
            
            # 验证天数参数
            try:
                days_int = int(days)
                if not (2 <= days_int <= 90):
                    raise ValueError("days 参数必须在2-90之间才能获取小时级数据")
            except ValueError as e:
                self.logger.error(str(e))
                raise
                
            # 构建API请求
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days
            }
            # 添加 API key 到查询参数
            params.update(self.api_params)
            
            # 添加重试逻辑
            retry_count = 0
            while retry_count < max_retries:
                try:
                    self.logger.info(f"正在请求历史数据 (尝试 {retry_count + 1}/{max_retries}): {url}")
                    self.logger.debug(f"请求参数: {params}")
                    response = requests.get(url, params=params)
                    
                    # 如果请求成功，直接跳出循环
                    if response.status_code == 200:
                        break
                        
                    # 如果是401错误，直接抛出异常（不需要重试）
                    if response.status_code == 401:
                        raise Exception(f"API认证失败: {response.text}")
                        
                    # 其他错误等待后重试
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count  # 指数退避
                        self.logger.warning(f"请求失败，{wait_time}秒后重试...")
                        import time
                        time.sleep(wait_time)
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"网络错误: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 2 ** retry_count
                        self.logger.warning(f"网络错误，{wait_time}秒后重试...")
                        import time
                        time.sleep(wait_time)
                    else:
                        raise
            
            # 如果所有重试都失败了
            if retry_count == max_retries and response.status_code != 200:
                raise Exception(f"达到最大重试次数，请求仍然失败：{response.text}")
            
            # 详细的错误处理
            if response.status_code == 401:
                self.logger.error("API认证失败。请检查：1. API Key是否正确 2. 是否有访问该端点的权限")
                raise Exception(f"API认证失败：{response.text}")
            elif response.status_code == 429:
                self.logger.error("超出API调用限制")
                raise Exception(f"超出API调用限制：{response.text}")
            elif response.status_code != 200:
                self.logger.error(f"API请求失败，状态码：{response.status_code}")
                raise Exception(f"API请求失败：{response.text}")
            
            # 如果请求成功，解析JSON响应
            data = response.json()
            
            # 转换为DataFrame
            prices_df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
            volumes_df = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
            
            # 合并数据
            df = prices_df.merge(volumes_df[["timestamp", "volume"]], on="timestamp")
            
            # 处理时间戳
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            
            # 按时间降序排序
            df = df.sort_index(ascending=False)
            
            # 如果指定了小时数限制，只返回最近N小时的数据
            if limit_hours:
                self.logger.info(f"正在限制返回最近 {limit_hours} 小时的数据...")
                # 确保数据是按小时对齐的
                df = df.resample('H').last().dropna()
                df = df.head(limit_hours)
                # 恢复原始的时间顺序（升序）
                df = df.sort_index(ascending=True)
            
            self.logger.info(f"成功获取 {symbol} 的历史数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {str(e)}")
            raise
            
    def get_market_data(self, symbol: str = "BTC") -> Dict:
        """
        获取市场数据
        :param symbol: 货币符号
        :return: 市场数据字典
        """
        try:
            coin_id = self._convert_symbol_to_id(symbol)
            url = f"{self.base_url}/coins/{coin_id}"
            self.logger.info(f"正在请求市场数据: {url}")
            response = requests.get(url, params=self.api_params)
            
            # 详细的错误处理
            if response.status_code == 401:
                self.logger.error("API认证失败。请检查：1. API Key是否正确 2. 是否有访问该端点的权限")
                raise Exception(f"API认证失败：{response.text}")
            elif response.status_code == 429:
                self.logger.error("超出API调用限制")
                raise Exception(f"超出API调用限制：{response.text}")
            elif response.status_code != 200:
                self.logger.error(f"API请求失败，状态码：{response.status_code}")
                raise Exception(f"API请求失败：{response.text}")
            
            # 如果请求成功，解析JSON响应
            data = response.json()
            
            market_data = {
                "current_price": data["market_data"]["current_price"]["usd"],
                "market_cap": data["market_data"]["market_cap"]["usd"],
                "total_volume": data["market_data"]["total_volume"]["usd"],
                "price_change_24h": data["market_data"]["price_change_percentage_24h"],
                "price_change_7d": data["market_data"]["price_change_percentage_7d"],
                "price_change_30d": data["market_data"]["price_change_percentage_30d"]
            }
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error fetching market data: {str(e)}")
            raise
    
    def _convert_symbol_to_id(self, symbol: str) -> str:
        """
        转换交易对符号为CoinGecko的coin_id
        """
        # 移除USDT后缀并转换为小写
        symbol = symbol.lower().replace("usdt", "")
        
        # 常用货币映射
        symbol_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "bnb": "binancecoin",
            "sol": "solana",
            "xrp": "ripple",
            "ada": "cardano",
            "doge": "dogecoin",
            # 可以根据需要添加更多映射
        }
        
        return symbol_map.get(symbol, symbol)

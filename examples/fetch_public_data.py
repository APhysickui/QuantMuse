from data_service.fetchers.coingecko_fetcher import CoinGeckoFetcher
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        print("正在初始化 CoinGecko API...")
        # 初始化 CoinGecko fetcher with Demo API key
        fetcher = CoinGeckoFetcher(api_key="CG-KR7HtkPQiycJwDhsxrKQpt7B")
        
        print("\n1. 获取当前价格...")
        # 获取 BTC 当前价格
        btc_price = fetcher.get_current_price("BTC")
        print(f"✅ BTC 当前价格: ${btc_price:,.2f}")
        
        print("\n2. 获取历史数据...")
                # 获取历史数据 (获取2天数据，但只返回最近24小时)
        df = fetcher.fetch_historical_data(
            symbol="BTC",
            days="2",     # 请求2天的数据（API要求最少2天）
            limit_hours=24  # 但只保留最近24小时
        )
        print("✅ 成功获取历史数据")
        print("\n最近的价格记录:")
        print(df.head())
        
        # 获取市场数据
        market_data = fetcher.get_market_data("BTC")
        print("\nMarket data:")
        for key, value in market_data.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()
import unittest
from unittest.mock import Mock, patch
import pandas as pd

from data_service.fetchers.binance_fetcher import BinanceFetcher
from data_service.utils.exceptions import DataFetchError


class TestBinanceFetcher(unittest.TestCase):
    """Test cases for BinanceFetcher"""

    def setUp(self):
        """Set up test fixtures"""
        # Patch the Spot client used inside BinanceFetcher so no real API calls are made
        self.spot_patcher = patch('data_service.fetchers.binance_fetcher.Spot')
        self.mock_spot_class = self.spot_patcher.start()

        # Configure the mock client instance returned by Spot(...)
        self.mock_client_instance = Mock()
        self.mock_spot_class.return_value = self.mock_client_instance

        # Create fetcher with mocked client
        self.fetcher = BinanceFetcher(use_proxy=False)

    def tearDown(self):
        """Clean up after each test"""
        self.spot_patcher.stop()

    def test_initialization(self):
        """Test if fetcher initializes correctly"""
        self.assertIsNotNone(self.fetcher.client)

    def test_fetch_historical_data(self):
        """Test historical data fetching"""
        # Mock data returned by Spot.klines
        mock_klines = [
            [
                1499040000000,  # Timestamp
                "8100.0",       # Open
                "8200.0",       # High
                "8000.0",       # Low
                "8150.0",       # Close
                "100.0",        # Volume
                1499644799999,  # Close time
                "1000.0",       # Quote volume
                100,            # Number of trades
                "50.0",         # Taker buy base
                "400.0",        # Taker buy quote
                "0"            # Ignore
            ]
        ]

        # Configure mock
        self.mock_client_instance.klines.return_value = mock_klines

        # Execute test
        df = self.fetcher.fetch_historical_data("BTCUSDT")

        # Verify results
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(float(df['close'].iloc[0]), 8150.0)
        self.mock_client_instance.klines.assert_called_once()

    def test_invalid_symbol(self):
        """Test handling of invalid symbol"""
        # Configure mock to raise an exception from the underlying client
        self.mock_client_instance.klines.side_effect = Exception("Invalid symbol")

        with self.assertRaises(DataFetchError):
            self.fetcher.fetch_historical_data("")

    def test_market_depth(self):
        """Test market depth fetching"""
        # Mock order book data
        mock_depth = {
            'bids': [['8100.0', '1.0'], ['8099.0', '2.0']],
            'asks': [['8101.0', '1.0'], ['8102.0', '2.0']]
        }

        # Configure mock depth response
        self.mock_client_instance.depth.return_value = mock_depth

        # Execute test using compatibility wrapper
        depth = self.fetcher.get_market_depth("BTCUSDT")

        # Verify results
        self.assertIn('bids', depth)
        self.assertIn('asks', depth)
        self.assertEqual(len(depth['bids']), 2)
        self.assertEqual(len(depth['asks']), 2)


if __name__ == '__main__':
    unittest.main()

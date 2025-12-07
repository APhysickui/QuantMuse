import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch

from data_service.ai.llm_integration import (
    LLMIntegration,
    LLMResponse,
    TradingInsight,
    OpenAIProvider,
    LocalLLMProvider,
)


class TestLLMIntegration(unittest.TestCase):
    """Test cases for LLM Integration module"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_market_data = pd.DataFrame({
            'AAPL_return': [0.01, -0.02, 0.03, 0.01, -0.01],
            'GOOGL_return': [0.02, -0.01, 0.04, -0.02, 0.01],
            'volume': [1000000, 1200000, 900000, 1100000, 1300000],
        })

        self.sample_factor_data = pd.DataFrame({
            'momentum_20d': [0.05, -0.03, 0.08, 0.02, -0.01],
            'pe_ratio': [25.5, 30.2, 22.1, 28.3, 26.7],
            'roe': [0.15, 0.12, 0.18, 0.14, 0.16],
        })

        self.sample_price_data = pd.DataFrame({
            'close': [150, 148, 152, 151, 149],
            'volume': [1000000, 1200000, 900000, 1100000, 1300000],
        })

    def test_llm_response_dataclass(self):
        """Test LLMResponse dataclass"""
        response = LLMResponse(
            content="Test response",
            confidence=0.8,
            metadata={'test': 'data'},
            timestamp=datetime.now(),
            model_used="gpt-3.5-turbo",
            tokens_used=100,
            cost=0.002,
        )

        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.confidence, 0.8)
        self.assertEqual(response.tokens_used, 100)
        self.assertEqual(response.cost, 0.002)

    def test_trading_insight_dataclass(self):
        """Test TradingInsight dataclass"""
        insight = TradingInsight(
            insight_type="signal",
            content="Buy signal for AAPL",
            confidence=0.7,
            symbols=["AAPL"],
            timeframe="1d",
            reasoning="Strong momentum and positive earnings",
            timestamp=datetime.now(),
        )

        self.assertEqual(insight.insight_type, "signal")
        self.assertEqual(insight.symbols, ["AAPL"])
        self.assertEqual(insight.confidence, 0.7)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_llm_integration_initialization(self, mock_provider):
        """Test LLMIntegration initialization"""
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(
            provider="openai",
            api_key="test-key",
            model="gpt-3.5-turbo",
        )

        self.assertIsNotNone(llm.provider)
        mock_provider.assert_called_once_with("test-key", "gpt-3.5-turbo")

    def test_llm_integration_invalid_provider(self):
        """Test LLMIntegration with invalid provider"""
        with self.assertRaises(ValueError):
            LLMIntegration(provider="invalid_provider")

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_market_analysis(self, mock_provider):
        """Test market analysis functionality"""
        # Mock provider response
        mock_response = LLMResponse(
            content='{"trend": "bullish", "levels": [150, 155], "catalysts": ["earnings"]}',
            confidence=0.8,
            metadata={},
            timestamp=datetime.now(),
            model_used="gpt-3.5-turbo",
            tokens_used=100,
        )

        mock_provider_instance = Mock()
        mock_provider_instance.generate_response.return_value = mock_response
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        insight = llm.analyze_market_data(self.sample_market_data, ['AAPL', 'GOOGL'])

        self.assertEqual(insight.insight_type, "analysis")
        self.assertEqual(insight.symbols, ['AAPL', 'GOOGL'])
        self.assertIsInstance(insight.confidence, float)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_signal_generation(self, mock_provider):
        """Test trading signal generation"""
        # Mock provider response
        mock_response = LLMResponse(
            content='{"signal_type": "buy", "confidence": 0.7, "reasoning": "strong momentum"}',
            confidence=0.7,
            metadata={},
            timestamp=datetime.now(),
            model_used="gpt-3.5-turbo",
            tokens_used=100,
        )

        mock_provider_instance = Mock()
        mock_provider_instance.generate_response.return_value = mock_response
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        insight = llm.generate_trading_signals(
            self.sample_factor_data,
            self.sample_price_data,
            "momentum strategy",
        )

        self.assertEqual(insight.insight_type, "signal")
        self.assertIsInstance(insight.confidence, float)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_risk_assessment(self, mock_provider):
        """Test risk assessment functionality"""
        # Mock provider response
        mock_response = LLMResponse(
            content='{"overall_risk": "medium", "risk_factors": ["volatility"], "recommendations": ["reduce exposure"]}',
            confidence=0.8,
            metadata={},
            timestamp=datetime.now(),
            model_used="gpt-3.5-turbo",
            tokens_used=100,
        )

        mock_provider_instance = Mock()
        mock_provider_instance.generate_response.return_value = mock_response
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        portfolio_data = {
            'total_value': 1000000,
            'positions': {'AAPL': {'quantity': 100, 'avg_price': 150}},
            'cash': 200000,
        }

        market_conditions = {
            'volatility_index': 25.5,
            'market_trend': 'bearish',
        }

        insight = llm.assess_risk(portfolio_data, market_conditions)

        self.assertEqual(insight.insight_type, "risk_warning")
        self.assertIsInstance(insight.confidence, float)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_portfolio_optimization(self, mock_provider):
        """Test portfolio optimization functionality"""
        # Mock provider response
        mock_response = LLMResponse(
            content='{"suggested_weights": {"AAPL": 0.4}, "expected_return": 0.12, "risk_level": "medium"}',
            confidence=0.8,
            metadata={},
            timestamp=datetime.now(),
            model_used="gpt-3.5-turbo",
            tokens_used=100,
        )

        mock_provider_instance = Mock()
        mock_provider_instance.generate_response.return_value = mock_response
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        current_weights = {'AAPL': 0.3, 'GOOGL': 0.7}
        factor_scores = {
            'AAPL': {'momentum': 0.05, 'value': 0.04},
            'GOOGL': {'momentum': 0.03, 'value': 0.03},
        }
        constraints = {'min_weight': 0.05, 'max_weight': 0.8}

        insight = llm.optimize_portfolio(current_weights, factor_scores, constraints)

        self.assertEqual(insight.insight_type, "recommendation")
        self.assertIsInstance(insight.confidence, float)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_question_answering(self, mock_provider):
        """Test question answering functionality"""
        # Mock provider response
        mock_response = LLMResponse(
            content="Momentum trading considers price trends, volume, and relative strength.",
            confidence=0.8,
            metadata={},
            timestamp=datetime.now(),
            model_used="gpt-3.5-turbo",
            tokens_used=100,
        )

        mock_provider_instance = Mock()
        mock_provider_instance.generate_response.return_value = mock_response
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        response = llm.answer_trading_question(
            "What are the key factors for momentum trading?",
        )

        self.assertIsInstance(response, LLMResponse)
        self.assertIsInstance(response.content, str)
        self.assertIsInstance(response.confidence, float)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_create_default_insight(self, mock_provider):
        """Test default insight creation"""
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        insight = llm._create_default_insight("signal", ["AAPL"])

        self.assertEqual(insight.insight_type, "signal")
        self.assertEqual(insight.symbols, ["AAPL"])
        self.assertEqual(insight.confidence, 0.0)
        self.assertIn("Unable to generate insight", insight.content)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_parse_trading_insight_json(self, mock_provider):
        """Test parsing JSON trading insight"""
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        json_content = '{"signal_type": "buy", "confidence": 0.8, "reasoning": "strong momentum"}'
        insight = llm._parse_trading_insight(json_content, "signal", ["AAPL"])

        self.assertEqual(insight.insight_type, "signal")
        self.assertEqual(insight.symbols, ["AAPL"])
        self.assertIn("strong momentum", insight.reasoning)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_parse_trading_insight_text(self, mock_provider):
        """Test parsing text trading insight"""
        mock_provider_instance = Mock()
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        text_content = "This is a simple text response without JSON"
        insight = llm._parse_trading_insight(text_content, "analysis", ["GOOGL"])

        self.assertEqual(insight.insight_type, "analysis")
        self.assertEqual(insight.symbols, ["GOOGL"])
        self.assertEqual(insight.reasoning, text_content)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_provider_info(self, mock_provider):
        """Test provider information retrieval"""
        mock_provider_instance = Mock()
        mock_provider_instance.get_model_info.return_value = {
            'provider': 'OpenAI',
            'model': 'gpt-test',
        }
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        info = llm.get_provider_info()
        self.assertIsInstance(info, dict)
        self.assertIn('provider', info)
        self.assertIn('model', info)

    @patch('data_service.ai.llm_integration.OpenAIProvider')
    def test_usage_stats(self, mock_provider):
        """Test usage statistics"""
        mock_provider_instance = Mock()
        mock_provider_instance.get_model_info.return_value = {
            'provider': 'OpenAI',
            'model': 'gpt-test',
        }
        mock_provider.return_value = mock_provider_instance

        llm = LLMIntegration(provider="openai", api_key="test-key")

        stats = llm.get_usage_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('provider', stats)
        self.assertIn('model', stats)
        self.assertIn('timestamp', stats)


if __name__ == '__main__':
    unittest.main()

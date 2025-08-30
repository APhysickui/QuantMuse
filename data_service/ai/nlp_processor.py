import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from collections import Counter

@dataclass
class ProcessedText:
    """Processed text data structure"""
    original_text: str
    cleaned_text: str
    tokens: List[str]
    keywords: List[str]
    sentiment_score: float
    sentiment_label: str
    topics: List[str]
    language: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    sentiment_score: float  # -1 to 1
    sentiment_label: str    # 'positive', 'negative', 'neutral'
    confidence: float
    keywords: List[str]
    topics: List[str]
    timestamp: datetime

class NLPProcessor:
    """NLP processing for financial text analysis"""
    
    def __init__(self, use_spacy: bool = True, use_transformers: bool = True):
        self.logger = logging.getLogger(__name__)
        self.use_spacy = use_spacy
        self.use_transformers = use_transformers
        
        # Initialize NLP components
        self._init_nlp_components()
        
        # Financial keywords for sentiment analysis
        self.financial_keywords = {
            'positive': [
                'bullish', 'rally', 'surge', 'gain', 'profit', 'earnings', 'growth',
                'positive', 'strong', 'up', 'higher', 'increase', 'beat', 'exceed',
                'optimistic', 'favorable', 'outperform', 'buy', 'long', 'target'
            ],
            'negative': [
                'bearish', 'decline', 'drop', 'fall', 'loss', 'miss', 'weak',
                'negative', 'down', 'lower', 'decrease', 'disappoint', 'worse',
                'pessimistic', 'unfavorable', 'underperform', 'sell', 'short', 'risk'
            ]
        }
    
    def _init_nlp_components(self):
        """Initialize NLP components"""
        try:
            # Initialize spaCy
            if self.use_spacy:
                import spacy
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    self.logger.info("spaCy model loaded successfully")
                except OSError:
                    self.logger.warning("spaCy model not found, downloading...")
                    spacy.cli.download("en_core_web_sm")
                    self.nlp = spacy.load("en_core_web_sm")
            else:
                self.nlp = None
            
            # Initialize transformers
            if self.use_transformers:
                try:
                    from transformers import pipeline
                    import torch
                    
                    # 强制使用 CPU 设备
                    device = torch.device("cpu")
                    self.logger.info(f"Device force set to use CPU")
                    
                    self.sentiment_pipeline = pipeline(
                        "sentiment-analysis",
                        model="cardiffnlp/twitter-roberta-base-sentiment",
                        device=device  # 指定使用 CPU
                    )
                    self.logger.info("Transformers sentiment pipeline loaded on CPU")
                except ImportError:
                    self.logger.warning("Transformers not available")
                    self.sentiment_pipeline = None
            else:
                self.sentiment_pipeline = None
            
            # Initialize NLTK
            try:
                import nltk
                from nltk.corpus import stopwords
                from nltk.tokenize import word_tokenize
                from nltk.stem import WordNetLemmatizer
                
                # Download required NLTK data
                try:
                    nltk.data.find('tokenizers/punkt')
                except LookupError:
                    nltk.download('punkt')
                
                try:
                    nltk.data.find('corpora/stopwords')
                except LookupError:
                    nltk.download('stopwords')
                
                try:
                    nltk.data.find('corpora/wordnet')
                except LookupError:
                    nltk.download('wordnet')
                
                self.stop_words = set(stopwords.words('english'))
                self.lemmatizer = WordNetLemmatizer()
                self.word_tokenize = word_tokenize
                self.logger.info("NLTK components loaded successfully")
                
            except ImportError:
                self.logger.warning("NLTK not available")
                self.stop_words = set()
                self.lemmatizer = None
                self.word_tokenize = None
            
        except Exception as e:
            self.logger.error(f"Error initializing NLP components: {e}")
            self.nlp = None
            self.sentiment_pipeline = None
            self.stop_words = set()
            self.lemmatizer = None
            self.word_tokenize = None
    
    def preprocess_text(self, text: str) -> ProcessedText:
        """Preprocess text for analysis"""
        try:
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Tokenize
            if self.nlp:
                tokens = self._tokenize_with_spacy(cleaned_text)
            elif self.word_tokenize:
                tokens = self._tokenize_with_nltk(cleaned_text)
            else:
                tokens = cleaned_text.lower().split()
            
            # Extract keywords
            keywords = self._extract_keywords(tokens)
            
            # Analyze sentiment
            sentiment_score, sentiment_label = self._analyze_sentiment(cleaned_text)
            
            # Extract topics
            topics = self._extract_topics(tokens)
            
            # Detect language
            language = self._detect_language(cleaned_text)
            
            return ProcessedText(
                original_text=text,
                cleaned_text=cleaned_text,
                tokens=tokens,
                keywords=keywords,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                topics=topics,
                language=language,
                timestamp=datetime.now(),
                metadata={}
            )
            
        except Exception as e:
            self.logger.error(f"Error preprocessing text: {e}")
            return self._create_default_processed_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and hashtags
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Remove special characters but keep financial symbols
        text = re.sub(r'[^\w\s\$\%\.\,\+\-]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _tokenize_with_spacy(self, text: str) -> List[str]:
        """Tokenize using spaCy"""
        doc = self.nlp(text)
        tokens = [token.text.lower() for token in doc 
                 if not token.is_stop and not token.is_punct and token.text.strip()]
        return tokens
    
    def _tokenize_with_nltk(self, text: str) -> List[str]:
        """Tokenize using NLTK"""
        tokens = self.word_tokenize(text.lower())
        tokens = [token for token in tokens 
                 if token not in self.stop_words and token.isalpha()]
        return tokens
    
    def _extract_keywords(self, tokens: List[str]) -> List[str]:
        """Extract keywords from tokens"""
        # Simple frequency-based keyword extraction
        token_freq = Counter(tokens)
        
        # Filter out common words and short tokens
        keywords = [token for token, freq in token_freq.most_common(20)
                   if len(token) > 3 and freq > 1]
        
        return keywords[:10]  # Return top 10 keywords
    
    def _analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """Analyze sentiment of text"""
        sentiment_score = 0.0
        sentiment_label = 'neutral'
        
        # Use transformers if available
        if self.sentiment_pipeline:
            try:
                result = self.sentiment_pipeline(text)[0]
                label_to_score = {'LABEL_0': -1, 'LABEL_1': 0, 'LABEL_2': 1}
                sentiment_score = label_to_score.get(result['label'], 0)
                sentiment_label = 'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'neutral'
            except Exception as e:
                self.logger.warning(f"Transformers sentiment analysis failed: {e}")
        
        # Fallback to keyword-based sentiment
        if sentiment_score == 0.0:
            sentiment_score = self._keyword_based_sentiment(text)
            sentiment_label = 'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'neutral'
        
        return sentiment_score, sentiment_label
    
    def _keyword_based_sentiment(self, text: str) -> float:
        """Simple keyword-based sentiment analysis"""
        text_lower = text.lower()
        positive_count = sum(1 for word in self.financial_keywords['positive'] 
                           if word in text_lower)
        negative_count = sum(1 for word in self.financial_keywords['negative'] 
                           if word in text_lower)
        
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_keywords
    
    def _extract_topics(self, tokens: List[str]) -> List[str]:
        """Extract topics from tokens"""
        # Simple topic extraction based on financial terms
        financial_topics = {
            'earnings': ['earnings', 'revenue', 'profit', 'income', 'quarterly'],
            'market': ['market', 'trading', 'stock', 'price', 'volume'],
            'economy': ['economy', 'inflation', 'interest', 'rate', 'fed'],
            'technology': ['tech', 'software', 'digital', 'innovation', 'ai'],
            'crypto': ['bitcoin', 'crypto', 'blockchain', 'ethereum', 'token']
        }
        
        topics = []
        for topic, keywords in financial_topics.items():
            if any(keyword in tokens for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _detect_language(self, text: str) -> str:
        """Detect language of text"""
        # Simple language detection based on common words
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of']
        english_count = sum(1 for word in english_words if word in text.lower())
        
        if english_count > 2:
            return 'en'
        else:
            return 'unknown'
    
    def _create_default_processed_text(self, text: str) -> ProcessedText:
        """Create default processed text when preprocessing fails"""
        return ProcessedText(
            original_text=text,
            cleaned_text=text,
            tokens=text.lower().split(),
            keywords=[],
            sentiment_score=0.0,
            sentiment_label='neutral',
            topics=[],
            language='unknown',
            timestamp=datetime.now(),
            metadata={'error': 'preprocessing_failed'}
        )
    
    def analyze_sentiment_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze sentiment for multiple texts"""
        results = []
        
        for text in texts:
            try:
                processed = self.preprocess_text(text)
                
                result = SentimentResult(
                    text=text,
                    sentiment_score=processed.sentiment_score,
                    sentiment_label=processed.sentiment_label,
                    confidence=0.7,  # Default confidence
                    keywords=processed.keywords,
                    topics=processed.topics,
                    timestamp=processed.timestamp
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error analyzing sentiment for text: {e}")
                # Add default result
                results.append(SentimentResult(
                    text=text,
                    sentiment_score=0.0,
                    sentiment_label='neutral',
                    confidence=0.0,
                    keywords=[],
                    topics=[],
                    timestamp=datetime.now()
                ))
        
        return results
    
    def calculate_market_sentiment(self, sentiment_results: List[SentimentResult]) -> Dict[str, Any]:
        """Calculate overall market sentiment from multiple results"""
        if not sentiment_results:
            return {
                'overall_sentiment': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'top_keywords': [],
                'top_topics': []
            }
        
        # Calculate sentiment statistics
        sentiment_scores = [r.sentiment_score for r in sentiment_results]
        overall_sentiment = np.mean(sentiment_scores)
        
        # Calculate sentiment distribution
        labels = [r.sentiment_label for r in sentiment_results]
        positive_ratio = labels.count('positive') / len(labels)
        negative_ratio = labels.count('negative') / len(labels)
        neutral_ratio = labels.count('neutral') / len(labels)
        
        # Determine overall sentiment label
        if positive_ratio > 0.5:
            sentiment_label = 'positive'
        elif negative_ratio > 0.5:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # Extract top keywords and topics
        all_keywords = []
        all_topics = []
        for result in sentiment_results:
            all_keywords.extend(result.keywords)
            all_topics.extend(result.topics)
        
        top_keywords = [word for word, count in Counter(all_keywords).most_common(10)]
        top_topics = [topic for topic, count in Counter(all_topics).most_common(5)]
        
        return {
            'overall_sentiment': overall_sentiment,
            'sentiment_label': sentiment_label,
            'confidence': np.std(sentiment_scores),  # Lower std = higher confidence
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': neutral_ratio,
            'top_keywords': top_keywords,
            'top_topics': top_topics
        }
    
    def extract_financial_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract financial entities from text"""
        entities = {
            'companies': [],
            'currencies': [],
            'numbers': [],
            'percentages': [],
            'dates': []
        }
        
        if self.nlp:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    entities['companies'].append(ent.text)
                elif ent.label_ == 'MONEY':
                    entities['currencies'].append(ent.text)
                elif ent.label_ == 'CARDINAL':
                    entities['numbers'].append(ent.text)
                elif ent.label_ == 'PERCENT':
                    entities['percentages'].append(ent.text)
                elif ent.label_ == 'DATE':
                    entities['dates'].append(ent.text)
        
        # Use regex as fallback
        if not entities['currencies']:
            currency_pattern = r'\$[\d,]+\.?\d*'
            entities['currencies'] = re.findall(currency_pattern, text)
        
        if not entities['percentages']:
            percent_pattern = r'\d+\.?\d*%'
            entities['percentages'] = re.findall(percent_pattern, text)
        
        return entities 
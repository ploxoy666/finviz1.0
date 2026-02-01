"""
Market Context Module
Adds market-wide context and sentiment analysis capabilities
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class MarketContextAnalyzer:
    """Analyzes broader market context to improve predictions"""
    
    def __init__(self):
        """Initialize market context analyzer"""
        self.sp500_data = None
        self.vix_data = None
        self.market_correlation = None
        
    def fetch_sp500_data(self, period="2y"):
        """
        Fetch S&P 500 index data for market context
        
        Args:
            period (str): Time period to fetch
            
        Returns:
            bool: Success status
        """
        try:
            sp500 = yf.Ticker("^GSPC")
            self.sp500_data = sp500.history(period=period)
            
            if not self.sp500_data.empty:
                # Calculate S&P 500 returns
                self.sp500_data['Returns'] = self.sp500_data['Close'].pct_change()
                print("S&P 500 data fetched successfully")
                return True
            return False
            
        except Exception as e:
            print(f"Error fetching S&P 500 data: {e}")
            return False
    
    def fetch_vix_data(self, period="2y"):
        """
        Fetch VIX (volatility index) data
        
        Args:
            period (str): Time period to fetch
            
        Returns:
            bool: Success status
        """
        try:
            vix = yf.Ticker("^VIX")
            self.vix_data = vix.history(period=period)
            
            if not self.vix_data.empty:
                print("VIX data fetched successfully")
                return True
            return False
            
        except Exception as e:
            print(f"Error fetching VIX data: {e}")
            return False
    
    def calculate_market_correlation(self, stock_data):
        """
        Calculate correlation between stock and S&P 500
        
        Args:
            stock_data (pd.DataFrame): Stock price data with returns
            
        Returns:
            float: Correlation coefficient
        """
        if self.sp500_data is None:
            self.fetch_sp500_data()
        
        try:
            # Align dates
            merged = pd.merge(
                stock_data[['Returns']],
                self.sp500_data[['Returns']],
                left_index=True,
                right_index=True,
                suffixes=('_stock', '_sp500')
            )
            
            # Calculate correlation
            self.market_correlation = merged['Returns_stock'].corr(merged['Returns_sp500'])
            
            return self.market_correlation
            
        except Exception as e:
            print(f"Error calculating market correlation: {e}")
            return None
    
    def get_market_regime(self):
        """
        Determine current market regime based on S&P 500 and VIX
        
        Returns:
            dict: Market regime information
        """
        regime = {
            'type': 'Unknown',
            'volatility': 'Unknown',
            'trend': 'Unknown',
            'confidence': 0.0
        }
        
        try:
            if self.sp500_data is not None and len(self.sp500_data) > 0:
                # Calculate recent trend
                recent_return = (self.sp500_data['Close'].iloc[-1] / 
                                self.sp500_data['Close'].iloc[-20] - 1)
                
                # Determine trend
                if recent_return > 0.05:
                    regime['trend'] = 'Strong Bullish'
                    regime['confidence'] = 0.8
                elif recent_return > 0.02:
                    regime['trend'] = 'Bullish'
                    regime['confidence'] = 0.6
                elif recent_return < -0.05:
                    regime['trend'] = 'Strong Bearish'
                    regime['confidence'] = 0.8
                elif recent_return < -0.02:
                    regime['trend'] = 'Bearish'
                    regime['confidence'] = 0.6
                else:
                    regime['trend'] = 'Sideways'
                    regime['confidence'] = 0.5
            
            if self.vix_data is not None and len(self.vix_data) > 0:
                current_vix = self.vix_data['Close'].iloc[-1]
                
                # Determine volatility regime
                if current_vix > 30:
                    regime['volatility'] = 'High Fear'
                    regime['type'] = 'Crisis'
                elif current_vix > 20:
                    regime['volatility'] = 'Elevated'
                    regime['type'] = 'Uncertain'
                elif current_vix < 12:
                    regime['volatility'] = 'Complacent'
                    regime['type'] = 'Calm'
                else:
                    regime['volatility'] = 'Normal'
                    regime['type'] = 'Stable'
        
        except Exception as e:
            print(f"Error determining market regime: {e}")
        
        return regime
    
    def add_market_features(self, stock_data):
        """
        Add market context features to stock data
        
        Args:
            stock_data (pd.DataFrame): Stock data
            
        Returns:
            pd.DataFrame: Data with added market features
        """
        df = stock_data.copy()
        
        try:
            # Fetch market data if not already fetched
            if self.sp500_data is None:
                self.fetch_sp500_data(period="2y")
            if self.vix_data is None:
                self.fetch_vix_data(period="2y")
            
            # Merge S&P 500 returns
            if self.sp500_data is not None:
                sp500_returns = self.sp500_data[['Returns']].rename(
                    columns={'Returns': 'SP500_Returns'}
                )
                df = pd.merge(df, sp500_returns, left_index=True, 
                            right_index=True, how='left')
                
                # Calculate relative performance
                df['Relative_Performance'] = df['Returns'] - df['SP500_Returns']
                
                # Calculate beta (rolling 60-day)
                df['Beta'] = df['Returns'].rolling(window=60).cov(
                    df['SP500_Returns']
                ) / df['SP500_Returns'].rolling(window=60).var()
            
            # Merge VIX data
            if self.vix_data is not None:
                vix_close = self.vix_data[['Close']].rename(
                    columns={'Close': 'VIX'}
                )
                df = pd.merge(df, vix_close, left_index=True, 
                            right_index=True, how='left')
                
                # VIX change
                df['VIX_Change'] = df['VIX'].pct_change()
        
        except Exception as e:
            print(f"Error adding market features: {e}")
        
        return df
    
    def get_market_summary(self):
        """
        Get a summary of current market conditions
        
        Returns:
            str: Formatted market summary
        """
        regime = self.get_market_regime()
        
        summary = []
        summary.append("\n" + "=" * 60)
        summary.append("MARKET CONTEXT")
        summary.append("=" * 60)
        
        if self.sp500_data is not None and len(self.sp500_data) > 0:
            sp500_current = self.sp500_data['Close'].iloc[-1]
            sp500_20d_ago = self.sp500_data['Close'].iloc[-20]
            sp500_return = (sp500_current / sp500_20d_ago - 1) * 100
            
            summary.append(f"\nS&P 500: {sp500_current:.2f}")
            summary.append(f"20-Day Return: {sp500_return:+.2f}%")
        
        if self.vix_data is not None and len(self.vix_data) > 0:
            vix_current = self.vix_data['Close'].iloc[-1]
            summary.append(f"VIX (Fear Index): {vix_current:.2f}")
        
        summary.append(f"\nMarket Regime: {regime['type']}")
        summary.append(f"Trend: {regime['trend']}")
        summary.append(f"Volatility: {regime['volatility']}")
        
        if self.market_correlation is not None:
            summary.append(f"\nStock-Market Correlation: {self.market_correlation:.3f}")
            
            if abs(self.market_correlation) > 0.7:
                summary.append("  → High correlation with market")
            elif abs(self.market_correlation) < 0.3:
                summary.append("  → Low correlation (more independent)")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)


class SentimentAnalyzer:
    """
    Sentiment analysis framework (extensible for future enhancements)
    Currently provides structure for adding sentiment data
    """
    
    def __init__(self):
        """Initialize sentiment analyzer"""
        self.sentiment_data = None
        self.sentiment_score = None
        
    def add_custom_sentiment(self, dates, scores):
        """
        Add custom sentiment scores
        
        Args:
            dates (list): List of dates
            scores (list): Sentiment scores (-1 to 1, negative to positive)
            
        Returns:
            pd.DataFrame: Sentiment data
        """
        self.sentiment_data = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Sentiment': scores
        })
        self.sentiment_data.set_index('Date', inplace=True)
        
        return self.sentiment_data
    
    def calculate_aggregate_sentiment(self):
        """
        Calculate aggregate sentiment score
        
        Returns:
            float: Average sentiment score
        """
        if self.sentiment_data is not None and len(self.sentiment_data) > 0:
            self.sentiment_score = self.sentiment_data['Sentiment'].mean()
            return self.sentiment_score
        return 0.0
    
    def get_sentiment_trend(self, window=7):
        """
        Get recent sentiment trend
        
        Args:
            window (int): Number of days for trend calculation
            
        Returns:
            str: Trend description
        """
        if self.sentiment_data is None or len(self.sentiment_data) < window:
            return "Insufficient data"
        
        recent = self.sentiment_data['Sentiment'].iloc[-window:]
        trend = recent.iloc[-1] - recent.iloc[0]
        
        if trend > 0.2:
            return "Strongly Improving"
        elif trend > 0.05:
            return "Improving"
        elif trend < -0.2:
            return "Strongly Declining"
        elif trend < -0.05:
            return "Declining"
        else:
            return "Stable"
    
    def merge_sentiment_with_data(self, stock_data):
        """
        Merge sentiment data with stock data
        
        Args:
            stock_data (pd.DataFrame): Stock price data
            
        Returns:
            pd.DataFrame: Data with sentiment features
        """
        if self.sentiment_data is None:
            return stock_data
        
        df = stock_data.copy()
        
        # Merge sentiment data
        df = pd.merge(df, self.sentiment_data, left_index=True, 
                     right_index=True, how='left')
        
        # Forward fill missing sentiment values
        df['Sentiment'] = df['Sentiment'].fillna(method='ffill')
        
        # Add sentiment momentum
        df['Sentiment_Change'] = df['Sentiment'].diff()
        df['Sentiment_MA'] = df['Sentiment'].rolling(window=5).mean()
        
        return df
    
    def get_sentiment_summary(self):
        """
        Get sentiment analysis summary
        
        Returns:
            str: Formatted sentiment summary
        """
        if self.sentiment_data is None:
            return "\nSentiment Analysis: Not available (requires external data)"
        
        summary = []
        summary.append("\n" + "=" * 60)
        summary.append("SENTIMENT ANALYSIS")
        summary.append("=" * 60)
        
        current_sentiment = self.sentiment_data['Sentiment'].iloc[-1]
        avg_sentiment = self.sentiment_data['Sentiment'].mean()
        trend = self.get_sentiment_trend()
        
        summary.append(f"\nCurrent Sentiment: {current_sentiment:.2f}")
        summary.append(f"Average Sentiment: {avg_sentiment:.2f}")
        summary.append(f"Sentiment Trend: {trend}")
        
        if current_sentiment > 0.5:
            summary.append("\n  → Very Positive sentiment")
        elif current_sentiment > 0.2:
            summary.append("\n  → Positive sentiment")
        elif current_sentiment < -0.5:
            summary.append("\n  → Very Negative sentiment")
        elif current_sentiment < -0.2:
            summary.append("\n  → Negative sentiment")
        else:
            summary.append("\n  → Neutral sentiment")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)
    
    def get_integration_guide(self):
        """
        Get guide for integrating external sentiment data
        
        Returns:
            str: Integration guide
        """
        guide = """
        ╔════════════════════════════════════════════════════════════╗
        ║          SENTIMENT ANALYSIS INTEGRATION GUIDE              ║
        ╚════════════════════════════════════════════════════════════╝
        
        To add sentiment analysis to your predictions:
        
        1. NEWS SENTIMENT:
           - Use NewsAPI or similar service
           - Analyze headlines with TextBlob or VADER
           - Convert to scores (-1 to 1)
        
        2. SOCIAL MEDIA SENTIMENT:
           - Twitter API for stock mentions
           - Reddit API for r/stocks, r/wallstreetbets
           - Use sentiment analysis libraries
        
        3. ANALYST RATINGS:
           - Scrape analyst recommendations
           - Convert ratings to scores
           - Weight by analyst reputation
        
        4. EXAMPLE CODE:
           ```python
           from market_context import SentimentAnalyzer
           
           sentiment = SentimentAnalyzer()
           
           # Add your sentiment data
           dates = ['2024-01-01', '2024-01-02']
           scores = [0.5, 0.7]  # Positive sentiment
           
           sentiment.add_custom_sentiment(dates, scores)
           
           # Merge with stock data
           enhanced_data = sentiment.merge_sentiment_with_data(stock_data)
           ```
        
        5. RECOMMENDED SOURCES:
           - FinBERT (financial sentiment)
           - Yahoo Finance sentiment
           - Stocktwits API
           - Alpha Vantage news sentiment
        
        ═══════════════════════════════════════════════════════════════
        """
        return guide

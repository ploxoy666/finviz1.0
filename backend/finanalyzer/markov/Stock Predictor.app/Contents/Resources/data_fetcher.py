"""
Data Fetcher Module
Handles fetching and preprocessing stock market data using yfinance API
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class StockDataFetcher:
    """Fetches and preprocesses stock market data"""
    
    def __init__(self, ticker, period="2y", interval="1d"):
        """
        Initialize the data fetcher
        
        Args:
            ticker (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            period (str): Time period for historical data ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
            interval (str): Data interval ('1d', '1wk', '1mo')
        """
        self.ticker = ticker.upper()
        self.period = period
        self.interval = interval
        self.data = None
        self.processed_data = None
        
    def fetch_data(self):
        """Fetch historical stock data from yfinance"""
        try:
            stock = yf.Ticker(self.ticker)
            self.data = stock.history(period=self.period, interval=self.interval)
            
            if self.data.empty:
                raise ValueError(f"No data found for ticker {self.ticker}")
            
            print(f"Successfully fetched {len(self.data)} data points for {self.ticker}")
            return True
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return False
    
    def calculate_returns(self):
        """Calculate price returns and log returns"""
        self.processed_data = self.data.copy()
        
        # Simple returns
        self.processed_data['Returns'] = self.processed_data['Close'].pct_change()
        
        # Log returns (more suitable for modeling)
        self.processed_data['Log_Returns'] = np.log(self.processed_data['Close'] / 
                                                      self.processed_data['Close'].shift(1))
        
        # Price change
        self.processed_data['Price_Change'] = self.processed_data['Close'].diff()
        
    def calculate_technical_indicators(self):
        """Calculate technical indicators for feature engineering"""
        df = self.processed_data
        
        # Simple Moving Averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Exponential Moving Average
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # MACD (Moving Average Convergence Divergence)
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Relative Strength Index (RSI)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        
        # Volatility (standard deviation of returns)
        df['Volatility'] = df['Returns'].rolling(window=20).std()
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Average True Range (ATR) - volatility indicator
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(window=14).mean()
        
        # Stochastic Oscillator
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['Stochastic_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
        df['Stochastic_D'] = df['Stochastic_K'].rolling(window=3).mean()
        
        # ADX (Average Directional Index) - trend strength
        plus_dm = df['High'].diff()
        minus_dm = -df['Low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = true_range
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX'] = dx.rolling(window=14).mean()
        df['Plus_DI'] = plus_di
        df['Minus_DI'] = minus_di
        
        # OBV (On-Balance Volume) - volume-based momentum
        obv = [0]
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.append(obv[-1] + df['Volume'].iloc[i])
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.append(obv[-1] - df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv
        df['OBV_SMA'] = df['OBV'].rolling(window=20).mean()
        
        self.processed_data = df
    
    def calculate_market_regime(self):
        """Identify market regime (Bull/Bear/Sideways)"""
        df = self.processed_data
        
        # Use SMA crossover and trend strength
        df['Trend'] = np.where(df['SMA_5'] > df['SMA_20'], 1,  # Bullish
                               np.where(df['SMA_5'] < df['SMA_20'], -1,  # Bearish
                                       0))  # Sideways
        
        # Trend strength
        df['Trend_Strength'] = np.abs(df['SMA_5'] - df['SMA_20']) / df['Close']
        
        self.processed_data = df
    
    def preprocess(self):
        """Complete preprocessing pipeline"""
        if self.data is None:
            raise ValueError("No data to process. Call fetch_data() first.")
        
        self.calculate_returns()
        self.calculate_technical_indicators()
        self.calculate_market_regime()
        
        # Drop NaN values
        self.processed_data = self.processed_data.dropna()
        
        print(f"Data preprocessed. {len(self.processed_data)} valid data points available.")
        
        return self.processed_data
    
    def get_data(self):
        """Get the processed data"""
        return self.processed_data
    
    def get_latest_price(self):
        """Get the most recent closing price"""
        if self.processed_data is not None:
            return self.processed_data['Close'].iloc[-1]
        return None
    
    def get_summary_statistics(self):
        """Get summary statistics of the stock"""
        if self.processed_data is None:
            return None
        
        stats = {
            'ticker': self.ticker,
            'current_price': self.get_latest_price(),
            'period_return': (self.processed_data['Close'].iloc[-1] / 
                            self.processed_data['Close'].iloc[0] - 1) * 100,
            'avg_daily_return': self.processed_data['Returns'].mean() * 100,
            'volatility': self.processed_data['Returns'].std() * 100,
            'max_price': self.processed_data['Close'].max(),
            'min_price': self.processed_data['Close'].min(),
            'avg_volume': self.processed_data['Volume'].mean(),
            'data_points': len(self.processed_data)
        }
        
        return stats

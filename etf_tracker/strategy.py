"""
Strategy Module for ETF Technical Analysis
Implements various technical indicators and provides buy/sell signals
"""
import pandas as pd
import numpy as np
import ta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETFStrategy:
    """Class to implement technical analysis strategies for ETFs"""
    
    def __init__(self, data):
        """
        Initialize the strategy calculator
        
        Args:
            data (pandas.DataFrame): OHLCV data for the ETF
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Data must be a pandas DataFrame")
        
        if data.empty:
            raise ValueError("Empty DataFrame provided")
            
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")
        
        self.data = data.copy()
        # Convert index to datetime if not already
        if not isinstance(self.data.index, pd.DatetimeIndex):
            try:
                self.data.index = pd.to_datetime(self.data.index)
            except Exception as e:
                logger.warning(f"Could not convert index to datetime: {e}")
                
        logger.info(f"Initialized ETFStrategy with {len(data)} data points")
        
    def calculate_all_indicators(self):
        """
        Calculate all technical indicators
        
        Returns:
            pandas.DataFrame: Data with indicators added
        """
        try:
            # Make a copy to avoid modifying the original
            df = self.data.copy()
            
            # Calculate Moving Averages
            df = self.add_moving_averages(df)
            
            # Calculate KD (Stochastic Oscillator)
            df = self.add_kd_indicator(df)
            
            # Calculate MACD
            df = self.add_macd_indicator(df)
            
            # Calculate RSI
            df = self.add_rsi(df)
            
            return df
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None
            
    def add_moving_averages(self, df, periods=[5, 10, 20, 60]):
        """
        Add simple moving averages to the dataframe
        
        Args:
            df (pandas.DataFrame): Price data
            periods (list): List of periods for moving averages
            
        Returns:
            pandas.DataFrame: DataFrame with MAs added
        """
        for period in periods:
            df[f'MA_{period}'] = ta.trend.sma_indicator(df['Close'], window=period)
        return df
        
    def add_kd_indicator(self, df, k_period=9, d_period=3):
        """
        Add Stochastic Oscillator (KD) indicator
        
        Args:
            df (pandas.DataFrame): Price data
            k_period (int): K period
            d_period (int): D period
            
        Returns:
            pandas.DataFrame: DataFrame with KD indicator added
        """
        stoch = ta.momentum.StochasticOscillator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=k_period,
            smooth_window=d_period
        )
        df['K'] = stoch.stoch()
        df['D'] = stoch.stoch_signal()
        return df
        
    def add_macd_indicator(self, df, fast=12, slow=26, signal=9):
        """
        Add MACD indicator
        
        Args:
            df (pandas.DataFrame): Price data
            fast (int): Fast period
            slow (int): Slow period
            signal (int): Signal period
            
        Returns:
            pandas.DataFrame: DataFrame with MACD indicator added
        """
        macd = ta.trend.MACD(
            close=df['Close'],
            window_fast=fast,
            window_slow=slow,
            window_sign=signal
        )
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        return df
        
    def add_rsi(self, df, period=14):
        """
        Add RSI indicator
        
        Args:
            df (pandas.DataFrame): Price data
            period (int): RSI period
            
        Returns:
            pandas.DataFrame: DataFrame with RSI added
        """
        df['RSI'] = ta.momentum.rsi(df['Close'], window=period)
        return df
    
    def generate_signals(self, df=None):
        """
        Generate buy/sell signals based on indicators
        
        Args:
            df (pandas.DataFrame, optional): Data with indicators. If None, uses calculate_all_indicators()
            
        Returns:
            pandas.DataFrame: DataFrame with signals added
        """
        if df is None:
            df = self.calculate_all_indicators()
            
        if df is None:
            return None
            
        # Initialize signal column (0 = neutral/hold)
        df['Signal'] = 0
        
        # Generate KD signals
        self._generate_kd_signals(df)
        
        # Generate MACD signals
        self._generate_macd_signals(df)
        
        # Generate MA crossover signals
        self._generate_ma_signals(df)
        
        # Generate combined signal
        df['SignalStrength'] = df['Signal'].rolling(window=3).mean()
        
        # Define signal categories
        def categorize_signal(row):
            strength = row['SignalStrength']
            if strength >= 0.7:
                return 'Strong Buy'
            elif strength >= 0.3:
                return 'Buy'
            elif strength <= -0.7:
                return 'Strong Sell'
            elif strength <= -0.3:
                return 'Sell'
            else:
                return 'Hold'
                
        df['SignalCategory'] = df.apply(categorize_signal, axis=1)
        
        return df
    
    def _generate_kd_signals(self, df):
        """Generate signals based on KD indicator"""
        # Buy signal: K crosses above D from below in oversold territory
        df.loc[(df['K'] > df['D']) & (df['K'].shift(1) <= df['D'].shift(1)) & (df['K'] < 30), 'Signal'] += 1
        
        # Sell signal: K crosses below D from above in overbought territory
        df.loc[(df['K'] < df['D']) & (df['K'].shift(1) >= df['D'].shift(1)) & (df['K'] > 70), 'Signal'] -= 1
    
    def _generate_macd_signals(self, df):
        """Generate signals based on MACD indicator"""
        # Buy signal: MACD crosses above signal line
        df.loc[(df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1)), 'Signal'] += 1
        
        # Sell signal: MACD crosses below signal line
        df.loc[(df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1)), 'Signal'] -= 1
    
    def _generate_ma_signals(self, df):
        """Generate signals based on MA crossovers"""
        # Buy signal: 5-day MA crosses above 20-day MA
        if 'MA_5' in df.columns and 'MA_20' in df.columns:
            df.loc[(df['MA_5'] > df['MA_20']) & (df['MA_5'].shift(1) <= df['MA_20'].shift(1)), 'Signal'] += 1
            
            # Sell signal: 5-day MA crosses below 20-day MA
            df.loc[(df['MA_5'] < df['MA_20']) & (df['MA_5'].shift(1) >= df['MA_20'].shift(1)), 'Signal'] -= 1
    
    def get_latest_signal(self, df=None):
        """
        Get the latest signal from the data
        
        Args:
            df (pandas.DataFrame, optional): Data with signals. If None, uses generate_signals()
            
        Returns:
            dict: Latest signal information
        """
        if df is None:
            df = self.generate_signals()
            
        if df is None or df.empty:
            return None
            
        # Get the last row
        last_row = df.iloc[-1]
        
        signal_info = {
            'date': last_row.name,
            'close': last_row['Close'],
            'signal': last_row['SignalCategory'],
            'strength': last_row['SignalStrength'],
            'k_value': last_row['K'],
            'd_value': last_row['D'],
            'macd': last_row['MACD'],
            'macd_signal': last_row['MACD_Signal'],
            'rsi': last_row['RSI']
        }
        
        return signal_info
        
# Testing functionality
if __name__ == "__main__":
    # Test with some sample data
    from data_fetcher import ETFDataFetcher
    
    # Fetch data for testing
    fetcher = ETFDataFetcher("0050")
    data = fetcher.fetch_historical_data(period="6mo")
    
    if data is not None:
        # Create strategy
        strategy = ETFStrategy(data)
        
        # Calculate indicators
        df_with_indicators = strategy.calculate_all_indicators()
        
        # Generate signals
        df_with_signals = strategy.generate_signals(df_with_indicators)
        
        # Get latest signal
        latest_signal = strategy.get_latest_signal(df_with_signals)
        
        print("\nLatest signal:", latest_signal) 
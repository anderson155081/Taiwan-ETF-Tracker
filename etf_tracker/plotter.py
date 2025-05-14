"""
Plotter Module for ETF Technical Analysis
Generates charts and visualizations of technical indicators
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set plot style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 12

class ETFPlotter:
    """Class to generate technical analysis charts for ETFs"""
    
    def __init__(self, data, etf_code, output_dir='etf_tracker/reports'):
        """
        Initialize the plotter
        
        Args:
            data (pandas.DataFrame): DataFrame with price data and indicators
            etf_code (str): ETF code (e.g., "0050")
            output_dir (str): Directory to save output files
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Data must be a pandas DataFrame")
            
        if data.empty:
            raise ValueError("Empty DataFrame provided")
            
        # Check required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")
            
        self.data = data.copy()
        self.etf_code = etf_code
        self.output_dir = output_dir
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Initialized ETFPlotter for {etf_code} with {len(data)} data points")
        
    def plot_all(self, last_n_days=180, show_plot=False):
        """
        Generate a comprehensive chart with all indicators
        
        Args:
            last_n_days (int): Number of days to plot
            show_plot (bool): Whether to display the plot
            
        Returns:
            str: Path to saved image
        """
        # Limit data to last N days
        if len(self.data) > last_n_days:
            plot_data = self.data.iloc[-last_n_days:]
        else:
            plot_data = self.data
            
        # Create figure and grid
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(4, 1, height_ratios=[3, 1, 1, 1])
        
        # Price chart with MAs
        ax1 = plt.subplot(gs[0])
        self._plot_price_chart(ax1, plot_data)
        
        # Volume
        ax2 = plt.subplot(gs[1], sharex=ax1)
        self._plot_volume(ax2, plot_data)
        
        # KD
        ax3 = plt.subplot(gs[2], sharex=ax1)
        self._plot_kd(ax3, plot_data)
        
        # MACD
        ax4 = plt.subplot(gs[3], sharex=ax1)
        self._plot_macd(ax4, plot_data)
        
        # Format x-axis
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        # Add title
        latest_close = plot_data['Close'].iloc[-1]
        latest_date = plot_data.index[-1].strftime('%Y-%m-%d')
        change = plot_data['Close'].iloc[-1] - plot_data['Close'].iloc[-2]
        change_pct = (change / plot_data['Close'].iloc[-2]) * 100
        
        # Get signal if available
        signal_text = ""
        if 'SignalCategory' in plot_data.columns:
            signal = plot_data['SignalCategory'].iloc[-1]
            signal_text = f" | Signal: {signal}"
            
        title = f"{self.etf_code} Technical Analysis | {latest_date} | Close: {latest_close:.2f} ({change_pct:+.2f}%){signal_text}"
        fig.suptitle(title, fontsize=16)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.95)
        
        # Save figure
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{self.etf_code}_technical_{today}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=100)
        logger.info(f"Saved plot to {filepath}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
            
        return filepath
        
    def _plot_price_chart(self, ax, data):
        """Plot price chart with MAs"""
        # Plot candlestick chart
        width = 0.6
        width2 = width * 0.8
        
        up = data[data['Close'] >= data['Open']]
        down = data[data['Close'] < data['Open']]
        
        # Up candles - now RED
        ax.bar(up.index, up['Close']-up['Open'], width, bottom=up['Open'], color='#F23645')
        ax.bar(up.index, up['High']-up['Close'], width2, bottom=up['Close'], color='#F23645')
        ax.bar(up.index, up['Open']-up['Low'], width2, bottom=up['Low'], color='#F23645')
        
        # Down candles - now GREEN
        ax.bar(down.index, down['Open']-down['Close'], width, bottom=down['Close'], color='#089981')
        ax.bar(down.index, down['High']-down['Open'], width2, bottom=down['Open'], color='#089981')
        ax.bar(down.index, down['Close']-down['Low'], width2, bottom=down['Low'], color='#089981')
        
        # Add moving averages
        ma_columns = [col for col in data.columns if col.startswith('MA_')]
        for column in ma_columns:
            period = column.split('_')[1]
            ax.plot(data.index, data[column], label=f'{period}-day MA', linewidth=1.5)
            
        # Add buy/sell signals if available
        if 'SignalCategory' in data.columns:
            buys = data[data['SignalCategory'].isin(['Buy', 'Strong Buy'])]
            sells = data[data['SignalCategory'].isin(['Sell', 'Strong Sell'])]
            
            if not buys.empty:
                ax.scatter(buys.index, buys['Low'] * 0.99, marker='^', color='red', s=100, label='Buy Signal')
                
            if not sells.empty:
                ax.scatter(sells.index, sells['High'] * 1.01, marker='v', color='green', s=100, label='Sell Signal')
        
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
    def _plot_volume(self, ax, data):
        """Plot volume bars"""
        ax.bar(data.index, data['Volume'], width=0.8, 
               color=data.apply(lambda x: '#F23645' if x['Close'] >= x['Open'] else '#089981', axis=1))
        ax.set_ylabel('Volume')
        ax.grid(True, alpha=0.3)
        
    def _plot_kd(self, ax, data):
        """Plot KD indicator"""
        ax.plot(data.index, data['K'], label='K', color='blue', linewidth=1.5)
        ax.plot(data.index, data['D'], label='D', color='orange', linewidth=1.5)
        
        # Add overbought/oversold lines
        ax.axhline(y=80, color='red', linestyle='--', alpha=0.3)
        ax.axhline(y=20, color='green', linestyle='--', alpha=0.3)
        
        ax.set_ylabel('KD')
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
    def _plot_macd(self, ax, data):
        """Plot MACD indicator"""
        ax.plot(data.index, data['MACD'], label='MACD', color='blue', linewidth=1.5)
        ax.plot(data.index, data['MACD_Signal'], label='Signal', color='orange', linewidth=1.5)
        
        # Add histogram
        ax.bar(data.index, data['MACD_Hist'], width=0.8, color=data.apply(
            lambda x: '#F23645' if x['MACD_Hist'] >= 0 else '#089981', axis=1
        ))
        
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax.set_ylabel('MACD')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
    def plot_signal_summary(self, show_plot=False):
        """
        Generate a summary plot for the latest signal
        
        Args:
            show_plot (bool): Whether to display the plot
            
        Returns:
            str: Path to saved image
        """
        # Use the last 60 days of data for the summary
        data = self.data.iloc[-60:]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot close price
        ax.plot(data.index, data['Close'], label='Close Price', color='#1E88E5', linewidth=2)
        
        # Add MA lines
        if 'MA_20' in data.columns:
            ax.plot(data.index, data['MA_20'], label='20-day MA', color='#FFC107', linewidth=1.5)
        if 'MA_60' in data.columns:
            ax.plot(data.index, data['MA_60'], label='60-day MA', color='#D81B60', linewidth=1.5)
            
        # Add buy/sell signals
        if 'SignalCategory' in data.columns:
            buys = data[data['SignalCategory'].isin(['Buy', 'Strong Buy'])]
            sells = data[data['SignalCategory'].isin(['Sell', 'Strong Sell'])]
            
            if not buys.empty:
                ax.scatter(buys.index, buys['Close'], marker='^', color='red', s=150, label='Buy Signal')
                
            if not sells.empty:
                ax.scatter(sells.index, sells['Close'], marker='v', color='green', s=150, label='Sell Signal')
        
        # Format plot
        latest_close = data['Close'].iloc[-1]
        latest_date = data.index[-1].strftime('%Y-%m-%d')
        change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
        change_pct = (change / data['Close'].iloc[-2]) * 100
        
        # Get signal if available
        signal_text = ""
        if 'SignalCategory' in data.columns:
            signal = data['SignalCategory'].iloc[-1]
            signal_text = f"Signal: {signal}"
            
        title = f"{self.etf_code} | {latest_date} | Close: {latest_close:.2f} ({change_pct:+.2f}%)"
        ax.set_title(title, fontsize=14)
        
        # Add signal as text box
        if signal_text:
            signal_color = 'red' if 'Buy' in signal_text else 'green' if 'Sell' in signal_text else 'black'
            ax.text(0.02, 0.05, signal_text, transform=ax.transAxes, fontsize=14, 
                   bbox=dict(facecolor='white', alpha=0.8, edgecolor=signal_color, boxstyle='round,pad=0.5'),
                   color=signal_color)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.xticks(rotation=45)
        
        ax.set_ylabel('Price')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left')
        
        plt.tight_layout()
        
        # Save figure
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{self.etf_code}_summary_{today}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=100)
        logger.info(f"Saved summary plot to {filepath}")
        
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
            
        return filepath
        
# Testing functionality
if __name__ == "__main__":
    # Test with some sample data
    from data_fetcher import ETFDataFetcher
    from strategy import ETFStrategy
    
    # Fetch data for testing
    etf_code = "0050"
    fetcher = ETFDataFetcher(etf_code)
    data = fetcher.fetch_historical_data(period="1y")
    
    if data is not None:
        # Calculate indicators
        strategy = ETFStrategy(data)
        df_with_signals = strategy.generate_signals()
        
        # Create plotter and generate charts
        plotter = ETFPlotter(df_with_signals, etf_code)
        plotter.plot_all(show_plot=True)
        plotter.plot_signal_summary(show_plot=True) 
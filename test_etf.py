#!/usr/bin/env python
"""
Simple test script for ETF Tracker
Run this to fetch and analyze 0050 ETF data
"""
import os
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import ETF Tracker modules
from etf_tracker.data_fetcher import ETFDataFetcher
from etf_tracker.strategy import ETFStrategy
from etf_tracker.plotter import ETFPlotter

def main():
    """Test ETF Tracker functionality"""
    print("=== ETF Tracker Test ===")
    
    # Define ETF code to test
    etf_code = "0050"  # Taiwan 50 ETF
    
    print(f"Testing with ETF: {etf_code}")
    
    # 1. Fetch ETF data
    print("\nFetching data...")
    fetcher = ETFDataFetcher(etf_code)
    data = fetcher.fetch_historical_data(period="6mo")
    
    if data is None or data.empty:
        print("Error: Could not fetch data.")
        return
        
    print(f"Successfully fetched {len(data)} days of data.")
    print("\nLatest data:")
    print(data.tail(3))
    
    # 2. Calculate technical indicators and signals
    print("\nCalculating technical indicators...")
    strategy = ETFStrategy(data)
    df_with_signals = strategy.generate_signals()
    
    if df_with_signals is None:
        print("Error: Could not generate signals.")
        return
        
    # 3. Get the latest signal
    print("\nGenerating trading signals...")
    signal_info = strategy.get_latest_signal(df_with_signals)
    
    if signal_info:
        print("\nLatest Signal Info:")
        print(f"Date: {signal_info['date']}")
        print(f"Close Price: {signal_info['close']:.2f}")
        print(f"Signal: {signal_info['signal']}")
        print(f"KD Values: K={signal_info['k_value']:.1f}, D={signal_info['d_value']:.1f}")
        print(f"MACD: {signal_info['macd']:.3f}, Signal: {signal_info['macd_signal']:.3f}")
        print(f"RSI: {signal_info['rsi']:.1f}")
    
    # 4. Generate plots
    print("\nGenerating plots...")
    plotter = ETFPlotter(df_with_signals, etf_code)
    
    # Generate technical analysis plot
    tech_image_path = plotter.plot_all(show_plot=False)
    print(f"Technical analysis chart saved to: {tech_image_path}")
    
    # Generate summary plot
    summary_image_path = plotter.plot_signal_summary(show_plot=False)
    print(f"Summary chart saved to: {summary_image_path}")
    
    print("\nTest completed successfully!")
    print(f"Current signal for {etf_code}: {signal_info['signal']}")

if __name__ == "__main__":
    main() 
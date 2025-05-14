#!/usr/bin/env python
"""
Test script to determine which Yahoo Finance ticker format works for Taiwan ETFs
"""
import os
import sys
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Taiwan ETF code mappings to test
TICKERS_TO_TEST = {
    "0050": ["0050.TW", "0050.TWO", "0050.TWO.TW", "0050.T", "0050.TWSE", "0050.TWO"],
    "006208": ["006208.TW", "6208.TW", "006208.TWO", "6208.TWO", "6208.TWO.TW"],
    "00878": ["00878.TW", "0878.TW", "0878.TWO", "00878.TWO", "0878.TWO.TW"],
}

def test_ticker(ticker, period="1mo"):
    """Test if a ticker works with yfinance"""
    try:
        logger.info(f"Testing ticker: {ticker}")
        data = yf.download(ticker, period=period, progress=False)
        
        if data.empty:
            logger.error(f"✘ No data returned for {ticker}")
            return False, None
            
        # Successfully found data
        logger.info(f"✓ Successfully fetched {len(data)} records for {ticker}")
        return True, data
        
    except Exception as e:
        logger.error(f"✘ Error fetching data for {ticker}: {e}")
        return False, None
        
def main():
    """Test all ticker formats"""
    results = {}
    
    for etf_code, ticker_formats in TICKERS_TO_TEST.items():
        logger.info(f"\n==== Testing ETF code: {etf_code} ====")
        results[etf_code] = {"working_tickers": []}
        
        for ticker in ticker_formats:
            success, data = test_ticker(ticker)
            
            if success:
                results[etf_code]["working_tickers"].append(ticker)
                # Print a sample of the data
                if data is not None:
                    print(f"\nSample data for {ticker}:")
                    print(data.head(3))
                    
    # Print summary
    print("\n==== SUMMARY ====")
    for etf_code, result in results.items():
        working_tickers = result["working_tickers"]
        if working_tickers:
            print(f"{etf_code}: Working formats: {', '.join(working_tickers)}")
        else:
            print(f"{etf_code}: No working ticker formats found")
            
if __name__ == "__main__":
    main() 
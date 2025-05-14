"""
Main Module for ETF Tracker & Analyzer
Orchestrates the entire ETF analysis pipeline and scheduling
"""
import os
import logging
import argparse
from datetime import datetime
import schedule
import time
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import local modules
from etf_tracker.data_fetcher import ETFDataFetcher, get_supported_etfs
from etf_tracker.strategy import ETFStrategy
from etf_tracker.plotter import ETFPlotter

# Try to import line_bot module (optional)
try:
    from etf_tracker.line_bot import broadcast_etf_report, LINE_AVAILABLE
    logger.info(f"LINE bot module loaded. LINE notifications {'enabled' if LINE_AVAILABLE else 'disabled (missing credentials)'}")
except ImportError:
    LINE_AVAILABLE = False
    logger.warning("LINE bot module not available. LINE notifications will be disabled.")
    # Create a dummy function that does nothing
    def broadcast_etf_report(etf_code, user_ids=None):
        logger.warning(f"LINE bot not available, notification for {etf_code} skipped")
        return

# Create reports directory if it doesn't exist
REPORTS_DIR = Path('etf_tracker/reports')
REPORTS_DIR.mkdir(exist_ok=True, parents=True)

# Configuration
DEFAULT_ETF_CODES = ['0050', '006208']

def process_etf(etf_code, save_data=True, generate_plots=True, period="1y"):
    """
    Process a single ETF - fetch data, calculate signals, generate plots
    
    Args:
        etf_code (str): ETF code to process
        save_data (bool): Whether to save data to CSV
        generate_plots (bool): Whether to generate plots
        period (str): Time period for data fetching
        
    Returns:
        tuple: (DataFrame with signals, signal info dict, plot filepath)
    """
    logger.info(f"Processing ETF {etf_code}")
    
    try:
        # 1. Fetch data
        fetcher = ETFDataFetcher(etf_code)
        data = fetcher.fetch_historical_data(period=period)
        
        if data is None or data.empty:
            logger.error(f"Failed to fetch data for {etf_code}")
            return None, None, None
        
        # 2. Save data if requested
        if save_data:
            today = datetime.now().strftime('%Y-%m-%d')
            csv_path = REPORTS_DIR / f"{etf_code}_{today}.csv"
            data.to_csv(csv_path)
            logger.info(f"Saved data to {csv_path}")
        
        # 3. Calculate signals
        strategy = ETFStrategy(data)
        df_with_signals = strategy.generate_signals()
        
        if df_with_signals is None:
            logger.error(f"Failed to generate signals for {etf_code}")
            return data, None, None
        
        # 4. Get latest signal info
        signal_info = strategy.get_latest_signal(df_with_signals)
        
        # 5. Generate plots if requested
        image_path = None
        if generate_plots:
            plotter = ETFPlotter(df_with_signals, etf_code, output_dir=str(REPORTS_DIR))
            # Generate detailed technical analysis plot
            tech_image_path = plotter.plot_all()
            # Generate summary plot
            summary_image_path = plotter.plot_signal_summary()
            image_path = summary_image_path
        
        # 6. Save signal info to JSON
        if signal_info:
            # Convert datetime to string for JSON serialization
            if hasattr(signal_info['date'], 'strftime'):
                signal_info['date'] = signal_info['date'].strftime('%Y-%m-%d')
                
            signal_file = REPORTS_DIR / f"{etf_code}_signal_{datetime.now().strftime('%Y-%m-%d')}.json"
            with open(signal_file, 'w') as f:
                json.dump(signal_info, f, indent=2)
            logger.info(f"Saved signal info to {signal_file}")
        
        return df_with_signals, signal_info, image_path
    
    except Exception as e:
        logger.error(f"Error processing ETF {etf_code}: {e}")
        return None, None, None

def process_all_etfs(etf_codes=None, notify=False, user_ids=None):
    """
    Process multiple ETFs and optionally send notifications
    
    Args:
        etf_codes (list): List of ETF codes to process. If None, uses all supported ETFs.
        notify (bool): Whether to send LINE notifications
        user_ids (list): User IDs to notify. Required if notify=True.
        
    Returns:
        dict: Results for each ETF
    """
    # Use default ETFs if none specified
    if etf_codes is None:
        etf_codes = DEFAULT_ETF_CODES
    
    results = {}
    
    for etf_code in etf_codes:
        df, signal_info, image_path = process_etf(etf_code)
        results[etf_code] = {
            'data_processed': df is not None,
            'signal': signal_info['signal'] if signal_info else None,
            'image_path': image_path
        }
        
        # Send notification if requested and LINE bot is available
        if notify and LINE_AVAILABLE and user_ids and signal_info:
            try:
                logger.info(f"Broadcasting {etf_code} report to {len(user_ids)} users")
                broadcast_etf_report(etf_code, user_ids)
                results[etf_code]['notification_sent'] = True
            except Exception as e:
                logger.error(f"Error sending notification for {etf_code}: {e}")
                results[etf_code]['notification_sent'] = False
        elif notify:
            logger.warning(f"Notifications requested but LINE is not available or user_ids not provided")
    
    return results

def scheduled_job():
    """Daily scheduled job to process ETFs"""
    logger.info("Running scheduled ETF analysis")
    
    # Get user IDs from environment variable or configuration
    user_ids_str = os.getenv('LINE_USER_IDS')
    user_ids = user_ids_str.split(',') if user_ids_str else None
    
    # Process ETFs and notify users if LINE is available
    results = process_all_etfs(notify=LINE_AVAILABLE, user_ids=user_ids)
    
    # Log results
    success_count = sum(1 for etf, result in results.items() if result['data_processed'])
    logger.info(f"Scheduled job completed. Processed {success_count}/{len(results)} ETFs successfully.")

def run_scheduled_jobs():
    """Configure and run scheduled jobs"""
    # Schedule daily job at market close (2:30 PM Taiwan time)
    schedule.every().monday.at("14:30").do(scheduled_job)
    schedule.every().tuesday.at("14:30").do(scheduled_job)
    schedule.every().wednesday.at("14:30").do(scheduled_job)
    schedule.every().thursday.at("14:30").do(scheduled_job)
    schedule.every().friday.at("14:30").do(scheduled_job)
    
    logger.info("Scheduled jobs configured. Running scheduler...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='ETF Tracker & Analyzer')
    
    parser.add_argument('--etf', type=str, help='ETF code to analyze')
    parser.add_argument('--all', action='store_true', help='Process all supported ETFs')
    parser.add_argument('--schedule', action='store_true', help='Run as a scheduled service')
    parser.add_argument('--notify', action='store_true', help='Send LINE notifications')
    parser.add_argument('--period', type=str, default="1y", help='Data period (e.g., 1y, 6mo)')
    
    args = parser.parse_args()
    
    # Get user IDs for notification
    user_ids_str = os.getenv('LINE_USER_IDS')
    user_ids = user_ids_str.split(',') if user_ids_str else None
    
    # Check if notifications are requested but LINE is not available
    if args.notify and not LINE_AVAILABLE:
        logger.warning("Notifications requested but LINE bot is not available or missing credentials")
    
    if args.schedule:
        # Run in scheduled mode
        logger.info("Starting ETF Tracker in scheduled mode")
        run_scheduled_jobs()
    elif args.all:
        # Process all ETFs
        logger.info("Processing all ETFs")
        results = process_all_etfs(notify=args.notify, user_ids=user_ids)
        logger.info(f"Processed {len(results)} ETFs")
    elif args.etf:
        # Process a single ETF
        etf_code = args.etf
        logger.info(f"Processing ETF {etf_code}")
        df, signal_info, image_path = process_etf(etf_code, period=args.period)
        
        if signal_info:
            logger.info(f"Signal for {etf_code}: {signal_info['signal']}")
            
        # Send notification if requested
        if args.notify and LINE_AVAILABLE and signal_info and user_ids:
            broadcast_etf_report(etf_code, user_ids)
    else:
        # No arguments, show help
        parser.print_help()

if __name__ == "__main__":
    main() 
"""
Web Server Module for ETF Tracker
Serves ETF analysis reports as interactive web pages
"""
import os
# Set matplotlib to use a non-interactive backend before any other imports
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend which doesn't require a GUI

from flask import Flask, render_template, send_from_directory, abort, request
import logging
from datetime import datetime
import json
from pathlib import Path
import argparse

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
from etf_tracker.main import process_etf, DEFAULT_ETF_CODES

# Initialize Flask app with proper template folder
app = Flask(__name__, 
           static_folder='etf_tracker/reports',
           template_folder='etf_tracker/templates')

# Create reports directory if it doesn't exist
REPORTS_DIR = Path('etf_tracker/reports')
REPORTS_DIR.mkdir(exist_ok=True, parents=True)

@app.route('/')
def index():
    """Landing page showing links to all supported ETFs"""
    supported_etfs = get_supported_etfs()
    return render_template('index.html', etfs=supported_etfs, now=datetime.now())

@app.route('/etf/<etf_code>')
def etf_report(etf_code):
    """Generate and display ETF report"""
    try:
        # Check if the ETF code is supported
        supported_etfs = get_supported_etfs()
        if etf_code not in supported_etfs:
            abort(404, description=f"ETF code {etf_code} not supported")
        
        # Process ETF data
        data, signal_info, image_path = process_etf(etf_code, save_data=True, generate_plots=True)
        
        if data is None or signal_info is None:
            abort(500, description=f"Failed to process ETF {etf_code}")
        
        # Get paths to image files
        today = datetime.now().strftime('%Y-%m-%d')
        summary_chart_path = f"/static/{etf_code}_summary_{today}.png"
        technical_chart_path = f"/static/{etf_code}_technical_{today}.png"
        
        # Add change_percent if missing
        if 'change_percent' not in signal_info:
            # Try to calculate from data if available
            if data is not None and len(data) > 1:
                try:
                    current_close = data['Close'].iloc[-1]
                    prev_close = data['Close'].iloc[-2]
                    change_percent = ((current_close / prev_close) - 1) * 100
                    signal_info['change_percent'] = change_percent
                except Exception as e:
                    logger.warning(f"Could not calculate change_percent: {e}")
                    signal_info['change_percent'] = 0.0
            else:
                # Default value if no data
                signal_info['change_percent'] = 0.0
        
        # Ensure all values are the correct type
        try:
            # Convert values to appropriate types to avoid comparison issues
            change_percent = float(signal_info['change_percent'])
            close_price = float(signal_info['close'])
            volume = int(signal_info.get('volume', 0))
            k_value = float(signal_info['k_value'])
            d_value = float(signal_info['d_value'])
            macd = float(signal_info['macd'])
            macd_signal = float(signal_info['macd_signal'])
            rsi = float(signal_info['rsi'])
        except (ValueError, TypeError) as e:
            logger.error(f"Error converting signal values: {e}")
            # Provide default values for any conversion errors
            if 'change_percent' not in locals(): change_percent = 0.0
            if 'close_price' not in locals(): close_price = 0.0
            if 'volume' not in locals(): volume = 0
            if 'k_value' not in locals(): k_value = 0.0
            if 'd_value' not in locals(): d_value = 0.0
            if 'macd' not in locals(): macd = 0.0
            if 'macd_signal' not in locals(): macd_signal = 0.0
            if 'rsi' not in locals(): rsi = 0.0
        
        # Prepare template context
        context = {
            'etf_code': etf_code,
            'report_date': today,
            'price': f"{close_price:.2f}",
            'change_percent': change_percent,  # Numeric for comparison
            'change_percent_fmt': f"{change_percent:.2f}",  # Formatted for display
            'volume': f"{volume:,}",
            'signal': signal_info['signal'],
            'k_value': f"{k_value:.2f}",
            'd_value': f"{d_value:.2f}",
            'macd': f"{macd:.3f}",
            'macd_signal': f"{macd_signal:.3f}",
            'rsi': f"{rsi:.2f}",
            'summary_chart_path': summary_chart_path,
            'technical_chart_path': technical_chart_path,
            'current_year': datetime.now().year
        }
        
        # Render template
        return render_template('report_template.html', **context)
    
    except Exception as e:
        logger.error(f"Error generating report for {etf_code}: {e}")
        abort(500, description=f"Internal server error: {str(e)}")

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files from the reports directory"""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/etfs')
def api_etfs():
    """API endpoint to get list of supported ETFs"""
    return {'etfs': get_supported_etfs()}

@app.route('/api/etf/<etf_code>')
def api_etf_data(etf_code):
    """API endpoint to get ETF data"""
    try:
        # Check if signal data exists for today
        today = datetime.now().strftime('%Y-%m-%d')
        signal_file = REPORTS_DIR / f"{etf_code}_signal_{today}.json"
        
        # If we don't have today's data, process it
        if not signal_file.exists():
            data, signal_info, _ = process_etf(etf_code)
        else:
            # Load existing signal data
            with open(signal_file, 'r') as f:
                signal_info = json.load(f)
                
            # Re-process data to get DataFrame if needed
            if 'change_percent' not in signal_info:
                data, _, _ = process_etf(etf_code, save_data=False, generate_plots=False)
                
                # Calculate change_percent
                if data is not None and len(data) > 1:
                    try:
                        current_close = data['Close'].iloc[-1]
                        prev_close = data['Close'].iloc[-2]
                        change_percent = ((current_close / prev_close) - 1) * 100
                        signal_info['change_percent'] = change_percent
                    except Exception as e:
                        logger.warning(f"Could not calculate change_percent: {e}")
                        signal_info['change_percent'] = 0.0
                else:
                    # Default value if no data
                    signal_info['change_percent'] = 0.0
        
        # Ensure volume is present
        if 'volume' not in signal_info:
            signal_info['volume'] = 0
            
        # Ensure all numeric values are actually numeric (for JSON serialization)
        numeric_fields = ['close', 'change_percent', 'k_value', 'd_value', 'macd', 'macd_signal', 'rsi', 'volume']
        for field in numeric_fields:
            if field in signal_info:
                try:
                    # Convert to the appropriate numeric type
                    signal_info[field] = float(signal_info[field])
                    # For volume specifically, convert to int
                    if field == 'volume':
                        signal_info[field] = int(signal_info[field])
                except (ValueError, TypeError):
                    # Use appropriate defaults for each field
                    if field == 'volume':
                        signal_info[field] = 0
                    else:
                        signal_info[field] = 0.0
                
        return signal_info
    
    except Exception as e:
        logger.error(f"Error fetching API data for {etf_code}: {e}")
        return {'error': str(e)}, 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error=error), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error=error), 500

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ETF Tracker Web Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Use environment variable for port if set, otherwise use command line arg
    port = int(os.environ.get('PORT', args.port))
    
    # In production, you'll want to use a proper WSGI server like gunicorn
    debug = args.debug or os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting ETF Tracker Web Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 
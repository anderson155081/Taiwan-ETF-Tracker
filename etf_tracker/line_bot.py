"""
LINE Bot Module for ETF Tracker
Provides webhook handling and message sending capabilities using LINE Messaging API
"""
import os
import json
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
    TemplateSendMessage, ButtonsTemplate, MessageAction, URIAction
)
from datetime import datetime
import tempfile
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# LINE API credentials
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

# Check if LINE credentials are available
LINE_AVAILABLE = bool(LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET)

if LINE_AVAILABLE:
    # Initialize LINE SDK clients
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    logger.info("LINE Messaging API initialized")
else:
    line_bot_api = None
    handler = None
    logger.warning("LINE credentials not found. LINE notifications will be disabled.")

# Import other modules
try:
    from etf_tracker.data_fetcher import ETFDataFetcher, get_supported_etfs
    from etf_tracker.strategy import ETFStrategy
    from etf_tracker.plotter import ETFPlotter
    MODULES_LOADED = True
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    MODULES_LOADED = False

@app.route("/callback", methods=['POST'])
def callback():
    """
    Handle LINE webhook callback
    """
    if not LINE_AVAILABLE:
        logger.error("LINE API not configured")
        abort(500)
        
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # Get request body as text
    body = request.get_data(as_text=True)
    logger.info(f"Request body: {body}")
    
    # Handle webhook verification
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Check your channel secret.")
        abort(400)
        
    return 'OK'

# Only define this function if LINE is available
if LINE_AVAILABLE:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_text_message(event):
        """
        Handle incoming text messages
        """
        text = event.message.text.strip().lower()
        user_id = event.source.user_id
        
        logger.info(f"Received message from {user_id}: {text}")
        
        # Check if modules are loaded
        if not MODULES_LOADED:
            send_text_message(user_id, "System is currently unavailable. Please try again later.")
            return
        
        # Handle ETF requests
        if text.startswith('etf'):
            parts = text.split()
            if len(parts) >= 2:
                etf_code = parts[1]
                handle_etf_request(user_id, etf_code)
            else:
                send_help_message(user_id)
        
        # Handle help request
        elif text == 'help':
            send_help_message(user_id)
        
        # Handle list request
        elif text == 'list':
            supported_etfs = get_supported_etfs()
            etf_list = "\n".join([f"• {etf}" for etf in supported_etfs])
            send_text_message(user_id, f"Supported ETFs:\n{etf_list}")
        
        # Handle unknown commands
        else:
            send_text_message(user_id, 
                "Welcome to ETF Tracker! Type 'help' to see available commands or 'etf 0050' to check 0050 ETF."
            )
else:
    # Define a dummy handler for when LINE is not available
    def handle_text_message(event):
        logger.warning("LINE is not available, message handling skipped")
        return

def handle_etf_request(user_id, etf_code):
    """
    Process an ETF request and send the analysis
    
    Args:
        user_id (str): LINE user ID
        etf_code (str): ETF code (e.g., "0050")
    """
    if not LINE_AVAILABLE:
        logger.warning(f"LINE API not configured, ETF request for {etf_code} skipped")
        return
        
    try:
        # Fetch and prepare ETF data
        fetcher = ETFDataFetcher(etf_code)
        data = fetcher.fetch_historical_data()
        
        if data is None or data.empty:
            send_text_message(user_id, f"Sorry, couldn't fetch data for ETF {etf_code}.")
            return
            
        # Calculate technical indicators and generate signals
        strategy = ETFStrategy(data)
        df_with_signals = strategy.generate_signals()
        
        if df_with_signals is None:
            send_text_message(user_id, f"Sorry, couldn't analyze ETF {etf_code}.")
            return
            
        # Get the latest signal
        signal_info = strategy.get_latest_signal(df_with_signals)
        
        # Generate summary plot
        plotter = ETFPlotter(df_with_signals, etf_code)
        image_path = plotter.plot_signal_summary()
        
        # Send the results
        send_etf_analysis(user_id, etf_code, signal_info, image_path)
        
    except ValueError as e:
        send_text_message(user_id, f"Error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing ETF request for {etf_code}: {e}")
        send_text_message(user_id, "Sorry, an error occurred while processing your request.")

def send_etf_analysis(user_id, etf_code, signal_info, image_path=None):
    """
    Send ETF analysis to the user
    
    Args:
        user_id (str): LINE user ID
        etf_code (str): ETF code
        signal_info (dict): Signal information
        image_path (str): Path to the analysis image
    """
    if not LINE_AVAILABLE:
        logger.warning("LINE API not configured, skipping message sending")
        return
        
    # Format date
    date_str = signal_info['date'].strftime('%Y-%m-%d') if hasattr(signal_info['date'], 'strftime') else signal_info['date']
    
    # Prepare message text
    message = f"📊 {etf_code} Analysis ({date_str})\n"
    message += f"Close: ${signal_info['close']:.2f}\n"
    message += f"Signal: {signal_info['signal']}\n\n"
    
    # Add indicator values
    message += "📈 Indicators:\n"
    message += f"• KD: K={signal_info['k_value']:.1f}, D={signal_info['d_value']:.1f}\n"
    message += f"• MACD: {signal_info['macd']:.3f}\n"
    message += f"• RSI: {signal_info['rsi']:.1f}\n"
    
    # Send text message
    send_text_message(user_id, message)
    
    # Send image if available
    if image_path and os.path.exists(image_path):
        # Get public URL for the image (requires hosting)
        # For simplicity in this example, we assume the image is publicly accessible
        # In a real implementation, you would upload this to a server
        image_url = get_public_url_for_image(image_path)
        
        if image_url:
            send_image_message(user_id, image_url)

def get_public_url_for_image(image_path):
    """
    This function would normally upload the image to a server and return a public URL
    For this example, we'll return a placeholder URL
    
    In a real implementation, you would:
    1. Upload the image to a storage service (AWS S3, Google Cloud Storage, etc.)
    2. Return the public URL
    
    Args:
        image_path (str): Local path to the image
        
    Returns:
        str: Public URL for the image
    """
    # Note: This is a placeholder. In a real implementation,
    # you would upload the image to a hosting service and return the URL
    return None  # TODO: Implement image hosting

def send_text_message(user_id, text):
    """
    Send a text message to a user
    
    Args:
        user_id (str): LINE user ID
        text (str): Message text
    """
    if not LINE_AVAILABLE:
        logger.warning(f"LINE API not configured, would have sent: {text}")
        return
        
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=text))
        logger.info(f"Sent text message to {user_id}")
    except Exception as e:
        logger.error(f"Error sending message to {user_id}: {e}")

def send_image_message(user_id, image_url):
    """
    Send an image message to a user
    
    Args:
        user_id (str): LINE user ID
        image_url (str): URL of the image
    """
    if not LINE_AVAILABLE:
        logger.warning(f"LINE API not configured, would have sent image: {image_url}")
        return
        
    try:
        line_bot_api.push_message(
            user_id, 
            ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        )
        logger.info(f"Sent image message to {user_id}")
    except Exception as e:
        logger.error(f"Error sending image to {user_id}: {e}")

def send_help_message(user_id):
    """
    Send a help message to a user
    
    Args:
        user_id (str): LINE user ID
    """
    help_text = """
🤖 ETF Tracker Bot - Commands:

• etf [code] - Get analysis for an ETF
  Example: etf 0050

• list - Show supported ETFs

• help - Show this help message
"""
    send_text_message(user_id, help_text)

def broadcast_etf_report(etf_code, user_ids=None):
    """
    Broadcast ETF analysis report to multiple users
    
    Args:
        etf_code (str): ETF code to analyze
        user_ids (list): List of LINE user IDs to send to. If None, uses registered users.
    """
    if not LINE_AVAILABLE:
        logger.warning("LINE API not configured, broadcast skipped")
        return
        
    if not user_ids:
        # In a real implementation, you would retrieve registered users from a database
        logger.warning("No user IDs provided for broadcast")
        return
        
    try:
        # Fetch and analyze ETF data
        fetcher = ETFDataFetcher(etf_code)
        data = fetcher.fetch_historical_data()
        
        if data is None or data.empty:
            logger.error(f"Could not fetch data for ETF {etf_code}")
            return
            
        # Calculate indicators and generate signals
        strategy = ETFStrategy(data)
        df_with_signals = strategy.generate_signals()
        
        if df_with_signals is None:
            logger.error(f"Could not analyze ETF {etf_code}")
            return
            
        # Get latest signal
        signal_info = strategy.get_latest_signal(df_with_signals)
        
        # Generate plot
        plotter = ETFPlotter(df_with_signals, etf_code)
        image_path = plotter.plot_signal_summary()
        
        # Send to each user
        for user_id in user_ids:
            send_etf_analysis(user_id, etf_code, signal_info, image_path)
            
        logger.info(f"Broadcast ETF {etf_code} analysis to {len(user_ids)} users")
        
    except Exception as e:
        logger.error(f"Error broadcasting ETF report: {e}")

if __name__ == "__main__":
    # For local development
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
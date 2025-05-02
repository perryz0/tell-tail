"""
Flask web server for TellTail.
Provides a web API for managing Tailscale networks.
"""

import os
from flask import Flask
from dotenv import load_dotenv
from services.api.TailscaleAPI import TailscaleAPI
from services.logging import logger
from web.api import api_bp

# Load environment variables
load_dotenv()

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
    app.config['JSON_SORT_KEYS'] = False  # Preserve JSON order
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Setup Tailscale API connection
    tailscale_token = os.getenv('TAILSCALE_API_TOKEN')
    tailnet_name = os.getenv('TAILNET_NAME')
    
    if not tailscale_token or not tailnet_name:
        logger.error("Missing required environment variables for Tailscale API")
    
    ts_api = TailscaleAPI(api_token=tailscale_token)
    
    # Store in app config for use in routes
    app.config['ts_api'] = ts_api
    app.config['tailnet'] = tailnet_name
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Root route for health check
    @app.route('/')
    def root():
        return {
            "status": "ok",
            "name": "TellTail API",
            "version": "1.0.0"
        }
    
    return app


def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    Run the Flask server.
    
    Args:
        host: Hostname to listen on
        port: Port to listen on
        debug: Whether to run in debug mode
    """
    app = create_app()
    logger.info(f"Starting TellTail API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    # Get configuration from environment variables
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'false').lower() == 'true'
    
    # Run the server
    run_server(host, port, debug) 
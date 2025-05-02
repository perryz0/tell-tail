"""
Flask web server for TellTail.
Provides a web API for managing Tailscale networks.
"""

import os
from flask import Flask, Blueprint, redirect, url_for, render_template, send_from_directory, session
from dotenv import load_dotenv
from services.api.TailscaleAPI import TailscaleAPI
from services.logging import logger
from web.api import api_bp
from settings.oauth import create_oauth_bp

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
    
    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
    
    # Setup Tailscale API connection
    tailscale_token = os.getenv('TAILSCALE_API_TOKEN')
    tailnet_name = os.getenv('TAILNET_NAME')
    
    if not tailscale_token or not tailnet_name:
        logger.error("Missing required environment variables for Tailscale API")
    
    ts_api = TailscaleAPI(api_token=tailscale_token)
    
    # Store in app config for use in routes
    app.config['ts_api'] = ts_api
    app.config['tailnet'] = tailnet_name
    
    # Register API blueprint
    app.register_blueprint(api_bp)
    
    # Create and register OAuth blueprint
    auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
    auth_bp = create_oauth_bp(auth_bp)
    app.register_blueprint(auth_bp)
    
    # Root route for dashboard with auth check
    @app.route('/')
    def root():
        # Check if user is logged in
        if session.get('user'):
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login_page'))
    
    # Login page route
    @app.route('/login')
    def login_page():
        # If already logged in, redirect to dashboard
        if session.get('user'):
            return redirect(url_for('dashboard'))
        return render_template('login.html')
    
    # Dashboard route with user info from session
    @app.route('/dashboard')
    def dashboard():
        user = session.get('user')
        # If not logged in, redirect to login
        if not user:
            return redirect(url_for('login_page'))
        return render_template('dashboard.html', user=user)
    
    # Redirect from /login to the OAuth login page
    @app.route('/auth/login')
    def login_redirect():
        return redirect(url_for('auth.login', next='/dashboard'))
    
    # Custom logout route that redirects to login page
    @app.route('/logout')
    def logout():
        # Clear the session
        session.clear()
        return redirect(url_for('login_page'))
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {
            "status": "ok",
            "name": "TellTail API",
            "version": "1.0.0"
        }
    
    # Handle favicon
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
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
#!/usr/bin/env python3
"""
Command-line script to start the TellTail API server.
Run with: python run_api.py
"""

import os
import argparse
from web.server import run_server
from dotenv import load_dotenv
from services.logging import logger

# Load environment variables
load_dotenv()

def main():
    """Parse command-line arguments and start the API server."""
    parser = argparse.ArgumentParser(description="Start the TellTail API server")
    parser.add_argument(
        "--host", 
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=int(os.getenv("API_PORT", "5000")),
        help="Port to bind the server to (default: 5000)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        default=os.getenv("API_DEBUG", "").lower() in ("true", "1", "yes"),
        help="Run the server in debug mode"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting TellTail API server")
    run_server(args.host, args.port, args.debug)


if __name__ == "__main__":
    main() 
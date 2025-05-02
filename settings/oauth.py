import os
import functools
from flask import Flask, redirect, request, url_for, session, jsonify
import requests
from dotenv import load_dotenv
from services.logging import logger

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
OAUTH_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
USER_URL = "https://discord.com/api/users/@me"

# List of Discord user IDs that are allowed to access the API
# If empty, all authenticated users are allowed
ALLOWED_DISCORD_IDS = [uid.strip() for uid in os.getenv("ALLOWED_DISCORD_IDS", "").split(",") if uid.strip()]

def login_required(f):
    """
    Decorator to require login for API endpoints.
    If the user is not authenticated, returns a 401 Unauthorized response.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return jsonify({
                "success": False,
                "message": "Authentication required",
            }), 401
            
        # If we have restricted access to specific users and the current user is not in the list
        if ALLOWED_DISCORD_IDS and str(session["user"]["id"]) not in ALLOWED_DISCORD_IDS:
            logger.warning(f"Unauthorized access attempt by {session['user']['username']} (ID: {session['user']['id']})")
            return jsonify({
                "success": False,
                "message": "You are not authorized to access this API",
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

def create_oauth_bp(bp):
    """
    Register OAuth routes on a Flask blueprint.
    """
    @bp.route("/login")
    def login():
        # Store the original URL to redirect back after login
        if 'next' in request.args:
            session['next'] = request.args.get('next')
            
        discord_auth_url = (
            f"{OAUTH_URL}?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}"
            f"&response_type=code&scope=identify"
        )
        return redirect(discord_auth_url)

    @bp.route("/callback")
    def callback():
        code = request.args.get("code")
        
        if not code:
            return jsonify({
                "success": False,
                "message": "Authorization code not provided",
            }), 400
            
        data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            # Exchange code for token
            response = requests.post(TOKEN_URL, data=data, headers=headers)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["access_token"]
            
            # Store token in session
            session["token"] = access_token

            # Fetch user info
            user_response = requests.get(
                USER_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_response.raise_for_status()
            user_info = user_response.json()
            
            # Check if user is authorized (if restriction list is set)
            if ALLOWED_DISCORD_IDS and str(user_info["id"]) not in ALLOWED_DISCORD_IDS:
                logger.warning(f"Login attempt by unauthorized user: {user_info['username']} (ID: {user_info['id']})")
                session.clear()
                return jsonify({
                    "success": False,
                    "message": "You are not authorized to access this API",
                }), 403

            # Store user info in session
            session["user"] = {
                "id": user_info["id"],
                "username": user_info["username"],
                "discriminator": user_info.get("discriminator", "0"),
                "avatar": user_info.get("avatar")
            }
            
            logger.info(f"User authenticated: {user_info['username']} (ID: {user_info['id']})")
            
            # Redirect to the original URL if it was stored
            next_url = session.pop('next', '/')
            return redirect(next_url)
            
        except requests.RequestException as e:
            logger.error(f"OAuth error: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Authentication failed",
            }), 500

    @bp.route("/logout")
    def logout():
        # Clear the session
        session.clear()
        return jsonify({
            "success": True,
            "message": "Successfully logged out",
        })
        
    @bp.route("/me")
    @login_required
    def me():
        # Return the current user info
        return jsonify({
            "success": True,
            "data": session.get("user")
        })
        
    return bp

@app.route("/")
def home():
    return '<a href="/login">Login with Discord</a>'

if __name__ == "__main__":
    app.run(debug=True)

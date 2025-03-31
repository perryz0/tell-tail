import os
from flask import Flask, redirect, request, url_for, session
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
OAUTH_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
USER_URL = "https://discord.com/api/users/@me"

@app.route("/")
def home():
    return '<a href="/login">Login with Discord</a>'

@app.route("/login")
def login():
    discord_auth_url = (
        f"{OAUTH_URL}?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code&scope=identify"
    )
    return redirect(discord_auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
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

    response = requests.post(TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    token = response.json()["access_token"]
    session["token"] = token

    # Fetch user info
    user_info = requests.get(
        USER_URL,
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    session["username"] = user_info["username"]
    return f"Logged in as {user_info['username']}"

if __name__ == "__main__":
    app.run(debug=True)

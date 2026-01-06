import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import uvicorn

from .keys import generate_rsa_keys, get_private_key_pem, get_public_key_pem


class AuthRequest(BaseModel):
    """Backwards compatible auth request format."""
    code: str
    redirectUri: str

load_dotenv()

app = FastAPI(title="Authentication Service")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8001/auth/callback")
PORT = int(os.getenv("PORT", 8001))

generate_rsa_keys()

def _exchange_discord_code(code: str, redirect_uri: str):
    """Helper: Exchange Discord auth code for user data."""
    try:
        token_response = requests.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri
            }
        )
        token_response.raise_for_status()
        token_data = token_response.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token exchange failed: {str(e)}")
    if "access_token" not in token_data:
        raise HTTPException(status_code=401, detail="No access token in response")
    try:
        user_response = requests.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_response.raise_for_status()
        user_data = user_response.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"User fetch failed: {str(e)}")
    
    if "id" not in user_data:
        raise HTTPException(status_code=401, detail="No user id in response")
    
    return user_data

def _create_jwt(user_data: dict):
    """Helper: Create JWT token from user data."""
    private_key = get_private_key_pem()
    
    # Payload includes both new fields and backwards-compatible discordId
    payload = {
        "discordId": user_data["id"],  # Backwards compatible
        "userId": user_data["id"],  # New format
        "username": user_data.get("username"),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=30)  # 30 days like original
    }
    
    return jwt.encode(payload, private_key, algorithm="RS256")


@app.get("/auth/public-key")
def get_public_key():
    """Returns the public key for JWT verification."""
    return JSONResponse({
        "public_key": get_public_key_pem()
    })


@app.get("/auth/login")
def discord_login():
    """Redirects user to Discord OAuth authorization."""
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize?"
        f"client_id={DISCORD_CLIENT_ID}&"
        f"redirect_uri={DISCORD_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=identify"
    )
    return JSONResponse({
        "auth_url": discord_auth_url
    })


@app.post("/auth")
async def discord_auth(request: AuthRequest):
    """Backwards compatible auth endpoint. Exchanges Discord code for JWT token."""
    try:
        user_data = _exchange_discord_code(request.code, request.redirectUri)
        token = _create_jwt(user_data)
        
        return JSONResponse({
            "token": token,
            "user": {
                "id": user_data["id"],
                "username": user_data.get("username")
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/auth/callback")
def discord_callback(code: str = Query(...), redirect_uri: str = Query(None)):
    """Handles Discord OAuth callback with code query parameter."""
    try:
        if not redirect_uri:
            redirect_uri = DISCORD_REDIRECT_URI
        
        user_data = _exchange_discord_code(code, redirect_uri)
        token = _create_jwt(user_data)
        
        return JSONResponse({
            "token": token,
            "user": {
                "id": user_data["id"],
                "username": user_data.get("username")
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)

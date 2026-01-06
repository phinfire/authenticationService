#!/usr/bin/env python
"""Automated full auth flow test with mocked Discord API."""
import os
import sys
import time
import jwt
from unittest.mock import patch, MagicMock
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

os.environ["DISCORD_CLIENT_ID"] = "test_client_id"
os.environ["DISCORD_CLIENT_SECRET"] = "test_client_secret"
os.environ["DISCORD_REDIRECT_URI"] = "http://localhost:8001/auth/callback"

from fastapi.testclient import TestClient
from src.main import app
from src.keys import get_public_key_pem

client: TestClient = TestClient(app)

def test_full_auth_flow() -> None:
    print("\n" + "="*60)
    print("FULL AUTH FLOW TEST")
    print("="*60)
    
    print("\n[1] Getting Discord OAuth URL...")
    response = client.get("/auth/login")
    assert response.status_code == 200, f"Failed: {response.text}"
    auth_url: str = response.json()["auth_url"]
    print(f"✓ Auth URL: {auth_url[:80]}...")
    assert "discord.com" in auth_url
    assert "scope=identify" in auth_url
    
    print("\n[2] Simulating Discord OAuth callback...")
    mock_user: Dict[str, Any] = {
        "id": "123456789",
        "username": "testuser"
    }
    
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "fake_token"}
        mock_post.return_value = mock_token_response
        
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = mock_user
        mock_get.return_value = mock_user_response
        
        response = client.post("/auth", json={
            "code": "fake_discord_code",
            "redirectUri": "http://localhost:8001/auth/callback"
        })
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data: Dict[str, Any] = response.json()
        print(f"✓ POST /auth endpoint works")
        print(f"✓ User: {data['user']['username']} ({data['user']['id']})")
        token_from_post: str = data["token"]
    
    print("\n[2b] Testing GET /auth/callback (Discord redirect flow)...")
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "fake_token"}
        mock_post.return_value = mock_token_response
        
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = mock_user
        mock_get.return_value = mock_user_response
        
        response = client.get("/auth/callback?code=fake_discord_code")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data: Dict[str, Any] = response.json()
        print(f"✓ GET /auth/callback endpoint works")
        print(f"✓ User: {data['user']['username']} ({data['user']['id']})")
        token_from_callback: str = data["token"]
    
    token: str = token_from_callback
    public_key: str = get_public_key_pem()
    
    decoded: Dict[str, Any] = jwt.decode(token, public_key, algorithms=["RS256"])
    print(f"✓ JWT is RS256 signed")
    print(f"✓ Payload claims:")
    print(f"  - discordId: {decoded['discordId']}")
    print(f"  - userId: {decoded['userId']}")
    print(f"  - username: {decoded['username']}")
    print(f"  - email: {decoded['email']}")
    assert decoded["discordId"] == "123456789"
    assert decoded["username"] == "testuser"
    
    print(f"\n[4] Checking token expiration...")
    exp_time: int = decoded["exp"]
    now: int = int(time.time())
    days_until_exp: float = (exp_time - now) / 86400
    print(f"✓ Token expires in {days_until_exp:.1f} days")
    assert 29 < days_until_exp < 31
    
    print(f"\n[5] Testing public key endpoint...")
    response = client.get("/auth/public-key")
    assert response.status_code == 200
    public_key_response: str = response.json()["public_key"]
    assert "BEGIN PUBLIC KEY" in public_key_response
    print(f"✓ Public key is accessible")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    try:
        test_full_auth_flow()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

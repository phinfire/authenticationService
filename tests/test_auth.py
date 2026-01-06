import os
import sys
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta, timezone

# Set environment variables BEFORE importing app
os.environ["DISCORD_CLIENT_ID"] = "test_id"
os.environ["DISCORD_CLIENT_SECRET"] = "test_secret"
os.environ["DISCORD_REDIRECT_URI"] = "http://localhost:8001/auth/callback"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import app
from src.keys import generate_rsa_keys, get_public_key_pem, get_private_key_pem

# Initialize for tests
generate_rsa_keys()

client = TestClient(app)


class TestHealthCheck:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data


class TestPublicKey:
    def test_public_key_endpoint(self):
        response = client.get("/public-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert data["public_key"].startswith("-----BEGIN PUBLIC KEY-----")
        assert data["public_key"].endswith("-----END PUBLIC KEY-----\n")


class TestJWTGeneration:
    def test_jwt_has_correct_claims(self):
        """Test that generated JWT contains expected claims."""
        private_key = get_private_key_pem()
        public_key = get_public_key_pem()
        
        payload = {
            "discordId": "test_user_123",
            "userId": "test_user_123",
            "username": "testuser",
            "email": "test@example.com",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(days=30)
        }
        
        token = jwt.encode(payload, private_key, algorithm="RS256")
        
        # Verify token can be decoded
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
        assert decoded["discordId"] == "test_user_123"
        assert decoded["username"] == "testuser"
        assert decoded["email"] == "test@example.com"


class TestAuthEndpoint:
    def test_auth_endpoint_missing_code(self):
        """Test auth endpoint rejects missing code."""
        response = client.post("/", json={"redirectUri": "http://localhost:3000"})
        assert response.status_code == 422  # Validation error
    
    def test_auth_endpoint_missing_redirect_uri(self):
        """Test auth endpoint rejects missing redirectUri."""
        response = client.post("/", json={"code": "test_code"})
        assert response.status_code == 422  # Validation error





# Manual test instructions
"""
To test the full OAuth flow manually:

1. Start the service:
   python -m uvicorn src.main:app --reload --port 8001

2. Get Discord OAuth URL:
   curl http://localhost:8001/auth/login
   
3. Visit the returned auth_url in your browser

4. After Discord redirects back, you'll have a real JWT token

5. Test JWT verification:
   curl -H "Authorization: Bearer <token>" http://localhost:8001/verify
   
6. Or test Docker locally:
   docker compose up
   
   Then curl the containerized service:
   curl -X POST http://localhost:8001/auth \
     -H "Content-Type: application/json" \
     -d '{"code":"test_code","redirectUri":"http://localhost:8001/auth/callback"}'
"""

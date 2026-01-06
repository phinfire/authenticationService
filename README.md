# Authentication Service

Discord OAuth → RS256 JWT tokens

## Endpoints

### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{"status": "healthy"}
```

### POST /
Exchange Discord authorization code for JWT token.

**Request:**
```json
{
  "code": "discord_auth_code",
  "redirectUri": "http://localhost:3000"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIs...",
  "user": {
    "id": "123456789",
    "username": "discordusername"
  }
}
```

### GET /public-key
Get RSA public key for JWT verification.

**Response:**
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\n..."
}
```

## JWT Claims
```json
{
  "discordId": "user_id",
  "userId": "user_id",
  "username": "username",
  "iat": 1767658324,
  "exp": 1770250324
}
```

- `discordId`: User's Discord ID (backwards compatible field)
- `userId`: User's Discord ID (new format)
- `username`: User's Discord username
- `iat`: Issued at (seconds since epoch)
- `exp`: Expiration (30 days from issue)

## Development
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run the service with auto-reload
python -m uvicorn src.main:app --reload --port 8001

# Run unit tests
pytest tests/ -v

# Run full integration test with mocked Discord API
python test_full_flow.py
```

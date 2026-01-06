# Authentication Service

Discord OAuth → RS256 JWT tokens

## Endpoints

### GET /health
Health check.

**Response:**
```json
{"status": "healthy"}
```

### GET /auth/login
Get Discord OAuth URL.

**Response:**
```json
{
  "auth_url": "https://discord.com/api/oauth2/authorize?client_id=...&..."
}
```

### POST /auth
Exchange Discord code for JWT.

**Request:**
```json
{
  "code": "discord_auth_code",
  "redirectUri": "http://localhost:8001/auth/callback"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJSUzI1NiIs...",
  "user": {
    "id": "334302555456929795",
    "username": "finfire"
  }
}
```

### GET /auth/callback
Discord redirect endpoint (query parameters).

**Query:** `code=...`

**Response:** Same as POST /auth

### GET /auth/public-key
Get public key for JWT verification (RS256).

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

## Environment Variables
```
DISCORD_CLIENT_ID=...
DISCORD_CLIENT_SECRET=...
DISCORD_REDIRECT_URI=http://localhost:8001/auth/callback
PORT=8001
```

## Development
```bash
python -m uvicorn src.main:app --reload --port 8001
pytest tests/ -v
python test_full_flow.py
```

## Docker
```bash
docker compose up --build
```

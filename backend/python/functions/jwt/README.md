# JWT Authentication Functions

This module provides JWT token management for authentication.

## Functions

### `setAuthJWT(user_id: int) -> str`
Creates a JWT token with user_id payload.

**Example:**
```python
from functions.jwt.setAuthJWT import setAuthJWT

token = setAuthJWT(123)
```

### `validateAuthJWT(token: str) -> bool`
Validates a JWT token (checks signature, expiration, and blacklist).

**Example:**
```python
from functions.jwt.validateAuthJWT import validateAuthJWT

is_valid = validateAuthJWT(token)
```

### `getPayloadAuthJWT(token: str) -> Optional[Dict]`
Extracts the payload from a JWT token.

**Example:**
```python
from functions.jwt.getPayloadAuthJWT import getPayloadAuthJWT, get_user_id_from_token

payload = getPayloadAuthJWT(token)
user_id = payload['user_id']  # if payload is not None

# Or use convenience function:
user_id = get_user_id_from_token(token)
```

### `deleteAuthJWT(token: str) -> bool`
Blacklists a JWT token (for logout functionality).

**Example:**
```python
from functions.jwt.deleteAuthJWT import deleteAuthJWT

success = deleteAuthJWT(token)
```

## Database Schema

You need to create a `jwt_blacklist` table for token blacklisting:

```sql
CREATE TABLE jwt_blacklist (
    id INT PRIMARY KEY AUTO_INCREMENT,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expires_at (expires_at)
);
```

## Environment Variables

Add to your `.env` file:
```env
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_EXPIRATION_HOURS=24
```

## Installation

Install PyJWT:
```bash
pip install PyJWT==2.9.0
```


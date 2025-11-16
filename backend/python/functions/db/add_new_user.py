"""
Add a new user to the database

This function creates a new user with:
- Encrypted email (AES-256)
- Hashed password (bcrypt)
- Encrypted API access key (AES-256)
"""

import sys
import os

# Add parent directories to path to import utils and crypto functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.db_connector import get_db_connection
from functions.crypto.password_hash import hash_password
from functions.crypto.aes_256_encrypt import encrypt, generate_api_key
from functions.crypto.email_hash import hash_email


def add_new_user(display_name: str, raw_email: str, raw_password: str):
    """
    Add a new user to the database.
    
    This function:
    1. Hashes the password using bcrypt
    2. Encrypts the email using AES-256
    3. Generates a new API access key
    4. Encrypts the API access key using AES-256
    5. Stores everything in the database
    
    Args:
        display_name: User's display name
        raw_email: User's raw email (will be encrypted)
        raw_password: User's raw password (will be hashed)
        
    Returns:
        User ID (int) if user was added successfully, None otherwise
    """
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return None
    
    try:
        # Hash the password
        password_hash = hash_password(raw_password)
        
        # Encrypt the email
        encrypted_email = encrypt(raw_email)
        
        # Hash the email for lookup (one-way hash, same result every time)
        email_hash = hash_email(raw_email)
        
        # Generate and encrypt API access key
        api_key = generate_api_key()
        encrypted_api_key = encrypt(api_key)
        
        cursor = conn.cursor()
        
        # Insert user with encrypted/hashed values
        query = """
            INSERT INTO users (display_name, encrypted_email, email_hash, password_hash, encrypted_api_key)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (display_name, encrypted_email, email_hash, password_hash, encrypted_api_key))
        conn.commit()
        
        # Get the user_id of the newly created user
        user_id = cursor.lastrowid
        
        print(f"User {display_name} added successfully (ID: {user_id})")
        print(f"API Key generated: {api_key}")  # Only print once during creation
        return user_id
        
    except Exception as e:
        print(f"Error adding user: {e}")
        conn.rollback()
        return None
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Example usage
    add_new_user("testuser", "test@example.com", "secure_password_123")


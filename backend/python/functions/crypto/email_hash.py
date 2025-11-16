"""
Email Hash Utility

This module provides a one-way hash function for email addresses.
Used for email lookup in the database since AES encryption produces
different results each time (due to random IV).
"""

import hashlib


def hash_email(email: str) -> str:
    """
    Generate a one-way SHA-256 hash of an email address.
    
    This produces the same hash for the same email every time,
    making it suitable for database lookups.
    
    Args:
        email: Email address to hash (will be lowercased and stripped)
        
    Returns:
        Hexadecimal string representation of the SHA-256 hash
        
    Example:
        from functions.crypto.email_hash import hash_email
        
        email_hash = hash_email("user@example.com")
        # Returns: "973dfe463ec85785f5f95af5ba3906eedb2d931c24e69824a89ea65dba4e813b"
    """
    # Normalize email: lowercase and strip whitespace
    normalized_email = email.lower().strip()
    
    # Generate SHA-256 hash
    hash_object = hashlib.sha256(normalized_email.encode('utf-8'))
    email_hash = hash_object.hexdigest()
    
    return email_hash


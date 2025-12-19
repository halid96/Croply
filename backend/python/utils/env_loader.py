"""
Environment Variable Loader Utility

This module provides functions to load environment variables from the project's
.env file (located at the repository root).
"""

import os
from typing import Dict, Optional


def load_env_file(env_path: str) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    if not os.path.exists(env_path):
        return env_vars
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                env_vars[key] = value
    
    return env_vars


def get_project_root() -> str:
    """
    Get the project root directory (where .env is located).
    
    Returns:
        Path to project root directory
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to project root: from backend/python/utils/ -> project root
    project_root = os.path.join(current_dir, "..", "..", "..")
    return os.path.abspath(project_root)


def get_env_file_path() -> str:
    """
    Get the absolute path to the repository's .env file.
    
    Returns:
        Path to .env file
    """
    project_root = get_project_root()
    return os.path.join(project_root, ".env")


def get_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a single environment variable from the appropriate .env file.
    
    Args:
        key: The environment variable key to retrieve
        default: Default value if key is not found
        
    Returns:
        The environment variable value or default if not found
        
    Example:
        from utils.env_loader import get_env_variable
        
        db_host = get_env_variable('DB_HOST', 'localhost')
        db_user = get_env_variable('DB_USER')
    """
    env_file_path = get_env_file_path()
    env_vars = load_env_file(env_file_path)
    return env_vars.get(key, default)


def get_env_variables() -> Dict[str, str]:
    """
    Get all environment variables from the .env file.
    
    Returns:
        Dictionary of all environment variables
        
    Example:
        from utils.env_loader import get_env_variables
        
        env_vars = get_env_variables()
        db_host = env_vars.get('DB_HOST')
        db_user = env_vars.get('DB_USER')
    """
    env_file_path = get_env_file_path()
    return load_env_file(env_file_path)

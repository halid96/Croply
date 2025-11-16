"""
Reusable MySQL Database Connector Utility

This module provides a reusable database connection function that loads
credentials from the appropriate .env file (local.env or production.env)
based on IS_DEVELOPMENT setting in environment.env.
"""

import mysql.connector
from mysql.connector import Error
from typing import Optional
from utils.env_loader import get_env_variables


def get_db_connection() -> Optional[mysql.connector.MySQLConnection]:
    """
    Get a MySQL database connection using credentials from the appropriate .env file.
    
    The .env file is determined by environment.env:
    - If IS_DEVELOPMENT=TRUE, uses local.env
    - Otherwise, uses production.env
    
    Expected environment variables in the .env file:
        DB_HOST=localhost
        DB_PORT=3306
        DB_USER=your_username
        DB_PASSWORD=your_password
        DB_NAME=your_database
    
    Returns:
        MySQL connection object or None if connection fails
        
    Example:
        from utils.db_connector import get_db_connection
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
            cursor.close()
            conn.close()
    """
    # Load environment variables from appropriate .env file
    env_vars = get_env_variables()
    
    # Get database credentials
    db_host = env_vars.get('DB_HOST', 'localhost')
    db_port = int(env_vars.get('DB_PORT', 3306))
    db_user = env_vars.get('DB_USER')
    db_password = env_vars.get('DB_PASSWORD')
    db_name = env_vars.get('DB_NAME')
    
    # Validate required credentials
    if not all([db_user, db_password, db_name]):
        from utils.env_loader import is_development
        env_type = "local.env" if is_development() else "production.env"
        raise ValueError(
            f"Missing required database credentials in {env_type}. "
            "Required: DB_USER, DB_PASSWORD, DB_NAME"
        )
    
    try:
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            autocommit=False
        )
        
        if connection.is_connected():
            return connection
            
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None
    
    return None


def get_db_cursor(connection: Optional[mysql.connector.MySQLConnection] = None):
    """
    Get a database cursor. If connection is provided, use it; otherwise create a new one.
    
    Args:
        connection: Optional existing connection. If None, creates a new connection.
        
    Returns:
        Tuple of (connection, cursor). If connection was provided, returns the same connection.
        If new connection was created, returns the new connection.
        
    Example:
        from utils.db_connector import get_db_cursor
        
        conn, cursor = get_db_cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
    """
    if connection is None:
        connection = get_db_connection()
        if connection is None:
            raise ConnectionError("Failed to establish database connection")
    
    return connection, connection.cursor()


"""
Job Status API Endpoint

GET /api/v1/job_status?job_id={job_id}&api_key={api_key}

Returns the current status and details of a reframe job.
"""

import os
import sys

# Add parent directories to path (go up from api/v1 to python/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from utils.db_connector import get_db_connection
from functions.crypto.aes_256_decrypt import decrypt

router = APIRouter()


def validate_api_key(api_key: str) -> dict:
    """
    Validate API key and return user info.
    API keys are stored encrypted in the database.
    Returns user dict if valid, None if invalid.
    """
    if not api_key:
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get all users with encrypted API keys
        query = """
            SELECT id, encrypted_api_key
            FROM users
            WHERE encrypted_api_key IS NOT NULL
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Decrypt and compare API keys
        for result in results:
            user_id, encrypted_key = result
            try:
                decrypted_key = decrypt(encrypted_key)
                if decrypted_key == api_key:
                    return {'id': user_id}
            except Exception:
                continue
        
        return None
    finally:
        cursor.close()
        conn.close()


def get_job_details(job_id: str, user_id: int) -> dict:
    """
    Get job details from database.
    Only returns job if it belongs to the user.
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                job_id,
                status,
                callback_url,
                job_started_unix,
                job_completed_unix,
                error_message,
                reframed_video_url,
                callback_response_error,
                failed_callbacks_count,
                last_callback_unix
            FROM jobs
            WHERE job_id = %s AND user_id = %s
        """
        cursor.execute(query, (job_id, user_id))
        result = cursor.fetchone()
        
        if result:
            return {
                'job_id': result[0],
                'status': result[1],
                'callback_url': result[2],
                'job_started_unix': result[3],
                'job_completed_unix': result[4],
                'error_message': result[5],
                'reframed_video_url': result[6],
                'callback_response_error': result[7],
                'failed_callbacks_count': result[8],
                'last_callback_unix': result[9]
            }
        return None
    finally:
        cursor.close()
        conn.close()


@router.get("/v1/job_status")
async def job_status(
    job_id: str = Query(..., description="The job ID returned from the reframe API"),
    api_key: str = Query(..., description="Your API access key")
) -> JSONResponse:
    """
    Check the status of a reframe job.
    
    Returns job details including status, timestamps, and result URLs.
    """
    
    # Validate API key
    user = validate_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get job details
    job = get_job_details(job_id, user['id'])
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JSONResponse(content=job)

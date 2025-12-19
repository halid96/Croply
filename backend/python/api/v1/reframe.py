"""
Reframe API Endpoint (v1)

This endpoint handles video reframing job submissions.
"""

import os
import sys
import uuid
import time
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from utils.db_connector import get_db_connection
from functions.crypto.aes_256_decrypt import decrypt

router = APIRouter()

# Configuration - using v1_reframe script
REFRAME_SCRIPT_VERSION = "v1"
REFRAME_SCRIPT_PATH = "backend/python/reframe_scripts/v1_reframe/reframe_v1.py"
COST_PER_MINUTE = 0.10  # £0.10 per minute
MINIMUM_CHARGE = 0.10   # £0.10 minimum


class ReframeRequest(BaseModel):
    video_url: HttpUrl
    api_key: str
    callback_url: Optional[HttpUrl] = None


def get_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Get user by decrypted API key.
    
    Args:
        api_key: User's API access key
        
    Returns:
        Dictionary with user data (id, balance) or None if not found
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get all users with encrypted API keys
        query = """
            SELECT id, encrypted_api_key, api_credits
            FROM users
            WHERE encrypted_api_key IS NOT NULL
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Decrypt and compare API keys
        for result in results:
            user_id, encrypted_key, balance = result
            try:
                decrypted_key = decrypt(encrypted_key)
                if decrypted_key == api_key:
                    return {
                        'id': user_id,
                        'balance': float(balance) if balance is not None else 0.00
                    }
            except Exception as e:
                print(f"Error decrypting API key for user {user_id}: {e}")
                continue
        
        return None
        
    except Exception as e:
        print(f"Error getting user by API key: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_video_duration(video_url: str) -> Optional[float]:
    """
    Get video duration in seconds using ffprobe.
    Downloads the video temporarily to check duration.
    
    Args:
        video_url: URL to the video file
        
    Returns:
        Duration in seconds or None if unable to determine
    """
    import subprocess
    import tempfile
    
    temp_file = None
    try:
        # Download video to temporary file
        print(f"Downloading video to check duration: {video_url}")
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            # Download in chunks
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Use ffprobe to get duration
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            temp_file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            print(f"Video duration: {duration} seconds")
            return duration
        else:
            print(f"ffprobe error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return None
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass


def create_job(user_id: int, video_url: str, callback_url: Optional[str]) -> str:
    """
    Create a new reframe job in the database.
    
    Args:
        user_id: User's ID
        video_url: URL to the video file
        callback_url: Optional callback URL
        
    Returns:
        job_id: Unique job identifier
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Failed to connect to database")
    
    job_id = str(uuid.uuid4())
    current_time = int(time.time())
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        query = """
            INSERT INTO jobs (
                job_id, 
                user_id, 
                video_url, 
                callback_url, 
                status, 
                created_unix
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            job_id,
            user_id,
            video_url,
            callback_url,
            'in_queue',
            current_time
        ))
        
        conn.commit()
        return job_id
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/v1/reframe")
async def reframe_video(request: ReframeRequest) -> JSONResponse:
    """
    Submit a video reframing job.
    
    This endpoint creates a job immediately and returns a job_id.
    The actual video processing happens asynchronously in a background worker.
    
    Args:
        request: ReframeRequest containing video_url, api_key, and optional callback_url
        
    Returns:
        JSON response with job_id or error
    """
    
    # Step 1: Validate API key and get user
    user = get_user_by_api_key(request.api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    user_id = user['id']
    user_balance = user['balance']
    
    # Step 2: Check if user has minimum balance
    # We only check minimum here - actual cost will be calculated during processing
    if user_balance < MINIMUM_CHARGE:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=f"Insufficient balance. Minimum required: £{MINIMUM_CHARGE:.2f}, Your balance: £{user_balance:.2f}"
        )
    
    # Step 3: Create job in database immediately
    # The job will be processed by a background worker
    try:
        job_id = create_job(
            user_id=user_id,
            video_url=str(request.video_url),
            callback_url=str(request.callback_url) if request.callback_url else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")
    
    # Step 4: Return success response immediately
    # Background worker will:
    # - Download video
    # - Check duration with ffprobe
    # - Verify user has enough balance
    # - Process video if balance sufficient
    # - Update job status
    # - Send webhook if callback_url provided
    return JSONResponse(content={
        "success": True,
        "job_id": job_id
    }, status_code=200)

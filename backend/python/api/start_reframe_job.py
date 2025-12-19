"""
Background Worker: Start Reframe Job

This script processes a single reframe job:
1. Downloads the video
2. Checks duration with ffprobe
3. Verifies user balance
4. Processes video with reframe script
5. Uploads result
6. Updates job status
7. Sends webhook callback
"""

import os
import sys
import time
import subprocess
import tempfile
import requests
import shutil
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.db_connector import get_db_connection
from utils.env_loader import get_env_variable

router = APIRouter()

# Configuration
COST_PER_MINUTE = 0.10  # £0.10 per minute
MINIMUM_CHARGE = 0.10   # £0.10 minimum
REFRAME_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    '..',  # Go up from api/
    'reframe_scripts', 
    'v1_reframe', 
    'reframe_v1.py'
)
STORAGE_DIR = os.path.join(
    os.path.dirname(__file__),
    '..',  # Go up from api/
    '..',  # Go up from python/
    'storage'
)
VIDEOS_AWAITING_DIR = os.path.join(STORAGE_DIR, 'videos_awaiting_reframe')
VIDEOS_REFRAMED_DIR = os.path.join(STORAGE_DIR, 'videos_reframed')

# Ensure directories exist
os.makedirs(VIDEOS_AWAITING_DIR, exist_ok=True)
os.makedirs(VIDEOS_REFRAMED_DIR, exist_ok=True)


class StartJobRequest(BaseModel):
    job_id: str
    internal_api_key: str


def validate_internal_api_key(api_key: str) -> bool:
    """Validate internal API key from environment."""
    expected_key = get_env_variable('INTERNAL_API_KEY')
    if not expected_key:
        print("ERROR: INTERNAL_API_KEY not set in environment")
        return False
    return api_key == expected_key


def get_job(job_id: str) -> dict:
    """Get job details from database."""
    conn = get_db_connection()
    if not conn:
        raise Exception("Failed to connect to database")
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT job_id, user_id, video_url, callback_url, status
            FROM jobs
            WHERE job_id = %s
            LIMIT 1
        """
        cursor.execute(query, (job_id,))
        result = cursor.fetchone()
        
        if not result:
            raise Exception(f"Job {job_id} not found")
        
        return {
            'job_id': result[0],
            'user_id': result[1],
            'video_url': result[2],
            'callback_url': result[3],
            'status': result[4]
        }
    finally:
        cursor.close()
        conn.close()


def update_job_status(job_id: str, status: str, error_message: str = None, 
                     reframed_video_url: str = None, started_unix: int = None,
                     completed_unix: int = None):
    """Update job status in database."""
    conn = get_db_connection()
    if not conn:
        raise Exception("Failed to connect to database")
    
    try:
        cursor = conn.cursor()
        
        # Build dynamic query based on provided parameters
        updates = ["status = %s"]
        params = [status]
        
        if error_message is not None:
            updates.append("error_message = %s")
            params.append(error_message)
        
        if reframed_video_url is not None:
            updates.append("reframed_video_url = %s")
            params.append(reframed_video_url)
        
        if started_unix is not None:
            updates.append("job_started_unix = %s")
            params.append(started_unix)
        
        if completed_unix is not None:
            updates.append("job_completed_unix = %s")
            params.append(completed_unix)
        
        params.append(job_id)
        
        query = f"""
            UPDATE jobs
            SET {', '.join(updates)}
            WHERE job_id = %s
        """
        
        cursor.execute(query, tuple(params))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_user_balance(user_id: int) -> float:
    """Get user's current balance."""
    conn = get_db_connection()
    if not conn:
        raise Exception("Failed to connect to database")
    
    try:
        cursor = conn.cursor()
        query = "SELECT api_credits FROM users WHERE id = %s LIMIT 1"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if not result:
            raise Exception(f"User {user_id} not found")
        
        return float(result[0]) if result[0] is not None else 0.00
    finally:
        cursor.close()
        conn.close()


def deduct_balance(user_id: int, amount: float):
    """Deduct amount from user's balance."""
    conn = get_db_connection()
    if not conn:
        raise Exception("Failed to connect to database")
    
    try:
        cursor = conn.cursor()
        query = """
            UPDATE users
            SET api_credits = api_credits - %s
            WHERE id = %s
        """
        cursor.execute(query, (amount, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0 and result.stdout.strip():
        return float(result.stdout.strip())
    else:
        raise Exception(f"ffprobe error: {result.stderr}")


def download_video(video_url: str, output_path: str):
    """Download video from URL."""
    print(f"Downloading video from: {video_url}")
    response = requests.get(video_url, stream=True, timeout=300)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print(f"Video downloaded to: {output_path}")


def process_video(input_path: str, output_path: str):
    """Process video using reframe script."""
    print(f"Processing video with reframe script...")
    
    cmd = [
        sys.executable,  # Use the same Python interpreter (venv)
        REFRAME_SCRIPT_PATH,
        input_path,
        '--output', output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    
    if result.returncode != 0:
        # Log full stderr internally for debugging, but don't expose it via API
        print(f"[Reframe script stderr] {result.stderr}")
        raise Exception("Reframe script failed with a processing error")
    
    print(f"Video processed successfully: {output_path}")


def send_webhook(callback_url: str, job_data: dict) -> bool:
    """
    Send webhook callback and record the attempt in database.
    
    The callback endpoint should return HTTP 200 to acknowledge receipt.
    If the response contains success=false, we record the error but don't retry
    (the webhook was delivered successfully, the error is on the recipient's side).
    
    Returns True if webhook was delivered (HTTP 200), False if delivery failed.
    """
    if not callback_url:
        return False
    
    job_id = job_data.get('job_id')
    print(f"Sending webhook to: {callback_url}")
    
    try:
        response = requests.post(
            callback_url,
            json=job_data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        callback_unix = int(time.time())
        
        if response.status_code == 200:
            # Parse response to check if recipient reported an error
            callback_error = None
            try:
                response_data = response.json()
                if response_data.get('success') == False:
                    # Recipient reported an error - record it but don't retry
                    error_msg = response_data.get('error_message') or response_data.get('error') or 'Unknown error'
                    callback_error = f"Recipient error: {error_msg}"
                    print(f"Webhook delivered but recipient reported error: {callback_error}")
                else:
                    print("Webhook sent successfully")
            except:
                # Response wasn't JSON, that's fine - just means success
                print("Webhook sent successfully (non-JSON response)")
            
            # Record callback as delivered (success=True means delivered, not processed)
            if job_id:
                update_callback_status(job_id, callback_unix, delivered=True, callback_error=callback_error)
            return True
        else:
            print(f"Webhook delivery failed with HTTP {response.status_code}: {response.text[:200]}")
            # Record failed delivery
            if job_id:
                update_callback_status(job_id, callback_unix, delivered=False, 
                                       callback_error=f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Webhook delivery error: {e}")
        callback_unix = int(time.time())
        if job_id:
            update_callback_status(job_id, callback_unix, delivered=False, callback_error=str(e))
        return False


def update_callback_status(job_id: str, callback_unix: int, delivered: bool, callback_error: str = None):
    """
    Update webhook callback status in database.
    
    Args:
        job_id: The job identifier
        callback_unix: Unix timestamp of the callback attempt
        delivered: True if HTTP 200 received (webhook delivered), False if delivery failed
        callback_error: Error message (either from failed delivery or recipient's error response)
    """
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database for callback status update")
        return
    
    try:
        cursor = conn.cursor()
        
        if delivered:
            # Webhook was delivered (HTTP 200) - record time and any recipient error
            # Reset failed_callbacks_count since delivery succeeded
            if callback_error:
                query = """
                    UPDATE jobs
                    SET last_callback_unix = %s,
                        failed_callbacks_count = 0,
                        callback_response_error = %s
                    WHERE job_id = %s
                """
                cursor.execute(query, (callback_unix, callback_error, job_id))
            else:
                query = """
                    UPDATE jobs
                    SET last_callback_unix = %s,
                        failed_callbacks_count = 0,
                        callback_response_error = NULL
                    WHERE job_id = %s
                """
                cursor.execute(query, (callback_unix, job_id))
        else:
            # Webhook delivery failed - increment retry counter
            query = """
                UPDATE jobs
                SET last_callback_unix = %s,
                    failed_callbacks_count = COALESCE(failed_callbacks_count, 0) + 1,
                    callback_response_error = %s
                WHERE job_id = %s
            """
            cursor.execute(query, (callback_unix, callback_error, job_id))
        
        conn.commit()
        status_str = "delivered" if delivered else "delivery failed"
        error_str = f" (error: {callback_error})" if callback_error else ""
        print(f"Updated callback status for job {job_id}: {status_str}{error_str}")
    except Exception as e:
        print(f"Error updating callback status: {e}")
    finally:
        cursor.close()
        conn.close()


def process_job(job_id: str):
    """Main job processing function."""
    started_unix = int(time.time())
    
    try:
        # Update status to processing
        update_job_status(job_id, 'processing', started_unix=started_unix)
        
        # Get job details
        job = get_job(job_id)
        user_id = job['user_id']
        video_url = job['video_url']
        callback_url = job['callback_url']
        
        # Download video
        input_filename = f"{job_id}_input.mp4"
        input_path = os.path.join(VIDEOS_AWAITING_DIR, input_filename)
        download_video(video_url, input_path)
        
        # Get video duration
        duration_seconds = get_video_duration(input_path)
        duration_minutes = duration_seconds / 60.0
        
        # Calculate cost
        cost = max(MINIMUM_CHARGE, duration_minutes * COST_PER_MINUTE)
        print(f"Video duration: {duration_seconds}s ({duration_minutes:.2f} min), Cost: £{cost:.2f}")
        
        # Check user balance
        user_balance = get_user_balance(user_id)
        print(f"User balance: £{user_balance:.2f}")
        
        if user_balance < cost:
            raise Exception(
                f"Insufficient balance. Required: £{cost:.2f}, Available: £{user_balance:.2f}"
            )
        
        # Process video
        output_filename = f"{job_id}_reframed.mp4"
        output_path = os.path.join(VIDEOS_REFRAMED_DIR, output_filename)
        process_video(input_path, output_path)
        
        # Deduct balance
        deduct_balance(user_id, cost)
        print(f"Deducted £{cost:.2f} from user balance")
        
        # Generate public URL for reframed video
        base_url = get_env_variable('BASE_URL', 'https://croply.uk')
        reframed_video_url = f"{base_url}/storage/videos_reframed/{output_filename}"
        
        # Update job as successful
        completed_unix = int(time.time())
        update_job_status(
            job_id,
            'success',
            reframed_video_url=reframed_video_url,
            completed_unix=completed_unix
        )
        
        # Send webhook
        if callback_url:
            webhook_data = {
                'status': 'success',
                'job_id': job_id,
                'callback_url': callback_url,
                'job_started_unix': started_unix,
                'job_completed_unix': completed_unix,
                'error_message': None,
                'reframed_video_url': reframed_video_url
            }
            send_webhook(callback_url, webhook_data)
        
        # Clean up input file
        if os.path.exists(input_path):
            os.unlink(input_path)
        
        print(f"Job {job_id} completed successfully!")
        return True
        
    except Exception as e:
        # Log full technical error internally
        print(f"Job {job_id} failed with internal error: {e}")
        
        # Generate a safe, human-readable error message for external consumers
        raw_msg = str(e) if e else ""
        if "Insufficient balance" in raw_msg:
            public_error = raw_msg
        elif "Job " in raw_msg and " not found" in raw_msg:
            public_error = "Job not found"
        elif "Failed to connect to database" in raw_msg:
            public_error = "Internal database connection error"
        elif "ffprobe error" in raw_msg:
            public_error = "Unable to analyze video file"
        elif "Reframe script failed" in raw_msg:
            public_error = "Video processing failed due to an internal error"
        else:
            public_error = "Video processing failed due to an internal error"
        
        # Update job as failed with safe error message
        completed_unix = int(time.time())
        update_job_status(
            job_id,
            'failed',
            error_message=public_error,
            completed_unix=completed_unix
        )
        
        # Send webhook with safe error message
        if callback_url:
            webhook_data = {
                'status': 'failed',
                'job_id': job_id,
                'callback_url': callback_url,
                'job_started_unix': started_unix,
                'job_completed_unix': completed_unix,
                'error_message': public_error,
                'reframed_video_url': None
            }
            send_webhook(callback_url, webhook_data)
        
        return False


@router.post("/internal/start_reframe_job")
async def start_reframe_job(request: StartJobRequest) -> JSONResponse:
    """
    Internal API endpoint to start processing a reframe job.
    
    This should only be called by the cron job with the internal API key.
    """
    
    # Validate internal API key
    if not validate_internal_api_key(request.internal_api_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    
    # Process the job
    try:
        success = process_job(request.job_id)
        
        return JSONResponse(content={
            "success": success,
            "job_id": request.job_id,
            "message": "Job processed successfully" if success else "Job processing failed"
        }, status_code=200)
        
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "job_id": request.job_id,
            "error": str(e)
        }, status_code=500)

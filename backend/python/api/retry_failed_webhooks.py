"""
Retry Failed Webhooks - Cron Job Handler

This endpoint is called by cron every minute.
It retries failed webhook callbacks according to the retry policy:
- Retry within 10 mins up to 3 times
"""

import os
import sys
import time
import requests

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from utils.db_connector import get_db_connection
from utils.env_loader import get_env_variable

router = APIRouter()

# Retry policy
MAX_RETRY_ATTEMPTS = 3
RETRY_INTERVAL_SECONDS = 180  # 3 minutes between retries (10 mins / 3 attempts ≈ 3 mins)


def validate_internal_api_key(api_key: str) -> bool:
    """Validate internal API key from environment."""
    expected_key = get_env_variable('INTERNAL_API_KEY')
    if not expected_key:
        print("ERROR: INTERNAL_API_KEY not set in environment")
        return False
    return api_key == expected_key


def get_jobs_needing_webhook_retry():
    """
    Get jobs that need webhook retry.
    
    Criteria:
    - Has callback_url
    - Status is 'success' or 'failed' (job completed)
    - failed_callbacks_count < 3
    - Either never attempted OR last attempt was > 3 minutes ago
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    current_time = int(time.time())
    retry_threshold = current_time - RETRY_INTERVAL_SECONDS
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT job_id, callback_url, status, job_started_unix, 
                   job_completed_unix, error_message, reframed_video_url,
                   failed_callbacks_count, last_callback_unix
            FROM jobs
            WHERE callback_url IS NOT NULL
              AND status IN ('success', 'failed')
              AND failed_callbacks_count < %s
              AND (last_callback_unix IS NULL OR last_callback_unix < %s)
            ORDER BY job_completed_unix ASC
            LIMIT 10
        """
        cursor.execute(query, (MAX_RETRY_ATTEMPTS, retry_threshold))
        results = cursor.fetchall()
        
        jobs = []
        for row in results:
            jobs.append({
                'job_id': row[0],
                'callback_url': row[1],
                'status': row[2],
                'job_started_unix': row[3],
                'job_completed_unix': row[4],
                'error_message': row[5],
                'reframed_video_url': row[6],
                'failed_callbacks_count': row[7],
                'last_callback_unix': row[8]
            })
        
        return jobs
    finally:
        cursor.close()
        conn.close()


def update_webhook_attempt(job_id: str, delivered: bool, callback_error: str = None):
    """
    Update webhook attempt status.
    
    Args:
        job_id: The job identifier
        delivered: True if HTTP 200 received, False if delivery failed
        callback_error: Error message from delivery failure or recipient's response
    """
    conn = get_db_connection()
    if not conn:
        return
    
    current_time = int(time.time())
    
    try:
        cursor = conn.cursor()
        
        if delivered:
            # Webhook delivered - reset counters, record any recipient error
            if callback_error:
                query = """
                    UPDATE jobs
                    SET failed_callbacks_count = 0,
                        last_callback_unix = %s,
                        callback_response_error = %s
                    WHERE job_id = %s
                """
                cursor.execute(query, (current_time, callback_error, job_id))
            else:
                query = """
                    UPDATE jobs
                    SET failed_callbacks_count = 0,
                        last_callback_unix = %s,
                        callback_response_error = NULL
                    WHERE job_id = %s
                """
                cursor.execute(query, (current_time, job_id))
        else:
            # Webhook delivery failed - increment counter
            query = """
                UPDATE jobs
                SET failed_callbacks_count = COALESCE(failed_callbacks_count, 0) + 1,
                    last_callback_unix = %s,
                    callback_response_error = %s
                WHERE job_id = %s
            """
            cursor.execute(query, (current_time, callback_error, job_id))
        
        conn.commit()
    except Exception as e:
        print(f"Error updating webhook attempt: {e}")
    finally:
        cursor.close()
        conn.close()


def send_webhook(job: dict) -> tuple:
    """
    Send webhook callback.
    
    Returns tuple of (delivered: bool, callback_error: str or None)
    - delivered=True means HTTP 200 was received (don't retry)
    - callback_error contains any error from delivery failure or recipient's response
    """
    callback_url = job['callback_url']
    job_id = job['job_id']
    
    webhook_data = {
        'status': job['status'],
        'job_id': job_id,
        'callback_url': callback_url,
        'job_started_unix': job['job_started_unix'],
        'job_completed_unix': job['job_completed_unix'],
        'error_message': job['error_message'],
        'reframed_video_url': job['reframed_video_url']
    }
    
    try:
        print(f"Sending webhook for job {job_id} to {callback_url}")
        response = requests.post(
            callback_url,
            json=webhook_data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            # Parse response to check if recipient reported an error
            callback_error = None
            try:
                response_data = response.json()
                if response_data.get('success') == False:
                    error_msg = response_data.get('error_message') or response_data.get('error') or 'Unknown error'
                    callback_error = f"Recipient error: {error_msg}"
                    print(f"Webhook delivered to {job_id} but recipient reported error: {callback_error}")
                else:
                    print(f"Webhook successful for job {job_id}")
            except:
                print(f"Webhook successful for job {job_id} (non-JSON response)")
            
            return (True, callback_error)
        else:
            error = f"HTTP {response.status_code}"
            print(f"Webhook delivery failed for job {job_id}: {error}")
            return (False, error)
            
    except Exception as e:
        error = str(e)
        print(f"Webhook error for job {job_id}: {error}")
        return (False, error)


@router.get("/retry_failed_webhooks")
async def retry_failed_webhooks(internal_api_key: str = Query(...)) -> JSONResponse:
    """
    Retry failed webhook callbacks.
    
    Called by cron every minute.
    Retries webhooks that failed, up to 3 times within 10 minutes.
    """
    
    # Validate internal API key
    if not validate_internal_api_key(internal_api_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    
    # Get jobs needing webhook retry
    jobs = get_jobs_needing_webhook_retry()
    
    if not jobs:
        return JSONResponse(content={
            "success": True,
            "message": "No webhooks need retry",
            "retried": 0
        })
    
    # Retry webhooks
    results = []
    delivered_count = 0
    failed_count = 0
    
    for job in jobs:
        job_id = job['job_id']
        attempt_num = job['failed_callbacks_count'] + 1
        
        print(f"Retrying webhook for job {job_id} (attempt {attempt_num}/{MAX_RETRY_ATTEMPTS})")
        
        delivered, callback_error = send_webhook(job)
        update_webhook_attempt(job_id, delivered, callback_error)
        
        if delivered:
            delivered_count += 1
        else:
            failed_count += 1
        
        results.append({
            'job_id': job_id,
            'attempt': attempt_num,
            'delivered': delivered,
            'callback_error': callback_error
        })
    
    return JSONResponse(content={
        "success": True,
        "message": f"Retried {len(jobs)} webhook(s)",
        "retried": len(jobs),
        "delivered": delivered_count,
        "failed": failed_count,
        "results": results
    })

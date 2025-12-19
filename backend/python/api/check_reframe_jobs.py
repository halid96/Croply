"""
Check Reframe Jobs - Cron Job Handler

This endpoint is called by cron every minute.
It checks if there's a job currently processing.
If not, it starts the next job in queue.
"""

import os
import sys

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from utils.db_connector import get_db_connection
from utils.env_loader import get_env_variable
from api.start_reframe_job import process_job

router = APIRouter()


def validate_internal_api_key(api_key: str) -> bool:
    """Validate internal API key from environment."""
    expected_key = get_env_variable('INTERNAL_API_KEY')
    if not expected_key:
        print("ERROR: INTERNAL_API_KEY not set in environment")
        return False
    return api_key == expected_key


def get_processing_job():
    """Check if there's a job currently processing."""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT job_id 
            FROM jobs 
            WHERE status = 'processing' 
            LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()


def get_next_job():
    """Get the next job in queue."""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
            SELECT job_id 
            FROM jobs 
            WHERE status = 'in_queue' 
            ORDER BY created_unix ASC 
            LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()


@router.get("/check_reframe_jobs")
async def check_reframe_jobs(internal_api_key: str = Query(...)) -> JSONResponse:
    """
    Check for jobs to process.
    
    Called by cron every minute.
    If no job is processing, starts the next job in queue.
    """
    
    # Validate internal API key
    if not validate_internal_api_key(internal_api_key):
        raise HTTPException(status_code=401, detail="Invalid internal API key")
    
    # Check if there's a job currently processing
    processing_job = get_processing_job()
    if processing_job:
        return JSONResponse(content={
            "success": True,
            "message": f"Job {processing_job} is currently processing",
            "action": "none"
        })
    
    # Get next job in queue
    next_job = get_next_job()
    if not next_job:
        return JSONResponse(content={
            "success": True,
            "message": "No jobs in queue",
            "action": "none"
        })
    
    # Process the job
    try:
        print(f"Starting job: {next_job}")
        success = process_job(next_job)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Job {next_job} processed",
            "action": "processed",
            "job_id": next_job,
            "result": "success" if success else "failed"
        })
        
    except Exception as e:
        print(f"Error processing job {next_job}: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"Error processing job {next_job}: {str(e)}",
            "action": "error",
            "job_id": next_job
        }, status_code=500)

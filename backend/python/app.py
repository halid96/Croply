import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from api.send_email_verification_code import router as email_verification_router
from api.regenerate_api_key import router as regenerate_api_key_router
from api.register_user import router as register_user_router
from api.get_user_info import router as get_user_info_router
from api.logout import router as logout_router
from api.login import router as login_router
from api.send_password_reset import router as send_password_reset_router
from api.reset_password import router as reset_password_router
from api.contact import router as contact_router
from api.v1.reframe import router as reframe_router
from api.v1.job_status import router as job_status_router
from api.start_reframe_job import router as start_reframe_job_router
from api.check_reframe_jobs import router as check_reframe_jobs_router
from api.retry_failed_webhooks import router as retry_failed_webhooks_router

app = FastAPI(
    title="Croply API",
    description="Croply Backend API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
# Available routes:
# POST /api/send_email_verification_code - Send email verification code
# POST /api/register_user - Register a new user
# POST /api/regenerate_api_key - Regenerate user's API key (requires JWT)
app.include_router(email_verification_router, prefix="/api", tags=["authentication"])
app.include_router(regenerate_api_key_router, prefix="/api", tags=["user"])
app.include_router(register_user_router, prefix="/api", tags=["authentication"])
app.include_router(get_user_info_router, prefix="/api", tags=["user"])
app.include_router(logout_router, prefix="/api", tags=["authentication"])
app.include_router(login_router, prefix="/api", tags=["authentication"])
app.include_router(send_password_reset_router, prefix="/api", tags=["authentication"])
app.include_router(reset_password_router, prefix="/api", tags=["authentication"])
app.include_router(contact_router, prefix="/api", tags=["contact"])
app.include_router(reframe_router, prefix="/api", tags=["reframe"])
app.include_router(job_status_router, prefix="/api", tags=["reframe"])
app.include_router(start_reframe_job_router, prefix="/api", tags=["internal"])
app.include_router(check_reframe_jobs_router, prefix="/api", tags=["cron"])
app.include_router(retry_failed_webhooks_router, prefix="/api", tags=["cron"])



@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main index.html page."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "..", "..", "frontend", "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/terms-of-service")
async def terms_endpoint():
    """Serve the terms.html page."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "..", "..", "frontend", "templates", "terms.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/privacy-policy")
async def privacy_policy_endpoint():
    """Serve the terms.html page."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "..", "..", "frontend", "templates", "terms.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/api/v1/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return JSONResponse(content={"success": True, "message": "API is working"})


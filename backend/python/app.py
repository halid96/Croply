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


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serve the main index.html page.
    """
    # Get the path to index.html
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to frontend/templates: from backend/python/ -> frontend/templates/
    html_path = os.path.join(current_dir, "..", "..", "frontend", "templates", "index.html")
    
    # Read and return the HTML file
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)


@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return JSONResponse(content={"success": True, "message": "API is working"})


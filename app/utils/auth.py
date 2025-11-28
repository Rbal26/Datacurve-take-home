import os
from fastapi import HTTPException, Header
from dotenv import load_dotenv

load_dotenv()


def verify_api_key(authorization: str = Header(None)):
    expected_token = os.getenv("API_TOKEN")
    
    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="API_TOKEN not configured"
        )
    
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization format. Use: Bearer <token>"
        )
    
    token = authorization.replace("Bearer ", "")
    
    if token != expected_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid API token"
        )
    
    return True


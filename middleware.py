# dependencies.py
from fastapi import Depends, HTTPException, Request
from security import verify_token

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = verify_token(token)
        request.state.user = payload  # Attach user payload to request state
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
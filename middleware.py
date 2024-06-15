# dependencies.py
from fastapi import Depends, HTTPException, Request
from security import verify_token

# def get_current_user(request: Request):
#     token = request.cookies.get("access_token")
#     if not token:
#         raise HTTPException(status_code=401, detail="Not authenticated")
    
#     try:
#         payload = verify_token(token)
#         request.state.user = payload  # Attach user payload to request state
#         return payload
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=str(e))

def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = verify_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        role: str = payload.get("role")
        if role is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        name: str = payload.get("name")
        if name is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        token_data = {"id": user_id, "role": role, "name": name}
        request.state.user = token_data  # Attach user payload to request state
        return token_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# def get_current_user(request: Request):
#     # Temporarily bypass authentication
#     token_data = {"id": 1, "role": "admin", "name": "test_user"}  # Mock user data
#     request.state.user = token_data  # Attach user payload to request state
#     return token_data
# dependencies.py
from fastapi import Depends, HTTPException, Request
from security import verify_token
from fastapi import HTTPException, status, Depends

from jose import JWTError, jwt

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
<<<<<<< Updated upstream
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
=======
    # Temporarily bypass authentication
    token_data = {"id": 1, "role": "centra", "name": "test_user"}  # Mock user data
    request.state.user = token_data  # Attach user payload to request state
    return token_data

def role_required(required_role: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if current_user.role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
>>>>>>> Stashed changes

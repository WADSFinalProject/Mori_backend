from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from security import verify_token
from jose import JWTError

class JWTMiddleware(BaseHTTPMiddleware): 
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get("refresh")
        if not token: 
            raise HTTPException(status_code=401, detail="Not Authenticated")
        
        try: 
            payload = verify_token(token)
            request.state.user = payload
        except JWTError as e: 
            raise HTTPException(status_code=401, detail="Invalid Token")
        
        response = await call_next(request)
        return response
        
        
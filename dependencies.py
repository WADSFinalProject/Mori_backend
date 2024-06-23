from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from utils import verify_token

# def get_current_user(request: Request):
#     authorization: str = request.headers.get("Authorization")
#     if not authorization or not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Not authenticated")

#     token = authorization.split(" ")[1]

#     try:
#         payload = verify_token(token)
#         user_id: int = payload.get("sub")
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication credentials")
#         role: str = payload.get("role")
#         if role is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication credentials")
#         name: str = payload.get("name")
#         if name is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication credentials")

#         token_data = {"id": user_id, "role": role, "name": name}

#         # Add centra_id if the user role is "Centra"
#         if role == "Centra":
#             centra_id = payload.get("centralID")
#             if centra_id is not None:
#                 token_data["centralID"] = centra_id
#         return token_data
#     except JWTError as e:
#         raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user():
    # Temporarily bypass authentication
    token_data = {"id": 4, "role": "Admin", "name": "test_user"}  # Mock user data
    # request.state.user = token_data  # Attach user payload to request state
    return token_data


def centra_user(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Centra", "Admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

def harbour_user(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Harbour Guard", "Admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

def xyz_user(user: dict = Depends(get_current_user)):
    if user["role"] not in ["XYZ", "Admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

def admin_user(user: dict = Depends(get_current_user)):
    if user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

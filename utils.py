from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import jwt , JWTError
import crud
from config import SECRET_KEY, ALGORITHM


def create_access_token(db: Session, user_id: int, role: str, name: str) -> str:
    payload = {
        "sub": str(user_id),
        "name": name,
        "role": role,
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30)
    }
    
    if role == "Centra":
        centra_id = crud.get_centra_id(db, user_id)
        if centra_id:
            payload["centralID"] = centra_id
    elif role == "XYZ":
        warehouse_id = crud.get_warehouse_id(db, user_id)
        if warehouse_id:
            payload["warehouse_id"] = warehouse_id

    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return access_token

def create_refresh_token(db: Session, user_id: int, role: str, name: str) -> str:
    payload = {
        "sub": str(user_id),
        "name": name,
        "role": role,
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=12)
    }

    if role == "Centra":
        centra_id = crud.get_centra_id(db, user_id)
        if centra_id:
            payload["centralID"] = centra_id
    elif role == "XYZ":
        warehouse_id = crud.get_warehouse_id(db, user_id)
        if warehouse_id:
            payload["warehouse_id"] = warehouse_id

    refresh_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token



def verify_token(token: str):
    try:
        decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_jwt
    except JWTError as e:
        if e.args[0] == 'Expired token':
            raise HTTPException(status_code=401, detail="Token expired")
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
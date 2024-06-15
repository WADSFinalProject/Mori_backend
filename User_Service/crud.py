from sqlalchemy.orm import Session
import models, schemas
from fastapi import HTTPException


from typing import List, Optional

from passlib.context import CryptContext
from utils.security import get_hash, generate_key,  decrypt_token, encrypt_token
import traceback
from sqlalchemy.exc import IntegrityError


from datetime import datetime, timedelta

from logging import error



# USER
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.Email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Check if the email already exists
    db_user = get_user_by_email(db, user.Email)
    if db_user:
        return None  # Indicate that the user already exists
    secretKey = generate_key("OTP") #forOTP 
    print(secretKey)
    encryptedKey = encrypt_token(secretKey)
    print(encryptedKey)

    new_user = models.User(
        IDORole=user.IDORole,
        Email=user.Email,
        FullName=user.FullName,
        Role=user.Role,
        Phone=user.Phone,
        secret_key = str(encryptedKey)
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except IntegrityError:
        db.rollback()
        return None  # Indicate that an integrity error occurred

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.UserID == user_id).first()

def update_user(db: Session, user_id: str, update_data: schemas.UserUpdate) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.UserID == user_id).first()
    if db_user:
        for key, value in update_data.dict().items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str) -> Optional[models.User]:
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def delete_user(db: Session, user_id: str):
    user = db.query(models.User).filter(models.User.userID == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user


def create_URLToken(db: Session, userid:int): #to maintain security of the setpass URL
    try:
        token_value = generate_key("URL")

        one_day = datetime.now() + timedelta(hours=24)

        new_token = models.URLToken(
            value=token_value,
            UserID=userid,
            exp=one_day
        )

        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        
        # Log the generated token value
        print("Generated token value:", token_value)

        return new_token
    
    except IntegrityError as e:
        db.rollback()
        print("IntegrityError:", e)
        return None  # Indicate that an integrity error occurred
    
    except Exception as e:
        db.rollback()
        print("Error:", e)
        traceback.print_exc()  # Print the full stack trace for debugging
        return None  # Indicate that an error occurred
    

    

def get_user_by_token(db:Session, token:str):

    try:
        decryptedToken = decrypt_token(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token")


    URLtoken = db.query(models.URLToken).filter(models.URLToken.value == decryptedToken).first()

    if URLtoken is None:
        raise HTTPException(status_code=404, detail="Invalid token")
    
    db_user = db.query(models.User).filter(models.User.UserID == URLtoken.UserID).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return db_user


def delete_token(db:Session, token:str):
    try:
        
        decryptedToken = decrypt_token(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token")

    
    URLtoken = db.query(models.URLToken).filter(models.URLToken.value == decryptedToken).first()

    if URLtoken:
        db.delete(URLtoken)
        db.commit()

    else:
        raise HTTPException(status_code=404, detail="Invalid token")


    return URLtoken

# def get_hash(password: str) -> str:
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password.decode('utf-8')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.Email == email).first()
    if user and pwd_context.verify(password, user.hashed_password):
        return user
    return None




def set_user_password(db: Session, Email: str, new_password: str):
    try:
        db_user = db.query(models.User).filter(models.User.Email == Email).first()
        if db_user:
            db_user.hashed_password = get_hash(new_password)
            db_user.is_password_set = True
            db.commit()
            db.refresh(db_user)
            return db_user
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        error(f"Error setting password: {e}")
        raise HTTPException(status_code=422, detail="Error setting password")
    

    
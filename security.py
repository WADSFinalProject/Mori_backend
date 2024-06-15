# app/security.py

from passlib.context import CryptContext
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import pyotp,secrets,ast
from jose import jwt
import os
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

# USER_EMAIL = os.getenv("USER_EMAIL")
# USER_PASSWORD = os.getenv("USER_PASSWORD")

KEY = ast.literal_eval(os.getenv("KEY")) #for encrypting URL tokens

SECRET_KEY = os.getenv("SECRET_KEY") #for JWT 

ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



def generate_key(type):
    if type == "OTP":
        key= pyotp.random_base32()
    elif type =="URL":
        key = secrets.token_urlsafe(32)

    
    return key

from cryptography.fernet import Fernet



# Encrypt a token using the key
def encrypt_token(token):
    cipher_suite = Fernet(KEY)
    encrypted_token = cipher_suite.encrypt(token.encode())
    return encrypted_token

# Decrypt an encrypted token using the key
def decrypt_token(encrypted_token):
    cipher_suite = Fernet(KEY)
    decrypted_token = cipher_suite.decrypt(ast.literal_eval(encrypted_token)).decode()
    return decrypted_token


def generate_otp(secret_key):
    decyptedKey = decrypt_token(secret_key)
    totp = pyotp.TOTP(decyptedKey,interval=120, digits=4)
    print(f"TOTP {totp.now()}")
    return totp.now()



def verify_otp(secret_key, user_otp):
    decryptedToken = decrypt_token(secret_key)
    totp = pyotp.TOTP(decryptedToken,interval=120, digits=4)
    print(f"TOTPNOW:{totp.now()}")
    return totp.verify(user_otp)


def create_access_token(user_id: int, role: str, name:str) -> tuple[str, str]:

    access_token_payload = {
        "sub": user_id,
        "name": name,
        "role": role,
        "exp": datetime.now() + timedelta(minutes=5)
    }
    access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    return access_token

def create_refresh_token(user_id: int, role: str, name:str) -> tuple[str, str,str]:
    
    refresh_token_payload = {
        "sub": user_id,
        "name": name,
        "role": role,
        "exp": datetime.now() + timedelta(hours=12)
    }
    refresh_token = jwt.encode(refresh_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    return refresh_token


def verify_token(token: str):
    try:
        decoded_jwt = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_jwt
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


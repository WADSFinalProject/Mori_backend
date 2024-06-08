# app/security.py

from passlib.context import CryptContext
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import jwt

import secrets


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



def generate_key():

    token = secrets.token_urlsafe(32)
    return token

from cryptography.fernet import Fernet

KEY = b'cssm6qehboYVn3uhLnGQwoN4uVRnex3MFMK-NajYlfM='

# Encrypt a token using the key
def encrypt_token(token):
    cipher_suite = Fernet(KEY)
    encrypted_token = cipher_suite.encrypt(token.encode())
    return encrypted_token

# Decrypt an encrypted token using the key
def decrypt_token(encrypted_token):
    cipher_suite = Fernet(KEY)
    decrypted_token = cipher_suite.decrypt(encrypted_token).decode()
    return decrypted_token



SECRET_KEY = "3ERVV8WvtbAdV0kqoYrF2ABWnVR-9eUnekABwITaQJI0GBNu7BcfuXAnA9I__RAQAKtkUwvhmKPFYs2pNxEGfg" 
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


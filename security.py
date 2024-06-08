# app/security.py

from passlib.context import CryptContext
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
import jwt,pyotp,secrets,ast



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



def generate_otp(secret_key):
    keyBytes = ast.literal_eval(secret_key)
    print(keyBytes)
    decyptedKey = decrypt_token(keyBytes)
    totp = pyotp.TOTP(decyptedKey,interval=120, digits=4)
    return totp.now()

def verify_otp(secret_key, user_otp):
    keyBytes = ast.literal_eval(secret_key)
    totp = pyotp.TOTP(decrypt_token(keyBytes))
    return totp.verify(user_otp)





SECRET_KEY = "3ERVV8WvtbAdV0kqoYrF2ABWnVR-9eUnekABwITaQJI0GBNu7BcfuXAnA9I__RAQAKtkUwvhmKPFYs2pNxEGfg" 
ALGORITHM = "HS256"

def create_access_token(user_id: int, role: str) -> tuple[str, str]:
    access_token_payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    


    return access_token

def create_refresh_token(user_id: int, role: str) -> tuple[str, str]:
    refresh_token_payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    refresh_token = jwt.encode(refresh_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    return refresh_token



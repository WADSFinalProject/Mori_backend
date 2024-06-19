from passlib.context import CryptContext
from cryptography.fernet import Fernet
import pyotp, ast , secrets
from config import KEY



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_key(type: str) -> str:
    if type == "OTP":
        key = pyotp.random_base32()
    elif type == "URL":
        key = secrets.token_urlsafe(32)
    return key

# Encrypt a token using the key
def encrypt_token(token: str) -> str:
    cipher_suite = Fernet(KEY)
    encrypted_token = cipher_suite.encrypt(token.encode())
    return encrypted_token

# Decrypt an encrypted token using the key
def decrypt_token(encrypted_token: str) -> str:
    cipher_suite = Fernet(KEY)
    decrypted_token = cipher_suite.decrypt(ast.literal_eval(encrypted_token)).decode()
    return decrypted_token

def generate_otp(secret_key: str) -> str:
    decrypted_key = decrypt_token(secret_key)
    totp = pyotp.TOTP(decrypted_key, interval=120, digits=4)
    return totp.now()

def verify_otp(secret_key: str, user_otp: str) -> bool:
    decrypted_key = decrypt_token(secret_key)
    totp = pyotp.TOTP(decrypted_key, interval=120, digits=4)
    return totp.verify(user_otp)


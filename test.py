import secrets
from cryptography.fernet import Fernet

# Generate a secure secret key
SECRET_KEY = secrets.token_urlsafe(64)
OTHER = Fernet.generate_key()

print(SECRET_KEY)
print (OTHER)


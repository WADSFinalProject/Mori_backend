import secrets

# Generate a secure secret key
SECRET_KEY = secrets.token_urlsafe(64)

print(SECRET_KEY)
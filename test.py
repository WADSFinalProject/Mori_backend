from cryptography.fernet import Fernet
import pyotp

# Generate a random base32 secret key
secret_key = pyotp.random_base32()

# Encrypt the secret key
cipher_suite = Fernet.generate_key()
cipher = Fernet(cipher_suite)
encrypted_key = cipher.encrypt(secret_key.encode())

# Decrypt the encrypted key
decrypted_key = cipher.decrypt(encrypted_key).decode()

print("Original secret key:", secret_key)
print("Encrypted key:", encrypted_key)
print("Decrypted key:", decrypted_key)

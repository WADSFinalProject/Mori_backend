from dotenv import load_dotenv
import ast, os

load_dotenv()

KEY = os.getenv("KEY") # Ensure this is correctly set in the .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
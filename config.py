from dotenv import load_dotenv
import ast, os

load_dotenv()

KEY = ast.literal_eval(os.getenv("KEY"))  # Ensure this is correctly set in the .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
NEON_URL = os.getenv("NEON_URL")
SESSION_EXPIRY_DAYS = int(os.getenv("SESSION_EXPIRY_DAYS", 3))

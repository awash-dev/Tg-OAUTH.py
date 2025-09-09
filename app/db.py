import psycopg2
from .config import NEON_URL

conn = psycopg2.connect(NEON_URL)
cursor = conn.cursor()

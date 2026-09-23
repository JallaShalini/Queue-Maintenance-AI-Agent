import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/app.db")
TRUST_THRESHOLD = int(os.environ.get("TRUST_THRESHOLD", 3))

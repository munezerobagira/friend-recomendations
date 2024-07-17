import os
from dotenv import load_dotenv
load_dotenv(override=True)

DATABASE_URL=os.getenv("DATABASE_URL")
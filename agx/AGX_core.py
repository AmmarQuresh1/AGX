from dotenv import load_dotenv
import os

load_dotenv()

secret_key = os.getenv("AGX_SECRET_KEY")
print("Loaded key:", secret_key)

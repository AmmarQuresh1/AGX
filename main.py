import os
from dotenv import load_dotenv
from agx.core import run_agx_backend

load_dotenv()

def main():
    print("[AGX] Secure Key Loaded:", os.getenv("AGX_SECRET_KEY"))
    run_agx_backend()

if __name__ == "__main__":
    main()

import os
from dotenv import load_dotenv
from agx.core import agx_main

load_dotenv()

def main():
    print("[AGX] Secure Key Loaded")
    agx_main()

if __name__ == "__main__":
    main()

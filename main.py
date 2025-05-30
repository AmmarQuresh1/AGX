"""
main.py

Entry point for AGX
- Loads environment variables from .env.
- Calls agx_main() to run the backend workflow.
"""
from dotenv import load_dotenv # Loads .env variables into py environment
from agx.core import agx_main # Imports agx_main from core.py

load_dotenv()

def main():
    print("[AGX] Secure Key Loaded")
    agx_main()

# If this file is being run directly, then call the main() function
if __name__ == "__main__":
    main()

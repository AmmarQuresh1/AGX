"""
run.py

The single, official entry point for running the AGX application.
- Sets up the environment.
- Calls the main function from the agx library.
"""
import os
from dotenv import load_dotenv
from agx.core import agx_main # <-- NO leading dot

def run_application():
    """
    Loads environment and executes the main application logic.
    """
    print("Starting AGX application...")
    agx_main()
    print("AGX application finished.")

if __name__ == "__main__":
    # Load .env file from the current directory (your monorepo root)
    load_dotenv()
    run_application()
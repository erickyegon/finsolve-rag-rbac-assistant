"""
Streamlit App Entry Point for Deployment
This file serves as the main entry point for Streamlit deployment.
Uses the existing main.py to run the full application.
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    print("🚀 Starting FinSolve AI Assistant for deployment...")

    # Set environment variables for deployment
    os.environ['DEPLOYMENT_MODE'] = 'streamlit'

    # Run the main application which handles both API and Streamlit
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

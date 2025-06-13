"""
Streamlit App Entry Point for Render Deployment
This file serves as the main entry point for Streamlit deployment on Render.
Uses the existing main.py with streamlit mode.
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Run the main application in streamlit mode
    subprocess.run([sys.executable, "main.py", "--mode", "streamlit"])

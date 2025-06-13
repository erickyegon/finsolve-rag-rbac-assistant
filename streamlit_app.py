"""
Streamlit App Entry Point for Deployment
This file serves as the main entry point for Streamlit deployment.
Starts both FastAPI backend and Streamlit frontend for full functionality.
"""

import subprocess
import sys
import os
import threading
import time
import atexit

# Global process references for cleanup
api_process = None
streamlit_process = None

def cleanup_processes():
    """Clean up background processes on exit"""
    global api_process, streamlit_process
    if api_process:
        try:
            api_process.terminate()
            api_process.wait(timeout=5)
        except:
            pass
    if streamlit_process:
        try:
            streamlit_process.terminate()
            streamlit_process.wait(timeout=5)
        except:
            pass

def start_api_server():
    """Start the FastAPI server in background"""
    global api_process
    try:
        print("🚀 Starting FastAPI backend server...")

        # Set environment variables for API server
        env = os.environ.copy()
        env['API_HOST'] = '0.0.0.0'
        env['API_PORT'] = '8000'

        api_process = subprocess.Popen([
            sys.executable, "main.py", "--mode", "api"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

        # Wait a bit to see if it starts successfully
        time.sleep(5)
        if api_process.poll() is None:
            print("✅ FastAPI server started successfully on port 8000")
        else:
            stdout, stderr = api_process.communicate()
            print(f"❌ FastAPI server failed to start")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")

    except Exception as e:
        print(f"❌ Failed to start FastAPI server: {e}")

def start_streamlit_app():
    """Start the Streamlit app"""
    try:
        print("🎨 Starting Streamlit frontend...")

        # Get port from environment (for deployment) or use default
        port = os.environ.get('PORT', '8501')

        # For Render deployment, use the PORT environment variable
        if os.environ.get('RENDER'):
            port = os.environ.get('PORT', '10000')

        print(f"Starting Streamlit on port {port}")

        # Start Streamlit directly
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/frontend/streamlit_app.py",
            "--server.port", str(port),
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ], check=True)

    except Exception as e:
        print(f"❌ Failed to start Streamlit app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting FinSolve AI Assistant for deployment...")

    # Register cleanup function
    atexit.register(cleanup_processes)

    # Start FastAPI in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    # Give API server time to start
    time.sleep(5)

    # Start Streamlit in main thread (this will block)
    start_streamlit_app()

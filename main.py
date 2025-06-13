"""
Main Application Runner for FinSolve RBAC Chatbot
Production-grade application launcher with comprehensive setup,
health checks, and graceful shutdown handling.

Author: Peter Pandey
Version: 1.0.0
"""

import asyncio
import signal
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

# Configure multiprocessing for Windows
if sys.platform.startswith('win'):
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import after path setup
try:
    import uvicorn
    from loguru import logger
    from src.core.config import settings
    from src.database.connection import init_database, db_manager
    from src.rag.vector_store import vector_store
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class FinSolveApplication:
    """
    Main application orchestrator for FinSolve RBAC Chatbot
    """
    
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.streamlit_process: Optional[subprocess.Popen] = None
        self.shutdown_event = asyncio.Event()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("FinSolve Application initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    async def setup(self):
        """Setup application components"""
        logger.info("Setting up FinSolve RBAC Chatbot...")
        
        try:
            # Initialize database
            logger.info("Initializing database...")
            init_database()
            
            # Check database health
            if not db_manager.health_check():
                raise Exception("Database health check failed")
            
            logger.info("Database initialized successfully")
            
            # Initialize vector store
            logger.info("Checking vector store...")
            stats = vector_store.get_collection_stats()
            
            if not stats or stats.get("total_documents", 0) == 0:
                logger.info("Indexing data sources...")
                success = vector_store.index_data_sources()
                
                if not success:
                    logger.warning("Data indexing failed, but continuing...")
                else:
                    logger.info("Data sources indexed successfully")
            else:
                logger.info(f"Vector store ready with {stats.get('total_documents', 0)} documents")
            
            logger.info("Application setup completed successfully")
            
        except Exception as e:
            logger.error(f"Application setup failed: {str(e)}")
            raise
    
    def start_api_server(self):
        """Start FastAPI server"""
        try:
            logger.info(f"Starting API server on {settings.langserve_host}:{settings.langserve_port}")

            # Prepare environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent)
            env["PYTHONUNBUFFERED"] = "1"

            # Use a startup script approach to avoid import conflicts
            startup_script = f"""
import sys
import os
from pathlib import Path

# Set up path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run
import uvicorn
from src.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="{settings.langserve_host}",
        port={settings.langserve_port},
        log_level="{settings.log_level.lower()}",
        access_log=True
    )
"""

            # Write temporary startup script
            script_path = Path(__file__).parent / "temp_api_start.py"
            with open(script_path, "w") as f:
                f.write(startup_script)

            try:
                self.api_process = subprocess.Popen([
                    sys.executable, str(script_path)
                ], env=env, cwd=Path(__file__).parent)

                # Wait for server to start
                time.sleep(5)

                if self.api_process.poll() is None:
                    logger.info("API server started successfully")
                else:
                    raise Exception("API server failed to start")

            finally:
                # Clean up temporary script
                if script_path.exists():
                    script_path.unlink()

        except Exception as e:
            logger.error(f"Failed to start API server: {str(e)}")
            raise
    
    def start_streamlit_app(self):
        """Start Streamlit application"""
        try:
            logger.info(f"Starting Streamlit app on {settings.streamlit_host}:{settings.streamlit_port}")

            # Check if Streamlit is installed
            try:
                import streamlit
                logger.info(f"Streamlit version: {streamlit.__version__}")
            except ImportError:
                raise Exception("Streamlit is not installed. Please run: pip install streamlit")

            # Prepare environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(Path(__file__).parent)
            env["PYTHONUNBUFFERED"] = "1"

            # Build command
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "src/frontend/streamlit_app.py",
                "--server.address", settings.streamlit_host,
                "--server.port", str(settings.streamlit_port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
                "--server.enableCORS", "false",
                "--server.enableXsrfProtection", "false"
            ]

            logger.info(f"Streamlit command: {' '.join(cmd)}")

            self.streamlit_process = subprocess.Popen(
                cmd,
                env=env,
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform.startswith('win') else 0
            )

            # Wait for app to start and check for errors
            time.sleep(8)

            if self.streamlit_process.poll() is None:
                logger.info("Streamlit app started successfully")
                logger.info(f"🎨 Streamlit App: http://{settings.streamlit_host}:{settings.streamlit_port}")
            else:
                # Process has terminated, get error output
                stdout, stderr = self.streamlit_process.communicate()
                error_msg = f"Streamlit process terminated. STDOUT: {stdout.decode()}, STDERR: {stderr.decode()}"
                logger.error(error_msg)
                raise Exception(f"Streamlit app failed to start: {error_msg}")

        except Exception as e:
            logger.error(f"Failed to start Streamlit app: {str(e)}")
            raise
    
    async def run(self):
        """Run the complete application"""
        try:
            # Setup
            await self.setup()
            
            # Start services
            self.start_api_server()
            self.start_streamlit_app()
            
            # Display startup information
            self.display_startup_info()
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            raise
        finally:
            await self.shutdown()
    
    def display_startup_info(self):
        """Display startup information"""
        logger.info("=" * 70)
        logger.info("🚀 FinSolve Technologies AI Assistant - Synapse Active!")
        logger.info("   Connected Intelligence • Seamless Data Flow • Innovation")
        logger.info("=" * 70)
        logger.info(f"📊 API Server: {settings.api_url}")
        logger.info(f"🎨 Streamlit App: {settings.streamlit_url}")
        logger.info(f"📚 API Documentation: {settings.docs_url}")
        logger.info(f"🔧 LangServe Playground: {settings.langserve_playground_url}")
        logger.info("=" * 60)
        logger.info("Demo Credentials:")
        logger.info("  🏢 Executive Team:")
        logger.info("    CEO: ceo.finsolve / CEO123!")
        logger.info("    CFO: cfo.finsolve / CFO123!")
        logger.info("    CTO: cto.finsolve / CTO123!")
        logger.info("    CHRO: chro.finsolve / CHRO123!")
        logger.info("    VP Marketing: vp.marketing / Marketing123!")
        logger.info("  👥 Department Heads:")
        logger.info("    Admin: admin / Admin123!")
        logger.info("    HR: jane.smith / HRpass123!")
        logger.info("    Finance: mike.johnson / Finance123!")
        logger.info("    Marketing: sarah.wilson / Marketing123!")
        logger.info("    Engineering: peter.pandey / Engineering123!")
        logger.info("  👤 Employee: john.doe / Employee123!")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop the application")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down FinSolve RBAC Chatbot...")
        
        # Stop Streamlit process
        if self.streamlit_process and self.streamlit_process.poll() is None:
            logger.info("Stopping Streamlit app...")
            self.streamlit_process.terminate()
            try:
                self.streamlit_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
        
        # Stop API process
        if self.api_process and self.api_process.poll() is None:
            logger.info("Stopping API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
        
        # Close database connections
        logger.info("Closing database connections...")
        db_manager.close()
        
        logger.info("Shutdown completed")
        self.shutdown_event.set()


def run_api_only():
    """Run only the API server"""
    logger.info("Starting API server only...")

    try:
        # Initialize database
        init_database()

        # Initialize vector store if needed
        stats = vector_store.get_collection_stats()
        if not stats or stats.get("total_documents", 0) == 0:
            logger.info("Indexing data sources...")
            vector_store.index_data_sources()

        # Import app after initialization
        from src.api.main import app

        # Run API server directly
        uvicorn.run(
            app,
            host=settings.langserve_host,
            port=settings.langserve_port,
            log_level=settings.log_level.lower(),
            access_log=True
        )

    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        sys.exit(1)


def run_streamlit_only():
    """Run only the Streamlit app"""
    logger.info("Starting Streamlit app only...")
    
    try:
        os.system(f"""
        streamlit run src/frontend/streamlit_app.py \
        --server.address {settings.streamlit_host} \
        --server.port {settings.streamlit_port} \
        --server.headless true \
        --browser.gatherUsageStats false
        """)
        
    except Exception as e:
        logger.error(f"Failed to start Streamlit app: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FinSolve RBAC Chatbot")
    parser.add_argument(
        "--mode",
        choices=["full", "api", "streamlit"],
        default="full",
        help="Run mode: full (both), api (API only), or streamlit (Streamlit only)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "api":
        run_api_only()
    elif args.mode == "streamlit":
        run_streamlit_only()
    else:
        # Run full application
        app = FinSolveApplication()
        asyncio.run(app.run())


if __name__ == "__main__":
    # Ensure proper multiprocessing on Windows
    if sys.platform.startswith('win'):
        multiprocessing.freeze_support()

    main()

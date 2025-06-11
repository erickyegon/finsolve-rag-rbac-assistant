#!/bin/bash
# FinSolve AI Assistant - Production Start Script
# Author: Dr. Erick K. Yegon

set -e

echo "🚀 Starting FinSolve AI Assistant..."

# Check if running in production mode
if [ "$ENVIRONMENT" = "production" ]; then
    echo "📊 Production mode detected"
    
    # Wait for database to be ready
    echo "⏳ Waiting for database connection..."
    python -c "
import time
import psycopg2
import os
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL')
if db_url:
    parsed = urlparse(db_url)
    for i in range(30):
        try:
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:]
            )
            conn.close()
            print('✅ Database connection successful')
            break
        except Exception as e:
            print(f'⏳ Waiting for database... ({i+1}/30)')
            time.sleep(2)
    else:
        print('❌ Database connection failed after 30 attempts')
        exit(1)
"

    # Wait for Redis to be ready
    echo "⏳ Waiting for Redis connection..."
    python -c "
import time
import redis
import os
from urllib.parse import urlparse

redis_url = os.getenv('REDIS_URL')
if redis_url:
    parsed = urlparse(redis_url)
    for i in range(30):
        try:
            r = redis.Redis(host=parsed.hostname, port=parsed.port, decode_responses=True)
            r.ping()
            print('✅ Redis connection successful')
            break
        except Exception as e:
            print(f'⏳ Waiting for Redis... ({i+1}/30)')
            time.sleep(2)
    else:
        print('❌ Redis connection failed after 30 attempts')
        exit(1)
"

    # Run database migrations
    echo "🔄 Running database migrations..."
    python -c "
from src.database.connection import init_database
init_database()
print('✅ Database initialized')
"

    # Initialize vector database
    echo "🔄 Initializing vector database..."
    python -c "
from src.rag.vector_store import initialize_vector_store
initialize_vector_store()
print('✅ Vector database initialized')
"

else
    echo "🔧 Development mode detected"
fi

# Create log directory
mkdir -p /app/logs

# Function to handle shutdown
shutdown() {
    echo "🛑 Shutting down FinSolve AI Assistant..."
    kill -TERM "$fastapi_pid" "$streamlit_pid" 2>/dev/null || true
    wait "$fastapi_pid" "$streamlit_pid" 2>/dev/null || true
    echo "✅ Shutdown complete"
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Start FastAPI backend
echo "🔧 Starting FastAPI backend on port 8000..."
uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info \
    --access-log \
    --log-config logging.conf 2>&1 | tee /app/logs/fastapi.log &
fastapi_pid=$!

# Wait a moment for FastAPI to start
sleep 5

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend on port 8501..."
streamlit run src/frontend/streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --logger.level info 2>&1 | tee /app/logs/streamlit.log &
streamlit_pid=$!

echo "✅ FinSolve AI Assistant started successfully!"
echo "📊 FastAPI: http://localhost:8000"
echo "🎨 Streamlit: http://localhost:8501"
echo "📋 Health Check: http://localhost:8000/health"

# Wait for both processes
wait "$fastapi_pid" "$streamlit_pid"

#!/bin/bash

# FinSolve RBAC Chatbot Setup Script
# Production-grade setup with comprehensive environment preparation

set -e  # Exit on any error

echo "🚀 Setting up FinSolve RBAC Chatbot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Environment file created from template"
            print_warning "Please edit .env file with your configuration"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_warning ".env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p chroma_db
    mkdir -p data
    
    print_success "Directories created"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    $PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from src.database.connection import init_database
try:
    init_database()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization failed: {e}')
    sys.exit(1)
"
    
    print_success "Database initialized"
}

# Index data sources
index_data() {
    print_status "Indexing data sources..."
    
    $PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from src.rag.vector_store import vector_store
try:
    success = vector_store.index_data_sources()
    if success:
        print('Data sources indexed successfully')
    else:
        print('Data indexing failed')
        sys.exit(1)
except Exception as e:
    print(f'Data indexing error: {e}')
    sys.exit(1)
"
    
    print_success "Data sources indexed"
}

# Run health check
health_check() {
    print_status "Running health check..."
    
    $PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from src.database.connection import db_manager
from src.rag.vector_store import vector_store

try:
    # Check database
    db_healthy = db_manager.health_check()
    print(f'Database health: {'OK' if db_healthy else 'FAILED'}')
    
    # Check vector store
    stats = vector_store.get_collection_stats()
    print(f'Vector store: {stats.get('total_documents', 0)} documents indexed')
    
    if db_healthy and stats:
        print('Health check passed')
    else:
        print('Health check failed')
        sys.exit(1)
        
except Exception as e:
    print(f'Health check error: {e}')
    sys.exit(1)
"
    
    print_success "Health check passed"
}

# Display completion message
display_completion() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Run the application:"
    echo "   python main.py"
    echo ""
    echo "Application URLs:"
    echo "- Streamlit UI: http://localhost:8501"
    echo "- API Server: http://localhost:8000"
    echo "- API Docs: http://localhost:8000/docs"
    echo ""
    echo "Demo credentials:"
    echo "- Admin: admin / Admin123!"
    echo "- Employee: john.doe / Employee123!"
    echo "- HR: jane.smith / HR123!"
    echo "- Finance: mike.johnson / Finance123!"
    echo "- Marketing: sarah.wilson / Marketing123!"
    echo "- Engineering: peter.pandey / Engineering123!"
    echo ""
}

# Main setup process
main() {
    echo "🚀 FinSolve RBAC Chatbot Setup"
    echo "================================"
    
    check_python
    create_venv
    activate_venv
    install_dependencies
    setup_env
    create_directories
    init_database
    index_data
    health_check
    display_completion
}

# Run main function
main "$@"

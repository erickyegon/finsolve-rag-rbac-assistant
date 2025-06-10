#!/bin/bash

# FinSolve RBAC Chatbot Run Script
# Production-grade application runner with health checks and monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if virtual environment exists and activate it
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_success "Virtual environment activated"
    else
        print_warning "Virtual environment not found, using system Python"
    fi
}

# Pre-flight checks
preflight_checks() {
    print_status "Running pre-flight checks..."
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Run setup.sh first."
        exit 1
    fi
    
    # Check if requirements are installed
    python -c "import fastapi, streamlit, langchain, langgraph" 2>/dev/null || {
        print_error "Dependencies not installed. Run setup.sh first."
        exit 1
    }
    
    print_success "Pre-flight checks passed"
}

# Run application
run_app() {
    local mode=${1:-"full"}
    
    print_status "Starting FinSolve RBAC Chatbot in $mode mode..."
    
    case $mode in
        "full")
            python main.py --mode full
            ;;
        "api")
            python main.py --mode api
            ;;
        "streamlit")
            python main.py --mode streamlit
            ;;
        *)
            print_error "Invalid mode: $mode. Use 'full', 'api', or 'streamlit'"
            exit 1
            ;;
    esac
}

# Display help
show_help() {
    echo "FinSolve RBAC Chatbot Runner"
    echo ""
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  full       Run both API server and Streamlit app (default)"
    echo "  api        Run only the API server"
    echo "  streamlit  Run only the Streamlit app"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Run full application"
    echo "  $0 full         # Run full application"
    echo "  $0 api          # Run API server only"
    echo "  $0 streamlit    # Run Streamlit app only"
    echo ""
}

# Main function
main() {
    local mode=${1:-"full"}
    
    if [ "$mode" = "help" ] || [ "$mode" = "-h" ] || [ "$mode" = "--help" ]; then
        show_help
        exit 0
    fi
    
    echo "🚀 FinSolve RBAC Chatbot"
    echo "========================"
    
    activate_venv
    preflight_checks
    run_app "$mode"
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}[INFO]${NC} Shutting down..."; exit 0' INT

# Run main function
main "$@"

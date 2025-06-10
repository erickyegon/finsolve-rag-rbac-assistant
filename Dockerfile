# FinSolve RBAC Chatbot Dockerfile
# Production-grade containerization with multi-stage build

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r finsolve && useradd -r -g finsolve finsolve

# Create application directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs chroma_db && \
    chown -R finsolve:finsolve /app

# Switch to non-root user
USER finsolve

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "main.py", "--mode", "full"]

# Labels
LABEL maintainer="Peter Pandey <peter.pandey@finsolve.com>" \
      version="1.0.0" \
      description="FinSolve RBAC Chatbot - Production-grade AI assistant" \
      org.opencontainers.image.title="FinSolve RBAC Chatbot" \
      org.opencontainers.image.description="Production-grade RBAC chatbot with hybrid MCP + RAG approach" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Peter Pandey" \
      org.opencontainers.image.vendor="FinSolve Technologies" \
      org.opencontainers.image.licenses="MIT"

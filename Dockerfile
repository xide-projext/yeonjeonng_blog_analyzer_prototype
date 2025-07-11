# Multi-stage build for production optimization
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[production]"

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Command for development
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Create non-root user
RUN groupadd -r blogapp && useradd -r -g blogapp -s /bin/false blogapp

# Copy source code
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# Change ownership
RUN chown -R blogapp:blogapp /app

# Switch to non-root user
USER blogapp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command for production
CMD ["gunicorn", "backend.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"] 
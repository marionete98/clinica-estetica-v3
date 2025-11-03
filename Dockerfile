FROM python:3.13.1-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip to latest version for Python 3.13 compatibility
RUN pip install --upgrade pip setuptools wheel

# Build arg to bust cache when dependencies change
ARG CACHEBUST=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations for Python 3.13
RUN pip install --no-cache-dir --compile -r requirements.txt

# Copy application code
COPY . .

# Copy start script and make it executable (before changing user)
COPY start.sh .
RUN chmod +x start.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/healthcheck.py

# Run with start script (Railway will set PORT automatically)
CMD ["./start.sh"]

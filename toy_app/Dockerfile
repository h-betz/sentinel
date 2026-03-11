FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into toy_app/ so imports like
# `from toy_app.app...` resolve correctly
COPY . toy_app/

# Make toy_app/ importable and set working dir for entrypoint
ENV PYTHONPATH=/workspace
WORKDIR /workspace/toy_app

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Run migrations and start the application
ENTRYPOINT ["./entrypoint.sh"]

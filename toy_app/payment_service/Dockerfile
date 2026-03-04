FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard]

# Copy application
COPY main.py .

# Expose port
EXPOSE 8001

# Health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

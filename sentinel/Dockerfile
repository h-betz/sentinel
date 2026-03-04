FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sentinel agent code
COPY . .

# Run the orchestrator
CMD ["python", "-m", "orchestrator"]

FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies (git + GitHub CLI)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
       | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sentinel agent code into sentinel/ so imports like
# `from sentinel.agents...` resolve correctly
COPY . sentinel/

# Make sentinel/ importable
ENV PYTHONPATH=/workspace

# Run the orchestrator
CMD ["python", "-m", "sentinel.orchestrator"]

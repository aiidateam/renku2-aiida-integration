#!/bin/bash

# Simple script to test MCA integration locally

set -e

# Default values
DEFAULT_PORT=8888
ARCHIVE_URL="https://archive.materialscloud.org/records/yf0rj-w3r97/files/acwf-verification_unaries-verification-PBE-v1_results_gpaw.aiida"

# Parse arguments
PORT=${1:-$DEFAULT_PORT}
if [ -n "$2" ]; then
    ARCHIVE_URL="$2"
fi

# Validate port is numeric
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1000 ] || [ "$PORT" -gt 65535 ]; then
    echo "Error: Port must be a number between 1000-65535"
    echo "Usage: $0 [PORT] [ARCHIVE_URL]"
    exit 1
fi

# Check if port is available
if command -v netstat >/dev/null 2>&1; then
    if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo "Warning: Port $PORT appears to be in use"
        echo "You might want to try a different port"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Try: $0 8889  # or another port"
            exit 1
        fi
    fi
fi

echo "Building Docker image..."
docker buildx build -t mca-test .docker/

echo ""
echo "Configuration:"
echo "  Port: $PORT"
echo "  Archive URL: $ARCHIVE_URL"
echo ""
echo "Jupyter will be available at: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

# Run the container - simplified approach without user switching
docker run -it --rm \
  --name "mca-test-$PORT" \
  -p "$PORT:8888" \
  -v "$(pwd):/home/jovyan/work" \
  -e "archive_url=$ARCHIVE_URL" \
  -e "RENKU_USERNAME=$USER" \
  -e "HOME=/home/jovyan" \
  --workdir /home/jovyan/work \
  mca-test \
  bash -c "
    # Run initialization and start Jupyter (disable auth properly)
    bash post-init.sh &&
    jupyter server \
      --ServerApp.ip=0.0.0.0 \
      --ServerApp.port=8888 \
      --ServerApp.token='' \
      --ServerApp.password='' \
      --ServerApp.disable_check_xsrf=True \
      --ServerApp.allow_remote_access=True \
      --ServerApp.allow_root=True \
      --ServerApp.allow_origin='*' \
      --ContentsManager.allow_hidden=True \
      --IdentityProvider.token=''
  "

#!/bin/bash
# Production start script for GymGenius AI Backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default values
export PORT=${PORT:-8000}
export HOST=${HOST:-0.0.0.0}
export ENVIRONMENT=${ENVIRONMENT:-production}

# Start the server
exec uvicorn main:app --host "$HOST" --port "$PORT"


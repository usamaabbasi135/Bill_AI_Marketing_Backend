#!/bin/bash
# Startup script for Render deployment
# Runs database migrations before starting the server

set -e

echo "Running database migrations..."
# FLASK_APP should be set in environment variables, but set it here as fallback
export FLASK_APP=${FLASK_APP:-wsgi.py}
flask db upgrade || echo "Migration warning: continuing anyway..."

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT wsgi:app


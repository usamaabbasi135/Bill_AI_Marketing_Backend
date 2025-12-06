#!/bin/bash
# Startup script for Render deployment
# Runs database migrations before starting the server (as backup if build-time migrations failed)

set -e

echo "Running database migrations (startup backup)..."
python run_migrations.py || echo "Warning: Migrations may have already run during build"

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT wsgi:app


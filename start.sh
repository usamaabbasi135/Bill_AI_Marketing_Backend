#!/bin/bash
# Startup script for Render deployment
# Runs database migrations before starting the server

set -e

echo "Running database migrations..."
python run_migrations.py

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT wsgi:app


#!/usr/bin/env python
"""
Script to run database migrations before starting the server.
This ensures migrations run with proper Flask app context.
"""
import sys
import os
from app import create_app
from flask_migrate import upgrade
from flask import current_app

def main():
    """Run database migrations."""
    print("=" * 50)
    print("Starting database migration process...")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set!")
        sys.exit(1)
    print(f"Database URL configured: {db_url[:20]}...")
    
    # Create app and run migrations
    app = create_app()
    
    with app.app_context():
        print("Flask app context created")
        print("Running database migrations...")
        try:
            upgrade()
            print("=" * 50)
            print("✓ Migrations completed successfully!")
            print("=" * 50)
        except Exception as e:
            print("=" * 50)
            print(f"✗ Migration error: {e}")
            print("=" * 50)
            import traceback
            traceback.print_exc()
            # Exit with error so we know migrations failed
            sys.exit(1)

if __name__ == "__main__":
    main()


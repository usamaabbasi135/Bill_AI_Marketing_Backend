from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Development
    app.run(debug=True, port=5000)
else:
    # Production (Gunicorn)
    pass
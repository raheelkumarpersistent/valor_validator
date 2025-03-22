# debug_db.py
from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if we can connect to the database
    try:
        # Updated for SQLAlchemy 2.x
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        
    # Check if tables exist
    try:
        from models.rule import Rule
        # Updated for SQLAlchemy 2.x
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        print(f"Tables in database: {inspector.get_table_names()}")
        print(f"Rule table exists: {'rules' in inspector.get_table_names()}")
    except Exception as e:
        print(f"Error checking Rule table: {e}")
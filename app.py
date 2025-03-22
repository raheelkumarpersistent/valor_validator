# app.py
from flask import Flask
import os
from config import config
from extensions import db, migrate

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from controllers.main import main_bp
    from controllers.rules import rules_bp
    from controllers.validation import validation_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(rules_bp, url_prefix='/rules')
    app.register_blueprint(validation_bp, url_prefix='/validation')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Import models here to avoid circular imports
        from models.rule import Rule
        
        # Check if we need to seed the database
        if not Rule.query.first():
            from services.seed import seed_default_rules
            seed_default_rules()
    
    return app

if __name__ == '__main__':
    app = create_app()

     # Print all registered routes
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule}")

        
    app.run(debug=True)
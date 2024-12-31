from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top10.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register template filters
    @app.template_filter('slice')
    def slice_filter(iterable, slc):
        return list(iterable)[:slc]
    
    # Import and register blueprints/routes
    from .app import main
    app.register_blueprint(main)
    
    return app

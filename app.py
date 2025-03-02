import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
from extensions import db, login_manager

# Load environment variables from .env file if it exists
load_dotenv()

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize extensions
# db = SQLAlchemy(model_class=Base)
# login_manager = LoginManager()

# create the app
app = Flask(__name__)
# setup a secret key, required by sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure the database
# If DATABASE_URL is set, use it (for MySQL); otherwise, fall back to SQLite
if os.environ.get("DATABASE_URL"):
    # print(os.environ.get("DATABASE_URL"))
    # For MySQL, the URL format should be: mysql://username:password@host:port/database_name
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
else:
    # SQLite fallback for local development
    # app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///app.db'
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    print("Database not connected ")
    exit()

# initialize the app with the extension
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Register blueprints
with app.app_context():
    # Import the models here
    import models
    from auth import bp as auth_bp

    app.register_blueprint(auth_bp)
    from timetable import timetable_bp as timetable_bp
    app.register_blueprint(timetable_bp, url_prefix='/timetable')

    # Create database tables
    db.create_all()

    # Initialize test data if needed
    try:
        if not models.UserCredentials.query.filter_by(email='admin@example.com').first():
            logger.info("Creating test users and data")
            models.create_test_data()
        else:
            logger.info("Test data already exists")
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        raise
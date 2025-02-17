from app import app
from extensions import db
from models import UserCredentials
from werkzeug.security import generate_password_hash

with app.app_context():  # Ensure we are inside the Flask application context
    # Check if an admin user already exists
    admin = UserCredentials.query.filter_by(email="admin@example.com").first()

    if not admin:
        # Create an admin user
        admin = UserCredentials(
            email="admin@example.com",
            role="admin",
            is_active=True
        )
        admin.set_password("Admin@123")  # Set hashed password

        # Add to database
        db.session.add(admin)
        db.session.commit()

        print("✅ Admin user created successfully!")
    else:
        print("⚠️ Admin user already exists.")

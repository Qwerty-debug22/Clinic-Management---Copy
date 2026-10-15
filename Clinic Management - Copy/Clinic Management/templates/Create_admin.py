import os
from Clinic_Management import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Ensure database tables exist
    db.create_all()
    
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        # Reset password for existing admin
        admin.password_hash = generate_password_hash('admin123')
        admin.role = 'Admin'
        print("Existing 'admin' account password reset to: admin123")
    else:
        # Create new admin user
        new_admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='Admin'
        )
        db.session.add(new_admin)
        print("Created new 'admin' account with password: admin123")
        
    db.session.commit()
    print("Done! You can now log in.")

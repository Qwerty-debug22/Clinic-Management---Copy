from Clinic_Management import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Make sure tables exist
    db.create_all()

    # Look for existing admin
    admin = User.query.filter_by(username='admin').first()

    if admin:
        admin.password_hash = generate_password_hash('admin123')
        admin.role = 'Admin'
        print("Success: 'admin' user password reset to 'admin123'!")
    else:
        new_admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='Admin'
        )
        db.session.add(new_admin)
        print("Success: Created new 'admin' user with password 'admin123'!")

    db.session.commit()

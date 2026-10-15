Python
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/consultation/new/<int:appointment_id>', methods=['GET', 'POST'])
def new_consultation(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if request.method == 'POST':
        consultation = Consultation(
            appointment_id=appointment.appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            consultation_date=request.form.get('consultation_date'),
            chief_complaint=request.form.get('chief_complaint'),
            clinical_notes=request.form.get('clinical_notes'),
            assessment=request.form.get('assessment'),
            diagnosis=request.form.get('diagnosis'),
            treatment_plan=request.form.get('treatment_plan'),
            doctor_remarks=request.form.get('doctor_remarks')
        )
        
        # Mark appointment as Completed
        appointment.status = 'Completed'
        
        db.session.add(consultation)
        db.session.commit()
        flash('Consultation record successfully saved!', 'success')
        return redirect(url_for('view_consultation', appointment_id=appointment.appointment_id))

    today_str = datetime.now().strftime("%B %d, %Y")
    return render_template('consultation_form.html', appointment=appointment, today_str=today_str)


@app.route('/consultation/view/<int:appointment_id>')
def view_consultation(appointment_id):
    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first_or_404()
    return render_template('consultation_view.html', consultation=consultation)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'st-jude-clinic-secret-key-2026'

# Database Setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'clinic.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# DATABASE MODELS
# -----------------------------------------------------------------------------

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Admin, Doctor, Patient

class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.String(20), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    doctor_id = db.Column(db.Integer, primary_key=True)
    doctor_code = db.Column(db.String(20), unique=True, nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    appointment_date = db.Column(db.String(20), nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Scheduled')

    patient = db.relationship('Patient', backref='appointments')
    doctor = db.relationship('Doctor', backref='appointments')

class Consultation(db.Model):
    __tablename__ = 'consultations'
    consultation_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    consultation_date = db.Column(db.String(20), nullable=False)
    chief_complaint = db.Column(db.Text, nullable=False)
    clinical_notes = db.Column(db.Text, nullable=True)
    assessment = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment_plan = db.Column(db.Text, nullable=False)
    doctor_remarks = db.Column(db.Text, nullable=True)

    appointment = db.relationship('Appointment', backref='consultation', uselist=False)
    patient = db.relationship('Patient', backref='consultations')
    doctor = db.relationship('Doctor', backref='consultations')

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def generate_next_patient_code():
    last_patient = Patient.query.order_by(Patient.patient_id.desc()).first()
    if not last_patient:
        return "P-0001"
    next_id = last_patient.patient_id + 1
    return f"P-{next_id:04d}"

def generate_next_doctor_code():
    last_doctor = Doctor.query.order_by(Doctor.doctor_id.desc()).first()
    if not last_doctor:
        return "D001"
    next_id = last_doctor.doctor_id + 1
    return f"D{next_id:03d}"

# -----------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# -----------------------------------------------------------------------------

@app.route('/')
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'Admin':
            return redirect(url_for('dashboard_admin'))
        elif role == 'Doctor':
            return redirect(url_for('dashboard_doctor'))
        elif role == 'Patient':
            return redirect(url_for('dashboard_patient'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_input = request.form.get('username', '').strip()
        password_input = request.form.get('password', '').strip()
        
        user = User.query.filter(User.username.ilike(username_input)).first()
        
        if user and check_password_hash(user.password_hash, password_input):
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role'] = user.role
            flash('Successfully logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'Patient')

        if role == 'Admin':
            flash('Admin account registration is restricted.', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter(User.username.ilike(username)).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'warning')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password_hash=hashed_password,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# -----------------------------------------------------------------------------
# DASHBOARD ROUTES
# -----------------------------------------------------------------------------

@app.route('/dashboard/admin')
def dashboard_admin():
    if session.get('role') != 'Admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    search_query = request.args.get('search', '').strip()
    if search_query:
        patients = Patient.query.filter(
            (Patient.patient_code.ilike(f"%{search_query}%")) |
            (Patient.first_name.ilike(f"%{search_query}%")) |
            (Patient.last_name.ilike(f"%{search_query}%"))
        ).all()
    else:
        patients = Patient.query.all()

    appointments = Appointment.query.order_by(Appointment.appointment_id.desc()).all()
    default_code = generate_next_patient_code()

    return render_template(
        'dashboard_admin.html',
        patients=patients,
        appointments=appointments,
        default_code=default_code,
        search_query=search_query
    )

@app.route('/dashboard/doctor')
def dashboard_doctor():
    if session.get('role') != 'Doctor':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    appointments = Appointment.query.order_by(Appointment.appointment_id.desc()).all()
    return render_template('dashboard_doctor.html', appointments=appointments)

@app.route('/dashboard/patient')
def dashboard_patient():
    if session.get('role') != 'Patient':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    return render_template('dashboard_patient.html')

# -----------------------------------------------------------------------------
# PATIENT MANAGEMENT ROUTES
# -----------------------------------------------------------------------------

@app.route('/patient/add', methods=['POST'])
def add_patient():
    if session.get('role') != 'Admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    patient_code = generate_next_patient_code()
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    birth_date = request.form.get('birth_date')
    sex = request.form.get('sex')
    contact_number = request.form.get('contact_number')
    address = request.form.get('address')

    new_patient = Patient(
        patient_code=patient_code,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        sex=sex,
        contact_number=contact_number,
        address=address,
        is_active=True
    )
    db.session.add(new_patient)
    db.session.commit()

    flash(f'Patient {patient_code} created successfully!', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/patient/edit/<int:patient_id>', methods=['POST'])
def edit_patient(patient_id):
    if session.get('role') != 'Admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(patient_id)
    patient.first_name = request.form.get('first_name')
    patient.last_name = request.form.get('last_name')
    patient.birth_date = request.form.get('birth_date')
    patient.sex = request.form.get('sex')
    patient.contact_number = request.form.get('contact_number')
    patient.address = request.form.get('address')

    db.session.commit()
    flash(f'Patient {patient.patient_code} updated successfully!', 'success')
    return redirect(url_for('dashboard_admin'))

@app.route('/patient/toggle_status/<int:patient_id>')
def toggle_patient_status(patient_id):
    if session.get('role') != 'Admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = not patient.is_active
    db.session.commit()

    status_str = "activated" if patient.is_active else "deactivated"
    flash(f'Patient {patient.patient_code} has been {status_str}.', 'info')
    return redirect(url_for('dashboard_admin'))

@app.route('/patient/profile/<int:patient_id>')
def patient_profile(patient_id):
    if 'user_id' not in session:
        flash('Please login to view patient profiles.', 'warning')
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(patient_id)
    return render_template('patient_profile.html', patient=patient)

# -----------------------------------------------------------------------------
# LABORATORY ACTIVITY 5: DOCTOR MANAGEMENT
# -----------------------------------------------------------------------------

@app.route('/doctors')
def doctor_management():
    if session.get('role') != 'Admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    search_query = request.args.get('search', '').strip()
    if search_query:
        doctors = Doctor.query.filter(
            (Doctor.doctor_code.ilike(f"%{search_query}%")) |
            (Doctor.doctor_name.ilike(f"%{search_query}%")) |
            (Doctor.specialization.ilike(f"%{search_query}%"))
        ).all()
    else:
        doctors = Doctor.query.all()

    default_doctor_code = generate_next_doctor_code()
    return render_template(
        'doctors.html',
        doctors=doctors,
        default_code=default_doctor_code,
        search_query=search_query
    )

@app.route('/doctor/add', methods=['POST'])
def add_doctor():
    if session.get('role') != 'Admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    doctor_code = request.form.get('doctor_code', '').strip()
    if not doctor_code:
        doctor_code = generate_next_doctor_code()

    doctor_name = request.form.get('doctor_name')
    specialization = request.form.get('specialization')
    contact_number = request.form.get('contact_number')

    new_doctor = Doctor(
        doctor_code=doctor_code,
        doctor_name=doctor_name,
        specialization=specialization,
        contact_number=contact_number,
        is_active=True
    )
    db.session.add(new_doctor)
    db.session.commit()

    flash(f'Doctor {doctor_name} ({doctor_code}) saved successfully!', 'success')
    return redirect(url_for('doctor_management'))

@app.route('/doctor/edit/<int:doctor_id>', methods=['POST'])
def edit_doctor(doctor_id):
    if session.get('role') != 'Admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.doctor_name = request.form.get('doctor_name')
    doctor.specialization = request.form.get('specialization')
    doctor.contact_number = request.form.get('contact_number')

    db.session.commit()
    flash(f'Doctor {doctor.doctor_name} updated successfully!', 'success')
    return redirect(url_for('doctor_management'))

@app.route('/doctor/view/<int:doctor_id>')
def view_doctor(doctor_id):
    if 'user_id' not in session:
        flash('Please login to view doctor details.', 'warning')
        return redirect(url_for('login'))

    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('doctor_profile.html', doctor=doctor)

@app.route('/doctor/toggle_status/<int:doctor_id>')
def toggle_doctor_status(doctor_id):
    if session.get('role') != 'Admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('login'))

    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_active = not doctor.is_active
    db.session.commit()

    status_str = "activated" if doctor.is_active else "deactivated"
    flash(f'Doctor {doctor.doctor_name} has been {status_str}.', 'info')
    return redirect(url_for('doctor_management'))

# -----------------------------------------------------------------------------
# LABORATORY ACTIVITY 6: APPOINTMENT SCHEDULING
# -----------------------------------------------------------------------------

@app.route('/appointments/schedule', methods=['GET', 'POST'])
def schedule_appointment():
    if 'user_id' not in session:
        flash('Please login to access appointment scheduling.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason', '').strip()

        if not patient_id:
            flash("Error: Please select a patient.", "danger")
            return redirect(url_for('schedule_appointment'))

        if not doctor_id:
            flash("Error: Please select a doctor.", "danger")
            return redirect(url_for('schedule_appointment'))

        try:
            selected_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            if selected_date < datetime.now().date():
                flash("Error: Invalid date. Appointment date cannot be in the past.", "danger")
                return redirect(url_for('schedule_appointment'))
        except (ValueError, TypeError):
            flash("Error: Invalid date format selected.", "danger")
            return redirect(url_for('schedule_appointment'))

        try:
            selected_time = datetime.strptime(appointment_time, '%H:%M').time()
            start_time = datetime.strptime('08:00', '%H:%M').time()
            end_time = datetime.strptime('17:00', '%H:%M').time()

            if selected_time < start_time or selected_time > end_time:
                flash("Error: Appointment outside clinic hours (08:00 AM - 05:00 PM).", "danger")
                return redirect(url_for('schedule_appointment'))
        except (ValueError, TypeError):
            flash("Error: Invalid time format selected.", "danger")
            return redirect(url_for('schedule_appointment'))

        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        ).filter(Appointment.status != 'Cancelled').first()

        if existing:
            flash("Error: Duplicate doctor/time booking. Doctor is already booked at this time slot.", "danger")
            return redirect(url_for('schedule_appointment'))

        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status='Scheduled'
        )
        db.session.add(new_appointment)
        db.session.commit()

        flash("Appointment scheduled successfully!", "success")
        return redirect(url_for('schedule_appointment'))

    patients = Patient.query.filter_by(is_active=True).all()
    doctors = Doctor.query.filter_by(is_active=True).all()
    appointments = Appointment.query.order_by(Appointment.appointment_id.desc()).all()

    return render_template('schedule_appointment.html', patients=patients, doctors=doctors, appointments=appointments)

# -----------------------------------------------------------------------------
# LABORATORY ACTIVITY 8: CONSULTATION MANAGEMENT
# -----------------------------------------------------------------------------

@app.route('/consultation/new/<int:appointment_id>', methods=['GET', 'POST'])
def new_consultation(appointment_id):
    if 'user_id' not in session or session.get('role') not in ['Admin', 'Doctor']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    appointment = Appointment.query.get_or_404(appointment_id)

    # If already conducted, redirect directly to consultation view
    existing_consultation = Consultation.query.filter_by(appointment_id=appointment_id).first()
    if existing_consultation:
        return redirect(url_for('view_consultation', appointment_id=appointment_id))

    if request.method == 'POST':
        consultation_date = request.form.get('consultation_date')
        chief_complaint = request.form.get('chief_complaint', '').strip()
        clinical_notes = request.form.get('clinical_notes', '').strip()
        assessment = request.form.get('assessment', '').strip()
        diagnosis = request.form.get('diagnosis', '').strip()
        treatment_plan = request.form.get('treatment_plan', '').strip()
        doctor_remarks = request.form.get('doctor_remarks', '').strip()

        new_record = Consultation(
            appointment_id=appointment.appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            consultation_date=consultation_date,
            chief_complaint=chief_complaint,
            clinical_notes=clinical_notes,
            assessment=assessment,
            diagnosis=diagnosis,
            treatment_plan=treatment_plan,
            doctor_remarks=doctor_remarks
        )

        appointment.status = 'Completed'

        db.session.add(new_record)
        db.session.commit()

        flash('Consultation record saved successfully!', 'success')
        return redirect(url_for('view_consultation', appointment_id=appointment_id))

    today_str = datetime.today().strftime('%Y-%m-%d')
    return render_template('consultation_form.html', appointment=appointment, today_str=today_str)


@app.route('/consultation/view/<int:appointment_id>')
def view_consultation(appointment_id):
    if 'user_id' not in session:
        flash('Please login to view consultation records.', 'warning')
        return redirect(url_for('login'))

    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first_or_404()
    return render_template('consultation_view.html', consultation=consultation)

# -----------------------------------------------------------------------------
# SERVER STARTUP & AUTO DB INITIALIZATION
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('admin123')
            admin_user = User(username='admin', password_hash=hashed_pw, role='Admin')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created: admin / admin123")


    app.run(debug=True)
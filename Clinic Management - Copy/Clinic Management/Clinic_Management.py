from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clinic_management_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# DATABASE MODELS
# ==========================================

class Patient(db.Model):
    __tablename__ = 'patients'

    patient_id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    birth_date = db.Column(db.String(20), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    consultations = db.relationship('Consultation', backref='patient', lazy=True)
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True)
    bills = db.relationship('Bill', backref='patient', lazy=True)


class Doctor(db.Model):
    __tablename__ = 'doctors'

    doctor_id = db.Column(db.Integer, primary_key=True)
    doctor_code = db.Column(db.String(20), unique=True, nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    consultations = db.relationship('Consultation', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)


class Appointment(db.Model):
    __tablename__ = 'appointments'

    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    appointment_date = db.Column(db.String(20), nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Scheduled')


class Consultation(db.Model):
    __tablename__ = 'consultations'

    consultation_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    
    consultation_date = db.Column(db.String(50), nullable=False, default=lambda: datetime.now().strftime("%B %d, %Y"))
    chief_complaint = db.Column(db.Text, nullable=False)
    clinical_notes = db.Column(db.Text, nullable=True)
    assessment = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment_plan = db.Column(db.Text, nullable=False)
    doctor_remarks = db.Column(db.Text, nullable=True)

    appointment = db.relationship('Appointment', backref=db.backref('consultation', uselist=False))


class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    prescription_id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.consultation_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    prescription_date = db.Column(db.String(50), nullable=False)

    items = db.relationship('PrescriptionItem', backref='prescription', cascade='all, delete-orphan', lazy=True)
    consultation = db.relationship('Consultation', backref=db.backref('prescription', uselist=False))


class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'

    item_id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.prescription_id'), nullable=False)
    medicine = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    instructions = db.Column(db.Text, nullable=True)


class ClinicService(db.Model):
    __tablename__ = 'clinic_services'

    service_id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    fee = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class Bill(db.Model):
    __tablename__ = 'bills'

    bill_id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.consultation_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), default='Unpaid')

    items = db.relationship('BillItem', backref='bill', cascade='all, delete-orphan', lazy=True)
    consultation = db.relationship('Consultation', backref=db.backref('bill', uselist=False))


class BillItem(db.Model):
    __tablename__ = 'bill_items'

    item_id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.bill_id'), nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    fee = db.Column(db.Float, nullable=False)


# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        role = request.form.get('role', 'Admin')
        
        session['user'] = username
        session['role'] = role

        if role == 'Patient':
            patient = Patient.query.first()
            if patient:
                session['user_id'] = patient.patient_id
            return redirect(url_for('dashboard_patient'))
        elif role == 'Doctor':
            return redirect(url_for('schedule_appointment'))
        else:
            return redirect(url_for('dashboard_admin'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        last_patient = Patient.query.order_by(Patient.patient_id.desc()).first()
        next_id = (last_patient.patient_id + 1) if last_patient else 1
        generated_code = f"PAT-{next_id:04d}"

        new_patient = Patient(
            patient_code=generated_code,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            birth_date=request.form.get('birth_date'),
            sex=request.form.get('sex'),
            contact_number=request.form.get('contact_number'),
            address=request.form.get('address'),
            is_active=True
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        last_doc = Doctor.query.order_by(Doctor.doctor_id.desc()).first()
        next_id = (last_doc.doctor_id + 1) if last_doc else 1
        generated_code = f"DOC-{next_id:04d}"

        new_doc = Doctor(
            doctor_code=generated_code,
            doctor_name=request.form.get('doctor_name'),
            specialization=request.form.get('specialization'),
            contact_number=request.form.get('contact_number'),
            is_active=True
        )
        db.session.add(new_doc)
        db.session.commit()
        flash('Doctor registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register_doctor.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# --- ADMIN DASHBOARD & PATIENTS ---

@app.route('/dashboard_admin')
def dashboard_admin():
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        patients = Patient.query.filter(
            (Patient.patient_code.ilike(f"%{search_query}%")) |
            (Patient.first_name.ilike(f"%{search_query}%")) |
            (Patient.last_name.ilike(f"%{search_query}%"))
        ).all()
    else:
        patients = Patient.query.all()

    last_patient = Patient.query.order_by(Patient.patient_id.desc()).first()
    next_id = (last_patient.patient_id + 1) if last_patient else 1
    default_code = f"PAT-{next_id:04d}"

    return render_template(
        'dashboard_admin.html', 
        patients=patients, 
        search_query=search_query, 
        default_code=default_code
    )


@app.route('/patient/add', methods=['POST'])
def add_patient():
    last_patient = Patient.query.order_by(Patient.patient_id.desc()).first()
    next_id = (last_patient.patient_id + 1) if last_patient else 1
    generated_code = f"PAT-{next_id:04d}"

    new_patient = Patient(
        patient_code=generated_code,
        first_name=request.form.get('first_name'),
        last_name=request.form.get('last_name'),
        birth_date=request.form.get('birth_date'),
        sex=request.form.get('sex'),
        contact_number=request.form.get('contact_number'),
        address=request.form.get('address'),
        is_active=True
    )
    db.session.add(new_patient)
    db.session.commit()
    flash('New patient added successfully!', 'success')
    return redirect(url_for('dashboard_admin'))


@app.route('/patient/<int:patient_id>')
def patient_profile(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patient_profile.html', patient=patient)


@app.route('/patient/toggle/<int:patient_id>')
def toggle_patient_status(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = not patient.is_active
    db.session.commit()
    flash(f"Patient status updated to {'Active' if patient.is_active else 'Inactive'}.", 'info')
    return redirect(url_for('dashboard_admin'))


# --- PATIENT DASHBOARD ---

@app.route('/dashboard_patient')
def dashboard_patient():
    patient_id = session.get('user_id')
    patient = Patient.query.get(patient_id) if patient_id else Patient.query.first()
    
    if not patient:
        flash('No patient profile found.', 'warning')
        return redirect(url_for('login'))

    appointments = Appointment.query.filter_by(patient_id=patient.patient_id).all()
    return render_template('dashboard_patient.html', patient=patient, appointments=appointments)


# --- DOCTORS MANAGEMENT ---

@app.route('/doctors')
def doctor_management():
    doctors = Doctor.query.all()
    last_doc = Doctor.query.order_by(Doctor.doctor_id.desc()).first()
    next_id = (last_doc.doctor_id + 1) if last_doc else 1
    default_code = f"DOC-{next_id:04d}"
    return render_template('doctors.html', doctors=doctors, default_code=default_code)


@app.route('/doctor/add', methods=['POST'])
def add_doctor():
    last_doc = Doctor.query.order_by(Doctor.doctor_id.desc()).first()
    next_id = (last_doc.doctor_id + 1) if last_doc else 1
    generated_code = f"DOC-{next_id:04d}"

    new_doc = Doctor(
        doctor_code=generated_code,
        doctor_name=request.form.get('doctor_name'),
        specialization=request.form.get('specialization'),
        contact_number=request.form.get('contact_number'),
        is_active=True
    )
    db.session.add(new_doc)
    db.session.commit()
    flash('Doctor added successfully!', 'success')
    return redirect(url_for('doctor_management'))


# --- APPOINTMENTS MANAGEMENT ---

@app.route('/appointments')
def schedule_appointment():
    appointments = Appointment.query.all()
    patients = Patient.query.filter_by(is_active=True).all()
    doctors = Doctor.query.filter_by(is_active=True).all()
    return render_template('appointments.html', appointments=appointments, patients=patients, doctors=doctors)


@app.route('/appointment/add', methods=['POST'])
def add_appointment():
    new_app = Appointment(
        patient_id=request.form.get('patient_id'),
        doctor_id=request.form.get('doctor_id'),
        appointment_date=request.form.get('appointment_date'),
        appointment_time=request.form.get('appointment_time'),
        reason=request.form.get('reason'),
        status='Scheduled'
    )
    db.session.add(new_app)
    db.session.commit()
    flash('Appointment scheduled successfully!', 'success')
    return redirect(url_for('schedule_appointment'))


# --- CONSULTATION MANAGEMENT ---

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
        appointment.status = 'Completed'
        db.session.add(consultation)
        db.session.commit()
        flash('Consultation record saved successfully!', 'success')
        return redirect(url_for('view_consultation', appointment_id=appointment.appointment_id))

    today_str = datetime.now().strftime("%B %d, %Y")
    return render_template('consultation_form.html', appointment=appointment, today_str=today_str)


@app.route('/consultation/view/<int:appointment_id>')
def view_consultation(appointment_id):
    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first_or_404()
    return render_template('consultation_view.html', consultation=consultation)


# --- PRESCRIPTION MANAGEMENT & PRINTING ---

@app.route('/prescription/new/<int:appointment_id>', methods=['GET', 'POST'])
def new_prescription(appointment_id):
    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first_or_404()
    
    if request.method == 'POST':
        prescription = Prescription.query.filter_by(consultation_id=consultation.consultation_id).first()
        if not prescription:
            prescription = Prescription(
                consultation_id=consultation.consultation_id,
                patient_id=consultation.patient_id,
                doctor_id=consultation.doctor_id,
                prescription_date=consultation.consultation_date
            )
            db.session.add(prescription)
            db.session.commit()

        item = PrescriptionItem(
            prescription_id=prescription.prescription_id,
            medicine=request.form.get('medicine'),
            dosage=request.form.get('dosage'),
            frequency=request.form.get('frequency'),
            duration=request.form.get('duration'),
            instructions=request.form.get('instructions')
        )
        db.session.add(item)
        db.session.commit()
        flash('Medicine added to prescription!', 'success')
        return redirect(url_for('new_prescription', appointment_id=appointment_id))

    prescription = Prescription.query.filter_by(consultation_id=consultation.consultation_id).first()
    return render_template('prescription_form.html', consultation=consultation, prescription=prescription)


@app.route('/prescription/view/<int:appointment_id>')
def view_prescription(appointment_id):
    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first_or_404()
    prescription = Prescription.query.filter_by(consultation_id=consultation.consultation_id).first_or_404()
    return render_template('prescription_view.html', prescription=prescription)


@app.route('/prescription/print/<int:appointment_id>')
def print_prescription(appointment_id):
    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first_or_404()
    prescription = Prescription.query.filter_by(consultation_id=consultation.consultation_id).first_or_404()
    return render_template('prescription_print.html', prescription=prescription)


# --- CLINIC SERVICES MANAGEMENT ---

@app.route('/services')
def clinic_services():
    search_query = request.args.get('search', '').strip()
    if search_query:
        services = ClinicService.query.filter(ClinicService.service_name.ilike(f"%{search_query}%")).all()
    else:
        services = ClinicService.query.all()
    return render_template('services.html', services=services, search_query=search_query)


@app.route('/service/add', methods=['POST'])
def add_service():
    service_name = request.form.get('service_name')
    fee = request.form.get('fee')
    if service_name and fee:
        new_svc = ClinicService(service_name=service_name, fee=float(fee), is_active=True)
        db.session.add(new_svc)
        db.session.commit()
        flash('Clinic service added successfully!', 'success')
    return redirect(url_for('clinic_services'))


@app.route('/service/edit/<int:service_id>', methods=['POST'])
def edit_service(service_id):
    service = ClinicService.query.get_or_404(service_id)
    service.service_name = request.form.get('service_name')
    service.fee = float(request.form.get('fee'))
    db.session.commit()
    flash('Service updated successfully!', 'success')
    return redirect(url_for('clinic_services'))


@app.route('/service/toggle/<int:service_id>')
def toggle_service(service_id):
    service = ClinicService.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()
    flash(f"Service status updated to {'Active' if service.is_active else 'Inactive'}.", 'info')
    return redirect(url_for('clinic_services'))


# --- BILLING MODULE ---

@app.route('/billing/view/<int:appointment_id>', methods=['GET', 'POST'])
def view_billing(appointment_id):
    consultation = Consultation.query.filter_by(appointment_id=appointment_id).first_or_404()
    bill = Bill.query.filter_by(consultation_id=consultation.consultation_id).first()
    
    if not bill:
        default_fee = 500.0
        bill = Bill(
            consultation_id=consultation.consultation_id,
            patient_id=consultation.patient_id,
            subtotal=default_fee,
            total=default_fee,
            status='Unpaid'
        )
        db.session.add(bill)
        db.session.commit()
        
        default_item = BillItem(bill_id=bill.bill_id, service_name='Consultation', fee=default_fee)
        db.session.add(default_item)
        db.session.commit()

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_service':
            service_id = request.form.get('service_id')
            if service_id:
                svc = ClinicService.query.get(service_id)
                if svc:
                    b_item = BillItem(bill_id=bill.bill_id, service_name=svc.service_name, fee=svc.fee)
                    db.session.add(b_item)
                    db.session.commit()
                    
                    bill.subtotal = sum(i.fee for i in bill.items)
                    bill.total = bill.subtotal - bill.discount
                    db.session.commit()
                    flash('Service added to bill!', 'success')
        elif action == 'pay':
            bill.status = 'Paid'
            db.session.commit()
            flash('Payment processed successfully!', 'success')
            return redirect(url_for('view_billing', appointment_id=appointment_id))

        return redirect(url_for('view_billing', appointment_id=appointment_id))

    all_services = ClinicService.query.filter_by(is_active=True).all()
    return render_template('billing.html', consultation=consultation, bill=bill, all_services=all_services)


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
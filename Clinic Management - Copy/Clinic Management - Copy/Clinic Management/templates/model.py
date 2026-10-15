from datetime import datetime
from app import db  # adjust import according to your project structure

class Consultation(db.Model):
    __tablename__ = 'consultations'

    consultation_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.appointment_id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    
    # Required Lab 8 Fields
    consultation_date = db.Column(db.String(50), nullable=False, default=lambda: datetime.now().strftime("%B %d, %Y"))
    chief_complaint = db.Column(db.Text, nullable=False)
    clinical_notes = db.Column(db.Text, nullable=True)  # History / Clinical Notes
    assessment = db.Column(db.Text, nullable=True)      # Assessment
    diagnosis = db.Column(db.Text, nullable=False)
    treatment_plan = db.Column(db.Text, nullable=False)
    doctor_remarks = db.Column(db.Text, nullable=True)

    # Relationships (Appointment -> Patient -> Doctor -> Consultation)
    appointment = db.relationship('Appointment', backref=db.backref('consultation', uselist=False))
    patient = db.relationship('Patient', backref=db.backref('consultations', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('consultations', lazy=True))

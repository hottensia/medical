from flask import Blueprint, request, jsonify, current_app
from models import db, Appointment, AppointmentStatus, Notification, NotificationStatus, User, UserType, PatientNote, Treatment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from flask_mail import Mail, Message

appointments_routes = Blueprint('appointments_routes', __name__)

mail = Mail()

import logging

def send_email(subject, body, to_email):
    msg = Message(subject, recipients=[to_email])
    msg.body = body

    try:
        mail.send(msg)
        logging.info(f"Email sent to {to_email} successfully!")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

@appointments_routes.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('therapist_id') or not data.get('patient_id') or not data.get('date') or not data.get('time'):
        return jsonify({'message': 'Therapist ID, patient ID, date, and time are required.'}), 400

    try:
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        appointment_time = datetime.strptime(data['time'], '%H:%M:%S').time()
    except ValueError:
        return jsonify({'message': 'Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM:SS for time.'}), 400

    new_appointment = Appointment(
        patient_id=data['patient_id'],
        therapist_id=data['therapist_id'],
        date=appointment_date,
        time=appointment_time,
        status=AppointmentStatus.PENDING,
        notes=data.get('notes', '')
    )

    db.session.add(new_appointment)

    notification_message = f"Your appointment has been successfully booked for {appointment_date} at {appointment_time}."
    notification = Notification(
        user_id=new_appointment.patient_id,
        message=notification_message,
        status=NotificationStatus.UNREAD
    )
    db.session.add(notification)
    db.session.commit()

    patient = User.query.get(new_appointment.patient_id)
    if patient and patient.email:
        subject = "Appointment Confirmation"
        body = f"Dear {patient.first_name},\n\nYour appointment has been successfully booked for {appointment_date} at {appointment_time}.\n\nBest regards,\nYour Therapy Team"
        email_sent = send_email(subject, body, patient.email)

        email_status = "Email sent successfully." if email_sent else "Email failed to send."
    else:
        email_status = "Patient email not found."

    appointment_response = {
        'id': new_appointment.id,
        'patient_id': new_appointment.patient_id,
        'therapist_id': new_appointment.therapist_id,
        'date': new_appointment.date.strftime('%Y-%m-%d'),
        'time': new_appointment.time.strftime('%H:%M:%S'),
        'status': new_appointment.status.value,
        'notes': new_appointment.notes,
        'created_at': new_appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': new_appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'email_status': email_status
    }

    return jsonify({'message': 'Appointment created successfully!', 'appointment': appointment_response}), 201


@appointments_routes.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    current_user_id = get_jwt_identity()

    appointments = Appointment.query.filter(
        (Appointment.patient_id == current_user_id) | (Appointment.therapist_id == current_user_id)
    ).all()

    appointment_list = [
        {
            'id': appointment.id,
            'patient_id': appointment.patient_id,
            'therapist_name': f"{appointment.therapist.first_name} {appointment.therapist.last_name}",
            'date': appointment.date.strftime('%Y-%m-%d'),
            'therapist_id': appointment.therapist_id,
            'time': appointment.time.strftime('%H:%M:%S'),
            'status': appointment.status.value,
            'notes': appointment.notes,
            'has_patient_note': PatientNote.query.filter_by(scheduled_appointment_id=appointment.id).count() > 0,
            'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for appointment in appointments
    ]

    return jsonify({'appointments': appointment_list}), 200

@appointments_routes.route('/appointments/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_appointments_by_user_id(user_id):
    current_user_id = get_jwt_identity()

    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({'message': 'User not found.'}), 404

    if current_user.user_type == UserType.THERAPIST:
        appointments = Appointment.query.filter(Appointment.therapist_id == current_user_id).all()
    elif current_user.user_type == UserType.PATIENT and current_user_id == user_id:
        appointments = Appointment.query.filter(Appointment.patient_id == user_id).all()
    else:
        return jsonify({'message': 'Unauthorized access.'}), 403

    appointment_list = [
        {
            'id': appointment.id,
            'patient_id': appointment.patient_id,
            'therapist_name': f"{appointment.therapist.first_name} {appointment.therapist.last_name}",
            'therapist_id': appointment.therapist_id,
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M:%S'),
            'status': appointment.status.value,
            'notes': appointment.notes,
            'has_patient_note': PatientNote.query.filter_by(scheduled_appointment_id=appointment.id).count() > 0,
            'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for appointment in appointments
    ]

    return jsonify({'appointments': appointment_list}), 200

@appointments_routes.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment_by_id(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found.'}), 404

    appointment_response = {
        'id': appointment.id,
        'patient_id': appointment.patient_id,
        'therapist_id': appointment.therapist_id,
        'date': appointment.date.strftime('%Y-%m-%d'),
        'time': appointment.time.strftime('%H:%M:%S'),
        'status': appointment.status.value,
        'notes': appointment.notes,
        'has_patient_note': PatientNote.query.filter_by(scheduled_appointment_id=appointment.id).count() > 0,
        'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    }

    return jsonify({'appointment': appointment_response}), 200

@appointments_routes.route('/appointment-details/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment_details(appointment_id):
    current_user_id = get_jwt_identity()

    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return jsonify({'message': 'Appointment not found.'}), 404

    therapist = User.query.get(appointment.therapist_id)
    therapist_name = f"{therapist.first_name} {therapist.last_name}" if therapist else "Unknown"

    patient_notes = PatientNote.query.filter_by(scheduled_appointment_id=appointment.id).all()

    treatments = Treatment.query.filter_by(patient_id=appointment.patient_id).all()

    response = {
        'appointment_id': appointment.id,
        'date': appointment.date.strftime('%Y-%m-%d'),
        'time': appointment.time.strftime('%H:%M:%S'),
        'status': appointment.status.name,
        'notes': appointment.notes,
        'therapist_name': therapist_name,
        'patient_notes': [
            {
                'id': note.id,
                'notes': note.notes,
                'diagnosis': note.diagnosis,
                'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            } for note in patient_notes
        ],
        'treatments': [
            {
                'id': treatment.id,
                'notes': treatment.notes,
                'prescription': treatment.prescription,
                'start_date': treatment.start_date.strftime('%Y-%m-%d'),
                'end_date': treatment.end_date.strftime('%Y-%m-%d') if treatment.end_date else None,
            } for treatment in treatments
        ]
    }

    return jsonify(response), 200

@appointments_routes.route('/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    data = request.get_json()
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found.'}), 404

    if data.get('status'):
        try:
            appointment.status = AppointmentStatus[data['status'].upper()]
        except KeyError:
            return jsonify({
                'message': 'Invalid status value. Use one of: PENDING, BOOKED, CANCELLED, COMPLETED, ONGOING.'
            }), 400

    if data.get('notes'):
        appointment.notes = data['notes']

    db.session.commit()

    # Send notification for the updated appointment
    notification_message = f"Your appointment on {appointment.date} at {appointment.time} has been updated to {appointment.status.value}."
    notification = Notification(
        user_id=appointment.patient_id,
        message=notification_message,
        status=NotificationStatus.UNREAD
    )
    db.session.add(notification)
    db.session.commit()

    patient = User.query.get(appointment.patient_id)
    if patient and patient.email:
        subject = "Appointment Status Update"
        body = f"Dear {patient.first_name},\n\nYour appointment on {appointment.date} at {appointment.time} has been updated to {appointment.status.value}.\n\nBest regards,\nYour Therapy Team"
        email_sent = send_email(subject, body, patient.email)
        email_status = "Email sent successfully." if email_sent else "Email failed to send."
    else:
        email_status = "Patient email not found."

    appointment_response = {
        'id': appointment.id,
        'patient_id': appointment.patient_id,
        'therapist_id': appointment.therapist_id,
        'date': appointment.date.strftime('%Y-%m-%d'),
        'time': appointment.time.strftime('%H:%M:%S'),
        'status': appointment.status.value,
        'notes': appointment.notes,
        'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'email_status': email_status
    }

    return jsonify({'message': 'Appointment updated successfully!', 'appointment': appointment_response}), 200


@appointments_routes.route('/appointments/<int:appointment_id>/ongoing', methods=['PUT'])
@jwt_required()
def mark_appointment_as_ongoing(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found.'}), 404

    appointment.status = AppointmentStatus.ONGOING
    db.session.commit()

    return jsonify({'message': 'Appointment marked as ongoing successfully!'}), 200

@appointments_routes.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found.'}), 404

    db.session.delete(appointment)
    db.session.commit()

    return jsonify({'message': 'Appointment deleted successfully!'}), 200

@appointments_routes.route('/therapist/<int:therapist_id>/patients', methods=['GET'])
@jwt_required()
def get_patients_by_therapist_id(therapist_id):
    current_user_id = get_jwt_identity()

    current_user = User.query.get(current_user_id)
    if current_user.user_type != UserType.THERAPIST or current_user_id != therapist_id:
        return jsonify({'message': 'Unauthorized access.'}), 403

    patients = User.query.join(Appointment, User.id == Appointment.patient_id) \
        .filter(Appointment.therapist_id == therapist_id) \
        .all()

    patient_list = [
        {
            'id': patient.id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'email': patient.email,
            'status': patient.status.value,
        }
        for patient in patients
    ]

    return jsonify({'patients': patient_list}), 200


@appointments_routes.route('/patient/<int:patient_id>/therapists', methods=['GET'])
@jwt_required()
def get_therapists_by_patient_id(patient_id):
    current_user_id = get_jwt_identity()

    current_user = User.query.get(current_user_id)
    if current_user.user_type != UserType.PATIENT or current_user_id != patient_id:
        return jsonify({'message': 'Unauthorized access.'}), 403

    therapists = User.query.join(Appointment, User.id == Appointment.therapist_id) \
        .filter(Appointment.patient_id == patient_id) \
        .all()

    therapist_list = [
        {
            'id': therapist.id,
            'first_name': therapist.first_name,
            'last_name': therapist.last_name,
            'email': therapist.email,
            'status': therapist.status.value,
        }
        for therapist in therapists
    ]

    return jsonify({'therapists': therapist_list}), 200

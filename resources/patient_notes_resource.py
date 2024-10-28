from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, PatientNote, ScheduledAppointment, Appointment, AppointmentStatus
from datetime import datetime

patient_notes_routes = Blueprint('patient_notes', __name__)

@patient_notes_routes.route('/patient_notes', methods=['POST'])
@jwt_required()
def create_patient_note():
    data = request.get_json()
    current_user_id = get_jwt_identity()  # Optional: Use this if you need to associate notes with the user

    scheduled_appointment_id = data.get('scheduled_appointment_id')
    notes = data.get('notes')
    diagnosis = data.get('diagnosis')

    # Validate required fields
    if not scheduled_appointment_id or not notes:
        return jsonify({'message': 'Scheduled appointment ID and notes are required.'}), 400

    # Fetch the scheduled appointment
    scheduled_appointment = ScheduledAppointment.query.get(scheduled_appointment_id)
    if not scheduled_appointment:
        return jsonify({'message': 'Scheduled appointment not found.'}), 404

    # Create a new patient note
    new_patient_note = PatientNote(
        scheduled_appointment_id=scheduled_appointment_id,
        notes=notes,
        diagnosis=diagnosis
    )

    db.session.add(new_patient_note)

    # Update the associated appointment's status
    appointment = Appointment.query.get(scheduled_appointment.appointment_id)
    if appointment:
        appointment.has_patient_note = True
        appointment.status = AppointmentStatus.ALMOST_COMPLETE  # Set status to ALMOST_COMPLETE

    # Commit the session to save the new patient note and update the appointment
    db.session.commit()

    # Prepare the response for the scheduled appointment
    scheduled_appointment_response = {
        'id': scheduled_appointment.id,
        'appointment_id': scheduled_appointment.appointment_id,
        'scheduled_time': scheduled_appointment.scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': scheduled_appointment.status.value,
        'created_at': scheduled_appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': scheduled_appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    }

    # Prepare the response for the new patient note
    patient_note_response = {
        'id': new_patient_note.id,
        'scheduled_appointment_id': new_patient_note.scheduled_appointment_id,
        'notes': new_patient_note.notes,
        'diagnosis': new_patient_note.diagnosis,
        'created_at': new_patient_note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': new_patient_note.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'scheduled_appointment': scheduled_appointment_response
    }

    return jsonify({'message': 'Patient note created successfully!', 'patient_note': patient_note_response}), 201



@patient_notes_routes.route('/patient_notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_patient_note(note_id):
    data = request.get_json()
    patient_note = PatientNote.query.get(note_id)

    if not patient_note:
        return jsonify({'message': 'Patient note not found.'}), 404

    # Update note fields if provided
    if 'notes' in data:
        patient_note.notes = data['notes']
    if 'diagnosis' in data:
        patient_note.diagnosis = data['diagnosis']

    db.session.commit()

    return jsonify({'message': 'Patient note updated successfully!'}), 200

@patient_notes_routes.route('/patient_notes/<int:note_id>', methods=['GET'])
@jwt_required()
def get_patient_note(note_id):
    patient_note = PatientNote.query.get(note_id)

    if not patient_note:
        return jsonify({'message': 'Patient note not found.'}), 404

    patient_note_response = {
        'id': patient_note.id,
        'scheduled_appointment_id': patient_note.scheduled_appointment_id,
        'notes': patient_note.notes,
        'diagnosis': patient_note.diagnosis,
        'created_at': patient_note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': patient_note.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    }

    return jsonify({'patient_note': patient_note_response}), 200

@patient_notes_routes.route('/patient_notes', methods=['GET'])
@jwt_required()
def get_patient_notes():
    current_user_id = get_jwt_identity()
    user_id = request.args.get('user_id')

    if user_id:
        patient_notes = (
            PatientNote.query
            .join(ScheduledAppointment)
            .join(Appointment)
            .filter((Appointment.patient_id == user_id) | (Appointment.therapist_id == user_id))
            .all()
        )
    else:
        patient_notes = PatientNote.query.all()

    notes_response = []
    for note in patient_notes:
        scheduled_appointment = ScheduledAppointment.query.get(note.scheduled_appointment_id)
        scheduled_appointment_response = {
            'id': scheduled_appointment.id,
            'appointment_id': scheduled_appointment.appointment_id,
            'scheduled_time': scheduled_appointment.scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': scheduled_appointment.status.value,
            'created_at': scheduled_appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': scheduled_appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        notes_response.append({
            'id': note.id,
            'scheduled_appointment_id': note.scheduled_appointment_id,
            'notes': note.notes,
            'diagnosis': note.diagnosis,
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': note.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'scheduled_appointment': scheduled_appointment_response
        })

    return jsonify({'message': 'Patient notes retrieved successfully!', 'patient_notes': notes_response}), 200

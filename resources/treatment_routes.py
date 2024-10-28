from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Treatment, User, AppointmentStatus, Appointment
from datetime import datetime

treatment_routes = Blueprint('treatments', __name__)


@treatment_routes.route('/treatments', methods=['POST'])
@jwt_required()
def create_treatment():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    patient_id = data.get('patient_id')
    therapist_id = data.get('therapist_id')
    notes = data.get('notes')
    prescription = data.get('prescription')
    appointment_id = data.get('appointment_id')

    start_date = data.get('start_date')
    end_date = data.get('end_date')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else datetime.utcnow().date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD for start_date and end_date.'}), 400

    if not (patient_id and therapist_id and notes and prescription):
        return jsonify({'message': 'Patient ID, Therapist ID, Notes, and Prescription are required.'}), 400

    patient = User.query.get(patient_id)
    therapist = User.query.get(therapist_id)
    if not patient or not therapist:
        return jsonify({'message': 'Patient or Therapist not found.'}), 404

    new_treatment = Treatment(
        patient_id=patient_id,
        therapist_id=therapist_id,
        notes=notes,
        prescription=prescription,
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(new_treatment)

    if appointment_id:
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return jsonify({'message': 'Appointment not found.'}), 404

        appointment.status = AppointmentStatus.COMPLETED

    db.session.commit()

    return jsonify({
        'message': 'Treatment created successfully!',
        'treatment': {
            'id': new_treatment.id,
            'patient_id': new_treatment.patient_id,
            'therapist_id': new_treatment.therapist_id,
            'notes': new_treatment.notes,
            'prescription': new_treatment.prescription,
            'start_date': new_treatment.start_date.strftime('%Y-%m-%d'),
            'end_date': new_treatment.end_date.strftime('%Y-%m-%d') if new_treatment.end_date else None,
            'created_at': new_treatment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 201


@treatment_routes.route('/treatments/<int:treatment_id>', methods=['PUT'])
@jwt_required()
def update_treatment(treatment_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()

    treatment = Treatment.query.get(treatment_id)
    if not treatment:
        return jsonify({'message': 'Treatment not found.'}), 404

    if 'notes' in data:
        treatment.notes = data['notes']
    if 'prescription' in data:
        treatment.prescription = data['prescription']

    if 'start_date' in data:
        try:
            treatment.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format for start_date. Use YYYY-MM-DD.'}), 400
    if 'end_date' in data:
        try:
            treatment.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format for end_date. Use YYYY-MM-DD.'}), 400

    db.session.commit()

    return jsonify({
        'message': 'Treatment updated successfully!',
        'treatment': {
            'id': treatment.id,
            'patient_id': treatment.patient_id,
            'therapist_id': treatment.therapist_id,
            'notes': treatment.notes,
            'prescription': treatment.prescription,
            'start_date': treatment.start_date.strftime('%Y-%m-%d'),
            'end_date': treatment.end_date.strftime('%Y-%m-%d') if treatment.end_date else None,
            'created_at': treatment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': treatment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 200


@treatment_routes.route('/treatments', methods=['GET'])
@jwt_required()
def get_treatments():
    patient_id = request.args.get('patient_id')
    therapist_id = request.args.get('therapist_id')

    query = Treatment.query
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if therapist_id:
        query = query.filter_by(therapist_id=therapist_id)

    treatments = query.all()
    treatments_response = []
    for treatment in treatments:
        treatments_response.append({
            'id': treatment.id,
            'patient_id': treatment.patient_id,
            'therapist_id': treatment.therapist_id,
            'notes': treatment.notes,
            'prescription': treatment.prescription,
            'start_date': treatment.start_date.strftime('%Y-%m-%d'),
            'end_date': treatment.end_date.strftime('%Y-%m-%d') if treatment.end_date else None,
            'created_at': treatment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': treatment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify({
        'message': 'Treatments retrieved successfully!',
        'treatments': treatments_response
    }), 200


@treatment_routes.route('/treatments/<int:treatment_id>', methods=['GET'])
@jwt_required()
def get_treatment(treatment_id):
    treatment = Treatment.query.get(treatment_id)

    if not treatment:
        return jsonify({'message': 'Treatment not found.'}), 404

    treatment_response = {
        'id': treatment.id,
        'patient_id': treatment.patient_id,
        'therapist_id': treatment.therapist_id,
        'notes': treatment.notes,
        'prescription': treatment.prescription,
        'start_date': treatment.start_date.strftime('%Y-%m-%d'),
        'end_date': treatment.end_date.strftime('%Y-%m-%d') if treatment.end_date else None,
        'created_at': treatment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': treatment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify({'treatment': treatment_response}), 200

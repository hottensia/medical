from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, MoodEntry
from datetime import datetime

mood_entries_routes = Blueprint('mood_entries', __name__)

@mood_entries_routes.route('/mood_entries', methods=['POST'])
@jwt_required()
def create_mood_entry():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    mood_score = data.get('mood_score')
    symptoms = data.get('symptoms')
    therapist_id = data.get('therapist_id')

    if mood_score is None or therapist_id is None:
        return jsonify({'message': 'Mood score and therapist ID are required.'}), 400

    new_mood_entry = MoodEntry(
        mood_score=mood_score,
        symptoms=symptoms,
        patient_id=current_user_id,
        therapist_id=therapist_id
    )

    db.session.add(new_mood_entry)
    db.session.commit()

    mood_entry_response = {
        'id': new_mood_entry.id,
        'mood_score': new_mood_entry.mood_score,
        'symptoms': new_mood_entry.symptoms,
        'patient_id': new_mood_entry.patient_id,
        'therapist_id': new_mood_entry.therapist_id,
        'created_at': new_mood_entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': new_mood_entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify({'message': 'Mood entry created successfully!', 'mood_entry': mood_entry_response}), 201


@mood_entries_routes.route('/mood_entries/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_mood_entry(entry_id):
    data = request.get_json()
    mood_entry = MoodEntry.query.get(entry_id)

    if not mood_entry:
        return jsonify({'message': 'Mood entry not found.'}), 404

    mood_entry.mood_score = data.get('mood_score', mood_entry.mood_score)
    mood_entry.symptoms = data.get('symptoms', mood_entry.symptoms)
    mood_entry.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({'message': 'Mood entry updated successfully!'}), 200


@mood_entries_routes.route('/mood_entries/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_mood_entry(entry_id):
    mood_entry = MoodEntry.query.get(entry_id)

    if not mood_entry:
        return jsonify({'message': 'Mood entry not found.'}), 404

    mood_entry_response = {
        'id': mood_entry.id,
        'mood_score': mood_entry.mood_score,
        'symptoms': mood_entry.symptoms,
        'patient_id': mood_entry.patient_id,
        'therapist_id': mood_entry.therapist_id,
        'created_at': mood_entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': mood_entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify({'mood_entry': mood_entry_response}), 200


@mood_entries_routes.route('/mood_entries', methods=['GET'])
@jwt_required()
def get_mood_entries():
    current_user_id = get_jwt_identity()

    therapist_id = request.args.get('therapist_id')

    query = MoodEntry.query.filter_by(patient_id=current_user_id)
    if therapist_id:
        query = query.filter_by(therapist_id=therapist_id)

    mood_entries = query.all()

    mood_entries_response = [
        {
            'id': entry.id,
            'mood_score': entry.mood_score,
            'symptoms': entry.symptoms,
            'patient_id': entry.patient_id,
            'therapist_id': entry.therapist_id,
            'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for entry in mood_entries
    ]

    return jsonify({'mood_entries': mood_entries_response}), 200

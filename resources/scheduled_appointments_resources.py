from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Appointment, AppointmentStatus, ScheduledAppointment, ScheduledAppointmentStatus
from datetime import datetime

scheduled_appointments_routes = Blueprint('scheduled_appointments', __name__)

@scheduled_appointments_routes.route('/scheduled_appointments', methods=['POST'])
@jwt_required()
def schedule_appointment():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    appointment_id = data.get('appointment_id')
    scheduled_time = data.get('scheduled_time')
    status = data.get('status', ScheduledAppointmentStatus.SCHEDULED.value)

    if not appointment_id or not scheduled_time:
        return jsonify({'message': 'Appointment ID and scheduled time are required.'}), 400

    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({'message': 'Appointment not found.'}), 404

    new_scheduled_appointment = ScheduledAppointment(
        appointment_id=appointment_id,
        scheduled_time=datetime.fromisoformat(scheduled_time),
        status=ScheduledAppointmentStatus[status.upper()],
    )

    db.session.add(new_scheduled_appointment)

    appointment.status = AppointmentStatus.BOOKED if new_scheduled_appointment.status == ScheduledAppointmentStatus.SCHEDULED else AppointmentStatus.CANCELLED

    db.session.commit()

    scheduled_appointment_response = {
        'id': new_scheduled_appointment.id,
        'appointment_id': new_scheduled_appointment.appointment_id,
        'scheduled_time': new_scheduled_appointment.scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': new_scheduled_appointment.status.value,
        'created_at': new_scheduled_appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': new_scheduled_appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    }

    return jsonify({
        'message': 'Appointment scheduled successfully!',
        'scheduled_appointment': scheduled_appointment_response
    }), 201

@scheduled_appointments_routes.route('/scheduled_appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_scheduled_appointment(appointment_id):
    scheduled_appointment = ScheduledAppointment.query.filter_by(appointment_id=appointment_id).first()

    if not scheduled_appointment:
        return jsonify({'message': 'Scheduled appointment not found.'}), 404

    scheduled_appointment_response = {
        'id': scheduled_appointment.id,
        'appointment_id': scheduled_appointment.appointment_id,
        'scheduled_time': scheduled_appointment.scheduled_time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': scheduled_appointment.status.value,
        'created_at': scheduled_appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': scheduled_appointment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    }

    return jsonify({
        'message': 'Scheduled appointment retrieved successfully!',
        'scheduled_appointment': scheduled_appointment_response
    }), 200

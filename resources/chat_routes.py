from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ChatMessage, MessageType, MessageStatus, User, ChatStatus, AppointmentStatus, Appointment

chat_routes = Blueprint('chat_routes', __name__)


@chat_routes.route('/chat/messages', methods=['POST'])
@jwt_required()
def send_message():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    recipient_id = data.get('recipient_id')
    content = data.get('content')
    appointment_id = data.get('appointment_id')

    if not recipient_id or not content or not appointment_id:
        return jsonify({'message': 'Recipient ID, message content, and appointment ID are required.'}), 400

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'message': 'Recipient not found.'}), 404

    message = ChatMessage(
        sender_id=current_user_id,
        recipient_id=recipient_id,
        appointment_id=appointment_id,
        content=content,
        message_type=(
            MessageType.PATIENT_TO_THERAPIST if current_user_id != recipient_id else MessageType.THERAPIST_TO_PATIENT),
        status=MessageStatus.DELIVERED,
        chat_status=ChatStatus.STARTED
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully!', 'message_id': message.id}), 201


@chat_routes.route('/chat/messages/reply', methods=['POST'])
@jwt_required()
def reply_message():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    original_message_id = data.get('original_message_id')
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    appointment_id = data.get('appointment_id')

    if not original_message_id or not recipient_id or not content or not appointment_id:
        return jsonify(
            {'message': 'Original message ID, recipient ID, reply content, and appointment ID are required.'}), 400

    original_message = ChatMessage.query.get(original_message_id)
    if not original_message:
        return jsonify({'message': 'Original message not found.'}), 404

    recipient = User.query.get(recipient_id)
    if not recipient:
        return jsonify({'message': 'Recipient not found.'}), 404

    reply = ChatMessage(
        sender_id=current_user_id,
        recipient_id=recipient_id,
        appointment_id=appointment_id,
        content=content,
        message_type=MessageType.THERAPIST_TO_PATIENT if current_user_id == original_message.recipient_id else MessageType.PATIENT_TO_THERAPIST,
        status=MessageStatus.DELIVERED,
        chat_status=ChatStatus.ONGOING
    )

    db.session.add(reply)
    db.session.commit()

    return jsonify({
        'message': 'Reply sent successfully!',
        'reply_id': reply.id
    }), 201


@chat_routes.route('/chat/messages/<int:message_id>/status', methods=['PATCH'])
@jwt_required()
def update_message_status(message_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()

    status = data.get('status')

    if not status:
        return jsonify({'message': 'Status is required.'}), 400

    try:
        message_status = MessageStatus[status.upper()]
    except KeyError:
        return jsonify({'message': 'Invalid status value. Use one of: DELIVERED, SEEN, REPLIED.'}), 400

    message = ChatMessage.query.get(message_id)
    if not message:
        return jsonify({'message': 'Message not found.'}), 404

    if message.sender_id != current_user_id and message.recipient_id != current_user_id:
        return jsonify({'message': 'You are not authorized to update this message.'}), 403

    message.status = message_status
    db.session.commit()

    return jsonify({'message': 'Message status updated successfully!'}), 200


@chat_routes.route('/chat/messages', methods=['GET'])
@jwt_required()
def get_messages():
    current_user_id = get_jwt_identity()

    messages = ChatMessage.query.filter(
        (ChatMessage.sender_id == current_user_id) | (ChatMessage.recipient_id == current_user_id)
    ).all()

    messages_response = []
    for message in messages:
        messages_response.append({
            'id': message.id,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id,
            'appointment_id': message.appointment_id,
            'content': message.content,
            'message_type': message.message_type.value,
            'status': message.status.value,
            'chat_status': message.chat_status.value,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    return jsonify({
        'messages': messages_response
    }), 200


@chat_routes.route('/chat/messages/appointment/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_messages_by_appointment(appointment_id):
    current_user_id = get_jwt_identity()

    messages = ChatMessage.query.filter_by(appointment_id=appointment_id).all()

    if not messages:
        return jsonify({'message': 'No messages found for this appointment.'}), 404

    messages_response = []
    for message in messages:
        messages_response.append({
            'id': message.id,
            'sender_id': message.sender_id,
            'sender_name': message.sender.first_name + " " + message.sender.last_name,
            'recipient_id': message.recipient_id,
            'recipient_name': message.recipient.first_name + " " + message.recipient.last_name,
            'appointment_id': message.appointment_id,
            'content': message.content,
            'message_type': message.message_type.value,
            'status': message.status.value,
            'chat_status': message.chat_status.value,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    return jsonify({
        'messages': messages_response
    }), 200


@chat_routes.route('/chat/messages/<int:appointment_id>/complete', methods=['POST'])
@jwt_required()
def mark_chat_complete(appointment_id):
    current_user_id = get_jwt_identity()

    messages = ChatMessage.query.filter_by(appointment_id=appointment_id).all()
    if not messages:
        return jsonify({'message': 'No messages found for this appointment.'}), 404

    for message in messages:
        if message.sender_id == current_user_id or message.recipient_id == current_user_id:
            message.chat_status = ChatStatus.COMPLETED

    appointment = Appointment.query.get(appointment_id)
    if appointment:
        appointment.status = AppointmentStatus.ONGOING
        db.session.commit()

    db.session.commit()
    return jsonify({'message': 'Chat marked as completed and appointment status updated to ONGOING successfully!'}), 200

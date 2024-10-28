from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Notification, User , NotificationStatus

notification_routes = Blueprint('notifications', __name__)

@notification_routes.route('/notifications', methods=['POST'])
@jwt_required()
def create_notification():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    message = data.get('message')

    if not message:
        return jsonify({'message': 'Message is required.'}), 400

    new_notification = Notification(
        user_id=current_user_id,
        message=message
    )

    db.session.add(new_notification)
    db.session.commit()

    return jsonify({
        'message': 'Notification created successfully!',
        'notification': {
            'id': new_notification.id,
            'user_id': new_notification.user_id,
            'message': new_notification.message,
            'status': new_notification.status.value,
            'created_at': new_notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }), 201


@notification_routes.route('/notifications/<int:notification_id>/mark_as_read', methods=['PATCH'])
@jwt_required()
def mark_notification_as_read(notification_id):
    current_user_id = get_jwt_identity()

    notification = Notification.query.filter_by(id=notification_id, user_id=current_user_id).first()

    if not notification:
        return jsonify({'message': 'Notification not found or access denied.'}), 404

    notification.status = NotificationStatus.READ

    db.session.commit()

    return jsonify({
        'message': 'Notification marked as read successfully!',
        'notification': {
            'id': notification.id,
            'user_id': notification.user_id,
            'message': notification.message,
            'status': notification.status.value,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
    }), 200


@notification_routes.route('/notifications/<int:notification_id>', methods=['PUT'])
@jwt_required()
def update_notification(notification_id):
    data = request.get_json()
    notification = Notification.query.get(notification_id)

    if not notification:
        return jsonify({'message': 'Notification not found.'}), 404

    status = data.get('status')
    if status:
        if status not in [s.value for s in NotificationStatus]:
            return jsonify({'message': 'Invalid status value. Must be "unread" or "read".'}), 400
        notification.status = NotificationStatus[status.upper()]

    db.session.commit()

    return jsonify({'message': 'Notification updated successfully!'}), 200

@notification_routes.route('/notifications', methods=['GET'])
@jwt_required()
def get_unread_notifications():
    current_user_id = get_jwt_identity()

    notifications = Notification.query.filter_by(
        user_id=current_user_id,
        status=NotificationStatus.UNREAD
    ).all()

    notifications_response = [
        {
            'id': notification.id,
            'user_id': notification.user_id,
            'message': notification.message,
            'status': notification.status.value,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for notification in notifications
    ]

    return jsonify({
        'message': 'Unread notifications retrieved successfully!',
        'notifications': notifications_response
    }), 200


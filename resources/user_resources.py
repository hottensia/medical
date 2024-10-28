from flask import Blueprint, request, jsonify
from models import db, User, UserType, UserStatus
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

user_routes = Blueprint('user_routes', __name__)


@user_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'message': 'Username, password, and email are required.'}), 400

    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'message': 'User already exists.'}), 400

    user_type = data.get('user_type', 'patient').upper()
    if user_type not in [type.name for type in UserType]:
        return jsonify({'message': f'Invalid user type. Possible values: {[type.name for type in UserType]}'}), 400

    new_user = User(
        username=data['username'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        user_type=UserType[user_type],
        status=UserStatus.ACTIVE  # Set status to ACTIVE on registration
    )

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=new_user.id)

    return jsonify({
        'message': 'User registered successfully!',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'user_type': new_user.user_type.name,
            'status': new_user.status.name  # Optionally include status in response
        },
        'access_token': access_token
    }), 201



import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

@user_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('username') or not data.get('password'):
        logging.warning('Login attempt with missing username or password.')
        return jsonify({'message': 'Username and password are required.'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user:
        logging.info(f'Login attempt for non-existent user: {data["username"]}.')
        return jsonify({'message': 'User not found.'}), 404

    if check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        logging.info(f'User {user.username} logged in successfully.')
        return jsonify({
            'message': 'Login successful!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type.name,
                'status': user.status.name
            },
            'access_token': access_token
        }), 200

    logging.warning(f'Failed login attempt for user: {data["username"]} due to incorrect password.')
    return jsonify({'message': 'Invalid password.'}), 401



@user_routes.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Current password and new password are required.'}), 400

    user = User.query.get(current_user_id)

    if not user or not check_password_hash(user.password, data['current_password']):
        return jsonify({'message': 'Current password is incorrect.'}), 401

    user.password = generate_password_hash(data['new_password'])
    db.session.commit()

    return jsonify({'message': 'Password changed successfully!'}), 200


@user_routes.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()

    if not data.get('username'):
        return jsonify({'message': 'Username is required.'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user:
        return jsonify({'message': 'User not found.'}), 404

    user.password = generate_password_hash('password')
    db.session.commit()

    return jsonify({'message': 'Password has been reset to "password".'}), 200

@user_routes.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    users = User.query.all()
    user_list = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'user_type': user.user_type.name,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'status':user.status.name

    } for user in users]

    return jsonify({'users': user_list}), 200

@user_routes.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found.'}), 404

    user_response = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'user_type': user.user_type.name,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'status':user.status.name

    }

    return jsonify({'user': user_response}), 200

@user_routes.route('/therapists', methods=['GET'])
@jwt_required()
def get_therapists():
    therapists = User.query.filter_by(user_type=UserType.THERAPIST).all()
    therapist_list = [{
        'id': therapist.id,
        'username': therapist.username,
        'email': therapist.email,
        'user_type': therapist.user_type.name,
        'first_name': therapist.first_name,
        'last_name': therapist.last_name,
        'status': therapist.status.name
    } for therapist in therapists]

    return jsonify({'therapists': therapist_list}), 200
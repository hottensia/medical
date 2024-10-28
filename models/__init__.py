from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date, Time, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLAlchemyEnum

db = SQLAlchemy()

class UserStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class UserType(Enum):
    ADMIN = 'admin'
    PATIENT = 'patient'
    THERAPIST = 'therapist'


class AppointmentStatus(Enum):
    PENDING = 'PENDING'
    BOOKED = 'BOOKED'
    ONGOING = "ONGOING"
    ALMOST_COMPLETE = 'ALMOST_COMPLETE'
    CANCELLED = 'CANCELLED'
    COMPLETED = 'COMPLETED'


class ScheduledAppointmentStatus(Enum):
    SCHEDULED = 'SCHEDULED'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'

class NotificationStatus(Enum):
    UNREAD = 'UNREAD'
    READ = 'READ'

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.ACTIVE)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)

    treatments_as_patient = relationship('Treatment', foreign_keys='Treatment.patient_id', back_populates='patient')
    treatments_as_therapist = relationship('Treatment', foreign_keys='Treatment.therapist_id', back_populates='therapist')
    notifications = relationship('Notification', foreign_keys='Notification.user_id', back_populates='user')
    def __repr__(self):
        return f'<User {self.username}>'



class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.PENDING)
    notes = db.Column(db.String(500), nullable=True)
    has_patient_note = db.Column(db.Boolean, default=False)
    chat_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('User', foreign_keys=[patient_id])
    therapist = db.relationship('User', foreign_keys=[therapist_id])
    scheduled_appointments = db.relationship('ScheduledAppointment', back_populates='appointment')
    chat_messages = db.relationship('ChatMessage', back_populates='appointment')

    def __repr__(self):
        return (f'<Appointment {self.id}: Patient {self.patient_id} '
                f'with Therapist {self.therapist_id} on {self.date} at {self.time}>')



class ScheduledAppointment(db.Model):
    __tablename__ = 'scheduled_appointments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    scheduled_time = db.Column(DateTime, nullable=False)
    status = db.Column(db.Enum(ScheduledAppointmentStatus), nullable=False, default=ScheduledAppointmentStatus.SCHEDULED)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointment = db.relationship('Appointment', back_populates='scheduled_appointments')
    patient_notes = db.relationship('PatientNote', back_populates='scheduled_appointment', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ScheduledAppointment {self.id}: Appointment {self.appointment_id} at {self.scheduled_time}>'





class MoodEntry(db.Model):
    __tablename__ = 'mood_entries'

    id = db.Column(Integer, primary_key=True)
    mood_score = db.Column(Integer, nullable=False)
    symptoms = db.Column(Text, nullable=True)
    patient_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    therapist_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)

    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship('User', foreign_keys=[patient_id])
    therapist = relationship('User', foreign_keys=[therapist_id])

    def __repr__(self):
        return (f'<MoodEntry {self.id}: Patient {self.patient_id} '
                f'Therapist {self.therapist_id} Score {self.mood_score}>')


class PatientNote(db.Model):
    __tablename__ = 'patient_notes'

    id = db.Column(db.Integer, primary_key=True)
    scheduled_appointment_id = db.Column(db.Integer, db.ForeignKey('scheduled_appointments.id'), nullable=False)
    notes = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to ScheduledAppointment
    scheduled_appointment = db.relationship('ScheduledAppointment', back_populates='patient_notes')

    def __repr__(self):
        return f'<PatientNote {self.id}: Appointment {self.scheduled_appointment_id}>'

class Treatment(db.Model):
    __tablename__ = 'treatments'

    id = db.Column(Integer, primary_key=True)
    patient_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    therapist_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    notes = db.Column(Text, nullable=True)
    prescription = db.Column(Text, nullable=True)
    start_date = db.Column(Date, nullable=False, default=datetime.utcnow().date())
    end_date = db.Column(Date, nullable=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship('User', foreign_keys=[patient_id])
    therapist = relationship('User', foreign_keys=[therapist_id])

    def __repr__(self):
        return f'<Treatment {self.id} for Patient {self.patient_id} by Therapist {self.therapist_id}>'

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(db.Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}: {self.message}, Status: {self.status}>'

class MessageStatus(Enum):
    DELIVERED = 'DELIVERED'
    SEEN = 'SEEN'
    REPLIED = 'REPLIED'

class MessageType(Enum):
    PATIENT_TO_THERAPIST = 'PATIENT_TO_THERAPIST'
    THERAPIST_TO_PATIENT = 'THERAPIST_TO_PATIENT'

class ChatStatus(Enum):
    STARTED = 'STARTED'
    ONGOING = 'ONGOING'
    COMPLETED = 'COMPLETED'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(SQLAlchemyEnum(MessageType), nullable=False)
    status = db.Column(SQLAlchemyEnum(MessageStatus), default=MessageStatus.DELIVERED)
    chat_status = db.Column(SQLAlchemyEnum(ChatStatus), default=ChatStatus.STARTED)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = relationship('User', foreign_keys=[sender_id])
    recipient = relationship('User', foreign_keys=[recipient_id])
    appointment = relationship('Appointment', back_populates='chat_messages')

    def __repr__(self):
        return f'<ChatMessage {self.id} from {self.sender_id} to {self.recipient_id} for appointment {self.appointment_id}>'


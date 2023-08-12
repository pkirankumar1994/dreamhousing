from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, timedelta

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    position = db.Column(db.String(150))
    business_arena = db.Column(db.String(150))
    street = db.Column(db.String(150))
    place = db.Column(db.String(150))
    country = db.Column(db.String(150))
    phone_number = db.Column(db.String(150))
    adhar_number = db.Column(db.String(150))
    role = db.Column(db.String(20), default="user")

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.String(50))
    description = db.Column(db.String(400))
    price =  db.Column(db.String(100))
    location = db.Column(db.String(150))
    property_type = db.Column(db.String(150))
    status = db.Column(db.Boolean, default=False, nullable=False)
    area = db.Column(db.String(150))
    imageUrls = db.Column(db.String(1000))
    beds = db.Column(db.Integer)
    baths = db.Column(db.Integer)
    garage = db.Column(db.Integer)
    balcony = db.Column(db.Boolean, default=False)
    outdoor_kitchen = db.Column(db.Boolean, default=False)
    cable_tv = db.Column(db.Boolean, default=False)
    decks = db.Column(db.Boolean, default=False)
    tennis_court = db.Column(db.Boolean, default=False)
    internet = db.Column(db.Boolean, default=False)
    parking = db.Column(db.Boolean, default=False)
    sun_room = db.Column(db.Boolean, default=False)
    concrete_flooring = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())

class PropertyBuyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    adhar_card_front_url = db.Column(db.String(255), nullable=False)
    adhar_card_back_url = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="Pending", nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    contact_number = db.Column(db.String(20))
    desired_price = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    scheduled_visit = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('property_buy_requests', cascade='all, delete-orphan'))
    property = db.relationship('Property', backref=db.backref('buy_requests', cascade='all, delete-orphan'))

class ResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(hours=1)  # Token is valid for 1 hour
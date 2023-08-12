from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User,ResetToken
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
import re
from flask_mail import Message, current_app
from threading import Thread
import secrets

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        form_fields = ['email', 'firstName', 'lastName', 'position', 'businessArena',
                       'street', 'place', 'country', 'phoneNumber', 'adharNumber',
                       'password1', 'password2']
        field_errors = {}

        for field in form_fields:
            value = request.form.get(field)

            if not value:
                field_errors[field] = 'This field is required.'

        if not field_errors:
            email = request.form.get('email')
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            position = request.form.get('position')
            business_arena = request.form.get('businessArena')
            street = request.form.get('street')
            place = request.form.get('place')
            country = request.form.get('country')
            phone_number = request.form.get('phoneNumber')
            adhar_number = request.form.get('adharNumber')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')

            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

            if User.query.filter_by(email=email).first():
                field_errors['email'] = 'Email already exists.'
            elif len(email) < 4:
                field_errors['email'] = 'Email must be greater than 3 characters.'
            elif not re.match(email_pattern, email):
                field_errors['email'] = 'Invalid email address.'
            elif len(first_name) < 2:
                field_errors['firstName'] = 'First name must be greater than 1 character.'
            elif password1 != password2:
                field_errors['password2'] = 'Passwords don\'t match.'
            elif len(password1) < 7:
                field_errors['password1'] = 'Password must be at least 7 characters.'

            if not field_errors:
                new_user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    position=position,
                    business_arena=business_arena,
                    street=street,
                    place=place,
                    country=country,
                    phone_number=phone_number,
                    adhar_number=adhar_number,
                    password=generate_password_hash(password1, method='sha256')
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return redirect(url_for('views.home'))

        for field, error in field_errors.items():
            flash(error, category='error')

    return render_template("sign_up.html", user=current_user)

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
 
        if user:
            # Generate a reset token
            token = secrets.token_hex(32)
            reset_token = ResetToken(user_id=user.id, token=token)
            db.session.add(reset_token)
            db.session.commit()

            # Send the reset token to the user's email
            subject = 'Password Reset Request'
            recipient = user.email

            reset_link = url_for('auth.reset_password', token=token, _external=True)
            html_body = render_template('email/reset_password_template.html', reset_link=reset_link)

            msg = Message(subject=subject, recipients=[recipient])
            msg.html = html_body

            Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

            flash('Password reset instructions sent to your email.', category='success')
            return redirect(url_for('auth.login'))

        flash('No account found with this email.', category='error')

    return render_template("forgot_password.html", user=current_user)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = ResetToken.query.filter_by(token=token).first()

    if not reset_token or reset_token.is_expired():
        flash('Invalid or expired reset token.', category='error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password == confirm_password:
            # Update the user's password
            user = User.query.get(reset_token.user_id)
            user.password = generate_password_hash(new_password, method='sha256')

            # Delete the reset token
            db.session.delete(reset_token)
            db.session.commit()

            flash('Password reset successful!', category='success')
            return redirect(url_for('auth.login'))
        else:
            flash('Passwords do not match.', category='error')

    return render_template("reset_password.html", token=token,user={})

def send_async_email(app, msg):
    with app.app_context():
        # Access `mail` object using `current_app`
        mail = current_app.extensions.get('mail')
        mail.send(msg)


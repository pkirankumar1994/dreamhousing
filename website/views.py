from flask import Blueprint, render_template, request, flash, jsonify,redirect,url_for,Flask,current_app
from flask_login import login_required, current_user
from .models import Property, PropertyBuyRequest,User
from . import db
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from flask_mail import Message
from threading import Thread

views = Blueprint('views', __name__)

app = Flask(__name__)

# Set the allowed file extensions for Aadhar card images
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/', methods=['GET'])
@login_required
def home():
    properties = Property.query.order_by(Property.date.desc()).limit(4).all()
    return render_template("index.html", user=current_user, properties=properties)

@views.route('/about', methods=['GET'])
@login_required
def about():
    return render_template("about.html", user=current_user)

@views.route('/property', methods=['GET'])
@login_required
def property():
    properties = Property.query.all()
    return render_template("property.html", user=current_user, properties=properties)

@views.route('/viewproperty/<property_id>', methods=['GET'])
@login_required
def viewproperty(property_id):
    property = Property.query.get(property_id)
    if property:
        return render_template("property-single.html", user=current_user, property=property)
    else:
        flash("Property not found.", "error")
        return redirect(url_for("views.property"))

@views.route('/contact', methods=['GET'])
@login_required
def contact():
    return render_template("contact.html", user=current_user)

@views.route('/property-request/<property_id>', methods=['GET', 'POST'])
@login_required
def product_buy_request(property_id):
    if request.method == 'POST':
        try:
            # Get property buy request details from the HTML form
            adhar_card_front = request.files['adhar_card_front']
            adhar_card_back = request.files['adhar_card_back']
            message = request.form.get('message')
            contact_number = request.form.get('contact_number')
            desired_price = request.form.get('desired_price')
            payment_method = request.form.get('payment_method')
            scheduled_visit = request.form.get('scheduled_visit')
            scheduled_visit = datetime.strptime(scheduled_visit, '%Y-%m-%dT%H:%M')

            # Retrieve the property based on the property_id
            property = Property.query.get(property_id)
            if property is None:
                flash('Property not found!', category='error')
                return redirect(url_for('views.property'))

            # Upload and save the Aadhar card images
            if adhar_card_front and allowed_file(adhar_card_front.filename) and adhar_card_back and allowed_file(adhar_card_back.filename):
                filename_front = secure_filename(adhar_card_front.filename)
                filename_back = secure_filename(adhar_card_back.filename)
                app.config['UPLOAD_FOLDER'] = 'website/static/upload'
                adhar_card_front.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_front))
                adhar_card_back.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_back))
            else:
                flash('Invalid file format for Aadhar card images!', category='error')
                return redirect(url_for('views.property'))

            # Create a new PropertyBuyRequest object and populate its attributes
            new_property_buy_request = PropertyBuyRequest(
                adhar_card_front_url=filename_front,
                adhar_card_back_url=filename_back,
                property=property,
                user=current_user,
                message=message,
                contact_number=contact_number,
                desired_price=desired_price,
                payment_method=payment_method,
                scheduled_visit=scheduled_visit
            )

            db.session.add(new_property_buy_request)
            db.session.commit()
            flash('Property buy request sent!', category='success')
            return redirect(url_for('views.property'))
        except Exception as e:
            flash('An error occurred while adding the property buy request!', category='error')
            return redirect(url_for('views.property'))

    property_buy_requests = PropertyBuyRequest.query.all()  # Retrieve all property buy requests
    return render_template("request.html", user=current_user, property_buy_requests=property_buy_requests)

@views.route('/admin', methods=['GET', 'POST'])
@login_required
def properties():
    if request.method == 'POST':
        try:
            # Get Property details from the HTML form
            property_id = request.form.get('property_id')
            description = request.form.get('description')
            price = request.form.get('price')
            location = request.form.get('location')
            property_type = request.form.get('property_type')
            status = 'status' in request.form
            area = request.form.get('area')
            beds = int(request.form.get('beds'))
            baths = int(request.form.get('baths'))
            garage = int(request.form.get('garage'))
            balcony = 'balcony' in request.form
            outdoor_kitchen = 'outdoor_kitchen' in request.form
            cable_tv = 'cable_tv' in request.form
            decks = 'decks' in request.form
            tennis_court = 'tennis_court' in request.form
            internet = 'internet' in request.form
            parking = 'parking' in request.form
            sun_room = 'sun_room' in request.form
            concrete_flooring = 'concrete_flooring' in request.form
            image_urls = request.form.get('image_urls')

            new_property = Property(
                property_id=property_id,
                description=description,
                price=price,
                location=location,
                property_type=property_type,
                status=status,
                area=area,
                imageUrls=image_urls,  # Assign the list of image URLs to the imageUrls attribute
                beds=beds,
                baths=baths,
                garage=garage,
                balcony=balcony,
                outdoor_kitchen=outdoor_kitchen,
                cable_tv=cable_tv,
                decks=decks,
                tennis_court=tennis_court,
                internet=internet,
                parking=parking,
                sun_room=sun_room,
                concrete_flooring=concrete_flooring
            )

            db.session.add(new_property)
            db.session.commit()
            flash('Property added!', category='success')
            return redirect(url_for("views.property"))
        except Exception as e:
            flash('An error occurred while adding the property!', category='error')
            print(e)

    properties = Property.query.all()  # Retrieve all properties
    return render_template("admin/admin.html", user=current_user, properties=properties)

@views.route('/admin/newproperty', methods=['GET', 'POST'])
@login_required
def newproperty():
    return render_template("admin/newproperty.html", user=current_user)

@views.route('/delete-property', methods=['POST'])
def delete_product():
    try:
        property_data = json.loads(request.data)
        property_id = property_data['propertyId']
        property = Property.query.get(property_id)
        if property:
            db.session.delete(property)
            db.session.commit()
            flash('Property deleted!', category='success')
            return redirect(url_for('views.properties'))
    except Exception as e:
        print(e)
        return redirect(url_for('views.properties'))

@views.route('admin/edit-property/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_property(product_id):
    if request.method == 'GET':
        property_data = Property.query.get(product_id)
        if property_data:
            return render_template('admin/editproperty.html', user=current_user, property=property_data)
        else:
            flash('Property not found', 'error')
            return redirect(url_for('views.properties'))

    if request.method == 'POST':
        try:
            property_db_id = request.form.get('property_db_id')

            edited_property = Property.query.get(property_db_id)
            if edited_property:
                edited_property.property_id = request.form.get('property_id')
                edited_property.description = request.form.get('description')
                edited_property.price = request.form.get('price')
                edited_property.location = request.form.get('location')
                edited_property.property_type = request.form.get('property_type')
                edited_property.status = 'status' in request.form
                edited_property.area = request.form.get('area')
                edited_property.beds = request.form.get('beds')
                edited_property.baths = request.form.get('baths')
                edited_property.garage = request.form.get('garage')
                edited_property.balcony = 'balcony' in request.form
                edited_property.outdoor_kitchen = 'outdoor_kitchen' in request.form
                edited_property.cable_tv = 'cable_tv' in request.form
                edited_property.decks = 'decks' in request.form
                edited_property.tennis_court = 'tennis_court' in request.form
                edited_property.internet = 'internet' in request.form
                edited_property.parking = 'parking' in request.form
                edited_property.sun_room = 'sun_room' in request.form
                edited_property.concrete_flooring = 'concrete_flooring' in request.form
                edited_property.imageUrls = request.form.get('image_urls')

                db.session.commit()
                flash('Property successfully updated', 'success')
                return redirect(url_for('views.properties'))
            else:
                flash('Property not found', 'error')
                return redirect(url_for('views.properties'))
        except Exception as e:
            print(e)
            flash('An error occurred while updating the property', 'error')
            return redirect(url_for('views.properties'))

    return redirect(url_for('views.properties'))

@views.route('/purchase-requests', methods=['GET'])
@login_required
def purchase_requests():
    purchase_requests = PropertyBuyRequest.query.all()  # Retrieve all purchase requests
    return render_template("admin/purchase_requests.html", user=current_user, purchase_requests=purchase_requests)

def send_async_email(app, msg):
    with app.app_context():
        # Access `mail` object using `current_app`
        mail = current_app.extensions.get('mail')
        mail.send(msg)

@views.route('/update-status/<request_id>/<status>', methods=['POST'])
@login_required
def update_status(request_id, status):
    # Retrieve the PropertyBuyRequest object based on the request_id
    request = PropertyBuyRequest.query.get(request_id)

    if request is None:
        return jsonify({'message': 'Property buy request not found!'}), 404

    if status not in ['Accepted', 'Rejected']:
        return jsonify({'message': 'Invalid status!'}), 400

    # Update the status of the request
    request.status = status
    db.session.commit()

    # Send email notification to the user
    subject = f'Property Buy Request {status}'
    recipient = request.user.email

    # Render the HTML template for the email
    html_body = render_template('email/status_update_template.html', status=status, request=request)

    msg = Message(subject=subject, recipients=[recipient])
    msg.html = html_body

    # Create a separate thread to send the email asynchronously
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

    return jsonify({'message': f'Property buy request {status.lower()}ed!'}), 200

@views.route('/users', methods=['GET'])
@login_required
def users():
    # Retrieve all users from the database
    all_users = User.query.all()

    # Render the users.html template and pass the users to it
    return render_template('admin/users.html', user=current_user,users=all_users)

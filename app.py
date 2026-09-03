import os
from datetime import datetime
import pandas as pd
from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, send_file, render_template_string
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz


# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/car_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


db = SQLAlchemy(app)

# Login Manager Setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'


# Helper function to check file extension
def allowed_file(filename):  # <-- ADD THIS FUNCTION
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_local_time():
    # Fetch local Italian time (Europe/Rome)
    rome_tz = pytz.timezone('Europe/Rome')
    return datetime.now(rome_tz)

# -----------------------------------------------------------------------------
# DATABASE MODELS
# -----------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), default='user')  # 'admin' or 'user'
    trips = db.relationship('TripLog', backref='user', lazy=True)

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make_model = db.Column(db.String(100), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    current_km = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False)  # 'available' or 'in_use'
    image_file = db.Column(db.String(100), default='default_car.jpg')
    trips = db.relationship('TripLog', backref='car', lazy=True)

class TripLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    #start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    start_time = db.Column(db.DateTime, default=get_local_time, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    start_km = db.Column(db.Integer, nullable=False)
    end_km = db.Column(db.Integer, nullable=True)
    destination_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active' or 'completed'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.first_name}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# -----------------------------------------------------------------------------
# ADMIN ROUTES
# -----------------------------------------------------------------------------
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    cars = Car.query.all()
    users = User.query.all()
    return render_template('admin_dashboard.html', cars=cars, users=users)

@app.route('/admin/add-user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    role = request.form.get('role')

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'warning')
        return redirect(url_for('admin_dashboard'))

    hashed_pw = generate_password_hash(password, method='scrypt')
    new_user = User(
        username=username,
        password=hashed_pw,
        first_name=first_name,
        last_name=last_name,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    flash(f'User "{username}" created successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add-car', methods=['POST'])
@login_required
def add_car():
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
    
    make_model = request.form.get('make_model')
    plate_number = request.form.get('plate_number')
    current_km = int(request.form.get('current_km', 0))

    if Car.query.filter_by(plate_number=plate_number).first():
        flash('A vehicle with this plate number already exists.', 'warning')
        return redirect(url_for('admin_dashboard'))

    # Handle Uploaded Image
    image_filename = 'default_car.jpg'
    if 'car_image' in request.files:
        file = request.files['car_image']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{plate_number}_{file.filename}")
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

    new_car = Car(
        make_model=make_model, 
        plate_number=plate_number, 
        current_km=current_km,
        image_file=image_filename
    )
    db.session.add(new_car)
    db.session.commit()
    flash('Vehicle added to fleet successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-car/<int:car_id>')
@login_required
def delete_car(car_id):
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
    
    car = Car.query.get_or_404(car_id)
    if car.status == 'in_use':
        flash('Cannot delete a vehicle that is currently checked out.', 'danger')
        return redirect(url_for('admin_dashboard'))

    TripLog.query.filter_by(car_id=car.id).delete()
    db.session.delete(car)
    db.session.commit()
    flash('Vehicle removed from fleet.', 'info')
    return redirect(url_for('admin_dashboard'))

# -----------------------------------------------------------------------------
# USER DASHBOARD & TRIP ROUTES
# -----------------------------------------------------------------------------
@app.route('/user')
@login_required
def user_dashboard():
    active_trips = TripLog.query.filter_by(user_id=current_user.id, status='active').all()
    available_cars = Car.query.filter_by(status='available').all()
    return render_template('user_dashboard.html', active_trips=active_trips, available_cars=available_cars)

@app.route('/checkout/<int:car_id>', methods=['POST'])
@login_required
def checkout_car(car_id):
    car = Car.query.get_or_404(car_id)
    start_km = int(request.form.get('start_km', car.current_km))
    notes = request.form.get('destination_notes', '')  # <-- Captures destination comment

    if car.status != 'available':
        flash('This car is currently unavailable.', 'danger')
        return redirect(url_for('user_dashboard'))

    trip = TripLog(
        user_id=current_user.id,
        car_id=car.id,
        start_km=start_km,
        destination_notes=notes,  # <-- Saves destination comment
        start_time=get_local_time()
    )
    
    car.status = 'in_use'
    car.current_km = start_km
    
    db.session.add(trip)
    db.session.commit()
    flash(f'Vehicle {car.make_model} successfully checked out.', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/return/<int:trip_id>', methods=['POST'])
@login_required
def return_car(trip_id):
    trip = TripLog.query.get_or_404(trip_id)
    
    if trip.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('user_dashboard'))

    end_km = int(request.form.get('end_km'))
    if end_km < trip.start_km:
        flash('Return odometer reading cannot be less than starting reading.', 'danger')
        return redirect(url_for('user_dashboard'))

    trip.end_km = end_km
    trip.end_time = get_local_time()
    trip.status = 'completed'

    car = Car.query.get(trip.car_id)
    car.status = 'available'
    car.current_km = end_km

    db.session.commit()
    flash('Vehicle returned successfully.', 'success')
    return redirect(url_for('user_dashboard'))

# -----------------------------------------------------------------------------
# REPORT GENERATION ROUTES
# -----------------------------------------------------------------------------
@app.route('/admin/export/car/csv/<int:car_id>')
@login_required
def export_car_csv(car_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403

    car = Car.query.get_or_404(car_id)
    logs = db.session.query(TripLog, User)\
        .join(User, TripLog.user_id == User.id)\
        .filter(TripLog.car_id == car_id).all()

    data = []
    for log, user in logs:
        data.append({
            "User": f"{user.first_name} {user.last_name}",
            "Username": user.username,
            "Car": car.make_model,
            "Plate": car.plate_number,
            "Destination/Notes": log.destination_notes or "N/A",
            "Start Time": log.start_time.strftime('%Y-%m-%d %H:%M:%S') if log.start_time else "",
            "End Time": log.end_time.strftime('%Y-%m-%d %H:%M:%S') if log.end_time else "In Progress",
            "Start KM": log.start_km,
            "End KM": log.end_km if log.end_km else "N/A",
            "Distance (KM)": (log.end_km - log.start_km) if log.end_km else "N/A"
        })

    df = pd.DataFrame(data)
    os.makedirs('exports', exist_ok=True)
    filename = f"exports/car_{car_id}_report.csv"
    df.to_csv(filename, index=False)
    return send_file(filename, as_attachment=True)

@app.route('/admin/export/car/html/<int:car_id>')
@login_required
def view_car_html_report(car_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403

    car = Car.query.get_or_404(car_id)
    logs = db.session.query(TripLog, User)\
        .join(User, TripLog.user_id == User.id)\
        .filter(TripLog.car_id == car_id).all()

    html_template = """
    {% extends "base.html" %}
    {% block content %}
    <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center mb-3 gap-2">
        <h4 class="mb-0">Report for {{ car.make_model }} ({{ car.plate_number }})</h4>
        <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary btn-sm">Back to Dashboard</a>
    </div>
    <div class="card shadow-sm">
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-striped align-middle mb-0 text-nowrap">
                    <thead class="table-dark">
                        <tr>
                            <th>Driver</th>
                            <th>Destination / Notes</th>
                            <th>Start Time</th>
                            <th>End Time</th>
                            <th>Start KM</th>
                            <th>End KM</th>
                            <th>Distance</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for log, user in logs %}
                        <tr>
                            <td>{{ user.first_name }} {{ user.last_name }}</td>
                            <td><span class="badge bg-info text-dark">{{ log.destination_notes or 'N/A' }}</span></td>
                            <td>{{ log.start_time.strftime('%Y-%m-%d %H:%M') if log.start_time }}</td>
                            <td>{{ log.end_time.strftime('%Y-%m-%d %H:%M') if log.end_time else 'In Progress' }}</td>
                            <td>{{ log.start_km }} km</td>
                            <td>{{ log.end_km ~ ' km' if log.end_km else 'N/A' }}</td>
                            <td>{{ (log.end_km - log.start_km) ~ ' km' if log.end_km else 'N/A' }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="7" class="text-center py-3 text-muted">No trip logs found.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(html_template, car=car, logs=logs)
# -----------------------------------------------------------------------------
# APP INITIALIZATION & DEFAULT SEED DATA
# -----------------------------------------------------------------------------
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='nec_admin').first():
            hashed_admin_pw = generate_password_hash('NeC2024!!', method='scrypt')
            admin_user = User(
                username='admin',
                password=hashed_admin_pw,
                first_name='System',
                last_name='Admin',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created: Username: nec_admin | Password: xxxxxx")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)

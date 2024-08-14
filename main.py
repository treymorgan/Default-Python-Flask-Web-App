from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_required, login_user, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from waitress import serve

# Initialize the Flask application
app = Flask(__name__)

# Import secret key and database URI from a separate configuration file
from config import SECRET_KEY, SQLALCHEMY_DATABASE_URI

# Set secret key for sessions and CSRF protection, and database URI for SQLAlchemy
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI

# Initialize the SQLAlchemy object
db = SQLAlchemy(app)

# Initialize the Flask-Login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Define the User class for database interaction and authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))

    # Method to set password hash using Werkzeug's security functions
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check if the provided password matches the stored hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Function to load a user from the database based on user ID (used by Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Route for user registration
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data from the POST request
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the username or email already exists in the database
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('A user already exists with that email or username.')
            return redirect(url_for('register'))

        # Create a new user object and set the password
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful, please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for user login
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get username and password from the form
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if the user exists and if the password is correct
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')
            
    return render_template('login.html')

# Route for logging out the user
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Main entry point of the application
if __name__ == "__main__":
    with app.app_context():  # This ensures that the app is running within an application context
        db.create_all()  # Create all database tables based on the defined models
    serve(app, host="0.0.0.0", port=5003)  # Serve the app using Waitress on port 5003

from dotenv import load_dotenv
import os
import secrets
from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message

# Load environment variables from .env
load_dotenv()

# Generate a random secret key
secret_key = secrets.token_hex(16)
print("Secret Key:", secret_key)

app = Flask(__name__)

# Configuration for Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')  # Default to Gmail SMTP
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))  # Use port 587 with TLS
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'ciarancairns@googlemail.com')  # Default fallback
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'fyyr hzan vffp quvz')  # Default fallback
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])  # Fallback
app.config['SECRET_KEY'] = secret_key

# Debug print to check if environment variables are loaded
print("MAIL_SERVER:", os.getenv('MAIL_SERVER'))
print("MAIL_PORT:", os.getenv('MAIL_PORT'))
print("MAIL_USERNAME:", os.getenv('MAIL_USERNAME'))
print("MAIL_PASSWORD:", os.getenv('MAIL_PASSWORD'))
print("MAIL_DEFAULT_SENDER:", os.getenv('MAIL_DEFAULT_SENDER'))

mail = Mail(app)

@app.route('/')
def hello_world():
    return render_template('index.html')  # Ensure 'index.html' exists and is properly configured




@app.route('/send-email', methods=['GET', 'POST'])
def send_email():
    # Extract form data
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject', 'Contact Form Submission')
    message = request.form.get('message')
    print("MAIL_PASSWORD (runtime):", os.getenv('MAIL_PASSWORD'))

    # Validate required fields
    if not name or not email or not message:
        return jsonify({"message": "Name, email, and message are required."}), 400

    # Create the email message
    msg = Message(
        subject=subject,
        sender=app.config['MAIL_DEFAULT_SENDER'],  # Use the default sender
        recipients=[app.config['MAIL_USERNAME']],  # Receiver's email
    )
    msg.body = f"Message from {name} ({email}):\n\n{message}"

    # Try to send the email
    try:
        mail.connect()
        mail.send(msg)
        return "<p class='text-green-500'>Message sent successfully!</p>", 200
    except Exception as e:
        return f"<p class='text-red-500'>Failed to send message: {str(e)}</p>", 500

# Do not include app.run(), as PythonAnywhere handles it


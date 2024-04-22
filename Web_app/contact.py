from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_mail import Message, Mail

# Assuming Flask-Mail is initialized in your main app file as 'mail'
from your_main_app import mail

contact = Blueprint('contact', __name__, template_folder='templates')

@contact.route('/contact', methods=['GET', 'POST'], endpoint='submit_contact')
def submit_contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Implement email sending functionality
        msg = Message("New Contact Form Submission",
                      sender=email,
                      recipients=["your-recipient@example.com"],
                      body=f"From: {name}, Email: {email}, Message: {message}")
        mail.send(msg)

        flash('Thank you for your message!', 'success')
        return redirect(url_for('contact.submit_contact'))

    return render_template('contact.html')  # Make sure this template is within 'templates' folder of the blueprint

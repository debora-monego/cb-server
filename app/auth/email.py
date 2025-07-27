from flask import current_app, render_template
from flask_mail import Message
from app import mail
import jwt
from datetime import datetime, timedelta

def send_email(subject, recipients, html_body, text_body):
    msg = Message(subject, sender=current_app.config['MAIL_DEFAULT_SENDER'], recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def get_reset_token(user, expires_in=3600):
    # Create a JWT token for password reset
    payload = {
        'reset_password': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_reset_token(token):
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload['reset_password']
    except:
        return None

def send_password_reset_email(user):
    token = get_reset_token(user)
    
    # Create a reset link - In production, use a real frontend URL
    reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/reset-password/{token}"
    
    # Simple plain text email
    text_body = f'''
    To reset your password click the following link:
    {reset_url}
    
    If you did not request a password reset simply ignore this message.
    '''
    
    # Simple HTML email
    html_body = f'''
    <p>To reset your password click the following link:</p>
    <p><a href="{reset_url}">Reset Password</a></p>
    <p>If you did not request a password reset simply ignore this message.</p>
    '''
    
    send_email('Reset Your Password', [user.email], html_body, text_body)
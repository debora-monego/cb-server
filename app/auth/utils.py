from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from datetime import datetime, timedelta

def generate_reset_token(user_id):
    """Generate a token for password reset."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    salt = current_app.config.get('SECURITY_PASSWORD_SALT', 'password-reset-salt')
    return serializer.dumps(user_id, salt=salt)

def verify_reset_token(token, expiration=3600):  # Token expires after 1 hour by default
    """Verify a password reset token."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    salt = current_app.config.get('SECURITY_PASSWORD_SALT', 'password-reset-salt')
    try:
        user_id = serializer.loads(
            token,
            salt=salt,
            max_age=expiration
        )
        return user_id
    except:
        return None

def get_user_from_token(token):
    """Get user from a token."""
    from app.models.user import User
    
    user_id = verify_reset_token(token)
    if not user_id:
        return None
        
    return User.query.get(user_id)
from flask import (
    Blueprint, request, jsonify, current_app, session
)
from datetime import datetime, timedelta
from app import db, limiter
from app.models.user import User, Role, LoginLog
from app.auth.email import send_password_reset_email
from app.auth.utils import generate_reset_token, verify_reset_token
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__)

# Rate limiting decorators
login_limit = limiter.limit("5 per minute")
register_limit = limiter.limit("3 per hour")

@bp.before_request
def before_request():
    if current_app.debug:
        print("\n=== Request Debug ===")
        print(f"Request Path: {request.path}")
        print(f"Request Method: {request.method}")
        print(f"Request Headers: {dict(request.headers)}")
        print(f"Request Body: {request.get_json(silent=True)}")
        print("===================\n")

@bp.route('/login', methods=['POST'])
@login_limit
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data received'
        }), 400

    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)  # Get remember flag with default False

    if not username or not password:
        return jsonify({
            'status': 'error',
            'message': 'Missing username or password'
        }), 400

    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        # Check if account is locked
        if user.is_locked():
            return jsonify({
                'status': 'error',
                'message': 'Account temporarily locked due to multiple failed login attempts'
            }), 403
            
        # Log login attempt
        login_log = LoginLog(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            success=True
        )
        db.session.add(login_log)
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log the user in with Flask-Login
        login_user(user, remember=remember)
        
        return jsonify({
            'status': 'success',
            'message': 'Successfully logged in',
            'username': user.username
        })
    else:
        # Log failed login attempt
        if user:
            user.failed_login_attempts += 1
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.lock_account(duration_minutes=30)
            db.session.commit()
            
            login_log = LoginLog(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                success=False
            )
            db.session.add(login_log)
            db.session.commit()
            
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    # Print debug info
    print(f"Logout called for user: {current_user.username if current_user else 'Unknown'}")
    
    # Log the user out with Flask-Login
    logout_user()
    
    # Clear session
    session.clear()
    
    # Return a success response
    return jsonify({
        'status': 'success',
        'message': 'Successfully logged out'
    })

@bp.route('/register', methods=['POST'])
@register_limit
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    try:
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'status': 'error',
                'message': 'Email address already registered'
            }), 400

        # Check if username is taken
        if User.query.filter_by(username=username).first():
            return jsonify({
                'status': 'error',
                'message': 'Username already taken'
            }), 400

        # Check if default role exists
        default_role = Role.query.filter_by(name='user').first()
        if not default_role:
            default_role = Role(name='user')
            db.session.add(default_role)
            db.session.commit()

        # Create new user
        user = User(
            username=username,
            email=email,
            created_at=datetime.utcnow(),
            role=default_role
        )
        user.set_password(password)
        
        # For development, automatically verify email
        if current_app.config.get('DEVELOPMENT', False):
            user.email_verified = True
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in with Flask-Login
        login_user(user)
        
        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'username': user.username
        })
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during registration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during registration'
        }), 500

@bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    return jsonify({
        'status': 'success',
        'data': {
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at.isoformat(),
            'email_verified': current_user.email_verified
        }
    })

@bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data received'
        }), 400
        
    # Update email
    new_email = data.get('email')
    if new_email and new_email != current_user.email:
        if User.query.filter_by(email=new_email).first():
            return jsonify({
                'status': 'error',
                'message': 'Email already in use'
            }), 400
        current_user.email = new_email
        current_user.email_verified = False  # Require re-verification
        
    # Update password
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    if current_password and new_password:
        if not current_user.check_password(current_password):
            return jsonify({
                'status': 'error',
                'message': 'Current password is incorrect'
            }), 400
        current_user.set_password(new_password)
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while updating profile'
        }), 500

@bp.route('/reset_password_request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({
            'status': 'error',
            'message': 'Email is required'
        }), 400
        
    user = User.query.filter_by(email=data['email']).first()
    if user:
        send_password_reset_email(user)
    
    # Always return success to prevent email enumeration
    return jsonify({
        'status': 'success',
        'message': 'Password reset instructions sent if email exists'
    })

@bp.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    if not data or not data.get('password'):
        return jsonify({
            'status': 'error',
            'message': 'New password is required'
        }), 400
    
    user_id = verify_reset_token(token)
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'Invalid or expired reset token'
        }), 400
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404
        
    user.set_password(data['password'])
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Password has been reset successfully'
    })

@bp.route('/verify_reset_token/<token>', methods=['GET'])
def verify_token(token):
    user_id = verify_reset_token(token)
    if not user_id:
        return jsonify({
            'status': 'error',
            'message': 'Invalid or expired reset token'
        }), 400
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404
        
    return jsonify({
        'status': 'success',
        'message': 'Token is valid',
        'email': user.email
    })

@bp.route('/delete_account', methods=['DELETE'])
@login_required
def delete_account():
    data = request.get_json()
    if not data or not current_user.check_password(data.get('password', '')):
        return jsonify({
            'status': 'error',
            'message': 'Invalid password'
        }), 400
        
    try:
        # Delete associated data
        LoginLog.query.filter_by(user_id=current_user.id).delete()
        user_id = current_user.id
        logout_user()  # Log the user out before deleting
        
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Account deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting account: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while deleting account'
        }), 500

@bp.route('/check-auth', methods=['GET'])
def check_auth():
    """Check if the user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'status': 'success',
            'authenticated': True,
            'username': current_user.username
        })
    else:
        return jsonify({
            'status': 'success',
            'authenticated': False
        }), 401
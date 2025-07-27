from flask import Blueprint

bp = Blueprint('main', __name__, url_prefix='/api')

from app.main import routes  # Import routes after bp is defined
# app/jobs/__init__.py
from flask import Blueprint

bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')

from app.jobs import routes  # Import routes after bp is defined
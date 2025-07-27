from flask import Blueprint, redirect, url_for
from flask_login import login_required
from app.main import bp

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    return redirect(url_for('jobs.index'))
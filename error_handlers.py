from flask import jsonify, flash, redirect, url_for, request
from colbuilder.exceptions import (
    ColbuilderError,
    SequenceGenerationError,
    GeometryGenerationError,
    TopologyGenerationError,
    ConfigurationError,
    SystemError
)

def register_error_handlers(app):
    @app.errorhandler(ColbuilderError)
    def handle_colbuilder_error(error):
        """Handle all Colbuilder-specific errors"""
        # Log the error using the built-in logging mechanism
        error.log_error()
        
        # Create user-friendly message
        user_message = error.detail.message
        if error.detail.suggestions:
            user_message += "\n\nSuggested actions:\n"
            user_message += "\n".join(f"- {s}" for s in error.detail.suggestions)
            
        # For API requests, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'error': True,
                'message': user_message,
                'error_code': error.detail.error_code,
                'category': error.detail.category.name,
                'severity': error.detail.severity.name,
                'docs_url': error.detail.docs_url
            }), 400
            
        # For web requests, flash message and redirect
        flash(user_message, 'error')
        
        # Update job status if this is a job-related error
        job_id = request.form.get('job_id')
        if job_id:
            try:
                job = Job.query.get(job_id)
                if job:
                    job.status = 'ERROR'
                    job.error_message = user_message
                    db.session.commit()
            except Exception as e:
                app.logger.error(f"Failed to update job status: {e}")
        
        return redirect(url_for('index'))

    # Optional: Add specific handlers for different error types if needed
    @app.errorhandler(SequenceGenerationError)
    def handle_sequence_error(error):
        """Handle sequence generation specific errors"""
        return handle_colbuilder_error(error)

    @app.errorhandler(GeometryGenerationError)
    def handle_geometry_error(error):
        """Handle geometry generation specific errors"""
        return handle_colbuilder_error(error)

    @app.errorhandler(TopologyGenerationError)
    def handle_topology_error(error):
        """Handle topology generation specific errors"""
        return handle_colbuilder_error(error)

    @app.errorhandler(ConfigurationError)
    def handle_config_error(error):
        """Handle configuration specific errors"""
        return handle_colbuilder_error(error)

    @app.errorhandler(SystemError)
    def handle_system_error(error):
        """Handle system level errors"""
        return handle_colbuilder_error(error)
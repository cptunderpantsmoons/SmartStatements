"""
API Endpoint for Processing Financial Statements
Vercel serverless function for AI workflow execution
"""
import json
import os
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pydantic import ValidationError

from ..utils.workflow_engine import WorkflowEngine
from ..config.settings import config
from .models import (
    ProcessRequest, ProcessResponse, StatusResponse, 
    ErrorResponse, HealthResponse, ReportsResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize workflow engine
workflow_engine = WorkflowEngine()


def handle_validation_error(e: ValidationError):
    """Convert Pydantic validation errors to HTTP response"""
    errors = []
    for error in e.errors():
        errors.append({
            'field': '.'.join(str(x) for x in error['loc']),
            'message': error['msg']
        })
    
    return jsonify({
        'error': 'Validation failed',
        'details': errors,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 400


@app.route('/api/process', methods=['POST'])
@limiter.limit("10 per hour")
def process_file():
    """Main processing endpoint for financial statements"""
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            logger.warning(f"Process request from {request.remote_addr}: No data provided")
            return jsonify({
                'error': 'No data provided',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 400
        
        # Validate request using Pydantic
        try:
            req = ProcessRequest(**data)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return handle_validation_error(e)
        
        # Log processing start
        logger.info(
            f"Starting file processing",
            extra={
                'user_id': req.user_id,
                'year': req.year,
                'file_path': req.file_path
            }
        )
        
        # Process file
        result = workflow_engine.process_file(req.file_path, req.user_id, req.year)
        
        # Log result
        logger.info(
            f"Processing completed with status: {result.get('status')}",
            extra={'report_id': result.get('report_id')}
        )
        
        return jsonify(result), 200 if result.get('status') == 'success' else 207
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Processing failed: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/api/status/<report_id>', methods=['GET'])
@limiter.limit("30 per hour")
def get_status(report_id: str):
    """Get processing status for a report"""
    try:
        logger.info(f"Fetching status for report {report_id}")
        status = workflow_engine.get_processing_status(report_id)
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Status check error for {report_id}: {str(e)}")
        return jsonify({
            'error': f'Failed to get status: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/api/reports/<user_id>', methods=['GET'])
@limiter.limit("30 per hour")
def get_user_reports(user_id: str):
    """Get all reports for a user"""
    try:
        logger.info(f"Fetching reports for user {user_id}")
        reports = workflow_engine.get_user_reports(user_id)
        
        completed = sum(1 for r in reports if r.get('status') == 'completed')
        failed = sum(1 for r in reports if r.get('status') == 'failed')
        
        return jsonify({
            'reports': reports,
            'total_count': len(reports),
            'completed_count': completed,
            'failed_count': failed
        }), 200
        
    except Exception as e:
        logger.error(f"Reports fetch error for user {user_id}: {str(e)}")
        return jsonify({
            'error': f'Failed to get reports: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/api/metrics', methods=['GET'])
@limiter.limit("60 per hour")
def get_metrics():
    """Get system metrics"""
    try:
        logger.info("Fetching system metrics")
        metrics = workflow_engine.metrics.get_metrics_summary()
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Metrics fetch error: {str(e)}")
        return jsonify({
            'error': f'Failed to get metrics: {str(e)}',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/api/health', methods=['GET'])
@limiter.limit("100 per hour")
def health_check():
    """Health check endpoint"""
    try:
        services_status = {
            'database': 'operational',
            'ai_models': 'operational',
            'cache': 'operational'
        }
        
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'services': services_status
        }), 200
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/api/start-monitoring', methods=['POST'])
def start_monitoring():
    """Start file monitoring"""
    try:
        # Define callback for file processing
        def file_callback(file_path: str, file_info: Dict[str, Any]):
            # Extract user_id from request or use default
            user_id = request.json.get('user_id', 'system') if request.json else 'system'
            
            # Process the file
            workflow_engine.process_file(file_path, user_id, file_info.get('year', 2025))
        
        workflow_engine.start_file_monitoring()
        
        return jsonify({
            'status': 'monitoring_started',
            'input_directory': config.input_directory
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to start monitoring: {str(e)}'
        }), 500


@app.route('/api/stop-monitoring', methods=['POST'])
def stop_monitoring():
    """Stop file monitoring"""
    try:
        workflow_engine.stop_file_monitoring()
        
        return jsonify({
            'status': 'monitoring_stopped'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to stop monitoring: {str(e)}'
        }), 500


@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Test email configuration"""
    try:
        result = workflow_engine.alert_system.test_email_configuration()
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Email test failed: {str(e)}'
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get system configuration (public info only)"""
    try:
        public_config = {
            'max_file_size_mb': config.max_file_size_mb,
            'max_pages_per_pdf': config.max_pages_per_pdf,
            'supported_file_types': ['.pdf', '.xlsx', '.xls'],
            'input_directory': config.input_directory,
            'models': {
                'gemini_pro': config.gemini_pro_model,
                'gemini_flash': config.gemini_flash_model,
                'grok': config.grok_model
            },
            'thresholds': {
                'auto_map': config.auto_map_threshold,
                'review': config.review_threshold
            }
        }
        
        return jsonify(public_config), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get config: {str(e)}'
        }), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error'
    }), 500


# Vercel serverless entry point
def handler(environ, start_response):
    """Vercel serverless function handler (WSGI compatible)"""
    return app(environ, start_response)


# Local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

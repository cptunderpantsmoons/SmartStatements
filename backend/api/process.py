"""
API Endpoint for Processing Financial Statements
Vercel serverless function for AI workflow execution
"""
import json
import os
from typing import Dict, Any
from flask import Flask, request, jsonify

from ..utils.workflow_engine import WorkflowEngine
from ..config.settings import config

# Initialize Flask app
app = Flask(__name__)

# Initialize workflow engine
workflow_engine = WorkflowEngine()


@app.route('/api/process', methods=['POST'])
def process_file():
    """Main processing endpoint for financial statements"""
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided'
            }), 400
        
        # Extract required parameters
        file_path = data.get('file_path')
        user_id = data.get('user_id')
        year = data.get('year', 2025)
        
        if not file_path or not user_id:
            return jsonify({
                'error': 'Missing required parameters: file_path, user_id'
            }), 400
        
        # Validate file exists
        if not os.path.exists(file_path):
            return jsonify({
                'error': f'File not found: {file_path}'
            }), 404
        
        # Process file
        result = workflow_engine.process_file(file_path, user_id, year)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Processing failed: {str(e)}'
        }), 500


@app.route('/api/status/<report_id>', methods=['GET'])
def get_status(report_id: str):
    """Get processing status for a report"""
    try:
        status = workflow_engine.get_processing_status(report_id)
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get status: {str(e)}'
        }), 500


@app.route('/api/reports/<user_id>', methods=['GET'])
def get_user_reports(user_id: str):
    """Get all reports for a user"""
    try:
        reports = workflow_engine.get_user_reports(user_id)
        return jsonify({
            'reports': reports
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get reports: {str(e)}'
        }), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get system metrics"""
    try:
        metrics = workflow_engine.metrics.get_metrics_summary()
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get metrics: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': workflow_engine.db_manager.get_system_metrics(),
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
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
def handler(request):
    """Vercel serverless function handler"""
    with app.request_context(request):
        return app.full_dispatch_request(request)


# Local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

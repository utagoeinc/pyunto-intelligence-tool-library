"""
Flask extension for Pyunto Intelligence API integration.
This module provides a Flask extension for easy integration with Pyunto Intelligence.
"""

import os
import base64
import json
import requests
from functools import wraps
from werkzeug.local import LocalProxy
from flask import current_app, _app_ctx_stack, request, jsonify

# Default configuration
DEFAULT_CONFIG = {
    'PYUNTO_API_URL': 'https://a.pyunto.com/api/i/v1',
    'PYUNTO_API_TIMEOUT': 30,  # seconds
    'PYUNTO_DEFAULT_ASSISTANT_ID': None,
}

class PyuntoIntelligence:
    """Flask extension for Pyunto Intelligence API."""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the extension with the Flask application."""
        # Set default configuration
        for key, value in DEFAULT_CONFIG.items():
            app.config.setdefault(key, value)

        # Add extension to Flask application
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['pyunto_intelligence'] = self

        # Register teardown function
        app.teardown_appcontext(self.teardown)

    def teardown(self, exception):
        """Clean up resources when the application context ends."""
        ctx = _app_ctx_stack.top
        if hasattr(ctx, 'pyunto_intelligence_client'):
            del ctx.pyunto_intelligence_client

    @property
    def client(self):
        """Return a PyuntoClient instance for the current application context."""
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'pyunto_intelligence_client'):
                ctx.pyunto_intelligence_client = PyuntoClient(
                    api_key=current_app.config.get('PYUNTO_API_KEY'),
                    api_url=current_app.config.get('PYUNTO_API_URL'),
                    timeout=current_app.config.get('PYUNTO_API_TIMEOUT'),
                    default_assistant_id=current_app.config.get('PYUNTO_DEFAULT_ASSISTANT_ID')
                )
            return ctx.pyunto_intelligence_client

    def require_api_key(self, f):
        """Decorator to check if Pyunto API key is configured."""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_app.config.get('PYUNTO_API_KEY'):
                return jsonify({
                    'error': {
                        'code': 'missing_api_key',
                        'message': 'Pyunto Intelligence API key is not configured'
                    }
                }), 500
            return f(*args, **kwargs)
        return decorated

    def process_route(self, rule=None, **options):
        """Create a route for processing data with Pyunto Intelligence.
        
        Example:
            @pyunto.process_route('/analyze-image', methods=['POST'])
            def analyze_image(result):
                # result contains the processed data from Pyunto
                return jsonify(result)
        """
        def decorator(f):
            endpoint = options.pop('endpoint', None)
            if rule is None:
                return f
            
            @self.require_api_key
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Get content type and data from request
                content_type = request.content_type or ''
                
                # Process different content types
                if 'application/json' in content_type:
                    request_data = request.get_json(silent=True) or {}
                    assistant_id = request_data.get('assistantId', current_app.config.get('PYUNTO_DEFAULT_ASSISTANT_ID'))
                    data_type = request_data.get('type', 'image')
                    data = request_data.get('data', '')
                    mime_type = request_data.get('mimeType', '')
                else:
                    return jsonify({
                        'error': {
                            'code': 'invalid_content_type',
                            'message': 'Unsupported content type'
                        }
                    }), 415
                
                # Call Pyunto API
                try:
                    if data_type == 'image':
                        result = self.client.process_image(
                            assistant_id=assistant_id,
                            image_data=data,
                            mime_type=mime_type
                        )
                    elif data_type == 'text':
                        result = self.client.process_text(
                            assistant_id=assistant_id,
                            text_data=data,
                            mime_type=mime_type
                        )
                    else:
                        return jsonify({
                            'error': {
                                'code': 'invalid_data_type',
                                'message': f'Unsupported data type: {data_type}'
                            }
                        }), 400
                except PyuntoError as e:
                    return jsonify({
                        'error': {
                            'code': e.code,
                            'message': str(e)
                        }
                    }), e.status_code
                
                # Pass the result to the decorated function
                return f(result, *args, **kwargs)
            
            current_app.add_url_rule(rule, endpoint, wrapper, **options)
            return f
        
        return decorator

class PyuntoError(Exception):
    """Exception raised for Pyunto Intelligence API errors."""
    
    def __init__(self, message, code='api_error', status_code=400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class PyuntoClient:
    """Client for interacting with the Pyunto Intelligence API."""
    
    def __init__(self, api_key=None, api_url=None, timeout=30, default_assistant_id=None):
        self.api_key = api_key
        self.api_url = api_url or DEFAULT_CONFIG['PYUNTO_API_URL']
        self.timeout = timeout
        self.default_assistant_id = default_assistant_id
    
    def _make_request(self, data):
        """Make a request to the Pyunto Intelligence API."""
        if not self.api_key:
            raise PyuntoError("API key is required", code='missing_api_key', status_code=401)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Check for API errors
            if 'error' in result:
                raise PyuntoError(
                    result['error'].get('message', 'Unknown API error'),
                    code=result['error'].get('code', 'api_error'),
                    status_code=400
                )
            
            return result
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        raise PyuntoError(
                            error_data['error'].get('message', str(e)),
                            code=error_data['error'].get('code', 'request_error'),
                            status_code=e.response.status_code
                        )
                except (ValueError, KeyError):
                    pass
            
            # Default error handling
            status_code = getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
            raise PyuntoError(str(e), code='request_error', status_code=status_code)
    
    def process_image(self, image_data, assistant_id=None, mime_type='image/jpeg'):
        """Process an image with Pyunto Intelligence.
        
        Args:
            image_data: Base64-encoded string of the image
            assistant_id: ID of the assistant to use (optional if default is set)
            mime_type: MIME type of the image
            
        Returns:
            dict: The processing results from Pyunto Intelligence
        """
        assistant_id = assistant_id or self.default_assistant_id
        if not assistant_id:
            raise PyuntoError("Assistant ID is required", code='missing_assistant_id', status_code=400)
        
        request_data = {
            'assistantId': assistant_id,
            'type': 'image',
            'data': image_data,
            'mimeType': mime_type
        }
        
        return self._make_request(request_data)
    
    def process_text(self, text_data, assistant_id=None, mime_type='text/plain'):
        """Process text with Pyunto Intelligence.
        
        Args:
            text_data: Base64-encoded string of the text
            assistant_id: ID of the assistant to use (optional if default is set)
            mime_type: MIME type of the text
            
        Returns:
            dict: The processing results from Pyunto Intelligence
        """
        assistant_id = assistant_id or self.default_assistant_id
        if not assistant_id:
            raise PyuntoError("Assistant ID is required", code='missing_assistant_id', status_code=400)
        
        request_data = {
            'assistantId': assistant_id,
            'type': 'text',
            'data': text_data,
            'mimeType': mime_type
        }
        
        return self._make_request(request_data)


# Create a proxy for the current PyuntoIntelligence instance
def _get_pyunto_intelligence():
    """Get the current PyuntoIntelligence instance."""
    if current_app:
        return current_app.extensions.get('pyunto_intelligence')
    raise RuntimeError('Working outside of application context')

pyunto = LocalProxy(_get_pyunto_intelligence)

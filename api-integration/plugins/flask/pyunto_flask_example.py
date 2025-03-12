"""
Example Flask application using the Pyunto Intelligence extension.
This demonstrates how to use the Pyunto Intelligence extension with Flask.
"""

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import base64
from pyunto_flask import PyuntoIntelligence

# Create Flask application
app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key'),
    PYUNTO_API_KEY=os.environ.get('PYUNTO_API_KEY'),
    PYUNTO_DEFAULT_ASSISTANT_ID=os.environ.get('PYUNTO_DEFAULT_ASSISTANT_ID'),
    UPLOAD_FOLDER='uploads',
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10 MB max upload size
)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Pyunto Intelligence extension
pyunto = PyuntoIntelligence(app)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if a filename has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads and process them with Pyunto Intelligence."""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If no file was selected
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        # Check file type
        if file and allowed_file(file.filename):
            # Secure filename to prevent path traversal
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read file as base64
            with open(filepath, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            try:
                # Get assistant ID from form or use default
                assistant_id = request.form.get('assistant_id') or app.config['PYUNTO_DEFAULT_ASSISTANT_ID']
                
                # Process image with Pyunto Intelligence
                result = pyunto.client.process_image(
                    image_data=image_data,
                    assistant_id=assistant_id,
                    mime_type=file.content_type
                )
                
                # Return results page
                return render_template('results.html', 
                                      filename=filename, 
                                      result=result,
                                      image_path=url_for('uploaded_file', filename=filename))
            except Exception as e:
                flash(f'Error processing image: {str(e)}')
                return redirect(request.url)
        else:
            flash('File type not allowed')
            return redirect(request.url)
            
    # GET request - show upload form
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Create API endpoint using the process_route decorator
@pyunto.process_route('/api/analyze', methods=['POST'])
def analyze_api(result):
    """API endpoint for analyzing data with Pyunto Intelligence."""
    # The result is pre-processed by the extension
    return jsonify(result)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page for configuring Pyunto Intelligence."""
    if request.method == 'POST':
        app.config['PYUNTO_API_KEY'] = request.form.get('api_key')
        app.config['PYUNTO_DEFAULT_ASSISTANT_ID'] = request.form.get('assistant_id')
        flash('Settings updated successfully')
        return redirect(url_for('settings'))
    
    return render_template('settings.html',
                          api_key=app.config.get('PYUNTO_API_KEY', ''),
                          assistant_id=app.config.get('PYUNTO_DEFAULT_ASSISTANT_ID', ''))

if __name__ == '__main__':
    app.run(debug=True)

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
from config import Config

from services.csv_processor import CSVProcessor

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the home page with file upload form."""
    return render_template('index.html')

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initial analysis."""
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
        
    file = request.files['file']
    
    # Check if the file was selected
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    # Check if the file extension is allowed
    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload a CSV file.', 'error')
        return redirect(request.url)
    
    try:
        # Process the uploaded file
        csv_processor = CSVProcessor(current_app.config['UPLOAD_FOLDER'])
        file_path = csv_processor.save_file(file)
        
        # Analyze the CSV file
        file_analysis = csv_processor.read_csv(file_path)
        
        # Start a validation session
        return redirect(url_for('validation.start_validation', 
                              filename=os.path.basename(file_path)))
        
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(request.url)

@main_bp.route('/analyze', methods=['POST'])
def analyze_file():
    """Analyze a CSV file without validation and return basic statistics."""
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    # Check if the file was selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if the file extension is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload a CSV file.'}), 400
    
    try:
        # Process the uploaded file for analysis only
        csv_processor = CSVProcessor(current_app.config['UPLOAD_FOLDER'])
        
        # No need to save the file for quick analysis
        file_analysis = csv_processor.read_csv(file)
        
        return jsonify(file_analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
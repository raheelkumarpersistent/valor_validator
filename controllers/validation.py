from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
import os
import json
import time
from werkzeug.utils import secure_filename

# from app import db
from extensions import db
from models.rule import ValidationSession, ValidationResult, Rule
from services.csv_processor import CSVProcessor
from services.validator import ValidationEngine
from services.matcher import ColumnMatcher

validation_bp = Blueprint('validation', __name__)

@validation_bp.route('/start', methods=['GET'])
def start_validation():
    """Start a validation session and show initial CSV analysis."""
    filename = request.args.get('filename')
    if not filename:
        flash('No filename provided', 'error')
        return redirect(url_for('main.index'))
    
    # Get path to the uploaded file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Make sure the file exists
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Analyze the CSV file
        csv_processor = CSVProcessor(current_app.config['UPLOAD_FOLDER'])
        file_analysis = csv_processor.read_csv(file_path)
        
        # Match columns to validation rules
        matcher = ColumnMatcher()
        column_rule_map = matcher.match_columns(file_analysis['column_names'])
        
        # Create a validation session
        validator = ValidationEngine()
        session = validator.create_validation_session(filename)
        
        # Get all active rules for the dropdown
        rules = Rule.query.filter_by(is_active=True).order_by(Rule.name).all()
        
        return render_template('validation/start.html', 
                             filename=filename,
                             file_analysis=file_analysis,
                             column_rule_map=column_rule_map,
                             session_id=session.id,
                             rules=rules)  # Pass rules to the template
                             
    except Exception as e:
        flash(f'Error preparing validation: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@validation_bp.route('/execute', methods=['POST'])
def execute_validation():
    """Execute the validation process."""
    session_id = request.form.get('session_id')
    filename = request.form.get('filename')
    
    if not session_id or not filename:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Get path to the uploaded file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Make sure the file exists
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Get column-rule mappings from the form
        column_rules = {}
        for key, value in request.form.items():
            if key.startswith('column_rule_'):
                column_name = key.replace('column_rule_', '')
                if value and value != 'none':
                    rule_id = int(value)
                    rule = Rule.query.get(rule_id)
                    if rule:
                        column_rules[column_name] = {'rule': rule, 'match_score': 100}
        
        # Update the session status
        session = ValidationSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Validation session not found'}), 404
            
        session.status = 'running'
        db.session.commit()
        
        # Process the CSV file in batches and validate
        csv_processor = CSVProcessor(current_app.config['UPLOAD_FOLDER'])
        validator = ValidationEngine()
        
        def validate_batch(batch_df, start_row):
            return validator.validate_dataframe(batch_df, column_rules, session_id, start_row)
        
        # Start validation
        summary = csv_processor.validate_with_iterator(file_path, validate_batch)
        
        # Update the session with results
        validator.finalize_validation(session_id, summary)
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'summary': summary
        })
        
    except Exception as e:
        # Update session status on error
        session = ValidationSession.query.get(session_id)
        if session:
            session.status = 'failed'
            session.summary = json.dumps({'error': str(e)})
            db.session.commit()
            
        return jsonify({'error': str(e)}), 500

@validation_bp.route('/status/<int:session_id>', methods=['GET'])
def validation_status(session_id):
    """Get the status of a validation session."""
    session = ValidationSession.query.get_or_404(session_id)
    
    return jsonify({
        'id': session.id,
        'status': session.status,
        'filename': session.filename,
        'total_rows': session.total_rows,
        'valid_rows': session.valid_rows,
        'invalid_rows': session.invalid_rows,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'completed_at': session.completed_at.isoformat() if session.completed_at else None,
        'summary': session.get_summary()
    })

@validation_bp.route('/results/<int:session_id>', methods=['GET'])
def validation_results(session_id):
    """Show validation results for a session."""
    # Get the validation session
    session = ValidationSession.query.get_or_404(session_id)
    
    # For AJAX requests, return results as JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        
        validator = ValidationEngine()
        results = validator.get_validation_results(session_id, page, per_page)
        
        # Convert results to JSON-serializable format
        results_data = {
            'items': [
                {
                    'id': item.id,
                    'row_number': item.row_number,
                    'column_name': item.column_name,
                    'rule_name': item.rule.name if item.rule else None,
                    'message': item.message,
                    'value': item.value
                }
                for item in results['items']
            ],
            'page': results['page'],
            'pages': results['pages'],
            'total': results['total'],
            'has_next': results['has_next'],
            'has_prev': results['has_prev']
        }
        
        return jsonify(results_data)
    
    # For regular requests, render the results page
    return render_template('validation/results.html', session=session)

@validation_bp.route('/export/<int:session_id>', methods=['GET'])
def export_results(session_id):
    """Export validation results as JSON."""
    session = ValidationSession.query.get_or_404(session_id)
    
    # Get all invalid results for the session
    results = ValidationResult.query.filter_by(
        session_id=session_id, 
        is_valid=False
    ).order_by(
        ValidationResult.row_number
    ).all()
    
    # Format results for export
    results_data = {
        'session': {
            'id': session.id,
            'filename': session.filename,
            'total_rows': session.total_rows,
            'valid_rows': session.valid_rows,
            'invalid_rows': session.invalid_rows,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
        },
        'results': [
            {
                'row_number': result.row_number,
                'column_name': result.column_name,
                'rule_name': result.rule.name if result.rule else None,
                'message': result.message,
                'value': result.value
            }
            for result in results
        ]
    }
    
    return jsonify(results_data)

@validation_bp.route('/history', methods=['GET'])
def validation_history():
    """Show validation history."""
    sessions = ValidationSession.query.order_by(ValidationSession.started_at.desc()).all()
    return render_template('validation/history.html', sessions=sessions)

@validation_bp.route('/suggest-rule', methods=['POST'])
def suggest_rule():
    """Suggest validation rules for a column based on its name and sample data."""
    column_name = request.json.get('column_name')
    sample_data = request.json.get('sample_data', [])
    
    if not column_name:
        return jsonify({'error': 'Column name is required'}), 400
    
    # Get rule suggestions based on column name
    matcher = ColumnMatcher()
    suggestions = matcher.suggest_rules(column_name)
    
    # Format suggestions for response
    suggestions_data = [
        {
            'id': suggestion['rule'].id,
            'name': suggestion['rule'].name,
            'description': suggestion['rule'].description,
            'match_score': suggestion['match_score']
        }
        for suggestion in suggestions
    ]
    
    return jsonify(suggestions_data)
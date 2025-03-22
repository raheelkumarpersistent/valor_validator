from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json

# from app import db
from extensions import db
from models.rule import Rule

rules_bp = Blueprint('rules', __name__)

@rules_bp.route('/')
def list_rules():
    """List all validation rules."""
    rules = Rule.query.order_by(Rule.is_system.desc(), Rule.name).all()
    print(f"Number of rules found: {len(rules)}")
    return render_template('rules/list.html', rules=rules)

@rules_bp.route('/create', methods=['GET', 'POST'])
def create_rule():
    """Create a new validation rule."""
    if request.method == 'POST':
        try:
            # Extract rule data from form
            rule_data = {
                'name': request.form.get('name'),
                'column_pattern': request.form.get('column_pattern'),
                'rule_type': request.form.get('rule_type'),
                'description': request.form.get('description', ''),
                'is_active': request.form.get('is_active') == 'on',
                'priority': int(request.form.get('priority', 100)),
                'is_system': False  # User-created rules are never system rules
            }
            
            # Extract parameters based on rule type
            parameters = {}
            rule_type = rule_data['rule_type']
            
            # Common parameters
            parameters['allow_null'] = request.form.get('allow_null') == 'on'
            
            if rule_type == 'data_type':
                parameters['type'] = request.form.get('data_type')
                
            elif rule_type == 'range':
                if request.form.get('min'):
                    parameters['min'] = float(request.form.get('min'))
                if request.form.get('max'):
                    parameters['max'] = float(request.form.get('max'))
                    
            elif rule_type == 'pattern':
                parameters['pattern'] = request.form.get('pattern')
                parameters['error_message'] = request.form.get('error_message', '')
                
            elif rule_type == 'enumeration':
                # Split comma-separated values and strip whitespace
                values = [v.strip() for v in request.form.get('values', '').split(',') if v.strip()]
                parameters['values'] = values
                parameters['case_insensitive'] = request.form.get('case_insensitive') == 'on'
                
            elif rule_type == 'date_format':
                parameters['format'] = request.form.get('date_format')
                
            elif rule_type == 'length':
                if request.form.get('min_length'):
                    parameters['min'] = int(request.form.get('min_length'))
                if request.form.get('max_length'):
                    parameters['max'] = int(request.form.get('max_length'))
                    
            elif rule_type == 'cross_field':
                parameters['compare_with'] = request.form.get('compare_with')
                parameters['operator'] = request.form.get('operator')
            
            # Create the rule
            rule = Rule(
                name=rule_data['name'],
                column_pattern=rule_data['column_pattern'],
                rule_type=rule_data['rule_type'],
                parameters=parameters,
                description=rule_data['description'],
                is_active=rule_data['is_active'],
                priority=rule_data['priority']
            )
            
            db.session.add(rule)
            db.session.commit()
            
            flash(f'Rule "{rule.name}" created successfully', 'success')
            return redirect(url_for('rules.list_rules'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating rule: {str(e)}', 'error')
            
    return render_template('rules/create.html')

@rules_bp.route('/<int:rule_id>', methods=['GET'])
def view_rule(rule_id):
    """View a single validation rule."""
    rule = Rule.query.get_or_404(rule_id)
    return render_template('rules/view.html', rule=rule)

@rules_bp.route('/<int:rule_id>/edit', methods=['GET', 'POST'])
def edit_rule(rule_id):
    """Edit an existing validation rule."""
    rule = Rule.query.get_or_404(rule_id)
    
    # Do not allow editing system rules
    if rule.is_system:
        flash('System rules cannot be modified', 'error')
        return redirect(url_for('rules.view_rule', rule_id=rule.id))
    
    if request.method == 'POST':
        try:
            # Update basic rule properties
            rule.name = request.form.get('name')
            rule.column_pattern = request.form.get('column_pattern')
            rule.description = request.form.get('description', '')
            rule.is_active = request.form.get('is_active') == 'on'
            rule.priority = int(request.form.get('priority', 100))
            
            # Extract parameters based on rule type
            parameters = {}
            rule_type = rule.rule_type  # Cannot change rule type after creation
            
            # Common parameters
            parameters['allow_null'] = request.form.get('allow_null') == 'on'
            
            if rule_type == 'data_type':
                parameters['type'] = request.form.get('data_type')
                
            elif rule_type == 'range':
                if request.form.get('min'):
                    parameters['min'] = float(request.form.get('min'))
                if request.form.get('max'):
                    parameters['max'] = float(request.form.get('max'))
                    
            elif rule_type == 'pattern':
                parameters['pattern'] = request.form.get('pattern')
                parameters['error_message'] = request.form.get('error_message', '')
                
            elif rule_type == 'enumeration':
                # Split comma-separated values and strip whitespace
                values = [v.strip() for v in request.form.get('values', '').split(',') if v.strip()]
                parameters['values'] = values
                parameters['case_insensitive'] = request.form.get('case_insensitive') == 'on'
                
            elif rule_type == 'date_format':
                parameters['format'] = request.form.get('date_format')
                
            elif rule_type == 'length':
                if request.form.get('min_length'):
                    parameters['min'] = int(request.form.get('min_length'))
                if request.form.get('max_length'):
                    parameters['max'] = int(request.form.get('max_length'))
                    
            elif rule_type == 'cross_field':
                parameters['compare_with'] = request.form.get('compare_with')
                parameters['operator'] = request.form.get('operator')
            
            # Update the rule parameters
            rule.parameters = json.dumps(parameters)
            
            db.session.commit()
            
            flash(f'Rule "{rule.name}" updated successfully', 'success')
            return redirect(url_for('rules.view_rule', rule_id=rule.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating rule: {str(e)}', 'error')
    
    # For GET request, load the rule data
    return render_template('rules/edit.html', rule=rule, parameters=rule.get_parameters())

@rules_bp.route('/<int:rule_id>/delete', methods=['POST'])
def delete_rule(rule_id):
    """Delete a validation rule."""
    rule = Rule.query.get_or_404(rule_id)
    
    # Do not allow deleting system rules
    if rule.is_system:
        flash('System rules cannot be deleted', 'error')
        return redirect(url_for('rules.list_rules'))
    
    try:
        db.session.delete(rule)
        db.session.commit()
        flash(f'Rule "{rule.name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting rule: {str(e)}', 'error')
    
    return redirect(url_for('rules.list_rules'))

@rules_bp.route('/export', methods=['GET'])
def export_rules():
    """Export all user-created rules as JSON."""
    rules = Rule.query.filter_by(is_system=False).all()
    
    rules_data = []
    for rule in rules:
        rules_data.append({
            'name': rule.name,
            'description': rule.description,
            'column_pattern': rule.column_pattern,
            'rule_type': rule.rule_type,
            'parameters': rule.get_parameters(),
            'is_active': rule.is_active,
            'priority': rule.priority
        })
    
    return jsonify(rules_data)

@rules_bp.route('/import', methods=['POST'])
def import_rules():
    """Import rules from JSON."""
    if 'rules_file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('rules.list_rules'))
        
    file = request.files['rules_file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('rules.list_rules'))
    
    try:
        rules_data = json.load(file)
        imported_count = 0
        
        for rule_data in rules_data:
            # Create a new rule for each entry
            rule = Rule(
                name=rule_data['name'],
                column_pattern=rule_data['column_pattern'],
                rule_type=rule_data['rule_type'],
                parameters=rule_data['parameters'],
                description=rule_data.get('description', ''),
                is_active=rule_data.get('is_active', True),
                priority=rule_data.get('priority', 100)
            )
            
            db.session.add(rule)
            imported_count += 1
        
        db.session.commit()
        flash(f'Successfully imported {imported_count} rules', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing rules: {str(e)}', 'error')
    
    return redirect(url_for('rules.list_rules'))


# Add these new routes to your controllers/rules.py file

@rules_bp.route('/ai-generator')
def ai_rule_generator():
    """Show the AI rule generator interface."""
    return render_template('rules/ai_converter.html')

@rules_bp.route('/generate-rules-ai', methods=['POST'])
def generate_rules_ai():
    """Generate validation rules using Amazon Nova Pro API."""
    # Get the request data
    try:
        data = request.get_json()
        plaintext = data.get('plaintext', '')
        
        if not plaintext:
            return jsonify({'error': 'No plaintext rules provided'}), 400
            
        # Get API key from headers
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401
        
        # Call the Amazon Nova Pro API to generate rules
        rules = call_nova_ai(api_key, plaintext)
        
        return jsonify({'rules': rules})
    except Exception as e:
        app.logger.error(f'Error generating rules: {str(e)}')
        return jsonify({'error': str(e)}), 500

@rules_bp.route('/save-rule', methods=['POST'])
def save_rule():
    """Save a single rule from AI-generated rules."""
    try:
        rule_data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'column_pattern', 'rule_type', 'parameters']
        for field in required_fields:
            if field not in rule_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create the rule
        rule = Rule(
            name=rule_data['name'],
            column_pattern=rule_data['column_pattern'],
            rule_type=rule_data['rule_type'],
            parameters=rule_data['parameters'],
            description=rule_data.get('description', ''),
            is_active=rule_data.get('is_active', True),
            priority=rule_data.get('priority', 100),
            is_system=False
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({'success': True, 'rule_id': rule.id})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error saving rule: {str(e)}')
        return jsonify({'error': str(e)}), 500

@rules_bp.route('/save-multiple-rules', methods=['POST'])
def save_multiple_rules():
    """Save multiple rules from AI-generated rules."""
    try:
        data = request.get_json()
        rules_data = data.get('rules', [])
        
        if not rules_data:
            return jsonify({'error': 'No rules provided'}), 400
        
        saved_count = 0
        new_rules = []
        
        for rule_data in rules_data:
            # Validate required fields for each rule
            required_fields = ['name', 'column_pattern', 'rule_type', 'parameters']
            valid = True
            
            for field in required_fields:
                if field not in rule_data:
                    valid = False
                    break
                    
            if valid:
                rule = Rule(
                    name=rule_data['name'],
                    column_pattern=rule_data['column_pattern'],
                    rule_type=rule_data['rule_type'],
                    parameters=rule_data['parameters'],
                    description=rule_data.get('description', ''),
                    is_active=rule_data.get('is_active', True),
                    priority=rule_data.get('priority', 100),
                    is_system=False
                )
                new_rules.append(rule)
                saved_count += 1
        
        db.session.bulk_save_objects(new_rules)
        db.session.commit()
        
        return jsonify({'success': True, 'saved_count': saved_count})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error saving multiple rules: {str(e)}')
        return jsonify({'error': str(e)}), 500

def call_nova_ai(api_key, plaintext):
    """Call the Amazon Nova Pro API to generate rules from plaintext."""
    import requests
    import json
    
    # Split the plaintext into individual rule descriptions
    rule_descriptions = [desc.strip() for desc in plaintext.split('\n') if desc.strip()]
    
    # Define the Nova Pro API endpoint
    url = "https://api.amazonaws.com/v1/nova-pro"
    
    # Prepare the prompt for the AI model
    prompt = f"""
    Convert the following plaintext rule descriptions into structured validation rules for CSV files.
    Return the result as a JSON array of rules.

    For each rule, include:
    - name: A concise name for the rule
    - description: A detailed description of what the rule validates
    - column_pattern: A pattern to match column names this rule applies to
    - rule_type: One of [data_type, range, pattern, required, enumeration, date_format, length, cross_field]
    - parameters: An object with appropriate parameters for the rule type

    Here are the rule descriptions:
    {json.dumps(rule_descriptions)}
    
    Return only valid JSON that can be parsed directly, with no additional text.
    """
    
    # Set up headers for the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Prepare the request payload
    payload = json.dumps({
        "model": "amazon.nova-pro-v1:0-AI_Team",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })
    
    try:
        # Simulated response for demonstration - in production, uncomment the following lines
        # response = requests.post(url, headers=headers, json=payload)
        # response.raise_for_status()
        # result = response.json()
        # generated_rules = json.loads(result["choices"][0]["text"])
        
        # For demonstration purposes, generate sample rules based on plaintext
        generated_rules = simulate_ai_response(rule_descriptions)
        
        return generated_rules
    except requests.exceptions.RequestException as e:
        # Handle API request errors
        raise Exception(f"API request failed: {str(e)}")
    except ValueError as e:
        # Handle JSON parsing errors
        raise Exception(f"Failed to parse AI response: {str(e)}")

def simulate_ai_response(rule_descriptions):
    """Simulate an AI response for demonstration purposes."""
    generated_rules = []
    
    for description in rule_descriptions:
        description = description.lower()
        
        if "email" in description:
            generated_rules.append({
                "name": "Email Validation",
                "description": "Validates that text is a valid email address",
                "column_pattern": "email",
                "rule_type": "pattern",
                "parameters": {
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "error_message": "Invalid email address format",
                    "allow_null": True
                }
            })
        elif "age" in description and ("between" in description or "range" in description):
            # Extract numbers from description
            import re
            numbers = re.findall(r'\d+', description)
            min_val = int(numbers[0]) if len(numbers) > 0 else 0
            max_val = int(numbers[1]) if len(numbers) > 1 else 120
            
            generated_rules.append({
                "name": "Age Range Validation",
                "description": f"Validates that age is between {min_val} and {max_val}",
                "column_pattern": "age",
                "rule_type": "range",
                "parameters": {
                    "min": min_val,
                    "max": max_val,
                    "allow_null": True
                }
            })
        elif "phone" in description:
            generated_rules.append({
                "name": "Phone Number Validation",
                "description": "Validates that text is a valid phone number",
                "column_pattern": "phone",
                "rule_type": "pattern",
                "parameters": {
                    "pattern": r"^\+?[0-9\s\-\(\)]{7,20}$",
                    "error_message": "Invalid phone number format",
                    "allow_null": True
                }
            })
        elif "state" in description and "code" in description:
            generated_rules.append({
                "name": "US State Code Validation",
                "description": "Validates US state 2-letter code",
                "column_pattern": "state",
                "rule_type": "enumeration",
                "parameters": {
                    "values": [
                        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
                        "DC", "PR"
                    ],
                    "case_insensitive": True,
                    "allow_null": True
                }
            })
        elif "zip" in description or "postal" in description:
            generated_rules.append({
                "name": "US ZIP Code Validation",
                "description": "Validates US ZIP code format (5 digits or 5+4)",
                "column_pattern": "zip",
                "rule_type": "pattern",
                "parameters": {
                    "pattern": r"^\d{5}(?:-\d{4})?$",
                    "error_message": "Invalid ZIP code format",
                    "allow_null": True
                }
            })
        elif "required" in description:
            column_pattern = ""
            for word in description.split():
                if word not in ["required", "field", "is", "a", "the", "must", "be", "not", "null", "empty"]:
                    column_pattern = word
                    break
                    
            generated_rules.append({
                "name": f"Required {column_pattern.title() if column_pattern else 'Field'}",
                "description": f"Validates that {column_pattern if column_pattern else 'the field'} is not empty",
                "column_pattern": column_pattern if column_pattern else "field",
                "rule_type": "required",
                "parameters": {
                    "allow_null": False
                }
            })
        else:
            # Generic fallback rule
            words = description.split()
            column_pattern = next((word for word in words if word not in ["the", "a", "an", "must", "should", "be", "valid"]), "field")
            
            generated_rules.append({
                "name": f"{column_pattern.title()} Validation",
                "description": description,
                "column_pattern": column_pattern,
                "rule_type": "data_type",
                "parameters": {
                    "type": "string",
                    "allow_null": True
                }
            })
    
    return generated_rules
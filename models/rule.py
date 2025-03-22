# from app import db
from extensions import db
from datetime import datetime
import json

class Rule(db.Model):
    """Model for validation rules."""
    __tablename__ = 'rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    column_pattern = db.Column(db.String(100), nullable=False)  # Used for fuzzy matching
    rule_type = db.Column(db.String(50), nullable=False)  # Type of validation rule
    parameters = db.Column(db.Text, nullable=False)  # JSON string of rule parameters
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=100)  # Higher priority rules are applied first
    is_system = db.Column(db.Boolean, default=False)  # System rules cannot be modified by users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, column_pattern, rule_type, parameters, description=None, 
                 is_active=True, priority=100, is_system=False):
        self.name = name
        self.description = description
        self.column_pattern = column_pattern
        self.rule_type = rule_type
        
        # Store parameters as JSON string
        if isinstance(parameters, dict):
            self.parameters = json.dumps(parameters)
        else:
            self.parameters = parameters
            
        self.is_active = is_active
        self.priority = priority
        self.is_system = is_system
    
    def get_parameters(self):
        """Return parameters as a dictionary."""
        return json.loads(self.parameters)
    
    def __repr__(self):
        return f'<Rule {self.name}>'


class ValidationSession(db.Model):
    """Model for validation sessions."""
    __tablename__ = 'validation_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, running, completed, failed
    total_rows = db.Column(db.Integer, default=0)
    valid_rows = db.Column(db.Integer, default=0)
    invalid_rows = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)  # JSON string of validation summary
    
    # Relationship with validation results
    results = db.relationship('ValidationResult', backref='session', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    def get_summary(self):
        """Return summary as a dictionary if it exists."""
        if self.summary:
            return json.loads(self.summary)
        return None
    
    def __repr__(self):
        return f'<ValidationSession {self.filename} - {self.status}>'


class ValidationResult(db.Model):
    """Model for individual validation results."""
    __tablename__ = 'validation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('validation_sessions.id'), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)
    column_name = db.Column(db.String(100), nullable=False)
    matched_rule_id = db.Column(db.Integer, db.ForeignKey('rules.id'), nullable=True)
    is_valid = db.Column(db.Boolean, default=True)
    message = db.Column(db.Text, nullable=True)
    value = db.Column(db.Text, nullable=True)
    
    # Relationship with the rule
    # rule = db.relationship('Rule', backref='validation_results')
    rule = db.relationship('Rule', backref=db.backref('validation_results', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ValidationResult Row {self.row_number}, Column {self.column_name}>'
import pandas as pd
import re
import json
from datetime import datetime
import numpy as np

from extensions import db
from models.rule import ValidationSession, ValidationResult
from services.matcher import ColumnMatcher


class ValidationEngine:
    """Core validation engine that applies rules to CSV data."""
    
    def __init__(self):
        """Initialize the validation engine."""
        self.matcher = ColumnMatcher()
        self.validation_functions = {
            'data_type': self._validate_data_type,
            'range': self._validate_range,
            'pattern': self._validate_pattern,
            'required': self._validate_required,
            'unique': self._validate_unique,
            'cross_field': self._validate_cross_field,
            'enumeration': self._validate_enumeration,
            'date_format': self._validate_date_format,
            'length': self._validate_length
        }
    
    def create_validation_session(self, filename):
        """
        Create a new validation session.
        
        Args:
            filename (str): Name of the file being validated
            
        Returns:
            ValidationSession: The created session
        """
        session = ValidationSession(filename=filename, status='pending')
        db.session.add(session)
        db.session.commit()
        return session
    
    def validate_dataframe(self, df, column_rule_map, session_id, start_row=0):
        """
        Validate a pandas DataFrame using the provided rule mappings.
        
        Args:
            df (DataFrame): The pandas DataFrame to validate
            column_rule_map (dict): Mapping of column names to rules
            session_id (int): ID of the validation session
            start_row (int): Starting row number for this batch
            
        Returns:
            dict: Summary of validation results
        """
        valid_rows = 0
        invalid_rows = 0
        results = []
        
        # Track which rows are valid
        row_valid = [True] * len(df)
        
        # Apply validation for each column that has a matched rule
        for column, rule_info in column_rule_map.items():
            if column not in df.columns:
                continue
                
            rule = rule_info['rule']
            rule_type = rule.rule_type
            parameters = rule.get_parameters()
            
            # Get the validation function for this rule type
            validate_func = self.validation_functions.get(rule_type)
            if not validate_func:
                continue
            
            # Apply validation to the column
            for i, value in enumerate(df[column]):
                row_num = start_row + i
                is_valid, message = validate_func(value, parameters, df.iloc[i])
                
                if not is_valid:
                    row_valid[i] = False
                    results.append(
                        ValidationResult(
                            session_id=session_id,
                            row_number=row_num,
                            column_name=column,
                            matched_rule_id=rule.id,
                            is_valid=False,
                            message=message,
                            value=str(value) if not pd.isna(value) else None
                        )
                    )
        
        # Count valid/invalid rows
        valid_rows = sum(row_valid)
        invalid_rows = len(df) - valid_rows
        
        # Bulk insert results
        if results:
            db.session.bulk_save_objects(results)
            db.session.commit()
        
        return {
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'results': len(results)
        }
    
    def finalize_validation(self, session_id, summary):
        """
        Update the validation session with final results.
        
        Args:
            session_id (int): ID of the validation session
            summary (dict): Summary of validation results
            
        Returns:
            ValidationSession: The updated session
        """
        session = ValidationSession.query.get(session_id)
        if session:
            session.status = 'completed'
            session.total_rows = summary.get('total_rows', 0)
            session.valid_rows = summary.get('valid_rows', 0)
            session.invalid_rows = summary.get('invalid_rows', 0)
            session.completed_at = datetime.utcnow()
            session.summary = json.dumps(summary)
            db.session.commit()
        return session
    
    def get_validation_results(self, session_id, page=1, per_page=100):
        """
        Get paginated validation results for a session.
        
        Args:
            session_id (int): ID of the validation session
            page (int): Page number
            per_page (int): Results per page
            
        Returns:
            dict: Paginated validation results
        """
        results = ValidationResult.query.filter_by(
            session_id=session_id, 
            is_valid=False
        ).order_by(
            ValidationResult.row_number
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return {
            'items': results.items,
            'page': results.page,
            'pages': results.pages,
            'total': results.total,
            'has_next': results.has_next,
            'has_prev': results.has_prev
        }
    
    # Validation functions for different rule types
    
    def _validate_data_type(self, value, parameters, row=None):
        """Validate that a value matches the expected data type."""
        if pd.isna(value):
            # Check if null values are allowed
            if parameters.get('allow_null', True):
                return True, None
            return False, "Value cannot be empty"
        
        data_type = parameters.get('type')
        if not data_type:
            return True, None
            
        try:
            if data_type == 'integer':
                # Check if value can be converted to int
                if isinstance(value, str) and not value.strip():
                    return False, "Empty string is not a valid integer"
                int(value)
                return True, None
                
            elif data_type == 'float' or data_type == 'number':
                # Check if value can be converted to float
                if isinstance(value, str) and not value.strip():
                    return False, "Empty string is not a valid number"
                float(value)
                return True, None
                
            elif data_type == 'date':
                # Check if value is a valid date
                if isinstance(value, str) and not value.strip():
                    return False, "Empty string is not a valid date"
                pd.to_datetime(value)
                return True, None
                
            elif data_type == 'boolean':
                # Check if value is a valid boolean
                if isinstance(value, bool):
                    return True, None
                if isinstance(value, str):
                    value = value.lower().strip()
                    if value in ('true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'):
                        return True, None
                return False, f"Value '{value}' is not a valid boolean"
                
            elif data_type == 'string':
                # String type accepts anything that can be converted to string
                return True, None
                
            else:
                # Unknown data type
                return True, None
                
        except (ValueError, TypeError):
            return False, f"Value '{value}' is not a valid {data_type}"
    
    def _validate_range(self, value, parameters, row=None):
        """Validate that a value falls within a specified range."""
        if pd.isna(value):
            if parameters.get('allow_null', True):
                return True, None
            return False, "Value cannot be empty"
        
        # Extract range parameters
        min_value = parameters.get('min')
        max_value = parameters.get('max')
        
        try:
            # Convert to appropriate numeric type if needed
            if isinstance(value, str):
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            
            # Check minimum value
            if min_value is not None and value < min_value:
                return False, f"Value {value} is less than minimum {min_value}"
                
            # Check maximum value
            if max_value is not None and value > max_value:
                return False, f"Value {value} is greater than maximum {max_value}"
                
            return True, None
            
        except (ValueError, TypeError):
            return False, f"Value '{value}' is not a valid number for range comparison"
            
    def _validate_pattern(self, value, parameters, row=None):
        """Validate that a value matches a regex pattern."""
        if pd.isna(value):
            if parameters.get('allow_null', True):
                return True, None
            return False, "Value cannot be empty"
        
        pattern = parameters.get('pattern')
        if not pattern:
            return True, None
            
        try:
            value_str = str(value)
            if re.match(pattern, value_str):
                return True, None
            else:
                error_message = parameters.get('error_message', f"Value '{value}' does not match pattern '{pattern}'")
                return False, error_message
        except Exception as e:
            return False, f"Error applying pattern: {str(e)}"
    
    def _validate_required(self, value, parameters, row=None):
        """Validate that a value is not empty."""
        if pd.isna(value) or (isinstance(value, str) and not value.strip()):
            return False, "Value is required but was empty"
        return True, None
    
    def _validate_unique(self, value, parameters, row=None):
        """
        Note: This is a placeholder. True uniqueness validation requires 
        checking the entire column, which is handled separately.
        """
        return True, None
    
    def _validate_cross_field(self, value, parameters, row):
        """Validate based on relationship with other fields in the same row."""
        if pd.isna(value) and parameters.get('allow_null', True):
            return True, None
            
        comparison_field = parameters.get('compare_with')
        if not comparison_field or comparison_field not in row:
            return True, None
            
        operator = parameters.get('operator', 'eq')
        compare_value = row[comparison_field]
        
        # Handle null comparison value
        if pd.isna(compare_value):
            if parameters.get('allow_null_compare', True):
                return True, None
            return False, f"Comparison field '{comparison_field}' is empty"
        
        # Convert values to comparable types if possible
        try:
            if isinstance(value, str) and isinstance(compare_value, str):
                # String comparison
                pass
            elif isinstance(value, (int, float)) or isinstance(compare_value, (int, float)):
                # Numeric comparison - try to convert both to numbers
                try:
                    value = float(value) if not pd.isna(value) else None
                    compare_value = float(compare_value) if not pd.isna(compare_value) else None
                except (ValueError, TypeError):
                    return False, f"Cannot compare '{value}' with '{compare_value}' as numbers"
        except Exception:
            pass
        
        # Perform comparison based on operator
        if operator == 'eq' and value != compare_value:
            return False, f"Value '{value}' must equal '{compare_value}'"
        elif operator == 'ne' and value == compare_value:
            return False, f"Value '{value}' must not equal '{compare_value}'"
        elif operator == 'gt' and not (value > compare_value):
            return False, f"Value '{value}' must be greater than '{compare_value}'"
        elif operator == 'gte' and not (value >= compare_value):
            return False, f"Value '{value}' must be greater than or equal to '{compare_value}'"
        elif operator == 'lt' and not (value < compare_value):
            return False, f"Value '{value}' must be less than '{compare_value}'"
        elif operator == 'lte' and not (value <= compare_value):
            return False, f"Value '{value}' must be less than or equal to '{compare_value}'"
            
        return True, None
    
    def _validate_enumeration(self, value, parameters, row=None):
        """Validate that a value is one of a set of allowed values."""
        if pd.isna(value):
            if parameters.get('allow_null', True):
                return True, None
            return False, "Value cannot be empty"
        
        allowed_values = parameters.get('values', [])
        if not allowed_values:
            return True, None
            
        # Check if value is in the allowed list
        if value in allowed_values:
            return True, None
            
        # Check case-insensitive if specified
        if parameters.get('case_insensitive', False) and isinstance(value, str):
            allowed_lower = [str(v).lower() for v in allowed_values if v is not None]
            if value.lower() in allowed_lower:
                return True, None
                
        return False, f"Value '{value}' is not in the allowed list: {', '.join(map(str, allowed_values))}"
    
    def _validate_date_format(self, value, parameters, row=None):
        """Validate that a value matches a date format."""
        if pd.isna(value):
            if parameters.get('allow_null', True):
                return True, None
            return False, "Value cannot be empty"
        
        date_format = parameters.get('format')
        if not date_format:
            return True, None
            
        try:
            if isinstance(value, str):
                datetime.strptime(value, date_format)
                return True, None
            elif isinstance(value, (datetime, pd.Timestamp)):
                # Value is already a datetime
                return True, None
            else:
                return False, f"Value '{value}' is not a valid date string"
        except ValueError:
            return False, f"Value '{value}' does not match date format '{date_format}'"
    
    def _validate_length(self, value, parameters, row=None):
        """Validate the length of a string value."""
        if pd.isna(value):
            if parameters.get('allow_null', True):
                return True, None
            return False, "Value cannot be empty"
        
        # Convert to string
        value_str = str(value)
        length = len(value_str)
        
        # Check minimum length
        min_length = parameters.get('min')
        if min_length is not None and length < min_length:
            return False, f"Value length ({length}) is less than minimum length ({min_length})"
            
        # Check maximum length
        max_length = parameters.get('max')
        if max_length is not None and length > max_length:
            return False, f"Value length ({length}) is greater than maximum length ({max_length})"
            
        return True, None
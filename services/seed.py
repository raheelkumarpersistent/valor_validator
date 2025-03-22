# from app import db
from extensions import db
from models.rule import Rule


def seed_default_rules():
    """Seed the database with default validation rules."""
    default_rules = [
        # Text validation rules
        Rule(
            name="Required Text",
            description="Validates that a text field is not empty",
            column_pattern="required",
            rule_type="required",
            parameters={"allow_null": False},
            is_system=True,
            priority=200
        ),
        Rule(
            name="Email Address",
            description="Validates that text is a valid email address",
            column_pattern="email",
            rule_type="pattern",
            parameters={
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "error_message": "Invalid email address format",
                "allow_null": True
            },
            is_system=True
        ),
        Rule(
            name="Phone Number",
            description="Validates that text is a valid phone number",
            column_pattern="phone",
            rule_type="pattern",
            parameters={
                "pattern": r"^\+?[0-9\s\-\(\)]{7,20}$",
                "error_message": "Invalid phone number format",
                "allow_null": True
            },
            is_system=True
        ),
        
        # Numeric validation rules
        Rule(
            name="Integer Type",
            description="Validates that a value is an integer",
            column_pattern="integer",
            rule_type="data_type",
            parameters={"type": "integer", "allow_null": True},
            is_system=True
        ),
        Rule(
            name="Numeric Type",
            description="Validates that a value is a number",
            column_pattern="number",
            rule_type="data_type",
            parameters={"type": "float", "allow_null": True},
            is_system=True
        ),
        Rule(
            name="Positive Number",
            description="Validates that a number is greater than zero",
            column_pattern="positive",
            rule_type="range",
            parameters={"min": 0, "allow_null": True},
            is_system=True
        ),
        Rule(
            name="Percentage",
            description="Validates that a number is between 0 and 100",
            column_pattern="percentage",
            rule_type="range",
            parameters={"min": 0, "max": 100, "allow_null": True},
            is_system=True
        ),
        
        # Date validation rules
        Rule(
            name="Date Type",
            description="Validates that a value is a valid date",
            column_pattern="date",
            rule_type="data_type",
            parameters={"type": "date", "allow_null": True},
            is_system=True
        ),
        Rule(
            name="ISO Date Format",
            description="Validates that a date is in ISO format (YYYY-MM-DD)",
            column_pattern="iso_date",
            rule_type="date_format",
            parameters={"format": "%Y-%m-%d", "allow_null": True},
            is_system=True
        ),
        
        # ID and code validation rules
        Rule(
            name="US Zip Code",
            description="Validates US ZIP code format (5 digits or 5+4)",
            column_pattern="zip",
            rule_type="pattern",
            parameters={
                "pattern": r"^\d{5}(?:-\d{4})?$",
                "error_message": "Invalid ZIP code format",
                "allow_null": True
            },
            is_system=True
        ),
        Rule(
            name="US State Code",
            description="Validates US state 2-letter code",
            column_pattern="state",
            rule_type="enumeration",
            parameters={
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
            },
            is_system=True
        ),
        
        # Common column patterns
        Rule(
            name="First Name",
            description="Common validation for first name fields",
            column_pattern="first name",
            rule_type="length",
            parameters={"min": 1, "max": 50, "allow_null": True},
            is_system=True
        ),
        Rule(
            name="Last Name",
            description="Common validation for last name fields",
            column_pattern="last name",
            rule_type="length",
            parameters={"min": 1, "max": 50, "allow_null": True},
            is_system=True
        ),
        Rule(
            name="Age",
            description="Validates that age is between 0 and 120",
            column_pattern="age",
            rule_type="range",
            parameters={"min": 0, "max": 120, "allow_null": True},
            is_system=True
        ),
        Rule(
            name="Gender",
            description="Validates common gender values",
            column_pattern="gender",
            rule_type="enumeration",
            parameters={
                "values": ["Male", "Female", "Other", "Prefer not to say", "Non-binary", "M", "F", "O"],
                "case_insensitive": True,
                "allow_null": True
            },
            is_system=True
        ),
        Rule(
            name="Boolean Type",
            description="Validates that a value is a boolean (yes/no, true/false, 1/0)",
            column_pattern="boolean",
            rule_type="data_type",
            parameters={"type": "boolean", "allow_null": True},
            is_system=True
        )
    ]
    
    # Add all default rules to the database
    db.session.bulk_save_objects(default_rules)
    db.session.commit()
    
    return len(default_rules)
# CSV Validator Web Application

A Flask-based web application for validating CSV files against predefined and custom validation rules.

## Features

- **CSV Upload & Analysis**: Upload CSV files and get instant analysis of column structure and data samples
- **Intelligent Column Matching**: Automatically match CSV columns to validation rules using fuzzy matching
- **Comprehensive Validation Rules**: Support for multiple validation types:
  - Data type validation (string, integer, float, date, etc.)
  - Range validation (min/max values)
  - Pattern matching (regex validation)
  - Required fields validation
  - Enumeration validation (allowed values)
  - Date format validation
  - String length validation
  - Cross-field validation
- **Custom Rules**: Create, edit, and manage your own validation rules
- **Interactive Results**: View validation results with clear error highlighting
- **Export Options**: Export validation results in JSON or CSV format
- **Rule Management**: Import/export validation rules for reuse across projects

## Technical Stack

- **Backend**: Flask 3.0+
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: Tailwind CSS, Alpine.js
- **CSV Processing**: Pandas
- **Fuzzy Matching**: RapidFuzz

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/csv-validator.git
cd csv-validator
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Initialize the database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Run the application
```bash
python app.py
```

6. Access the application at `http://localhost:5000`

## Project Structure

- `app.py`: Main application entry point
- `config.py`: Configuration settings
- `models/`: Database models
- `services/`: Business logic services
- `controllers/`: Request handlers
- `templates/`: Jinja2 templates
- `static/`: Static assets

## Usage

### 1. Upload a CSV File

Upload your CSV file from the home page to start the validation process.

### 2. Configure Validation Rules

Once uploaded, you'll see the automatic column mapping. You can:
- Accept the automatic mappings
- Manually select validation rules for each column
- Skip validation for certain columns

### 3. Execute Validation

Click "Start Validation" to process the file against the selected rules.

### 4. Review Results

View the validation results showing:
- Summary statistics (valid/invalid rows)
- Detailed error information
- Export options for sharing results

### 5. Manage Rules

Navigate to the Rules section to:
- Create new validation rules
- Edit existing rules
- Import/export rule sets

## Development

### Adding New Validation Types

To add a new validation type:

1. Add the validation function in `services/validator.py`
2. Register the function in the `ValidationEngine` class
3. Update the rule creation form in `templates/rules/create.html`
4. Update the rule view template in `templates/rules/view.html`

### Custom CSV Processing

For custom CSV processing, extend the `CSVProcessor` class in `services/csv_processor.py`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
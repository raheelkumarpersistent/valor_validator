# CSV Validator

A powerful Flask-based web application for validating CSV files against predefined and custom validation rules with an AI-powered rule generator.

## Features

### CSV Upload & Analysis
- Upload and analyze CSV files with instant column detection
- Automatic data type inference and value sampling
- Support for large files with batch processing

### Intelligent Validation
- **Automatic Column Matching**: Uses fuzzy matching algorithms to map columns to validation rules
- **Comprehensive Rule Types**:
  - Data type validation (string, integer, float, date, boolean)
  - Range validation (min/max values for numbers and dates)
  - Pattern matching (regex validation)
  - Required fields validation
  - Enumeration validation (allowed values)
  - Date format validation
  - String length validation
  - Cross-field validation (relationships between columns)
- Real-time validation with progress indicators

### Rule Management
- Create, edit, and manage validation rules
- System rules for common validation scenarios
- Custom rules for specific business needs
- Import/export rule sets for reuse across projects

### AI-Powered Rule Generation
- Generate validation rules from plain text descriptions
- Leverages Amazon Nova Pro API for natural language understanding
- Convert descriptions like "Email addresses must be valid" into structured rules

### Results & Reporting
- Interactive results display with detailed error information
- Row and column-level validation feedback
- Export validation results in JSON or CSV format
- Validation history tracking

### User Interface
- Clean, responsive UI using Tailwind CSS
- Interactive components with Alpine.js
- Asynchronous processing with AJAX

## Technical Stack

- **Backend**: Flask 3.0+
- **Database**: SQLite (via SQLAlchemy ORM)
- **Frontend**: 
  - Tailwind CSS for styling
  - Alpine.js for client-side interactivity
  - Axios for AJAX requests
- **Data Processing**: 
  - Pandas for CSV handling
  - RapidFuzz for column name matching
- **External Services**:
  - Amazon Nova Pro API for AI rule generation

## Installation

### Prerequisites
- Python 3.12+
- pip (Python package manager)
- Git (optional)

### Setup

1. Clone the repository (or download the source code):
```bash
git clone https://github.com/yourusername/csv-validator.git
cd csv-validator
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create necessary directories:
```bash
mkdir -p uploads instance
```

### Configuration

The application uses a configuration file (`config.py`) that you can modify for different environments:

- `DevelopmentConfig`: For local development
- `ProductionConfig`: For production deployment
- `TestingConfig`: For running tests

You can set the environment by modifying the default configuration in `app.py` or by setting the environment variable:

```bash
# On Windows
set FLASK_CONFIG=development

# On macOS/Linux
export FLASK_CONFIG=development
```

## Running the Application

1. Make sure your virtual environment is activated
2. Start the Flask application:
```bash
python app.py
```
3. Access the application at `http://localhost:5000`

## Usage Guide

### 1. Upload a CSV File
- From the home page, upload your CSV file
- The application will analyze the file structure and show a preview

### 2. Configure Validation Rules
- The system will automatically match columns to appropriate rules
- You can adjust the rule mappings manually

### 3. Run Validation
- Click "Start Validation" to process the file
- Monitor progress with the real-time indicator

### 4. Review Results
- View validation summary showing valid and invalid rows
- Explore detailed error reports
- Export results in desired format

### 5. Manage Rules
- Navigate to the Rules section to view existing rules
- Create new rules manually or using the AI Generator
- Import/export rule sets

### 6. AI Rule Generation
- Go to the AI Generator page
- Enter your Amazon Nova Pro API key
- Describe validation rules in plain text
- Generate and save structured rules

## Development

### Project Structure
```
csv_validator/
├── app.py                # Main Flask application entry point
├── config.py             # Configuration settings
├── extensions.py         # Flask extensions
├── requirements.txt      # Package dependencies
├── README.md             # This file
├── instance/             # Instance-specific data (SQLite DB)
├── uploads/              # Uploaded CSV files
├── models/               # Database models
├── services/             # Business logic services
├── controllers/          # Request handlers
├── static/               # Static assets
└── templates/            # Jinja2 templates
```

### Adding New Validation Types

To add a new validation type:

1. Add the validation function in `services/validator.py`
2. Register the function in the `ValidationEngine` class
3. Update the rule creation form in `templates/rules/create.html`
4. Update the rule view template in `templates/rules/view.html`

### Custom CSV Processing

For custom CSV processing, extend the `CSVProcessor` class in `services/csv_processor.py`.

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2025 CSV Validator

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

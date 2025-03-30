# Flask Web Application

A simple web application built with Flask.

## Project Structure

```
project/
├── app.py               # Main application file
├── requirements.txt     # Python dependencies
├── static/              # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/           # HTML templates
│   ├── index.html
│   ├── about.html
│   └── contact.html
├── models/              # Data models
│   ├── __init__.py
│   └── user.py
└── routes/              # Route handlers
    ├── __init__.py
    └── main_routes.py
```

## Setup Instructions

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to `http://127.0.0.1:5000/`

## Features

- Home page
- About page
- Contact form

## Technologies Used

- Flask
- HTML/CSS
- JavaScript 

# Database Setup Script

This script helps you create the database schema for the FYP project using SQLAlchemy.

## Prerequisites

- Python 3.7 or higher
- MySQL server installed and running
- pip (Python package installer)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the database connection:
   Open `create_database.py` and modify the following variables according to your MySQL setup:
   ```python
   DB_USER = 'root'  # Replace with your MySQL username
   DB_PASSWORD = ''  # Replace with your MySQL password
   DB_HOST = 'localhost'
   DB_NAME = 'fyp_db'  # Replace with your desired database name
   ```

## Usage

Run the script using Python:
```bash
python create_database.py
```

The script will:
1. Create the database if it doesn't exist
2. Create all the necessary tables with proper relationships
3. Set up indexes for optimal performance
4. Log the progress and any errors that occur

## Tables Created

1. Companies
2. Developers
3. Users
4. Datasets
5. Dataset_Combinations
6. Models
7. Training_Sessions
8. Retraining_History
9. Deployments
10. Predictions

Each table is created with appropriate:
- Primary and foreign keys
- Indexes for performance
- Constraints for data integrity
- Default values where applicable
- Proper data types and lengths

## Error Handling

The script includes comprehensive error handling and logging:
- All operations are wrapped in try-except blocks
- Errors are logged with detailed messages
- The script will exit gracefully if any error occurs

## Support

If you encounter any issues or need assistance, please check:
1. MySQL server is running
2. Database credentials are correct
3. You have sufficient privileges to create databases and tables 
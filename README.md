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
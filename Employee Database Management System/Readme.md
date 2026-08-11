# Flask MySQL Web Application

This is a simple Flask web application that provides user registration, login, profile display, and update functionalities using a MySQL database.

---

## Features

- User registration with validation
- User login and session management
- Profile display
- Profile update
- Logout functionality

---

## Prerequisites

- Python 3.x
- MySQL Server installed and running
- `pip` package manager

---

## Installation & Setup

### 1. Clone the repository (if applicable)

```bash
git clone <your-repo-url>
cd <your-repo-folder>

python3 -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
pip install flask flask_mysqldb
'''
Database Setup
Start MySQL server on your machine.

Create the database:
Database Setup
Start MySQL server on your machine.

Create the database:

sql
Copy
Edit
CREATE DATABASE web_app_db;
Create the accounts table:

sql
Copy
Edit
USE web_app_db;

CREATE TABLE accounts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  paassword VARCHAR(255) NOT NULL,
  email VARCHAR(100),
  organisation VARCHAR(100),
  address VARCHAR(255),
  city VARCHAR(100),
  state VARCHAR(100),
  country VARCHAR(100),
  postalcode VARCHAR(20)
);
Note: The paassword column is intentionally spelled as in the original code but should ideally be password. Adjust the code or database accordingly for consistency.

Update MySQL credentials in app.py if needed:

python
Copy
Edit
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_mysql_password'
app.config['MYSQL_DB'] = 'web_app_db'
Running the Application
Make sure your MySQL server is running.

Run the Flask app:

bash
Copy
Edit
python app.py
Open your browser and navigate to:


http://localhost:5000/
Folder Structure

/project-folder
|-- app.py
|-- templates/
    |-- login.html
    |-- register.html
    |-- index.html
    |-- display.html
    |-- update.html
|-- static/ (optional for CSS/JS/images)
Place all your HTML files inside the templates folder.

Important Notes
The app uses Flask sessions; app.secret_key should be a strong secret key in production.

Passwords are stored in plain text in the database — for production use, hash passwords securely!

The code currently has a typo in the SQL query for login (paassword instead of password) which must be fixed.

Input validation is basic; consider adding stronger validation and security measures.

The app runs with debug mode enabled (debug=True), which should be disabled in production.

Troubleshooting
MySQL Connection Errors:
Ensure your MySQL server is running and the credentials in app.py are correct.

Module Not Found Errors:
Make sure you've installed all required Python packages.

Port Already in Use:
Change the port in app.py by modifying the line app.run(host="localhost", port=5000, debug=True).

'''
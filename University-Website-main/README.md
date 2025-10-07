# UNIVERSITY WEBSITE
* Frontend: HTML / CSS / JavaScript (Bootstrap used for responsiveness and quicker UI)
* Backend: Python (Flask)
* Database: MySQL (XAMPP). SQL script included to create database/tables and seed admin & instructor users.

# HOW TO RUN?
1. Install Python packages: pip install flask mysql-connector-python pandas openpyxl werkzeug
2. Start XAMPP and MySQL server.
3. In phpMyAdmin (or via CLI), create DB by running create_db.sql.
4. Put the project files into folder university-website.
5. Edit config section in app.py to set your MySQL username/password if needed.
6. Run app.py.
7. Open the IP address of your local computer with its given port in your browser.

# GOOGLE SHEET SYNCING
1. Enable Google Sheets API
* Go to Google Cloud Console.
* Create a project and enable Google Sheets API and Google Drive API.
* Create Service Account Credentials and download the credentials.json file.
* Share your Google Sheet with the service account email with Editor access.
2. In your virtual environment, install: pip install gspread oauth2client

# HASHED PASSWORD
👉 To generate the hashed password, open a Python terminal and run:
* from werkzeug.security import generate_password_hash

* print(generate_password_hash("yourpassword"))

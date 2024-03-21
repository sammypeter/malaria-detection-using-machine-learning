from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from datetime import date
from werkzeug.utils import secure_filename
import os
import tensorflow as tf
from PIL import Image
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///malaria_management.db' 
app.secret_key = 'secret123'
db = SQLAlchemy(app)

# SQLite database configuration
DATABASE_NAME = 'malaria_management.db'

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Check if the provided username and password are valid
def is_valid_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve the user from the database based on the provided username
    cursor.execute('SELECT * FROM Users WHERE LOWER(Username) = LOWER(?)', (username,))
    user = cursor.fetchone()

    # Check if the user exists and the password is correct
    if user and user['Password'] == password.strip():
        user_type = user['UserType']
        session['username'] = username
        return True, user_type
    else:
        return False

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the TensorFlow model
MODEL_PATH = 'models/my_model.h5'  
model = tf.keras.models.load_model(MODEL_PATH)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html', result=None)  # Pass 'result' as None initially

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Preprocess the image for the model
        img = Image.open(filepath)
        img = img.resize((50, 50))  
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Make predictions
        predictions = model.predict(img_array)
        result = 'Infected' if predictions[0][0] > 0.5 else 'Uninfected'

        # Remove the uploaded file
        os.remove(filepath)

        return render_template('addpatient.html', result=result)

    return jsonify({'error': 'Invalid file format'})

@app.route('/predictnew', methods=['POST'])
def predictnew():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Preprocess the image for the model
        img = Image.open(filepath)
        img = img.resize((50, 50))  
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Make predictions
        predictions = model.predict(img_array)
        result = 'Infected' if predictions[0][0] > 0.5 else 'Uninfected'

        # Remove the uploaded file
        os.remove(filepath)

        return render_template('addpatient1.html', result=result)

    return jsonify({'error': 'Invalid file format'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        valid_user, user_type = is_valid_user(username, password)

        if valid_user:
            if user_type == "admin":
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            
            elif user_type == "doctor":
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard1'))
            
            elif user_type == "lab":
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard3'))
        
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard2'))
        else:
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard(): 
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()
    cursor1 = conn.cursor()
    cursor2 = conn.cursor()
    cursor3 = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT COUNT(*) FROM patients")
    p_count = cursor.fetchone()[0]

    # Retrieve doctors records from the database
    cursor1.execute("SELECT COUNT(*) FROM Doctors")
    d_count = cursor1.fetchone()[0]

    cursor2.execute("SELECT COUNT(*) FROM lab")
    l_count = cursor2.fetchone()[0]
    
    cursor3.execute("SELECT COUNT(*) FROM office")
    o_count = cursor3.fetchone()[0]


    # Close the database connection
    conn.close()
    return render_template('dashboard.html',p_count=p_count,d_count=d_count,l_count=l_count,o_count=o_count)

@app.route('/patient')
def patient():
    # Logic to render the patient page goes here
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template and pass the patient records 
    return render_template('patient.html',patients=patients)

@app.route('/addpatient', methods=['GET', 'POST'])
def addpatient():
    if request.method == 'POST':
        # Get form data
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        insurance = request.form.get('insurance')
        phone = request.form.get('phone')
        result = request.form.get('result')
        
        # Get a database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Execute the insert query
        cursor.execute("INSERT INTO patients (fname, lname, insurance, phone, result) VALUES (?, ?, ?, ?, ?)",
                       (fname, lname, insurance, phone, result))
        
        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        flash('Patient added successfully!', 'success') 
    
    return render_template('addpatient.html') 

@app.route('/doctor')
def doctor():
    # Logic to render the doctor page goes here
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM Doctors")
    doctors = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template and pass the patient records 
    return render_template('doctor.html',doctors=doctors) 

@app.route('/adddoctor', methods=['GET', 'POST'])
def adddoctor():
    if request.method == 'POST':
        # Get form data
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        insurance = request.form.get('insurance')
        phone = request.form.get('phone') 
        
        # Get a database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Execute the insert query
        cursor.execute("INSERT INTO Doctors (fname, lname, insurance, phone) VALUES (?, ?, ?, ?)",
                       (fname, lname, insurance, phone))
        
        # Execute the insert query
        cursor.execute("INSERT INTO Users (Username, Password, UserType) VALUES (?, ?, ?)",
                       (fname, "abc@123", "doctor"))
        
        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        flash('Doctor added successfully!', 'success') 
    
    return render_template('adddoctor.html') 

@app.route('/delete/<int:patient_id>', methods=['POST', 'GET'])
def delete_patient(patient_id):
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the SQL delete statement with parameterized query
    cursor.execute("DELETE FROM patients WHERE patientid = ?", (patient_id,))
    conn.commit()

    # Close the database connection
    conn.close()

    # Flash a success message
    flash('Patient deleted successfully!', 'success')

    # Redirect to the patient page
    return redirect(url_for('patient'))

@app.route('/deletedoctor/<int:doctors_id>', methods=['POST'])
def delete_doctor(doctors_id):
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the SQL delete statement with parameterized query
    cursor.execute("DELETE FROM Doctors WHERE DoctorID = ?", (doctors_id,))
    conn.commit()

    # Close the database connection
    conn.close()

    # Flash a success message
    flash('Doctor deleted successfully!', 'success')

    # Redirect to the doctor page
    return redirect(url_for('doctor'))
    
@app.route('/dashboard1')
def dashboard1():
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor() 

    # Retrieve patient records from the database
    cursor.execute("SELECT COUNT(*) FROM patients")
    p1_count = cursor.fetchone()[0]

    # Close the database connection
    conn.close()
    return render_template('dashboard1.html',p1_count=p1_count)

@app.route('/patient1')
def patient1():
    # Logic to render the patient page goes here
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("""
                   SELECT * FROM patients
                   RIGHT JOIN reco ON patients.insurance = reco.insurance
                   """)
    
    patients1 = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template and pass the patient records 
    return render_template('patient1.html',patients1=patients1)

@app.route('/addpatientnew', methods=['GET', 'POST'])
def addpatientnew():
    if request.method == 'POST':
        # Get form data 
        insurance1 = request.form.get('insurance')
        reco = request.form.get('reco') 
        
        # Get a database connection
        conn1 = get_db_connection()
        cursor1 = conn1.cursor()

        # Execute the insert query
        cursor1.execute("INSERT INTO reco (insurance, reco) VALUES (?, ?)",
                       (insurance1, reco))
        
        # Commit the transaction and close the connection
        conn1.commit()
        conn1.close()

        flash('Patient added successfully!', 'success') 
    
    return render_template('addpatient1.html') 

@app.route('/deletenew/<int:patient1_id>', methods=['POST', 'GET'])
def delete_patientnew(patient1_id):
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the SQL delete statement with parameterized query
    cursor.execute("DELETE FROM patients WHERE patientid = ?", (patient1_id,))
    conn.commit()

    # Close the database connection
    conn.close()

    # Redirect to the patient page
    return redirect(url_for('patient1'))

@app.route('/profile/<int:doctors_id>', methods=['POST'])
def profile(doctors_id):
    # Logic to render the profile page goes here 
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()
 

    # Retrieve profile records from the database based on doctors_id
    cursor.execute("SELECT * FROM Doctors WHERE fname = ?", (doctors_id,)) 
    doc = cursor.fetchall()

    # Close the database connection
    conn.close()
    return render_template('profile.html',doc = doc)

@app.route('/print/<int:patient_id>', methods=['POST'])
def print_patient(patient_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM patients WHERE patientid = ?", (patient_id,))
    patient_tuple = cursor.fetchone()  # Fetch as a tuple
    patient = dict(zip([c[0] for c in cursor.description], patient_tuple))  # Convert tuple to dictionary

    # Close the database connection
    conn.close()

    if patient:
        # Generate PDF
        pdf_path = generate_patient_pdf(patient)

        # Send the PDF to the printer
        send_to_printer(pdf_path)

        flash('Patient details printed successfully!', 'success')
    else:
        flash('Patient not found!', 'error')

    return redirect(url_for('patient'))

@app.route('/printnew/<int:patient1_id>', methods=['POST'])
def print_patient1(patient1_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("""SELECT * FROM patients
                   RIGHT JOIN reco ON patients.insurance = reco.insurance 
                   WHERE patientid = ?""", (patient1_id,))
    patient_tuple = cursor.fetchone()  # Fetch as a tuple
    patientdoc = dict(zip([c[0] for c in cursor.description], patient_tuple))

    # Close the database connection
    conn.close()

    if patientdoc:
        # Generate PDF
        pdf_path = generate_patient_pdfdoc(patientdoc)

        # Send the PDF to the printer
        send_to_printer(pdf_path)

        flash('Patient details printed successfully!', 'success')
    else:
        flash('Patient not found!', 'error')

    return redirect(url_for('patient1'))

@app.route('/printnew1/<int:patient1_id>', methods=['POST'])
def print_patient2(patient1_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM patients WHERE patientid = ?", (patient1_id,))
    patient_tuple = cursor.fetchone()  # Fetch as a tuple
    patient = dict(zip([c[0] for c in cursor.description], patient_tuple))  # Convert tuple to dictionary

    # Close the database connection
    conn.close()

    if patient:
        # Generate PDF
        pdf_path = generate_patient_pdf(patient)

        # Send the PDF to the printer
        send_to_printer(pdf_path)

        flash('Patient details printed successfully!', 'success')
    else:
        flash('Patient not found!', 'error')

    return redirect(url_for('patient2'))

def generate_patient_pdf(patient):
    pdf_path = f"patient_{patient['patientid']}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, f"Patient ID: {patient['patientid']}")
    c.drawString(100, 730, f"First Name: {patient['fname']}")
    c.drawString(100, 710, f"Last Name: {patient['lname']}")
    c.drawString(100, 690, f"Insurance: {patient['insurance']}")
    c.drawString(100, 670, f"Contact Number: {patient['phone']}")
    c.drawString(100, 650, f"Result: {patient['Result']}")
    c.save()
    return pdf_path

def generate_patient_pdfdoc(patientdoc):
    pdf_path = f"patient_{patientdoc['patientid']}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, f"Patient ID: {patientdoc['patientid']}")
    c.drawString(100, 730, f"First Name: {patientdoc['fname']}")
    c.drawString(100, 710, f"Last Name: {patientdoc['lname']}")
    c.drawString(100, 690, f"Insurance: {patientdoc['insurance']}")
    c.drawString(100, 670, f"Contact Number: {patientdoc['phone']}")
    c.drawString(100, 650, f"Result: {patientdoc['Result']}")
    c.drawString(100, 630, f"Recommendation: {patientdoc['reco']}")
    c.save()
    return pdf_path

def send_to_printer(pdf_path):
    # Code to send the PDF to the printer goes here
    try:
        # Use lpr command to print the document
        subprocess.run(['lpr', pdf_path])
        return True
    except Exception as e:
        print(f"Error printing document: {e}")
        return False
    pass

@app.route('/office')
def office():
    # Logic to render the doctor page goes here
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM office")
    office = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template and pass the patient records 
    return render_template('office.html',office=office) 

@app.route('/addoffice', methods=['GET', 'POST'])
def addoffice():
    if request.method == 'POST':
        # Get form data
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        insurance = request.form.get('insurance')
        phone = request.form.get('phone') 
        
        # Get a database connection
        conn = get_db_connection() 
        cursor = conn.cursor()
        cursor1 = conn.cursor()

        # Execute the insert query
        cursor.execute("INSERT INTO office (fname, lname, insurance, phone) VALUES (?, ?, ?, ?)",
                       (fname, lname, insurance, phone))
        
        # Execute the insert query
        cursor1.execute("INSERT INTO Users (Username, Password, UserType) VALUES (?, ?, ?)",
                       (fname, "office@123", "office"))
        
        # Commit the transaction and close the connection
        conn.commit()
        conn.close()
    
    return render_template('addoffice.html') 

@app.route('/deleteoffice/<int:office_id>', methods=['POST'])
def delete_office(office_id):
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the SQL delete statement with parameterized query
    cursor.execute("DELETE FROM office WHERE UserID = ?", (office_id,))
    conn.commit()

    # Close the database connection
    conn.close()

    # Flash a success message
    flash('office deleted successfully!', 'success')

    # Redirect to the doctor page
    return redirect(url_for('office.html'))

@app.route('/lab')
def lab():
    # Logic to render the doctor page goes here
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM lab")
    lab = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template and pass the patient records 
    return render_template('lab.html',lab=lab) 

@app.route('/addlab', methods=['GET', 'POST'])
def addlab():
    if request.method == 'POST':
        # Get form data
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        insurance = request.form.get('insurance')
        phone = request.form.get('phone') 
        
        # Get a database connection
        conn = get_db_connection() 
        cursor = conn.cursor()
        cursor1 = conn.cursor()

        # Execute the insert query
        cursor.execute("INSERT INTO lab (fname, lname, insurance, phone) VALUES (?, ?, ?, ?)",
                       (fname, lname, insurance, phone))
        
        # Execute the insert query
        cursor1.execute("INSERT INTO Users (Username, Password, UserType) VALUES (?, ?, ?)",
                       (fname, "lab@123", "lab"))
        
        # Commit the transaction and close the connection
        conn.commit()
        conn.close()
    
    return render_template('addlab.html') 

@app.route('/deletelab/<int:lab_id>', methods=['POST'])
def delete_lab(lab_id):
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the SQL delete statement with parameterized query
    cursor.execute("DELETE FROM lab WHERE UserID = ?", (lab_id,))
    conn.commit()

    # Close the database connection
    conn.close()

    # Flash a success message
    flash('lab deleted successfully!', 'success')

    # Redirect to the doctor page
    return redirect(url_for('lab.html'))

@app.route('/dashboard2')
def dashboard2():
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor() 

    # Retrieve patient records from the database
    cursor.execute("SELECT COUNT(*) FROM patients")
    p1_count = cursor.fetchone()[0]

    # Close the database connection
    conn.close()
    return render_template('dashboard2.html',p1_count=p1_count)

@app.route('/patient2')
def patient2():
    # Logic to render the patient page goes here
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM patients")
    patients1 = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template and pass the patient records 
    return render_template('patient2.html',patients1=patients1)

@app.route('/deletenew1/<int:patient1_id>', methods=['POST', 'GET'])
def delete_patientnew1(patient1_id):
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the SQL delete statement with parameterized query
    cursor.execute("DELETE FROM patients WHERE patientid = ?", (patient1_id,))
    conn.commit()

    # Close the database connection
    conn.close()

    # Redirect to the patient page
    return redirect(url_for('patient2'))

@app.route('/addpatientnew1', methods=['GET', 'POST'])
def addpatientnew1():
    if request.method == 'POST':
        # Get form data
        fname1 = request.form.get('fname')
        lname1 = request.form.get('lname')
        insurance1 = request.form.get('insurance')
        phone1 = request.form.get('phone')
        result1 = request.form.get('result')
        
        # Get a database connection
        conn1 = get_db_connection()
        cursor1 = conn1.cursor()

        # Execute the insert query
        cursor1.execute("INSERT INTO patients (fname, lname, insurance, phone, result) VALUES (?, ?, ?, ?, ?)",
                       (fname1, lname1, insurance1, phone1, 'No results'))
        
        # Commit the transaction and close the connection
        conn1.commit()
        conn1.close()

        flash('Patient added successfully!', 'success') 
    
    return render_template('addpatient2.html') 

@app.route('/dashboard3')
def dashboard3():
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor() 

    # Retrieve patient records from the database
    cursor.execute("SELECT COUNT(*) FROM patients")
    p1_count = cursor.fetchone()[0]

    # Close the database connection
    conn.close()
    return render_template('dashboard3.html',p1_count=p1_count)

@app.route('/patient3')
def patient3():
    # Logic to render the patient page goes here
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Render the HTML template and pass the patient records 
    return render_template('patient3.html',patients=patients)

@app.route('/addpatient3', methods=['GET', 'POST'])
def addpatient3():
    if request.method == 'POST':
        # Get form data 
        insurance = request.form.get('insurance') 
        result = request.form.get('result')

        # Get a database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Execute the update query
        cursor.execute("UPDATE patients SET Result = ? WHERE insurance = ?", (result, insurance))

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        flash('Patient added successfully!', 'success') 
    
    return render_template('addpatient3.html') 

@app.route('/predictnew3', methods=['POST'])
def predictnew3():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Preprocess the image for the model
        img = Image.open(filepath)
        img = img.resize((50, 50))  
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Make predictions
        predictions = model.predict(img_array)
        result = 'Infected' if predictions[0][0] > 0.5 else 'Uninfected'

        # Remove the uploaded file
        os.remove(filepath)

        return render_template('addpatient3.html', result=result)

    return jsonify({'error': 'Invalid file format'})

@app.route('/deletenew3/<int:patient1_id>', methods=['POST', 'GET'])
def delete_patientnew3(patient1_id):
    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute the SQL delete statement with parameterized query
    cursor.execute("DELETE FROM patients WHERE patientid = ?", (patient1_id,))
    conn.commit()

    # Close the database connection
    conn.close()

    # Redirect to the patient page
    return redirect(url_for('patient3'))

@app.route('/printnew3/<int:patient1_id>', methods=['POST'])
def print_patient3(patient1_id):
    # Connect to the SQLite database
    conn = sqlite3.connect('malaria_management.db')
    cursor = conn.cursor()

    # Retrieve patient records from the database
    cursor.execute("SELECT * FROM patients WHERE patientid = ?", (patient1_id,))
    patient_tuple = cursor.fetchone()  # Fetch as a tuple
    patient = dict(zip([c[0] for c in cursor.description], patient_tuple))  # Convert tuple to dictionary

    # Close the database connection
    conn.close()

    if patient:
        # Generate PDF
        pdf_path = generate_patient_pdf(patient)

        # Send the PDF to the printer
        send_to_printer(pdf_path)

        flash('Patient details printed successfully!', 'success')
    else:
        flash('Patient not found!', 'error')

    return redirect(url_for('patient3'))

if __name__ == '__main__':
    app.run(debug=True)
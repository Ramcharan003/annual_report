from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt

# Connect to the database
cnx = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="system",
    database="prem13"  # Ensure the correct database is specified
)

cur = cnx.cursor()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session and flash messages

# Route to display the login page
@app.route('/')
def login():
    return render_template("log.html")

def generate_plot(semester_marks):
    semesters = ['Semester 1', 'Semester 2', 'Semester 3', 'Semester 4', 'Semester 5', 'Semester 6']
    marks = [semester_marks[f'semester{i}'] for i in range(1, 7)]

    plt.figure()
    plt.bar(semesters, marks, color='skyblue')
    plt.title('Semester-wise Marks Visualization')
    plt.xlabel('Semesters')
    plt.ylabel('Marks')
    plt.ylim(0, 100)

    plot_path = 'static/marks_plot.png'
    plt.savefig(plot_path)
    plt.close()

    return plot_path


@app.route('/login', methods=['POST'])
def login_user():
    username = request.form['username']  # Get the username from the form
    password = request.form['password']  # Get the password from the form
    
    # Fetch user data from the database
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()

    # Check if the user exists and if the password is correct
    if user and check_password_hash(user[4], password):  # Assuming password is in user[4]
        # Store user info and account type in session
        session['username'] = username
        session['account_type'] = user[5]  # Assuming account_type is in user[5]

        # Debugging: print session variables
        print(f"Logged in as {session['username']} with account type {session['account_type']}")

        # Redirect to the student dashboard if the user is a student
        return redirect(url_for('faculty_dashboard'))
    else:
        # If login fails, show an alert
        flash("Incorrect username or password", "error")
        return redirect(url_for('login'))  # Redirect back to login page


@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('faculty_dashboard.html')


@app.route('/admission')
def admission():
    if 'username' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in
    if session.get('account_type') != 'faculty':
        return render_template('input_form.html')
    return render_template('input_form.html')  # Admission page template


@app.route('/marks')
def marks():
    if 'username' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in
    if session.get('account_type') != 'student':
        return render_template('marks.html')  # Redirect non-studentsreturn
    return render_template('marks.html')  # Marks entry page template

# Route to display the registration page
@app.route('/regis')
def regis():
    return render_template('regis.html')

# Route to handle registration (POST)
@app.route('/register', methods=['POST'])
def register_user():
    fullname = request.form['fullname']
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm-password']
    account_type = request.form['account_type']  # Capture the account type

    # Check if passwords match
    if password != confirm_password:
        flash("Passwords do not match", "error")
        return redirect(url_for('regis'))

    # Hash the password before storing it
    hashed_password = generate_password_hash(password)

    # Check if the username already exists in the database
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cur.fetchone()

    if existing_user:
        flash("Username already exists", "error")
        return redirect(url_for('regis'))

    # Insert new user into the users table, including account_type
    insert_query = """
        INSERT INTO users (fullname, email, username, password, account_type)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(insert_query, (fullname, email, username, hashed_password, account_type))
    cnx.commit()

    flash("Registration successful, please log in", "success")
    return redirect(url_for('login'))


@app.route('/input_form')
def input_form():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    if session.get('account_type') != 'faculty':
        return redirect(url_for('faculty_dashboard'))  # Redirect non-faculty users

    return render_template('input_form.html') 

# Route to handle admission form submission (POST)
@app.route('/submit_form', methods=['POST'])
def submit_form():
    if 'username' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in
    
    # Retrieve form data
    name = request.form['name']
    eamcetRank = request.form['eamcetRank']
    admissionNo = request.form['admissionNo']
    joiningDate = request.form['joiningDate']
    feeStructure = request.form['feeStructure']
    parentMobile = request.form['parentMobile']
    studentMobile = request.form['studentMobile']
    aadharNumber = request.form['aadharNumber']
    studentEmail = request.form['studentEmail']

    # Check if the record already exists using the unique field (e.g., `admissionNo`)
    cur.execute("SELECT * FROM admission WHERE admissionNo = %s", (admissionNo,))
    existing_record = cur.fetchone()

    if existing_record:
        # If the record exists, update it
        update_query = """
            UPDATE admission SET 
                name = %s, eamcetRank = %s, joiningDate = %s, 
                feeStructure = %s, parentMobile = %s, studentMobile = %s, 
                aadharNumber = %s, studentEmail = %s
            WHERE admissionNo = %s
        """
        cur.execute(update_query, (name, eamcetRank, joiningDate, feeStructure, 
                                   parentMobile, studentMobile, aadharNumber, 
                                   studentEmail, admissionNo))
        cnx.commit()
        message = "Record updated successfully!"
    else:
        # If the record does not exist, insert a new one
        insert_query = """
            INSERT INTO admission (name, eamcetRank, admissionNo, joiningDate, 
                                   feeStructure, parentMobile, studentMobile, 
                                   aadharNumber, studentEmail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(insert_query, (name, eamcetRank, admissionNo, joiningDate, 
                                   feeStructure, parentMobile, studentMobile, 
                                   aadharNumber, studentEmail))
        cnx.commit()
        message = "Record inserted successfully!"

    return render_template('input_form.html', message=message)


@app.route('/submit_marks', methods=['POST'])
def submit_marks():
    if 'username' not in session:
        return redirect(url_for('login'))  # Ensure user is logged in
    
    admissionNo = request.form['admissionNo']  # Get the admissionNo from the form submission
    
    # Retrieve the marks for each semester from the form fields
    semester_marks = {
        'semester1': int(request.form['marks1']),
        'semester2': int(request.form['marks2']),
        'semester3': int(request.form['marks3']),
        'semester4': int(request.form['marks4']),
        'semester5': int(request.form['marks5']),
        'semester6': int(request.form['marks6']),
    }

    # Calculate total marks
    total_marks = sum(semester_marks.values())

    # Check if the student exists in the admission table
    cur.execute("SELECT * FROM admission WHERE admissionNo = %s", (admissionNo,))
    admission_record = cur.fetchone()

    if not admission_record:
        flash("No student found with the provided Admission Number", "error")
        return redirect(url_for('marks'))  # Redirect back to the marks entry page if no record exists

    # Check if the student has already entered marks for the given admissionNo
    cur.execute("SELECT * FROM marks WHERE admissionNo = %s", (admissionNo,))
    existing_marks = cur.fetchone()

    if existing_marks:
        # If marks already exist, update the record
        update_query = """
            UPDATE marks
            SET semester1_marks = %s, semester2_marks = %s, semester3_marks = %s, 
                semester4_marks = %s, semester5_marks = %s, semester6_marks = %s,
                total_marks = %s
            WHERE admissionNo = %s
        """
        cur.execute(update_query, (
            semester_marks['semester1'], semester_marks['semester2'], semester_marks['semester3'],
            semester_marks['semester4'], semester_marks['semester5'], semester_marks['semester6'],
            total_marks, admissionNo
        ))
        cnx.commit()
        flash("Marks updated successfully", "success")
    else:
        # If marks do not exist, insert a new record
        insert_query = """
            INSERT INTO marks (admissionNo, semester1_marks, semester2_marks, semester3_marks, 
                               semester4_marks, semester5_marks, semester6_marks, total_marks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(insert_query, (
            admissionNo, semester_marks['semester1'], semester_marks['semester2'], semester_marks['semester3'],
            semester_marks['semester4'], semester_marks['semester5'], semester_marks['semester6'],
            total_marks
        ))
        cnx.commit()
        flash("Marks inserted successfully", "success")

    # Now generate the plot after marks are saved
    plot_path = generate_plot(semester_marks)

    return redirect(url_for('faculty_dashboard'))  # Redirect back to the dashboard after submission

# Route to handle logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove user from session
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

# Close the connection to the database when the app stops
cnx.close()

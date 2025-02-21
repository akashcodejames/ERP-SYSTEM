import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import re
from extensions import db
from models import UserCredentials, TeacherDetails, StudentDetails, AdminProfile, HODProfile, SubjectAssignment, Course, CourseSubject, Attendance
import random
import string
import logging
from datetime import datetime
from sqlalchemy import inspect, or_, text
import csv
from io import StringIO

bp = Blueprint('auth', __name__)

def generate_random_password(length=12):
    """Generate a random password with letters, digits, and special characters"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        logging.info(f"Login attempt for email: {email}, role: {role}")

        if not all([email, password, role]):
            flash('Please fill in all required fields')
            return redirect(url_for('auth.login'))

        user = UserCredentials.query.filter_by(email=email, role=role).first()

        if not user:
            logging.warning(f"No user found with email: {email} and role: {role}")
            flash('Invalid credentials')
            return redirect(url_for('auth.login'))

        if not user.check_password(password):
            logging.warning(f"Invalid password for user: {email}")
            flash('Invalid credentials')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Your account is deactivated. Please contact administrator.')
            return redirect(url_for('auth.login'))

        # Additional verification for students
        if role == 'student':
            admission_year = request.form.get('admission_year')
            student = StudentDetails.query.filter_by(credential_id=user.id).first()

            if not admission_year or not student:
                flash('Please select admission year')
                return redirect(url_for('auth.login'))

            if str(student.admission_year) != admission_year:
                flash('Invalid credentials for the selected admission year')
                return redirect(url_for('auth.login'))

        login_user(user)
        logging.info(f"Successful login for user: {email}, role: {role}")
        return redirect(url_for(f'auth.{user.role}_dashboard'))

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))


# @bp.route('/add_user', methods=['POST'])
# @login_required
# def add_user():
#     print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
#     if current_user.role != 'admin':
#         flash('Access denied: Admin privileges required')
#         return redirect(url_for(f'auth.{current_user.role}_dashboard'))
#
#     try:
#         role = request.form.get('role')
#         email = request.form.get('email')
#         first_name = request.form.get('first_name')
#         last_name = request.form.get('last_name')
#         phone = request.form.get('phone')
#         address = request.form.get('address')
#         department = request.form.get('department')
#
#         # Handle photo upload
#         photo_path = None
#         if 'photo' in request.files:
#             photo = request.files['photo']
#             if photo.filename:
#                 filename = f"{role}_{email.split('@')[0]}_{photo.filename}"
#                 photo_path = os.path.join('static', 'uploads', 'photos', filename)
#                 os.makedirs(os.path.dirname(photo_path), exist_ok=True)
#                 photo.save(photo_path)
#
#         # Generate random password
#         password = generate_random_password()
#
#         # Create credentials
#         credentials = UserCredentials(
#             email=email,
#             role=role
#         )
#         credentials.set_password(password)
#         db.session.add(credentials)
#         db.session.flush()  # Get the ID before creating profile
#
#         if role == 'student':
#             print("*******************************************************************************************************************************************")
#             admission_year = request.form.get('admission_year')
#             roll_number = request.form.get('roll_number')
#             course_id = request.form.get('course_id')
#
#             # Validate admission year exists in batches
#             available_years = get_available_batch_years(course_id)
#             if int(admission_year) not in available_years:
#                 flash('Selected admission year does not exist in batches')
#                 return redirect(url_for('auth.admin_dashboard'))
#
#             # Calculate current year based on admission year
#             current_year = datetime.utcnow().year - int(admission_year) + 1
#             if current_year < 1:
#                 current_year = 1
#             elif current_year > 4:
#                 current_year = 4
#
#             # Determine the batch table name
#             batch_table = f'student_batch_{course_id}_{admission_year}'
#
#             # Insert student into the batch table instead of StudentDetails
#             sql = text(f"""
#             INSERT INTO {batch_table} (
#                 credential_id, first_name, last_name, email, phone, address, photo_path,
#                 roll_number, current_year, current_semester, admission_year, course_id, batch, admission_date
#             ) VALUES (
#                 :credential_id, :first_name, :last_name, :email, :phone, :address, :photo_path,
#                 :roll_number, :current_year, :current_semester, :admission_year, :course_id, :batch, :admission_date
#             )
#             """)
#
#             db.session.execute(sql, {
#                 'credential_id': credentials.id,
#                 'first_name': first_name,
#                 'last_name': last_name,
#                 'email': email,
#                 'phone': phone,
#                 'address': address,
#                 'photo_path': photo_path,
#                 'roll_number': roll_number,
#                 'current_year': current_year,
#                 'current_semester': 1,
#                 'admission_year': int(admission_year),
#                 'course_id': course_id,
#                 'batch': str(admission_year),
#                 'admission_date': datetime.utcnow()
#             })
#
#         elif role == 'teacher':
#             print("#####################################################################################################################################################")
#             sql_teacher = text("""
#                 INSERT INTO teacher_details (
#                     credential_id, first_name, last_name, email, department, phone, address, photo_path
#                 ) VALUES (
#                     :credential_id, :first_name, :last_name, :email, :department, :phone, :address, :photo_path
#                 )
#             """)
#
#             db.session.execute(sql_teacher, {
#                 'credential_id': credentials.id,
#                 'first_name': first_name,
#                 'last_name': last_name,
#                 'email': email,
#                 'department': department,
#                 'phone': phone,
#                 'address': address,
#                 'photo_path': photo_path
#             })
#
#         elif role == 'hod':
#             sql_hod = text("""
#                 INSERT INTO hod_profiles (
#                     credential_id, first_name, last_name, email, phone, address, photo_path, department, office_location
#                 ) VALUES (
#                     :credential_id, :first_name, :last_name, :email, :phone, :address, :photo_path, :department, :office_location
#                 )
#             """)
#
#             db.session.execute(sql_hod, {
#                 'credential_id': credentials.id,
#                 'first_name': first_name,
#                 'last_name': last_name,
#                 'email': email,
#                 'phone': phone,
#                 'address': address,
#                 'photo_path': photo_path,
#                 'department': department,
#                 'office_location': request.form.get('office_location', 'Sanjay Nagar,Ghaziabad')
#             })
#
#         db.session.commit()
#         flash(f'User created successfully. Temporary password: {password}')
#         logging.info(f'New {role} user created: {email}')
#
#     except Exception as e:
#         db.session.rollback()
#         flash(f'Error creating user: {str(e)}')
#         logging.error(f'Error creating user: {str(e)}')
#
#     return redirect(url_for('auth.admin_dashboard'))




@bp.route('/create_student_batch', methods=['POST'])
@login_required
def create_student_batch():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required', 'danger')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    try:
        batch_year = request.form.get('batch_year')
        course_id = request.form.get('course_id')
        batch_id = request.form.get('batch_id')
        semester = request.form.get('semester')

        if not all([batch_year, course_id, batch_id, semester]):
            flash('Batch year, course, batch ID, and semester are required', 'warning')
            return redirect(url_for('auth.admin_dashboard'))

        # Validate batch year
        try:
            batch_year = int(batch_year)
            if batch_year < 1900 or batch_year > 2100:
                raise ValueError("Batch year out of valid range")
        except ValueError:
            flash('Invalid batch year format', 'danger')
            return redirect(url_for('auth.admin_dashboard'))

        # Validate batch ID (1 to 5)
        try:
            batch_id = int(batch_id)
            if batch_id < 1 or batch_id > 5:
                raise ValueError("Batch ID must be between 1 and 5")
        except ValueError:
            flash('Invalid batch ID', 'danger')
            return redirect(url_for('auth.admin_dashboard'))

        # Validate semester (1 to 8)
        try:
            semester = int(semester)
            if semester < 1 or semester > 8:
                raise ValueError("Semester must be between 1 and 8")
        except ValueError:
            flash('Invalid semester', 'danger')
            return redirect(url_for('auth.admin_dashboard'))

        # Fetch course to validate and use in table name
        course = Course.query.get(course_id)
        if not course:
            flash('Invalid course selected', 'danger')
            return redirect(url_for('auth.admin_dashboard'))

        # Generate table name
        table_name = f'student_batch_{course_id}_{batch_year}_{semester}_{batch_id}'

        # SQL Query to create the table
        create_table_sql = text(f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            credential_id INT UNIQUE NOT NULL,
            first_name VARCHAR(64) NOT NULL,
            last_name VARCHAR(64) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            photo_path VARCHAR(500),
            roll_number VARCHAR(20) UNIQUE NOT NULL,
            current_year INT NOT NULL,
            current_semester INT NOT NULL CHECK (current_semester BETWEEN 1 AND 8),
            admission_year INT NOT NULL,
            course_id INT NOT NULL,
            batch VARCHAR(10) NOT NULL,
            admission_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            batch_id INT NOT NULL,
            semester INT NOT NULL,
            FOREIGN KEY (credential_id) REFERENCES user_credentials(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Execute the table creation
        db.session.execute(create_table_sql)
        db.session.commit()

        flash(f'Student batch table `{table_name}` created successfully!', 'success')
        logging.info(f'Successfully created student batch table: {table_name}')

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating student batch: {str(e)}', 'danger')
        logging.error(f'Error creating student batch: {str(e)}')

    return redirect(url_for('auth.admin_dashboard'))



@bp.route('/get_batch_years')
def get_batch_years():
    """API endpoint to get available batch years"""
    try:
        course_id = request.args.get('course_id')
        if not course_id:
            return jsonify({'error': 'Course ID is required'}), 400

        # Query to get all tables that are related to the specified course
        sql = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE :pattern
        AND table_schema = DATABASE()
        """)
        result = db.session.execute(sql, {'pattern': f'student_batch_{course_id}_%'})
        batch_tables = result.fetchall()

        # Extract years from table names and sort them
        years = []
        for (table_name,) in batch_tables:
            try:
                year = int(table_name.split('_')[-1])
                years.append(year)
            except ValueError:
                continue

        sorted_years = sorted(years, reverse=True)
        logging.info(f'Retrieved batch years for course {course_id}: {sorted_years}')
        return jsonify({'years': sorted_years})
    except Exception as e:
        logging.error(f'Error fetching batch years: {str(e)}')
        return jsonify({'error': str(e)}), 500

def get_available_batch_years(course_id=None):
    """Fetch all available batch years from existing batch tables for a specific course"""
    try:
        pattern = f'student_batch_{course_id}_%' if course_id else 'student_batch_%'
        # Query to get all tables that start with the pattern
        sql = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE :pattern
        AND table_schema = DATABASE()
        """)
        result = db.session.execute(sql, {'pattern': pattern})
        batch_tables = result.fetchall()

        # Extract years from table names and sort them
        years = []
        for (table_name,) in batch_tables:
            try:
                year = int(table_name.split('_')[-1])
                years.append(year)
            except ValueError:
                continue

        sorted_years = sorted(years, reverse=True)
        logging.info(f'Retrieved batch years for course {course_id}: {sorted_years}')
        return sorted_years
    except Exception as e:
        logging.error(f'Error fetching batch years: {str(e)}')
        return []


@bp.route('/add_hod', methods=['GET', 'POST'])
@login_required
def add_hod():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    if request.method == 'POST':
        try:
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            department = request.form.get('department')
            office_location = request.form.get('office_location', 'Sanjay Nagar, Ghaziabad')

            # Handle photo upload
            photo_path = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo.filename:
                    filename = f"hod_{email.split('@')[0]}_{photo.filename}"
                    photo_paths = os.path.join('static', 'uploads', filename)
                    photo_path=filename
                    print(photo_path)
                    os.makedirs(os.path.dirname(photo_paths), exist_ok=True)
                    photo.save(photo_paths)

            # Generate random password
            password = generate_random_password()

            # Create credentials
            credentials = UserCredentials(email=email, role='hod')
            credentials.set_password(password)
            db.session.add(credentials)
            db.session.flush()

            # Insert into HOD table
            sql_hod = text("""
                INSERT INTO hod_profiles (
                    credential_id, first_name, last_name, email, phone, address, photo_path, department, office_location
                ) VALUES (
                    :credential_id, :first_name, :last_name, :email, :phone, :address, :photo_path, :department, :office_location
                )
            """)

            db.session.execute(sql_hod, {
                'credential_id': credentials.id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'address': address,
                'photo_path': photo_path,
                'department': department,
                'office_location': office_location
            })

            db.session.commit()
            flash(f'HOD added successfully. Temporary password: {password}')
            return redirect(url_for('auth.render_hod'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding HOD: {str(e)}')

    return render_template('add_hod.html')



# Allowed image extensions


def allowed_file(filename):
    """Check if the uploaded file has a valid image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
@bp.route('/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required', 'danger')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    if request.method == 'POST':
        try:
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            address = request.form.get('address')
            department = request.form.get('department')

            # **BACKEND VALIDATION: Check Email Format**
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                flash("Invalid email format!", "danger")
                return redirect(url_for('auth.add_teacher'))

            # **BACKEND VALIDATION: Ensure Phone Number is 10 Digits**
            if not phone.isdigit():
                flash("Phone number must contain only numbers!", "danger")
                return redirect(url_for('auth.add_teacher'))

            if len(phone) == 11 and phone.startswith("0"):
                phone = phone[1:]  # Remove first zero
            elif len(phone) != 10:
                flash("Phone number must be exactly 10 digits or 11 digits starting with 0!", "danger")
                return redirect(url_for('auth.add_teacher'))

            # Generate random password
            password = generate_random_password()

            # Create credentials
            credentials = UserCredentials(email=email, role='teacher')
            credentials.set_password(password)
            db.session.add(credentials)
            db.session.flush()  # Get credential_id before committing

            # Define default photo path
            photo_path = None

            # **BACKEND VALIDATION: Check and Save Image File**
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo.filename:
                    if not allowed_file(photo.filename):
                        flash("Invalid file format! Only PNG, JPG, JPEG, GIF allowed.", "danger")
                        return redirect(url_for('auth.add_teacher'))

                    # Ensure upload folder exists
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'teacher_photos')
                    os.makedirs(upload_folder, exist_ok=True)

                    # Secure filename and save
                    photo_filename = f"teacher_{credentials.id}.jpg"
                    photo_path = f"{photo_filename}"
                    photo.save(os.path.join(upload_folder, photo_filename))

            # Insert into Teacher table
            sql_teacher = text("""
                INSERT INTO teacher_details (
                    credential_id, first_name, last_name, email, department, phone, address, photo_path
                ) VALUES (
                    :credential_id, :first_name, :last_name, :email, :department, :phone, :address, :photo_path
                )
            """)

            db.session.execute(sql_teacher, {
                'credential_id': credentials.id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'department': department,
                'phone': phone,
                'address': address,
                'photo_path': photo_path
            })

            db.session.commit()
            flash(f'Teacher added successfully. Temporary password: {password}', 'success')
            return redirect(url_for('auth.render_teacher'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding teacher: {str(e)}', 'danger')

    return render_template('dashboard/add_teacher.html')






@bp.route('/render_hod', methods=['GET', 'POST'])
@login_required
def render_hod():
    return render_template('dashboard/add_hod.html')

@bp.route('/render_teacher', methods=['GET', 'POST'])
@login_required
def render_teacher():
    return render_template('dashboard/add_teacher.html')





@bp.route('/add_student', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    try:
        # Fetch form data
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        admission_year = request.form.get('admission_year')
        roll_number = request.form.get('roll_number')
        course_id = request.form.get('course_id')
        batch_id = request.form.get('batch')  # Batch ID
        semester = request.form.get('semester')  # Semester selection

        # Ensure semester value is valid (1 to 8)
        semester = int(semester)
        if semester < 1 or semester > 8:
            flash('Invalid semester. Choose between 1 and 8.')
            return redirect(url_for('auth.admin_dashboard'))

        # Handle photo upload
        photo_path = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename:
                filename = secure_filename(f"student_{email.split('@')[0]}_{photo.filename}")
                photo_path = os.path.join('static', 'uploads', 'photos', filename)
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                photo.save(photo_path)

        # Generate random password for student login
        password = generate_random_password()

        # Create user credentials entry
        credentials = UserCredentials(email=email, role="student")
        credentials.set_password(password)
        db.session.add(credentials)
        db.session.flush()  # Get credential ID before inserting student

        # Calculate current academic year (1st to 4th year)
        current_year = datetime.utcnow().year - int(admission_year) + 1
        current_year = max(1, min(current_year, 4))  # Ensuring it's between 1st to 4th year

        # Define batch-specific table name (Includes Course, Admission Year, Batch ID, and Semester)
        batch_table = f'student_batch_{course_id}_{admission_year}_{batch_id}_{semester}'

        # Insert student data into batch-semester-specific table
        sql = text(f"""
        INSERT INTO {batch_table} (
            credential_id, first_name, last_name, email, phone, address, photo_path,
            roll_number, current_year, current_semester, admission_year, course_id, batch, admission_date
        ) VALUES (
            :credential_id, :first_name, :last_name, :email, :phone, :address, :photo_path,
            :roll_number, :current_year, :current_semester, :admission_year, :course_id, :batch, :admission_date
        )
        """)

        db.session.execute(sql, {
            'credential_id': credentials.id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'address': address,
            'photo_path': photo_path,
            'roll_number': roll_number,
            'current_year': current_year,
            'current_semester': semester,  # Storing selected semester
            'admission_year': int(admission_year),
            'course_id': course_id,
            'batch': batch_id,  # Storing batch ID
            'admission_date': datetime.utcnow()
        })

        db.session.commit()
        flash(f'Student added successfully. Temporary password: {password}')
        logging.info(f'New student created: {email}, Batch {batch_id}, Semester {semester}, Table: {batch_table}')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding student: {str(e)}')
        logging.error(f'Error creating student: {str(e)}')

    return redirect(url_for('auth.admin_dashboard'))


























@bp.route('/admin/manage_batches')
@login_required
def manage_batches():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    # Fetch all existing student batch tables
    sql = text("""
    SELECT table_name FROM information_schema.tables
    WHERE table_name LIKE 'student_batch_%' AND table_schema = DATABASE()
    """)
    result = db.session.execute(sql)
    batch_tables = result.fetchall()

    student_batches = []
    for (table_name,) in batch_tables:
        parts = table_name.split('_')
        if len(parts) >= 4:
            course_id = parts[2]
            year = parts[3]
            course = Course.query.get(course_id)
            if course:
                student_batches.append({
                    'table_name': table_name,
                    'course': course.name,
                    'year': year
                })

    return render_template('dashboard/manage_batches.html', student_batches=student_batches)


@bp.route('/admin/view_batch/<table_name>')
@login_required
def view_batch(table_name):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.manage_batches'))

    try:
        # Fetch table data dynamically
        sql = text(f"SELECT * FROM {table_name}")
        result = db.session.execute(sql)
        rows = result.fetchall()

        # Get column names dynamically
        columns = [col[0] for col in db.session.execute(text(f"DESCRIBE {table_name}")).fetchall()]

        return render_template('dashboard/view_batch.html', table_name=table_name, rows=rows, columns=columns)

    except Exception as e:
        flash(f"Error retrieving batch data: {str(e)}")
        return redirect(url_for('auth.manage_batches'))


@bp.route('/admin/update_student/<table_name>/<int:student_id>', methods=['POST'])
@login_required
def update_student(table_name, student_id):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.manage_batches'))

    try:
        # Get actual column names from the table
        column_query = db.session.execute(text(f"DESCRIBE {table_name}"))
        columns = [col[0] for col in column_query.fetchall()]

        # Build update query
        sql = f"UPDATE {table_name} SET "
        updates = []
        values = {"student_id": student_id}

        for key, value in request.form.items():
            column_index = key.replace("column_", "")  # Get column index
            if column_index.isdigit():
                column_index = int(column_index) - 1  # Convert to zero-based index
                if 0 <= column_index < len(columns):  # Ensure valid index
                    column_name = columns[column_index]  # Get actual column name
                    updates.append(f"{column_name} = :{column_name}")
                    values[column_name] = value

        sql += ", ".join(updates) + " WHERE id = :student_id"

        # Execute the query
        db.session.execute(text(sql), values)
        db.session.commit()

        flash('Student data updated successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating student data: {str(e)}')
        logging.error(f'Error updating student data: {str(e)}')

    return redirect(url_for('auth.view_batch', table_name=table_name))



@bp.route('/admin/delete_student/<table_name>/<int:student_id>', methods=['POST'])
@login_required
def delete_student(table_name, student_id):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.manage_batches'))

    try:
        # Retrieve the student's credential_id from the batch table before deleting
        student_query = db.session.execute(
            text(f"SELECT credential_id FROM {table_name} WHERE id = :student_id"),
            {"student_id": student_id}
        )
        student = student_query.fetchone()

        if student and student[0]:  # Ensure credential_id is found
            credential_id = student[0]

            # First, delete the student from the batch table
            db.session.execute(
                text(f"DELETE FROM {table_name} WHERE id = :student_id"),
                {"student_id": student_id}
            )

            # Check if the credential exists in `user_credentials`
            credential_check = db.session.execute(
                text("SELECT id FROM user_credentials WHERE id = :credential_id"),
                {"credential_id": credential_id}
            ).fetchone()

            if credential_check:
                # Delete credentials from `user_credentials`
                db.session.execute(
                    text("DELETE FROM user_credentials WHERE id = :credential_id"),
                    {"credential_id": credential_id}
                )
                flash('Student and credentials deleted successfully', 'success')
            else:
                flash('Student deleted, but credentials not found in user_credentials', 'warning')

            db.session.commit()

        else:
            flash('Student not found or credential ID missing', 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'danger')
        logging.error(f'Error deleting student: {str(e)}')

    return redirect(url_for('auth.view_batch', table_name=table_name))


@bp.route('/admin/delete_student_batch/<batch_name>', methods=['POST'])
@login_required
def delete_student_batch(batch_name):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.manage_batches'))

    try:
        sql = text(f"DROP TABLE {batch_name}")
        db.session.execute(sql)
        db.session.commit()
        flash('Student batch deleted successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student batch: {str(e)}')

    return redirect(url_for('auth.manage_batches'))


@bp.route('/admin/manage_hods')
@login_required
def manage_hods():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.admin_dashboard'))

    # Fetch HOD details along with credentials and photo path
    sql = text("""
        SELECT h.id, h.credential_id, h.first_name, h.last_name, h.email, h.phone, h.address, 
               h.department, h.office_location, h.appointment_date, h.photo_path
        FROM hod_profiles h
        JOIN user_credentials u ON h.credential_id = u.id
    """)
    hods = db.session.execute(sql).fetchall()

    return render_template('dashboard/manage_hods.html', hods=hods)



@bp.route('/admin/manage_teachers')
@login_required
def manage_teachers():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required', 'danger')
        return redirect(url_for('auth.admin_dashboard'))

    try:
        # Fetch Teacher details along with credentials using raw SQL
        sql = text("""
            SELECT t.id, t.credential_id, t.first_name, t.last_name, t.phone, 
                   t.address, t.department, t.photo_path, u.email
            FROM teacher_details t
            JOIN user_credentials u ON t.credential_id = u.id
        """)
        teachers = db.session.execute(sql).fetchall()

        return render_template('dashboard/manage_teachers.html', teachers=teachers)

    except Exception as e:
        flash(f"Error fetching teacher details: {str(e)}", "danger")
        return redirect(url_for('auth.admin_dashboard'))





@bp.route('/admin/update_hod/<int:hod_id>', methods=['POST'])
@login_required
def update_hod(hod_id):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required', 'danger')
        return redirect(url_for('auth.manage_hods'))

    try:
        # Get existing HOD details, including the photo path
        hod_query = db.session.execute(
            text("SELECT credential_id, photo_path FROM hod_profiles WHERE id = :hod_id"),
            {"hod_id": hod_id}
        ).fetchone()

        if hod_query:
            credential_id = hod_query[0]
            old_photo_path = hod_query[1]  # Old photo filename

            # Extract updated values from the form
            department = request.form.get("department")
            office_location = request.form.get("office_location")
            email = request.form.get("email")
            new_photo = request.files.get("photo")  # New photo file

            # Handle photo update
            new_photo_filename = old_photo_path  # Default: Keep the old one

            if new_photo and new_photo.filename:  # If user uploads a new photo
                filename = secure_filename(new_photo.filename)
                new_photo_filename = f"hod_{hod_id}_{filename}"  # Unique filename
                photo_path = os.path.join(current_app.root_path, 'static/uploads', new_photo_filename)

                # Delete the old photo if it exists
                if old_photo_path:
                    old_photo_full_path = os.path.join(current_app.root_path, 'static/uploads', old_photo_path)
                    if os.path.exists(old_photo_full_path):
                        os.remove(old_photo_full_path)

                # Save the new photo
                new_photo.save(photo_path)

            # Update HOD details in the database
            sql = """
            UPDATE hod_profiles 
            SET email=:email, department=:department, office_location=:office_location, photo_path=:photo_path
            WHERE id=:hod_id
            """
            db.session.execute(text(sql), {
                "email": email,
                "department": department,
                "office_location": office_location,
                "photo_path": new_photo_filename,
                "hod_id": hod_id
            })

            # Update email in `user_credentials` table
            sql = """
            UPDATE user_credentials 
            SET email=:email 
            WHERE id=:credential_id
            """
            db.session.execute(text(sql), {"email": email, "credential_id": credential_id})

            db.session.commit()
            flash('HOD details and photo updated successfully!', 'success')

        else:
            flash('HOD not found or credential ID missing', 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating HOD: {str(e)}', 'danger')

    return redirect(url_for('auth.manage_hods'))

@bp.route('/admin/delete_hod/<int:hod_id>', methods=['GET','POST'])
@login_required
def delete_hod(hod_id):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.manage_hods'))

    try:
        # Get the HOD's credential_id and photo path before deleting
        hod_query = db.session.execute(
            text("SELECT credential_id, photo_path FROM hod_profiles WHERE id = :hod_id"),
            {"hod_id": hod_id}
        )
        hod = hod_query.fetchone()  # Fetch only one row (assuming ID is unique)

        if hod:
            credential_id, photo_path = hod  # Extract values

            # Delete the profile photo if it exists
            if photo_path:
                photo_file_path = os.path.join(current_app.root_path, 'static', 'uploads', photo_path)
                if os.path.exists(photo_file_path):
                    os.remove(photo_file_path)

            # Delete the HOD record
            db.session.execute(text("DELETE FROM hod_profiles WHERE id = :hod_id"), {"hod_id": hod_id})

            # Delete from `user_credentials`
            db.session.execute(text("DELETE FROM user_credentials WHERE id = :credential_id"), {"credential_id": credential_id})

            db.session.commit()
            flash('HOD, credentials, and profile photo deleted successfully', 'success')

        else:
            flash('HOD not found or credential ID missing', 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting HOD: {str(e)}', 'danger')

    return redirect(url_for('auth.manage_hods'))

@bp.route('/admin/update_teacher/<int:teacher_id>', methods=['POST'])
@login_required
def update_teacher(teacher_id):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.manage_teachers'))

    try:
        # Get the credential_id and existing photo path before updating
        teacher_query = db.session.execute(
            text("SELECT credential_id FROM teacher_details WHERE id = :teacher_id"),
            {"teacher_id": teacher_id}
        ).fetchone()

        if not teacher_query:
            flash('Teacher not found!', 'danger')
            return redirect(url_for('auth.manage_teachers'))

        credential_id = teacher_query[0]

        # Extract updated values from the form
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        department = request.form.get("department")

        # Define upload folder
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'teacher_photos')
        os.makedirs(upload_folder, exist_ok=True)

        # Handle new photo upload (overwrite existing)
        new_photo = request.files.get("photo")
        photo_path = f"teacher_{teacher_id}.jpg"  # Consistent naming

        if new_photo and new_photo.filename:
            new_photo.save(os.path.join(upload_folder, f"teacher_{teacher_id}.jpg"))

        # Update Teacher details
        sql = """
        UPDATE teacher_details 
        SET first_name=:first_name, last_name=:last_name, email=:email, 
            phone=:phone, address=:address, department=:department, photo_path=:photo_path
        WHERE id=:teacher_id
        """
        db.session.execute(text(sql), {
            "first_name": first_name, "last_name": last_name, "email": email,
            "phone": phone, "address": address, "department": department,
            "photo_path": photo_path,  # Ensures photo path is updated
            "teacher_id": teacher_id
        })

        # Update user_credentials table (email and name)
        sql = """
        UPDATE user_credentials 
        SET email=:email,
        WHERE id=:credential_id
        """
        db.session.execute(text(sql), {
            "email": email,
            "credential_id": credential_id
        })

        db.session.commit()
        flash('Teacher updated successfully', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating Teacher: {str(e)}', 'danger')

    return redirect(url_for('auth.manage_teachers'))




@bp.route('/admin/delete_teacher/<int:teacher_id>', methods=['GET','POST'])
@login_required
def delete_teacher(teacher_id):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for('auth.manage_teachers'))

    try:
        # Get the teacher's credential_id and photo path before deleting
        teacher_query = db.session.execute(
            text("SELECT credential_id, photo_path FROM teacher_details WHERE id = :teacher_id"),
            {"teacher_id": teacher_id}
        )
        teacher = teacher_query.fetchone()

        if teacher:
            credential_id, photo_path = teacher  # Extract values from the query result

            # Delete the profile photo if it exists
            if photo_path:
                photo_file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'teacher_photos', photo_path)
                if os.path.exists(photo_file_path):
                    os.remove(photo_file_path)

            # Delete the Teacher record
            db.session.execute(text("DELETE FROM teacher_details WHERE id = :teacher_id"), {"teacher_id": teacher_id})

            # Delete from `user_credentials`
            db.session.execute(text("DELETE FROM user_credentials WHERE id = :credential_id"), {"credential_id": credential_id})

            db.session.commit()
            flash('Teacher, credentials, and profile photo deleted successfully', 'success')

        else:
            flash('Teacher not found', 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting Teacher: {str(e)}', 'danger')

    return redirect(url_for('auth.manage_teachers'))























@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    courses = Course.query.all()
    course_subjects = CourseSubject.query.all()
    result = db.session.execute(text("SHOW TABLES LIKE 'student_batch_%'"))
    tables = [row[0] for row in result.fetchall()]  # Fetch all table names
    print(tables)
    # Fetch all existing student batch data for dropdown handling

    return render_template(
        'dashboard/admin.html',
        courses=courses,
        course_subjects=course_subjects,
        table_names = tables
    )


@bp.route('/hod/dashboard')
@login_required
def hod_dashboard():
    if current_user.role != 'hod':
        flash('Access denied: HOD privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    # Get all teachers in the HOD's department with their details
    teachers = TeacherDetails.query.filter_by(
        department=current_user.hod_profile.department
    ).all()

    # Get all courses
    courses = Course.query.all()

    # Get all subject assignments for the department
    subject_assignments = SubjectAssignment.query.join(CourseSubject).filter(
        CourseSubject.course_id == Course.id
    ).all()

    return render_template('dashboard/hod.html',
                         teachers=teachers,
                         courses=courses,
                         subject_assignments=subject_assignments)

@bp.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied: Teacher privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    # Get assigned subjects for the teacher
    assigned_subjects = SubjectAssignment.query.filter_by(
        teacher_id=current_user.teacher_profile.id,
        is_active=True
    ).all()

    return render_template('dashboard/teacher.html',
                         assigned_subjects=assigned_subjects)

@bp.route('/teacher/take_attendance/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def take_attendance(subject_id):
    if current_user.role != 'teacher':
        flash('Access denied: Teacher privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    subject = CourseSubject.query.get_or_404(subject_id)
    if request.method == 'POST':
        try:
            date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            for key, value in request.form.items():
                if key.startswith('student_'):
                    student_id = int(key.split('_')[1])
                    attendance = Attendance(
                        subject_id=subject_id,
                        student_id=student_id,
                        teacher_id=current_user.teacher_profile.id,
                        date=date,
                        status=value,
                        remarks=request.form.get(f'remarks_{student_id}', '')
                    )
                    db.session.add(attendance)

            db.session.commit()
            flash('Attendance recorded successfully')
            return redirect(url_for('auth.teacher_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error recording attendance: {str(e)}')
            logging.error(f'Error recording attendance: {str(e)}')

    # Get students for the subject's year and semester.  Hardcoded for now, needs improvement.
    students = StudentDetails.query.filter_by(
        current_year=subject.year,  # Assuming subject.year is available
        department=subject.department # Assuming subject.department is available
    ).all()

    return render_template('dashboard/take_attendance.html',
                         subject=subject,
                         students=students,
                         today=datetime.now().date())

@bp.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied: Student privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))
    return render_template('dashboard/student.html')

@bp.route('/get_subjects')
@login_required
def get_subjects():
    if current_user.role != 'hod':
        return jsonify({'error': 'Unauthorized'}), 403

    year = request.args.get('year')
    semester = request.args.get('semester')
    course_id = request.args.get('course_id')

    if not all([year, semester, course_id]):
        return jsonify({'error': 'Missing parameters'}), 400

    subjects = CourseSubject.query.filter_by(
        year=year,
        semester=semester,
        course_id=course_id
    ).all()

    return jsonify({
        'subjects': [{
            'id': subject.id,
            'subject_name': subject.subject_name
        } for subject in subjects]
    })

@bp.route('/hod/assign_subject', methods=['POST'])
@login_required
def assign_subject():
    if current_user.role != 'hod':
        flash('Access denied: HOD privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    try:
        subject_id = request.form.get('subject_id')
        teacher_id = request.form.get('teacher_id')

        subject = CourseSubject.query.get_or_404(subject_id)

        # Create the assignment
        assignment = SubjectAssignment(
            subject_id=subject_id,
            teacher_id=teacher_id,
            hod_id=current_user.hod_profile.id,
            academic_year=datetime.utcnow().year
        )

        db.session.add(assignment)
        db.session.commit()

        flash('Subject assigned successfully')
        logging.info(f'Subject {subject.subject_name} assigned to teacher {teacher_id}')

    except Exception as e:
        db.session.rollback()
        flash(f'Error assigning subject: {str(e)}')
        logging.error(f'Error assigning subject: {str(e)}')

    return redirect(url_for('auth.hod_dashboard'))

@bp.route('/hod/remove_subject_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def remove_subject_assignment(assignment_id):
    if current_user.role != 'hod':
        flash('Access denied: HOD privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    try:
        assignment = SubjectAssignment.query.get_or_404(assignment_id)
        db.session.delete(assignment)
        db.session.commit()
        flash('Subject assignment removed successfully')

    except Exception as e:
        db.session.rollback()
        flash(f'Error removing subject assignment: {str(e)}')
        logging.error(f'Error removing subject assignment: {str(e)}')

    return redirect(url_for('auth.hod_dashboard'))

@bp.route('/admin/add_course', methods=['POST'])
@login_required
def add_course():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    try:
        course = Course(
            code=request.form.get('course_code'),
            name=request.form.get('course_name')
        )
        db.session.add(course)
        db.session.commit()
        flash('Course added successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding course: {str(e)}')
        logging.error(f'Error adding course: {str(e)}')

    return redirect(url_for('auth.admin_dashboard'))


@bp.route('/admin/add_course_subject', methods=['POST'])
@login_required
def add_course_subject():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    course_id = request.form.get('course_id')
    year = request.form.get('year')
    semester = request.form.get('semester')
    batch_id = request.form.get('batch_id')
    subject_code = request.form.get('subject_code')
    subject_name = request.form.get('subject_name')

    # Validate required fields
    if not all([course_id, year, semester, batch_id, subject_code, subject_name]):
        flash('All fields are required!')
        return redirect(url_for('auth.admin_dashboard'))

    try:
        # Check if subject already exists for the same batch
        existing_subject = CourseSubject.query.filter_by(
            course_id=course_id, year=year, semester=semester, batch_id=batch_id, subject_code=subject_code
        ).first()

        if existing_subject:
            flash('Subject already exists for the selected course and batch!')
        else:
            new_subject = CourseSubject(
                course_id=course_id,
                year=int(year),
                semester=int(semester),
                batch_id=batch_id,
                subject_code=subject_code,
                subject_name=subject_name
            )
            db.session.add(new_subject)
            db.session.commit()
            flash('Subject added successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding subject: {str(e)}')
        logging.error(f'Error adding subject: {str(e)}')

    return redirect(url_for('auth.admin_dashboard'))


@bp.route('/admin/database')
@login_required
def database_management():
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    # Get all models from SQLAlchemy
    models_list = []
    for cls in db.Model._decl_class_registry.values():
        if isinstance(cls, type) and issubclass(cls, db.Model):
            if hasattr(cls, '__tablename__'):
                count = db.session.query(cls).count()
                models_list.append({
                    'name': cls.__name__,
                    'table': cls.__tablename__,
                    'columns': [column.name for column in cls.__table__.columns],
                    'count': count
                })

    return render_template('dashboard/database.html', models=models_list)

@bp.route('/admin/database/<table_name>')
@login_required
def view_table(table_name):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    # Get the model class for the table
    model = None
    for cls in db.Model._decl_class_registry.values():
        if isinstance(cls, type) and issubclass(cls, db.Model):
            if hasattr(cls, '__tablename__') and cls.__tablename__ == table_name:
                model = cls
                break

    if not model:
        flash(f'Table {table_name} not found')
        return redirect(url_for('auth.database_management'))

    # Get search parameter
    search = request.args.get('search', '').strip()

    # Get table data with optional search
    query = model.query
    if search:
        # Create search conditions for string columns
        conditions = []
        for column in model.__table__.columns:
            if isinstance(column.type, db.String):
                conditions.append(column.ilike(f'%{search}%'))
        if conditions:
            query = query.filter(or_(*conditions))

    records = query.all()
    columns = [column.name for column in model.__table__.columns]

    return render_template('dashboard/table_view.html',
                         table_name=table_name,
                         columns=columns,
                         records=records)

@bp.route('/admin/database/<table_name>/schema')
@login_required
def view_schema(table_name):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Get the model class for the table
    model = None
    for cls in db.Model._decl_class_registry.values():
        if isinstance(cls, type) and issubclass(cls, db.Model):
            if hasattr(cls, '__tablename__') and cls.__tablename__ == table_name:
                model = cls
                break

    if not model:
        return jsonify({'error': 'Table not found'}), 404

    # Get schema information
    inspector = inspect(db.engine)
    columns = []
    for column in inspector.get_columns(table_name):
        columns.append({
            'name': column['name'],
            'type': str(column['type']),
            'nullable': column['nullable'],
            'default': str(column['default']) if column['default'] else None,
            'primary_key': column['primary_key']
        })

    return jsonify({'columns': columns})

@bp.route('/admin/database/<table_name>/export')
@login_required
def export_table(table_name):
    if current_user.role != 'admin':
        flash('Access denied: Admin privileges required')
        return redirect(url_for(f'auth.{current_user.role}_dashboard'))

    # Get the model class for the table
    model = None
    for cls in db.Model._decl_class_registry.values():
        if isinstance(cls, type) and issubclass(cls, db.Model):
            if hasattr(cls, '__tablename__') and cls.__tablename__ == table_name:
                model = cls
                break

    if not model:
        flash(f'Table {table_name} not found')
        return redirect(url_for('auth.database_management'))

    # Create CSV data
    si = StringIO()
    writer = csv.writer(si)

    # Write headers
    columns = [column.name for column in model.__table__.columns]
    writer.writerow(columns)

    # Write data
    records = model.query.all()
    for record in records:
        row = [getattr(record, column) for column in columns]
        writer.writerow(row)

    output = si.getvalue()
    si.close()

    # Create the response
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{table_name}.csv'
    )
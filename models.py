from sqlalchemy import func

from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone


class UserCredentials(UserMixin, db.Model):
    __tablename__ = 'user_credentials'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class TeacherDetails(db.Model):
    __tablename__ = 'teacher_details'

    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('user_credentials.id'), unique=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    photo_path = db.Column(db.String(500))  # Optional photo storage
    department = db.Column(db.String(64), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False, server_default=func.now())

    # Relationships
    credentials = db.relationship('UserCredentials', backref=db.backref('teacher_profile', uselist=False))
    assigned_subjects = db.relationship('SubjectAssignment', backref='teacher', lazy=True)
    uploaded_materials = db.relationship('StudyMaterial', backref='teacher', lazy=True)
    attendance_records = db.relationship('Attendance', backref='teacher', lazy=True)

class StudentDetails(db.Model):
    __tablename__ = 'student_details'

    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('user_credentials.id'), unique=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    photo_path = db.Column(db.String(500))  # Optional photo storage
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    current_year = db.Column(db.Integer, nullable=False)
    current_semester = db.Column(db.Integer, nullable=False)
    admission_year = db.Column(db.Integer, nullable=False)
    course = db.Column(db.String(10), nullable=False)
    batch = db.Column(db.String(10), nullable=False)
    department = db.Column(db.String(64), nullable=False)
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    credentials = db.relationship('UserCredentials', backref=db.backref('student_profile', uselist=False))
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)

class AdminProfile(db.Model):
    __tablename__ = 'admin_profiles'

    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('user_credentials.id'), unique=True)
    department = db.Column(db.String(64))
    access_level = db.Column(db.String(20), default='full')

    # Relationship
    credentials = db.relationship('UserCredentials', backref=db.backref('admin_profile', uselist=False))

class HODProfile(db.Model):
    __tablename__ = 'hod_profiles'

    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.Integer, db.ForeignKey('user_credentials.id', ondelete="CASCADE"), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    photo_path = db.Column(db.String(500))
    department = db.Column(db.String(64), nullable=False)
    office_location = db.Column(db.String(64))
    appointment_date = db.Column(db.DateTime, nullable=False, server_default=func.now())

    # Relationships
    credentials = db.relationship('UserCredentials', backref=db.backref('hod_profile', uselist=False, cascade="all, delete"))
    subject_assignments = db.relationship('SubjectAssignment', backref='hod', lazy=True)

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class CourseSubject(db.Model):
    __tablename__ = 'course_subjects'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    batch_id = db.Column(db.Integer, nullable=False)  # Batch ID field
    subject_code = db.Column(db.String(20), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)  # Admission year, e.g., 2024
    semester = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    course = db.relationship('Course', backref='subjects')

class SubjectAssignment(db.Model):
    __tablename__ = 'subject_assignments'

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_details.id'), nullable=False)
    hod_id = db.Column(db.Integer, db.ForeignKey('hod_profiles.id'), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    subject = db.relationship('CourseSubject', backref='assignments')

class StudyMaterial(db.Model):
    __tablename__ = 'study_materials'

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_details.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('course_subjects.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_details.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher_details.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    remarks = db.Column(db.String(200))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(id):
    return UserCredentials.query.get(int(id))


def create_test_data():
    try:
        # Create admin user if it doesn't exist
        admin = UserCredentials.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = UserCredentials(
                email='admin@example.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()  # Get the ID before creating profile

            admin_profile = AdminProfile(
                credential_id=admin.id,
                department='Administration',
                access_level='full'
            )
            db.session.add(admin_profile)
            db.session.commit()
            print("Admin user created successfully")

        # Ensure courses exist
        cse = Course.query.filter_by(code='CSE').first()
        if not cse:
            cse = Course(code='CSE', name='Computer Science and Engineering')
            db.session.add(cse)
            db.session.commit()

        ece = Course.query.filter_by(code='ECE').first()
        if not ece:
            ece = Course(code='ECE', name='Electronics and Communication Engineering')
            db.session.add(ece)
            db.session.commit()

        # Hardcoded batch IDs as integers
        batch_ids = {
            "CSE_2024": 101,
            "CSE_2023": 102,
            "CSE_2022": 103,
            "ECE_2024": 201,
            "ECE_2023": 202
        }

        # Create test subjects for CSE
        existing_subjects = CourseSubject.query.filter_by(course_id=cse.id).all()
        existing_codes = {subject.subject_code for subject in existing_subjects}

        cse_subjects = []
        for subject_data in [
            {'code': 'CS101', 'name': 'Introduction to Programming', 'year': 2024, 'semester': 1,
             'batch_id': batch_ids["CSE_2024"]},
            {'code': 'CS102', 'name': 'Digital Logic', 'year': 2024, 'semester': 1, 'batch_id': batch_ids["CSE_2024"]},
            {'code': 'CS103', 'name': 'Data Structures', 'year': 2024, 'semester': 2,
             'batch_id': batch_ids["CSE_2024"]},
            {'code': 'CS201', 'name': 'Object Oriented Programming', 'year': 2023, 'semester': 1,
             'batch_id': batch_ids["CSE_2023"]},
            {'code': 'CS202', 'name': 'Computer Architecture', 'year': 2023, 'semester': 1,
             'batch_id': batch_ids["CSE_2023"]},
            {'code': 'CS301', 'name': 'Database Systems', 'year': 2022, 'semester': 1,
             'batch_id': batch_ids["CSE_2022"]},
            {'code': 'CS302', 'name': 'Operating Systems', 'year': 2022, 'semester': 1,
             'batch_id': batch_ids["CSE_2022"]},
        ]:
            if subject_data['code'] not in existing_codes:
                subject = CourseSubject(
                    course_id=cse.id,
                    subject_code=subject_data['code'],
                    subject_name=subject_data['name'],
                    year=subject_data['year'],
                    semester=subject_data['semester'],
                    batch_id=subject_data['batch_id']
                )
                cse_subjects.append(subject)

        # Create test subjects for ECE
        existing_subjects = CourseSubject.query.filter_by(course_id=ece.id).all()
        existing_codes = {subject.subject_code for subject in existing_subjects}

        ece_subjects = []
        for subject_data in [
            {'code': 'EC101', 'name': 'Basic Electronics', 'year': 2024, 'semester': 1,
             'batch_id': batch_ids["ECE_2024"]},
            {'code': 'EC102', 'name': 'Circuit Theory', 'year': 2024, 'semester': 1, 'batch_id': batch_ids["ECE_2024"]},
            {'code': 'EC201', 'name': 'Analog Electronics', 'year': 2023, 'semester': 1,
             'batch_id': batch_ids["ECE_2023"]},
            {'code': 'EC202', 'name': 'Digital Electronics', 'year': 2023, 'semester': 1,
             'batch_id': batch_ids["ECE_2023"]},
        ]:
            if subject_data['code'] not in existing_codes:
                subject = CourseSubject(
                    course_id=ece.id,
                    subject_code=subject_data['code'],
                    subject_name=subject_data['name'],
                    year=subject_data['year'],
                    semester=subject_data['semester'],
                    batch_id=subject_data['batch_id']
                )
                ece_subjects.append(subject)

        if cse_subjects or ece_subjects:
            db.session.add_all(cse_subjects + ece_subjects)
            db.session.commit()
            return "Test data added successfully"

        return "No new test data was added (all subjects exist)"

    except Exception as e:
        db.session.rollback()
        # logging.error(f"Error creating test data: {str(e)}")
        return f"Error: {str(e)}"


    except Exception as e:
        db.session.rollback()
        raise e
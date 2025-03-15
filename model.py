from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified

db = SQLAlchemy()

class Schools(db.Model):
    __tablename__ = 'Schools'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.Date, nullable=False)
    School_Name = db.Column(db.Text, nullable=False)
    User = db.Column(db.Text, unique=True, nullable=False)
    Address = db.Column(db.Text, nullable=False)
    UDISE = db.Column(db.Text, unique=True, nullable=False)
    Phone = db.Column(db.Text, nullable=False)
    WhatsApp = db.Column(db.Text, nullable=False)
    Email = db.Column(db.Text, unique=True, nullable=False)
    Password = db.Column(db.Text, nullable=False)
    Classes = db.Column(db.JSON)
    IP = db.Column(db.JSON)
    Logo = db.Column(db.Text)
    Manager = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.Text, nullable=False)
    
class FeesDB(db.Model):
    __tablename__ = 'FeesDB'
    id = db.Column(db.Integer, primary_key=True)
    CLASS = db.Column(db.Text, nullable=False)
    Fee = db.Column(db.Integer, nullable=False)
    school_id = db.Column(db.Text, nullable=False)

class TeachersLogin(db.Model):
    __tablename__ = 'TeachersLogin'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    Classes = db.Column(db.JSON, nullable=False)
    ip = db.Column(db.JSON)
    role = db.Column(db.Text, nullable=False)
    school_id = db.Column(db.Text, nullable=False)

class StudentsDB(db.Model):
    __tablename__ = 'StudentsDB'
    id = db.Column(db.Integer, primary_key=True)
    STUDENTS_NAME = db.Column(db.Text, nullable=False)
    DOB = db.Column(db.Date)
    CLASS = db.Column(db.Text, nullable=False)
    ROLL = db.Column(db.Integer, nullable=False)
    PHONE = db.Column(db.Text)
    PEN = db.Column(db.Text)
    GENDER = db.Column(db.Text, nullable=False)
    SR = db.Column(db.Integer)
    ADDRESS = db.Column(db.Text)
    HEIGHT = db.Column(db.Integer)
    WEIGHT = db.Column(db.Integer)
    CAST = db.Column(db.Text)
    RELIGION = db.Column(db.Text)
    PIN = db.Column(db.Text)
    IMAGE = db.Column(db.Text)
    AADHAAR = db.Column(db.Text)
    FATHERS_NAME = db.Column(db.Text)
    MOTHERS_NAME = db.Column(db.Text)
    ADMISSION_SESSION = db.Column(db.Text)
    ADMISSION_NO = db.Column(db.Integer)
    ADMISSION_DATE = db.Column(db.Date)
    FA1 = db.Column(db.JSON)
    SA1 = db.Column(db.JSON)
    FA2 = db.Column(db.JSON)
    SA2 = db.Column(db.JSON)
    Fees = db.Column(db.JSON)
    Parents_Aadhar = db.Column(db.JSON)
    Free_Scheme = db.Column(db.JSON)
    school_id = db.Column(db.Text, nullable=False)
    Attendance = db.Column(db.Text)
    BLOOD_GROUP = db.Column(db.Text)
    FATHERS_AADHAR = db.Column(db.Text)
    MOTHERS_AADHAR = db.Column(db.Text)
    Previous_School = db.Column(db.Text)
    OCCUPATION = db.Column(db.Text)

    __table_args__ = (
        db.Index('idx_class_roll', 'CLASS', 'ROLL'),
    )
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    
def updateFees(id, months=None, date=None, extra=None):
    student = StudentsDB.query.filter_by(id=id).first()

    if student:
        fees = student.Fees or {}  # Default to empty dict if Fees is None

        if months:
            for month in months:
                fees[month] = date

        if extra:
            fees["Extra"] = int(fees.get("Extra", 0)) + extra


        student.Fees = fees  # Explicitly reassign the updated dictionary
        
        db.session.add(student)  # Notify SQLAlchemy about the update
        flag_modified(student, 'Fees')
        db.session.commit()        

        return "SUCCESS"


def updateScore(id, exam, subject, score):
    student = StudentsDB.query.filter_by(id=id).first()
    

    try:
        if exam=="Attendance":
            
            student.Attendance = score

        else:
            student_data = getattr(student, exam)  # Retrieve the JSON object
            student_data[subject] = score  # Modify the JSON object with the new score
            setattr(student, exam, student_data)  # Reassign the modified JSON back to the column
            flag_modified(student, exam)  # Flag the JSON column as modified

        db.session.commit()
        return "SUCCESS"
    except:
        return "FAILED"

def StudentData(*args, class_filter_json=None):
    # Class order mapping for post-query sorting
    class_order_mapping = {
        'Nursery/KG/PP3': 1, 'LKG/KG1/PP2': 2,
        'UKG/KG2/PP1': 3, '1st': 4,
        '2nd': 5, '3rd': 6,
        '4th': 7, '5th': 8,
        '6th': 9, '7th': 10, '8th': 11
    }

    # Determine columns to select; include 'CLASS' by default
    selected_columns = [getattr(StudentsDB, col) for col in args if hasattr(StudentsDB, col)]
    if not any(col.key == 'CLASS' for col in selected_columns):
        selected_columns.append(StudentsDB.CLASS)

    # Construct query with selected columns
    query = StudentsDB.query.with_entities(*selected_columns)

    # Apply class filter if provided
    if class_filter_json and 'CLASS' in class_filter_json:
        query = query.filter(StudentsDB.CLASS.in_(class_filter_json['CLASS']))

    # Order results directly in the query
    query = query.order_by(StudentsDB.CLASS.asc(), StudentsDB.ROLL.asc()).yield_per(1000)

    # Fetch all results
    results = query.all()

    # Map the selected column names to their values in each row
    column_names = [col.key for col in selected_columns]  # Get the names of selected columns
    results_json = [
        dict(zip(column_names, row)) for row in results
    ]

    # Sort by class order mapping
    results_json.sort(key=lambda row: (class_order_mapping.get(row['CLASS'], float('inf')), row['ROLL']))

    for student in results_json:
        student["CLASS"]=student["CLASS"].split("/")[0]

    return results_json

def updateCell(id, colum, value):
    student = StudentsDB.query.filter_by(id=id).first()
    if student:

        setattr(student, colum, value)
        flag_modified(student, colum)
        
        db.session.commit()
        return 'SUCCESS'
    else:
        return 'FAILED'


def Verhoeff(aadhar_number: str) -> bool:
    """
    Validates the Aadhaar number using the Verhoeff algorithm.
    
    Parameters:
        aadhar_number (str): The Aadhaar number as a string (it can include hyphens or spaces).
    
    Returns:
        bool: True if the Aadhaar number is valid, False otherwise.
    """
    # Clean the input: remove hyphens and spaces.
    aadhar_number = aadhar_number.replace("-", "").replace(" ", "")
    
    # Ensure the number consists of exactly 12 digits.
    if not aadhar_number.isdigit() or len(aadhar_number) != 12:
        return False

    # The multiplication table d
    d = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]
    
    # The permutation table p
    p = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
    ]
    
    # Initialize checksum to 0.
    c = 0

    # Process each digit, starting from the rightmost digit.
    for i, digit in enumerate(reversed(aadhar_number)):
        c = d[c][p[i % 8][int(digit)]]
    
    # Return True if the final checksum is 0, otherwise False.
    if c == 0:
        return True
    else:
        return False

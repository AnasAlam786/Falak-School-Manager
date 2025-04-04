from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import (
    Column, Integer, BigInteger, Text, Date, DateTime, Boolean, Numeric, JSON,
    ForeignKey, func, case, literal, cast, String
)


from itertools import groupby
from operator import itemgetter
from collections import defaultdict

db = SQLAlchemy()

class Schools(db.Model):
    __tablename__ = 'Schools'
    
    id = Column(Text, primary_key=True)  # Primary key, text type
    created_at = Column(Date, nullable=False)
    School_Name = Column(Text, nullable=True)         # In DB, School_Name is nullable
    Address = Column(Text, nullable=True)               # In DB, Address is nullable
    Logo = Column(Text, nullable=True)
    UDISE = Column(Text, unique=True, nullable=True)    # In DB, UDISE is nullable but unique
    Phone = Column(Text, nullable=True)
    WhatsApp = Column(Text, nullable=True, server_default='')  # Default empty string
    Email = Column(Text, unique=True, nullable=True)
    Password = Column(Text, nullable=True)
    Manager = Column(Text, nullable=False)
    Classes = Column(JSON, nullable=False)              # Not null in DB
    IP = Column(JSON, nullable=True)
    session_id = Column(Text, nullable=False)
    
    # Relationships
    students = db.relationship("StudentsDB", back_populates="school")
    class_data = db.relationship("ClassData", back_populates="school")
    students_marks = db.relationship("StudentsMarks", back_populates="school")
    fees_data = db.relationship("FeesData", back_populates="school")
    teachers = db.relationship("TeachersLogin", back_populates="school")


class Sessions(db.Model):
    __tablename__ = 'Sessions'
    
    id = Column(BigInteger, primary_key=True)
    created_at = Column(Date, nullable=False)
    session = Column(Text, unique=True, nullable=False)
    current_session = Column(Boolean, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Relationships
    students = db.relationship("StudentsDB", back_populates="session")
    fees_data = db.relationship("FeesData", back_populates="session")
    student_sessions = db.relationship("StudentSessions", back_populates="session")
    students_marks = db.relationship("StudentsMarks", back_populates="session")


class ClassData(db.Model):
    __tablename__ = 'ClassData'
    
    id = Column(BigInteger, primary_key=True)
    CLASS = Column(Text, nullable=False)
    Fee = Column(Integer, nullable=False)
    Numeric_Subjects = Column(JSON, nullable=False)
    exam_format = Column(JSON, nullable=False)
    Grading_Subjects = Column(JSON, nullable=True)
    Section = Column(Text, nullable=True)   # Added Section column as per DB
    
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    school = db.relationship("Schools", back_populates="class_data")
    
    # Relationships
    student_sessions =  db.relationship("StudentSessions", back_populates="class_data")
    students = db.relationship("StudentsDB", back_populates="class_data")
    fees_data = db.relationship("FeesData", back_populates="class_data")
    teachers = db.relationship("TeachersLogin", back_populates="class_data")


class FeesData(db.Model):
    __tablename__ = 'FeesData'
    
    id = Column(BigInteger, primary_key=True)
    created_at = Column(Date, nullable=False)
    Fee = Column(Numeric, nullable=False)  # Using Numeric to match DB type
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=True)
    class_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=True)
    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=True)
    
    school = db.relationship("Schools", back_populates="fees_data")
    class_data = db.relationship("ClassData", back_populates="fees_data")
    session = db.relationship("Sessions", back_populates="fees_data")


class StudentsDB(db.Model):
    __tablename__ = 'StudentsDB'
    
    id = Column(BigInteger, primary_key=True)
    STUDENTS_NAME = Column(Text, nullable=False)
    DOB = Column(Date, nullable=True)
    class_data_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=False)
    AADHAAR = Column(Text, nullable=True)
    FATHERS_NAME = Column(Text, nullable=True)
    MOTHERS_NAME = Column(Text, nullable=True)
    PHONE = Column(Text, nullable=True)
    ADMISSION_NO = Column(BigInteger, nullable=True)
    PEN = Column(Text, nullable=True)
    GENDER = Column(Text, nullable=True)
    ADMISSION_SESSION = Column(Text, nullable=True)
    ADDRESS = Column(Text, nullable=True)
    HEIGHT = Column(Integer, nullable=True)
    WEIGHT = Column(Integer, nullable=True)
    CAST = Column(Text, nullable=True)
    RELIGION = Column(Text, nullable=True)
    PIN = Column(Text, nullable=True)
    ADMISSION_DATE = Column(Date, nullable=True)
    SR = Column(Integer, nullable=True)
    IMAGE = Column(Text, nullable=True)
    FA1 = Column(JSON, nullable=True)
    SA1 = Column(JSON, nullable=True)
    FA2 = Column(JSON, nullable=True)
    SA2 = Column(JSON, nullable=True)
    Fees = Column(JSON, nullable=True)
    Previous_School_Marks = Column(Integer, nullable=True)  # smallint in DB; using Integer here
    Previous_School_Attendance = Column(BigInteger, nullable=True)
    Home_Distance = Column(Text, nullable=True)
    Free_Scheme = Column(JSON, nullable=True)
    Attendance = Column(Text, nullable=True)
    BLOOD_GROUP = Column(Text, nullable=True)
    FATHERS_AADHAR = Column(Text, nullable=True)
    MOTHERS_AADHAR = Column(Text, nullable=True)
    FATHERS_EDUCATION = Column(Text, nullable=True)
    MOTHERS_EDUCATION = Column(Text, nullable=True)
    OCCUPATION = Column(Text, nullable=True)
    Previous_School_Name = Column(Text, nullable=True)
    APAAR = Column(Text, nullable=True)

    Admission_Class = Column(Numeric, nullable=True)

    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=True)
    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=False)
    
    school = db.relationship("Schools", back_populates="students")
    class_data = db.relationship("ClassData", back_populates="students")
    session = db.relationship("Sessions", back_populates="students")
    
    student_sessions = db.relationship("StudentSessions", back_populates="students")
    students_marks = db.relationship("StudentsMarks", back_populates="students")


class StudentSessions(db.Model):
    __tablename__ = 'StudentSessions'
    
    id = Column(BigInteger, primary_key=True)
    student_id = Column(BigInteger, ForeignKey('StudentsDB.id', onupdate="CASCADE"), nullable=False)
    class_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=False)
    ROLL = Column(Integer, nullable=True)
    Height = Column(Integer, nullable=True)
    Weight = Column(Integer, nullable=True)
    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=False)
    Attendance = Column(Integer, nullable=True)


    class_data = db.relationship("ClassData", back_populates="student_sessions")
    students = db.relationship("StudentsDB", back_populates="student_sessions")
    session = db.relationship("Sessions", back_populates="student_sessions")


class StudentsMarks(db.Model):
    __tablename__ = 'StudentsMarks'
    
    id = Column(BigInteger, primary_key=True)
    student_id = Column(BigInteger, ForeignKey('StudentsDB.id', onupdate="CASCADE"), nullable=False)
    Subject = Column(Text, nullable=False)
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    FA1 = Column(Text, nullable=True)
    FA2 = Column(Text, nullable=True)
    SA1 = Column(Text, nullable=True)
    SA2 = Column(Text, nullable=True)
    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=False)
    
    school = db.relationship("Schools", back_populates="students_marks")
    students = db.relationship("StudentsDB", back_populates="students_marks")
    session = db.relationship("Sessions", back_populates="students_marks")


class TeachersLogin(db.Model):
    __tablename__ = 'TeachersLogin'
    
    id = Column(Integer, primary_key=True)  # 'serial' is represented as Integer with auto-increment
    Name = Column(Text, nullable=False)
    Email = Column(Text, nullable=False, unique=True)
    Password = Column(Text, nullable=False)
    Classes = Column(Text, nullable=False)  # In DB, this column is text (not JSON)
    Role = Column(Text, nullable=False)
    IP = Column(JSON, nullable=True)
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    Sign = Column(Text, nullable=True)
    User = Column(Text, nullable=False)    # Added missing "User" column as per DB
    class_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=True)
    
    school = db.relationship("Schools", back_populates="teachers")
    class_data = db.relationship("ClassData", back_populates="teachers")


def updateCell(db_name, id, colum, value):
    student = db_name.query.filter_by(id=id).first()
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
    

def handleMarks(exam, replace_by):
    return case(
          # If FA1 consists solely of digits, cast it to Integer.
        (exam.op('~')(r'^[0-9]+(\.[0-9]+)?$'), cast(exam, Numeric)),
    
    else_=replace_by  # Otherwise, return None (SQL NULL), so SUM will ignore it.
)

def GetGrade(number):
    if number >= 80:
        return "A", "Excellent"
    elif number >= 60:
        return "B", "Very Good"
    elif number >= 45:
        return "C", "Good"
    elif number >= 33:
        return "D", "Satisfactory"
    else:
        return "E", "Needs Improvement"


def ResultData(students_ids=None):
    if not students_ids:
        return []

    # Cast marks to Numeric in subject_query
    subject_query = db.session.query(
        StudentsMarks.student_id,
        cast(StudentsMarks.Subject, String).label('Subject'),
        StudentsMarks.FA1.label('FA1'),
        StudentsMarks.SA1.label('SA1'),
        StudentsMarks.FA2.label('FA2'),
        StudentsMarks.SA2.label('SA2'),
        (handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0)).label('FA1_SA1_Total'),
        (handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('FA2_SA2_Total'),
        (handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0) + 
         handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('Grand_Total'),
        cast(literal(None), Integer).label('SA1_Rank'),
        cast(literal(None), Integer).label('SA2_Rank'),
        cast(literal(None), Integer).label('Grand_Rank')
    ).join(StudentsDB, StudentsMarks.student_id == StudentsDB.id
    ).filter(StudentsMarks.student_id.in_(students_ids))

    # Summary query without filtering by student_ids to compute ranks across all students in the class
    summary_query = db.session.query(
        StudentsMarks.student_id,
        cast(literal('Total'), String).label('Subject'),
        cast(func.sum(handleMarks(StudentsMarks.FA1, 0)), String).label('FA1'),
        cast(func.sum(handleMarks(StudentsMarks.SA1, 0)), String).label('SA1'),
        cast(func.sum(handleMarks(StudentsMarks.FA2, 0)), String).label('FA2'),
        cast(func.sum(handleMarks(StudentsMarks.SA2, 0)), String).label('SA2'),
        func.sum(handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0)).label('FA1_SA1_Total'),
        func.sum(handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('FA2_SA2_Total'),
        func.sum(handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0) +
        handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('Grand_Total'),
        func.rank().over(
            partition_by=ClassData.CLASS,
            order_by=func.sum(handleMarks(StudentsMarks.SA1, 0)).desc()
        ).label('SA1_Rank'),
        func.rank().over(
            partition_by=ClassData.CLASS,
            order_by=func.sum(handleMarks(StudentsMarks.SA2, 0)).desc()
        ).label('SA2_Rank'),
        func.rank().over(
            partition_by=ClassData.CLASS,
            order_by=func.sum(
                handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0) +
                handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)
            ).desc()
        ).label('Grand_Rank')
    ).join(StudentsDB, StudentsMarks.student_id == StudentsDB.id
    ).join(ClassData, StudentsDB.class_data_id == ClassData.id
    ).group_by(StudentsMarks.student_id, ClassData.CLASS)  # Removed the student filter here

    combined_query = subject_query.union_all(summary_query)
    results = combined_query.all()

    # Filter results to include only the specified student_ids
    student_ids_set = set(students_ids)
    filtered_results = [row for row in results if row[0] in student_ids_set]

    sorted_results = sorted(filtered_results, key=itemgetter(0))  # Sorting by student_id

    grouped_data = defaultdict(dict)
    for student_id, data in groupby(sorted_results, key=itemgetter(0)):
        grouped_data[student_id] = {
            row[1]: {
                "FA1": row[2], "SA1": row[3], "FA2": row[4], "SA2": row[5],
                "FA1_SA1_Total": row[6], "FA2_SA2_Total": row[7], "Grand_Total": row[8],
                "SA1_Rank": row[9], "SA2_Rank": row[10], "Grand_Rank": row[11]
            }
            for row in data
        }

    return grouped_data


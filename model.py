from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import case, func, literal, cast, Numeric, String, null, Integer, ForeignKey
from sqlalchemy.sql.expression import over
from sqlalchemy.orm import relationship

from itertools import groupby
from operator import itemgetter
from collections import defaultdict


db = SQLAlchemy()

class Schools(db.Model):
    __tablename__ = 'Schools'
    
    created_at = db.Column(db.Date, nullable=False)
    School_Name = db.Column(db.Text, nullable=False)
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
    id = db.Column(db.Text, primary_key=True)

    # One-to-Many Relationship
    students = db.relationship("StudentsDB", back_populates="school")
    classData = db.relationship("ClassData", back_populates="school")
    studentMarks = db.relationship("StudentsMarks", back_populates="school")

    
class ClassData(db.Model):
    __tablename__ = 'ClassData'
    CLASS = db.Column(db.Text, primary_key=True)
    Fee = db.Column(db.Integer, nullable=False)
    Numeric_Subjects = db.Column(db.JSON, nullable=False)
    Grading_Subjects = db.Column(db.JSON)
    exam_format = db.Column(db.JSON, nullable=False)

    school_id = db.Column(db.Text, db.ForeignKey('Schools.id'))
    school = db.relationship("Schools", back_populates="classData")

    # Relationships
    #Going
    students = db.relationship("StudentsDB", back_populates="class_data")
    



class StudentsDB(db.Model):
    __tablename__ = 'StudentsDB'
    id = db.Column(db.Integer, primary_key=True)
    
    STUDENTS_NAME = db.Column(db.Text, nullable=False)
    DOB = db.Column(db.Date)
    
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
    Free_Scheme = db.Column(db.JSON)
    Attendance = db.Column(db.Text)
    BLOOD_GROUP = db.Column(db.Text)
    FATHERS_AADHAR = db.Column(db.Text)
    MOTHERS_AADHAR = db.Column(db.Text)
    Previous_School_Name = db.Column(db.Text)
    OCCUPATION = db.Column(db.Text)

    

    school_id = db.Column(db.Text, db.ForeignKey('Schools.id'))     # StudentsDB.school_id <----  Schools.id
    CLASS = db.Column(db.Text, db.ForeignKey('ClassData.CLASS'))  # StudentsDB.CLASS     <----- ClassData.CLASS

    #comming
    school = db.relationship("Schools", back_populates="students")
    class_data = db.relationship("ClassData", back_populates="students")

    #Going
    studentsMarks = db.relationship("StudentsMarks", back_populates="students")  # StudentsDB.id ----> StudentsMarks.id``

    __table_args__ = (
        db.Index('idx_class_roll', 'CLASS', 'ROLL'),
    )
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    


class StudentsMarks(db.Model):
    __tablename__ = 'StudentsMarks'
    id = db.Column(db.Integer, primary_key=True)
    #student_id = db.Column(db.Integer)
    Subject = db.Column(db.Text)  # Might be 'subject' instead of 'Subject'
    FA1 = db.Column(db.Text)     # Might be 'fa1' instead of 'FA1'
    FA2 = db.Column(db.Text)
    SA1 = db.Column(db.Text)
    SA2 = db.Column(db.Text)

    school_id = db.Column(db.Text, db.ForeignKey('Schools.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('StudentsDB.id'))

    # Relationships
    school = db.relationship("Schools", back_populates="studentMarks")
    students = db.relationship("StudentsDB", back_populates="studentsMarks")


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
        return "A"
    elif number >= 60:
        return "B"
    elif number >= 45:
        return "C"
    elif number >= 33:
        return "D"
    else:
        return "E"



def ResultData(students_ids=None):
    if not students_ids:
        return []

    # Cast marks to Numeric in subject_query
    subject_query = db.session.query(
        StudentsMarks.student_id,
        cast(StudentsMarks.Subject, String).label('Subject'),
        # Use handleMarks on individual columns to sanitize values
        cast(handleMarks(StudentsMarks.FA1, 0), Numeric).label('FA1'),  # Handle empty strings
        cast(handleMarks(StudentsMarks.SA1, 0), Numeric).label('SA1'),
        cast(handleMarks(StudentsMarks.FA2, 0), Numeric).label('FA2'),
        cast(handleMarks(StudentsMarks.SA2, 0), Numeric).label('SA2'),
        (handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0)).label('FA1_SA1_Total'),
        (handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('FA2_SA2_Total'),
        (handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0) + 
         handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('Grand_Total'),
        # Cast ranks to Integer (instead of Numeric) to match summary_query's rank()
        cast(literal(None), Integer).label('SA1_Rank'),
        cast(literal(None), Integer).label('SA2_Rank'),
        cast(literal(None), Integer).label('Grand_Rank')
    ).join(StudentsDB, StudentsMarks.student_id == StudentsDB.id
    ).filter(StudentsMarks.student_id.in_(students_ids))

    # Summary query remains mostly the same
    summary_query = db.session.query(
        StudentsMarks.student_id,
        cast(literal('Total'), String).label('Subject'),
        func.sum(handleMarks(StudentsMarks.FA1, 0)).label('FA1'),
        func.sum(handleMarks(StudentsMarks.SA1, 0)).label('SA1'),
        func.sum(handleMarks(StudentsMarks.FA2, 0)).label('FA2'),
        func.sum(handleMarks(StudentsMarks.SA2, 0)).label('SA2'),
        func.sum(handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0)).label('FA1_SA1_Total'),
        func.sum(handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('FA2_SA2_Total'),
        func.sum(handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0) +
        handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)).label('Grand_Total'),
        # Use Integer for ranks to match subject_query's cast
        func.rank().over(
            partition_by=StudentsDB.CLASS,
            order_by=func.sum(handleMarks(StudentsMarks.SA1, 0)).desc()
        ).label('SA1_Rank'),
        func.rank().over(
            partition_by=StudentsDB.CLASS,
            order_by=func.sum(handleMarks(StudentsMarks.SA2, 0)).desc()
        ).label('SA2_Rank'),
        func.rank().over(
            partition_by=StudentsDB.CLASS,
            order_by=func.sum(
                handleMarks(StudentsMarks.FA1, 0) + handleMarks(StudentsMarks.SA1, 0) +
                handleMarks(StudentsMarks.FA2, 0) + handleMarks(StudentsMarks.SA2, 0)
            ).desc()
        ).label('Grand_Rank')
    ).join(StudentsDB, StudentsMarks.student_id == StudentsDB.id
    ).filter(StudentsMarks.student_id.in_(students_ids)
    ).group_by(StudentsMarks.student_id, StudentsDB.CLASS)

    combined_query = subject_query.union_all(summary_query)
    results = combined_query.all()

    sorted_results = sorted(results, key=itemgetter(0))  # Sorting by student_id

    grouped_data = defaultdict(dict)
    for student_id, data in groupby(sorted_results, key=itemgetter(0)):  # Group by student ID
        grouped_data[student_id] = {
            row[1]: {  # Subject name as key
                "FA1": row[2], "SA1": row[3], "FA2": row[4], "SA2": row[5],
                "FA1_SA1_Total": row[6], "FA2_SA2_Total": row[7], "Grand_Total": row[8],
                "SA1_Rank": row[9], "SA2_Rank": row[10], "Grand_Rank": row[11]
            }
            for row in data
        }

    return grouped_data


def GetStudentDataByID(ids, columns=None):
    if not ids:
        return {}  # Return empty dictionary for consistency
    
    query = db.session.query(StudentsDB)

    # if columns is not None, select only that specified columns
    if columns:

        #if id not in columns, add it to the list
        columns = ["id"] + [col for col in columns if col != "id"]

        #this will get the columns from the StudentsDB class based on the columns list we provided
        selected_columns = [getattr(StudentsDB, col) for col in columns if hasattr(StudentsDB, col)]
        query = query.with_entities(*selected_columns)
    else:

        # Fetch all columns if we don't specify any columns
        selected_columns = StudentsDB.__table__.columns.keys()  
    
    students = query.filter(StudentsDB.id.in_(ids)).all()

    if students:
        student_dict = {s.id: dict(s._asdict()) for s in students}
        return student_dict


    return {}

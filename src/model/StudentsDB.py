from sqlalchemy import (
    Column, Integer, BigInteger, Text, Date, Numeric, JSON,
    ForeignKey, TypeDecorator)

from src import db
from .enums import StudentsDBEnums

import os
from cryptography.fernet import Fernet



FERNET_KEY = os.environ.get('FERNET_KEY')

if not FERNET_KEY:
    raise ValueError("FERNET_KEY not found in environment variables")

fernet = Fernet(FERNET_KEY)

def create_encrypted_text_type(fernet_instance):
    class EncryptedText(TypeDecorator):
        impl = Text  # Underlying database type is Text

        def process_bind_param(self, value, dialect):
            """Encrypt the value before saving to the database."""
            if value is not None:
                encrypted = fernet_instance.encrypt(value.encode())
                return encrypted.decode('utf-8')
            return value

        def process_result_value(self, value, dialect):
            """Decrypt the value after loading from the database."""
            if value is not None:
                decrypted = fernet_instance.decrypt(value.encode('utf-8'))
                return decrypted.decode('utf-8')
            return value

    return EncryptedText

# Create the EncryptedText type with the Fernet instance
EncryptedText = create_encrypted_text_type(fernet)



class StudentsDB(db.Model):
    __tablename__ = 'StudentsDB'
    
    id = Column(BigInteger, unique=True, primary_key=True)
    STUDENTS_NAME = Column(Text, nullable=False)
    DOB = Column(Date, nullable=True)
    class_data_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=False)


    FATHERS_NAME = Column(Text, nullable=True)
    MOTHERS_NAME = Column(Text, nullable=True)

    FATHERS_AADHAR = db.Column(EncryptedText, nullable=True)
    MOTHERS_AADHAR = db.Column(EncryptedText, nullable=True)
    AADHAAR = db.Column(EncryptedText, unique=True, nullable=True)


    PHONE = Column(Text, nullable=True)
    ALT_MOBILE = Column(Text, nullable=True)
    ADMISSION_NO = Column(BigInteger, unique=True, nullable=True)
    PEN = Column(Text, unique=True, nullable=True)

    ADMISSION_SESSION = Column(Text, nullable=True)
    ADDRESS = Column(Text, nullable=True)
    HEIGHT = Column(Integer, nullable=True)
    WEIGHT = Column(Integer, nullable=True)
    Caste = Column(Text, nullable=True)

    PIN = Column(Text, nullable=True)
    ADMISSION_DATE = Column(Date, nullable=True)
    SR = Column(Integer, nullable=True, unique=True)
    IMAGE = Column(Text, unique=True, nullable=True)
    Previous_School_Marks = Column(Integer, nullable=True)  # smallint in DB; using Integer here
    Previous_School_Attendance = Column(BigInteger, nullable=True)


    Free_Scheme = Column(JSON, nullable=True)
    Attendance = Column(Text, nullable=True)

    Previous_School_Name = Column(Text, nullable=True)
    APAAR = Column(Text, unique=True, nullable=True)
    EMAIL = Column(Text, nullable=True)

    Admission_Class = Column(Numeric, nullable=True)

    GENDER = Column(StudentsDBEnums.GENDER, nullable=False)
    Caste_Type = Column(StudentsDBEnums.CASTE_TYPE, nullable=True)
    RELIGION = Column(StudentsDBEnums.RELIGION, nullable=True)
    Home_Distance = Column(StudentsDBEnums.HOME_DISTANCE, nullable=True)
    BLOOD_GROUP = Column(StudentsDBEnums.BLOOD_GROUP, nullable=True)
    FATHERS_EDUCATION = Column(StudentsDBEnums.EDUCATION_TYPE, nullable=True)
    MOTHERS_EDUCATION = Column(StudentsDBEnums.EDUCATION_TYPE, nullable=True)
    FATHERS_OCCUPATION = Column(StudentsDBEnums.FATHERS_OCCUPATION, nullable=True)
    MOTHERS_OCCUPATION = Column(StudentsDBEnums.MOTHERS_OCCUPATION, nullable=True)

    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=True)
    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=False)
    
    school = db.relationship("Schools", back_populates="students")
    class_data = db.relationship("ClassData", back_populates="students")
    session = db.relationship("Sessions", back_populates="students")
    
    student_sessions = db.relationship("StudentSessions", back_populates="students")
    students_marks = db.relationship("StudentsMarks", back_populates="students")

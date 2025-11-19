from sqlalchemy import (
    Column, BigInteger, SmallInteger, Text, JSON, ForeignKey
)
from src import db

class ClassData(db.Model):
    __tablename__ = 'ClassData'
    
    id = Column(BigInteger, primary_key=True)
    CLASS = Column(Text, nullable=False)
    Numeric_Subjects = Column(JSON, nullable=False)
    exam_format = Column(JSON, nullable=False)
    Grading_Subjects = Column(JSON, nullable=True)
    Section = Column(Text, nullable=True)   # Added Section column as per DB
    display_order = Column(SmallInteger, nullable=True)

    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    school = db.relationship("Schools", back_populates="class_data")

    class_teacher_id = Column(BigInteger, ForeignKey('TeachersLogin.id', onupdate="CASCADE"), nullable=False)
    class_teacher_data = db.relationship("TeachersLogin", back_populates="class_data")
    
    # Relationships
    subjects = db.relationship("Subjects", back_populates="class_data")
    student_sessions =  db.relationship("StudentSessions", back_populates="class_data")
    class_access = db.relationship("ClassAccess", back_populates="class_data")
    class_exams = db.relationship("ClassExams", back_populates="class_data")
    fee_sessions = db.relationship("FeeSessionData", back_populates="class_data")

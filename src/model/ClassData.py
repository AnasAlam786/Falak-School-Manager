from sqlalchemy import (
    Column, Integer, BigInteger, Text, JSON, ForeignKey
)
from src import db

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

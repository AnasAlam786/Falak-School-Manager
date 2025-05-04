from sqlalchemy import (
    Column, Text, Date, JSON,
)
from src import db

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
    students_image_folder_id = Column(Text, nullable=True)  # Added students_image_folder_id as per DB
    session_id = Column(Text, nullable=False)
    
    # Relationships
    students = db.relationship("StudentsDB", back_populates="school")
    class_data = db.relationship("ClassData", back_populates="school")
    students_marks = db.relationship("StudentsMarks", back_populates="school")
    fees_data = db.relationship("FeesData", back_populates="school")
    teachers = db.relationship("TeachersLogin", back_populates="school")
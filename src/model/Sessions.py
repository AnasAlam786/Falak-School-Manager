from sqlalchemy import (
    Column, BigInteger, Text, Date, Boolean
)
from src import db

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
    fee_data = db.relationship("FeeData", back_populates="session")
    fee_amount = db.relationship("FeeAmount", back_populates="session")
    student_sessions = db.relationship("StudentSessions", back_populates="session")
    students_marks = db.relationship("StudentsMarks", back_populates="session")

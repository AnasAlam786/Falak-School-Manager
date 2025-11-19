from sqlalchemy import (
    Column, Integer, BigInteger, Text, DateTime, Numeric,
    ForeignKey, UniqueConstraint
)
from src import db

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
    created_at = Column(DateTime)
    Due_Amount = Column(Numeric, nullable=True)
    Section = Column(Text, nullable=True)


    class_data = db.relationship("ClassData", back_populates="student_sessions")
    students = db.relationship("StudentsDB", back_populates="student_sessions")
    session = db.relationship("Sessions", back_populates="student_sessions")
    fee_data = db.relationship("FeeData", back_populates="student_sessions")

    __table_args__ = (
        UniqueConstraint('class_id', 'ROLL', 'session_id' ,'Section', name='uix_school_SR'),
    )

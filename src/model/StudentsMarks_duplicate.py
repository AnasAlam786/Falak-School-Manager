from datetime import datetime
from sqlalchemy import (
    Column, Text, ForeignKey,BigInteger, Date
)
from src import db

class StudentsMarks_duplicate(db.Model):
    __tablename__ = 'StudentsMarks_duplicate'

    id = db.Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(BigInteger, db.ForeignKey('StudentsDB.id', onupdate='CASCADE'), nullable=False)
    subject_id = Column(BigInteger, db.ForeignKey('Subjects.id', onupdate='CASCADE'), nullable=False)
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=True)
    session_id = Column(BigInteger, db.ForeignKey('Sessions.id', onupdate='CASCADE'), nullable=False)
    exam_id = Column(BigInteger, db.ForeignKey('Exams.id', onupdate='CASCADE'), nullable=False)
    score = Column(Text, nullable=True)
    created_at = Column(Date, default=datetime.utcnow)

    # Optional: relationships for easier access (recommended)
    students = db.relationship('StudentsDB', back_populates='marks')
    subjects = db.relationship('Subjects', back_populates='marks')
    school = db.relationship('Schools', back_populates='marks')
    session = db.relationship('Sessions', back_populates='marks')
    exams = db.relationship('Exams', back_populates='marks')

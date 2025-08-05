from src import db
from sqlalchemy import (
    Column, Text, ForeignKey,BigInteger, Numeric, Integer, Boolean, TIMESTAMP
)
from datetime import datetime


class Subjects(db.Model):
    __tablename__ = 'Subjects'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    school_id = Column(Text, ForeignKey('Schools.id', onupdate='CASCADE'), nullable=False)
    class_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate='CASCADE'), nullable=False)
    subject_code = Column(Text, nullable=True)
    subject = Column(Text, nullable=False)
    max_marks = Column(Numeric, nullable=True)
    pass_marks = Column(Numeric, nullable=True)
    display_order = Column(Numeric, nullable=True)
    evaluation_type = Column(Text, nullable=False)
    abbreviation = Column(Text, nullable=False)
    staff_id = Column(Integer, ForeignKey('TeachersLogin.id', onupdate='CASCADE'), nullable=True)
    subject_type = Column(Text, nullable=False, default='core')
    is_active = Column(Boolean, nullable=False, default=True)

    # Optional relationships
    school = db.relationship('Schools', back_populates='subjects')
    class_data = db.relationship('ClassData', back_populates='subjects')
    staff_data = db.relationship('TeachersLogin', back_populates='subjects')

    marks = db.relationship("StudentsMarks_duplicate", back_populates="subjects")

from sqlalchemy import (
    Column, BigInteger, Text, ForeignKey
)
from src import db

# class StudentsMarks(db.Model):
#     __tablename__ = 'StudentsMarks'
    
    # id = Column(BigInteger, primary_key=True)
    
    # Subject = Column(Text, nullable=False)
    
    # FA1 = Column(Text, nullable=True)
    # FA2 = Column(Text, nullable=True)
    # SA1 = Column(Text, nullable=True)
    # SA2 = Column(Text, nullable=True)
    

    # school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    # school = db.relationship("Schools", back_populates="students_marks")

    # student_id = Column(BigInteger, ForeignKey('StudentsDB.id', onupdate="CASCADE"), nullable=False)
    # students = db.relationship("StudentsDB", back_populates="students_marks")

    # session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=False)
    # session = db.relationship("Sessions", back_populates="students_marks")

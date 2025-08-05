from sqlalchemy import (
    Column, BigInteger, Text, Date, Numeric, ForeignKey
)
from src import db

class FeeData(db.Model):
    __tablename__ = 'FeeData'
    
    id = Column(BigInteger, primary_key=True)
    paid_at = Column(Date, nullable=False)
    paid_amount = Column(Numeric, nullable=False)

    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=True)
    school = db.relationship("Schools", back_populates="fee_data")
    
    student_id = Column(BigInteger, ForeignKey('StudentsDB.id', onupdate="CASCADE"), nullable=False)
    students = db.relationship("StudentsDB", back_populates="fee_data")
    
    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=False)
    session = db.relationship("Sessions", back_populates="fee_data")


    structure_id = Column(BigInteger, ForeignKey('FeeStructure.id', onupdate="CASCADE"), nullable=False)
    fee_structure = db.relationship("FeeStructure", back_populates="fee_data")

    amount_id = Column(BigInteger, ForeignKey('FeeAmount.id', onupdate="CASCADE"), nullable=False)
    fee_amount = db.relationship("FeeAmount", back_populates="fee_data")
    

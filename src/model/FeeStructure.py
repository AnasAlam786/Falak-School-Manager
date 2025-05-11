from sqlalchemy import (
    Column, BigInteger, Text, Date, ForeignKey
)
from src import db

class FeeStructure(db.Model):
    __tablename__ = 'FeeStructure'
    
    id = Column(BigInteger, primary_key=True)
    sequence_number = Column(BigInteger, nullable=False)
    period_name = Column(Text, nullable=False)
    created_at = Column(Date, nullable=False)

    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=True)
    school = db.relationship("Schools", back_populates="fee_structure")

    fee_data = db.relationship("FeeData", back_populates="fee_structure")
    



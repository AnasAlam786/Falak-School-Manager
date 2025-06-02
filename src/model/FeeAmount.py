from sqlalchemy import (
    Column, BigInteger, Text, ForeignKey, Numeric
)
from src import db

class FeeAmount(db.Model):
    __tablename__ = 'FeeAmount'
    
    id = Column(BigInteger, primary_key=True)
    amount = Column(Numeric, nullable=False)

    class_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=False)
    class_data = db.relationship("ClassData", back_populates="fee_amount")

    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=False)
    session = db.relationship("Sessions", back_populates="fee_amount")

    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    school = db.relationship("Schools", back_populates="fee_amount")

    fee_data = db.relationship("FeeData", back_populates="fee_amount")
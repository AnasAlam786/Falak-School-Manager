from sqlalchemy import (
    Column, BigInteger, Text, Date, Numeric, ForeignKey
)
from src import db

class FeesData(db.Model):
    __tablename__ = 'FeesData'
    
    id = Column(BigInteger, primary_key=True)
    created_at = Column(Date, nullable=False)
    Fee = Column(Numeric, nullable=False)  # Using Numeric to match DB type
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=True)
    class_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=True)
    session_id = Column(BigInteger, ForeignKey('Sessions.id', onupdate="CASCADE"), nullable=True)
    
    school = db.relationship("Schools", back_populates="fees_data")
    class_data = db.relationship("ClassData", back_populates="fees_data")
    session = db.relationship("Sessions", back_populates="fees_data")

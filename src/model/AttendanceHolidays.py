from sqlalchemy import Column, BigInteger, Date, ForeignKey, Text, TIMESTAMP
from src import db

class AttendanceHolidays(db.Model):
    __tablename__ = 'AttendanceHolidays'

    id = Column(BigInteger, primary_key=True)
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    name = Column(Text, nullable=False)
    class_id = Column(BigInteger, ForeignKey('ClassData.id'), nullable=True)
    created_at = Column(TIMESTAMP, nullable=True)

    school = db.relationship("Schools", back_populates="holidays")
    class_data = db.relationship("ClassData", back_populates="holidays")
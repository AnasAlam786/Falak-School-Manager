from sqlalchemy import (
    Column, Integer, BigInteger, Text, JSON, ForeignKey
)
from src import db

class TeachersLogin(db.Model):
    __tablename__ = 'TeachersLogin'
    
    id = Column(Integer, primary_key=True)  # 'serial' is represented as Integer with auto-increment
    Name = Column(Text, nullable=False)
    Email = Column(Text, nullable=False, unique=True)
    Password = Column(Text, nullable=False)
    Classes = Column(Text, nullable=False)  # In DB, this column is text (not JSON)
    Role = Column(Text, nullable=False)
    IP = Column(JSON, nullable=True)
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    Sign = Column(Text, nullable=True)
    User = Column(Text, nullable=False)    # Added missing "User" column as per DB
    class_id = Column(BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=True)
    
    school = db.relationship("Schools", back_populates="teachers")
    class_data = db.relationship("ClassData", back_populates="teachers")

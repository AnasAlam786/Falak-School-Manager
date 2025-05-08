from sqlalchemy import (
    Column, Integer, Text, JSON, ForeignKey, NUMERIC
)
from src import db

class TeachersLogin(db.Model):
    __tablename__ = 'TeachersLogin'
    
    id = Column(Integer, primary_key=True)  # 'serial' is represented as Integer with auto-increment
    Name = Column(Text, nullable=False)
    Email = Column(Text, nullable=False, unique=True)
    Password = Column(Text, nullable=False)
    Role = Column(Text, nullable=False)
    IP = Column(JSON, nullable=True)
    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    Sign = Column(Text, nullable=True)
    User = Column(Text, nullable=False)
    status = Column(Text, nullable=False)

    class_data = db.relationship("ClassData", back_populates="class_teacher_data")
    
    school = db.relationship("Schools", back_populates="staff_data")
    class_access = db.relationship("ClassAccess", back_populates="staff_data")

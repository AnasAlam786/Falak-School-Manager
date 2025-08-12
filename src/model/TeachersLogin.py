from sqlalchemy import (
    Column, Text, JSON, ForeignKey, BigInteger
)
from src import db

class TeachersLogin(db.Model):
    __tablename__ = 'TeachersLogin'
    
    id = Column(BigInteger, primary_key=True)  # 'serial' is represented as Integer with auto-increment
    Name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    Password = Column(Text, nullable=False)
    IP = Column(JSON, nullable=True)
    
    Sign = Column(Text, nullable=True)
    User = Column(Text, nullable=False)
    status = Column(Text, nullable=False)

    # New optional assets
    # profile_image_url = Column(Text, nullable=True)
    # signature_url = Column(Text, nullable=True)

    school_id = Column(Text, ForeignKey('Schools.id', onupdate="CASCADE"), nullable=False)
    school = db.relationship("Schools", back_populates="staff_data")

    role_id = Column(BigInteger, ForeignKey('Roles.id', onupdate="CASCADE"), nullable=False)
    role_data = db.relationship("Roles", back_populates="staff_data")

    class_data = db.relationship("ClassData", back_populates="class_teacher_data")
    class_access = db.relationship("ClassAccess", back_populates="staff_data")
    subjects = db.relationship("Subjects", back_populates="staff_data")
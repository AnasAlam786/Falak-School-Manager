from sqlalchemy import (
    Column, BigInteger, Text, Date, ForeignKey
)
from src import db

class ClassAccess(db.Model):
    __tablename__ = 'ClassAccess'
    id = Column(BigInteger, primary_key=True)
    granted_at = Column(Date, nullable=True)
    access_role = Column(Text, nullable=True)

    class_id = Column(Text, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=False)
    class_data = db.relationship("ClassData", back_populates="class_access")

    staff_id = Column(Text, ForeignKey('TeachersLogin.id', onupdate="CASCADE"), nullable=False)
    staff_data = db.relationship("TeachersLogin", back_populates="class_access")


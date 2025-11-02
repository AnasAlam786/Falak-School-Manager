from sqlalchemy import (
    Column, BigInteger, Text, Date, ForeignKey
)
from src import db

class ClassAccess(db.Model):
    __tablename__ = 'ClassAccess'
    id = Column(BigInteger, primary_key=True, autoincrement=True)  # ✅ add autoincrement
    granted_at = Column(Date, nullable=True)

    class_id = Column(db.BigInteger, ForeignKey('ClassData.id', onupdate="CASCADE"), nullable=False)
    class_data = db.relationship("ClassData", back_populates="class_access")

    staff_id = Column(db.BigInteger, ForeignKey('TeachersLogin.id', onupdate="CASCADE"), nullable=False)
    staff_data = db.relationship("TeachersLogin", back_populates="class_access")


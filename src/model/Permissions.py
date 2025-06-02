from sqlalchemy import (
    Column, BigInteger, Text, Date
)
from src import db

class Permissions(db.Model):
    __tablename__ = 'Permissions'
    id = Column(BigInteger, primary_key=True)
    permission_name = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(Date, nullable=True)

    role_permissions = db.relationship("RolePermissions", back_populates="permission_data")
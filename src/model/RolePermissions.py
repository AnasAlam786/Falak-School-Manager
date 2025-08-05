from sqlalchemy import (
    Column, BigInteger, ForeignKey, Date
)
from src import db

class RolePermissions(db.Model):
    __tablename__ = 'RolePermissions'
    id = Column(BigInteger, primary_key=True)
    granted_at = Column(Date, nullable=False)
    
    
    role_id = Column(BigInteger, ForeignKey('Roles.id', onupdate="CASCADE"), nullable=False)
    role_data = db.relationship("Roles", back_populates="role_permissions")

    permission_id = Column(BigInteger, ForeignKey('Permissions.id', onupdate="CASCADE"), nullable=False)
    permission_data = db.relationship("Permissions", back_populates="role_permissions")

    
from datetime import datetime, timezone
from sqlalchemy import Column, BigInteger, ForeignKey, Boolean, DateTime
from src import db

class StaffPermissions(db.Model):
    __tablename__ = 'StaffPermissions'
    
    id = Column(BigInteger, primary_key=True)
    staff_id = Column(BigInteger, ForeignKey('TeachersLogin.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    permission_id = Column(BigInteger, ForeignKey('Permissions.id', onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    is_granted = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    staff = db.relationship("TeachersLogin", backref=db.backref("permissions", lazy="dynamic"))
    permission = db.relationship("Permissions", backref=db.backref("staff_permissions", lazy="dynamic"))

    def __repr__(self):
        return f"<StaffPermission staff_id={self.staff_id} permission_id={self.permission_id} granted={self.is_granted}>"

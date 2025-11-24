from sqlalchemy import (
    Column, BigInteger, Date, Enum, ForeignKey, Text, UniqueConstraint
)
from src import db

class Attendance(db.Model):
    __tablename__ = 'Attendance'

    id = Column(BigInteger, primary_key=True)
    student_session_id = Column(BigInteger,ForeignKey('StudentSessions.id', onupdate="CASCADE"),nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum("PRESENT", "ABSENT", "HALF_DAY", "LEAVE", "HOLIDAY", name="Attendance_Status"), nullable=False)
    marked_by = Column(BigInteger, ForeignKey('TeachersLogin.id', onupdate="CASCADE"), nullable=True)
    remark = Column(Text, nullable=True)

    student_sessions = db.relationship("StudentSessions", back_populates="attendance")
    staff_data = db.relationship("TeachersLogin", back_populates="attendance")

    __table_args__ = (
        UniqueConstraint('student_session_id', 'date', name='uix_attendance_unique'),
    )
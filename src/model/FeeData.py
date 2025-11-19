from sqlalchemy import TIMESTAMP, Column, BigInteger, String, ForeignKey, text
from src import db

class FeeData(db.Model):
    __tablename__ = "FeeData"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    payment_status = Column(String, nullable=True)

    transaction_id = Column(BigInteger, ForeignKey("FeeTransaction.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True)
    fee_transactions = db.relationship("FeeTransaction", back_populates="fee_data")

    student_session_id = Column(BigInteger, ForeignKey("StudentSessions.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True)
    student_sessions = db.relationship("StudentSessions", back_populates="fee_data")

    fee_session_id = Column(BigInteger, ForeignKey("FeeSessionData.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True)
    fee_sessions = db.relationship("FeeSessionData", back_populates="fee_data")
    

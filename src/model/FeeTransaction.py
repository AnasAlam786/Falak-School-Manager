from sqlalchemy import Column, BigInteger, Integer, String, Text, Numeric, Date, TIMESTAMP, ForeignKey
from sqlalchemy.sql import text
from src import db

class FeeTransaction(db.Model):
    __tablename__ = "FeeTransaction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_no = Column(String, nullable=True)
    paid_amount = Column(Numeric, nullable=True)
    payment_date = Column(Date, nullable=True)
    payment_mode = Column(String, nullable=True)
    discount = Column(Numeric, nullable=True)
    seq_no = Column(Numeric, nullable=False)
    remark = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=True, server_default=text("now()"))

    # Optional relationships
    school_id = Column(String, ForeignKey("Schools.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True)
    school = db.relationship("Schools", back_populates="fee_transactions")

    session_id = Column(BigInteger, ForeignKey("Sessions.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True)
    session = db.relationship("Sessions", back_populates="fee_transactions")

    fee_data = db.relationship("FeeData", back_populates="fee_transactions", uselist=True)
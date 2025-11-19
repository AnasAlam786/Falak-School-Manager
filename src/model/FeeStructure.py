from sqlalchemy import Column, BigInteger, Integer, SmallInteger, Text, ForeignKey
from src import db

class FeeStructure(db.Model):
    __tablename__ = "FeeStructure"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sequence_number = Column(Integer, nullable=False)
    period_name = Column(Text, nullable=False)
    fee_type = Column(Text, nullable=True)
    start_day = Column(SmallInteger, nullable=True)
    start_month = Column(SmallInteger, nullable=True)
    due_day = Column(SmallInteger, nullable=True)
    due_month = Column(SmallInteger, nullable=True)
    year_increment = Column(SmallInteger, nullable=True)

    # Optional relationships
    fee_type_id = Column(BigInteger, ForeignKey("FeeHeads.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True)
    fee_head = db.relationship("FeeHeads", back_populates="fee_structure")

    school_id = Column(Text, ForeignKey("Schools.id", onupdate="CASCADE"), nullable=False)
    school = db.relationship("Schools", back_populates="fee_structure")

    fee_sessions = db.relationship("FeeSessionData", back_populates="fee_structure")
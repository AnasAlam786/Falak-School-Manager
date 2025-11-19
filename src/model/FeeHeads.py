from sqlalchemy import Column, BigInteger, Text
from src import db

class FeeHeads(db.Model):
    __tablename__ = "FeeHeads"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fee_type = Column(Text, nullable=True)

    fee_structure = db.relationship("FeeStructure", back_populates="fee_head", uselist=True)
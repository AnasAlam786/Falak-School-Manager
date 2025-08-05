from sqlalchemy import func, and_, or_
from src.model import (StudentsDB, StudentSessions, ClassData, 
                       FeeStructure, FeeAmount, FeeData)

class FeeQueryBuilder:
    def __init__(self, session):
        self.session = session
        self.query = session.query(FeeData)  # Start with FeeData as the base
    
    def reset(self):
        self.query = self.session.query(FeeData)
        return self

    # --------------------------------------------------
    # Core Joins
    # --------------------------------------------------
    def join_student(self):
        self.query = self.query.join(StudentsDB, FeeData.student_id == StudentsDB.id)
        return self

    def join_fee_amount(self):
        self.query = self.query.join(FeeAmount, FeeData.amount_id == FeeAmount.id)
        return self

    def join_class(self):
        self.query = self.query.join(FeeAmount.class_data)  # Via FeeAmount → ClassData
        return self

    def join_session(self):
        self.query = self.query.join(Sessions, FeeData.session_id == Sessions.id)
        return self

    def join_fee_structure(self):
        self.query = self.query.join(FeeStructure, FeeData.structure_id == FeeStructure.id)
        return self

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------
    def filter_by_student(self, student_id):
        self.query = self.query.filter(FeeData.student_id == student_id)
        return self

    def filter_by_class(self, class_id):
        self.query = self.query.filter(FeeAmount.class_id == class_id)
        return self

    def filter_by_session(self, session_id):
        self.query = self.query.filter(FeeData.session_id == session_id)
        return self

    def filter_by_school(self, school_id):
        self.query = self.query.filter(FeeData.school_id == school_id)
        return self

    def filter_by_amount_range(self, min_amount=None, max_amount=None):
        if min_amount:
            self.query = self.query.filter(FeeData.amount >= min_amount)
        if max_amount:
            self.query = self.query.filter(FeeData.amount <= max_amount)
        return self

    def filter_by_payment_date(self, start_date=None, end_date=None):
        if start_date:
            self.query = self.query.filter(FeeData.paid_at >= start_date)
        if end_date:
            self.query = self.query.filter(FeeData.paid_at <= end_date)
        return self

    # --------------------------------------------------
    # Aggregates & Calculations
    # --------------------------------------------------
    def with_total_paid(self):
        total_paid = func.sum(FeeData.amount).label('total_paid')
        self.query = self.query.add_columns(total_paid)
        return self

    def with_total_due(self):
        # Assuming FeeAmount.amount is the total fee, and FeeData.amount is paid
        total_due = (func.sum(FeeAmount.amount) - func.sum(FeeData.amount)).label('total_due')
        self.query = (
            self.query.join(FeeAmount, FeeData.amount_id == FeeAmount.id)
            .add_columns(total_due)
        )
        return self

    # --------------------------------------------------
    # Specialized Queries
    # --------------------------------------------------
    def get_student_fee_history(self, student_id):
        return (
            self.reset()
                .join_fee_amount()
                .join_fee_structure()
                .filter_by_student(student_id)
                .query.all()
        )

    def get_class_fee_summary(self, class_id):
        return (
            self.reset()
                .join_fee_amount()
                .filter_by_class(class_id)
                .with_total_paid()
                .query.group_by(FeeData.student_id)
                .all()
        )

    # --------------------------------------------------
    # Executors
    # --------------------------------------------------
    def execute(self):
        return self.query.all()

    def first(self):
        return self.query.first()

    def count(self):
        return self.query.count()
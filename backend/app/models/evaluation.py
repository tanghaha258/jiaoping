"""Evaluation model."""

from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship

from app.db.base import Base, CommonMixin


class Evaluation(Base, CommonMixin):
    __tablename__ = "evaluations"

    submission_id = Column(CHAR(36), ForeignKey("submissions.id"), nullable=False, index=True)
    evaluator_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    evaluator_type = Column(String(20), nullable=False, default="teacher")
    rubric_id = Column(CHAR(36), ForeignKey("rubrics.id"), nullable=False)
    scores = Column(JSON, nullable=True, default=dict)
    comments = Column(String(5000), nullable=True)
    status = Column(String(20), nullable=False, default="draft")
    confirmed_by = Column(CHAR(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="evaluations")
    evaluator = relationship("User", backref="evaluations", foreign_keys=[evaluator_id])
    rubric = relationship("Rubric", backref="evaluations")
    confirmer = relationship("User", backref="confirmed_evaluations", foreign_keys=[confirmed_by])

    def __repr__(self):
        return f"<Evaluation(submission_id={self.submission_id}, type={self.evaluator_type})>"

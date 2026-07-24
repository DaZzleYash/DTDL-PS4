"""Loan application context — documentation model for demos and API docs.

This shape is not enforced by the generic engine; it documents the expected
request payload for Contributors C/E and anyone running the finance demo.
"""

from pydantic import BaseModel, Field


class ApplicantInfo(BaseModel):
    creditScore: int = Field(description="FICO-style credit score")
    annualIncome: float = Field(description="Gross annual income")
    employmentStatus: str = Field(description="e.g. EMPLOYED, SELF_EMPLOYED, UNEMPLOYED")
    dateOfBirth: str = Field(description="ISO-8601 date, e.g. 1990-05-15")
    existingCustomer: bool = Field(description="True if the applicant already banks with us")


class LoanInfo(BaseModel):
    amount: float
    purpose: str = Field(description="e.g. HOME, AUTO, PERSONAL, EDUCATION")
    termMonths: int


class RiskFlags(BaseModel):
    hasDefaulted: bool
    debtToIncomeRatio: float = Field(description="Total debt payments / gross income")


class LoanApplicationContext(BaseModel):
    """Documentation-only model of a loan application evaluation context."""

    applicant: ApplicantInfo
    loan: LoanInfo
    risk_flags: RiskFlags

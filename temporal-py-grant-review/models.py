"""Plain dataclasses passed between the client, the workflow and the activities."""
from dataclasses import dataclass, field

TASK_QUEUE = "grant-review"


@dataclass
class Application:
    application_id: str
    applicant: str
    contact_email: str
    proposal: str


@dataclass
class Screening:
    category: str  # garden | youth | arts | mobility | other
    requested_amount: int
    fit_score: int  # 1 (poor) .. 5 (excellent)
    summary: str


@dataclass
class BudgetCheck:
    category: str
    requested_amount: int
    remaining_before: int
    affordable: bool


@dataclass
class ReviewResult:
    application_id: str
    screening: Screening
    budget: BudgetCheck
    decision: str  # approved | declined
    letter: str
    notes: list[str] = field(default_factory=list)

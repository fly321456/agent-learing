from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class TaskAudit:
    independent_subtasks: bool
    distinct_expertise: bool
    parallelizable: bool
    low_shared_state: bool
    evaluation_available: bool


@dataclass(frozen=True)
class ArchitectureDecision:
    use_multi_agent: bool
    reasons: tuple[str, ...]


def audit_task(audit: TaskAudit) -> ArchitectureDecision:
    benefits = sum([
        audit.independent_subtasks,
        audit.distinct_expertise,
        audit.parallelizable,
        audit.low_shared_state,
    ])
    reasons: list[str] = []
    if not audit.evaluation_available:
        reasons.append("No evaluation exists to prove a multi-agent gain.")
    if not audit.independent_subtasks:
        reasons.append("Subtasks are tightly coupled.")
    if not audit.low_shared_state:
        reasons.append("Shared-state coordination cost is high.")
    use_multi = audit.evaluation_available and benefits >= 3
    if use_multi:
        reasons.append("The task has measurable, separable work.")
    return ArchitectureDecision(use_multi, tuple(reasons))


@dataclass(frozen=True)
class PlanItem:
    id: str
    objective: str


@dataclass(frozen=True)
class WorkResult:
    item_id: str
    status: str
    output: str = ""
    error: str | None = None


@dataclass
class ExecutionState:
    plan: list[PlanItem]
    results: list[WorkResult] = field(default_factory=list)


def create_plan(objectives: list[str]) -> list[PlanItem]:
    return [PlanItem(f"task-{index:02d}", objective) for index, objective in enumerate(objectives, 1)]


def execute_plan(
    plan: list[PlanItem], executor: Callable[[PlanItem], str]
) -> ExecutionState:
    state = ExecutionState(plan)
    for item in plan:
        try:
            state.results.append(WorkResult(item.id, "success", executor(item)))
        except Exception as exc:
            state.results.append(WorkResult(item.id, "error", error=str(exc)))
    return state


@dataclass(frozen=True)
class Message:
    sender: str
    receiver: str
    content: str


@dataclass
class SharedState:
    messages: list[Message] = field(default_factory=list)

    def record(self, sender: str, receiver: str, content: str) -> None:
        self.messages.append(Message(sender, receiver, content))

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def communication_chars(self) -> int:
        return sum(len(message.content) for message in self.messages)


@dataclass(frozen=True)
class ReviewCase:
    id: str
    candidate: str
    required_fragments: tuple[str, ...]


@dataclass(frozen=True)
class Review:
    approved: bool
    issues: tuple[str, ...]


def review_candidate(case: ReviewCase) -> Review:
    issues = tuple(
        f"Missing required fragment: {fragment}"
        for fragment in case.required_fragments
        if fragment not in case.candidate
    )
    return Review(not issues, issues)


@dataclass(frozen=True)
class Comparison:
    single_false_accepts: int
    reviewer_false_accepts: int
    communication_chars: int


def compare_single_and_reviewer(cases: list[ReviewCase]) -> Comparison:
    # Scripted single-agent baseline self-approves every candidate.
    single_false_accepts = sum(not review_candidate(case).approved for case in cases)
    shared = SharedState()
    reviewer_false_accepts = 0
    for case in cases:
        shared.record("executor", "reviewer", case.candidate)
        review = review_candidate(case)
        shared.record("reviewer", "executor", "approved" if review.approved else "; ".join(review.issues))
        if review.approved and any(fragment not in case.candidate for fragment in case.required_fragments):
            reviewer_false_accepts += 1
    return Comparison(single_false_accepts, reviewer_false_accepts, shared.communication_chars)


def decide_from_comparison(comparison: Comparison) -> ArchitectureDecision:
    gain = comparison.single_false_accepts - comparison.reviewer_false_accepts
    if gain <= 0:
        return ArchitectureDecision(False, ("Reviewer produced no measured quality gain.",))
    return ArchitectureDecision(
        True,
        (f"Reviewer prevented {gain} false acceptance(s).", f"Communication cost: {comparison.communication_chars} chars."),
    )

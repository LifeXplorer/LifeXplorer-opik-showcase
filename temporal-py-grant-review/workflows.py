"""The durable review workflow."""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import check_budget, decide, draft_letter, screen_application
    from models import Application, ReviewResult

RETRY = RetryPolicy(initial_interval=timedelta(seconds=1), backoff_coefficient=1.5, maximum_attempts=5)


@workflow.defn
class GrantReview:
    @workflow.run
    async def run(self, application: Application) -> ReviewResult:
        opts = {"start_to_close_timeout": timedelta(minutes=1), "retry_policy": RETRY}
        screening = await workflow.execute_activity(screen_application, application, **opts)
        budget = await workflow.execute_activity(check_budget, screening, **opts)  # fails once, retried
        await workflow.sleep(timedelta(seconds=2))  # durable timer: stands in for a committee cooling-off period
        decision = decide(screening, budget)
        letter = await workflow.execute_activity(draft_letter, args=[application, screening, budget, decision], **opts)
        return ReviewResult(application.application_id, screening, budget, decision, letter)

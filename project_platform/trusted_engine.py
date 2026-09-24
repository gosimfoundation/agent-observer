"""Bridge from the unchanged trusted Python simulator to the public session API.

This module runs only in the trusted job. It must never be imported by the
participant project or used on the executor host with a hidden scenario mounted.
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from challenge.challenge_workflow import ChallengeWorkflow
from .session import SessionClient, wait_until


def result_summary(result: dict) -> dict:
    """Small database summary; full action/replay evidence stays in private storage."""
    report=result["score_report"]
    completion=report.get("completion",{})
    return {
        "schema_version":"observer-run-summary-v1",
        "score":report["score"],
        "completed_tiles":len(completion.get("completed_tiles",[])),
        "required_missing":len(completion.get("required_missing",[])),
        "termination_reason":result["termination_reason"],
        "committed_action_count":result["committed_action_count"],
        "accounted_wallclock_seconds":result["accounted_wallclock_seconds"],
    }


class RemoteProvider:
    def __init__(self, workflow: ChallengeWorkflow, client: SessionClient, *, startup_seconds: float = 900):
        self.workflow, self.client = workflow, client
        self.startup_seconds = startup_seconds
        self.server_deadline: float | None = None
        self.flushed_sequence = 0
        self.flushed_rows = 0

    def publish_initial(self, publication):
        startup = time.monotonic()+self.startup_seconds
        self.client.call("initialize",publication=publication,deadline=startup)
        wait_until(lambda:self.client.call("poll",scope="engine",deadline=startup)["ready"],deadline=startup)
        deadline_at = self.client.call("begin",deadline=startup)
        server_time = datetime.fromisoformat(deadline_at.replace("Z","+00:00"))
        self.server_deadline=time.monotonic()+max(0,(server_time-datetime.now(timezone.utc)).total_seconds())

    def flush(self):
        # Called only after the simulator has validated and actually committed
        # the preceding response. Includes report rows emitted by that action.
        for entry in self.workflow.commit_log:
            if not entry["committed"] or entry["sequence"]<=self.flushed_sequence:
                continue
            rows=[item.csv_row() for item in self.workflow.committed[self.flushed_rows:]]
            self.client.call("commit",sequence=entry["sequence"],committed={"rows":rows})
            self.flushed_rows=len(self.workflow.committed)
            self.flushed_sequence=entry["sequence"]

    def __call__(self,snapshot,deadline_monotonic):
        deadline=min(deadline_monotonic,self.server_deadline or deadline_monotonic)
        self.flush()
        sequence=snapshot["decision_sequence"]
        self.client.call("publish",sequence=sequence,observation=snapshot,deadline=deadline)
        return wait_until(lambda:self.client.call("poll",scope="engine",deadline=deadline)["response"],deadline=deadline)


def run_session(scenario: Path, output: Path, client: SessionClient, *, wallclock_seconds: float | None = None):
    workflow=ChallengeWorkflow(scenario)
    provider=RemoteProvider(workflow,client)
    result=workflow.run(provider,wallclock_seconds=wallclock_seconds)
    provider.flush()
    workflow.write_outputs(output,result)
    digest=hashlib.sha256((output/"decisions.csv").read_bytes()).hexdigest()
    return result,digest

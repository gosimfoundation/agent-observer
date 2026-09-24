"""Run a complete project using only public observations from the session API."""
from __future__ import annotations

import time
from datetime import datetime, timezone

from challenge.challenge_workflow import GlobalDeadlineExpired

from .docker_runtime import DockerWorkspace
from .session import SessionClient, SessionError, wait_until


def execute(runtime: DockerWorkspace, client: SessionClient, environment: dict[str,str], *, startup_seconds: float = 900):
    try:
        return _execute(runtime,client,environment,startup_seconds=startup_seconds)
    except GlobalDeadlineExpired:
        # The simulator still needs to persist and score the committed prefix.
        # Expiration ends participant decisions, not trusted result publication.
        runtime.close()
        finish_deadline=time.monotonic()+120
        while time.monotonic()<finish_deadline:
            status=client.call('status',deadline=finish_deadline)
            if status['status'] in ('scored','awaiting_csv'):
                return status
            if status['status'] in ('failed','cancelled'):
                raise SessionError('evaluation_failed')
            time.sleep(0.5)
        raise SessionError('result_publication_timeout')
    finally:
        runtime.close()


def _execute(runtime: DockerWorkspace, client: SessionClient, environment: dict[str,str], *, startup_seconds: float):
    runtime.build()
    transport=runtime.start(environment)
    startup=time.monotonic()+startup_seconds
    publication=wait_until(lambda:client.call("poll",deadline=startup)["publication"],deadline=startup)
    transport.publish_initial(publication)
    client.call("ready",deadline=startup)
    last_sequence=0
    last_response=None
    try:
        while True:
            try:
                message=client.call("poll",initialized=True)
            except SessionError as exc:
                if exc.code=="invalid_or_expired_capability":
                    status=client.call("status")
                    if status["status"] in ("scored","awaiting_csv"):
                        return status
                raise
            snapshot=message["observation"]
            if snapshot is None:
                time.sleep(0.1)
                continue
            sequence=message["sequence"]
            if sequence==last_sequence:
                # A lost POST response or a slow commit must not invoke a
                # nondeterministic participant model a second time.
                if not message["action_received"]:
                    client.call("respond",sequence=sequence,response=last_response)
                time.sleep(0.1)
                continue
            if sequence!=last_sequence+1:
                raise SessionError("unexpected_sequence")
            deadline_at=datetime.fromisoformat(message["deadline_at"].replace("Z","+00:00"))
            deadline=time.monotonic()+max(0,(deadline_at-datetime.now(timezone.utc)).total_seconds())
            response=transport(snapshot,deadline)
            client.call("respond",sequence=sequence,response=response,deadline=deadline)
            last_sequence,last_response=sequence,response
    finally:
        runtime.close()

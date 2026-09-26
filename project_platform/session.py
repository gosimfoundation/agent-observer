"""HTTP client shared by local participants and the isolated executor.

Only a scoped run capability is required. It cannot administer a project, read
another run, choose a future observation, or publish a score.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from challenge.challenge_workflow import GlobalDeadlineExpired
from .publication import encode_publication, decode_publication


@dataclass
class SessionError(RuntimeError):
    code: str
    status: int = 0

    def __str__(self):
        return self.code


# Run the session function next to the database. Each request then crosses the
# ocean once, and its server-side waits and database checks stay local.
SESSION_REGION = os.environ.get("OBSERVER_SESSION_REGION", "ap-southeast-1")
# Seconds the server may hold one poll open while waiting for the next step.
LONG_POLL_SECONDS = 10.0
LARGE_REQUEST_BYTES = 1024 * 1024


def long_poll_seconds(deadline: float | None) -> float:
    """Server wait that always ends before this client's own request timeout."""
    if deadline is None:
        return LONG_POLL_SECONDS
    return max(0.0, min(LONG_POLL_SECONDS, deadline-time.monotonic()-2))


class SessionClient:
    def __init__(self, url: str, credential: str, *, timeout: float = 30, catalog_timeout: float = 120):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")):
            raise ValueError("Session endpoint must use HTTPS (except a local test server).")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Invalid session endpoint.")
        self.url, self.credential, self.timeout = url, credential, timeout
        self.catalog_timeout = catalog_timeout
        self.opener = urllib.request.build_opener(_NoRedirect())

    def call(self, action: str, *, deadline: float | None = None, **arguments):
        if action == "initialize":
            arguments["publication"] = encode_publication(arguments["publication"])
        payload = json.dumps({"action": action, **arguments}, allow_nan=False, separators=(",", ":")).encode()
        # Catalogs and large observations (a formal first step is several MB) need
        # longer transfers than a normal step.
        request_timeout = self.catalog_timeout if (action == "initialize" or len(payload) > LARGE_REQUEST_BYTES or
            (action == "poll" and arguments.get("scope") != "engine" and not arguments.get("initialized"))) else self.timeout
        attempts = 0
        # Protocol writes are idempotent with sequence+body. A network retry must
        # send exactly the same action, never ask the agent to decide again.
        while True:
            remaining = (deadline-time.monotonic()) if deadline is not None else request_timeout
            if remaining <= 0:
                raise GlobalDeadlineExpired()
            request = urllib.request.Request(self.url, data=payload,
                headers={"Authorization":"Bearer "+self.credential, "Content-Type":"application/json",
                         **({"x-region":SESSION_REGION} if SESSION_REGION else {})}, method="POST")
            try:
                with self.opener.open(request, timeout=min(remaining,request_timeout)) as response:
                    raw = response.read(17*1024*1024+1)
                    if len(raw)>17*1024*1024:
                        raise SessionError("session_response_too_large")
                    result = json.loads(raw)["data"]
                    if action == "poll" and isinstance(result, dict) and result.get("publication") is not None:
                        result["publication"] = decode_publication(result["publication"])
                    return result
            except urllib.error.HTTPError as exc:
                try:
                    error = json.loads(exc.read(4096)).get("error","session_error")
                except (ValueError, AttributeError):
                    error = "session_error"
                if error == "session_deadline":
                    raise GlobalDeadlineExpired() from None
                if exc.code < 500 or attempts >= 2:
                    raise SessionError(str(error),exc.code) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempts >= 2:
                    raise SessionError("session_network_error") from None
            attempts += 1
            pause = min(0.25*attempts,max(0,(deadline-time.monotonic()) if deadline is not None else 1))
            time.sleep(pause)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SessionError("session_redirect_rejected",code)


def wait_until(check, *, deadline: float, interval: float = 0.1):
    while time.monotonic()<deadline:
        value=check()
        if value:
            return value
        time.sleep(min(interval,max(0,deadline-time.monotonic())))
    raise GlobalDeadlineExpired()

"""Bounded private project diagnostics; never copy a trusted exception verbatim."""
from __future__ import annotations

import re

from .job_client import JobError
from .session import SessionError


def safe_code(error: Exception) -> str:
    value=str(error)
    if isinstance(error,(JobError,SessionError)) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}',value):
        return value
    return 'project_operation_failed'


def private_log(value: str, secrets=()) -> str:
    for secret in secrets:
        if secret:value=value.replace(secret,'[REDACTED]')
    value=re.sub(r'https?://[^\s<>\x22\x27]+','[URL REDACTED]',value)
    value=re.sub(r'obs_[0-9a-f-]{36}\.[A-Za-z0-9_-]+','[REDACTED]',value)
    value=re.sub(r'(?:gh[pousr]_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+)','[REDACTED]',value)
    value=re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+','[REDACTED]',value)
    value=re.sub(r'(?i)(authorization\s*[:=]\s*|bearer\s+)[^\s]+',r'\1[REDACTED]',value)
    return value.encode()[-32768:].decode(errors='ignore')


class ProjectJobFailure(JobError):
    def __init__(self, diagnostics: dict):
        super().__init__('project_operation_failed')
        self.diagnostics=diagnostics

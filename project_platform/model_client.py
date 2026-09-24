"""Small non-streaming OpenAI-compatible client for preparation jobs."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .manifest import ProjectError
from .session import _NoRedirect


class ModelClient:
    def __init__(self, base_url: str, credential: str, *, timeout: float = 125):
        parsed=urllib.parse.urlsplit(base_url)
        if parsed.scheme!="https" and not (parsed.scheme=="http" and parsed.hostname in ("localhost","127.0.0.1")):
            raise ProjectError("Model proxy must use HTTPS except in local tests.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ProjectError("Invalid model proxy URL.")
        self.url=base_url.rstrip("/")+"/chat/completions"
        self.credential=credential
        self.timeout=timeout
        self.opener=urllib.request.build_opener(_NoRedirect())

    def __call__(self, body: dict) -> dict:
        payload=json.dumps(body,allow_nan=False).encode()
        if len(payload)>65536:
            raise ProjectError("Model request exceeds the proxy size limit.")
        call_id=str(uuid.uuid4())
        for attempt in range(3):
            request=urllib.request.Request(self.url,data=payload,method="POST",
                headers={"Authorization":"Bearer "+self.credential,"Content-Type":"application/json",
                         "Idempotency-Key":call_id})
            try:
                with self.opener.open(request,timeout=self.timeout) as response:
                    result=response.read(2*1024*1024+1)
                    if len(result)>2*1024*1024:
                        raise ProjectError("Model response is too large.")
                    value=json.loads(result)
                    if not isinstance(value,dict):
                        raise ProjectError("Invalid model response.")
                    return value
            except urllib.error.HTTPError as exc:
                if exc.code==409:
                    raise ProjectError("The model request was already received. Review the preparation status before retrying.") from None
                if exc.code<500 or attempt==2:
                    raise ProjectError("Model call failed (HTTP "+str(exc.code)+").") from None
            except (urllib.error.URLError,TimeoutError,ConnectionError):
                if attempt==2:
                    raise ProjectError("Model service is unavailable.") from None
            time.sleep(0.25*(attempt+1))
        raise ProjectError("Model service is unavailable.")

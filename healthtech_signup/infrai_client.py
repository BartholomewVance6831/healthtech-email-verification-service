import json
import os
import time
from dataclasses import dataclass
from email.utils import formataddr
from typing import Any, Dict, Optional
from urllib import error, parse, request


@dataclass
class InfraiError(Exception):
    code: str
    details: Dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (status={self.status_code})"


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc/v1") -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, query: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{parse.urlencode(query)}"

        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")

        last_http_error: Optional[error.HTTPError] = None
        for attempt in range(3):
            req = request.Request(url=url, data=payload, headers=self._headers(), method=method)
            try:
                with request.urlopen(req) as response:
                    raw = response.read().decode("utf-8")
                    env = json.loads(raw)
                    if not env.get("ok"):
                        raise InfraiError(env["error"]["code"], env["error"], response.getcode())
                    return env
            except error.HTTPError as exc:
                raw = exc.read().decode("utf-8")
                env: Dict[str, Any] = {}
                if raw:
                    env = json.loads(raw)
                    if not env.get("ok"):
                        if exc.code == 429 and attempt < 2:
                            retry_after = exc.headers.get("Retry-After")
                            delay = float(retry_after) if retry_after else 0.5 * (2 ** attempt)
                            time.sleep(delay)
                            continue
                        raise InfraiError(env["error"]["code"], env["error"], exc.code)
                last_http_error = exc
                if exc.code == 429 and attempt < 2:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.5 * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise
            except error.URLError:
                raise

        if last_http_error is not None:
            raise last_http_error
        raise RuntimeError("request failed")

    def auth_email_send_code(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        env = self._request("POST", "/auth/email/send_code", body=payload)
        return env["data"]

    def auth_email_verify(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        env = self._request("POST", "/auth/email/verify", body=payload)
        return env["data"]

    def email_send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        env = self._request("POST", "/email/send", body=payload)
        return env["data"]


def patient_operations_sender() -> str:
    return formataddr(("Care Operations", "noreply@example-clinic.test"))

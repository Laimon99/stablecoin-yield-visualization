from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from stablecoin_yield.raw import make_envelope, utc_timestamp

REDACTED = "<redacted>"
SENSITIVE_PARAMETER_FRAGMENTS = (
    "apikey",
    "authorization",
    "password",
    "secret",
    "token",
)


def redact_request_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Return request metadata that is safe to persist in raw envelopes."""
    redacted: dict[str, Any] = {}
    for key, value in parameters.items():
        normalized = "".join(character for character in key.lower() if character.isalnum())
        redacted[key] = (
            REDACTED
            if any(fragment in normalized for fragment in SENSITIVE_PARAMETER_FRAGMENTS)
            else value
        )
    return redacted


class SourceRequestError(RuntimeError):
    """Raised when a source request fails after retries."""


@dataclass(frozen=True)
class SourceResponse:
    envelope_path: str | None
    payload: Any
    status_code: int


class RateLimiter:
    def __init__(self, requests_per_minute: int | None) -> None:
        self._delay = 0.0 if not requests_per_minute else 60.0 / requests_per_minute
        self._last = 0.0

    def wait(self) -> None:
        if self._delay <= 0:
            return
        elapsed = time.monotonic() - self._last
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
        self._last = time.monotonic()


class JsonHttpClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        requests_per_minute: int | None = None,
        user_agent: str = "stablecoin-yield/1.0",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            timeout=timeout_seconds,
            headers={"User-Agent": user_agent},
            transport=transport,
        )
        self._limiter = RateLimiter(requests_per_minute)

    def close(self) -> None:
        self._client.close()

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, SourceRequestError)),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def get_json(
        self,
        *,
        source: str,
        base_url: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        documentation_url: str | None = None,
    ):
        self._limiter.wait()
        request_params = params or {}
        request_headers = headers or {}
        persisted_params = redact_request_parameters(request_params)
        requested_at = utc_timestamp()
        url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")
        response = self._client.get(url, params=request_params, headers=request_headers)
        received_at = utc_timestamp()
        if response.status_code >= 500 or response.status_code == 429:
            raise SourceRequestError(f"{source} {endpoint} returned {response.status_code}")
        response.raise_for_status()
        payload = response.json()
        return make_envelope(
            source=source,
            endpoint=endpoint,
            requested_at=requested_at,
            received_at=received_at,
            status_code=response.status_code,
            request_parameters=persisted_params,
            payload=payload,
            documentation_url=documentation_url,
            request_url=str(httpx.URL(url).copy_merge_params(persisted_params)),
        )

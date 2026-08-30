from __future__ import annotations

import httpx

from stablecoin_yield.http import JsonHttpClient


def test_sensitive_request_metadata_is_not_persisted() -> None:
    secret = "do-not-persist-this-key"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == secret
        assert request.url.params["api_key"] == secret
        return httpx.Response(200, json={"ok": True})

    client = JsonHttpClient(
        requests_per_minute=None,
        transport=httpx.MockTransport(handler),
    )
    try:
        envelope = client.get_json(
            source="test",
            base_url="https://example.test",
            endpoint="/data",
            params={"api_key": secret, "page": 1},
            headers={"x-api-key": secret},
        )
    finally:
        client.close()

    assert envelope.request_parameters == {"api_key": "<redacted>", "page": 1}
    assert secret not in str(envelope.request_parameters)
    assert secret not in str(envelope.request_url)

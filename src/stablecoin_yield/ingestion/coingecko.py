from __future__ import annotations

import os
from typing import Any

from stablecoin_yield.http import JsonHttpClient


class CoinGeckoClient:
    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3") -> None:
        self.base_url = base_url
        self.documentation_url = "https://docs.coingecko.com/demo/reference/coins-markets.md"
        self._http = JsonHttpClient(requests_per_minute=25)
        self._api_key = os.environ.get("COINGECKO_API_KEY")

    def close(self) -> None:
        self._http.close()

    def _auth_headers(self) -> dict[str, str]:
        """Send credentials as headers so raw request metadata never persists a key."""
        return {"x-cg-demo-api-key": self._api_key} if self._api_key else {}

    def coins_markets(self, ids: list[str], vs_currency: str = "usd"):
        params = {
            "vs_currency": vs_currency,
            "ids": ",".join(ids),
            "order": "market_cap_desc",
            "per_page": min(max(len(ids), 1), 250),
            "page": 1,
        }
        return self._http.get_json(
            source="coingecko",
            base_url=self.base_url,
            endpoint="/coins/markets",
            params=params,
            headers=self._auth_headers(),
            documentation_url=self.documentation_url,
        )

    def market_chart(self, coin_id: str, days: int = 365, vs_currency: str = "usd"):
        params: dict[str, Any] = {"vs_currency": vs_currency, "days": days, "interval": "daily"}
        return self._http.get_json(
            source="coingecko",
            base_url=self.base_url,
            endpoint=f"/coins/{coin_id}/market_chart",
            params=params,
            headers=self._auth_headers(),
            documentation_url="https://docs.coingecko.com/demo/reference/coins-id-market-chart.md",
        )

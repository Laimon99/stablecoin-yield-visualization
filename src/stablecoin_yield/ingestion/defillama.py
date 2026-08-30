from __future__ import annotations

from typing import Any

from stablecoin_yield.http import JsonHttpClient


class DefiLlamaYieldsClient:
    def __init__(self, base_url: str = "https://yields.llama.fi") -> None:
        self.base_url = base_url
        self.documentation_url = "https://api-docs.defillama.com/llms-free.txt"
        self._http = JsonHttpClient(requests_per_minute=60)

    def close(self) -> None:
        self._http.close()

    def pools(self):
        return self._http.get_json(
            source="defillama_yields",
            base_url=self.base_url,
            endpoint="/pools",
            documentation_url=self.documentation_url,
        )

    def chart(self, pool_id: str):
        return self._http.get_json(
            source="defillama_yields",
            base_url=self.base_url,
            endpoint=f"/chart/{pool_id}",
            documentation_url=self.documentation_url,
        )


class DefiLlamaStablecoinsClient:
    def __init__(self, base_url: str = "https://stablecoins.llama.fi") -> None:
        self.base_url = base_url
        self.documentation_url = "https://api-docs.defillama.com/llms-free.txt"
        self._http = JsonHttpClient(requests_per_minute=60)

    def close(self) -> None:
        self._http.close()

    def stablecoins(self, include_prices: bool = True):
        params: dict[str, Any] = {"includePrices": "true"} if include_prices else {}
        return self._http.get_json(
            source="defillama_stablecoins",
            base_url=self.base_url,
            endpoint="/stablecoins",
            params=params,
            documentation_url=self.documentation_url,
        )

    def stablecoin_prices(self):
        return self._http.get_json(
            source="defillama_stablecoins",
            base_url=self.base_url,
            endpoint="/stablecoinprices",
            documentation_url=self.documentation_url,
        )


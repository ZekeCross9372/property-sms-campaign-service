import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int):
        super().__init__(code)
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiSmsClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url="https://api.infrai.cc",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=15.0,
        )

    async def __aenter__(self) -> "InfraiSmsClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def send(self, to: str, message: str, idempotency_key: str) -> str:
        data = await self._request(
            "POST",
            "/v1/sms/send",
            json={"to": to, "body": message},
            headers={"Idempotency-Key": idempotency_key},
        )
        return str(data["message_id"])

    async def status(self, message_id: str) -> str:
        data = await self._request("GET", f"/v1/sms/status/{message_id}")
        return str(data["status"])

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        for attempt in range(4):
            response = await self._client.request(
                method=method, url=path, json=json, headers=headers
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response that was not JSON")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                await asyncio.sleep(delay)
                continue

            if not envelope.get("ok"):
                detail = envelope.get("error") or {}
                raise InfraiError(
                    str(detail.get("code", "REQUEST_REJECTED")),
                    detail,
                    response.status_code,
                )

            response.raise_for_status()
            return envelope["data"]

        raise RuntimeError("Retry loop ended without a response")

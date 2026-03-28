from flask import current_app
import requests

from app.errors import AppError, ValidationError


class TinyFishClient:
    def __init__(self) -> None:
        self.base_url = current_app.config["TINYFISH_BASE_URL"]
        self.api_key = current_app.config["TINYFISH_API_KEY"]
        self.timeout = current_app.config["TINYFISH_API_TIMEOUT_SECONDS"]

        if not self.api_key:
            raise ValidationError(
                "TinyFish API key is not configured.",
                payload={"env_var": "TINYFISH_API_KEY"},
            )

    def start_async_run(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.base_url}/v1/automation/run-async",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get_run(self, run_id: str) -> dict:
        response = requests.post(
            f"{self.base_url}/v1/runs/batch",
            headers=self._headers(),
            json={"run_ids": [run_id]},
            timeout=self.timeout,
        )
        payload = self._handle_response(response)
        if payload.get("not_found"):
            raise AppError("TinyFish run was not found.", status_code=404)
        data = payload.get("data") or []
        if not data:
            raise AppError("TinyFish returned an empty run lookup response.", status_code=502)
        return data[0]

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

    def _handle_response(self, response):
        try:
            payload = response.json()
        except ValueError as error:
            raise AppError("TinyFish returned a non-JSON response.", status_code=502) from error

        if response.status_code >= 400:
            raise AppError(
                "TinyFish API request failed.",
                status_code=502,
                payload={
                    "tinyfish_status": response.status_code,
                    "tinyfish_response": payload,
                },
            )
        return payload

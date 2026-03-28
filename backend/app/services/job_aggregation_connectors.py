from app.errors import ValidationError


def _coerce_jobs(payload: dict) -> list[dict]:
    jobs = payload.get("jobs") or []
    if not isinstance(jobs, list) or not jobs:
        raise ValidationError("Job ingestion requires a non-empty jobs array.")
    normalized = []
    for item in jobs:
        if not isinstance(item, dict):
            raise ValidationError("Each job item must be an object.")
        normalized.append(item)
    return normalized


class BaseJobSourceConnector:
    connector_type = "base"
    connector_name = "Base Connector"

    def fetch_jobs(self, payload: dict) -> list[dict]:
        raise NotImplementedError


class ManualJobSourceConnector(BaseJobSourceConnector):
    connector_type = "manual"
    connector_name = "Manual Payload Connector"

    def fetch_jobs(self, payload: dict) -> list[dict]:
        return _coerce_jobs(payload)


class TinyFishLinkedInConnector(BaseJobSourceConnector):
    connector_type = "tinyfish_linkedin"
    connector_name = "TinyFish LinkedIn Connector"

    def fetch_jobs(self, payload: dict) -> list[dict]:
        return _coerce_jobs(payload)


class JobConnectorRegistry:
    def __init__(self) -> None:
        self._connectors = {
            ManualJobSourceConnector.connector_type: ManualJobSourceConnector(),
            TinyFishLinkedInConnector.connector_type: TinyFishLinkedInConnector(),
        }

    def get_connector(self, connector_type: str) -> BaseJobSourceConnector:
        connector = self._connectors.get(str(connector_type).strip().lower())
        if not connector:
            raise ValidationError(
                f"Unsupported connector_type '{connector_type}'.",
                payload={"supported_connectors": sorted(self._connectors.keys())},
            )
        return connector

    def list_connectors(self) -> list[dict]:
        return [
            {
                "connector_type": connector.connector_type,
                "connector_name": connector.connector_name,
            }
            for connector in self._connectors.values()
        ]

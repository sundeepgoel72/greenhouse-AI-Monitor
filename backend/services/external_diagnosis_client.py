import json
from pathlib import Path
from typing import Any, Literal

import httpx

from app.config import settings


DiagnosisKind = Literal["plant", "disease"]


class ExternalDiagnosisClient:
    def __init__(self, kind: DiagnosisKind):
        self.kind = kind
        if kind == "plant":
            self.url = settings.plant_identification_api_url
            self.api_key = settings.plant_identification_api_key
        else:
            self.url = settings.disease_identification_api_url
            self.api_key = settings.disease_identification_api_key
        if not self.url:
            raise ValueError(f"{kind} identification API URL is not configured")
        if not self.api_key:
            raise ValueError(f"{kind} identification API key is not configured")

    def diagnose(self, image_path: str | Path, context: dict[str, Any]) -> dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            raise ValueError("diagnosis image does not exist")

        headers = {settings.external_diagnosis_api_key_header: self.api_key or ""}
        with path.open("rb") as image:
            response = httpx.post(
                self.url or "",
                headers=headers,
                files={
                    settings.external_diagnosis_image_field: (
                        path.name,
                        image,
                        "image/jpeg",
                    )
                },
                data={"context": json.dumps(context)},
                timeout=45,
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"external {self.kind} diagnosis API returned {exc.response.status_code}"
            ) from exc
        return normalize_external_response(response)


def normalize_external_response(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}
    return {
        "status": "ok",
        "provider_status_code": response.status_code,
        "result": payload,
    }

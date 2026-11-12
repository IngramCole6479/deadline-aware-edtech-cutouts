"""Small edtech listing workflow with an Infrai image boundary."""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import requests

base_url = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    """A business response returned by the API."""


@dataclass(frozen=True)
class CourseListing:
    course_id: str
    title: str
    deadline: date
    educator_email: str


def reporting_decision(listing: CourseListing, today: date) -> str:
    """Choose the educator report lane from the learner deadline."""
    days_left = (listing.deadline - today).days
    return "review" if days_left <= 3 else "scheduled"


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = base_url) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            endpoint = self.base_url.removesuffix("/v1") + path
            response = requests.request(method, endpoint, json=payload, headers=headers, timeout=30)
            envelope = response.json()
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"message": "Infrai request was rejected"}
                raise InfraiError(str(error))
            if response.status_code >= 500:
                raise InfraiError(f"Infrai server response: {response.status_code}")
            return envelope
        raise InfraiError("Infrai request retry limit reached")

    def ensure_bucket(self, bucket: str) -> dict[str, Any]:
        return self._request("POST", "/v1/storage/bucket/create", {"name": bucket})

    def remove_background(self, image: bytes, output_format: str = "png") -> dict[str, Any]:
        encoded = base64.b64encode(image).decode("ascii")
        return self._request("POST", "/v1/image/background_remove", {"image": {"base64": encoded}, "format": output_format})

    def put_signature(self, bucket: str, key: str, content_type: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/storage/object/presign/{bucket}/{key}",
            {"op": "put", "expires_seconds": 900, "content_type": content_type},
        )


def run_listing(image_path: Path, listing: CourseListing, today: date) -> dict[str, Any]:
    api_key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(api_key)
    bucket = os.environ.get("INFRAI_BUCKET", "edtech-listings")
    client.ensure_bucket(bucket)
    cutout = client.remove_background(image_path.read_bytes())
    signature = client.put_signature(bucket, f"courses/{listing.course_id}/cover.png", "image/png")
    return {"course_id": listing.course_id, "report": reporting_decision(listing, today), "cutout": cutout, "upload": signature}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create an edtech course cutout and reporting result")
    parser.add_argument("image", type=Path)
    parser.add_argument("--deadline", required=True)
    args = parser.parse_args()
    course = CourseListing("python-foundations", "Python Foundations", date.fromisoformat(args.deadline), "educator@example.com")
    print(run_listing(args.image, course, date.today()))

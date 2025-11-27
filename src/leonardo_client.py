from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"


@lru_cache(maxsize=1)
def get_api_key() -> str:
    """Return the Leonardo API key from .env or environment variables.

    The original implementation raised a RuntimeError during import if the key
    was missing, which prevented the rest of the application (including
    frontend development) from running. We lazily load and cache the key so the
    error is raised only when Leonardo requests are initiated.
    """

    load_dotenv(ROOT / ".env")
    api_key = (os.getenv("LEONARDO_API_KEY") or "").strip()
    if api_key and "<" not in api_key:
        return api_key

    raise RuntimeError(
        "LEONARDO_API_KEY not set. Add it to .env (LEONARDO_API_KEY=...) or set "
        "the environment variable before calling Leonardo APIs."
    )


def build_headers(api_key: str) -> dict:
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
    }


def _raise_request_error(resp: requests.Response, payload: dict[str, Any]) -> None:
    """Raise a RuntimeError with detailed context from a Leonardo response."""

    error_detail: str | None = None
    try:
        data = resp.json()
        error_detail = data.get("error") or data.get("message") or data
    except Exception:
        error_detail = resp.text

    hints = []
    if resp.status_code == 401:
        hints.append("Check LEONARDO_API_KEY; the key may be missing or invalid.")
    if resp.status_code == 400:
        hints.append(
            "Verify modelId, width/height limits, and that the prompt is not empty."
        )
        if payload.get("modelId"):
            hints.append(
                "Model IDs come from Leonardo > Models > (select model) > ID in the URL."
            )
    hint_text = f" Hints: {' '.join(hints)}" if hints else ""
    raise RuntimeError(
        f"Leonardo request failed ({resp.status_code}). Details: {error_detail}.{hint_text}"
    )


def start_generation(
    prompt: str,
    model_id: str,
    width: int = 1024,
    height: int = 1024,
    num_images: int = 1,
    negative_prompt: str | None = None,
    elements: list[dict] | None = None,
    dataset_id: str | None = None,
) -> str:
    """Kick off a Leonardo generation using the official `/generations` shape.

    The payload mirrors the Getting Started example (prompt, modelId, width,
    height, optional num_images) and intentionally omits unsupported training
    fields such as `datasetId`. Use the `/elements` endpoint separately if you
    need to train custom models.
    """
    api_key = get_api_key()
    headers = build_headers(api_key)
    payload: dict = {
        "prompt": prompt,
        "modelId": model_id,
        "width": width,
        "height": height,
        "num_images": num_images,
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    if elements:
        payload["elements"] = elements
    if dataset_id:
        payload["datasetId"] = dataset_id
    print("POST /generations payload:")
    print(json.dumps(payload, indent=2))

    try:
        resp = requests.post(
            f"{BASE_URL}/generations",
            headers=headers,
            json=payload,
            timeout=60,
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "Could not reach Leonardo. Check your internet connection, VPN/proxy, or DNS settings."
        ) from exc
    content_type = resp.headers.get("content-type", "")
    if not resp.ok:
        _raise_request_error(resp, payload)
    if "text/html" in content_type.lower():
        raise RuntimeError("Unexpected HTML from Leonardo (Cloudflare).")
    data = resp.json()
    # Leonardo returns sdGenerationJob.generationId; if missing, surface error
    if "sdGenerationJob" not in data or "generationId" not in data["sdGenerationJob"]:
        raise RuntimeError(f"Unexpected response from Leonardo: {data}")
    return data["sdGenerationJob"]["generationId"]


def poll_generation(generation_id: str, max_attempts: int = 30, interval_seconds: int = 5) -> dict:
    url = f"{BASE_URL}/generations/{generation_id}"
    api_key = get_api_key()
    headers = build_headers(api_key)
    for attempt in range(1, max_attempts + 1):
        time.sleep(interval_seconds)
        try:
            resp = requests.get(url, headers=headers, timeout=60)
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                "Could not reach Leonardo while polling. Check connectivity, VPN/proxy, or DNS."
            ) from exc
        if resp.status_code >= 400:
            print(f"Poll {attempt}: error {resp.status_code} {resp.text}")
            continue
        data = resp.json()
        gen = data.get("generations_by_pk") or data
        status = gen.get("status")
        print(f"Poll {attempt} status: {status}")
        if status == "COMPLETE":
            return gen
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Generation failed with status: {status}")
    raise RuntimeError("Polling ended without COMPLETE status")


def get_first_image_url(result_json: dict) -> str:
    images = result_json.get("generated_images") or []
    if not images:
        raise RuntimeError("No generated_images found in result JSON")
    url = images[0].get("url")
    if not url:
        raise RuntimeError("No URL found in first generated image")
    return url


def download_image(url: str, out_path: Path) -> Path:
    try:
        resp = requests.get(url, timeout=120)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "Could not download image from Leonardo. Check connectivity, VPN/proxy, or DNS."
        ) from exc
    resp.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path


def list_platform_models(limit: int = 15) -> list[dict[str, Any]]:
    """Return public platform models from Leonardo for easier ID selection.

    The official docs recommend pulling platform model IDs from
    `/api/rest/v1/platformModels` (see https://docs.leonardo.ai/docs/connect-to-leonardoai-mcp).
    This helper keeps the call in one place with the same error handling we use
    for generation requests.
    """

    api_key = get_api_key()
    headers = build_headers(api_key)
    try:
        resp = requests.get(
            f"{BASE_URL}/platformModels",
            headers=headers,
            params={"page": 1, "perPage": max(1, limit)},
            timeout=60,
        )
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            "Could not reach Leonardo platformModels. Check connectivity, VPN/proxy, or DNS."
        ) from exc
    if not resp.ok:
        _raise_request_error(resp, payload={})
    data = resp.json()
    models = data.get("data") or data
    if not isinstance(models, list):
        raise RuntimeError(f"Unexpected platformModels response: {data}")
    return models[:limit]


def generate_image_and_download(
    prompt: str,
    model_id: str,
    out_path: Path,
    width: int = 1024,
    height: int = 1024,
    num_images: int = 1,
    negative_prompt: str | None = None,
    element_id: str | None = None,
    dataset_id: str | None = None,
) -> tuple[Path, str]:
    elements = [{"id": element_id, "weight": 1.0}] if element_id else None
    generation_id = start_generation(
        prompt=prompt,
        model_id=model_id,
        width=width,
        height=height,
        num_images=num_images,
        negative_prompt=negative_prompt,
        elements=elements,
        dataset_id=dataset_id,
    )
    result = poll_generation(generation_id)
    image_url = get_first_image_url(result)
    local_path = download_image(image_url, out_path)
    return local_path, image_url

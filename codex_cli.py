from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# ---- User-configurable IDs ----
# Fill these in with your real Leonardo IDs before running the script.
BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

LEO_MODELS = {
    # Flux Dev (storybook style)
    "storybook_flux": "REPLACE_WITH_FLUX_DEV_MODEL_ID",
}

LEO_ELEMENTS = {
    # Your trained boy character Element (integer userLoraId)
    "boy_model": 0,
}


# ---- Helpers ----
def load_api_key() -> str:
    """Return the Leonardo API key from .env or environment variables."""

    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env")
    api_key = (os.getenv("LEONARDO_API_KEY") or "").strip()
    if api_key and "<" not in api_key:
        return api_key
    raise RuntimeError(
        "LEONARDO_API_KEY is missing. Add it to .env (LEONARDO_API_KEY=...) before running."
    )


def build_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }


def _parse_json_response(resp: requests.Response, context: str) -> dict:
    content_type = resp.headers.get("content-type", "")
    if "text/html" in content_type.lower():
        raise RuntimeError(
            f"{context}: Unexpected HTML from Leonardo (Cloudflare). Body: {resp.text[:300]}"
        )
    if "json" not in content_type.lower():
        raise RuntimeError(
            f"{context}: Expected JSON but got content-type '{content_type}'. Body: {resp.text[:300]}"
        )
    try:
        return resp.json()
    except ValueError as exc:
        raise RuntimeError(
            f"{context}: Could not parse JSON. Body: {resp.text[:300]}"
        ) from exc


def _raise_request_error(resp: requests.Response, payload: dict[str, Any]) -> None:
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
        hints.append("Verify modelId, userElements, prompt, and width/height limits.")
    hint_text = f" Hints: {' '.join(hints)}" if hints else ""
    raise RuntimeError(
        f"Leonardo request failed ({resp.status_code}). Details: {error_detail}.{hint_text}"
    )


# ---- Core workflow ----
def start_generation(prompt: str, width: int, height: int, num_images: int) -> str:
    """Kick off a generation using a base model + userLora element."""

    model_id = LEO_MODELS["storybook_flux"]
    user_lora_id = LEO_ELEMENTS["boy_model"]
    if not model_id or "REPLACE_WITH" in str(model_id):
        raise RuntimeError("Set LEO_MODELS['storybook_flux'] to your real modelId before running.")
    if not user_lora_id:
        raise RuntimeError("Set LEO_ELEMENTS['boy_model'] to your userLoraId (integer) before running.")
    try:
        user_lora_id_int = int(user_lora_id)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("userLoraId must be an integer (Leonardo user element ID).") from exc
    api_key = load_api_key()
    headers = build_headers(api_key)

    payload: dict[str, Any] = {
        "prompt": prompt,
        "modelId": model_id,
        "width": width,
        "height": height,
        "num_images": num_images,
        "userElements": [
            {
                "weight": 1.0,
                "userLoraId": user_lora_id_int,
            }
        ],
    }

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

    if not resp.ok:
        _raise_request_error(resp, payload)

    data = _parse_json_response(resp, "Leonardo generation response")
    try:
        return data["sdGenerationJob"]["generationId"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Unexpected response: {data}") from exc


def poll_generation(generation_id: str, interval_seconds: int = 5, max_attempts: int = 30) -> dict:
    api_key = load_api_key()
    headers = build_headers(api_key)
    url = f"{BASE_URL}/generations/{generation_id}"

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

        data = _parse_json_response(resp, "Leonardo poll response")
        gen = data.get("generations_by_pk") or data
        status = gen.get("status")
        print(f"Poll {attempt} status: {status}")
        if status == "COMPLETE":
            return gen
        if status in {"FAILED", "CANCELLED"}:
            raise RuntimeError(f"Generation failed with status: {status}")

    raise RuntimeError("Polling ended without COMPLETE status")


def extract_first_image_url(result: dict) -> str:
    images = result.get("generated_images") or []
    if not images:
        raise RuntimeError("No generated_images found in response")
    url = images[0].get("url")
    if not url:
        raise RuntimeError("No URL found in the first generated image")
    return url


def generate_image(prompt: str, width: int = 832, height: int = 1216, num_images: int = 1) -> dict:
    """
    Call Leonardo `/generations` using the configured base model and Element.

    - modelId: LEO_MODELS["storybook_flux"]
    - userElements: [{"userLoraId": LEO_ELEMENTS["boy_model"], "weight": 1.0}]
    """

    generation_id = start_generation(prompt, width=width, height=height, num_images=num_images)
    return poll_generation(generation_id)


# ---- CLI entrypoint ----
def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate a storybook image with Leonardo.ai")
    parser.add_argument(
        "prompt",
        nargs="?",
        default="storybook illustration of a happy child explorer, simple background, no text",
        help="Prompt to send to Leonardo",
    )
    parser.add_argument("--width", type=int, default=832, help="Image width")
    parser.add_argument("--height", type=int, default=1216, help="Image height")
    parser.add_argument("--num-images", type=int, default=1, help="Number of images to request")
    args = parser.parse_args(argv)

    try:
        result = generate_image(args.prompt, width=args.width, height=args.height, num_images=args.num_images)
        image_url = extract_first_image_url(result)
    except Exception as exc:  # noqa: BLE001
        print(exc)
        return 1

    print("\nGeneration complete.")
    print(f"First image URL: {image_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

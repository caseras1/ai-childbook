from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from config.models import (
    BASE_URL,
    LEO_ELEMENTS,
    LEO_MODELS,
    STORY_VARIANTS,
    STYLE_PRESETS,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def build_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }


def _parse_json_response(resp: requests.Response, context: str) -> Dict[str, Any]:
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


def _raise_request_error(resp: requests.Response, payload: Dict[str, Any]) -> None:
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


def _require_config_value(label: str, value: Any) -> Any:
    if value is None:
        raise RuntimeError(f"Set a value for {label} before running.")
    if isinstance(value, str) and (not value or "REPLACE_WITH" in value):
        raise RuntimeError(f"Replace the placeholder for {label} with your real value.")
    if isinstance(value, (int, float)) and value <= 0:
        raise RuntimeError(f"Set a positive value for {label} before running.")
    if isinstance(value, (list, tuple)) and not value:
        raise RuntimeError(f"Provide at least one entry for {label}.")
    return value


def _resolve_style(character: str, story: str) -> Dict[str, Any]:
    if character not in STYLE_PRESETS:
        raise RuntimeError(f"Unknown character key '{character}'. Choose from: {list(STYLE_PRESETS)}")
    if story not in STORY_VARIANTS:
        raise RuntimeError(f"Unknown story key '{story}'. Choose from: {list(STORY_VARIANTS)}")

    style = STYLE_PRESETS[character]
    story_cfg = STORY_VARIANTS[story]

    model_id = _require_config_value("LEO_MODELS[model_key]", LEO_MODELS.get(style["model_key"]))
    element_id = _require_config_value("LEO_ELEMENTS[element_key]", LEO_ELEMENTS.get(style["element_key"]))
    prompt_base = _require_config_value("STYLE_PRESETS base_prompt", style.get("base_prompt"))
    extra_prompt = _require_config_value("STORY_VARIANTS extra_prompt", story_cfg.get("extra_prompt"))

    try:
        user_lora_id_int = int(element_id)
    except (TypeError, ValueError) as exc:  # noqa: BLE001
        raise RuntimeError("userLoraId must be an integer (Leonardo user element ID).") from exc

    payload: Dict[str, Any] = {
        "prompt": f"{prompt_base}, {extra_prompt}",
        "modelId": model_id,
        "width": style.get("width", 832),
        "height": style.get("height", 1216),
        "num_images": 1,
        "alchemy": bool(style.get("alchemy", False)),
        "contrast": style.get("contrast"),
        "userElements": [
            {
                "weight": 1.0,
                "userLoraId": user_lora_id_int,
            }
        ],
    }

    image_prompts: List[str] = story_cfg.get("image_prompts") or []
    if image_prompts:
        payload["imagePrompts"] = image_prompts

    return payload


# ---------------------------------------------------------------------------
# Core workflow
# ---------------------------------------------------------------------------

def start_generation(payload: Dict[str, Any]) -> str:
    """Kick off a generation using the provided payload."""

    api_key = load_api_key()
    headers = build_headers(api_key)

    print("POST /generations payload:")
    print(json.dumps(payload, indent=2))

    try:
        resp = requests.post(
            f"{BASE_URL}/generations",
            headers=headers,
            json=payload,
            timeout=60,
        )
    except requests.exceptions.RequestException as exc:  # noqa: BLE001
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


def poll_generation(generation_id: str, interval_seconds: int = 5, max_attempts: int = 30) -> Dict[str, Any]:
    api_key = load_api_key()
    headers = build_headers(api_key)
    url = f"{BASE_URL}/generations/{generation_id}"

    for attempt in range(1, max_attempts + 1):
        time.sleep(interval_seconds)
        try:
            resp = requests.get(url, headers=headers, timeout=60)
        except requests.exceptions.RequestException as exc:  # noqa: BLE001
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


def extract_first_image_url(result: Dict[str, Any]) -> str:
    images = result.get("generated_images") or []
    if not images:
        raise RuntimeError("No generated_images found in response")
    url = images[0].get("url")
    if not url:
        raise RuntimeError("No URL found in the first generated image")
    return url


def generate_image(character: str, story: str) -> Dict[str, Any]:
    """Generate an image for the given character + story preset."""

    payload = _resolve_style(character, story)
    generation_id = start_generation(payload)
    return poll_generation(generation_id)


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a storybook image with Leonardo.ai using style + story presets",
    )
    parser.add_argument(
        "character",
        choices=sorted(STYLE_PRESETS.keys()),
        help="Which character style to use (e.g., boy, girl)",
    )
    parser.add_argument(
        "story",
        choices=sorted(STORY_VARIANTS.keys()),
        help="Which story variant to use (e.g., dino, princess, superhero)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=30,
        help="Max polling attempts",
    )
    args = parser.parse_args(argv)

    try:
        result = generate_image(args.character, args.story)
        image_url = extract_first_image_url(result)
    except Exception as exc:  # noqa: BLE001
        print(exc)
        return 1

    print("\nGeneration complete.")
    print(f"First image URL: {image_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

"""Leonardo connectivity and model ID helper.

Run this module to verify your API key and pull valid model IDs directly from
Leonardo's public platform models endpoint. This follows the official
integration guidance in the Leonardo docs
https://docs.leonardo.ai/docs/connect-to-leonardoai-mcp so you don't need to
guess or copy stale IDs.
"""

from typing import Any

from src.leonardo_client import BASE_URL, build_headers, get_api_key, list_platform_models
import requests


def _check_api_key() -> str:
    """Validate that the API key exists and has basic access."""

    api_key = get_api_key()
    headers = build_headers(api_key)
    # The platformModels call is lightweight and confirms the key works.
    try:
        resp = requests.get(f"{BASE_URL}/platformModels?page=1&perPage=1", headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "LEONARDO_API_KEY looks missing or invalid, or the service is unreachable. "
            "Double-check the key in your .env file and retry."
        ) from exc
    return api_key


def print_platform_models(limit: int = 10) -> None:
    """Fetch platform models and print their IDs and names for easy copy/paste."""

    models: list[dict[str, Any]] = list_platform_models(limit=limit)
    print(f"Found {len(models)} platform models (showing up to {limit}):")
    for m in models:
        model_id = m.get("id") or m.get("uuid") or m.get("modelId")
        name = m.get("name") or m.get("title") or m.get("label")
        print(f"- {name or 'Unnamed model'} :: {model_id}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Leonardo API key + model ID helper")
    parser.add_argument(
        "--list-platform-models",
        action="store_true",
        help="List platform model IDs from Leonardo to avoid stale IDs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="How many platform models to display (default: 10)",
    )
    args = parser.parse_args()

    _check_api_key()
    if args.list_platform_models:
        print_platform_models(limit=args.limit)
    else:
        print(
            "API key looks OK. To fetch model IDs, rerun with --list-platform-models",
        )


if __name__ == "__main__":
    main()

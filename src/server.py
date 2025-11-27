from __future__ import annotations

import sys
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.generate_story import generate_story, STORY_TEMPLATES
from config.models import MODELS

app = Flask(__name__, static_folder=str(ROOT / "frontend"), static_url_path="")


@app.route("/api/templates", methods=["GET"])
def api_templates():
    templates = [
        {"key": key, "title": meta["title"], "json": str(meta["json_path"])}
        for key, meta in STORY_TEMPLATES.items()
    ]
    return jsonify({"templates": templates})


@app.route("/api/models", methods=["GET"])
def api_models():
    models = [
        {"key": key, "title": cfg.get("title", key), "model_id": cfg.get("model_id")}
        for key, cfg in MODELS.items()
    ]
    return jsonify({"models": models})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    def _coerce_value(field: str) -> str:
        value = request.form.getlist(field) or request.form.get(field) or ""
        if isinstance(value, list):
            value = value[0] if value else ""
        return str(value)

    story_key = _coerce_value("story").strip().lower()
    model_key = _coerce_value("model").strip()
    child_name = _coerce_value("child_name").strip()
    # no image upload in this flow

    if story_key not in STORY_TEMPLATES:
        return jsonify({"error": "Invalid story key"}), 400
    if not child_name:
        return jsonify({"error": "Child name required"}), 400

    try:
        pdf_path = generate_story(
            story_key=story_key,
            child_name=child_name,
            # child_image_path=img_path,
            model_key=model_key or None,
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"ok": True, "pdf": str(pdf_path)})


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path: str):
    return send_from_directory(app.static_folder, path)


def main() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    main()

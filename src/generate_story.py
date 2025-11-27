from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFont

from src.leonardo_client import generate_image_and_download
from config.models import MODELS

ROOT = Path(__file__).resolve().parent.parent

STORY_TEMPLATES = {
    "dragons_20": {
        "title": "Anna and the Dragon Valley",
        "json_path": ROOT / "data" / "pages_dragons.json",
    },
    "vacation_20": {
        "title": "Anna's Vacation Dream",
        "json_path": ROOT / "data" / "pages_vacation.json",
    },
}

DEFAULT_MODEL_KEY = next(iter(MODELS.keys())) if MODELS else None
DEFAULT_MODEL_ID = ""
STYLE_HINT = "light-skinned girl with blond hair in a pink princess dress, holding a rose, castle softly blurred in the background"
NEGATIVE_PROMPT = "text, logo, watermark, nsfw, blood, gore, creepy, scary, low quality"


def load_pages(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        pages = json.load(f)
    pages = sorted(pages, key=lambda p: p["page"])
    return pages


def build_page_prompt(child_name: str, scene: str, style_hint: str = STYLE_HINT) -> str:
    return (
        f"3D storybook illustration of a child named {child_name}, "
        f"{style_hint}, in this scene: {scene}. "
        "Soft cinematic lighting, pastel colors, gentle depth of field, "
        "charming children's picture book style, high detail, no text, no logo."
    )


def render_page_with_text(image: Image.Image, text: str, title: str | None = None) -> Image.Image:
    font_main = _get_font(28)
    font_title = _get_font(22)
    padding = 24
    panel_height = int(image.height * 0.26)

    canvas = Image.new("RGB", (image.width, image.height), "white")
    # Illustration area
    illu_height = image.height - panel_height
    image_resized = image.resize((image.width, illu_height))
    canvas.paste(image_resized, (0, 0))

    # Panel
    panel = Image.new("RGB", (image.width, panel_height), (235, 242, 252))
    draw = ImageDraw.Draw(panel)
    y = padding
    if title:
        draw.text((padding, y), title, font=font_title, fill=(62, 82, 120))
        y += font_title.getbbox("Ag")[3] - font_title.getbbox("Ag")[1] + 8

    max_width = image.width - padding * 2
    lines = wrap_text(text, font_main, max_width)
    for line in lines:
        draw.text((padding, y), line, font=font_main, fill=(30, 41, 59))
        y += font_main.getbbox("Ag")[3] - font_main.getbbox("Ag")[1] + 6

    canvas.paste(panel, (0, illu_height))
    return canvas


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line: list[str] = []
    for word in words:
        test = " ".join(line + [word])
        if font.getlength(test) <= max_width:
            line.append(word)
        else:
            lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))
    return lines


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def generate_story(
    story_key: str,
    child_name: str,
    # child_image_path: Path,
    model_key: str | None = None,
    model_id: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    if story_key not in STORY_TEMPLATES:
        raise ValueError(f"Unknown story key: {story_key}")
    story = STORY_TEMPLATES[story_key]
    # Resolve model config
    model_cfg = None
    if model_key and model_key in MODELS:
        model_cfg = MODELS[model_key]
    elif DEFAULT_MODEL_KEY and DEFAULT_MODEL_KEY in MODELS:
        model_cfg = MODELS[DEFAULT_MODEL_KEY]
    else:
        model_cfg = next(iter(MODELS.values()), {})

    resolved_model_id = model_id or model_cfg.get("model_id") or DEFAULT_MODEL_ID
    if not resolved_model_id or "<" in resolved_model_id or resolved_model_id.strip() == "":
        raise ValueError("No valid model_id set. Update config/models.py with your trained model ID.")
    style_hint = model_cfg.get("style_hint", STYLE_HINT)
    title = story["title"]
    pages = load_pages(story["json_path"])
    output_dir = output_dir or (ROOT / "output" / f"{child_name.lower()}_{story_key}")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = ROOT / "output" / f"{child_name}_{title.replace(' ', '_')}.pdf"

    rendered_pages: list[Image.Image] = []
    for page in pages:
        prompt = build_page_prompt(child_name, page["scene"], style_hint=style_hint)
        out_img = output_dir / f"page_{page['page']:02d}.png"
        generate_image_and_download(
            prompt=prompt,
            model_id=resolved_model_id,
            out_path=out_img,
            width=1024,
            height=1024,
            negative_prompt=NEGATIVE_PROMPT,
        )
        img = Image.open(out_img).convert("RGB")
        page_img = render_page_with_text(img, page["text"], title=f"Page {page['page']}")
        rendered_pages.append(page_img)

    if not rendered_pages:
        raise RuntimeError("No pages rendered")
    first, *rest = rendered_pages
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    first.save(pdf_path, save_all=True, append_images=rest)
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="Generate a story PDF.")
    parser.add_argument("--story", required=True, help="Story key, e.g., dragons_20")
    parser.add_argument("--child-name", required=True, help="Child name")
    # parser.add_argument("--image-path", required=True, type=Path, help="Path to child photo")
    parser.add_argument("--model-key", help="Model key from config.models")
    parser.add_argument("--model-id", help="Override Leonardo model id (optional)")
    args = parser.parse_args()
    pdf = generate_story(
        story_key=args.story,
        child_name=args.child_name,
        # child_image_path=args.image_path,
        model_key=args.model_key,
        model_id=args.model_id,
    )
    print(f"Saved PDF: {pdf}")


if __name__ == "__main__":
    main()

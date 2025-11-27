# Leonardo setup guide

Follow these steps to get the API keys and IDs the app needs to generate a local book without uploading any of your own images to Leonardo.

## 1) Create an API key
1. Log into [https://app.leonardo.ai](https://app.leonardo.ai).
2. Open **Settings › API Keys**.
3. Click **Create New Key**, copy the value, and keep it safe. Treat it like a password.
4. Store it in a `.env` file at the repo root:
   ```
   LEONARDO_API_KEY=your-key-here
   ```
   (The code trims whitespace and will reject placeholder values like `<YOUR_KEY>`.)

## 2) Pick a model ID
- To use a platform model, open **Explore › Models**, pick a model, and copy the **ID** from the model detail page URL.
- To use one of your fine-tuned models, open **Models › Trained Models**, choose the model, and copy its ID from the URL.
- Update `config/models.py` with the ID (and optional `element_id`/style hint) or pass `--model-id` when running `generate_story.py`.

## 3) Optional: element/style IDs
If your trained model exposes an element/style ID, grab it from the model page and place it in `config/models.py` as `element_id`. The generation call includes the element so you get consistent styling.

## 4) Test your credentials
Run a lightweight smoke test (no uploads are performed):
```bash
python - <<'PY'
from src.leonardo_client import start_generation

# Uses the default SDXL base model unless you override the model_id below
try:
    start_generation(
        prompt="test ping for ai-childbook",
        model_id="16e7060a-803e-4df3-97ee-edcfa5dc9cc8",
        width=512,
        height=512,
    )
except Exception as exc:
    print(exc)
PY
```
If the API key or model ID is wrong, the error will now include hints (e.g., how to find a valid model ID).

## 5) Generate your first book locally
```bash
python -m src.generate_story --story dragons_20 --child-name Alex
```
The script only calls Leonardo to generate new images; it does **not** upload any of your local photos.

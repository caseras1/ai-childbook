# Leonardo setup guide

Follow these steps from Leonardo's official **Getting Started** guide so the project matches the documented `/generations` flow (no uploads, no datasets in the request body).

## 1) Create an API key
1. Log into [https://app.leonardo.ai](https://app.leonardo.ai).
2. Open **Settings › API Keys**.
3. Click **Create New Key**, copy the value, and keep it safe. Treat it like a password.
4. Store it in a `.env` file at the repo root:
   ```
   LEONARDO_API_KEY=your-key-here
   ```
   (The code trims whitespace and will reject placeholder values like `<YOUR_KEY>`.)

## 2) Pick a model ID (exactly what the docs expect)
- From Leonardo's UI: **Explore › Models** (for platform models) or **Models › Trained Models** (for your fine-tunes).
- Open the model page and copy the **ID** from the URL (e.g., `6bef9f1b-29cb-40c7-b9df-32b51c1f67d3`).
- Paste that ID into `config/models.py` under `model_id` (a list is allowed; the first non-empty entry is used) or pass `--model-id` on the CLI.
- No other IDs belong in the `/generations` call—**do not send `datasetId` in generation payloads**. Datasets are only used while training new models via the `/elements` endpoint, which is an advanced paid workflow.

### Minimal request that matches the docs
The official example payload is:

```bash
curl --request POST \
     --url https://cloud.leonardo.ai/api/rest/v1/generations \
     --header "accept: application/json" \
     --header "authorization: Bearer $LEONARDO_API_KEY" \
     --header "content-type: application/json" \
     --data '{
       "height": 512,
       "width": 512,
       "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
       "prompt": "An oil painting of a cat"
     }'
```

The project now sends this same shape (plus optional fields like `num_images` or `negative_prompt`) so you can copy/paste working values from the docs.

## 3) Optional: element/style IDs
If your trained model exposes an element/style ID, grab it from the model page and place it in `config/models.py` as `element_id`. The generation call includes the element for consistency, but datasets are not transmitted.

## 4) Test your credentials and pull model IDs from Leonardo (recommended)
The official docs recommend pulling platform models from Leonardo itself instead of copying stale IDs. Run the helper:

```bash
python -m src.leonardo_diag --list-platform-models --limit 8
```

- If the API key is missing or invalid, the script will fail immediately.
- The output lists model names alongside their IDs so you can copy them directly into `config/models.py`.

To sanity-check generation with the base SDXL model, you can still run this lightweight smoke test (no uploads are performed and no dataset IDs are sent):
```bash
python - <<'PY'
from src.leonardo_client import start_generation

try:
    start_generation(
        prompt="test ping for ai-childbook",
        model_id="6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Getting Started example model
        width=512,
        height=512,
    )
except Exception as exc:
    print(exc)
PY
```
If the API key or model ID is wrong, the error will include hints (e.g., how to find a valid model ID). If you see `Unexpected variable datasetId` from any other client, remove that field—it's not accepted by `/generations` per the official docs.

## 5) Generate your first book locally
```bash
python -m src.generate_story --story dragons_20 --child-name Alex
```
The script only calls Leonardo to generate new images; it does **not** upload any of your local photos.
- Use a model key defined in `config/models.py` (e.g., `--model-key boy_model`) or supply `--model-id` directly.
- If you later train your own model from a dataset, swap in that trained **model ID**; do not pass the dataset ID itself to `/generations`.

## If you hit a connection error
An error like `NameResolutionError` or "Could not reach Leonardo" means the client cannot resolve or reach `cloud.leonardo.ai`.
- Verify you are online (or not behind a restrictive VPN, proxy, or firewall).
- Try switching networks or DNS (e.g., Google DNS `8.8.8.8`) if resolution is blocked.
- Run the smoke test in step 4 again after connectivity is restored.

# config/models.py
#
# Define your Leonardo models here. Keep the dataset/init IDs in comments so you can reuse them later.

MODELS = {
    "default_princess": {
        "title": "Princess Pastel Style",
        "model_id": "217e-cf37-4b04-a11f-c6b61389dab8",
        "element_id": "6f3e-4d96-4f12-8f4b-8bb9735f4c5e",
        # "dataset_id": "a1f4-5b6c-7d
        "style_hint": "light-skinned girl with blond hair.",
    },
    "boy_dataset": {
        "title": "Boy Adventure Dataset",
        # Replace with your Leonardo dataset ID for boys (e.g., dino adventures)
        "dataset_id": "<BOY_DATASET_ID>",
        # Optionally keep the model_id empty to fall back to the SDXL base model
        # "model_id": "",
        "style_hint": "curly-haired boy wearing a T-rex hoodie, playful smile, bright outdoor scenes.",
    },
    "girl_dataset": {
        "title": "Girl Adventure Dataset",
        # Replace with your Leonardo dataset ID for girls (e.g., princess or space stories)
        "dataset_id": "<GIRL_DATASET_ID>",
        # Optionally keep the model_id empty to fall back to the SDXL base model
        # "model_id": "",
        "style_hint": "girl with wavy hair in pastel outfit, friendly expression, storybook lighting.",
    },
    # Add more styles as needed:
    # "space_style": {
    #     "title": "Cosmic Glow Style",
    #     "model_id": "<MODEL_ID>",
    #     # "dataset_id": "<DATASET_ID>",
    #     # "init_image_id": "<INIT_IMAGE_ID>",
    #     "style_hint": "child astronaut in soft neon space suit, pastel nebula background",
    # },
}

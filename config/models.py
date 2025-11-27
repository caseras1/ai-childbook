# config/models.py
#
# Define your Leonardo models here. Keep the dataset/init IDs in comments so you can reuse them later.

MODELS = {
    "boy_dataset": {
        "title": "Boy Adventure Dataset",
        # Replace with your Leonardo dataset ID for boys (e.g., dino adventures)
        "dataset_id": "edb5fc09-59ea-41f5-a484-227ca0712673",
        # Optionally keep the model_id empty to fall back to the SDXL base model
        "model_id": [
            "f37bf120-42da-4154-b803-90142b779922",
            "cb431562-df55-43bc-8673-cd9a607a18ab",
            "cac14d90-a3d3-4074-8681-d9685368a23b",
            "b3a33c7f-bc58-43bf-9174-659114ee8571",
            "da0c6489-d579-4403-bc4a-4096cfe8ab8a",
        ],
        "style_hint": "brown skinned boy, with blond hair and blue eyes. playful smile, bright outdoor scenes.",
    },
    # "girl_dataset": {
    #     "title": "Girl Adventure Dataset",
    #     # Replace with your Leonardo dataset ID for girls (e.g., princess or space stories)
    #     "dataset_id": "<GIRL_DATASET_ID>",
    #     # Optionally keep the model_id empty to fall back to the SDXL base model
    #     # "model_id": "",
    #     "style_hint": "girl with wavy hair in pastel outfit, friendly expression, storybook lighting.",
    # },
    # Add more styles as needed:
    # "space_style": {
    #     "title": "Cosmic Glow Style",
    #     "model_id": "<MODEL_ID>",
    #     # "dataset_id": "<DATASET_ID>",
    #     # "init_image_id": "<INIT_IMAGE_ID>",
    #     "style_hint": "child astronaut in soft neon space suit, pastel nebula background",
    # },
}

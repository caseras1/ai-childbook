# config/models.py
#
# Define your Leonardo models here. Keep dataset/init IDs in comments if you are training models separately.

MODELS = {
    "boy_model": {
        "title": "Boy Adventure Model",
        # Optional: keep dataset/init IDs as comments if you plan to train models later.
        # dataset_id: edb5fc09-59ea-41f5-a484-227ca0712673
        "model_id": [
            "f37bf120-42da-4154-b803-90142b779922",
            "cb431562-df55-43bc-8673-cd9a607a18ab",
            "cac14d90-a3d3-4074-8681-d9685368a23b",
            "b3a33c7f-bc58-43bf-9174-659114ee8571",
            "da0c6489-d579-4403-bc4a-4096cfe8ab8a",
        ],
        "style_hint": "brown skinned boy, with blond hair and blue eyes. playful smile, bright outdoor scenes.",
    },
    # "girl_model": {
    #     "title": "Girl Adventure Model",
    #     # Optional comment-only storage for dataset IDs if you train your own models later:
    #     # dataset_id: <GIRL_DATASET_ID>
    #     # Add your trained model ID(s) below when available.
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

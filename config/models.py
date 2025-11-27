"""Central Leonardo configuration used by both the CLI and story generator."""

BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"

# Leonardo model IDs (from the web app > Models > ID in the URL).
LEO_MODELS = {
    # Example: Phoenix 1.0 base model
    "phoenix_1_0": "REPLACE_WITH_MODEL_ID",
    # Add more models as needed (e.g., Flux, Alchemy, etc.)
}

# Leonardo user Elements (trained LoRA IDs). These are integers.
LEO_ELEMENTS = {
    # Example: your trained boy element (userLoraId)
    "boy_model": 0,
    # Example: your trained girl element (userLoraId)
    "girl_model": 0,
}

# Base style presets for each character type.
# Fill in the prompts/settings you used when you created the images in that style.
STYLE_PRESETS = {
    "boy": {
        "title": "Boy collection style",
        "model_key": "phoenix_1_0",  # points to LEO_MODELS
        "element_key": "boy_model",  # points to LEO_ELEMENTS
        "base_prompt": "REPLACE_WITH_BOY_BASE_PROMPT",
        "width": 832,
        "height": 1216,
        "alchemy": True,
        "contrast": 3.5,
    },
    "girl": {
        "title": "Girl collection style",
        "model_key": "phoenix_1_0",
        "element_key": "girl_model",
        "base_prompt": "REPLACE_WITH_GIRL_BASE_PROMPT",
        "width": 832,
        "height": 1216,
        "alchemy": True,
        "contrast": 3.5,
    },
}

# Story variants layered on top of the base style.
STORY_VARIANTS = {
    "dino": {
        "extra_prompt": "REPLACE_WITH_DINO_STORY_DETAILS",
        # Optional: image IDs from your collection to nudge style
        "image_prompts": [],
    },
    "princess": {
        "extra_prompt": "REPLACE_WITH_PRINCESS_STORY_DETAILS",
        "image_prompts": [],
    },
    "superhero": {
        "extra_prompt": "REPLACE_WITH_SUPERHERO_STORY_DETAILS",
        "image_prompts": [],
    },
}

# Backwards-compatible model list used by the story generator UI.
# You can keep dataset/init IDs as comments if you plan to train models later.
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

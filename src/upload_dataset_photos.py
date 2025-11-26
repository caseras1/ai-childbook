
# # src/upload_anna_photos.py
# from pathlib import Path
# import sys

# ROOT = Path(__file__).resolve().parent.parent
# if str(ROOT) not in sys.path:
#     sys.path.append(str(ROOT))

# from config.models import child_config
# from src.leonardo_client import upload_dataset_image_local


# def main():
#     dataset_id = child_config.get("dataset_id")
#     if not dataset_id or dataset_id.startswith("YOUR-"):
#         raise RuntimeError("Set a valid dataset_id in config/child_anna.py first")

#     # Put your kid photos in AI_Childbook/input/
#     # e.g. anna_01.jpg, anna_02.jpg, ...
#     input_dir = ROOT / "input"
#     if not input_dir.exists():
#         raise RuntimeError(f"Input folder not found: {input_dir}")

#     # choose which files to upload (here: all jpg/jpeg/png/webp in input/)
#     candidates = []
#     for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
#         candidates.extend(input_dir.glob(ext))

#     if not candidates:
#         raise RuntimeError(f"No images found in {input_dir} (jpg/jpeg/png/webp).")

#     print(f"Found {len(candidates)} image(s) to upload to dataset {dataset_id}:\n")
#     for p in candidates:
#         print(" -", p)

#     print("\nStarting upload...")

#     for p in candidates:
#         print(f"\n=== Uploading {p.name} ===")
#         info = upload_dataset_image_local(dataset_id, p)
#         print("Result:", info)

#     print("\n✅ All uploads finished.")


# if __name__ == "__main__":
#     main()
# --- IGNORE ---
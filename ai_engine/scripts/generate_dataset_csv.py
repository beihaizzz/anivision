"""Generate CSV index for the onepiece dataset.

Scans data/datasets/onepiece/{train,val,test}/ and produces a CSV with columns:
    image_path, label, label_name, split

Usage:
    python scripts/generate_dataset_csv.py

The CSV is written to ai_engine/models/dataset.csv by default.
"""
import argparse
import csv
import os
import json
from pathlib import Path

# Project root relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATASET_DIR = PROJECT_ROOT / "data" / "datasets" / "onepiece"
LABEL_MAP_PATH = SCRIPT_DIR.parent / "models" / "label_map.json"
DEFAULT_OUTPUT = SCRIPT_DIR.parent / "models" / "dataset.csv"


def load_label_map(path: Path) -> dict:
    """Load label_map.json and build {dir_name: label_id} mapping."""
    with open(path, "r", encoding="utf-8") as f:
        label_map = json.load(f)

    # Build reverse mapping: folder name → label id
    # Folder names are pinyin: lufei, luobin, namei, ...
    # label_map keys are "0", "1", ... in order matching folder listing order
    folder_order = ["lufei", "luobin", "namei", "qiaoba", "shanzhi", "suolong", "wusuopu"]
    dir_to_id = {}
    for idx, folder in enumerate(folder_order):
        if str(idx) in label_map:
            dir_to_id[folder] = idx
    return dir_to_id


def generate_csv(dataset_dir: Path, output_file: Path):
    """Walk train/val/test dirs and write CSV."""
    dir_to_id = load_label_map(LABEL_MAP_PATH)
    label_map = {}
    with open(LABEL_MAP_PATH, "r", encoding="utf-8") as f:
        label_map = json.load(f)

    rows = []
    for split in ["train", "val", "test"]:
        split_dir = dataset_dir / split
        if not split_dir.exists():
            print(f"  [WARN] {split_dir} does not exist, skipping.")
            continue

        for char_dir in sorted(split_dir.iterdir()):
            if not char_dir.is_dir():
                continue

            folder_name = char_dir.name.lower()
            label_id = dir_to_id.get(folder_name)
            if label_id is None:
                print(f"  [WARN] Unknown character folder: {folder_name}, skipping.")
                continue

            label_name = label_map.get(str(label_id), folder_name)

            for img_file in sorted(char_dir.iterdir()):
                if img_file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
                    rows.append({
                        "image_path": str(img_file.resolve()),
                        "label": label_id,
                        "label_name": label_name,
                        "split": split,
                    })

    # Write CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "label", "label_name", "split"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {output_file} with {len(rows)} entries.")
    # Summary
    for split in ["train", "val", "test"]:
        count = sum(1 for r in rows if r["split"] == split)
        print(f"  {split}: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dataset CSV index")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=str(DATASET_DIR),
        help="Path to the dataset root directory (default: data/datasets/onepiece)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="Output CSV file path",
    )
    args = parser.parse_args()
    generate_csv(Path(args.dataset_dir), Path(args.output))

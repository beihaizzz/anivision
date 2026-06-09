"""Dataset splitting script skeleton."""
import argparse
import os
import shutil
from pathlib import Path


def split_dataset(input_dir, output_dir, ratio="7:2:1"):
    """Split dataset into train/val/test partitions.

    Args:
        input_dir: Directory containing all images.
        output_dir: Directory to save split datasets.
        ratio: Split ratio as string "train:val:test" (e.g., "7:2:1").
    """
    # TODO: Implement dataset splitting
    # - Parse ratio
    # - Stratified split by character
    # - Create train/val/test directories
    # - Copy/move images to respective folders
    raise NotImplementedError("Dataset splitting implementation in Phase 2")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split dataset into train/val/test")
    parser.add_argument("--input-dir", type=str, required=True, help="Input directory with all images")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory for split datasets")
    parser.add_argument("--ratio", type=str, default="7:2:1", help="Split ratio (e.g., 7:2:1)")
    args = parser.parse_args()
    split_dataset(args.input_dir, args.output_dir, args.ratio)
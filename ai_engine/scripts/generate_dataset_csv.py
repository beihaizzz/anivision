"""CSV dataset generator script skeleton."""
import argparse
import csv
import os
from pathlib import Path


def generate_csv(input_dir, output_file):
    """Generate CSV file listing all dataset images with labels.

    Args:
        input_dir: Directory containing split datasets (train/val/test subdirs).
        output_file: Path to output CSV file.
    """
    # TODO: Implement CSV generation
    # - Scan train/val/test subdirectories
    # - Extract image paths and labels
    # - Write CSV with columns: image_path, label, split
    raise NotImplementedError("CSV generation implementation in Phase 2")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dataset CSV file")
    parser.add_argument("--input-dir", type=str, required=True, help="Input directory with split datasets")
    parser.add_argument("--output-file", type=str, required=True, help="Output CSV file path")
    args = parser.parse_args()
    generate_csv(args.input_dir, args.output_file)
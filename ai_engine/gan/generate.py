"""CLI: Generate batch of GAN images for data augmentation.

Generates N images per class using a trained cDCGAN generator,
saves them to data/generated/{dataset}/{class_name}/.

Usage:
    python -m gan.generate --dataset onepiece            # 30 images/class
    python -m gan.generate --dataset aot --count 60      # 60 images/class
    python -m gan.generate --dataset onepiece --model-path models/gan/generator_epoch_100.pth
"""
import argparse
import os
import sys
from pathlib import Path

from tqdm import tqdm

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.gan.generator import GANGenerator

# ── Constants ──────────────────────────────────────────────────────────
DATASET_PATHS = {
    "onepiece": {
        "model_dir": PROJECT_ROOT / "ai_engine" / "models" / "gan",
        "generator_file": "generator_best.pth",
        "output_base": PROJECT_ROOT / "data" / "generated" / "onepiece",
        "num_classes": 7,
        "class_names": ["lufei", "luobin", "namei", "qiaoba", "shanzhi", "suolong", "wusuopu"],
    },
    "aot": {
        "model_dir": PROJECT_ROOT / "ai_engine" / "models" / "gan" / "aot",
        "generator_file": "generator_best.pth",
        "output_base": PROJECT_ROOT / "data" / "generated" / "aot",
        "num_classes": 14,
        "class_names": [f"{i:03d}" for i in range(1, 15)],  # 001, 002, ..., 014
    },
}


def main():
    parser = argparse.ArgumentParser(description="Generate GAN images for data augmentation")
    parser.add_argument("--dataset", type=str, required=True, choices=["onepiece", "aot"],
                        help="Dataset to generate images for")
    parser.add_argument("--model-path", type=str, default=None,
                        help="Path to generator .pth (default: models/gan/{dataset}/generator_best.pth)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: data/generated/{dataset}/)")
    parser.add_argument("--count", type=int, default=30,
                        help="Number of images to generate per character class")
    parser.add_argument("--device", type=str, default="cuda",
                        help="Device: cuda / cpu")

    args = parser.parse_args()
    cfg = DATASET_PATHS[args.dataset]

    # Resolve model path
    if args.model_path:
        model_path = Path(args.model_path)
    else:
        model_path = cfg["model_dir"] / cfg["generator_file"]

    if not model_path.exists():
        print(f"❌ Generator checkpoint not found: {model_path}")
        print(f"   Train a {args.dataset} GAN first:")
        print(f"   python -m gan.train --data-dir data/datasets/{args.dataset} "
              f"--output-dir {cfg['model_dir']}")
        sys.exit(1)

    # Resolve output dir
    output_base = Path(args.output_dir) if args.output_dir else cfg["output_base"]
    output_base.mkdir(parents=True, exist_ok=True)

    # ── Load generator ──
    print(f"Loading generator: {model_path}")
    gen = GANGenerator(
        model_path=str(model_path),
        num_classes=cfg["num_classes"],
    )
    print(f"  Device: {gen.device}")
    print(f"  Target: {args.count} images × {cfg['num_classes']} classes = "
          f"{args.count * cfg['num_classes']} total")

    # ── Generate per class ──
    total_generated = 0
    for class_id, class_name in enumerate(cfg["class_names"]):
        class_dir = output_base / class_name
        class_dir.mkdir(parents=True, exist_ok=True)

        images = gen.generate(character_id=class_id, count=args.count)

        for i, img in enumerate(images):
            img_path = class_dir / f"gan_{i:03d}.png"
            img.save(img_path)

        total_generated += len(images)
        print(f"  ✓ {class_name}: {len(images)} images → {class_dir}")

    # ── Done ──
    print(f"\n{'=' * 55}")
    print(f"Done — {total_generated} images generated → {output_base}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()

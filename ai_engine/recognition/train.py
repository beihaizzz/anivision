"""Training script for anime character recognition using EfficientNet-B3.

Dataset directory structure expected:
    data/datasets/onepiece/
        train/
            lufei/   (images)
            luobin/  (images)
            ...
        val/
            lufei/
            luobin/
            ...
        test/
            ...

Usage:
    python -m recognition.train                          # uses defaults
    python -m recognition.train --epochs 80 --lr 0.0005  # custom
    python -m recognition.train --device cpu              # force CPU
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from tqdm import tqdm

# Resolve project root and add to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.recognition.model import AnimeRecognitionModel

# ── Constants ──────────────────────────────────────────────────────────
DATASET_DIR = PROJECT_ROOT / "data" / "datasets" / "onepiece"
OUTPUT_DIR = PROJECT_ROOT / "ai_engine" / "models"
LABEL_MAP_PATH = OUTPUT_DIR / "label_map.json"
INPUT_SIZE = 300  # EfficientNet-B3 standard
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def get_transforms(train: bool = True):
    """Build image transforms. Training adds augmentation for small datasets."""
    if train:
        return transforms.Compose(
            [
                transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=15),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
                transforms.ToTensor(),
                transforms.Normalize(mean=MEAN, std=STD),
            ]
        )
    else:
        return transforms.Compose(
            [
                transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(mean=MEAN, std=STD),
            ]
        )


def build_dataloaders(data_dir: Path, batch_size: int, num_workers: int):
    """Create train/val dataloaders using ImageFolder."""
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists():
        raise FileNotFoundError(f"Training directory not found: {train_dir}")
    if not val_dir.exists():
        raise FileNotFoundError(f"Validation directory not found: {val_dir}")

    train_dataset = datasets.ImageFolder(str(train_dir), transform=get_transforms(train=True))
    val_dataset = datasets.ImageFolder(str(val_dir), transform=get_transforms(train=False))

    # ImageFolder assigns labels in alphabetical order: lufei(0), luobin(1), namei(2), ...
    print(f"Classes detected ({len(train_dataset.classes)}): {train_dataset.classes}")
    print(f"Samples - train: {len(train_dataset)}, val: {len(val_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )
    return train_loader, val_loader, train_dataset.classes


def train_one_epoch(model, loader, criterion, optimizer, device, epoch):
    """Single training epoch. Returns average loss and accuracy."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    pbar = tqdm(loader, desc=f"Epoch {epoch:3d} [train]", unit="batch", leave=False)
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += labels.size(0)

        pbar.set_postfix(loss=f"{loss.item():.4f}", acc=f"{100.0 * correct / total:.1f}%")

    return running_loss / total, 100.0 * correct / total


@torch.no_grad()
def validate(model, loader, criterion, device, epoch):
    """Validation pass. Returns average loss and accuracy."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    pbar = tqdm(loader, desc=f"Epoch {epoch:3d} [val  ]", unit="batch", leave=False)
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += labels.size(0)

        pbar.set_postfix(loss=f"{loss.item():.4f}", acc=f"{100.0 * correct / total:.1f}%")

    return running_loss / total, 100.0 * correct / total


def save_checkpoint(model, classes, output_dir: Path, filename: str):
    """Save model state dict and class names (Chinese names from label_map.json)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = output_dir / filename
    torch.save(model.state_dict(), ckpt_path)
    print(f"  Checkpoint saved → {ckpt_path}")

    # Load label_map.json to get Chinese names; fall back to folder names
    mapping_path = output_dir / "class_names.json"
    label_map_path = output_dir / "label_map.json"
    label_names = {}
    if label_map_path.exists():
        with open(label_map_path, "r", encoding="utf-8") as f:
            label_names = json.load(f)

    class_map = {}
    for i, folder_name in enumerate(classes):
        class_map[str(i)] = label_names.get(str(i), folder_name)

    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(class_map, f, ensure_ascii=False, indent=2)


def log_epoch(epoch, train_loss, train_acc, val_loss, val_acc, lr, elapsed):
    """Print one-line epoch summary."""
    print(
        f"Epoch {epoch:3d} | "
        f"train loss={train_loss:.4f}  acc={train_acc:5.1f}% | "
        f"val loss={val_loss:.4f}  acc={val_acc:5.1f}% | "
        f"lr={lr:.2e} | {elapsed:.1f}s"
    )


def train(args):
    """Main training routine."""
    # ── Device ──
    if args.device.lower() == "cuda":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    # ── Data ──
    data_dir = Path(args.data_dir)
    train_loader, val_loader, classes = build_dataloaders(data_dir, args.batch_size, args.num_workers)
    num_classes = len(classes)

    # ── Model ──
    model = AnimeRecognitionModel(num_classes=num_classes, pretrained=not args.no_pretrain)
    model = model.to(device)
    param_info = model.get_trainable_params()
    print(f"Model: EfficientNet-B3 | {num_classes} classes")
    print(
        f"  Params: {param_info['total']:,} total, "
        f"{param_info['trainable']:,} trainable, "
        f"{param_info['frozen']:,} frozen"
    )

    # ── Loss / Optimizer / Scheduler ──
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # ── Training loop ──
    output_dir = Path(args.output_dir)
    best_val_acc = 0.0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}

    print(f"\n{'='*60}")
    print(f"Training started — {args.epochs} epochs, batch_size={args.batch_size}")
    print(f"{'='*60}")

    start_time = time.time()
    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()

        # Train
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device, epoch)

        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, device, epoch)

        # Step scheduler
        scheduler.step()
        current_lr = scheduler.get_last_lr()[0]

        # Log
        elapsed = time.time() - epoch_start
        log_epoch(epoch, train_loss, train_acc, val_loss, val_acc, current_lr, elapsed)

        # Track history
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        # Save best
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_checkpoint(model, classes, output_dir, "best_model.pth")

    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Training complete — {total_time / 60:.1f} min total")
    print(f"Best val accuracy: {best_val_acc:.2f}%")
    print(f"{'='*60}")

    # ── Final save ──
    save_checkpoint(model, classes, output_dir, "last_model.pth")
    print("Done.")


# ── CLI ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train anime character recognition model")
    parser.add_argument("--data-dir", type=str, default=str(DATASET_DIR), help="Dataset root directory")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="Output directory for checkpoints")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Initial learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay for AdamW")
    parser.add_argument("--num-workers", type=int, default=2, help="DataLoader workers")
    parser.add_argument("--device", type=str, default="cuda", help="Device: cuda / cpu")
    parser.add_argument("--no-pretrain", action="store_true", help="Disable ImageNet pretrained weights")
    args = parser.parse_args()
    train(args)

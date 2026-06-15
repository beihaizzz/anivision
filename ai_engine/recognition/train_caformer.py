"""
CAFormer-S36 Training Script — Anime Character Recognition
===========================================================
Danbooru-pretrained CAFormer-S36 (animetimm) fine-tuned on
One Piece (7 classes) or Attack on Titan (14 classes) datasets.

Architecture:
    CAFormer-S36: ConvNeXt backbone + local attention blocks
    Danbooru pretrained (4M+ anime images, 12,476 tags)
    → Replace MlpHead → Linear(num_classes)
    → Progressive unfreezing + EMA + CosineAnnealingWarmRestarts

Usage:
    # One Piece (ready)
    python -m recognition.train_caformer --dataset onepiece

    # AOT (requires dataset at data/datasets/aot/)
    python -m recognition.train_caformer --dataset aot

HF Token:
    set HF_TOKEN=hf_your_token
    (model is gated — accept terms at huggingface.co/animetimm/caformer_s36.dbv4-full)
"""
import argparse
import json
import os
import time
from copy import deepcopy
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, LambdaLR, SequentialLR
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from tqdm import tqdm

# ── Project paths ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # ai_engine/
DATA_ROOT = PROJECT_ROOT.parent / "data" / "datasets"
OUTPUT_ROOT = PROJECT_ROOT / "models"

# ── Constants ──────────────────────────────────────────────────────────
INPUT_SIZE = 384  # CAFormer-S36 native
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

# ── Dataset Presets ────────────────────────────────────────────────────
PRESETS = {
    "onepiece": {
        "data_dir": str(DATA_ROOT / "onepiece"),
        "num_classes": 7,
        "label_map": "label_map.json",
        "gan_dir": str(PROJECT_ROOT.parent / "data" / "generated" / "onepiece"),
        "batch_size": 16,
        "epochs": 100,
        "lr": 1e-3,
        "weight_decay": 0.01,
        "label_smoothing": 0.1,
        "randaug_n": 1,
        "randaug_m": 5,
        "color_jitter": 0.1,
        "warmup_epochs": 3,
        "freeze_epochs": 10,
        "T0": 10,
        "Tmult": 1,
        "early_stop_patience": 15,
    },
    "aot": {
        "data_dir": str(DATA_ROOT / "aot"),
        "num_classes": 14,
        "label_map": "label_map.json",
        "gan_dir": None,  # No GAN trained for AOT yet
        "batch_size": 32,
        "epochs": 80,
        "lr": 1e-3,
        "weight_decay": 0.02,
        "label_smoothing": 0.1,
        "randaug_n": 2,
        "randaug_m": 9,
        "color_jitter": 0.2,
        "warmup_epochs": 5,
        "freeze_epochs": 5,
        "T0": 15,
        "Tmult": 2,
        "early_stop_patience": 12,
    },
}


# ═══════════════════════════════════════════════════════════════════════
# EMA (Exponential Moving Average)
# ═══════════════════════════════════════════════════════════════════════
class ModelEMA:
    """Exponential Moving Average of model weights.

    Keeps a shadow copy of trainable parameters. Use apply() before
    validation/inference, restore() before resuming training.
    """

    def __init__(self, model: nn.Module, decay: float = 0.999):
        self.model = model
        self.decay = decay
        self.shadow: dict[str, torch.Tensor] = {}
        self.backup: dict[str, torch.Tensor] = {}
        self._register()

    def _register(self):
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.shadow[name] = param.data.clone().detach()

    def update(self):
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.shadow[name].mul_(self.decay).add_(param.data, alpha=1 - self.decay)

    def apply(self):
        """Swap EMA weights into model (for eval)."""
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.backup[name] = param.data.clone()
                param.data.copy_(self.shadow[name])

    def restore(self):
        """Restore original weights (for continued training)."""
        for name, param in self.model.named_parameters():
            if param.requires_grad and name in self.backup:
                param.data.copy_(self.backup[name])
        self.backup.clear()


# ═══════════════════════════════════════════════════════════════════════
# Model
# ═══════════════════════════════════════════════════════════════════════
def build_model(num_classes: int, hf_token: str = None) -> nn.Module:
    """Load CAFormer-S36 with Danbooru pretraining, replace classification head.

    Args:
        num_classes: Number of character classes (7 for OP, 14 for AOT).
        hf_token: HuggingFace token for gated model access.

    Returns:
        CAFormer-S36 model with custom classifier head.
    """
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token

    if "HF_TOKEN" not in os.environ:
        print("⚠️  HF_TOKEN not set. Attempting unauthenticated load...")
        print("   If download fails, set: set HF_TOKEN=hf_your_token")
        print("   Accept terms at: https://huggingface.co/animetimm/caformer_s36.dbv4-full")

    import timm

    model = timm.create_model(
        "hf-hub:animetimm/caformer_s36.dbv4-full",
        pretrained=True,
    )

    # Replace Danbooru tag head (12,476 classes) with our classifier
    in_features = model.num_features  # 512
    model.reset_classifier(num_classes=num_classes)

    print(f"Model: CAFormer-S36 (Danbooru pretrained)")
    print(f"  Backbone features: {in_features}")
    print(f"  Output classes: {num_classes}")
    total = sum(p.numel() for p in model.parameters())
    print(f"  Total params: {total / 1e6:.1f}M")

    return model


def set_trainable(model: nn.Module, backbone_trainable: bool):
    """Freeze or unfreeze all backbone parameters. Head always trainable."""
    for name, param in model.named_parameters():
        if name.startswith("head") or name.startswith("fc"):
            param.requires_grad = True
        else:
            param.requires_grad = backbone_trainable

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    status = "UNFROZEN" if backbone_trainable else "FROZEN"
    print(f"  Backbone: {status} | Trainable: {trainable / 1e6:.1f}M / {total / 1e6:.1f}M")


# ═══════════════════════════════════════════════════════════════════════
# Data
# ═══════════════════════════════════════════════════════════════════════
def build_gan_dataset(gan_dir: str, class_names: list, transform) -> torch.utils.data.Dataset | None:
    """Load GAN-generated images matching the given class folders.

    Returns None if gan_dir doesn't exist or has no matching classes.
    """
    gan_dir = Path(gan_dir)
    if not gan_dir.exists():
        print(f"  GAN: directory not found ({gan_dir}), skipping")
        return None

    # ImageFolder auto-detects classes from subdirectories
    gan_dataset = datasets.ImageFolder(str(gan_dir), transform=transform)

    # Verify class alignment
    if gan_dataset.classes != class_names:
        print(f"  GAN: class mismatch! GAN={gan_dataset.classes}, train={class_names}")
        return None

    print(f"  GAN data: {len(gan_dataset)} generated images (30/class)")
    return gan_dataset


def build_dataloaders(
    data_dir: str,
    batch_size: int,
    num_workers: int,
    randaug_n: int,
    randaug_m: int,
    color_jitter: float,
    use_gan: bool = False,
    gan_dir: str = None,
):
    """Build train/val DataLoaders with ImageFolder (+ optional GAN augmentation).

    Expected directory structure:
        data_dir/
            train/
                lufei/  (images)
                luobin/ (images)
                ...
            val/
                ...

    GAN directory (optional):
        gan_dir/
            lufei/   (generated images)
            luobin/  (generated images)
            ...
    """
    data_dir = Path(data_dir)

    train_transform = transforms.Compose(
        [
            transforms.RandomResizedCrop(INPUT_SIZE, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandAugment(num_ops=randaug_n, magnitude=randaug_m),
            transforms.ColorJitter(
                brightness=color_jitter,
                contrast=color_jitter,
                saturation=color_jitter,
                hue=0.05,
            ),
            transforms.ToTensor(),
            transforms.Normalize(mean=MEAN, std=STD),
        ]
    )

    val_transform = transforms.Compose(
        [
            transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=MEAN, std=STD),
        ]
    )

    train_dir = data_dir / "train"
    val_dir = data_dir / "val"

    if not train_dir.exists():
        raise FileNotFoundError(f"Train directory not found: {train_dir}")
    if not val_dir.exists():
        raise FileNotFoundError(f"Val directory not found: {val_dir}")

    train_dataset = datasets.ImageFolder(str(train_dir), transform=train_transform)
    val_dataset = datasets.ImageFolder(str(val_dir), transform=val_transform)

    # GAN augmentation
    gan_count = 0
    if use_gan and gan_dir:
        gan_dataset = build_gan_dataset(gan_dir, train_dataset.classes, train_transform)
        if gan_dataset is not None:
            from torch.utils.data import ConcatDataset
            gan_count = len(gan_dataset)
            train_dataset = ConcatDataset([train_dataset, gan_dataset])

    print(f"Dataset: {data_dir.name}")
    print(f"  Classes ({len(train_dataset.datasets[0].classes if gan_count else train_dataset.classes)}): "
          f"{', '.join(train_dataset.datasets[0].classes if gan_count else train_dataset.classes)}")
    real_count = len(train_dataset) - gan_count if gan_count else len(train_dataset)
    print(f"  Samples — train: {len(train_dataset)} (real: {real_count}"
          + (f", GAN: {gan_count})" if gan_count else ")"))
    print(f"  Val: {len(val_dataset)}")

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


# ═══════════════════════════════════════════════════════════════════════
# Training / Validation loops
# ═══════════════════════════════════════════════════════════════════════
def train_one_epoch(
    model, loader, criterion, optimizer, device, epoch, ema: ModelEMA = None
):
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

        if ema:
            ema.update()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += labels.size(0)

        pbar.set_postfix(
            loss=f"{loss.item():.4f}", acc=f"{100.0 * correct / total:.1f}%"
        )

    return running_loss / total, 100.0 * correct / total


@torch.no_grad()
def validate(model, loader, criterion, device, ema: ModelEMA = None):
    if ema:
        ema.apply()

    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in tqdm(loader, desc="Validating", unit="batch", leave=False):
        images, labels = images.to(device), labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        correct += predicted.eq(labels).sum().item()
        total += labels.size(0)

    if ema:
        ema.restore()

    return running_loss / total, 100.0 * correct / total


# ═══════════════════════════════════════════════════════════════════════
# Checkpoint
# ═══════════════════════════════════════════════════════════════════════
def save_checkpoint(
    model, ema: ModelEMA, classes, output_dir: Path, filename: str, extra: dict = None
):
    """Save model state dict, EMA weights, and metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Regular checkpoint
    ckpt_path = output_dir / filename
    torch.save(model.state_dict(), ckpt_path)

    # EMA checkpoint
    if ema:
        ema.apply()
        ema_path = output_dir / filename.replace(".pth", "_ema.pth")
        torch.save(model.state_dict(), ema_path)
        ema.restore()

    # Metadata
    meta = {"architecture": "caformer_s36", "num_classes": len(classes), "classes": classes}
    if extra:
        meta.update(extra)
    meta_path = output_dir / "model_config.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    size_mb = ckpt_path.stat().st_size / 1e6
    print(f"  Checkpoint → {ckpt_path.name} ({size_mb:.1f} MB)")


def save_label_map(classes, output_dir: Path, label_map_path: str):
    """Generate/update label_map.json from ImageFolder classes.

    Uses existing label_map.json if present (for Chinese character names),
    otherwise falls back to folder names.
    """
    existing_map = {}
    existing_path = output_dir / label_map_path
    if existing_path.exists():
        with open(existing_path, "r", encoding="utf-8") as f:
            existing_map = json.load(f)

    label_map = {}
    for i, folder_name in enumerate(classes):
        label_map[str(i)] = existing_map.get(str(i), folder_name)

    with open(existing_path, "w", encoding="utf-8") as f:
        json.dump(label_map, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
def train(args):
    cfg = PRESETS[args.dataset]
    # CLI overrides
    for key in [
        "batch_size", "epochs", "lr", "weight_decay", "label_smoothing",
        "randaug_n", "randaug_m", "color_jitter", "warmup_epochs",
        "freeze_epochs", "T0", "Tmult", "early_stop_patience",
    ]:
        if getattr(args, key, None) is not None:
            cfg[key] = getattr(args, key)

    # ── Device ──
    if args.device == "cuda" and torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    # ── Data ──
    train_loader, val_loader, classes = build_dataloaders(
        data_dir=cfg["data_dir"],
        batch_size=cfg["batch_size"],
        num_workers=args.num_workers,
        randaug_n=cfg["randaug_n"],
        randaug_m=cfg["randaug_m"],
        color_jitter=cfg["color_jitter"],
        use_gan=args.use_gan,
        gan_dir=cfg.get("gan_dir"),
    )

    # ── Model ──
    model = build_model(num_classes=cfg["num_classes"], hf_token=args.hf_token)
    model = model.to(device)

    # Phase 1: train head only
    set_trainable(model, backbone_trainable=False)

    # ── Optimizer ──
    optimizer = optim.AdamW(
        model.parameters(),
        lr=cfg["lr"],
        weight_decay=cfg["weight_decay"],
    )

    # ── Loss ──
    criterion = nn.CrossEntropyLoss(label_smoothing=cfg["label_smoothing"])

    # ── Scheduler: Warmup → CosineAnnealingWarmRestarts ──
    warmup = LambdaLR(
        optimizer,
        lr_lambda=lambda e: (e + 1) / max(1, cfg["warmup_epochs"]),
    )
    cosine = CosineAnnealingWarmRestarts(
        optimizer,
        T_0=cfg["T0"],
        T_mult=cfg["Tmult"],
    )
    scheduler = SequentialLR(
        optimizer,
        schedulers=[warmup, cosine],
        milestones=[cfg["warmup_epochs"]],
    )

    # ── EMA ──
    ema = None if args.no_ema else ModelEMA(model, decay=0.999)

    # ── Output ──
    output_dir = OUTPUT_ROOT / args.dataset
    if args.output_name:
        output_dir = output_dir / args.output_name
    output_dir.mkdir(parents=True, exist_ok=True)
    save_label_map(classes, output_dir, cfg["label_map"])

    # ── Training loop ──
    best_val_acc = 0.0
    patience_counter = 0
    history: dict = {
        "train_loss": [], "train_acc": [],
        "val_loss": [], "val_acc": [],
        "lr": [],
        "config": {
            "architecture": "caformer_s36",
            "dataset": args.dataset,
            "num_classes": cfg["num_classes"],
            "total_train": len(train_loader.dataset),
            "use_gan": args.use_gan,
            "batch_size": cfg["batch_size"],
            "epochs_trained": 0,
            "lr": cfg["lr"],
            "weight_decay": cfg["weight_decay"],
            "label_smoothing": cfg["label_smoothing"],
        },
    }

    print(f"\n{'=' * 60}")
    print(f"Training: {args.dataset} | {cfg['num_classes']} classes | {cfg['epochs']} epochs")
    print(f"  Batch: {cfg['batch_size']} | LR: {cfg['lr']} | WD: {cfg['weight_decay']}")
    print(f"  Label Smoothing: {cfg['label_smoothing']} | EMA: {'ON' if ema else 'OFF'}")
    print(f"  GAN Augmentation: {'ON' if args.use_gan else 'OFF'}")
    print(f"{'=' * 60}\n")

    start_time = time.time()
    for epoch in range(1, cfg["epochs"] + 1):
        epoch_start = time.time()

        # Progressive unfreezing
        if epoch == cfg["freeze_epochs"] + 1:
            print(f"\n─── Epoch {epoch}: Unfreezing backbone ───")
            set_trainable(model, backbone_trainable=True)
            # Re-create optimizer for newly trainable params
            optimizer = optim.AdamW(
                model.parameters(),
                lr=cfg["lr"] * 0.1,  # lower LR after unfreezing
                weight_decay=cfg["weight_decay"],
            )
            # Re-create scheduler
            warmup2 = LambdaLR(
                optimizer,
                lr_lambda=lambda e: max(0.5, 1.0),  # gentle restart
            )
            cosine2 = CosineAnnealingWarmRestarts(
                optimizer, T_0=cfg["T0"], T_mult=cfg["Tmult"]
            )
            scheduler = SequentialLR(
                optimizer, schedulers=[warmup2, cosine2], milestones=[1]
            )
            if ema:
                ema = ModelEMA(model, decay=0.999)

        # Train
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch, ema
        )

        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, device, ema)

        # Step scheduler
        scheduler.step()
        current_lr = optimizer.param_groups[0]["lr"]

        # Log
        elapsed = time.time() - epoch_start
        print(
            f"Epoch {epoch:3d} | "
            f"train loss={train_loss:.4f}  acc={train_acc:5.1f}% | "
            f"val loss={val_loss:.4f}  acc={val_acc:5.1f}% | "
            f"lr={current_lr:.2e} | {elapsed:.1f}s"
        )

        # Track
        history["train_loss"].append(round(train_loss, 4))
        history["train_acc"].append(round(train_acc, 2))
        history["val_loss"].append(round(val_loss, 4))
        history["val_acc"].append(round(val_acc, 2))
        history["lr"].append(current_lr)

        # Save best
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            save_checkpoint(
                model, ema, classes, output_dir, "best_model.pth",
                extra={
                    "val_acc": val_acc, "epoch": epoch,
                    "use_gan": args.use_gan,
                },
            )
        else:
            patience_counter += 1

        # Early stop
        if patience_counter >= cfg["early_stop_patience"]:
            print(f"\nEarly stopping triggered at epoch {epoch}")
            break

    # ── Finish ──
    total_time = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Training complete — {total_time / 60:.1f} min")
    print(f"Best val accuracy: {best_val_acc:.2f}%")
    print(f"{'=' * 60}")

    # Save training log
    log_path = output_dir / "training_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print(f"Training log → {log_path}")


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train CAFormer-S36 for anime character recognition"
    )
    parser.add_argument(
        "--dataset", type=str, required=True, choices=["onepiece", "aot"],
        help="Dataset to train on",
    )
    parser.add_argument("--hf-token", type=str, default=None, help="HF token for gated model")
    parser.add_argument("--device", type=str, default="cuda", help="cuda / cpu")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers (0=safe on Windows)")
    parser.add_argument("--no-ema", action="store_true", help="Disable EMA")
    parser.add_argument("--use-gan", action="store_true", help="Augment training data with GAN-generated images")
    parser.add_argument("--output-name", type=str, default=None,
                        help="Subdirectory name under models/{dataset}/ to isolate this run (e.g. baseline, gan-run)")

    # Override presets
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--weight-decay", type=float, default=None)
    parser.add_argument("--label-smoothing", type=float, default=None)
    parser.add_argument("--randaug-n", type=int, default=None)
    parser.add_argument("--randaug-m", type=int, default=None)
    parser.add_argument("--color-jitter", type=float, default=None)
    parser.add_argument("--warmup-epochs", type=int, default=None)
    parser.add_argument("--freeze-epochs", type=int, default=None)
    parser.add_argument("--T0", type=int, default=None)
    parser.add_argument("--Tmult", type=int, default=None)
    parser.add_argument("--early-stop-patience", type=int, default=None)

    args = parser.parse_args()
    train(args)

"""Train conditional DCGAN for anime character data augmentation.

Generates 128×128 RGB images conditioned on character labels.
Training follows the DCGAN paper with conditional extension.

Usage:
    python -m gan.train                          # defaults
    python -m gan.train --epochs 200 --lr 0.0002 # custom
"""
import argparse
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.utils as vutils
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from tqdm import tqdm

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.gan.dcgan import cDCGANGenerator, cDCGANDiscriminator

# ── Constants ──────────────────────────────────────────────────────────
DATASET_DIR = PROJECT_ROOT / "data" / "datasets" / "onepiece"
OUTPUT_DIR = PROJECT_ROOT / "ai_engine" / "models" / "gan"
IMAGE_SIZE = 128
LATENT_DIM = 100
NUM_CLASSES = 7
FIXED_NOISE = None  # set after dataloader init


def build_dataloader(data_dir: Path, batch_size: int, num_workers: int):
    """Build training dataloader with 128×128 resize and [-1,1] normalization."""
    train_dir = data_dir / "train"
    if not train_dir.exists():
        raise FileNotFoundError(f"Training directory not found: {train_dir}")

    transform = transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )

    dataset = datasets.ImageFolder(str(train_dir), transform=transform)
    print(f"GAN dataset: {len(dataset)} images, {len(dataset.classes)} classes: {dataset.classes}")

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
    )
    return loader, dataset.classes


def weights_init(m):
    """Initialize Conv/ConvTranspose/BatchNorm weights (DCGAN paper)."""
    classname = m.__class__.__name__
    if classname.find("Conv") != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find("BatchNorm") != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


def save_samples(generator, fixed_noise, fixed_labels, output_dir: Path, epoch: int):
    """Generate and save a grid of sample images."""
    generator.eval()
    with torch.no_grad():
        fake = generator(fixed_noise, fixed_labels)
        grid = vutils.make_grid(fake, nrow=7, normalize=True, value_range=(-1, 1))
        vutils.save_image(grid, output_dir / f"epoch_{epoch:04d}.png")
    generator.train()


def save_checkpoint(generator, discriminator, output_dir: Path, epoch: int, is_best: bool = False):
    """Save G and D state dicts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = "best" if is_best else f"epoch_{epoch:04d}"
    torch.save(generator.state_dict(), output_dir / f"generator_{suffix}.pth")
    torch.save(discriminator.state_dict(), output_dir / f"discriminator_{suffix}.pth")


def train(args):
    # ── Device ──
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    # ── Data ──
    loader, classes = build_dataloader(DATASET_DIR, args.batch_size, args.num_workers)
    num_classes = len(classes)

    # ── Fixed noise for consistent sample visualization ──
    global FIXED_NOISE
    sample_count = num_classes * 4  # 4 samples per class
    FIXED_NOISE = torch.randn(sample_count, LATENT_DIM, device=device)
    fixed_labels = torch.arange(num_classes).repeat_interleave(4).to(device)

    # ── Models ──
    netG = cDCGANGenerator(latent_dim=LATENT_DIM, num_classes=num_classes).to(device)
    netD = cDCGANDiscriminator(num_classes=num_classes).to(device)
    netG.apply(weights_init)
    netD.apply(weights_init)

    print(f"Generator params:    {sum(p.numel() for p in netG.parameters()):,}")
    print(f"Discriminator params: {sum(p.numel() for p in netD.parameters()):,}")

    # ── Loss & Optimizers ──
    criterion = nn.BCEWithLogitsLoss()
    optG = optim.Adam(netG.parameters(), lr=args.lr, betas=(0.5, 0.999))
    optD = optim.Adam(netD.parameters(), lr=args.lr, betas=(0.5, 0.999))

    # ── Output dirs ──
    output_dir = Path(args.output_dir)
    sample_dir = output_dir / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # ── Training loop ──
    real_label = 1.0
    fake_label = 0.0

    history = {"g_loss": [], "d_loss": []}
    best_g_loss = float("inf")

    print(f"\n{'='*60}")
    print(f"GAN Training — {args.epochs} epochs, batch={args.batch_size}, lr={args.lr}")
    print(f"{'='*60}")

    for epoch in range(1, args.epochs + 1):
        g_losses = []
        d_losses = []

        pbar = tqdm(loader, desc=f"Epoch {epoch:4d}", unit="batch", leave=False)
        for i, (real_imgs, labels) in enumerate(pbar):
            real_imgs = real_imgs.to(device)
            labels = labels.to(device)
            batch_size = real_imgs.size(0)

            # ── Train Discriminator ──
            netD.zero_grad()

            # Real images
            output_real = netD(real_imgs, labels)
            loss_d_real = criterion(output_real, torch.full_like(output_real, real_label))

            # Fake images
            noise = torch.randn(batch_size, LATENT_DIM, device=device)
            fake_imgs = netG(noise, labels).detach()
            output_fake = netD(fake_imgs, labels)
            loss_d_fake = criterion(output_fake, torch.full_like(output_fake, fake_label))

            loss_d = loss_d_real + loss_d_fake
            loss_d.backward()
            optD.step()

            # ── Train Generator ──
            netG.zero_grad()
            noise = torch.randn(batch_size, LATENT_DIM, device=device)
            fake_imgs = netG(noise, labels)
            output = netD(fake_imgs, labels)
            loss_g = criterion(output, torch.full_like(output, real_label))
            loss_g.backward()
            optG.step()

            g_losses.append(loss_g.item())
            d_losses.append(loss_d.item())

            pbar.set_postfix(D=f"{loss_d.item():.4f}", G=f"{loss_g.item():.4f}")

        avg_g = sum(g_losses) / len(g_losses)
        avg_d = sum(d_losses) / len(d_losses)
        history["g_loss"].append(avg_g)
        history["d_loss"].append(avg_d)

        print(f"Epoch {epoch:4d} | D loss={avg_d:.4f}  G loss={avg_g:.4f}")

        # Save samples every N epochs
        if epoch % 10 == 0 or epoch == 1:
            save_samples(netG, FIXED_NOISE, fixed_labels, sample_dir, epoch)

        # Save best generator
        if avg_g < best_g_loss:
            best_g_loss = avg_g
            save_checkpoint(netG, netD, output_dir, epoch, is_best=True)

    # ── Final save ──
    save_checkpoint(netG, netD, output_dir, args.epochs)
    save_samples(netG, FIXED_NOISE, fixed_labels, sample_dir, args.epochs)
    print(f"\n{'='*60}")
    print(f"GAN training complete. Checkpoints → {output_dir}")
    print(f"Samples → {sample_dir}")
    print(f"{'='*60}")


# ── CLI ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train conditional DCGAN")
    parser.add_argument("--data-dir", type=str, default=str(DATASET_DIR), help="Dataset root")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--epochs", type=int, default=200, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.0002, help="Learning rate")
    parser.add_argument("--num-workers", type=int, default=2, help="DataLoader workers")
    args = parser.parse_args()
    train(args)

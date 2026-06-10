"""Generator wrapper for conditional DCGAN.

Loads a trained generator checkpoint and provides an interface for
generating anime character images conditioned on class labels.

Usage:
    gen = GANGenerator("models/gan/generator_best.pth", num_classes=7)
    images = gen.generate(character_id=0, count=8)  # 8 Luffy images
"""
from typing import List

import torch
from PIL import Image
from torchvision.transforms.functional import to_pil_image

from .dcgan import cDCGANGenerator


class GANGenerator:
    """Wrapper for cDCGAN generator — loads checkpoint and generates images.

    Args:
        model_path: Path to generator .pth checkpoint.
        num_classes: Number of character classes.
        latent_dim: Noise dimension (default 100).
    """

    def __init__(self, model_path: str, num_classes: int = 7, latent_dim: int = 100):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.num_classes = num_classes
        self.latent_dim = latent_dim

        self.generator = cDCGANGenerator(
            latent_dim=latent_dim, num_classes=num_classes
        )
        self.generator.load_state_dict(
            torch.load(model_path, map_location=self.device, weights_only=True)
        )
        self.generator.to(self.device)
        self.generator.eval()

    def generate(self, character_id: int, count: int = 1) -> List[Image.Image]:
        """Generate images for a specific character.

        Args:
            character_id: Class index (0-6).
            count: Number of images to generate.

        Returns:
            List of PIL.Image (128×128 RGB).
        """
        noise = torch.randn(count, self.latent_dim, device=self.device)
        labels = torch.full((count,), character_id, dtype=torch.long, device=self.device)

        with torch.no_grad():
            fake = self.generator(noise, labels)  # (count, 3, 128, 128)

        # [-1, 1] → [0, 1] → PIL
        images = []
        for i in range(count):
            tensor = (fake[i].cpu() + 1.0) / 2.0
            tensor = tensor.clamp(0.0, 1.0)
            images.append(to_pil_image(tensor))

        return images

    def generate_batch(self, character_ids: List[int]) -> List[Image.Image]:
        """Generate one image per character_id (faster than individual calls).

        Args:
            character_ids: List of class indices.

        Returns:
            List of PIL.Image (128×128 RGB), one per character_id.
        """
        count = len(character_ids)
        noise = torch.randn(count, self.latent_dim, device=self.device)
        labels = torch.tensor(character_ids, dtype=torch.long, device=self.device)

        with torch.no_grad():
            fake = self.generator(noise, labels)

        images = []
        for i in range(count):
            tensor = (fake[i].cpu() + 1.0) / 2.0
            tensor = tensor.clamp(0.0, 1.0)
            images.append(to_pil_image(tensor))

        return images

"""Conditional DCGAN for anime character data augmentation.

Architecture follows the detailed design spec:
  - Generator: noise(100) + label_embed(512) → 128×128 RGB
  - Discriminator: image(128×128) + label condition → real/fake

Training config: Adam(lr=0.0002, β1=0.5), BCE loss, batch=64.
"""
import torch
import torch.nn as nn


class cDCGANGenerator(nn.Module):
    """Conditional DCGAN Generator.

    Input:  noise z ∈ R^100  +  class label (int)
    Output: RGB image (3, 128, 128), values in [-1, 1]
    """

    def __init__(self, latent_dim: int = 100, num_classes: int = 7, channels: int = 3):
        super().__init__()
        self.latent_dim = latent_dim
        self.num_classes = num_classes

        # Label embedding
        self.label_embed = nn.Sequential(
            nn.Embedding(num_classes, latent_dim),
            nn.Linear(latent_dim, latent_dim),
            nn.LeakyReLU(0.2),
        )

        # Noise projection: 100 → 512 * 4 * 4
        self.noise_proj = nn.Sequential(
            nn.Linear(latent_dim, 512 * 4 * 4),
            nn.BatchNorm1d(512 * 4 * 4),
            nn.ReLU(True),
        )

        # Label projection to match noise feat map
        self.label_proj = nn.Sequential(
            nn.Linear(latent_dim, 512 * 4 * 4),
            nn.BatchNorm1d(512 * 4 * 4),
            nn.ReLU(True),
        )

        # Upsampling blocks: concat noise+label → 128×128
        self.main = nn.Sequential(
            # (1024, 4, 4) → (512, 8, 8)
            nn.ConvTranspose2d(1024, 512, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(512),
            nn.ReLU(True),
            # (512, 8, 8) → (256, 16, 16)
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(True),
            # (256, 16, 16) → (128, 32, 32)
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(True),
            # (128, 32, 32) → (64, 64, 64)
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(True),
            # (64, 64, 64) → (3, 128, 128)
            nn.ConvTranspose2d(64, channels, kernel_size=4, stride=2, padding=1, bias=False),
            nn.Tanh(),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, (nn.ConvTranspose2d, nn.Linear)):
                nn.init.normal_(m.weight, 0.0, 0.02)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.normal_(m.weight, 1.0, 0.02)
                nn.init.constant_(m.bias, 0)

    def forward(self, noise: torch.Tensor, labels: torch.Tensor):
        """Forward pass.

        Args:
            noise: (batch, latent_dim) random noise.
            labels: (batch,) class indices.
        Returns:
            Tensor of shape (batch, 3, 128, 128).
        """
        # Label conditioning
        label_feat = self.label_embed(labels)              # (B, latent_dim)

        # Noise + label projections → feature maps
        noise_map = self.noise_proj(noise).view(-1, 512, 4, 4)   # (B, 512, 4, 4)
        label_map = self.label_proj(label_feat).view(-1, 512, 4, 4)

        # Concatenate on channel dim → (B, 1024, 4, 4)
        combined = torch.cat([noise_map, label_map], dim=1)

        return self.main(combined)


class cDCGANDiscriminator(nn.Module):
    """Conditional DCGAN Discriminator.

    Input:  RGB image (3, 128, 128) + class label
    Output: probability that the image is real.
    """

    def __init__(self, num_classes: int = 7, channels: int = 3):
        super().__init__()
        self.num_classes = num_classes

        # Label embedding → projected to final feature map
        self.label_embed = nn.Sequential(
            nn.Embedding(num_classes, 128),
            nn.Linear(128, 128),
            nn.LeakyReLU(0.2),
        )

        # Downsampling conv net (no BN in first layer per DCGAN paper)
        self.main = nn.Sequential(
            # (3, 128, 128) → (64, 64, 64)
            nn.Conv2d(channels, 64, kernel_size=4, stride=2, padding=1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            # (64, 64, 64) → (128, 32, 32)
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=True),
            # (128, 32, 32) → (256, 16, 16)
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, inplace=True),
            # (256, 16, 16) → (512, 8, 8)
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, inplace=True),
            # (512, 8, 8) → (1024, 4, 4)
            nn.Conv2d(512, 1024, kernel_size=4, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(1024),
            nn.LeakyReLU(0.2, inplace=True),
        )

        # Classifier: (1024*4*4 + 128) → 1
        self.classifier = nn.Sequential(
            nn.Linear(1024 * 4 * 4 + 128, 1),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                nn.init.normal_(m.weight, 0.0, 0.02)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.normal_(m.weight, 1.0, 0.02)
                nn.init.constant_(m.bias, 0)

    def forward(self, img: torch.Tensor, labels: torch.Tensor):
        """Forward pass.

        Args:
            img: (batch, 3, 128, 128) image tensor.
            labels: (batch,) class indices.
        Returns:
            Tensor of shape (batch, 1).
        """
        # Image features
        features = self.main(img)                           # (B, 1024, 4, 4)
        features = features.view(features.size(0), -1)      # (B, 1024*4*4)

        # Label conditioning
        label_feat = self.label_embed(labels)               # (B, 128)

        # Concatenate and classify
        combined = torch.cat([features, label_feat], dim=1) # (B, 1024*4*4 + 128)
        return self.classifier(combined)

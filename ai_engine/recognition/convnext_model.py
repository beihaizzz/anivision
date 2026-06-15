"""ConvNeXt-Tiny + ArcFace Head for anime character recognition.

Architecture:
    Input: RGB 224×224×3
    → ConvNeXt-Tiny Backbone (pretrained, Stage 0-2 frozen)
    → Global Avg Pooling → 768-dim
    → ArcFace Head:
        Linear(768→512) → BN → ReLU → L2 Norm
        × Normalized Weight (14, 512)
        → ArcFace cos(θ + m) * s → 14-dim logits

Reference:
    ConvNeXt: A ConvNet for the 2020s (Liu et al., 2022)
    ArcFace: Additive Angular Margin Loss (Deng et al., 2019)
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import convnext_tiny


class ArcFaceHead(nn.Module):
    """ArcFace classification head with additive angular margin.

    Args:
        in_features: Backbone output dimension (768 for ConvNeXt-Tiny).
        num_classes: Number of character classes.
        s: Feature scale (default 30.0).
        m: Angular margin in radians (default 0.5).
        embedding_dim: Dimension of intermediate embedding (default 512).
    """

    def __init__(
        self,
        in_features: int = 768,
        num_classes: int = 14,
        s: float = 30.0,
        m: float = 0.5,
        embedding_dim: int = 512,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.s = s
        self.m = m
        self.cos_m = torch.cos(torch.tensor(m))
        self.sin_m = torch.sin(torch.tensor(m))
        self.threshold = torch.cos(torch.tensor(torch.pi) - torch.tensor(m))
        self.mm = torch.sin(torch.tensor(torch.pi) - torch.tensor(m)) * m

        # Embedding network
        self.embedding = nn.Sequential(
            nn.Linear(in_features, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
            nn.ReLU(inplace=True),
        )

        # ArcFace weight (no bias)
        self.weight = nn.Parameter(torch.FloatTensor(num_classes, embedding_dim))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, features: torch.Tensor, labels: torch.Tensor = None):
        """Forward with optional ArcFace loss-compatible logits.

        Args:
            features: (B, in_features) from backbone.
            labels: (B,) class indices. If provided, applies ArcFace margin.
                    If None, returns plain cosine logits (for inference).

        Returns:
            logits: (B, num_classes) classification scores.
        """
        # Embed and normalize
        emb = self.embedding(features)           # (B, 512)
        emb = F.normalize(emb, p=2, dim=1)       # L2 norm
        W = F.normalize(self.weight, p=2, dim=1) # (num_classes, 512)

        # Cosine similarity
        cos_theta = F.linear(emb, W)             # (B, num_classes)

        if labels is None:
            # Inference: plain cosine logits scaled by s
            return cos_theta * self.s

        # ArcFace margin (training only)
        cos_theta = cos_theta.clamp(-1.0, 1.0)
        one_hot = F.one_hot(labels, num_classes=self.num_classes).float()

        # cos(θ + m) = cosθ * cos_m - sinθ * sin_m
        sin_theta = torch.sqrt(1.0 - cos_theta ** 2)
        cos_theta_m = cos_theta * self.cos_m - sin_theta * self.sin_m

        # Apply margin only to the correct class
        arcface_logits = one_hot * cos_theta_m + (1.0 - one_hot) * cos_theta

        return arcface_logits * self.s

    def get_embedding(self, features: torch.Tensor):
        """Return normalized embedding vector (for feature matching)."""
        emb = self.embedding(features)
        return F.normalize(emb, p=2, dim=1)


class ConvNeXtRecognitionModel(nn.Module):
    """ConvNeXt-Tiny backbone + ArcFace head.

    Args:
        num_classes: Number of character classes.
        pretrained: Use ImageNet-1K pretrained weights.
        freeze_stages: Which stages to freeze (default: [0, 1, 2]).
        arcface_s: ArcFace feature scale.
        arcface_m: ArcFace angular margin.
    """

    def __init__(
        self,
        num_classes: int = 14,
        pretrained: bool = True,
        freeze_stages: list = None,
        arcface_s: float = 30.0,
        arcface_m: float = 0.5,
    ):
        super().__init__()
        if freeze_stages is None:
            freeze_stages = [0, 1, 2]

        # Backbone
        weights = "IMAGENET1K_V1" if pretrained else None
        self.backbone = convnext_tiny(weights=weights)

        # Replace classifier with Identity
        self.backbone.classifier = nn.Identity()
        self.backbone.head = nn.Identity()  # older versions use .head

        # Feature dimension
        in_features = 768  # ConvNeXt-Tiny output

        # ArcFace head
        self.head = ArcFaceHead(
            in_features=in_features,
            num_classes=num_classes,
            s=arcface_s,
            m=arcface_m,
        )

        # Freeze strategy
        self._apply_freeze(freeze_stages)

    def _apply_freeze(self, freeze_stages: list):
        """Freeze selected stages by their index in backbone.features.

        ConvNeXt-Tiny feature indices:
            features[0]  = Stem (first patchify conv + LN)
            features[1]  = Stage 1 (dim=96)
            features[2]  = Downsample to Stage 2
            features[3]  = Stage 2 (dim=192)
            features[4]  = Downsample to Stage 3
            features[5]  = Stage 3 (dim=384)
            features[6]  = Downsample to Stage 4
            features[7]  = Stage 4 (dim=768)
        """
        # Map stage indices to actual feature sequence indices
        stage_to_idx = {
            0: [0],         # Stem
            1: [1],         # Stage 1
            2: [2, 3],      # Downsample + Stage 2
            3: [4, 5],      # Downsample + Stage 3
            4: [6, 7],      # Downsample + Stage 4
        }

        for stage in freeze_stages:
            if stage in stage_to_idx:
                for idx in stage_to_idx[stage]:
                    if idx < len(self.backbone.features):
                        for param in self.backbone.features[idx].parameters():
                            param.requires_grad = False

    def forward(self, x: torch.Tensor, labels: torch.Tensor = None):
        """Forward pass.

        Args:
            x: (B, 3, 224, 224) input images.
            labels: (B,) class indices for ArcFace margin during training.

        Returns:
            logits: (B, num_classes).
        """
        features = self.backbone(x)   # (B, 768, 1, 1)
        features = features.view(features.size(0), -1)  # (B, 768)
        return self.head(features, labels)

    def get_embedding(self, x: torch.Tensor):
        """Extract normalized embedding vector for inference."""
        features = self.backbone(x)
        features = features.view(features.size(0), -1)
        return self.head.get_embedding(features)

    def get_trainable_params(self):
        """Return summary of trainable vs total parameters."""
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.parameters())
        return {"trainable": trainable, "total": total, "frozen": total - trainable}

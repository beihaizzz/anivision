"""EfficientNet-B3 based anime character recognition model.

Architecture:
    Input: RGB 300x300x3
    → EfficientNet-B3 Backbone (pretrained, partially frozen)
    → Dropout(p=0.3)
    → Linear(1536, num_classes)
    → Softmax

Freeze strategy: freeze stem + blocks[0:5], train blocks[5:]+head.
"""
import torch.nn as nn
from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights


class AnimeRecognitionModel(nn.Module):
    """EfficientNet-B3 based anime character recognition model.

    Args:
        num_classes: Number of character classes.
        pretrained: Use ImageNet pretrained weights.
    """

    def __init__(self, num_classes: int = 7, pretrained: bool = True):
        super().__init__()

        weights = EfficientNet_B3_Weights.IMAGENET1K_V1 if pretrained else None
        self.backbone = efficientnet_b3(weights=weights)

        # Freeze stem + early MBConv blocks (blocks 0-4)
        # features[0] = stem, features[1]-features[7] = MBConv blocks
        # Freeze: features[0] through features[5] → stem + blocks 0-4
        for i in range(6):
            for param in self.backbone.features[i].parameters():
                param.requires_grad = False

        # Replace classifier head
        in_features = self.backbone.classifier[1].in_features  # 1536 for B3
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, num_classes),
        )

    def forward(self, x):
        return self.backbone(x)

    def get_trainable_params(self):
        """Return summary of trainable vs total parameters."""
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.parameters())
        return {"trainable": trainable, "total": total, "frozen": total - trainable}

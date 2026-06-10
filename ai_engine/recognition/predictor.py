"""Recognition predictor — loads model checkpoint and runs inference.

Loads the trained EfficientNet-B3 model, applies the same preprocessing
pipeline as training, and returns Top-K predictions with confidence scores.

Usage:
    predictor = RecognitionPredictor(model_path, label_map_path)
    result = predictor.predict("path/to/image.png", top_k=5)
"""
import json
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from .model import AnimeRecognitionModel

# ── Constants ──────────────────────────────────────────────────────────
INPUT_SIZE = 300
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def _build_transform():
    """Build inference transform (same as validation / preprocessing)."""
    return transforms.Compose(
        [
            transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=MEAN, std=STD),
        ]
    )


class RecognitionPredictor:
    """Singleton predictor for anime character recognition.

    Args:
        model_path: Path to trained .pth checkpoint.
        label_map_path: Path to label_map.json or class_names.json.
    """

    _instance = None

    def __init__(self, model_path: str = None, label_map_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.label_map: dict = {}
        self.transform = _build_transform()

        if model_path and label_map_path:
            self._load_model(model_path)
            self._load_label_map(label_map_path)

    # ── Singleton ──────────────────────────────────────────────────
    @classmethod
    def get_instance(cls, model_path: str = None, label_map_path: str = None):
        if cls._instance is None:
            cls._instance = cls(model_path, label_map_path)
        return cls._instance

    # ── Loading ────────────────────────────────────────────────────
    def _load_model(self, model_path: str):
        """Load model weights from checkpoint."""
        ckpt = torch.load(model_path, map_location=self.device, weights_only=True)

        # Detect number of classes from checkpoint classifier weight shape
        classifier_weight = ckpt["backbone.classifier.1.weight"]
        num_classes = classifier_weight.shape[0]

        self.model = AnimeRecognitionModel(num_classes=num_classes, pretrained=False)
        self.model.load_state_dict(ckpt)
        self.model.to(self.device)
        self.model.eval()

    def _load_label_map(self, label_map_path: str):
        """Load label mapping from JSON."""
        with open(label_map_path, "r", encoding="utf-8") as f:
            self.label_map = json.load(f)
        # Normalize keys to int
        self.label_map = {int(k): v for k, v in self.label_map.items()}

    # ── Inference ──────────────────────────────────────────────────
    def predict(self, image_path: str, top_k: int = 5) -> dict:
        """Run recognition on a single image.

        Args:
            image_path: Path to the input image file (PNG/JPG/...).
            top_k: Return top-K predictions.

        Returns:
            dict with keys:
                predictions: list of {rank, character_id, character_name, confidence}
                inference_time_ms: float, inference time in milliseconds
        """
        if self.model is None:
            # Fallback: no model loaded, return mock-like empty result
            return {
                "predictions": [],
                "inference_time_ms": 0,
                "error": "Model not loaded. Train the model first and provide a checkpoint path.",
            }

        # 1. Load & preprocess
        image = Image.open(image_path).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        # 2. Inference
        t_start = time.time()
        with torch.no_grad():
            logits = self.model(tensor)
            probs = F.softmax(logits, dim=1)
        inference_time = round((time.time() - t_start) * 1000, 2)

        # 3. Top-K
        topk_probs, topk_indices = torch.topk(probs, min(top_k, probs.size(1)))
        topk_probs = topk_probs.cpu().numpy()[0]
        topk_indices = topk_indices.cpu().numpy()[0]

        # 4. Build results
        predictions = []
        for rank, (idx, conf) in enumerate(zip(topk_indices, topk_probs), start=1):
            char_name = self.label_map.get(int(idx), f"class_{idx}")
            predictions.append(
                {
                    "rank": rank,
                    "character_id": int(idx),
                    "character_name": char_name,
                    "confidence": round(float(conf), 4),
                }
            )

        return {"predictions": predictions, "inference_time_ms": inference_time}

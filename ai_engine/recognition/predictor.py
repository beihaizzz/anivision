"""Recognition predictor - loads model and runs inference."""
import torch


class RecognitionPredictor:
    """Singleton predictor for anime character recognition."""

    _instance = None

    def __init__(self, model_path=None, label_map_path=None):
        self.model = None
        self.label_map = {}
        self.device = "cpu"

    @classmethod
    def get_instance(cls, model_path=None, label_map_path=None):
        if cls._instance is None:
            cls._instance = cls(model_path, label_map_path)
        return cls._instance

    def predict(self, image_path, top_k=5):
        """Returns mock prediction results for Phase 1."""
        # Phase 1: return mock data
        # Phase 2: actual model inference
        return [
            {"character_id": 1, "character_name": "灶门炭治郎", "confidence": 0.85},
            {"character_id": 2, "character_name": "灶门祢豆子", "confidence": 0.08},
            {"character_id": 3, "character_name": "我妻善逸", "confidence": 0.04},
            {"character_id": 4, "character_name": "嘴平伊之助", "confidence": 0.02},
            {"character_id": 5, "character_name": "富冈义勇", "confidence": 0.01},
        ]
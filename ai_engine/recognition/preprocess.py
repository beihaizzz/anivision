"""Image preprocessing utilities."""
from PIL import Image
import torchvision.transforms as transforms


def preprocess_image(image_path, input_size=(300, 300)):
    """Load, resize, and normalize an image for model input.

    Args:
        image_path: Path to the input image file.
        input_size: Tuple of (width, height) for resizing.

    Returns:
        torch.Tensor: Preprocessed image tensor ready for model input.
    """
    transform = transforms.Compose([
        transforms.Resize(input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    image = Image.open(image_path).convert("RGB")
    return transform(image)
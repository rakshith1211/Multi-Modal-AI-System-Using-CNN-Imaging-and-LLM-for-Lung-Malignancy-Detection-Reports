import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np

# FIX 5: cv2 is an optional dependency — import lazily inside the method
# that needs it so a missing opencv install does NOT crash the entire module.


class ImagePreprocessor:
    """Handles image loading and preprocessing for inference."""

    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size
        # Inference transform: resize → tensor → ImageNet normalisation
        self.transform = transforms.Compose([
            transforms.Resize(target_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    def preprocess_image(self, image_path):
        """Load and preprocess a single image for model inference."""
        image = Image.open(image_path).convert('RGB')
        return self.transform(image).unsqueeze(0)   # shape: [1, 3, H, W]

    def denoise_image(self, image):
        """
        Apply bilateral filter noise reduction.
        FIX 5: cv2 imported lazily — module still loads if opencv is absent.
        """
        try:
            import cv2
        except ImportError:
            raise ImportError(
                "opencv-python is required for denoise_image(). "
                "Install it with: pip install opencv-python"
            )
        if isinstance(image, Image.Image):
            image = np.array(image)
        return cv2.bilateralFilter(image, 9, 75, 75)


class DatasetExpander:
    """Provides augmentation transforms for training and clean transforms for validation."""

    def get_training_transforms(self):
        """
        FIX 6: All spatial/colour augmentations are applied BEFORE ToTensor()
        so they operate on PIL images as torchvision expects.
        RandomErasing (tensor-only op) stays after ToTensor + Normalize.
        """
        return transforms.Compose([
            transforms.Resize((224, 224)),
            # --- PIL-based augmentations (must come before ToTensor) ---
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
            # --- Tensor conversion + normalisation ---
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
            # --- Tensor-only augmentation (must come after ToTensor) ---
            transforms.RandomErasing(p=0.3, scale=(0.02, 0.33), ratio=(0.3, 3.3)),
        ])

    def get_validation_transforms(self):
        """Clean deterministic transforms for validation and test sets."""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
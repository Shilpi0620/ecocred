# ═══════════════════════════════════════════════════════════
# EcoCred ML Service — Model Architecture & Inference
# File: ml_service/model.py
#
# Handles:
#   - Model architecture (ResNet50 fine-tuned)
#   - Loading trained weights
#   - Single image inference
#   - Confidence thresholding
#   - Edge case handling (blurry, dark, non-waste images)
#   - Test-time augmentation (TTA) for higher accuracy
# ═══════════════════════════════════════════════════════════

import io
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image, ImageStat
import numpy as np

from dataset import (
    LABELS, NUM_CLASSES, LABEL_TO_SLUG,
    get_inference_transforms, IMG_SIZE
)


# ── Model path ─────────────────────────────────────────────
MODEL_PATH = Path(__file__).parent / "ecocred_model.pth"

# Confidence threshold — below this → manual review
AUTO_APPROVE_THRESHOLD = 0.85

# Minimum image quality thresholds
MIN_BRIGHTNESS = 20     # 0-255, too dark = unreliable
MAX_BRIGHTNESS = 235    # too washed out / overexposed
MIN_CONTRAST   = 10     # std dev of pixel values


# ── Model Architecture ────────────────────────────────────

def build_model(num_classes: int = NUM_CLASSES, pretrained: bool = False) -> nn.Module:
    """
    ResNet50 with custom classifier head.
    
    Architecture:
        ResNet50 backbone (pretrained on ImageNet)
            ↓
        Global Average Pooling (2048 features)
            ↓
        Dropout(0.5)         ← prevents overfitting
            ↓
        Linear(2048 → 512)
            ↓
        ReLU + Dropout(0.3)
            ↓
        Linear(512 → num_classes)
            ↓
        Softmax (during inference)
    
    We freeze early layers and only train:
        - Layer3, Layer4 (deeper features)
        - Custom classifier head
    This is called "fine-tuning" — we keep ImageNet's
    low-level feature detection but teach it waste-specific patterns.
    """
    # Load ResNet50 backbone
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1 if pretrained else None)

    # Freeze early layers (they learn basic edges/textures from ImageNet)
    # We only want to retrain layers that learn higher-level features
    for name, param in model.named_parameters():
        if "layer1" in name or "layer2" in name:
            param.requires_grad = False

    # Replace the final FC layer with our custom head
    in_features = model.fc.in_features  # 2048 for ResNet50
    model.fc = nn.Sequential(
        nn.Dropout(p=0.5),
        nn.Linear(in_features, 512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.3),
        nn.Linear(512, num_classes)
    )

    return model


def load_model(model_path: str = None, device: str = None) -> nn.Module:
    """
    Load trained model from .pth file.
    
    Args:
        model_path: path to .pth file (defaults to MODEL_PATH)
        device: 'cuda', 'mps', or 'cpu' (auto-detected if None)
    
    Returns:
        Loaded model in eval mode
    """
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"   # Apple Silicon
        else:
            device = "cpu"

    path = Path(model_path) if model_path else MODEL_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found: {path}\n"
            f"Run training first: python train.py"
        )

    print(f"  📦 Loading model from {path} on {device}...")

    model = build_model(num_classes=NUM_CLASSES, pretrained=False)
    checkpoint = torch.load(str(path), map_location=device)

    # Handle both raw state_dict and full checkpoint
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        print(f"  ✓ Loaded checkpoint (epoch {checkpoint.get('epoch', '?')}, "
              f"val_acc={checkpoint.get('val_acc', '?'):.2%})")
    else:
        model.load_state_dict(checkpoint)

    model = model.to(device)
    model.eval()  # disable dropout for inference

    return model, device


# ── Image Quality Checks ───────────────────────────────────

def check_image_quality(image: Image.Image) -> tuple[bool, str]:
    """
    Basic quality checks before running ML.
    Returns (is_acceptable, reason_if_not).
    
    Catches:
    - Images that are too dark (taken in bad lighting)
    - Images that are too bright / washed out
    - Images with very low contrast (blank/featureless)
    - Images that are too small
    """
    # Size check
    w, h = image.size
    if w < 64 or h < 64:
        return False, "Image too small (minimum 64x64 pixels)"

    # Convert to grayscale for brightness/contrast analysis
    gray = image.convert("L")
    stat = ImageStat.Stat(gray)

    mean_brightness = stat.mean[0]
    contrast = stat.stddev[0]

    if mean_brightness < MIN_BRIGHTNESS:
        return False, f"Image too dark (brightness={mean_brightness:.0f})"

    if mean_brightness > MAX_BRIGHTNESS:
        return False, f"Image overexposed (brightness={mean_brightness:.0f})"

    if contrast < MIN_CONTRAST:
        return False, f"Image has too low contrast (std={contrast:.0f}) — may be blank or uniform"

    return True, "ok"


def preprocess_image(image_bytes: bytes) -> tuple[Image.Image, torch.Tensor]:
    """
    Convert raw image bytes → PIL Image + tensor ready for model.
    
    Args:
        image_bytes: raw bytes from file upload or URL download
    
    Returns:
        (pil_image, tensor) where tensor shape is [1, 3, 224, 224]
    """
    # Load PIL image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Apply inference transforms
    transform = get_inference_transforms()
    tensor = transform(image).unsqueeze(0)  # add batch dimension

    return image, tensor


# ── Test-Time Augmentation (TTA) ───────────────────────────

def predict_with_tta(model: nn.Module, image: Image.Image, device: str, n_augments: int = 5) -> np.ndarray:
    """
    Test-Time Augmentation: run the same image through the model
    multiple times with slight variations, then average predictions.
    
    This improves accuracy by ~2-4% at the cost of more compute.
    Used when single-pass confidence is borderline (0.75 - 0.90).
    
    Args:
        model: loaded PyTorch model
        image: PIL Image
        device: 'cuda' or 'cpu'
        n_augments: how many augmented versions to average
    
    Returns:
        averaged probability array of shape [num_classes]
    """
    tta_transforms = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(IMG_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])

    all_probs = []
    with torch.no_grad():
        for _ in range(n_augments):
            tensor = tta_transforms(image).unsqueeze(0).to(device)
            logits = model(tensor)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
            all_probs.append(probs)

    return np.mean(all_probs, axis=0)


# ── Main Inference Function ────────────────────────────────

def classify_waste(
    image_bytes: bytes,
    model: nn.Module = None,
    device: str = None,
    use_tta: bool = True
) -> dict:
    """
    Full inference pipeline for a single waste image.
    
    Args:
        image_bytes: raw image bytes (from upload or URL)
        model: pre-loaded model (if None, loads from disk)
        device: compute device
        use_tta: use test-time augmentation for borderline cases
    
    Returns dict:
        {
            "label": "plastic",          # predicted class
            "slug": "plastic",           # EcoCred material slug
            "confidence": 0.94,          # confidence 0-1
            "all_predictions": {...},    # all class probabilities
            "auto_approve": True,        # confidence >= threshold
            "quality_ok": True,          # image passed quality check
            "quality_note": "ok",        # quality check message
            "processing_time_ms": 142,   # inference time
            "used_tta": False,           # whether TTA was used
        }
    """
    start_time = time.time()

    # ── Load model if not provided ──
    if model is None:
        model, device = load_model()
    if device is None:
        device = next(model.parameters()).device

    # ── Load and quality-check image ──
    try:
        pil_image, tensor = preprocess_image(image_bytes)
    except Exception as e:
        return {
            "label": None,
            "slug": None,
            "confidence": 0.0,
            "all_predictions": {},
            "auto_approve": False,
            "quality_ok": False,
            "quality_note": f"Failed to load image: {str(e)}",
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "used_tta": False,
        }

    quality_ok, quality_note = check_image_quality(pil_image)

    # ── Single-pass inference ──
    tensor = tensor.to(device)
    used_tta = False

    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1).cpu().numpy()[0]

    top_confidence = float(probs.max())
    top_idx = int(probs.argmax())

    # ── Use TTA if confidence is borderline ──
    # (between 65% and 90% — worth spending extra compute)
    if use_tta and 0.65 <= top_confidence < 0.90:
        probs = predict_with_tta(model, pil_image, device, n_augments=6)
        top_confidence = float(probs.max())
        top_idx = int(probs.argmax())
        used_tta = True

    label = LABELS[top_idx]
    slug = LABEL_TO_SLUG.get(label)

    # Build full predictions dict (sorted by confidence)
    all_preds = {
        LABELS[i]: round(float(probs[i]), 4)
        for i in range(len(LABELS))
    }
    all_preds = dict(sorted(all_preds.items(), key=lambda x: x[1], reverse=True))

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "label": label,
        "slug": slug,
        "confidence": round(top_confidence, 4),
        "all_predictions": all_preds,
        "auto_approve": top_confidence >= AUTO_APPROVE_THRESHOLD and quality_ok,
        "quality_ok": quality_ok,
        "quality_note": quality_note,
        "processing_time_ms": elapsed_ms,
        "used_tta": used_tta,
    }


# ── Singleton model loader ─────────────────────────────────
# Load model once at startup rather than on every request

_model = None
_device = None

def get_loaded_model():
    """
    Returns the globally loaded model.
    Call this at FastAPI startup.
    """
    global _model, _device
    if _model is None:
        _model, _device = load_model()
    return _model, _device


# ── Quick test ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import requests

    if len(sys.argv) > 1:
        # Test with a local image file
        img_path = sys.argv[1]
        with open(img_path, "rb") as f:
            img_bytes = f.read()
    else:
        # Download a test image
        print("Downloading test image...")
        r = requests.get("https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Plastic_bottle.jpg/320px-Plastic_bottle.jpg")
        img_bytes = r.content

    print("\n🔍 Running inference...\n")
    result = classify_waste(img_bytes)

    print(f"  Prediction:      {result['label']} ({result['slug']})")
    print(f"  Confidence:      {result['confidence']:.1%}")
    print(f"  Auto-approve:    {result['auto_approve']}")
    print(f"  Quality OK:      {result['quality_ok']} — {result['quality_note']}")
    print(f"  Used TTA:        {result['used_tta']}")
    print(f"  Processing time: {result['processing_time_ms']}ms")
    print(f"\n  All predictions:")
    for label, prob in result["all_predictions"].items():
        bar = "█" * int(prob * 30)
        print(f"    {label:<12} {prob:.3f}  {bar}")
import os
import shutil
import random
from pathlib import Path
from collections import Counter

import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np


# ── Label mapping ──────────────────────────────────────────
# Must match your folder names exactly
LABELS = [
    "cardboard",   # maps to 'paper' in EcoCred
    "ewaste",      # maps to 'ewaste'
    "glass",       # maps to 'glass'
    "metal",       # maps to 'metal'
    "organic",     # maps to 'organic'
    "paper",       # maps to 'paper' (combined with cardboard)
    "plastic",     # maps to 'plastic'
    "trash",       # generic trash / unknown
]

NUM_CLASSES = len(LABELS)

# Map ML labels → EcoCred material slugs
LABEL_TO_SLUG = {
    "cardboard": "paper",
    "ewaste":    "ewaste",
    "glass":     "glass",
    "metal":     "metal",
    "organic":   "organic",
    "paper":     "paper",
    "plastic":   "plastic",
    "trash":     None,  # no reward for unclassified trash
}

# Image size ResNet expects
IMG_SIZE = 224


# ── Transforms ────────────────────────────────────────────

def get_train_transforms():
    """
    Aggressive augmentation for training.
    Makes model robust to:
    - Different lighting (phones, outdoor, indoor)
    - Different angles (upright, sideways, tilted)
    - Different distances (close-up vs wide shot)
    - Dirt, shadows, partial occlusion
    """
    return transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(IMG_SIZE),                      # random crop instead of center
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(degrees=30),                # waste can be at any angle
        transforms.ColorJitter(
            brightness=0.4,   # lighting varies a lot on phone cameras
            contrast=0.4,
            saturation=0.3,
            hue=0.1
        ),
        transforms.RandomGrayscale(p=0.05),                   # occasional grayscale
        transforms.RandomPerspective(distortion_scale=0.2, p=0.3),  # angle distortion
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],   # ImageNet mean
            std=[0.229, 0.224, 0.225]     # ImageNet std
        ),
        transforms.RandomErasing(p=0.1, scale=(0.02, 0.1)),  # simulate partial occlusion
    ])


def get_val_transforms():
    """
    Minimal transforms for validation/test.
    Only resize and normalize — no augmentation.
    """
    return transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])


def get_inference_transforms():
    """
    For inference on a single uploaded image.
    Same as val but returns a batch tensor.
    """
    return transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])


# ── Dataset Class ─────────────────────────────────────────

class WasteDataset(Dataset):
    """
    Expects folder structure:
    
    data/
    ├── train/
    │   ├── plastic/
    │   │   ├── img001.jpg
    │   │   ├── img002.jpg
    │   │   └── ...
    │   ├── metal/
    │   ├── glass/
    │   └── ...
    ├── val/
    │   ├── plastic/
    │   └── ...
    └── test/
        ├── plastic/
        └── ...
    """

    def __init__(self, root_dir: str, split: str = "train", transform=None):
        """
        Args:
            root_dir: path to data/ folder
            split: "train", "val", or "test"
            transform: torchvision transforms to apply
        """
        self.root = Path(root_dir) / split
        self.transform = transform
        self.samples = []   # list of (image_path, label_index)
        self.labels = LABELS

        if not self.root.exists():
            raise FileNotFoundError(f"Dataset split '{split}' not found at {self.root}")

        # Walk through each class folder
        for label_idx, label_name in enumerate(self.labels):
            class_dir = self.root / label_name
            if not class_dir.exists():
                print(f"  ⚠️  Warning: class folder '{label_name}' not found, skipping.")
                continue

            images = [
                f for f in class_dir.iterdir()
                if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            ]
            for img_path in images:
                self.samples.append((str(img_path), label_idx))

        if len(self.samples) == 0:
            raise ValueError(f"No images found in {self.root}")

        print(f"  ✓ {split}: {len(self.samples)} images across {len(self.labels)} classes")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]

        # Load image — handle corrupt files gracefully
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"  ⚠️  Skipping corrupt image {img_path}: {e}")
            # Return a black image as fallback
            image = Image.new("RGB", (IMG_SIZE, IMG_SIZE), (0, 0, 0))

        if self.transform:
            image = self.transform(image)

        return image, label

    def get_class_counts(self) -> dict:
        """Return count of samples per class."""
        counts = Counter(label for _, label in self.samples)
        return {self.labels[i]: counts[i] for i in range(len(self.labels))}

    def get_sample_weights(self) -> list:
        """
        Returns per-sample weights for WeightedRandomSampler.
        Classes with fewer samples get higher weight → balances training.
        """
        counts = Counter(label for _, label in self.samples)
        # Weight = inverse of class frequency
        class_weights = {
            label: 1.0 / count
            for label, count in counts.items()
        }
        return [class_weights[label] for _, label in self.samples]


# ── DataLoader Factory ─────────────────────────────────────

def get_dataloaders(
    data_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    balance_classes: bool = True
) -> dict:
    """
    Creates train, val, test DataLoaders.
    
    Args:
        data_dir: path to data/ folder
        batch_size: images per batch
        num_workers: parallel data loading workers
        balance_classes: use weighted sampling to handle imbalanced data
    
    Returns:
        dict with keys: "train", "val", "test"
    """
    print("\n📂 Loading datasets...")

    datasets = {
        "train": WasteDataset(data_dir, "train", get_train_transforms()),
        "val":   WasteDataset(data_dir, "val",   get_val_transforms()),
        "test":  WasteDataset(data_dir, "test",  get_val_transforms()),
    }

    # Print class distribution
    print("\n📊 Class distribution (train):")
    for cls, count in datasets["train"].get_class_counts().items():
        bar = "█" * (count // 10)
        print(f"  {cls:<12} {count:>4} samples  {bar}")

    # Weighted sampler for imbalanced classes
    train_sampler = None
    if balance_classes:
        weights = datasets["train"].get_sample_weights()
        train_sampler = WeightedRandomSampler(
            weights=weights,
            num_samples=len(weights),
            replacement=True
        )
        print("\n⚖️  Using weighted sampling to balance classes.")

    loaders = {
        "train": DataLoader(
            datasets["train"],
            batch_size=batch_size,
            sampler=train_sampler,
            shuffle=(train_sampler is None),
            num_workers=num_workers,
            pin_memory=True
        ),
        "val": DataLoader(
            datasets["val"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True
        ),
        "test": DataLoader(
            datasets["test"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True
        ),
    }

    print(f"\n✅ DataLoaders ready:")
    for split, loader in loaders.items():
        print(f"  {split:<6}: {len(loader.dataset)} samples, {len(loader)} batches")

    return loaders, datasets


# ── Dataset Preparation Helper ─────────────────────────────

def prepare_dataset_from_raw(
    raw_dir: str,
    output_dir: str,
    train_pct: float = 0.70,
    val_pct: float = 0.15,
    test_pct: float = 0.15,
    seed: int = 42
):
    """
    Splits a flat dataset into train/val/test folders.
    
    Use this if you downloaded a dataset like TrashNet which
    has structure:
        raw_data/
        ├── plastic/  (all images together)
        ├── metal/
        └── ...
    
    This will reorganize it to:
        data/
        ├── train/
        │   ├── plastic/
        │   └── ...
        ├── val/
        │   ├── plastic/
        │   └── ...
        └── test/
            ├── plastic/
            └── ...
    
    Args:
        raw_dir: folder with class subfolders
        output_dir: where to write train/val/test splits
        train_pct / val_pct / test_pct: split ratios (must sum to 1.0)
        seed: random seed for reproducibility
    """
    assert abs(train_pct + val_pct + test_pct - 1.0) < 1e-6, "Split percentages must sum to 1.0"

    random.seed(seed)
    raw_path = Path(raw_dir)
    out_path = Path(output_dir)

    print(f"\n📁 Preparing dataset from {raw_dir} → {output_dir}")
    print(f"   Split: {train_pct*100:.0f}% train / {val_pct*100:.0f}% val / {test_pct*100:.0f}% test\n")

    total_copied = 0

    for class_dir in sorted(raw_path.iterdir()):
        if not class_dir.is_dir():
            continue

        class_name = class_dir.name.lower().strip()
        images = [
            f for f in class_dir.iterdir()
            if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ]
        random.shuffle(images)

        n = len(images)
        n_train = int(n * train_pct)
        n_val   = int(n * val_pct)

        splits = {
            "train": images[:n_train],
            "val":   images[n_train:n_train + n_val],
            "test":  images[n_train + n_val:],
        }

        for split_name, split_images in splits.items():
            dest = out_path / split_name / class_name
            dest.mkdir(parents=True, exist_ok=True)
            for img in split_images:
                shutil.copy2(str(img), str(dest / img.name))
            total_copied += len(split_images)

        print(f"  {class_name:<12}: {n_train} train / {n_val} val / {n - n_train - n_val} test  ({n} total)")

    print(f"\n✅ Done. {total_copied} images copied to {output_dir}")


# ── Quick test ─────────────────────────────────────────────

if __name__ == "__main__":
    # Test: prepare dataset from raw TrashNet download
    # Download from: https://github.com/garythung/trashnet
    # Then run: python dataset.py

    import sys

    if len(sys.argv) == 3:
        raw_dir    = sys.argv[1]   # e.g. "dataset-resized150x150"
        output_dir = sys.argv[2]   # e.g. "data"
        prepare_dataset_from_raw(raw_dir, output_dir)
    else:
        # Just test loading if data/ already exists
        try:
            loaders, datasets = get_dataloaders("data", batch_size=4, num_workers=0)
            images, labels = next(iter(loaders["train"]))
            print(f"\n✅ Batch shape: {images.shape}")
            print(f"   Labels: {[LABELS[l] for l in labels.tolist()]}")
        except FileNotFoundError as e:
            print(f"\nUsage: python dataset.py <raw_dir> <output_dir>")
            print(f"  e.g: python dataset.py dataset-resized150x150 data")
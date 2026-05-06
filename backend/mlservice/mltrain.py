# ═══════════════════════════════════════════════════════════
# EcoCred ML Service — Training Script
# File: ml_service/train.py
#
# Handles:
#   - Full training loop with validation
#   - Learning rate scheduling
#   - Early stopping (stops if no improvement)
#   - Checkpoint saving (best model only)
#   - Training history logging
#   - Resuming from checkpoint
# ═══════════════════════════════════════════════════════════

import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import OneCycleLR, CosineAnnealingLR
from torchvision import models

from dataset import get_dataloaders, LABELS, NUM_CLASSES
from model import build_model


# ── Training Config ────────────────────────────────────────

DEFAULT_CONFIG = {
    "data_dir":        "data",             # path to train/val/test folders
    "model_path":      "ecocred_model.pth",# where to save best model
    "epochs":          50,                 # max epochs (early stopping may stop earlier)
    "batch_size":      32,
    "learning_rate":   1e-4,               # initial LR for fine-tuning (low because pretrained)
    "weight_decay":    1e-4,               # L2 regularization
    "num_workers":     4,                  # parallel data loading
    "patience":        8,                  # early stopping patience (epochs without improvement)
    "min_delta":       0.001,              # min improvement to count as improvement
    "balance_classes": True,               # weighted sampling for imbalanced data
    "use_amp":         True,               # automatic mixed precision (faster on GPU)
    "scheduler":       "cosine",           # 'cosine' or 'onecycle'
    "seed":            42,
}


# ── Early Stopping ─────────────────────────────────────────

class EarlyStopping:
    """
    Stops training if validation accuracy doesn't improve
    for `patience` consecutive epochs.
    """
    def __init__(self, patience: int = 8, min_delta: float = 0.001):
        self.patience   = patience
        self.min_delta  = min_delta
        self.best_score = None
        self.counter    = 0
        self.should_stop = False

    def __call__(self, val_acc: float) -> bool:
        score = val_acc
        if self.best_score is None:
            self.best_score = score
        elif score < self.best_score + self.min_delta:
            self.counter += 1
            print(f"  ⏳ EarlyStopping: {self.counter}/{self.patience} epochs without improvement")
            if self.counter >= self.patience:
                self.should_stop = True
        else:
            self.best_score = score
            self.counter    = 0
        return self.should_stop


# ── Training Loop ──────────────────────────────────────────

def train_one_epoch(
    model, loader, optimizer, criterion,
    device, scaler=None, epoch=0
) -> tuple[float, float]:
    """
    Train model for one epoch.
    Returns (average_loss, accuracy).
    """
    model.train()
    total_loss = 0.0
    correct    = 0
    total      = 0

    for batch_idx, (images, labels) in enumerate(loader):
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad()

        # Automatic Mixed Precision (fp16 on GPU for speed)
        if scaler is not None:
            with torch.cuda.amp.autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total   += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        # Progress every 20 batches
        if (batch_idx + 1) % 20 == 0:
            print(f"    Batch {batch_idx+1}/{len(loader)} — "
                  f"loss={total_loss/(batch_idx+1):.4f} "
                  f"acc={correct/total:.3f}")

    avg_loss = total_loss / len(loader)
    accuracy = correct / total
    return avg_loss, accuracy


@torch.no_grad()
def evaluate(model, loader, criterion, device) -> tuple[float, float]:
    """
    Evaluate model on val or test set.
    Returns (average_loss, accuracy).
    """
    model.eval()
    total_loss = 0.0
    correct    = 0
    total      = 0

    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        outputs = model(images)
        loss = criterion(outputs, labels)

        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total   += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return total_loss / len(loader), correct / total


# ── Main Training Function ─────────────────────────────────

def train(config: dict = None):
    """
    Full training pipeline.
    
    Steps:
    1. Set up device and seeds
    2. Load datasets
    3. Build model
    4. Set up optimizer, scheduler, loss
    5. Train with early stopping
    6. Save best model
    7. Evaluate on test set
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}

    # ── Setup ──
    torch.manual_seed(cfg["seed"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Device
    if torch.cuda.is_available():
        device = "cuda"
        print(f"🖥️  Using GPU: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = "mps"
        print(f"🖥️  Using Apple Silicon MPS")
    else:
        device = "cpu"
        print(f"🖥️  Using CPU (training will be slow)")

    # ── Load data ──
    loaders, datasets = get_dataloaders(
        data_dir       = cfg["data_dir"],
        batch_size     = cfg["batch_size"],
        num_workers    = cfg["num_workers"],
        balance_classes= cfg["balance_classes"]
    )

    # ── Build model ──
    print(f"\n🏗️  Building ResNet50 model ({NUM_CLASSES} classes)...")
    model = build_model(num_classes=NUM_CLASSES, pretrained=True)
    model = model.to(device)

    # Count trainable parameters
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    print(f"   Trainable params: {trainable:,} / {total:,} ({trainable/total:.1%})")

    # ── Loss function ──
    # LabelSmoothing reduces overconfidence on training data
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # ── Optimizer ──
    # Different learning rates for backbone vs classifier head
    backbone_params   = [p for n, p in model.named_parameters() if "fc" not in n and p.requires_grad]
    classifier_params = [p for n, p in model.named_parameters() if "fc" in n]

    optimizer = optim.AdamW([
        {"params": backbone_params,   "lr": cfg["learning_rate"] * 0.1},  # slower for pretrained
        {"params": classifier_params, "lr": cfg["learning_rate"]},         # faster for new head
    ], weight_decay=cfg["weight_decay"])

    # ── LR Scheduler ──
    steps_per_epoch = len(loaders["train"])
    if cfg["scheduler"] == "onecycle":
        scheduler = OneCycleLR(
            optimizer,
            max_lr=[cfg["learning_rate"] * 0.1, cfg["learning_rate"]],
            steps_per_epoch=steps_per_epoch,
            epochs=cfg["epochs"],
            pct_start=0.1
        )
    else:
        scheduler = CosineAnnealingLR(
            optimizer,
            T_max=cfg["epochs"],
            eta_min=1e-6
        )

    # ── AMP Scaler (GPU only) ──
    scaler = torch.cuda.amp.GradScaler() if (cfg["use_amp"] and device == "cuda") else None

    # ── Early stopping ──
    early_stopping = EarlyStopping(patience=cfg["patience"], min_delta=cfg["min_delta"])

    # ── Training history ──
    history = {
        "train_loss": [], "train_acc": [],
        "val_loss":   [], "val_acc":   [],
        "lr": []
    }

    best_val_acc  = 0.0
    best_epoch    = 0
    model_path    = cfg["model_path"]

    print(f"\n🚀 Starting training for up to {cfg['epochs']} epochs...\n")
    print("=" * 65)

    for epoch in range(1, cfg["epochs"] + 1):
        epoch_start = time.time()
        print(f"\nEpoch {epoch}/{cfg['epochs']}")

        # Train
        train_loss, train_acc = train_one_epoch(
            model, loaders["train"], optimizer, criterion,
            device, scaler, epoch
        )

        # Validate
        val_loss, val_acc = evaluate(model, loaders["val"], criterion, device)

        # Step scheduler
        if cfg["scheduler"] == "cosine":
            scheduler.step()
        # (onecycle steps inside train_one_epoch)

        current_lr = optimizer.param_groups[-1]["lr"]
        elapsed = time.time() - epoch_start

        # Log
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["lr"].append(current_lr)

        print(f"  Train: loss={train_loss:.4f} acc={train_acc:.3f}")
        print(f"  Val:   loss={val_loss:.4f}  acc={val_acc:.3f}  ← {'✅ BEST' if val_acc > best_val_acc else ''}")
        print(f"  LR={current_lr:.2e}  Time={elapsed:.1f}s")

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch   = epoch
            torch.save({
                "epoch":            epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state":  optimizer.state_dict(),
                "val_acc":          val_acc,
                "val_loss":         val_loss,
                "config":           cfg,
                "labels":           LABELS,
            }, model_path)
            print(f"  💾 Saved best model → {model_path}")

        # Early stopping check
        if early_stopping(val_acc):
            print(f"\n⛔ Early stopping at epoch {epoch}. Best was epoch {best_epoch}.")
            break

        print("-" * 65)

    # ── Save training history ──
    history_path = f"training_history_{timestamp}.json"
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\n📊 Training history saved to {history_path}")

    # ── Final evaluation on test set ──
    print(f"\n{'='*65}")
    print(f"📋 Final Evaluation on Test Set")
    print(f"   Loading best model from epoch {best_epoch} (val_acc={best_val_acc:.3f})")

    # Reload best model weights
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    test_loss, test_acc = evaluate(model, loaders["test"], criterion, device)
    print(f"\n   Test Loss: {test_loss:.4f}")
    print(f"   Test Accuracy: {test_acc:.4f} ({test_acc:.2%})")

    if test_acc >= 0.85:
        print(f"   ✅ Model meets 85% accuracy threshold for production")
    else:
        print(f"   ⚠️  Model below 85% threshold — consider more data or tuning")

    print(f"\n✅ Training complete. Model saved to: {model_path}")
    return history


# ── Entry Point ────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EcoCred waste classifier")
    parser.add_argument("--data_dir",     default="data",                help="Path to dataset")
    parser.add_argument("--model_path",   default="ecocred_model.pth",   help="Output model file")
    parser.add_argument("--epochs",       type=int,   default=50)
    parser.add_argument("--batch_size",   type=int,   default=32)
    parser.add_argument("--lr",           type=float, default=1e-4)
    parser.add_argument("--patience",     type=int,   default=8)
    parser.add_argument("--scheduler",    default="cosine", choices=["cosine", "onecycle"])
    parser.add_argument("--no_balance",   action="store_true", help="Disable class balancing")
    parser.add_argument("--no_amp",       action="store_true", help="Disable mixed precision")
    args = parser.parse_args()

    config = {
        "data_dir":        args.data_dir,
        "model_path":      args.model_path,
        "epochs":          args.epochs,
        "batch_size":      args.batch_size,
        "learning_rate":   args.lr,
        "patience":        args.patience,
        "scheduler":       args.scheduler,
        "balance_classes": not args.no_balance,
        "use_amp":         not args.no_amp,
    }

    print("\n🌿 EcoCred Waste Classifier — Training")
    print("=" * 65)
    print("Config:")
    for k, v in config.items():
        print(f"  {k:<20} {v}")
    print()

    train(config)
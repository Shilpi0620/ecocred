# ═══════════════════════════════════════════════════════════
# EcoCred ML Service — Model Evaluation
# File: ml_service/evaluate.py
#
# Handles:
#   - Overall accuracy on test set
#   - Per-class precision, recall, F1
#   - Confusion matrix
#   - Confidence distribution analysis
#   - Finding worst misclassifications
#   - Checking if model is production-ready
# ═══════════════════════════════════════════════════════════

import json
import argparse
from pathlib import Path
from collections import defaultdict

import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image

from dataset import get_dataloaders, LABELS, NUM_CLASSES
from model import load_model, AUTO_APPROVE_THRESHOLD


# ── Core Evaluation ────────────────────────────────────────

@torch.no_grad()
def evaluate_full(model, loader, device) -> dict:
    """
    Run model on entire dataset split.
    
    Returns dict with:
        - all true labels
        - all predicted labels  
        - all confidence scores
        - all probability arrays
    """
    model.eval()

    all_true      = []
    all_predicted = []
    all_confidences = []
    all_probs     = []

    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        logits = model(images)
        probs  = F.softmax(logits, dim=1).cpu().numpy()

        predicted   = probs.argmax(axis=1)
        confidences = probs.max(axis=1)

        all_true.extend(labels.numpy())
        all_predicted.extend(predicted)
        all_confidences.extend(confidences)
        all_probs.extend(probs)

    return {
        "true":        np.array(all_true),
        "predicted":   np.array(all_predicted),
        "confidences": np.array(all_confidences),
        "probs":       np.array(all_probs),
    }


# ── Metrics ────────────────────────────────────────────────

def compute_metrics(results: dict) -> dict:
    """
    Compute per-class and overall metrics from evaluation results.
    
    Metrics:
        - Accuracy: % of correct predictions overall
        - Precision: of all predictions for class X, how many were right
        - Recall: of all actual class X samples, how many did we catch
        - F1: harmonic mean of precision and recall
    """
    true      = results["true"]
    predicted = results["predicted"]

    overall_acc = (true == predicted).mean()

    per_class = {}
    for i, label in enumerate(LABELS):
        tp = ((predicted == i) & (true == i)).sum()
        fp = ((predicted == i) & (true != i)).sum()
        fn = ((predicted != i) & (true == i)).sum()
        tn = ((predicted != i) & (true != i)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support   = (true == i).sum()

        per_class[label] = {
            "precision": round(float(precision), 4),
            "recall":    round(float(recall), 4),
            "f1":        round(float(f1), 4),
            "support":   int(support),
            "tp": int(tp), "fp": int(fp), "fn": int(fn),
        }

    macro_f1 = np.mean([per_class[l]["f1"] for l in LABELS])

    return {
        "overall_accuracy": round(float(overall_acc), 4),
        "macro_f1":         round(float(macro_f1), 4),
        "per_class":        per_class,
    }


def compute_confusion_matrix(results: dict) -> np.ndarray:
    """
    Returns confusion matrix of shape [num_classes, num_classes].
    Row = true label, Column = predicted label.
    """
    n = NUM_CLASSES
    matrix = np.zeros((n, n), dtype=int)
    for true, pred in zip(results["true"], results["predicted"]):
        matrix[true][pred] += 1
    return matrix


def analyze_confidence(results: dict) -> dict:
    """
    Analyze confidence score distribution.
    
    Important for production:
    - What % of predictions would be auto-approved (>= 85%)?
    - What's the average confidence on correct vs wrong predictions?
    """
    true        = results["true"]
    predicted   = results["predicted"]
    confidences = results["confidences"]

    correct_mask   = true == predicted
    incorrect_mask = ~correct_mask

    auto_approve_mask = confidences >= AUTO_APPROVE_THRESHOLD
    auto_approve_correct = (auto_approve_mask & correct_mask).sum()
    auto_approve_total   = auto_approve_mask.sum()

    return {
        "mean_confidence_correct":   round(float(confidences[correct_mask].mean()), 4) if correct_mask.any() else 0,
        "mean_confidence_incorrect": round(float(confidences[incorrect_mask].mean()), 4) if incorrect_mask.any() else 0,
        "pct_above_threshold":       round(float(auto_approve_mask.mean()), 4),
        "auto_approve_accuracy":     round(float(auto_approve_correct / auto_approve_total), 4) if auto_approve_total > 0 else 0,
        "auto_approve_count":        int(auto_approve_total),
        "manual_review_count":       int((~auto_approve_mask).sum()),
        "threshold":                 AUTO_APPROVE_THRESHOLD,
    }


# ── Pretty Printing ────────────────────────────────────────

def print_report(metrics: dict, confusion: np.ndarray, confidence: dict):
    """Print a formatted evaluation report to console."""

    print("\n" + "="*65)
    print("📋 EcoCred ML Model — Evaluation Report")
    print("="*65)

    # Overall metrics
    print(f"\n📊 Overall Metrics:")
    print(f"  Accuracy:  {metrics['overall_accuracy']:.4f}  ({metrics['overall_accuracy']:.2%})")
    print(f"  Macro F1:  {metrics['macro_f1']:.4f}")

    prod_ready = metrics["overall_accuracy"] >= 0.85
    print(f"  Production ready: {'✅ YES' if prod_ready else '❌ NO (need >=85%)'}")

    # Per-class metrics
    print(f"\n📦 Per-Class Metrics:")
    print(f"  {'Class':<12} {'Precision':>10} {'Recall':>8} {'F1':>6} {'Support':>8}")
    print(f"  {'-'*48}")
    for label, m in metrics["per_class"].items():
        flag = " ⚠️" if m["f1"] < 0.70 else ""
        print(f"  {label:<12} {m['precision']:>10.3f} {m['recall']:>8.3f} {m['f1']:>6.3f} {m['support']:>8}{flag}")

    # Confidence analysis
    print(f"\n🎯 Confidence Analysis (threshold={confidence['threshold']:.0%}):")
    print(f"  Avg confidence (correct):   {confidence['mean_confidence_correct']:.3f}")
    print(f"  Avg confidence (incorrect): {confidence['mean_confidence_incorrect']:.3f}")
    print(f"  Auto-approve rate:          {confidence['pct_above_threshold']:.1%} of predictions")
    print(f"  Auto-approve accuracy:      {confidence['auto_approve_accuracy']:.2%}")
    print(f"  Would go to manual review:  {confidence['manual_review_count']} samples")

    # Confusion matrix
    print(f"\n🔀 Confusion Matrix (row=true, col=predicted):")
    header = f"  {'':>10}" + "".join(f"{l[:6]:>8}" for l in LABELS)
    print(header)
    for i, label in enumerate(LABELS):
        row = f"  {label:<10}" + "".join(
            f"{'█' if j == i else ' '}{confusion[i][j]:>7}" if confusion[i][j] > 0
            else f"{'':>8}"
            for j in range(NUM_CLASSES)
        )
        print(row)

    # Top misclassifications
    print(f"\n❌ Top Misclassifications:")
    mistakes = []
    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            if i != j and confusion[i][j] > 0:
                mistakes.append((confusion[i][j], LABELS[i], LABELS[j]))
    mistakes.sort(reverse=True)
    for count, true_lbl, pred_lbl in mistakes[:8]:
        print(f"  {true_lbl:<12} → predicted as {pred_lbl:<12}  ({count} times)")

    print("\n" + "="*65)


# ── Main ───────────────────────────────────────────────────

def main(data_dir: str = "data", model_path: str = "ecocred_model.pth", split: str = "test"):
    print(f"\n🌿 EcoCred Model Evaluation")
    print(f"   Model: {model_path}")
    print(f"   Split: {split}")

    # Load model
    model, device = load_model(model_path)

    # Load data
    loaders, _ = get_dataloaders(data_dir, batch_size=64, num_workers=4, balance_classes=False)
    loader = loaders[split]

    print(f"\n⏳ Running evaluation on {len(loader.dataset)} samples...")
    results   = evaluate_full(model, loader, device)
    metrics   = compute_metrics(results)
    confusion = compute_confusion_matrix(results)
    confidence = analyze_confidence(results)

    # Print report
    print_report(metrics, confusion, confidence)

    # Save JSON report
    report = {
        "model_path":  model_path,
        "split":       split,
        "n_samples":   len(loader.dataset),
        "metrics":     metrics,
        "confidence":  confidence,
        "confusion_matrix": confusion.tolist(),
        "labels":      LABELS,
    }
    report_path = f"eval_report_{split}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n💾 Full report saved to {report_path}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate EcoCred waste classifier")
    parser.add_argument("--data_dir",   default="data")
    parser.add_argument("--model_path", default="ecocred_model.pth")
    parser.add_argument("--split",      default="test", choices=["train", "val", "test"])
    args = parser.parse_args()
    main(args.data_dir, args.model_path, args.split)
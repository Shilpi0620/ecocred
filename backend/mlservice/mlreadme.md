# EcoCred ML Service — Setup & Usage Guide

## 📁 Files

```
ml_service/
├── dataset.py          # Image loading, augmentation, preprocessing
├── model.py            # ResNet50 architecture + inference logic
├── train.py            # Full training loop
├── evaluate.py         # Accuracy metrics + confusion matrix
├── main.py             # FastAPI server (production endpoint)
├── requirements.txt    # Python dependencies
└── ecocred_model.pth   # ← Created after training (not in repo)
```

---

## 🚀 Step-by-Step Setup

### Step 1 — Install dependencies

```bash
cd ecocred-backend/ml_service
pip install -r requirements.txt
```

---

### Step 2 — Download training dataset

We use **TrashNet** — a popular open dataset of 2,527 waste images across 6 classes.

```bash
# Option A: Download from Kaggle (recommended — more images)
# https://www.kaggle.com/datasets/fedesoriano/garbage-classification

# Option B: TrashNet (original)
# https://github.com/garythung/trashnet
# Download: dataset-resized150x150.zip
```

After downloading, your raw data folder should look like:
```
dataset-resized150x150/
├── cardboard/    (403 images)
├── glass/        (501 images)
├── metal/        (410 images)
├── paper/        (594 images)
├── plastic/      (482 images)
└── trash/        (137 images)
```

---

### Step 3 — Prepare dataset (split into train/val/test)

```bash
python dataset.py dataset-resized150x150 data
```

This creates:
```
data/
├── train/   (70% of images per class)
├── val/     (15% of images per class)
└── test/    (15% of images per class)
```

For E-Waste (not in TrashNet), collect your own images or use:
```
https://www.kaggle.com/datasets/akshaynair/e-waste-images-dataset
```
Place them in `data/train/ewaste/`, `data/val/ewaste/`, `data/test/ewaste/`

---

### Step 4 — Train the model

```bash
# Default training (recommended settings)
python train.py

# Custom settings
python train.py --epochs 60 --batch_size 16 --lr 5e-5 --patience 10

# If you have limited GPU memory, reduce batch size:
python train.py --batch_size 16
```

Training will:
- Show progress every 20 batches
- Save best model to `ecocred_model.pth` automatically
- Stop early if validation accuracy stops improving
- Print final test accuracy

Expected output:
```
Epoch 1/50
  Batch 20/52 — loss=1.8432 acc=0.312
  Train: loss=1.6234 acc=0.421
  Val:   loss=1.2341 acc=0.623  ← BEST
  💾 Saved best model → ecocred_model.pth

Epoch 2/50
  ...

Epoch 18/50 (early stopping may trigger around here)
  Train: loss=0.3421 acc=0.912
  Val:   loss=0.4123 acc=0.891  ← BEST

📋 Final Test Accuracy: 0.8847 (88.47%)
✅ Model meets 85% accuracy threshold for production
```

---

### Step 5 — Evaluate the model

```bash
python evaluate.py

# Evaluate on validation set instead of test
python evaluate.py --split val
```

Output includes:
- Overall accuracy and F1 score
- Per-class precision, recall, F1
- Confusion matrix (which classes get mixed up)
- Confidence distribution (what % will auto-approve)

Example:
```
📊 Overall Metrics:
  Accuracy:  0.8847  (88.47%)
  Macro F1:  0.8712
  Production ready: ✅ YES

📦 Per-Class Metrics:
  Class        Precision   Recall     F1  Support
  cardboard       0.921    0.904  0.912       61
  ewaste          0.876    0.891  0.883       45
  glass           0.862    0.849  0.855       75
  metal           0.901    0.918  0.909       62
  organic         0.834    0.821  0.827       84
  paper           0.889    0.876  0.882       89
  plastic         0.912    0.934  0.923       72
  trash           0.778    0.742  0.759       21

🎯 Confidence Analysis (threshold=85%):
  Auto-approve rate:     73.2% of predictions
  Auto-approve accuracy: 96.8%
  Would go to manual review: 135 samples
```

---

### Step 6 — Start the ML service

```bash
# Development
uvicorn main:app --port 8001 --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2
```

Test it works:
```bash
curl http://localhost:8001/health
```

---

### Step 7 — Test with a real image

```bash
# Test with local file
python model.py path/to/plastic_bottle.jpg

# Test the API endpoint
curl -X POST http://localhost:8001/verify-upload \
  -F "file=@plastic_bottle.jpg"
```

---

## 🔗 How Django connects to this service

In `apps/waste/tasks.py` (Celery task):

```python
response = requests.post(
    "http://localhost:8001/verify",           # ML service URL
    json={"image_url": submission.image.url}, # Cloudinary URL
    timeout=30
)
data = response.json()
# data = { label: "plastic", confidence: 0.94, auto_approve: True, ... }
```

Django never imports Python from `ml_service/` — it only communicates via HTTP.

---

## 🌡️ Model Performance Targets

| Metric | Minimum | Target |
|--------|---------|--------|
| Overall accuracy | 85% | 90%+ |
| Auto-approve rate | 60% | 75%+ |
| Auto-approve accuracy | 95% | 97%+ |
| Inference time | < 500ms | < 200ms |

---

## 🧠 Improving the Model

If accuracy is below 85%, try:

1. **More data** — collect more images per class (especially E-Waste and Trash)
2. **Longer training** — `--epochs 80 --patience 15`
3. **Lower learning rate** — `--lr 5e-5`
4. **Larger model** — change `resnet50` to `resnet101` in `model.py`
5. **Better augmentation** — add more transforms in `dataset.py`

---

## 📦 Adding New Waste Categories

1. Add the new class name to `LABELS` in `dataset.py`
2. Add mapping to `LABEL_TO_SLUG` in `dataset.py`  
3. Add a corresponding Material in Django admin
4. Collect 300+ training images for the new class
5. Retrain: `python train.py`
6. Re-evaluate: `python evaluate.py`
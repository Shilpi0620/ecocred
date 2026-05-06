from PIL import Image
import io, torch
from torchvision import transforms, models

LABELS = ['cardboard', 'ewaste', 'glass', 'metal', 'organic', 'paper', 'plastic']

model = models.resnet50(pretrained=False)
model.fc = torch.nn.Linear(model.fc.in_features, len(LABELS))
# model.load_state_dict(torch.load('ecocred_model.pth', map_location='cpu'))
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def classify_waste(image_bytes: bytes) -> dict:
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    t = transform(img).unsqueeze(0)
    with torch.no_grad():
        out = torch.softmax(model(t), dim=1)[0]
    conf, idx = out.max(0)
    return {
        "label": LABELS[idx],
        "confidence": round(float(conf), 4),
        "all": {LABELS[i]: round(float(out[i]), 4) for i in range(len(LABELS))}
    }
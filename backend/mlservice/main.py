from fastapi import FastAPI
from pydantic import BaseModel
import httpx

app = FastAPI(title="EcoCred ML Service")

class VerifyRequest(BaseModel):
    image_url: str

@app.post("/verify")
async def verify_waste(req: VerifyRequest):
    async with httpx.AsyncClient() as client:
        r = await client.get(req.image_url)
        image_bytes = r.content

    from models import classify_waste
    result = classify_waste(image_bytes)

    return {
        "predicted_material": result["label"],
        "confidence": result["confidence"],
        "all_predictions": result["all"],
        "model_version": "v1.2"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "BookTime API - Test simple"}

@app.get("/health")
def health():
    return {"status": "ok", "message": "Backend simplifié fonctionnel"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
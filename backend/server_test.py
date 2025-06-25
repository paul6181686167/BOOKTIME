from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="BookTime API Test")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

@app.get("/")
async def read_root():
    return {"message": "BookTime API Test - Fonctionnel"}

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Server is running"}
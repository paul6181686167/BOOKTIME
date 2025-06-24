from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Test API works"}

@app.get("/api/test")
async def test():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
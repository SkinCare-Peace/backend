# main.py
import uvicorn
from fastapi import FastAPI
from api import cosmetic_recommend, predict
from services.model_loader import load_models

app = FastAPI()

app.include_router(predict.router)
app.include_router(cosmetic_recommend.router)

if __name__ == "__main__":
    load_models()
    uvicorn.run(app, host="127.0.0.1", port=8000)

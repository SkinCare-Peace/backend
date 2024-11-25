# main.py
import uvicorn
from fastapi import FastAPI
from api import cosmetic_recommend, predict, routine_generate
from services.model_loader import load_models
import pprint

app = FastAPI()

app.include_router(predict.router)
app.include_router(cosmetic_recommend.router)
app.include_router(routine_generate.router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

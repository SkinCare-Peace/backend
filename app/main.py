# main.py
import uvicorn
from fastapi import FastAPI
from api import cosmetics, predict, routine, user
from services.model_loader import load_models

app = FastAPI()

app.include_router(predict.router)
app.include_router(routine.router)
app.include_router(cosmetics.router)
app.include_router(user.router)


if __name__ == "__main__":
    load_models()
    uvicorn.run(app, host="127.0.0.1", port=8000)

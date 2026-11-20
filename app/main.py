from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path

from app.core.lifespan import lifespan

load_dotenv()  # Load environment variables from .env file

BASE_DIR = Path(__file__).resolve().parentexi

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "Server is running!"}


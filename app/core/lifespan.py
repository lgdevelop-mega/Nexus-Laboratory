from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load environment variables from .env file
    load_dotenv()

    # Perform any startup tasks here
    print("Starting up the application...")

    yield  # This is where the application runs

    # Perform any shutdown tasks here
    print("Shutting down the application...")
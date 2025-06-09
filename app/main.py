from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.router import router

app = FastAPI(title="DynamicRAG - Gemini LLM Q&A")

app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, actions, insights

app = FastAPI(title="ParcelPilot AI Support Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(actions.router)
app.include_router(insights.router)


@app.get("/health")
def health():
    return {"status": "ok"}

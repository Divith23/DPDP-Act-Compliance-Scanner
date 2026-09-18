from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.mongodb import connect, disconnect
from app.routes.analyze import router as analyze_router
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    try:
        from app.services.rag import _load
        _load()
        print("RAG vectorstore pre-warmed successfully.")
    except Exception as e:
        print(f"Notice: RAG pre-warming skipped: {e}")
    yield
    await disconnect()


app = FastAPI(title="DPDP Guard AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(analyze_router, prefix="/api")

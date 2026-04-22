from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import dbs_router

app = FastAPI(title="DB Query API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dbs_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

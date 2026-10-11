from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.routes import router as agents_router
from app.numbers.routes import router as numbers_router

# Keys and DEMO_MODE live in the repo-root .env. Real environment variables win over the file.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

app = FastAPI(title="AI Credit Committee API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(numbers_router)
app.include_router(agents_router)


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}

# AI Credit Committee

AI agents act as a credit fund's committee and decide whether to lend to a company. The demo
borrower is Pizza Co. (`PZCO`), which is fictional. The backend does the covenant math locally,
then a LangGraph pipeline of Gemini agents (two analysts, a Bull, a Bear and a Chair) debates and
streams its verdict to the Next.js dashboard.

Copy `.env.example` to `.env` and set `GEMINI_API_KEY`. With `DEMO_MODE=1` the backend replays the
saved runs in `data/demo_runs/` instead of calling Gemini; it also falls back to them if a Gemini
call fails.

## Run locally

```bash
# Terminal 1
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. API docs are at http://localhost:8000/docs.

Run the calculator tests with `cd backend && pytest`.

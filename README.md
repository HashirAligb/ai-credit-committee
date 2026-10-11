# AI Credit Committee

A fake-data demo where a credit committee evaluates Pizza Co. (`PZCO`). The backend
calculates covenant stress locally and streams canned analyst decisions; the Next.js
frontend presents the dashboard.

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

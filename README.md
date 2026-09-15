# Finlens

Finlens turns bank and card statements into a clear picture of how your money
actually behaves — income, spending by category, recurring expenses, and
month-over-month trends, instead of a raw transaction list.

## Stack

- **Backend** — FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT auth, pdfplumber
  for PDF statement parsing.
- **Frontend** — React 19, Vite, TypeScript, Tailwind CSS v4, TanStack Query.
- **Infra** — Docker Compose (Postgres, Redis, API, web) for local dev.

## Getting started

### Docker (recommended)

```bash
docker compose up --build
```

This runs migrations and seeds the default category tree automatically. The
app is at http://localhost:5173, the API at http://localhost:8000/api.

### Running locally without Docker

Backend:

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
# Postgres + Redis must be reachable at the URLs in .env — `docker compose up postgres redis` works for just those two.
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## How ingestion works

Upload → `app/services/parsing/{csv,pdf}_parser.py` extracts raw rows →
`normalize.py` cleans the merchant name and flags obvious self-transfers →
`categorize.py` matches the merchant/description against a keyword rule table
→ the transaction lands in Postgres with a category and a confidence score.
Manually correcting a category in the UI sets confidence to 1.0, so those
corrections are distinguishable from the rule engine's guesses later if this
becomes a training signal for a smarter classifier.

**CSV** is the reliable path — it recognizes the column-header conventions
most Indian bank exports use (Date/Narration/Debit/Credit, Date/Description/
Amount, etc.). **PDF** parsing is best-effort: it works when pdfplumber can
detect a real table in the statement, which most net-banking PDF exports have.
Scanned statements, image-only PDFs, and banks that lay out transactions as
free text rather than a table aren't supported yet — that needs a bank-specific
parser, which is a natural next step once you know which banks matter most to
you.

## What's implemented (MVP)

- Auth (register/login, JWT)
- Multiple accounts per user
- CSV/PDF statement upload → parse → normalize → categorize
- Dashboard: income/expenses/savings rate, 6-month cash flow trend, spending
  by category, recurring expense detection
- Transaction search/filter, manual category correction

## Roadmap

- **V2**: subscription detection, refund/reversal matching (net out
  return-and-refund pairs instead of double-counting them), smarter transfer
  detection between a user's own accounts, per-bank PDF parsers, multi-account
  aggregate net worth.
- **V3**: "Ask Finlens" natural-language queries over transaction data,
  anomaly detection, exportable reports, forecasting.

The statement parser currently runs synchronously inside the upload request
(`app/services/ingestion.py`) — fine for the file sizes a personal statement
export produces. Redis + RQ are already wired into the stack for when that
needs to move to a background worker (larger files, OCR on scanned PDFs).

## Privacy

This app handles bank statements, so a few things are worth being deliberate
about as it grows past a local project: encrypting statement files at rest if
raw uploads are ever persisted (currently they aren't — only the parsed
transactions are stored), scoping every query to the authenticated user
(enforced in every route in `app/api/routes/`), and giving users a real way to
delete their data.

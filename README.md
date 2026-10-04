# Campus Customs

A Yale-themed campus merchandise shop: a React + FastAPI website with an AI shopping
assistant that can search the real product catalogue, answer price/description/stock
questions, and suggest in-stock alternatives — all grounded in an actual SQLite database,
never guessed or made up.

## What's in each folder

| Folder | Contents |
|---|---|
| `backend/` | FastAPI app — routes, auth, the PydanticAI chatbot agent and its tools, the audit trail. See `backend/main.py` for the entry point. |
| `frontend/` | React + Vite + TypeScript site — pages, components, the floating chat widget. |
| `data/` | **Not included in this repo.** The product database and images go here — see "Adding the data pack" below. |
| `output/` | Project deliverables: `harness.md` (full system writeup), `design.md`, `usability.md`, `app_check.html` (test report with screenshots), `audit_trail.json` (generated at runtime — see `output/harness.md`). |
| `AI_prompts.md` | Log of every prompt used to build this project, one section per problem. |

## Adding the data pack

This repo doesn't include the database or product images (they're in `.gitignore`). To run
the app, place:

- `data/campus_customs.db`
- `data/products/` (the product image files)

directly under this repo's root, so the paths are `data/campus_customs.db` and
`data/products/<file>.jpg`. Ask whoever shared this project with you for that data pack.

## Backend setup

From this repo's root:

```bash
python -m venv .venv
```

Activate it — Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env` (in this repo's root) and fill in real values:

```bash
cp .env.example .env
```

- `PORTKEY_API_KEY` — routes the chatbot's model calls through Portkey. Get one from
  [portkey.ai](https://portkey.ai).
- `SESSION_SECRET_KEY` — signs login session tokens. Any long random string works, e.g.:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

Never commit your real `.env` — it's already in `.gitignore`.

## Running the backend

From `backend/`, using the virtual environment created above:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Serves the API at `http://localhost:8000`.

## Running the frontend

From `frontend/`, in a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Serves the site at `http://localhost:5173` (Vite's default), which talks to the backend
above.

## Test login

A seed account exists in the data pack for trying out the logged-in experience (saved chat
history, personalized greetings):

- **Email:** `test@campuscustoms.yale.edu`
- **Password:** `password`

Or sign up your own account from the site's signup page — it only ever writes a new row to
the `users` table.

# Engauge — local professor polling app

This is a local Django app that helps instructors upload class materials (PDF or PowerPoint), generate candidate multiple-choice questions using Groq, allow the instructor to accept/reject generated questions, and run live polls where students answer and the instructor sees results.

# Our Methodology

Creating material for students to reinforce learning and move information from short term to long term information is one of the most effective ways for instructors to improve learning, recall, and gauge student understanding. However, creating this material for every class can be time consuming and high effort. Additionally, this material might not be reinforced continually after the class, and students may end up forgetting it. Engauge serves a double purpose. Using the professors lessons plans, it will automatically create poll questions and exit tickets, moving up the pyramid of Blooms Taxonomy, to assist with student learning. It will also provide students a gamified way to continually reinforce the information outside of lessons. It will also provide metrics to the professors, informing them on the subjects that are least understood by students, and giving them insight on which students need the most assistance.


Key points
- Python + Django backend
- Postgres is recommended (configured via env vars)
- Uses Groq LLM to generate questions (provide `GROQ_API_KEY`)

Quick setup (macOS):

1. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure database and environment variables

- EITHER use SQLite for quick local runs (no Postgres required):

```bash
cp .env.example .env
echo "USE_SQLITE=1" >> .env
```

- OR use Postgres. Create a Postgres DB and user, or set env vars to match your setup. Required env variables:

  - POSTGRES_DB (default: engauge_db)
  - POSTGRES_USER (default: engauge_user)
  - POSTGRES_PASSWORD (default: engauge_pass)
  - POSTGRES_HOST (default: localhost)
  - POSTGRES_PORT (default: 5432)
  - GROQ_API_KEY — your Groq API key
  - GROQ_MODEL — (optional) e.g., `llama-3.1-70b-versatile`
  - DJANGO_SECRET_KEY — (optional) a secret string

You can create a `.env` file in the project root and the app will load it.

3. Run migrations and start server

```bash
python manage.py migrate
python manage.py runserver
```

4. Open the site at http://127.0.0.1:8000/

Postgres setup quickstart (optional)

If you prefer Postgres locally, these commands (psql) will create the role and DB matching defaults:

```sql
CREATE ROLE engauge_user WITH LOGIN PASSWORD 'engauge_pass';
CREATE DATABASE engauge_db OWNER engauge_user;
GRANT ALL PRIVILEGES ON DATABASE engauge_db TO engauge_user;
```

Or configure DATABASE_URL, e.g.:

```bash
export DATABASE_URL="postgres://engauge_user:engauge_pass@localhost:5432/engauge_db"
```

Notes & assumptions
- The Groq client in `polls/llm_client.py` uses the Chat Completions API and instructs the model to return a strict JSON array of question items. The parser will attempt strict JSON first, then extract the first JSON array from text. Fallback mock questions are used when no key is set or parsing fails.
- The app extracts text using `pdfminer.six` for PDFs and `python-pptx` for PowerPoint files.
- For quick local testing without Postgres, set `USE_SQLITE=1` in `.env`.

Next steps / possible enhancements
- Add authentication for professors
- Add a nicer UI and websockets for live updates
- Improve parsing & prompt engineering for Claude to guarantee JSON output
# Engauge
Claude For Good Hackathon Project

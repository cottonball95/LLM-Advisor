# AI Academic Advisor — Hybrid (Streamlit + SQLite + OpenAI)

## Run locally
```bash
pip install -r requirements.txt
# set your key if using OpenAI mode
# Windows PowerShell:
#   $env:OPENAI_API_KEY="sk-..."
# Mac/Linux:
#   export OPENAI_API_KEY="sk-..."

streamlit run app.py
```

- In the app, set **SQLite DB path** to your `advising.db` (built with DB Browser for SQLite).
- Choose a student or mark completed courses.
- Pick term & target credits.
- (Optional) tick **Use OpenAI** to get rationale and prioritization.

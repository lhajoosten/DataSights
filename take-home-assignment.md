# Take-Home Assignment: Full-Stack AI Developer

## Theme & brief
**Theme:** "Talk to your data" — build an LLM chatbot that turns questions about data into charts.  
**Timebox:** Up to 4 hours.  
**What we're assessing:** approach, decision-making, and communication of trade-offs (not perfect polish).

---

## The brief
Build a small web app where a user can:
- Upload a CSV file.
- Ask a natural-language question about that data (e.g., “show total sales by month for 2024”).
- Receive an answer as a chart (bar/line/scatter etc.) with a short textual explanation.

Use off-the-shelf components as needed to stay within the timebox.

---

## Must-haves (acceptance criteria)
- **Upload**
    - Accept a CSV (≤ 10 MB) and parse it safely.
    - Show a quick preview (first ~20 rows).
- **Question → chart**
    - Use an LLM to interpret the question and produce a chart of the uploaded data.
    - The LLM can suggest aggregation, grouping, filtering, and chart type.
    - Render the chart in the UI.
- **Basic guardrails**
    - Handle unclear questions (ask for clarification or return a friendly error).
- **Reproducible run**
    - Provide a simple way to run locally.
- **Documentation**
    - Include a short `DECISIONS.md` describing approach, key choices, trade-offs, and next steps.

---

## Nice-to-haves (if time permits)
- Follow-ups: keep chat context so follow-up questions refine the same chart/data.
- Multiple charts: allow switching chart types when sensible.
- Explainability: show generated query/code used to build the chart (e.g., pandas/SQL) with brief rationale.
- Minimal tests: unit/integration tests for critical pieces (CSV validation, chart spec generation).
- Light auth: simple route protection or basic rate-limiting.

---

## Suggested tools (pick what you know)
- Frontend/UI: Streamlit, Gradio, React + Next.js, or minimal Flask/FastAPI.
- Charts: Plotly, Vega-Lite/Altair, Chart.js/Recharts.
- LLM & orchestration: Azure OpenAI / OpenAI API, OpenRouter, Hugging Face, Ollama (local).
- Data handling: pandas / pyarrow or DuckDB for quick aggregations.
- Environment: Python or TypeScript/Node.

---

## Notes
- LLMs: If you have paid LLM API access, feel free to use it. If not, consider running a local model with Ollama (e.g., Gemma3 4B or Qwen3 4B).
- Credentials: Do not commit API keys. Use environment variables and a `.env` file.
- Sample CSV: You can use your own dataset or generate a small sales dataset:
    - Columns: `date`, `region`, `product`, `units_sold`, `unit_price`.

---

## What to submit
A Git repo (GitHub link or zip) containing:
- Source code
- Test dataset
- `README.md` with setup/run instructions (target: <5 minutes to run)
- `DECISIONS.md` (1–2 pages max): include ASCII architecture diagram, key libraries, reasoning, risks, and a “if I had 2 more days” roadmap

Optional:
- Short screen recording (<2 min) demoing the flow, or demo live during evaluation.
- If using Docker, include a `Dockerfile` (and `docker-compose.yml` if needed).

---

## Evaluation rubric
- Problem framing & trade-offs (35%)
    - Are choices explained? Do off-the-shelf components fit the problem?
    - Are edge cases acknowledged (ambiguous questions, missing columns)?
- Functionality & UX (25%)
    - Can we upload a CSV, ask a question, and get a sensible chart + brief explanation?
    - Reasonable defaults; helpful errors; tidy UI.
- Code quality (20%)
- Reliability & reproducibility (10%)
    - Easy to run; works out-of-the-box with provided instructions.
- Extendability (10%)
    - Is it obvious how to add features (more chart types, SQL over larger files, caching)?

---

## Discussion topics (follow-up call)
- Why the chosen stack and libraries?
- How questions are translated to chart specs (reasoning flow).
- Handling ambiguity and safety.
- Priorities for further work (performance, vectorization, SQL pushdown, RAG over docs, multi-file support, etc.).

---

## Practical constraints & notes
- Timebox: Stop at ~4 hours; document anything intentionally left out.
- Licensing: Prefer permissive libraries; note any licenses that may matter.
- Safety: Avoid committing secrets and executing untrusted generated code without safeguards.
- Keep the UI simple and the boundaries between UI / LLM / data processing clear.
- Aim for a reproducible, minimal demo that demonstrates the core flow.

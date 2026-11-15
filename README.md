# MindMate 🌱

A responsive, installable student wellbeing support app prototype for school, college and university students, with a calm, confident conversational voice.

**MindMate is not therapy, diagnosis, or crisis care.** It offers supportive conversation, low-risk self-help ideas, mood reflection, journaling stored locally in the browser, and links to trusted resources.

## Live demo

- **App:** https://mindmate-nine-coral.vercel.app/
- **API health check:** https://mindmate-api-live.onrender.com/health
- **API documentation:** https://mindmate-api-live.onrender.com/docs

## Features

- Responsive phone/desktop interface; installable PWA.
- Hybrid assistant: lightweight lexical NLP + curated knowledge retrieval + optional OpenAI-compatible chat API.
- Conversational style: calm, confident, perceptive and gently witty; designed to listen before offering suggestions.
- Safety-first response path for crisis language and an always-visible urgent-help action.
- Mood check-ins and journal entries stored in browser localStorage only.
- Curated knowledge cards with source links and review metadata.
- No account, no analytics, no server-side chat or mood storage.

## Run locally

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend: serve the repository root with any static server (for example `python -m http.server 8080`) and open http://localhost:8080. Set `window.MINDMATE_API_URL` in `config.js` to your API URL if needed.

## Optional LLM

Set `LLM_API_KEY`, `LLM_BASE_URL` (default OpenAI-compatible `https://api.openai.com/v1`) and `LLM_MODEL` on the backend host. The key must only be stored as a server environment secret, never in frontend code. Without these variables, the assistant uses its local retrieval-and-template fallback.

The LLM receives the current message, up to eight recent messages from the active chat, and a small set of retrieved public knowledge snippets. Chat history is held in browser memory for the active session and is not stored in a MindMate account or database. When an external LLM is enabled, those messages are sent to the configured provider; review that provider's data policy before enabling it. Do not enter identifying or highly sensitive information. Review the provider's data policy before enabling an external model.

## Safety & limitations

- Crisis keyword rules are intentionally conservative but **cannot reliably detect every crisis**. They are not a risk assessment. The urgent-help button is always available.
- If someone may be in immediate danger, encourage contacting local emergency services, going to the nearest emergency department, and telling a trusted person who can stay with them. Do not rely on this app.
- The assistant does not diagnose, prescribe, or replace a qualified professional.
- Emotion/topic cues are simple lexical heuristics, not validated clinical NLP.
- Knowledge snippets are brief educational summaries, not treatment instructions. See source URLs and review dates in `backend/app/knowledge.json`.
- Mood/journal data stay in this browser's local storage. Clearing browser site data removes them; anyone with access to the unlocked device may see them.
- This is an educational prototype. Conduct clinical, safeguarding, accessibility, privacy and ethics review before any real-world deployment or study.

## Tests

GitHub Actions runs the backend test suite on pushes to `main` that change `backend/` and on pull requests that change backend files.

Run locally:

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Research direction

Potential evaluation: usability and accessibility testing; retrieval precision against a reviewed query set; safety red-team scenarios; expert review of resource summaries; opt-in user study with ethics approval. Do not report efficacy without appropriate evidence.

## Sources

- WHO, *Doing What Matters in Times of Stress* (2020): https://www.who.int/publications/i/item/9789240003927
- WHO, Psychological self-help interventions: https://www.who.int/teams/mental-health-and-substance-use/treatment-care/psychological-interventions/psychological-self-help-interventions
- NHS Every Mind Matters, Self-help CBT techniques: https://www.nhs.uk/every-mind-matters/mental-wellbeing-tips/self-help-cbt-techniques/
- NHS Inform, Anxiety self-help guide: https://www.nhsinform.scot/illnesses-and-conditions/mental-health/mental-health-self-help-guides/anxiety-self-help-guide/

## License

MIT (prototype code). External source materials remain the property of their respective publishers.

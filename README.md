# Shiva Draft Intelligence v2

A mobile-first fantasy football draft companion built with Streamlit.

## What is included

- **Ask Shiva GPT** — OpenAI Responses API Q&A with current rankings, watchlist, league-history summary and live draft state injected into every question.
- **Live Mock Draft** — 10/12-team snake drafts, CPU picks, available-player pool, roster tracking and a Sleeper-style draft board.
- **Who Should I Pick?** — one-click live recommendation that knows your roster, the board, the current pick, ADP and watchlist.
- **Draft Coach** — pick-slot schedule and ADP windows for planning early rounds.
- **My Players** — persistent-in-session target/watch list that follows you into the mock draft and Ask Shiva.
- **League History** — searches the existing `shiva_draft_roi.sqlite` database.

## Streamlit deployment

1. Deploy this repository in Streamlit Community Cloud and use `app.py` as the entry point.
2. In **App → Settings → Secrets**, add:

```toml
OPENAI_API_KEY = "your_openai_api_key"
OPENAI_MODEL = "gpt-5-mini"
```

`OPENAI_MODEL` is optional. Never commit `secrets.toml` or an API key to GitHub.

## Data

The app expects these existing repository files:

- `current_rankings.csv`
- `shiva_draft_roi.sqlite`

The current rankings file is treated as the authoritative board for mock-draft availability and ADP.

## Design note

The visual language is intentionally inspired by modern fantasy-sports apps—dark surfaces, compact mobile navigation, dense player cards, green live-state accents—but does not copy ESPN or DraftSharks proprietary branding or assets.

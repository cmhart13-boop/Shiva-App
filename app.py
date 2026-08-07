from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from shiva_ai import ask_shiva, build_context
from shiva_draft import (
    DraftConfig,
    advance_cpus,
    available_players,
    board_matrix,
    make_pick,
    pick_team,
    roster_counts,
    score_board,
    slot_picks,
    user_roster,
)

APP_DIR = Path(__file__).resolve().parent
RANKINGS_PATH = APP_DIR / "current_rankings.csv"
DB_PATH = APP_DIR / "shiva_draft_roi.sqlite"
MODEL = "gpt-5-mini"

st.set_page_config(page_title="Shiva Draft Intelligence", page_icon="🏆", layout="wide", initial_sidebar_state="collapsed")

CSS = r"""
<style>
:root{--bg:#0a0a0c;--panel:#18191d;--panel2:#22242b;--line:#34363e;--text:#f7f7f8;--muted:#999ba3;--green:#32f244;--blue:#62a0ff;--red:#ff5965;--gold:#ffbd42}
html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.stApp{background:var(--bg);color:var(--text)}
.block-container{max-width:1180px;padding:14px 18px 70px!important}
#MainMenu,footer,header{visibility:hidden}
h1,h2,h3,p,label,.stMarkdown{color:var(--text)}
.hero{padding:22px 24px;border:1px solid var(--line);border-radius:24px;background:linear-gradient(145deg,#1d1f24,#131418);margin:8px 0 18px}
.kicker{color:var(--green);font-weight:900;letter-spacing:.12em;text-transform:uppercase;font-size:12px}.hero h1{font-size:34px;line-height:1.05;margin:8px 0}.muted{color:var(--muted);font-size:14px;line-height:1.5}
.navlabel{color:#777980;font-size:10px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;margin:4px 0 7px}
div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel){gap:8px}
.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_watch button,.st-key-nav_history button{min-height:76px!important;border-radius:18px!important;background:#1d1f24!important;border:1px solid #34363e!important;color:#fff!important;font-weight:900!important;font-size:12px!important;white-space:pre-line!important;line-height:1.15!important}
.st-key-nav_intel button[kind="primary"],.st-key-nav_coach button[kind="primary"],.st-key-nav_mock button[kind="primary"],.st-key-nav_watch button[kind="primary"],.st-key-nav_history button[kind="primary"]{border-color:var(--green)!important;box-shadow:0 0 18px rgba(50,242,68,.22)!important}
[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{background:#20232b!important;border:1px solid #343946!important;color:white!important;border-radius:14px!important}
.stButton button{border-radius:14px!important;min-height:44px!important;font-weight:800!important}
.stButton button[kind="primary"]{background:var(--green)!important;color:#071107!important;border-color:var(--green)!important}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:18px;margin:10px 0}.panel-title{font-size:20px;font-weight:950;margin-bottom:4px}.small{font-size:12px;color:var(--muted)}
.metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin:12px 0}.metric{background:#202126;border:1px solid #34363e;border-radius:16px;padding:13px}.metric-label{font-size:10px;color:#898b92;font-weight:900;text-transform:uppercase}.metric-value{font-size:23px;font-weight:950;margin-top:7px}.green{color:var(--green)}.blue{color:var(--blue)}.red{color:var(--red)}
.player-card{display:grid;grid-template-columns:46px 1fr auto;gap:10px;align-items:center;background:#1b1c20;border:1px solid #30323a;border-radius:15px;padding:11px 12px;margin:7px 0}.pos{font-size:11px;font-weight:950;border-radius:8px;padding:7px 5px;text-align:center;background:#292c34}.player-name{font-weight:900;font-size:15px}.player-sub{font-size:11px;color:#8f9199;margin-top:2px}.adp{font-size:12px;color:#aeb0b7;font-weight:800}
.board-wrap{overflow-x:auto;border:1px solid #30323a;border-radius:18px;background:#121316;padding:10px}.board{display:grid;gap:6px;min-width:920px}.board-cell{min-height:58px;background:#202126;border:1px solid #34363e;border-radius:9px;padding:7px}.board-empty{opacity:.3}.board-rnd{font-size:9px;color:#777;font-weight:900}.board-player{font-size:10px;font-weight:900;line-height:1.15}.board-pos{font-size:9px;color:var(--green);margin-top:3px}
.answer{border-left:5px solid var(--green);background:#17191d;border-radius:18px;padding:18px;margin-top:12px;font-size:15px;line-height:1.55}.watch-chip{display:inline-block;background:#242730;border:1px solid #3b3e48;padding:6px 9px;border-radius:999px;margin:3px;font-size:11px;font-weight:800}
@media(max-width:720px){.block-container{padding:10px 12px 60px!important}.hero{padding:18px;border-radius:20px}.hero h1{font-size:28px}.metric-grid{grid-template-columns:repeat(2,1fr)}div[data-testid="stHorizontalBlock"]:has(.st-key-nav_intel){gap:4px}.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_watch button,.st-key-nav_history button{min-height:70px!important;padding:5px 3px!important;font-size:10px!important;border-radius:15px!important}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_rankings() -> pd.DataFrame:
    df = pd.read_csv(RANKINGS_PATH)
    for col in ["adp", "consensus_adp", "overall_rank", "position_rank", "bye"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["position"] = df["position"].astype(str).str.upper().str.strip()
    return df.dropna(subset=["player_name", "position"]).sort_values(["adp", "overall_rank"], na_position="last").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def history_frame() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as con:
            return pd.read_sql_query("SELECT * FROM draft_roi_scores", con)
    except Exception:
        return pd.DataFrame()


def history_summary(df: pd.DataFrame) -> str:
    if df.empty:
        return "Historical league database unavailable."
    bits = [f"draft_roi_scores contains {len(df):,} verified historical draft rows"]
    if "season" in df.columns:
        bits.append(f"seasons {int(df['season'].min())}-{int(df['season'].max())}")
    if "league_name" in df.columns:
        bits.append("leagues: " + ", ".join(map(str, sorted(df["league_name"].dropna().unique())[:8])))
    return "; ".join(bits) + "."


def secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return os.getenv(name, default)


def api_key() -> str:
    return secret("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))


def init_state() -> None:
    defaults: dict[str, Any] = {
        "page": "Shiva Intelligence",
        "watchlist": [],
        "draft": None,
        "last_shiva_answer": "",
        "draft_recommendation": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


rankings = load_rankings()
history = history_frame()
init_state()

st.markdown('<div class="navlabel">SHIVA TOOLS</div>', unsafe_allow_html=True)
nav = [
    ("📊\nShiva\nIntelligence", "Shiva Intelligence", "nav_intel"),
    ("📋\nDraft\nCoach", "Draft Coach", "nav_coach"),
    ("🧩\nMock\nDraft", "Mock Draft", "nav_mock"),
    ("⭐\nMy\nPlayers", "My Players", "nav_watch"),
    ("🏛️\nLeague\nHistory", "League History", "nav_history"),
]
cols = st.columns(len(nav))
for col, (label, page, key) in zip(cols, nav):
    with col:
        if st.button(label, key=key, type="primary" if st.session_state.page == page else "secondary", use_container_width=True):
            st.session_state.page = page
            st.rerun()


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="hero"><div class="kicker">{kicker}</div><h1>{title}</h1><div class="muted">{subtitle}</div></div>', unsafe_allow_html=True)


def draft_context() -> dict | None:
    d = st.session_state.draft
    if not d:
        return None
    cfg = d["config"]
    avail = available_players(rankings, d["picks"]).head(25)
    return {
        "teams": cfg["teams"], "rounds": cfg["rounds"], "user_slot": cfg["user_slot"], "scoring": cfg["scoring"],
        "next_pick": d["next_pick"],
        "user_roster": user_roster(d["picks"], cfg["user_slot"]),
        "roster_counts": roster_counts(d["picks"], cfg["user_slot"]),
        "top_available": avail[["player_name", "position", "team", "adp", "position_rank"]].where(pd.notna(avail), None).to_dict("records"),
        "recent_picks": d["picks"][-18:],
        "watchlist": st.session_state.watchlist,
    }


def render_ask_shiva(prefill: str = "") -> None:
    st.markdown('<div class="panel"><div class="kicker">🧠 ASK SHIVA</div><div class="panel-title">Ask Shiva GPT</div><div class="small">ChatGPT receives your question plus the app\'s rankings, watchlist and live draft state.</div></div>', unsafe_allow_html=True)
    with st.form("ask_shiva_form"):
        q = st.text_area("What do you want to know?", value=prefill, placeholder="Example: I already drafted two RBs. Who should I take at 3.04?", height=88)
        submit = st.form_submit_button("ASK SHIVA GPT", use_container_width=True)
    if submit and q.strip():
        if not api_key():
            st.error("Ask Shiva is wired correctly, but Streamlit needs OPENAI_API_KEY in App → Settings → Secrets.")
        else:
            context = build_context(rankings=rankings, watchlist=st.session_state.watchlist, draft=draft_context(), history_summary=history_summary(history))
            try:
                with st.spinner("Shiva is analyzing the board..."):
                    st.session_state.last_shiva_answer = ask_shiva(api_key(), secret("OPENAI_MODEL", MODEL), q.strip(), context)
            except Exception as exc:
                st.error(f"Shiva API error: {exc}")
    if st.session_state.last_shiva_answer:
        st.markdown(f'<div class="answer">{st.session_state.last_shiva_answer}</div>', unsafe_allow_html=True)


if st.session_state.page == "Shiva Intelligence":
    hero("📊 SHIVA INTELLIGENCE", "Your Fantasy Draft Command Center", "Ask questions, pressure-test decisions and combine current ESPN-style ADP with your live draft state instead of using preset fantasy verdicts.")
    render_ask_shiva()
    st.markdown('<div class="panel-title" style="margin-top:26px">Quick Intelligence</div>', unsafe_allow_html=True)
    top_rb = rankings[rankings.position.eq("RB")].head(1)
    top_wr = rankings[rankings.position.eq("WR")].head(1)
    st.markdown(f'''<div class="metric-grid"><div class="metric"><div class="metric-label">Players Loaded</div><div class="metric-value green">{len(rankings)}</div></div><div class="metric"><div class="metric-label">Historical Rows</div><div class="metric-value blue">{len(history):,}</div></div><div class="metric"><div class="metric-label">Top RB</div><div class="metric-value" style="font-size:15px">{top_rb.iloc[0].player_name if not top_rb.empty else '—'}</div></div><div class="metric"><div class="metric-label">Top WR</div><div class="metric-value" style="font-size:15px">{top_wr.iloc[0].player_name if not top_wr.empty else '—'}</div></div></div>''', unsafe_allow_html=True)

elif st.session_state.page == "Draft Coach":
    hero("📋 DRAFT COACH", "Build Your 2026 Draft Plan", "Turn draft slot, positional priorities and player targets into a round-by-round plan you can actually use during a draft.")
    c1, c2, c3 = st.columns(3)
    with c1: teams = st.selectbox("Teams", [10, 12], index=0)
    with c2: slot = st.number_input("Draft Position", 1, int(teams), min(4, int(teams)), 1)
    with c3: rounds = st.selectbox("Rounds", [15, 16, 17, 18], index=1)
    schedule = slot_picks(int(slot), int(teams), int(rounds))
    st.markdown(f'''<div class="metric-grid"><div class="metric"><div class="metric-label">Round 1</div><div class="metric-value green">#{schedule[0]}</div></div><div class="metric"><div class="metric-label">Round 2</div><div class="metric-value blue">#{schedule[1]}</div></div><div class="metric"><div class="metric-label">Round 3</div><div class="metric-value">#{schedule[2]}</div></div><div class="metric"><div class="metric-label">Turn Gap</div><div class="metric-value">{schedule[1]-schedule[0]}</div></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="panel-title">Players likely around your first four picks</div><div class="small">A practical planning window based on current ADP, not a guarantee of availability.</div></div>', unsafe_allow_html=True)
    for pick in schedule[:4]:
        window = rankings[(rankings.adp >= max(1, pick-5)) & (rankings.adp <= pick+8)].head(7)
        with st.expander(f"Pick #{pick}", expanded=pick == schedule[0]):
            st.dataframe(window[["player_name", "position", "team", "adp", "position_rank"]], hide_index=True, use_container_width=True)
    render_ask_shiva(f"I'm drafting from slot {int(slot)} in a {int(teams)}-team PPR league. Build me a smart plan for my first six rounds using the current board.")

elif st.session_state.page == "My Players":
    hero("⭐ MY PLAYERS", "Targets, Favorites & Watch List", "Build the short list you want visible during every mock. Your watch list automatically becomes context for Ask Shiva.")
    options = rankings.player_name.tolist()
    selected = st.multiselect("Add players", options, default=st.session_state.watchlist, placeholder="Search a player")
    st.session_state.watchlist = selected
    if not selected:
        st.info("Add a few players you want to track. They'll be highlighted in the mock draft player pool.")
    else:
        watch = rankings[rankings.player_name.isin(selected)].copy().sort_values("adp")
        st.dataframe(watch[["player_name", "position", "team", "adp", "position_rank", "bye"]], hide_index=True, use_container_width=True)
        render_ask_shiva("Which of the players on my watch list are the best values at current ADP, and where would you target them?")

elif st.session_state.page == "League History":
    hero("🏛️ SHIVA LEAGUE HISTORY", "Search Historical Drafts", "Use the verified league database to see who was drafted, where they were selected and how they finished.")
    if history.empty:
        st.warning("The historical database could not be read.")
    else:
        filt = history.copy()
        c1, c2, c3 = st.columns(3)
        with c1:
            leagues = ["All"] + sorted(map(str, filt.get("league_name", pd.Series(dtype=str)).dropna().unique()))
            league = st.selectbox("League", leagues)
        with c2:
            seasons = ["All"] + sorted([int(x) for x in filt.get("season", pd.Series(dtype=float)).dropna().unique()], reverse=True)
            season = st.selectbox("Season", seasons)
        with c3:
            positions = ["All"] + sorted(map(str, filt.get("position", pd.Series(dtype=str)).dropna().unique()))
            pos = st.selectbox("Position", positions)
        search = st.text_input("Search player", placeholder="Christian McCaffrey")
        if league != "All" and "league_name" in filt: filt = filt[filt.league_name.astype(str).eq(str(league))]
        if season != "All" and "season" in filt: filt = filt[filt.season.eq(int(season))]
        if pos != "All" and "position" in filt: filt = filt[filt.position.astype(str).eq(str(pos))]
        if search and "player_name" in filt: filt = filt[filt.player_name.astype(str).str.contains(search, case=False, na=False)]
        preferred = [c for c in ["season","league_name","manager_name","player_name","position","round","overall_pick","ppg","position_finish_total","fantasy_points_ppr"] if c in filt.columns]
        sort_cols = [c for c in ["season","overall_pick"] if c in preferred]
        shown = filt[preferred]
        if sort_cols:
            shown = shown.sort_values(sort_cols, ascending=[False if c == "season" else True for c in sort_cols])
        st.dataframe(shown.head(300), hide_index=True, use_container_width=True)

elif st.session_state.page == "Mock Draft":
    hero("🧩 MOCK DRAFT", "2026 Live Interactive Draft Room", "One draft state. Switch between available players, your roster and a Sleeper-style draft board without losing a pick.")
    if not st.session_state.draft:
        with st.form("mock_setup"):
            c1, c2, c3, c4 = st.columns(4)
            with c1: teams = st.selectbox("Teams", [10, 12])
            with c2: slot = st.number_input("Draft Position", 1, 12, 4, 1)
            with c3: rounds = st.selectbox("Rounds", [15,16,17,18], index=1)
            with c4: scoring = st.selectbox("Scoring", ["PPR", "Half PPR", "Standard"])
            start = st.form_submit_button("START MOCK DRAFT", use_container_width=True)
        if start:
            slot = min(int(slot), int(teams))
            cfg = DraftConfig(teams=int(teams), rounds=int(rounds), user_slot=slot, scoring=scoring)
            picks: list[dict] = []
            picks, next_pick = advance_cpus(rankings, picks, 1, cfg)
            st.session_state.draft = {"config": cfg.__dict__, "picks": picks, "next_pick": next_pick}
            st.rerun()
    else:
        d = st.session_state.draft
        cfg = DraftConfig(**d["config"])
        total = cfg.teams * cfg.rounds
        done = d["next_pick"] > total
        roster = user_roster(d["picks"], cfg.user_slot)
        counts = roster_counts(d["picks"], cfg.user_slot)
        st.markdown(f'''<div class="metric-grid"><div class="metric"><div class="metric-label">On The Clock</div><div class="metric-value green">{'DONE' if done else '#'+str(d['next_pick'])}</div></div><div class="metric"><div class="metric-label">Your Team</div><div class="metric-value blue">{cfg.user_slot}</div></div><div class="metric"><div class="metric-label">Roster</div><div class="metric-value">{len(roster)}</div></div><div class="metric"><div class="metric-label">RB / WR</div><div class="metric-value">{counts['RB']} / {counts['WR']}</div></div></div>''', unsafe_allow_html=True)
        reset_col, rec_col = st.columns([1,2])
        with reset_col:
            if st.button("Reset Draft", use_container_width=True):
                st.session_state.draft = None; st.session_state.draft_recommendation = ""; st.rerun()
        with rec_col:
            if not done and st.button("🧠 WHO SHOULD I PICK?", type="primary", use_container_width=True):
                board = score_board(rankings, d["picks"], cfg.user_slot, d["next_pick"]).head(8)
                if api_key():
                    q = "I am on the clock right now. Who should I pick? Give me one primary pick, two alternatives, and explain the roster-construction logic."
                    context = build_context(rankings=rankings, watchlist=st.session_state.watchlist, draft=draft_context(), history_summary=history_summary(history))
                    try:
                        st.session_state.draft_recommendation = ask_shiva(api_key(), secret("OPENAI_MODEL", MODEL), q, context)
                    except Exception as exc:
                        st.session_state.draft_recommendation = f"AI unavailable ({exc}). Draft engine top choice: {board.iloc[0].player_name}."
                else:
                    top = board.iloc[0]
                    st.session_state.draft_recommendation = f"Draft engine: **{top.player_name} ({top.position})** is the best fit on the current board. Add OPENAI_API_KEY to Streamlit Secrets for the full Shiva GPT explanation."
        if st.session_state.draft_recommendation:
            st.info(st.session_state.draft_recommendation)
        tabs = st.tabs(["Players", "Draft Board", "My Roster"])
        with tabs[0]:
            if done:
                st.success("Mock draft complete.")
            else:
                pos_filter = st.segmented_control("Position", ["ALL","RB","WR","QB","TE"], default="ALL")
                avail = score_board(rankings, d["picks"], cfg.user_slot, d["next_pick"])
                if pos_filter and pos_filter != "ALL": avail = avail[avail.position.eq(pos_filter)]
                query = st.text_input("Search available players", key="mock_search", placeholder="Search name or team")
                if query:
                    avail = avail[avail.player_name.str.contains(query, case=False, na=False) | avail.team.astype(str).str.contains(query, case=False, na=False)]
                for idx, row in avail.head(18).iterrows():
                    left, right = st.columns([4,1])
                    star = "⭐ " if row.player_name in st.session_state.watchlist else ""
                    with left:
                        st.markdown(f'<div class="player-card"><div class="pos">{row.position}</div><div><div class="player-name">{star}{row.player_name}</div><div class="player-sub">{row.team} · {row.position}{int(row.position_rank) if pd.notna(row.position_rank) else ""}</div></div><div class="adp">ADP {row.adp:.1f}</div></div>', unsafe_allow_html=True)
                    with right:
                        if st.button("DRAFT", key=f"draft_{idx}", type="primary", use_container_width=True):
                            if pick_team(d["next_pick"], cfg.teams) != cfg.user_slot:
                                st.error("Not your pick yet.")
                            else:
                                d["picks"].append(make_pick(row.to_dict(), d["next_pick"], cfg.teams))
                                d["next_pick"] += 1
                                d["picks"], d["next_pick"] = advance_cpus(rankings, d["picks"], d["next_pick"], cfg)
                                st.session_state.draft = d
                                st.session_state.draft_recommendation = ""
                                st.rerun()
        with tabs[1]:
            matrix = board_matrix(d["picks"], cfg.teams, cfg.rounds)
            cells = []
            for rnd, row in enumerate(matrix, 1):
                for team, pick in enumerate(row, 1):
                    if pick:
                        cells.append(f'<div class="board-cell"><div class="board-rnd">R{rnd} · T{team}</div><div class="board-player">{pick["player_name"]}</div><div class="board-pos">{pick["position"]}</div></div>')
                    else:
                        cells.append(f'<div class="board-cell board-empty"><div class="board-rnd">R{rnd} · T{team}</div><div class="board-player">—</div></div>')
            st.markdown(f'<div class="board-wrap"><div class="board" style="grid-template-columns:repeat({cfg.teams},minmax(82px,1fr))">{"".join(cells)}</div></div>', unsafe_allow_html=True)
        with tabs[2]:
            if not roster: st.info("You have not drafted a player yet.")
            else: st.dataframe(pd.DataFrame(roster)[["round","overall","player_name","position","nfl_team","adp"]], hide_index=True, use_container_width=True)

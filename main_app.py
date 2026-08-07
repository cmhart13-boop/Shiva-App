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

st.set_page_config(
    page_title="Shiva Draft Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = r"""
<style>
:root{--bg:#090a0d;--panel:#15171c;--line:#30343d;--text:#f7f8fb;--muted:#9398a3;--green:#30e95b;--blue:#5b9dff;--red:#ff5d6c;--gold:#ffbd45}
html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;-webkit-font-smoothing:antialiased}
html,body{overflow-x:hidden!important;background:var(--bg)!important}.stApp{background:var(--bg);color:var(--text);overflow-x:hidden!important}
.block-container{width:100%!important;max-width:480px!important;padding:8px 10px 70px!important;margin:0 auto!important}
#MainMenu,footer,header{visibility:hidden!important;height:0!important}[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
h1,h2,h3,p,label,.stMarkdown{color:var(--text)}
.mobile-head{position:sticky;top:0;z-index:50;margin:0 -10px 9px;padding:12px 10px 10px;background:rgba(9,10,13,.96);backdrop-filter:blur(14px);border-bottom:1px solid #20232a}.mobile-title{font-size:17px;line-height:1;font-weight:1000;text-align:center}.mobile-sub{font-size:9px;color:#747a86;font-weight:900;letter-spacing:.14em;text-transform:uppercase;text-align:center;margin-top:5px}.navlabel{color:#777d88;font-size:9px;font-weight:1000;letter-spacing:.14em;text-transform:uppercase;margin:5px 0 7px}
div[data-testid="stHorizontalBlock"]{gap:6px!important;align-items:stretch!important}div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]{min-width:0!important}
.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_watch button,.st-key-nav_history button{width:100%!important;min-height:66px!important;padding:6px 3px!important;border-radius:15px!important;background:linear-gradient(180deg,#1d2026,#17191e)!important;border:1px solid #2d313a!important;color:#dadde5!important;font-weight:950!important;font-size:10px!important;white-space:pre-line!important;line-height:1.12!important;box-shadow:none!important}
.st-key-nav_intel button p,.st-key-nav_coach button p,.st-key-nav_mock button p,.st-key-nav_watch button p,.st-key-nav_history button p{white-space:pre-line!important;text-align:center!important;color:inherit!important;line-height:1.12!important}
.st-key-nav_intel button[kind="primary"],.st-key-nav_coach button[kind="primary"],.st-key-nav_mock button[kind="primary"],.st-key-nav_watch button[kind="primary"],.st-key-nav_history button[kind="primary"]{color:#fff!important;border-color:var(--green)!important;box-shadow:inset 0 -3px 0 var(--green)!important}
.hero{padding:15px;border:1px solid var(--line);border-radius:19px;background:linear-gradient(145deg,#1b1e24,#111319);margin:10px 0 11px;box-shadow:0 10px 24px rgba(0,0,0,.24)}.kicker{color:var(--green);font-weight:1000;letter-spacing:.11em;text-transform:uppercase;font-size:10px}.hero h1{font-size:24px;line-height:1.04;margin:7px 0 8px;font-weight:1000;letter-spacing:-.03em}.muted{color:var(--muted);font-size:12px;line-height:1.45}
.panel{background:#15171c;border:1px solid var(--line);border-radius:17px;padding:14px;margin:9px 0}.panel-title{font-size:17px;font-weight:1000;line-height:1.15;margin-bottom:4px}.small{font-size:11.5px;color:var(--muted);line-height:1.4}
.metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:10px 0}.metric{background:#191c22;border:1px solid #2b3039;border-radius:14px;padding:11px;min-height:76px}.metric-label{font-size:9px;color:#878d99;font-weight:950;text-transform:uppercase}.metric-value{font-size:20px;line-height:1.05;font-weight:1000;margin-top:8px;word-break:break-word}.green{color:var(--green)}.blue{color:var(--blue)}.red{color:var(--red)}
[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{min-height:48px!important;background:#1d2129!important;border:1px solid #343a46!important;color:#fff!important;border-radius:14px!important;font-size:16px!important}[data-testid="stTextArea"] textarea{min-height:104px!important;line-height:1.4!important;padding:12px!important}.stButton button,div[data-testid="stFormSubmitButton"] button{min-height:48px!important;border-radius:14px!important;font-weight:950!important;font-size:13px!important}.stButton button[kind="primary"],div[data-testid="stFormSubmitButton"] button[kind="primary"]{background:var(--green)!important;color:#071108!important;border-color:var(--green)!important}
[data-testid="stSegmentedControl"]{width:100%!important;overflow:visible!important}[data-testid="stSegmentedControl"] button{min-height:42px!important;padding:5px 8px!important}[data-testid="stTabs"] button{font-size:12px!important;font-weight:900!important;min-height:44px!important;padding:6px 8px!important}
.player-card{display:grid;grid-template-columns:40px minmax(0,1fr) auto;gap:9px;align-items:center;background:#181b20;border:1px solid #2c313a;border-radius:14px;padding:10px;margin:6px 0}.pos{font-size:10px;font-weight:1000;border-radius:9px;padding:8px 4px;text-align:center;background:#252a33}.player-name{font-weight:1000;font-size:14px;line-height:1.16}.player-sub{font-size:10px;color:#9297a2;margin-top:3px}.adp{font-size:11px;color:#c4c7ce;font-weight:900;white-space:nowrap}.answer{border-left:4px solid var(--green);background:#15181d;border-radius:16px;padding:14px;margin-top:10px;font-size:13.5px;line-height:1.55}
[data-testid="stDataFrame"]{width:100%!important;border:1px solid #2e333d!important;border-radius:14px!important;overflow:hidden!important}.board-wrap{overflow-x:auto!important;-webkit-overflow-scrolling:touch;border:1px solid #2e333d;border-radius:16px;background:#111318;padding:8px;margin:4px 0 10px;max-width:100%}.board{display:grid;gap:5px;min-width:760px}.board-cell{min-height:54px;background:#1c1f25;border:1px solid #303640;border-radius:9px;padding:6px}.board-empty{opacity:.32}.board-rnd{font-size:8px;color:#7f8590;font-weight:950}.board-player{font-size:9px;font-weight:950;line-height:1.13}.board-pos{font-size:8px;color:var(--green);margin-top:3px;font-weight:900}
@media(max-width:390px){.block-container{padding-left:8px!important;padding-right:8px!important}.hero h1{font-size:22px}.metric-value{font-size:19px}.st-key-nav_intel button,.st-key-nav_coach button,.st-key-nav_mock button,.st-key-nav_watch button,.st-key-nav_history button{font-size:9.3px!important;min-height:63px!important}.player-card{grid-template-columns:36px minmax(0,1fr) auto;padding:9px 8px}.player-name{font-size:13px}}
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
    defaults: dict[str, Any] = {"page":"Shiva Intelligence","watchlist":[],"draft":None,"last_shiva_answer":"","draft_recommendation":""}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


rankings = load_rankings()
history = history_frame()
init_state()

st.markdown('<div class="mobile-head"><div class="mobile-title">🏆 SHIVA DRAFT INTELLIGENCE</div><div class="mobile-sub">2026 Fantasy Draft Command Center</div></div>', unsafe_allow_html=True)
st.markdown('<div class="navlabel">SHIVA TOOLS</div>', unsafe_allow_html=True)
nav_rows = [
    [("📊\nShiva\nIntel","Shiva Intelligence","nav_intel"),("📋\nDraft\nCoach","Draft Coach","nav_coach"),("🧩\nMock\nDraft","Mock Draft","nav_mock")],
    [("⭐\nMy\nPlayers","My Players","nav_watch"),("🏛️\nLeague\nHistory","League History","nav_history")],
]
for group in nav_rows:
    cols = st.columns(len(group))
    for col, (label, page, key) in zip(cols, group):
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
    return {"teams":cfg["teams"],"rounds":cfg["rounds"],"user_slot":cfg["user_slot"],"scoring":cfg["scoring"],"next_pick":d["next_pick"],"user_roster":user_roster(d["picks"],cfg["user_slot"]),"roster_counts":roster_counts(d["picks"],cfg["user_slot"]),"top_available":avail[["player_name","position","team","adp","position_rank"]].where(pd.notna(avail),None).to_dict("records"),"recent_picks":d["picks"][-18:],"watchlist":st.session_state.watchlist}


def render_ask_shiva(prefill: str = "") -> None:
    st.markdown('<div class="panel"><div class="kicker">🧠 ASK SHIVA</div><div class="panel-title">Ask Shiva GPT</div><div class="small">Your question, rankings, watch list and live draft state all go to Shiva together.</div></div>', unsafe_allow_html=True)
    with st.form("ask_shiva_form"):
        q = st.text_area("What do you want to know?", value=prefill, placeholder="Example: I already drafted two RBs. Who should I take at 3.04?", height=104)
        submit = st.form_submit_button("ASK SHIVA GPT", use_container_width=True)
    if submit and q.strip():
        if not api_key():
            st.error("Add OPENAI_API_KEY in Streamlit → App Settings → Secrets to activate Ask Shiva.")
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
    hero("📊 SHIVA INTELLIGENCE", "Your Draft Command Center", "Ask questions, pressure-test decisions and combine current ADP with your live draft state.")
    render_ask_shiva()
    top_rb = rankings[rankings.position.eq("RB")].head(1)
    top_wr = rankings[rankings.position.eq("WR")].head(1)
    st.markdown(f'''<div class="metric-grid"><div class="metric"><div class="metric-label">Players Loaded</div><div class="metric-value green">{len(rankings)}</div></div><div class="metric"><div class="metric-label">Historical Rows</div><div class="metric-value blue">{len(history):,}</div></div><div class="metric"><div class="metric-label">Top RB</div><div class="metric-value" style="font-size:14px">{top_rb.iloc[0].player_name if not top_rb.empty else '—'}</div></div><div class="metric"><div class="metric-label">Top WR</div><div class="metric-value" style="font-size:14px">{top_wr.iloc[0].player_name if not top_wr.empty else '—'}</div></div></div>''', unsafe_allow_html=True)

elif st.session_state.page == "Draft Coach":
    hero("📋 DRAFT COACH", "Build Your 2026 Draft Plan", "Set your slot and see exact turns, likely player windows and a Shiva-built plan.")
    c1,c2 = st.columns(2)
    with c1: teams = st.selectbox("Teams", [10,12], index=0)
    with c2: slot = st.number_input("Draft Position",1,int(teams),min(4,int(teams)),1)
    rounds = st.selectbox("Rounds",[15,16,17,18],index=1)
    schedule = slot_picks(int(slot),int(teams),int(rounds))
    st.markdown(f'''<div class="metric-grid"><div class="metric"><div class="metric-label">Round 1</div><div class="metric-value green">#{schedule[0]}</div></div><div class="metric"><div class="metric-label">Round 2</div><div class="metric-value blue">#{schedule[1]}</div></div><div class="metric"><div class="metric-label">Round 3</div><div class="metric-value">#{schedule[2]}</div></div><div class="metric"><div class="metric-label">Turn Gap</div><div class="metric-value">{schedule[1]-schedule[0]}</div></div></div>''', unsafe_allow_html=True)
    for pick in schedule[:4]:
        window = rankings[(rankings.adp >= max(1,pick-5)) & (rankings.adp <= pick+8)].head(7)
        with st.expander(f"Pick #{pick}", expanded=pick == schedule[0]):
            st.dataframe(window[["player_name","position","team","adp","position_rank"]], hide_index=True, use_container_width=True)
    render_ask_shiva(f"I'm drafting from slot {int(slot)} in a {int(teams)}-team PPR league. Build me a smart plan for my first six rounds using the current board.")

elif st.session_state.page == "My Players":
    hero("⭐ MY PLAYERS", "Targets & Watch List", "Build the players you want tracked during every mock and included in Shiva's context.")
    selected = st.multiselect("Add players", rankings.player_name.tolist(), default=st.session_state.watchlist, placeholder="Search a player")
    st.session_state.watchlist = selected
    if not selected:
        st.info("Add players you want to track. They'll be highlighted in the mock draft pool.")
    else:
        watch = rankings[rankings.player_name.isin(selected)].copy().sort_values("adp")
        st.dataframe(watch[["player_name","position","team","adp","position_rank","bye"]], hide_index=True, use_container_width=True)
        render_ask_shiva("Which players on my watch list are the best values at current ADP, and where should I target them?")

elif st.session_state.page == "League History":
    hero("🏛️ LEAGUE HISTORY", "Search Historical Drafts", "Search the verified league database by league, season, position or player.")
    if history.empty:
        st.warning("The historical database could not be read.")
    else:
        filt = history.copy()
        c1,c2 = st.columns(2)
        with c1:
            leagues = ["All"] + sorted(map(str,filt.get("league_name",pd.Series(dtype=str)).dropna().unique()))
            league = st.selectbox("League",leagues)
        with c2:
            seasons = ["All"] + sorted([int(x) for x in filt.get("season",pd.Series(dtype=float)).dropna().unique()], reverse=True)
            season = st.selectbox("Season",seasons)
        positions = ["All"] + sorted(map(str,filt.get("position",pd.Series(dtype=str)).dropna().unique()))
        pos = st.selectbox("Position",positions)
        search = st.text_input("Search player",placeholder="Christian McCaffrey")
        if league != "All" and "league_name" in filt: filt = filt[filt.league_name.astype(str).eq(str(league))]
        if season != "All" and "season" in filt: filt = filt[filt.season.eq(int(season))]
        if pos != "All" and "position" in filt: filt = filt[filt.position.astype(str).eq(str(pos))]
        if search and "player_name" in filt: filt = filt[filt.player_name.astype(str).str.contains(search,case=False,na=False)]
        preferred = [c for c in ["season","league_name","manager_name","player_name","position","round","overall_pick","ppg","position_finish_total","fantasy_points_ppr"] if c in filt.columns]
        shown = filt[preferred]
        sort_cols = [c for c in ["season","overall_pick"] if c in preferred]
        if sort_cols: shown = shown.sort_values(sort_cols, ascending=[False if c == "season" else True for c in sort_cols])
        st.dataframe(shown.head(300), hide_index=True, use_container_width=True)

elif st.session_state.page == "Mock Draft":
    hero("🧩 MOCK DRAFT", "2026 Live Draft Room", "Available players, your roster, full board and one-tap Shiva advice in one mobile draft room.")
    if not st.session_state.draft:
        with st.form("mock_setup"):
            c1,c2 = st.columns(2)
            with c1: teams = st.selectbox("Teams",[10,12])
            with c2: slot = st.number_input("Draft Position",1,12,4,1)
            c3,c4 = st.columns(2)
            with c3: rounds = st.selectbox("Rounds",[15,16,17,18],index=1)
            with c4: scoring = st.selectbox("Scoring",["PPR","Half PPR","Standard"])
            start = st.form_submit_button("START MOCK DRAFT",use_container_width=True)
        if start:
            slot = min(int(slot),int(teams))
            cfg = DraftConfig(teams=int(teams),rounds=int(rounds),user_slot=slot,scoring=scoring)
            picks: list[dict] = []
            picks,next_pick = advance_cpus(rankings,picks,1,cfg)
            st.session_state.draft = {"config":cfg.__dict__,"picks":picks,"next_pick":next_pick}
            st.rerun()
    else:
        d = st.session_state.draft
        cfg = DraftConfig(**d["config"])
        total = cfg.teams * cfg.rounds
        done = d["next_pick"] > total
        roster = user_roster(d["picks"],cfg.user_slot)
        counts = roster_counts(d["picks"],cfg.user_slot)
        st.markdown(f'''<div class="metric-grid"><div class="metric"><div class="metric-label">On The Clock</div><div class="metric-value green">{'DONE' if done else '#'+str(d['next_pick'])}</div></div><div class="metric"><div class="metric-label">Your Slot</div><div class="metric-value blue">{cfg.user_slot}</div></div><div class="metric"><div class="metric-label">Roster</div><div class="metric-value">{len(roster)}</div></div><div class="metric"><div class="metric-label">RB / WR</div><div class="metric-value">{counts['RB']} / {counts['WR']}</div></div></div>''', unsafe_allow_html=True)
        if not done and st.button("🧠 WHO SHOULD I PICK?",type="primary",use_container_width=True):
            board = score_board(rankings,d["picks"],cfg.user_slot,d["next_pick"]).head(8)
            if api_key():
                q = "I am on the clock right now. Who should I pick? Give me one primary pick, two alternatives, and explain the roster-construction logic."
                context = build_context(rankings=rankings,watchlist=st.session_state.watchlist,draft=draft_context(),history_summary=history_summary(history))
                try:
                    st.session_state.draft_recommendation = ask_shiva(api_key(),secret("OPENAI_MODEL",MODEL),q,context)
                except Exception as exc:
                    st.session_state.draft_recommendation = f"AI unavailable ({exc}). Draft engine top choice: {board.iloc[0].player_name}."
            else:
                top = board.iloc[0]
                st.session_state.draft_recommendation = f"Draft engine: **{top.player_name} ({top.position})** is the best fit on the board. Add OPENAI_API_KEY for the full Shiva explanation."
        if st.session_state.draft_recommendation: st.info(st.session_state.draft_recommendation)
        if st.button("Reset Draft",use_container_width=True):
            st.session_state.draft = None; st.session_state.draft_recommendation = ""; st.rerun()
        tabs = st.tabs(["Players","Draft Board","My Roster"])
        with tabs[0]:
            if done:
                st.success("Mock draft complete.")
            else:
                pos_filter = st.segmented_control("Position",["ALL","RB","WR","QB","TE"],default="ALL")
                avail = score_board(rankings,d["picks"],cfg.user_slot,d["next_pick"])
                if pos_filter and pos_filter != "ALL": avail = avail[avail.position.eq(pos_filter)]
                query = st.text_input("Search available players",key="mock_search",placeholder="Search name or team")
                if query: avail = avail[avail.player_name.str.contains(query,case=False,na=False) | avail.team.astype(str).str.contains(query,case=False,na=False)]
                for idx,row in avail.head(18).iterrows():
                    star = "⭐ " if row.player_name in st.session_state.watchlist else ""
                    st.markdown(f'<div class="player-card"><div class="pos">{row.position}</div><div><div class="player-name">{star}{row.player_name}</div><div class="player-sub">{row.team} · {row.position}{int(row.position_rank) if pd.notna(row.position_rank) else ""}</div></div><div class="adp">ADP {row.adp:.1f}</div></div>', unsafe_allow_html=True)
                    if st.button(f"DRAFT {row.player_name}",key=f"draft_{idx}",type="primary",use_container_width=True):
                        if pick_team(d["next_pick"],cfg.teams) != cfg.user_slot:
                            st.error("Not your pick yet.")
                        else:
                            d["picks"].append(make_pick(row.to_dict(),d["next_pick"],cfg.teams)); d["next_pick"] += 1
                            d["picks"],d["next_pick"] = advance_cpus(rankings,d["picks"],d["next_pick"],cfg)
                            st.session_state.draft = d; st.session_state.draft_recommendation = ""; st.rerun()
        with tabs[1]:
            st.caption("Swipe inside the board to see every team. The rest of the app stays locked to phone width.")
            matrix = board_matrix(d["picks"],cfg.teams,cfg.rounds)
            cells = []
            for rnd,row in enumerate(matrix,1):
                for team,pick in enumerate(row,1):
                    if pick: cells.append(f'<div class="board-cell"><div class="board-rnd">R{rnd} · T{team}</div><div class="board-player">{pick["player_name"]}</div><div class="board-pos">{pick["position"]}</div></div>')
                    else: cells.append(f'<div class="board-cell board-empty"><div class="board-rnd">R{rnd} · T{team}</div><div class="board-player">—</div></div>')
            st.markdown(f'<div class="board-wrap"><div class="board" style="grid-template-columns:repeat({cfg.teams},minmax(72px,1fr))">{"".join(cells)}</div></div>',unsafe_allow_html=True)
        with tabs[2]:
            if not roster: st.info("You have not drafted a player yet.")
            else: st.dataframe(pd.DataFrame(roster)[["round","overall","player_name","position","nfl_team","adp"]],hide_index=True,use_container_width=True)

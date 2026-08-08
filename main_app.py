from __future__ import annotations

import base64
import os
import re
import sqlite3
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote

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
SPLASH_PATH = APP_DIR / "assets" / "shiva_splash.b64"
MODEL = "gpt-5-mini"

st.set_page_config(
    page_title="Shiva Intelligence",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "_shiva_splash_seen" not in st.session_state:
    try:
        splash_bytes = base64.b64decode(SPLASH_PATH.read_text(encoding="utf-8").strip())
        splash = st.empty()
        st.markdown(
            """
            <style>
              #MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
              .block-container{max-width:520px!important;padding:0!important;margin:0 auto!important}
              .stApp{background:#03105b!important}
              [data-testid="stImage"] img{width:100%!important;height:100vh!important;object-fit:cover!important;object-position:center top!important;display:block!important}
            </style>
            """,
            unsafe_allow_html=True,
        )
        with splash.container():
            st.image(splash_bytes, use_container_width=True)
        time.sleep(2.5)
        splash.empty()
        st.session_state["_shiva_splash_seen"] = True
    except Exception:
        st.session_state["_shiva_splash_seen"] = True

CSS = r"""
<style>
:root{--bg:#05080d;--bg2:#08111b;--panel:#0c1621;--panel2:#101d2b;--line:#1d3448;--text:#f7fbff;--muted:#99a9b8;--lime:#d7ff00;--cyan:#22c5ff;--blue:#168eea;--purple:#9c4cff;--gold:#ffb51f;--red:#e33036;--green:#38a844;--orange:#e96c00}
html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;-webkit-font-smoothing:antialiased}
html,body{overflow-x:hidden!important;background:var(--bg)!important}.stApp{background:radial-gradient(circle at 50% -8%,rgba(0,157,255,.12),transparent 34%),linear-gradient(180deg,#060a10 0%,#04070b 100%)!important;color:var(--text)!important;overflow-x:hidden!important}
.block-container{width:100%!important;max-width:520px!important;padding:8px 12px 86px!important;margin:0 auto!important}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}h1,h2,h3,p,label,.stMarkdown{color:var(--text)}
div[data-testid="stHorizontalBlock"]{gap:8px!important;align-items:stretch!important}div[data-testid="stHorizontalBlock"]>div[data-testid="stColumn"]{min-width:0!important}
.appbar{position:sticky;top:0;z-index:20;margin:0 -12px 12px;padding:12px 14px 10px;background:rgba(4,8,13,.94);backdrop-filter:blur(14px);border-bottom:1px solid #132537}.brand{font-size:18px;line-height:1;font-weight:1000;font-style:italic;color:var(--lime);letter-spacing:.06em;text-align:center}.brand-sub{font-size:11px;text-align:center;color:#d1d9e2;margin-top:4px}
.page-head{margin:8px 0 12px;text-align:center}.page-title{font-size:28px;font-weight:1000;line-height:1.02}.page-sub{font-size:14px;color:#d0d9e3;margin-top:5px}
.nav-card button{min-height:104px!important;border-radius:16px!important;border:1px solid #25435d!important;background:linear-gradient(145deg,#111b25,#09131c)!important;color:#fff!important;font-size:15px!important;font-weight:900!important;padding:10px!important;box-shadow:0 10px 24px rgba(0,0,0,.25)!important}.nav-card button p{white-space:pre-line!important;line-height:1.18!important}.nav-gold button{border-color:#8a5b00!important;background:linear-gradient(145deg,#201809,#0d1116)!important}.nav-purple button{border-color:#68318c!important;background:linear-gradient(145deg,#22132a,#0d1116)!important}.nav-cyan button{border-color:#145f7d!important;background:linear-gradient(145deg,#0c2630,#0d1116)!important}.nav-green button{border-color:#376f15!important;background:linear-gradient(145deg,#14270c,#0d1116)!important}.nav-pink button{border-color:#7b274d!important;background:linear-gradient(145deg,#25101a,#0d1116)!important}.nav-yellow button{border-color:#796316!important;background:linear-gradient(145deg,#211d09,#0d1116)!important}
.panel{background:linear-gradient(145deg,#101b27,#09121b);border:1px solid #213d54;border-radius:18px;padding:16px;margin:10px 0;box-shadow:0 10px 28px rgba(0,0,0,.2)}.panel-title{font-size:19px;font-weight:1000}.small{font-size:13px;color:var(--muted);line-height:1.45}.kicker{color:var(--lime);font-size:12px;font-weight:1000;letter-spacing:.1em;text-transform:uppercase}
.hero{background:linear-gradient(135deg,#0c1c31,#0b1120);border:1px solid #244965;border-radius:20px;padding:18px;margin:10px 0 14px;box-shadow:0 10px 32px rgba(0,82,150,.12)}.hero h1{font-size:29px;line-height:1.02;margin:8px 0 8px}.muted{font-size:14px;color:#a9b5c2;line-height:1.48}.ask-cta{background:linear-gradient(135deg,#08213c,#0b1728);border:1px solid #184d7c;border-radius:16px;padding:16px;margin:12px 0}.ask-title{font-size:19px;font-weight:1000}.ask-sub{font-size:12px;color:#bdc8d4;margin-top:4px}
[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stTextArea"] textarea{min-height:50px!important;background:#0c1722!important;border:1px solid #20374a!important;color:#fff!important;border-radius:12px!important;font-size:17px!important}[data-testid="stTextArea"] textarea{min-height:112px!important}.stButton button,div[data-testid="stFormSubmitButton"] button{min-height:48px!important;border-radius:12px!important;font-size:15px!important;font-weight:900!important}.stButton button[kind="primary"],div[data-testid="stFormSubmitButton"] button[kind="primary"]{background:linear-gradient(180deg,#dfff00,#b8e700)!important;color:#101500!important;border:1px solid #e5ff45!important}.stButton button[kind="secondary"]{background:#0f1a25!important;color:#fff!important;border:1px solid #263c4d!important}[data-testid="stSegmentedControl"] button{min-height:42px!important;font-size:14px!important;font-weight:900!important}[data-testid="stTabs"] button{font-size:14px!important;font-weight:900!important;min-height:46px!important}
.position-legend{display:flex;gap:7px;flex-wrap:wrap;margin:8px 0 10px}.pospill{padding:7px 13px;border-radius:10px;color:#fff;font-size:13px;font-weight:1000;border:1px solid rgba(255,255,255,.14)}.pos-QB{background:linear-gradient(180deg,#df3335,#9e191b)!important}.pos-RB{background:linear-gradient(180deg,#f28a13,#c55400)!important}.pos-WR{background:linear-gradient(180deg,#179eea,#086ab0)!important}.pos-TE{background:linear-gradient(180deg,#45b946,#247f28)!important}.pos-FLEX{background:linear-gradient(180deg,#9c54de,#65309b)!important}.pos-K{background:linear-gradient(180deg,#59636d,#303840)!important}.pos-DEF{background:linear-gradient(180deg,#8a551f,#5f3511)!important}
.player-line{display:grid;grid-template-columns:38px minmax(0,1fr) 46px;gap:8px;align-items:center;border-radius:11px;padding:9px 10px;margin:5px 0;border:1px solid rgba(255,255,255,.12);color:#fff}.player-line.QB{background:linear-gradient(90deg,#8e1a1d,#bc2d30)}.player-line.RB{background:linear-gradient(90deg,#c65300,#e87807)}.player-line.WR{background:linear-gradient(90deg,#0b619d,#147fbe)}.player-line.TE{background:linear-gradient(90deg,#237527,#3b9e3d)}.player-line.FLEX{background:linear-gradient(90deg,#60308e,#8c48c7)}.rank-circle{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:rgba(0,0,0,.18);font-size:13px;font-weight:1000}.player-main{font-size:15px;font-weight:1000;line-height:1.1}.player-meta{font-size:11px;opacity:.86;margin-top:3px}.player-adp{text-align:right;font-size:13px;font-weight:1000}
.board-wrap{overflow-x:auto!important;-webkit-overflow-scrolling:touch;border:1px solid #193047;border-radius:14px;background:#071019;padding:7px;margin:6px 0 10px}.board{display:grid;gap:4px;min-width:820px}.board-cell{min-height:62px;border-radius:7px;padding:6px;border:1px solid rgba(255,255,255,.12);color:#fff}.board-cell.QB{background:#8f1e22}.board-cell.RB{background:#c65b06}.board-cell.WR{background:#0d6b9f}.board-cell.TE{background:#2b802d}.board-cell.FLEX{background:#643398}.board-cell.K{background:#3a434b}.board-cell.DEF{background:#624017}.board-empty{background:#0d1720!important;opacity:.45}.board-rnd{font-size:9px;opacity:.8}.board-player{font-size:10px;font-weight:1000;line-height:1.1;margin-top:4px}.board-pos{font-size:9px;margin-top:3px;font-weight:900}.board-player a{color:#fff!important;text-decoration:none!important}
.profile-head{background:linear-gradient(145deg,#0d1a25,#09121a);border:1px solid #24445d;border-radius:18px;padding:16px;margin:10px 0}.profile-name{font-size:27px;font-weight:1000;text-align:center}.profile-meta{text-align:center;color:#c0cad4;font-size:13px;margin-top:4px}.profile-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:12px 0}.profile-stat{background:#0b1721;border:1px solid #1e3a4f;border-radius:12px;padding:10px 6px;text-align:center}.profile-val{font-size:21px;font-weight:1000}.profile-label{font-size:9px;color:#9aa8b5;margin-top:3px;font-weight:900}.week-row{display:grid;grid-template-columns:38px 48px 1fr 52px;gap:7px;align-items:center;border-bottom:1px solid #182d3d;padding:10px 3px;font-size:12px}.week-head{color:#9cacb9;font-size:10px;font-weight:900}.week-pts{font-weight:1000;color:#27c7ff;text-align:right}
.answer{background:#0d1a25;border:1px solid #25445c;border-left:4px solid var(--lime);border-radius:14px;padding:14px;font-size:15px;line-height:1.5;margin-top:10px}.bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:min(100%,520px);z-index:50;background:rgba(4,8,13,.96);border-top:1px solid #1b3345;padding:6px 12px 8px;backdrop-filter:blur(14px)}.bottom-grid{display:grid;grid-template-columns:repeat(5,1fr);text-align:center}.bn{font-size:11px;color:#c7d0d9}.bn .ico{font-size:20px;display:block;margin-bottom:2px}.bn.active{color:var(--lime);font-weight:1000}@media(max-width:390px){.page-title{font-size:26px}.brand{font-size:17px}.nav-card button{font-size:14px!important}.player-main{font-size:14px}.profile-val{font-size:19px}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_rankings() -> pd.DataFrame:
    df = pd.read_csv(RANKINGS_PATH)
    for col in ["adp", "consensus_adp", "overall_rank", "position_rank", "bye"]:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")
    df["position"] = df["position"].astype(str).str.upper().str.strip()
    return df.dropna(subset=["player_name", "position"]).sort_values(["adp", "overall_rank"], na_position="last").reset_index(drop=True)

@st.cache_data(show_spinner=False)
def history_frame() -> pd.DataFrame:
    if not DB_PATH.exists(): return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as con: return pd.read_sql_query("SELECT * FROM draft_roi_scores", con)
    except Exception: return pd.DataFrame()

def _norm(value: str) -> str:
    v = unicodedata.normalize("NFKD", str(value or "")).encode("ascii","ignore").decode().lower()
    v = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", v)
    return re.sub(r"[^a-z0-9]+", "", v)

@st.cache_data(show_spinner=False, ttl=3600)
def weekly_season(season: int) -> pd.DataFrame:
    url = f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_week_{int(season)}.csv"
    try: df = pd.read_csv(url, low_memory=False)
    except Exception: return pd.DataFrame()
    name_col = next((c for c in ["player_display_name","player_name","display_name","name"] if c in df.columns), None)
    if not name_col: return pd.DataFrame()
    df["_name_key"] = df[name_col].map(_norm)
    return df

def history_summary(df: pd.DataFrame) -> str:
    if df.empty: return "Historical league database unavailable."
    bits = [f"{len(df):,} verified historical draft rows"]
    if "season" in df.columns and not df["season"].dropna().empty: bits.append(f"seasons {int(df['season'].min())}-{int(df['season'].max())}")
    return "; ".join(bits) + "."

def secret(name: str, default: str = "") -> str:
    try: return str(st.secrets.get(name, default))
    except Exception: return os.getenv(name, default)

def api_key() -> str: return secret("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY",""))

def init_state():
    defaults: dict[str, Any] = {"page":"Home","watchlist":[],"draft":None,"last_shiva_answer":"","draft_recommendation":"","selected_player":"","profile_return_page":"Home"}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v

rankings = load_rankings(); history = history_frame(); init_state()
try:
    qp_player = st.query_params.get("player", "")
    if qp_player:
        st.session_state.selected_player = qp_player; st.session_state.profile_return_page = st.session_state.get("page","Home"); st.session_state.page = "Player Profile"; st.query_params.clear()
except Exception: pass

def go(page: str): st.session_state.page = page; st.rerun()
def open_profile(name: str, return_page: str | None = None): st.session_state.selected_player = str(name); st.session_state.profile_return_page = return_page or st.session_state.page; st.session_state.page = "Player Profile"; st.rerun()
def appbar(title: str = "SHIVA INTELLIGENCE", subtitle: str = "Your Draft Command Center"): st.markdown(f'<div class="appbar"><div class="brand">{title}</div><div class="brand-sub">{subtitle}</div></div>', unsafe_allow_html=True)
def bottom_nav(active: str):
    items = [("🏠","Home"),("🏈","Draft"),("👤","Players"),("👥","Team"),("•••","More")]; html = '<div class="bottom-nav"><div class="bottom-grid">'
    for ico,label in items:
        cls="bn active" if label==active else "bn"; html += f'<div class="{cls}"><span class="ico">{ico}</span>{label}</div>'
    st.markdown(html + '</div></div>', unsafe_allow_html=True)
def hero(kicker: str, title: str, subtitle: str): st.markdown(f'<div class="hero"><div class="kicker">{kicker}</div><h1>{title}</h1><div class="muted">{subtitle}</div></div>', unsafe_allow_html=True)

def draft_context() -> dict | None:
    d = st.session_state.draft
    if not d: return None
    cfg=d["config"]; avail=available_players(rankings,d["picks"]).head(25)
    return {"teams":cfg["teams"],"rounds":cfg["rounds"],"user_slot":cfg["user_slot"],"scoring":cfg["scoring"],"next_pick":d["next_pick"],"user_roster":user_roster(d["picks"],cfg["user_slot"]),"roster_counts":roster_counts(d["picks"],cfg["user_slot"]),"top_available":avail[["player_name","position","team","adp","position_rank"]].where(pd.notna(avail),None).to_dict("records"),"recent_picks":d["picks"][-18:],"watchlist":st.session_state.watchlist}

def render_ask_shiva(prefill: str = ""):
    st.markdown('<div class="ask-cta"><div class="ask-title">🤖 ASK SHIVA GPT</div><div class="ask-sub">Ask questions, get draft advice, pressure-test a pick.</div></div>', unsafe_allow_html=True)
    with st.form("ask_shiva_form"):
        q=st.text_area("What do you want to know?",value=prefill,placeholder="Who should I take at 3.04 after starting RB-RB?",height=110); submit=st.form_submit_button("ASK SHIVA GPT",use_container_width=True)
    if submit and q.strip():
        if not api_key(): st.warning("Ask Shiva is ready, but this deployment still needs your OPENAI_API_KEY in Streamlit → App Settings → Secrets.")
        else:
            context=build_context(rankings=rankings,watchlist=st.session_state.watchlist,draft=draft_context(),history_summary=history_summary(history))
            try:
                with st.spinner("Shiva is analyzing the board..."): st.session_state.last_shiva_answer=ask_shiva(api_key(),secret("OPENAI_MODEL",MODEL),q.strip(),context)
            except Exception as exc: st.error(f"Shiva API error: {exc}")
    if st.session_state.last_shiva_answer: st.markdown(f'<div class="answer">{st.session_state.last_shiva_answer}</div>',unsafe_allow_html=True)

def position_legend(): st.markdown('<div class="position-legend"><span class="pospill pos-QB">QB</span><span class="pospill pos-RB">RB</span><span class="pospill pos-WR">WR</span><span class="pospill pos-TE">TE</span><span class="pospill pos-FLEX">FLEX</span><span class="pospill pos-K">K</span><span class="pospill pos-DEF">DEF</span></div>',unsafe_allow_html=True)
def player_line(row, rank: int):
    pos=str(row.position).upper(); cls=pos if pos in {"QB","RB","WR","TE","FLEX"} else "FLEX"; adp=f"{float(row.adp):.1f}" if pd.notna(row.adp) else "—"; pr=f"{pos}{int(row.position_rank)}" if pd.notna(row.position_rank) else pos
    st.markdown(f'<div class="player-line {cls}"><div class="rank-circle">{rank}</div><div><div class="player-main">{row.player_name}</div><div class="player-meta">{row.team} · {pr}</div></div><div class="player-adp">{adp}</div></div>',unsafe_allow_html=True)

def render_player_profile(name: str):
    appbar(name.upper(), "Player Profile")
    if st.button("‹ Back",key="profile_back",use_container_width=True): go(st.session_state.get("profile_return_page","Home"))
    ranked=rankings[rankings.player_name.astype(str).eq(str(name))]; row=ranked.iloc[0] if not ranked.empty else None
    team=str(row.team) if row is not None and pd.notna(row.team) else "—"; pos=str(row.position) if row is not None and pd.notna(row.position) else "—"; adp=float(row.adp) if row is not None and pd.notna(row.adp) else None; pos_rank=int(row.position_rank) if row is not None and pd.notna(row.position_rank) else None
    hist=history.copy()
    if not hist.empty and "player_name" in hist.columns: hist=hist[hist.player_name.map(_norm).eq(_norm(name))]
    seasons=sorted({int(x) for x in hist.season.dropna().tolist() if 2000 <= int(x) <= 2025},reverse=True) if not hist.empty and "season" in hist.columns else []
    if not seasons: seasons=list(range(2025,2013,-1))
    season=st.selectbox("Season",seasons,key=f"profile_season_{_norm(name)}")
    weekly=weekly_season(int(season))
    if not weekly.empty:
        weekly=weekly[weekly["_name_key"].eq(_norm(name))].copy()
        if "season_type" in weekly.columns:
            reg=weekly[weekly.season_type.astype(str).str.upper().eq("REG")]
            if not reg.empty: weekly=reg
    fp_col="fantasy_points_ppr" if "fantasy_points_ppr" in weekly.columns else ("fantasy_points" if "fantasy_points" in weekly.columns else None); games=len(weekly); pts=pd.to_numeric(weekly[fp_col],errors="coerce").fillna(0) if fp_col and not weekly.empty else pd.Series(dtype=float); total=float(pts.sum()) if len(pts) else 0.0; ppg=float(pts.mean()) if len(pts) else 0.0; finish=f"{pos}{pos_rank}" if pos_rank else pos
    st.markdown(f'<div class="profile-head"><div class="profile-name">{name}</div><div class="profile-meta">{pos} · {team} · 2026 ADP {"—" if adp is None else f"{adp:.1f}"}</div><div class="profile-stats"><div class="profile-stat"><div class="profile-val" style="color:#ffb51f">{total:.1f}</div><div class="profile-label">FPTS</div></div><div class="profile-stat"><div class="profile-val" style="color:#ffb51f">{ppg:.1f}</div><div class="profile-label">PPG</div></div><div class="profile-stat"><div class="profile-val" style="color:#ffb51f">{games}</div><div class="profile-label">GAMES</div></div><div class="profile-stat"><div class="profile-val" style="color:#ff4154">{finish}</div><div class="profile-label">2026 RANK</div></div></div></div>',unsafe_allow_html=True)
    st.markdown("### GAME LOG")
    if weekly.empty or not fp_col: st.info(f"Weekly {season} stats are not available for {name} from the current data feed.")
    else:
        if "week" in weekly.columns: weekly["week"]=pd.to_numeric(weekly["week"],errors="coerce"); weekly=weekly.sort_values("week")
        opp_col=next((c for c in ["opponent_team","opponent","opp"] if c in weekly.columns),None); st.markdown('<div class="week-row week-head"><div>WK</div><div>OPP</div><div>STAT SNAPSHOT</div><div>FPTS</div></div>',unsafe_allow_html=True)
        for _,w in weekly.iterrows():
            wk=int(w.get("week",0)) if pd.notna(w.get("week",0)) else 0; opp=str(w.get(opp_col,"—")) if opp_col else "—"; fpts=float(pd.to_numeric(pd.Series([w.get(fp_col,0)]),errors="coerce").fillna(0).iloc[0]); rush=int(pd.to_numeric(pd.Series([w.get("rushing_yards",0)]),errors="coerce").fillna(0).iloc[0]); rec=int(pd.to_numeric(pd.Series([w.get("receptions",0)]),errors="coerce").fillna(0).iloc[0]); recyd=int(pd.to_numeric(pd.Series([w.get("receiving_yards",0)]),errors="coerce").fillna(0).iloc[0]); pas=int(pd.to_numeric(pd.Series([w.get("passing_yards",0)]),errors="coerce").fillna(0).iloc[0]); tds=int(sum(float(pd.to_numeric(pd.Series([w.get(c,0)]),errors="coerce").fillna(0).iloc[0]) for c in ["passing_tds","rushing_tds","receiving_tds"])); parts=[]
            if pas: parts.append(f"{pas} pass")
            if rush: parts.append(f"{rush} rush")
            if rec: parts.append(f"{rec} rec")
            if recyd: parts.append(f"{recyd} rec yds")
            if tds: parts.append(f"{tds} TD")
            st.markdown(f'<div class="week-row"><div>{wk}</div><div>{opp}</div><div>{" · ".join(parts) if parts else "—"}</div><div class="week-pts">{fpts:.1f}</div></div>',unsafe_allow_html=True)
    bottom_nav("Players")

def render_home():
    appbar(); rows=[[("🏆\nDRAFT BOARD\n2026 Rankings","Draft Board","nav-gold"),("👥\nMOCK DRAFT\nPractice & Plan","Mock Draft","nav-purple"),("👤\nPLAYER PROFILES\nStats & Trends","Players","nav-cyan")],[("🛡️\nMY TEAM HQ\nRoster & Lineup","Team","nav-green"),("🥷\nSLEEPERS\nHidden Gems","Sleepers","nav-yellow"),("📋\nCHEAT SHEETS\nKey Rankings","Draft Coach","nav-pink")]]
    for ridx,row in enumerate(rows):
        cols=st.columns(3)
        for c,(label,page,cls) in zip(cols,row):
            with c:
                st.markdown(f'<div class="nav-card {cls}">',unsafe_allow_html=True)
                if st.button(label,key=f"home_{ridx}_{page}",use_container_width=True): go(page)
                st.markdown('</div>',unsafe_allow_html=True)
    if st.button("🤖  ASK SHIVA GPT  →",key="home_ask",use_container_width=True,type="primary"): go("Ask Shiva")
    st.markdown('<div class="panel"><div class="small">MY LEAGUE</div><div class="panel-title">Shiva Champion League</div><div class="small">10-Team PPR</div></div>',unsafe_allow_html=True); bottom_nav("Home")

def render_rankings():
    appbar("DRAFT BOARD","2026 Rankings"); position_legend(); q=st.text_input("Search players",placeholder="Search player..."); pos=st.selectbox("Position",["ALL","QB","RB","WR","TE"],index=0); board=rankings.copy()
    if pos!="ALL": board=board[board.position.eq(pos)]
    if q: board=board[board.player_name.astype(str).str.contains(q,case=False,na=False)]
    for i,(_,r) in enumerate(board.head(40).iterrows(),1):
        player_line(r,i)
        if st.button(str(r.player_name),key=f"rank_profile_{i}",use_container_width=True): open_profile(str(r.player_name),"Draft Board")
    bottom_nav("Draft")

def render_players():
    appbar("PLAYER PROFILES","Stats & Trends"); q=st.text_input("Find a player",placeholder="Ja'Marr Chase"); pos=st.selectbox("Position",["ALL","QB","RB","WR","TE"],index=0,key="profiles_pos"); frame=rankings.copy()
    if pos!="ALL": frame=frame[frame.position.eq(pos)]
    if q: frame=frame[frame.player_name.astype(str).str.contains(q,case=False,na=False)]
    for i,(_,r) in enumerate(frame.head(35).iterrows(),1):
        player_line(r,i)
        if st.button(f"VIEW {r.player_name}",key=f"profilelist_{i}",use_container_width=True): open_profile(str(r.player_name),"Players")
    bottom_nav("Players")

def render_draft_coach():
    appbar("CHEAT SHEETS","Draft Plan"); hero("DRAFT COACH","Build Your 2026 Draft Plan","Set your slot, see the turns, then use Shiva to pressure-test the plan."); c1,c2=st.columns(2)
    with c1: teams=st.selectbox("Teams",[10,12],index=0)
    with c2: slot=st.number_input("Draft Position",1,int(teams),min(4,int(teams)),1)
    rounds=st.selectbox("Rounds",[15,16,17,18],index=1); schedule=slot_picks(int(slot),int(teams),int(rounds))
    for rno,pick in enumerate(schedule[:5],1):
        with st.expander(f"Round {rno} · Pick #{pick}",expanded=rno==1):
            window=rankings[(rankings.adp>=max(1,pick-5))&(rankings.adp<=pick+8)].head(8)
            for j,(_,p) in enumerate(window.iterrows(),1):
                player_line(p,j)
                if st.button(str(p.player_name),key=f"coach_{rno}_{j}",use_container_width=True): open_profile(str(p.player_name),"Draft Coach")
    render_ask_shiva(f"I'm drafting from slot {int(slot)} in a {int(teams)}-team PPR league. Build a smart first-six-round plan."); bottom_nav("More")

def render_team():
    appbar("MY TEAM HQ","Roster & Watch List"); st.markdown('<div class="panel"><div class="panel-title">⭐ Watch List</div><div class="small">Favorite players stay visible during mocks and are sent to Shiva as context.</div></div>',unsafe_allow_html=True); selected=st.multiselect("Add players",rankings.player_name.tolist(),default=st.session_state.watchlist,placeholder="Search a player"); st.session_state.watchlist=selected; watch=rankings[rankings.player_name.isin(selected)].sort_values("adp") if selected else pd.DataFrame()
    for i,(_,r) in enumerate(watch.iterrows(),1):
        player_line(r,i)
        if st.button(str(r.player_name),key=f"watch_profile_{i}",use_container_width=True): open_profile(str(r.player_name),"Team")
    bottom_nav("Team")

def render_sleepers():
    appbar("SLEEPERS","Hidden Gems"); hero("VALUE HUNT","2026 Draft Sleepers","Players whose current ADP creates room for upside. Use this as a shortlist, not a verdict."); frame=rankings[(rankings.adp>=45)&(rankings.position.isin(["RB","WR","TE","QB"]))].head(25)
    for i,(_,r) in enumerate(frame.iterrows(),1):
        player_line(r,i)
        if st.button(str(r.player_name),key=f"sleeper_{i}",use_container_width=True): open_profile(str(r.player_name),"Sleepers")
    bottom_nav("More")

def render_history():
    appbar("LEAGUE HISTORY","Verified Drafts")
    if history.empty: st.warning("Historical database unavailable."); return
    q=st.text_input("Search player",placeholder="Christian McCaffrey"); filt=history.copy()
    if q and "player_name" in filt.columns: filt=filt[filt.player_name.astype(str).str.contains(q,case=False,na=False)]
    preferred=[c for c in ["season","league_name","manager_name","player_name","position","round","overall_pick","ppg","position_finish_total"] if c in filt.columns]; st.dataframe(filt[preferred].head(250),hide_index=True,use_container_width=True)
    if q:
        matches=rankings[rankings.player_name.astype(str).str.contains(q,case=False,na=False)].head(8)
        for i,(_,r) in enumerate(matches.iterrows(),1):
            if st.button(f"OPEN {r.player_name} PROFILE",key=f"hist_prof_{i}",use_container_width=True): open_profile(str(r.player_name),"League History")
    bottom_nav("More")

def render_mock():
    appbar("MOCK DRAFT","10-Team PPR • Snake Draft")
    if not st.session_state.draft:
        hero("PRACTICE & PLAN","Build a Mock Draft","Choose your format, then draft against CPU managers.")
        with st.form("mock_setup"):
            c1,c2=st.columns(2)
            with c1: teams=st.selectbox("Teams",[10,12])
            with c2: slot=st.number_input("Draft Position",1,12,4,1)
            c3,c4=st.columns(2)
            with c3: rounds=st.selectbox("Rounds",[15,16,17,18],index=1)
            with c4: scoring=st.selectbox("Scoring",["PPR","Half PPR","Standard"])
            start=st.form_submit_button("START MOCK DRAFT",use_container_width=True,type="primary")
        if start:
            slot=min(int(slot),int(teams)); cfg=DraftConfig(teams=int(teams),rounds=int(rounds),user_slot=slot,scoring=scoring); picks:list[dict]=[]; picks,next_pick=advance_cpus(rankings,picks,1,cfg); st.session_state.draft={"config":cfg.__dict__,"picks":picks,"next_pick":next_pick}; st.rerun()
        bottom_nav("Draft"); return
    d=st.session_state.draft; cfg=DraftConfig(**d["config"]); total=cfg.teams*cfg.rounds; done=d["next_pick"]>total; roster=user_roster(d["picks"],cfg.user_slot); c1,c2=st.columns([2,1])
    with c1:
        if not done and st.button("🧠 WHO SHOULD I PICK?",type="primary",use_container_width=True):
            board=score_board(rankings,d["picks"],cfg.user_slot,d["next_pick"]).head(8)
            if api_key():
                context=build_context(rankings=rankings,watchlist=st.session_state.watchlist,draft=draft_context(),history_summary=history_summary(history))
                try: st.session_state.draft_recommendation=ask_shiva(api_key(),secret("OPENAI_MODEL",MODEL),"I'm on the clock. Give one primary pick and two alternatives.",context)
                except Exception as exc: st.session_state.draft_recommendation=f"AI unavailable ({exc}). Draft engine: {board.iloc[0].player_name}"
            else: st.session_state.draft_recommendation=f"Draft engine: **{board.iloc[0].player_name}**. Add OPENAI_API_KEY for Shiva's full explanation."
    with c2:
        if st.button("RESET",use_container_width=True): st.session_state.draft=None;st.session_state.draft_recommendation="";st.rerun()
    if st.session_state.draft_recommendation: st.info(st.session_state.draft_recommendation)
    tabs=st.tabs(["DRAFT BOARD","QUEUE","TEAM","RESULTS"])
    with tabs[0]:
        q=st.text_input("Search players",key="mock_search",placeholder="Search players..."); pos_filter=st.selectbox("All Positions",["ALL","QB","RB","WR","TE"],key="mock_pos"); position_legend(); avail=score_board(rankings,d["picks"],cfg.user_slot,d["next_pick"])
        if pos_filter!="ALL": avail=avail[avail.position.eq(pos_filter)]
        if q: avail=avail[avail.player_name.astype(str).str.contains(q,case=False,na=False)]
        for i,(_,r) in enumerate(avail.head(30).iterrows(),1):
            player_line(r,i); cols=st.columns([1,1])
            with cols[0]:
                if st.button("PROFILE",key=f"mock_profile_{i}",use_container_width=True): open_profile(str(r.player_name),"Mock Draft")
            with cols[1]:
                if not done and st.button("DRAFT",key=f"mock_draft_{i}",type="primary",use_container_width=True):
                    if pick_team(d["next_pick"],cfg.teams)!=cfg.user_slot: st.error("Not your pick yet.")
                    else: d["picks"].append(make_pick(r.to_dict(),d["next_pick"],cfg.teams));d["next_pick"]+=1;d["picks"],d["next_pick"]=advance_cpus(rankings,d["picks"],d["next_pick"],cfg);st.session_state.draft=d;st.session_state.draft_recommendation="";st.rerun()
        clock_text="DRAFT COMPLETE" if done else f"Pick #{d['next_pick']}"; st.markdown(f'<div class="panel"><div class="small">YOU’RE ON THE CLOCK</div><div class="panel-title" style="color:var(--lime)">{clock_text}</div></div>',unsafe_allow_html=True)
    with tabs[1]:
        st.markdown('<div class="panel"><div class="panel-title">Queue</div><div class="small">Your watch list doubles as your pre-draft queue.</div></div>',unsafe_allow_html=True); qdf=rankings[rankings.player_name.isin(st.session_state.watchlist)].sort_values("adp")
        for i,(_,r) in enumerate(qdf.iterrows(),1):
            player_line(r,i)
            if st.button(str(r.player_name),key=f"queue_prof_{i}",use_container_width=True): open_profile(str(r.player_name),"Mock Draft")
    with tabs[2]:
        if not roster: st.info("No picks yet.")
        else:
            rdf=pd.DataFrame(roster)
            for i,(_,r) in enumerate(rdf.iterrows(),1):
                pos=str(r.get("position","")); name=str(r.get("player_name","")); st.markdown(f'<div class="player-line {pos if pos in {"QB","RB","WR","TE"} else "FLEX"}"><div class="rank-circle">{i}</div><div><div class="player-main">{name}</div><div class="player-meta">Round {r.get("round","—")} · Pick {r.get("overall","—")}</div></div><div class="player-adp">{pos}</div></div>',unsafe_allow_html=True)
                if st.button(name,key=f"roster_prof_{i}",use_container_width=True): open_profile(name,"Mock Draft")
    with tabs[3]:
        position_legend(); matrix=board_matrix(d["picks"],cfg.teams,cfg.rounds); cells=[]
        for rnd,row in enumerate(matrix,1):
            for team,pick in enumerate(row,1):
                if pick:
                    pos=str(pick.get("position","FLEX")).upper(); pos=pos if pos in {"QB","RB","WR","TE","FLEX","K","DEF"} else "FLEX"; name=str(pick.get("player_name","")); cells.append(f'<div class="board-cell {pos}"><div class="board-rnd">R{rnd} · T{team}</div><div class="board-player"><a href="?player={quote(name)}">{name}</a></div><div class="board-pos">{pos}</div></div>')
                else: cells.append(f'<div class="board-cell board-empty"><div class="board-rnd">R{rnd} · T{team}</div><div class="board-player">—</div></div>')
        st.markdown(f'<div class="board-wrap"><div class="board" style="grid-template-columns:repeat({cfg.teams},minmax(76px,1fr))">{"".join(cells)}</div></div>',unsafe_allow_html=True)
    bottom_nav("Draft")

page=st.session_state.page
if page=="Home": render_home()
elif page=="Draft Board": render_rankings()
elif page=="Players": render_players()
elif page=="Player Profile": render_player_profile(st.session_state.selected_player)
elif page=="Mock Draft": render_mock()
elif page=="Draft Coach": render_draft_coach()
elif page=="Team": render_team()
elif page=="Sleepers": render_sleepers()
elif page=="League History": render_history()
elif page=="Ask Shiva": appbar("ASK SHIVA GPT","Draft Intelligence"); render_ask_shiva(); bottom_nav("Home")
else: render_home()

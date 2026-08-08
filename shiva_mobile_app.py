from __future__ import annotations
import os, re, sqlite3, unicodedata
from pathlib import Path
from urllib.parse import quote
import pandas as pd
import streamlit as st

from shiva_ai import ask_shiva, build_context
from shiva_draft import DraftConfig, advance_cpus, board_matrix, make_pick, pick_team, score_board, user_roster

APP_DIR = Path(__file__).resolve().parent
RANKINGS_PATH = APP_DIR / "current_rankings.csv"
DB_PATH = APP_DIR / "shiva_draft_roi.sqlite"
MODEL = "gpt-5-mini"

st.set_page_config(page_title="Shiva Intelligence", page_icon="🏆", layout="centered", initial_sidebar_state="collapsed")

CSS = r"""
<style>
:root{--bg:#03070b;--panel:#07131d;--line:#16334a;--text:#f7fbff;--muted:#a7b3be;--lime:#d8ff00;--qb:#bf1f24;--rb:#df6500;--wr:#0878bb;--te:#318c31;--flex:#7d36b5;--k:#33414d;--def:#69451d}
html,body,.stApp{background:linear-gradient(180deg,#020509,#06111b)!important;color:var(--text)!important;overflow-x:hidden!important}
html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
.block-container{width:100%!important;max-width:530px!important;padding:0 14px 86px!important;margin:0 auto!important}
#MainMenu,header,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
[data-testid="stVerticalBlock"]{gap:.45rem!important}[data-testid="stHorizontalBlock"]{gap:8px!important}h1,h2,h3,p,label,.stMarkdown{color:#fff}
.app-head{position:sticky;top:0;z-index:30;background:rgba(2,6,10,.96);margin:0 -14px 6px;padding:12px 14px 8px;border-bottom:1px solid rgba(255,255,255,.04);backdrop-filter:blur(12px)}
.brand{font-size:19px;font-style:italic;font-weight:1000;letter-spacing:.07em;text-align:center;color:var(--lime)}.sub{font-size:12px;color:#fff;text-align:center;margin-top:4px}.top-title{font-size:21px;font-weight:1000;text-align:center;line-height:1.05}.top-sub{font-size:12px;text-align:center;color:#e4e9ee;margin-top:4px}
.home-grid .stButton button{min-height:100px!important;border-radius:10px!important;border:1px solid #25445f!important;background:linear-gradient(145deg,#0d1a24,#071019)!important;color:#fff!important;font-weight:900!important;white-space:pre-line!important}.home-gold .stButton button{border-color:#694700!important;background:linear-gradient(145deg,#2a1800,#11100b)!important}.home-purple .stButton button{border-color:#5a2880!important;background:linear-gradient(145deg,#20102c,#0b0d13)!important}.home-blue .stButton button{border-color:#005887!important;background:linear-gradient(145deg,#05253b,#071019)!important}.home-green .stButton button{border-color:#356b20!important;background:linear-gradient(145deg,#102c10,#071019)!important}.home-yellow .stButton button{border-color:#6f4d00!important;background:linear-gradient(145deg,#2b1e00,#10100a)!important}.home-pink .stButton button{border-color:#741b45!important;background:linear-gradient(145deg,#2a0c1c,#0b0d13)!important}
.ask-card{background:linear-gradient(135deg,#06233c,#071827);border:1px solid #16557e;border-radius:8px;padding:13px 15px;margin:10px 0}.ask-title{font-size:16px;font-weight:1000}.ask-sub{font-size:12px;color:#d0d8df;margin-top:2px}.league-card{background:linear-gradient(145deg,#0a121b,#071019);border:1px solid #20384b;border-radius:8px;padding:14px;margin-top:10px}.small{font-size:11px;color:#c3ccd4}.league-name{font-size:16px;font-weight:900;margin:3px 0}
.bottom-nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:min(100%,530px);z-index:50;background:rgba(3,7,11,.98);border-top:1px solid #183044;padding:8px 10px 9px}.bottom-grid{display:grid;grid-template-columns:repeat(5,1fr);text-align:center}.bn{font-size:11px;color:#e0e5ea}.bn .ico{display:block;font-size:20px;margin-bottom:2px}.bn.active{color:var(--lime);font-weight:900}
.mock-tabs{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #1b2731;margin:6px 0 12px}.mock-tab{padding:10px 0;text-align:center;font-size:12px;font-weight:900;color:#fff}.mock-tab.active{color:var(--lime);border-bottom:2px solid var(--lime)}
[data-testid="stTextInput"] input,[data-baseweb="select"]>div,[data-testid="stNumberInput"] input{min-height:42px!important;background:#07141f!important;border:1px solid #1a3448!important;color:#fff!important;border-radius:7px!important;font-size:13px!important}.stButton button{min-height:40px!important;border-radius:7px!important;font-size:13px!important;font-weight:900!important}.stButton button[kind="primary"]{background:var(--lime)!important;color:#101500!important;border-color:#eaff48!important}
.posbar{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin:9px 0 8px}.pos{padding:7px 2px;text-align:center;border-radius:6px;color:#fff;font-size:12px;font-weight:1000;border:1px solid rgba(255,255,255,.12)}.QB{background:linear-gradient(#d5282d,#9d1519)}.RB{background:linear-gradient(#ee7600,#b84e00)}.WR{background:linear-gradient(#1592d5,#0666a1)}.TE{background:linear-gradient(#48a940,#267427)}.FLEX{background:linear-gradient(#9850d3,#652e9b)}.K{background:linear-gradient(#4b5963,#25313a)}.DEF{background:linear-gradient(#8a5b24,#5a3612)}
.list-head{display:grid;grid-template-columns:34px minmax(0,1fr) 48px 48px 46px;gap:4px;padding:5px 8px;font-size:9px;color:#cfd7dd;font-weight:900}.prow{display:grid;grid-template-columns:34px minmax(0,1fr) 48px 48px 46px;gap:4px;align-items:center;border-radius:6px;margin:2px 0;padding:8px;color:#fff;border:1px solid rgba(255,255,255,.08)}.prow.QB{background:linear-gradient(90deg,#9f181c,#bd2429)}.prow.RB{background:linear-gradient(90deg,#c95800,#ea6c00)}.prow.WR{background:linear-gradient(90deg,#0b68a5,#1382c5)}.prow.TE{background:linear-gradient(90deg,#2b7b2b,#3e9e3b)}.prow.FLEX{background:linear-gradient(90deg,#663096,#8a43bd)}.rank{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:rgba(0,0,0,.16);font-size:12px;font-weight:1000}.pname{font-size:13px;font-weight:1000;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.cell{font-size:12px;font-weight:900;text-align:center}.pname a{color:#fff!important;text-decoration:none!important}
.draft-status{position:sticky;bottom:66px;z-index:20;background:#03090f;border:1px solid #20384b;border-radius:7px;padding:9px 10px;margin-top:10px;display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center}.clock-main{font-size:12px}.pick{color:var(--lime);font-size:16px;font-weight:1000}.teamtxt{font-size:13px;font-weight:900}.timer{background:var(--lime);color:#101500;border-radius:6px;padding:8px 10px;font-size:16px;font-weight:1000}
.board-shell{margin:0 -10px;overflow:hidden}.board-title{font-size:18px;font-weight:1000;text-align:center}.board-meta{display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center;font-size:11px;margin:2px 4px 4px}.legend{font-size:9px;text-align:center;white-space:nowrap}.teamheads{display:grid;grid-template-columns:repeat(10,1fr);gap:2px;margin:7px 0 3px}.teamhead{font-size:8px;text-align:center;font-weight:900}.boardgrid{display:grid;grid-template-columns:repeat(10,1fr);gap:2px}.bcell{min-height:54px;border-radius:3px;padding:3px 2px;text-align:center;color:#fff;border:1px solid rgba(255,255,255,.09);overflow:hidden}.bcell.QB{background:#a51c21}.bcell.RB{background:#ce6000}.bcell.WR{background:#0a70aa}.bcell.TE{background:#347f31}.bcell.FLEX{background:#6c3598}.bcell.K{background:#33414d}.bcell.DEF{background:#68451d}.bcell.empty{background:#08131d}.bpick{font-size:7px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.bpos{font-size:8px;margin-top:8px;font-weight:900}.bcell a{color:#fff!important;text-decoration:none!important}
.profile-bar{display:grid;grid-template-columns:32px 1fr 60px;align-items:center;margin:5px 0 3px}.back{font-size:28px}.p-title{text-align:center;font-size:20px;font-weight:1000}.p-meta{text-align:center;font-size:10px;color:#d8dee3}.icons{text-align:right;font-size:21px}.profile-tabs{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #1d2a34;margin-bottom:7px}.profile-tab{padding:10px 0;text-align:center;font-size:10px;font-weight:900}.profile-tab.active{border-bottom:2px solid var(--lime)}
.profile-card{background:linear-gradient(145deg,#08141e,#071019);border:1px solid #183347;border-radius:8px;padding:8px 9px}.profile-top{display:grid;grid-template-columns:108px 1fr;gap:7px;align-items:center}.headshot{height:82px;display:flex;align-items:flex-end;justify-content:center;overflow:hidden}.headshot img{max-height:82px;max-width:100%}.stats4{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;text-align:center}.statv{font-size:17px;font-weight:1000;color:#ffb21b}.statv.rankv{color:#ff4258}.statl{font-size:9px}.bio-row{display:grid;grid-template-columns:repeat(4,1fr);font-size:9px;text-align:center;background:#061019;border-radius:5px;padding:5px;margin-top:4px}.year-pills{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin:6px 0}.year-pill{padding:6px 0;border-radius:5px;background:#0b1a26;border:1px solid #21384b;text-align:center;font-size:11px;font-weight:900}.year-pill.active{background:#0d68b2}.game-head,.game-row{display:grid;grid-template-columns:30px 45px 58px 45px 42px 36px 52px 28px;gap:2px;align-items:center}.game-head{font-size:8px;font-weight:900;color:#d6dde3;padding:3px 2px}.game-row{font-size:9px;padding:4px 2px;border-bottom:1px solid #142a3b}.fpts{color:#22c8ff;font-weight:1000}
@media(max-width:390px){.block-container{padding-left:9px!important;padding-right:9px!important}.pname{font-size:12px}.prow,.list-head{grid-template-columns:32px minmax(0,1fr) 42px 42px 42px}.bcell{min-height:50px}.bpick{font-size:6.5px}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def norm(v):
    v=unicodedata.normalize("NFKD",str(v or "")).encode("ascii","ignore").decode().lower(); v=re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?","",v); return re.sub(r"[^a-z0-9]+","",v)

@st.cache_data(show_spinner=False)
def rankings_df():
    df=pd.read_csv(RANKINGS_PATH)
    for c in ["adp","overall_rank","position_rank","bye"]:
        if c in df: df[c]=pd.to_numeric(df[c],errors="coerce")
    df["position"]=df["position"].astype(str).str.upper(); return df.sort_values(["adp","overall_rank"],na_position="last").reset_index(drop=True)

@st.cache_data(show_spinner=False)
def history_df():
    if not DB_PATH.exists(): return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as con:return pd.read_sql_query("select * from draft_roi_scores",con)
    except Exception:return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=3600)
def weekly_year(year:int):
    try:df=pd.read_csv(f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_week_{year}.csv",low_memory=False)
    except Exception:return pd.DataFrame()
    nc=next((c for c in ["player_display_name","player_name","display_name","name"] if c in df.columns),None)
    if not nc:return pd.DataFrame()
    df["_name_key"]=df[nc].map(norm); return df

@st.cache_data(show_spinner=False, ttl=86400)
def players_meta():
    for u in ["https://github.com/nflverse/nflverse-data/releases/download/players/players.csv","https://github.com/nflverse/nflverse-data/releases/download/players/players.csv.gz"]:
        try:df=pd.read_csv(u,low_memory=False); break
        except Exception:df=pd.DataFrame()
    if df.empty:return df
    nc=next((c for c in ["display_name","full_name","player_name"] if c in df.columns),None)
    if nc:df["_name_key"]=df[nc].map(norm)
    return df

R=rankings_df(); H=history_df()
for k,v in {"page":"Home","selected_player":"","return_page":"Home","watchlist":[],"draft":None,"mock_view":"PLAYERS"}.items():
    if k not in st.session_state:st.session_state[k]=v

def go(p):st.session_state.page=p; st.rerun()
def open_profile(name,ret=None):st.session_state.selected_player=str(name); st.session_state.return_page=ret or st.session_state.page; st.session_state.page="Profile"; st.rerun()
try:
    qp=st.query_params.get("player","")
    if qp:st.session_state.selected_player=qp; st.session_state.return_page=st.session_state.page; st.session_state.page="Profile"; st.query_params.clear()
except Exception:pass

def header(title="SHIVA INTELLIGENCE",sub="Your Draft Command Center",brand=False):
    cls="brand" if brand else "top-title"; scls="sub" if brand else "top-sub"; st.markdown(f'<div class="app-head"><div class="{cls}">{title}</div><div class="{scls}">{sub}</div></div>',unsafe_allow_html=True)
def bottom(active):
    html='<div class="bottom-nav"><div class="bottom-grid">'
    for ico,label in [("⌂","Home"),("◉","Draft"),("♙","Players"),("♧","Team"),("•••","More")]:html+=f'<div class="bn {"active" if label==active else ""}"><span class="ico">{ico}</span>{label}</div>'
    st.markdown(html+'</div></div>',unsafe_allow_html=True)
def posbar():st.markdown('<div class="posbar">'+''.join(f'<div class="pos {p}">{p}</div>' for p in ["QB","RB","WR","TE","FLEX","K","DEF"])+'</div>',unsafe_allow_html=True)
def clspos(p):p=str(p).upper(); return p if p in {"QB","RB","WR","TE","FLEX","K","DEF"} else "FLEX"

def player_rows(df,prefix,ret,draftable=False):
    st.markdown('<div class="list-head"><div>RK</div><div>PLAYER</div><div>POS</div><div>TEAM</div><div>ADP</div></div>',unsafe_allow_html=True)
    for i,(_,r) in enumerate(df.iterrows(),1):
        p=clspos(r.get("position","FLEX")); name=str(r.get("player_name","")); adp="—" if pd.isna(r.get("adp")) else f'{float(r.get("adp")):.1f}'
        st.markdown(f'<div class="prow {p}"><div class="rank">{i}</div><div class="pname"><a href="?player={quote(name)}">{name}</a></div><div class="cell">{p}</div><div class="cell">{r.get("team","—")}</div><div class="cell">{adp}</div></div>',unsafe_allow_html=True)
        if draftable and st.button(f"Draft {name}",key=f"{prefix}_draft_{i}",use_container_width=True):
            d=st.session_state.draft; cfg=DraftConfig(**d["config"])
            if pick_team(d["next_pick"],cfg.teams)!=cfg.user_slot:st.warning("CPU is picking.")
            else:d["picks"].append(make_pick(r.to_dict(),d["next_pick"],cfg.teams)); d["next_pick"]+=1; d["picks"],d["next_pick"]=advance_cpus(R,d["picks"],d["next_pick"],cfg); st.session_state.draft=d; st.rerun()

def home():
    header(brand=True)
    rows=[[("🏆\nDRAFT BOARD\n2026 Rankings","Draft Board","home-gold"),("👥\nMOCK DRAFT\nPractice & Plan","Mock Draft","home-purple"),("👤\nPLAYER PROFILES\nStats & Trends","Players","home-blue")],[("🛡️\nMY TEAM HQ\nRoster & Lineup","Team","home-green"),("🥷\nSLEEPERS\nHidden Gems","Sleepers","home-yellow"),("📋\nCHEAT SHEETS\nKey Rankings","Draft Board","home-pink")]]
    for ri,row in enumerate(rows):
        cols=st.columns(3)
        for c,(label,page,klass) in zip(cols,row):
            with c:
                st.markdown(f'<div class="home-grid {klass}">',unsafe_allow_html=True)
                if st.button(label,key=f"h_{ri}_{page}",use_container_width=True):go(page)
                st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="ask-card"><div class="ask-title">🤖 &nbsp; ASK SHIVA GPT</div><div class="ask-sub">Ask questions, get advice, win your league. &nbsp; →</div></div>',unsafe_allow_html=True)
    if st.button("ASK SHIVA GPT",key="ask_home",use_container_width=True):go("Ask")
    st.markdown('<div class="league-card"><div class="small">MY LEAGUE</div><div class="league-name">Shiva Champion League</div><div class="small">10-Team PPR</div></div>',unsafe_allow_html=True); bottom("Home")

def draft_board_page():
    header("DRAFT BOARD","2026 Rankings"); q=st.text_input("Search",placeholder="Search players...",label_visibility="collapsed"); pos=st.selectbox("Position",["ALL","QB","RB","WR","TE"],label_visibility="collapsed"); posbar(); df=R.copy()
    if pos!="ALL":df=df[df.position.eq(pos)]
    if q:df=df[df.player_name.astype(str).str.contains(q,case=False,na=False)]
    player_rows(df.head(50),"rank","Draft Board"); bottom("Draft")

def players_page():
    header("PLAYER PROFILES","Stats & Trends"); q=st.text_input("Search",placeholder="Search player...",label_visibility="collapsed"); df=R.copy()
    if q:df=df[df.player_name.astype(str).str.contains(q,case=False,na=False)]
    posbar(); player_rows(df.head(50),"players","Players"); bottom("Players")

def mock_setup():
    header("MOCK DRAFT","10-Team PPR • Snake Draft")
    with st.form("setup"):
        c1,c2=st.columns(2); teams=c1.selectbox("Teams",[10,12]); slot=c2.number_input("Draft Position",1,int(teams),1); c3,c4=st.columns(2); rounds=c3.selectbox("Rounds",[15,16,17,18],index=1); scoring=c4.selectbox("Scoring",["PPR","Half PPR","Standard"]); start=st.form_submit_button("START MOCK DRAFT",use_container_width=True,type="primary")
    if start:
        cfg=DraftConfig(teams=int(teams),rounds=int(rounds),user_slot=int(slot),scoring=scoring); picks,next_pick=advance_cpus(R,[],1,cfg); st.session_state.draft={"config":cfg.__dict__,"picks":picks,"next_pick":next_pick}; st.rerun()
    bottom("Draft")

def mock():
    if not st.session_state.draft:return mock_setup()
    d=st.session_state.draft; cfg=DraftConfig(**d["config"]); roster=user_roster(d["picks"],cfg.user_slot); header("MOCK DRAFT",f"{cfg.teams}-Team PPR • Snake Draft")
    tabs=["PLAYERS","QUEUE","TEAM","BOARD"]; cols=st.columns(4)
    for c,t in zip(cols,tabs):
        with c:
            if st.button(t,key=f"mt_{t}",use_container_width=True):st.session_state.mock_view=t; st.rerun()
    v=st.session_state.mock_view; st.markdown('<div class="mock-tabs">'+''.join(f'<div class="mock-tab {"active" if t==v else ""}">{("DRAFT BOARD" if t=="PLAYERS" else "RESULTS" if t=="BOARD" else t)}</div>' for t in tabs)+'</div>',unsafe_allow_html=True)
    if v=="PLAYERS":
        c1,c2,c3=st.columns([1.5,1,1]); q=c1.text_input("Search",placeholder="Search players...",label_visibility="collapsed"); pos=c2.selectbox("Pos",["ALL","QB","RB","WR","TE"],label_visibility="collapsed"); team=c3.selectbox("Team",["ALL"]+sorted(R.team.dropna().astype(str).unique()),label_visibility="collapsed"); posbar(); df=score_board(R,d["picks"],cfg.user_slot,d["next_pick"])
        if pos!="ALL":df=df[df.position.eq(pos)]
        if team!="ALL":df=df[df.team.eq(team)]
        if q:df=df[df.player_name.astype(str).str.contains(q,case=False,na=False)]
        player_rows(df.head(35),"mock","Mock Draft",True); pick=d["next_pick"]; rnd=(pick-1)//cfg.teams+1; slot=((pick-1)%cfg.teams)+1 if rnd%2==1 else cfg.teams-((pick-1)%cfg.teams); st.markdown(f'<div class="draft-status"><div><div class="clock-main">You’re on the clock!</div><div class="pick">Pick {rnd}.{slot:02d}</div></div><div class="teamtxt">Team {cfg.user_slot}</div><div class="timer">01:30</div></div>',unsafe_allow_html=True)
    elif v=="QUEUE":player_rows(R[R.player_name.isin(st.session_state.watchlist)].sort_values("adp"),"queue","Mock Draft")
    elif v=="TEAM":
        rdf=pd.DataFrame(roster)
        if rdf.empty:st.info("No picks yet.")
        else:
            if "adp" not in rdf:rdf["adp"]=pd.NA
            player_rows(rdf,"team","Mock Draft")
    else:
        st.markdown('<div class="board-shell"><div class="board-title">MOCK DRAFT BOARD</div><div class="board-meta"><div>‹</div><div style="text-align:center">Round 1⌄</div><div style="text-align:right">10 Teams • PPR</div></div><div class="legend">🟥 QB &nbsp; 🟧 RB &nbsp; 🟦 WR &nbsp; 🟩 TE &nbsp; 🟪 FLEX &nbsp; ⬛ K &nbsp; 🟫 DEF</div>',unsafe_allow_html=True); st.markdown('<div class="teamheads">'+''.join(f'<div class="teamhead">TEAM {i}</div>' for i in range(1,cfg.teams+1))+'</div>',unsafe_allow_html=True); matrix=board_matrix(d["picks"],cfg.teams,cfg.rounds); cells=[]
        for rnd,row in enumerate(matrix,1):
            for team,pick in enumerate(row,1):
                if pick:
                    name=str(pick.get("player_name","")); p=clspos(pick.get("position","FLEX")); parts=name.split(); disp=(parts[0][0]+"."+parts[-1]) if len(parts)>1 else name; cells.append(f'<div class="bcell {p}"><div class="bpick"><a href="?player={quote(name)}">{rnd}.{team} {disp}</a></div><div class="bpos">{p}</div></div>')
                else:cells.append('<div class="bcell empty"></div>')
        st.markdown('<div class="boardgrid">'+''.join(cells)+'</div></div>',unsafe_allow_html=True)
    bottom("Draft")

def season_list(name):
    if not H.empty and {"player_name","season"}.issubset(H.columns):
        h=H[H.player_name.map(norm).eq(norm(name))]; years=sorted({int(x) for x in h.season.dropna() if 1990<int(x)<2100},reverse=True)
        if years:return years
    found=[]
    for y in range(2025,2013,-1):
        df=weekly_year(y)
        if not df.empty and (df["_name_key"]==norm(name)).any():found.append(y)
    return found or [2025]

def profile():
    name=st.session_state.selected_player; rr=R[R.player_name.astype(str).map(norm).eq(norm(name))]; r=rr.iloc[0] if not rr.empty else None; team=str(r.team) if r is not None else "—"; pos=str(r.position) if r is not None else "—"
    st.markdown(f'<div class="profile-bar"><div class="back">‹</div><div><div class="p-title">{name.upper()}</div><div class="p-meta">{pos} • {team}</div></div><div class="icons">⭐ ⤴</div></div>',unsafe_allow_html=True)
    if st.button("Back",key="profile_back",use_container_width=True):go(st.session_state.return_page)
    st.markdown('<div class="profile-tabs"><div class="profile-tab active">OVERVIEW</div><div class="profile-tab">STATS</div><div class="profile-tab">GAME LOG</div><div class="profile-tab">NEWS</div></div>',unsafe_allow_html=True)
    years=season_list(name); year=st.selectbox("Year",years,format_func=lambda y:f"{y} (Year)",label_visibility="collapsed"); w=weekly_year(int(year))
    if not w.empty:
        w=w[w["_name_key"].eq(norm(name))].copy()
        if "season_type" in w.columns:
            reg=w[w.season_type.astype(str).str.upper().eq("REG")]
            if not reg.empty:w=reg
    fp="fantasy_points_ppr" if "fantasy_points_ppr" in w.columns else ("fantasy_points" if "fantasy_points" in w.columns else None); pts=pd.to_numeric(w[fp],errors="coerce").fillna(0) if fp and not w.empty else pd.Series(dtype=float); total=float(pts.sum()) if len(pts) else 0; ppg=float(pts.mean()) if len(pts) else 0; games=len(w); posrank="—"
    meta=players_meta(); m=None
    if not meta.empty and "_name_key" in meta.columns:
        mm=meta[meta["_name_key"].eq(norm(name))]
        if not mm.empty:m=mm.iloc[0]
    def mv(*cols):
        if m is None:return "—"
        for c in cols:
            if c in m.index and pd.notna(m[c]) and str(m[c]).strip() not in {"","nan"}:return str(m[c])
        return "—"
    head=mv("headshot","headshot_url"); head_html=f'<img src="{head}">' if str(head).startswith("http") else ""; st.markdown(f'<div class="profile-card"><div class="profile-top"><div class="headshot">{head_html}</div><div class="stats4"><div><div class="statv">{total:.1f}</div><div class="statl">FPTS</div></div><div><div class="statv">{ppg:.1f}</div><div class="statl">PPG</div></div><div><div class="statv">{games}</div><div class="statl">GAMES</div></div><div><div class="statv rankv">{posrank}</div><div class="statl">RANK</div></div></div></div><div class="bio-row"><div>Height: {mv("height")}</div><div>Weight: {mv("weight")} lbs</div><div>College: {mv("college_name","college")}</div><div>Age: {mv("age")}</div></div></div>',unsafe_allow_html=True); st.markdown('<div class="year-pills">'+''.join(f'<div class="year-pill {"active" if y==year else ""}">{y}</div>' for y in years[:5])+'</div>',unsafe_allow_html=True)
    if w.empty or not fp:st.info(f"No weekly {year} data available.")
    else:
        if "week" in w:w=w.sort_values("week")
        st.markdown('<div class="game-head"><div>WK</div><div>OPP</div><div>RESULT</div><div>FPTS</div><div>RUSH</div><div>REC</div><div>REC YDS</div><div>TD</div></div>',unsafe_allow_html=True); oppc=next((c for c in ["opponent_team","opponent","opp"] if c in w.columns),None)
        for _,x in w.iterrows():
            def num(c):
                try:return int(float(x.get(c,0) or 0))
                except:return 0
            wk=num("week"); opp=str(x.get(oppc,"—")) if oppc else "—"; f=float(pd.to_numeric(pd.Series([x.get(fp,0)]),errors="coerce").fillna(0).iloc[0]); rush=num("rushing_yards"); rec=num("receptions"); ry=num("receiving_yards"); td=num("rushing_tds")+num("receiving_tds")+num("passing_tds"); res=str(x.get("result","—")); st.markdown(f'<div class="game-row"><div>{wk}</div><div>@{opp}</div><div>{res}</div><div class="fpts">{f:.1f}</div><div>{rush}</div><div>{rec}</div><div>{ry}</div><div>{td}</div></div>',unsafe_allow_html=True)
    bottom("Players")

def team():header("MY TEAM HQ","Roster & Lineup"); sel=st.multiselect("Watch List",R.player_name.tolist(),default=st.session_state.watchlist); st.session_state.watchlist=sel; player_rows(R[R.player_name.isin(sel)].sort_values("adp"),"watch","Team"); bottom("Team")
def sleepers():header("SLEEPERS","Hidden Gems"); player_rows(R[(R.adp>=45)&R.position.isin(["RB","WR","TE","QB"])].head(30),"sleep","Sleepers"); bottom("More")
def ask():
    header("ASK SHIVA GPT","Draft Intelligence"); q=st.text_area("Ask Shiva",placeholder="Who should I draft at 1.03?")
    if st.button("ASK SHIVA",type="primary",use_container_width=True) and q.strip():
        key=os.getenv("OPENAI_API_KEY","")
        try:key=str(st.secrets.get("OPENAI_API_KEY",key))
        except Exception:pass
        if not key:st.warning("Add OPENAI_API_KEY in Streamlit secrets.")
        else:
            ctx=build_context(rankings=R,watchlist=st.session_state.watchlist,draft=None,history_summary=f"{len(H)} historical rows")
            try:st.write(ask_shiva(key,MODEL,q.strip(),ctx))
            except Exception as e:st.error(str(e))
    bottom("Home")

page=st.session_state.page
if page=="Home":home()
elif page=="Draft Board":draft_board_page()
elif page=="Players":players_page()
elif page=="Mock Draft":mock()
elif page=="Profile":profile()
elif page=="Team":team()
elif page=="Sleepers":sleepers()
elif page=="Ask":ask()
else:home()

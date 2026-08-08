from __future__ import annotations
import base64, os, re, sqlite3, time, unicodedata
from pathlib import Path
from urllib.parse import quote
import pandas as pd
import streamlit as st
from shiva_ai import ask_shiva, build_context
from shiva_draft import DraftConfig, advance_cpus, board_matrix, make_pick, pick_team, score_board, user_roster

ROOT=Path(__file__).resolve().parent
RANKINGS_PATH=ROOT/'current_rankings.csv'; DB_PATH=ROOT/'shiva_draft_roi.sqlite'; SPLASH=ROOT/'assets'/'shiva_splash.b64'
MODEL='gpt-5-mini'
st.set_page_config(page_title='Shiva Intelligence',page_icon='🏆',layout='centered',initial_sidebar_state='collapsed')

if '_splash_seen' not in st.session_state:
    try:
        b64=SPLASH.read_text(encoding='utf-8').strip()
        ph=st.empty()
        ph.markdown(f'''<style>#MainMenu,header,footer,[data-testid="stToolbar"]{{display:none!important}}.shiva-splash{{position:fixed;inset:0;z-index:2147483647;background:#020713;display:flex;justify-content:center;align-items:center;overflow:hidden}}.shiva-splash img{{width:100vw;height:100vh;object-fit:cover;object-position:center center}}@media(min-width:600px){{.shiva-splash img{{width:min(100vw,560px)}}}}</style><div class="shiva-splash"><img src="data:image/jpeg;base64,{b64}"></div>''',unsafe_allow_html=True)
        time.sleep(2.5); ph.empty()
    finally:
        st.session_state._splash_seen=True

CSS='''<style>
:root{--bg:#03070b;--surface:#08121b;--surface2:#0c1924;--line:#1b3142;--text:#f7fbff;--muted:#94a6b5;--lime:#d9ff00;--blue:#1297dc;--qb:#bc252a;--rb:#d96b08;--wr:#147cb8;--te:#368d3a;--flex:#7942aa;--k:#48545e;--def:#745027}
html,body,.stApp{background:radial-gradient(circle at 50% -10%,rgba(18,151,220,.12),transparent 34%),linear-gradient(180deg,#02060a,#07111a)!important;color:var(--text)!important;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.block-container{max-width:560px!important;padding:0 12px 90px!important}#MainMenu,header,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}[data-testid="stHorizontalBlock"]{gap:8px!important}.topbar{position:sticky;top:0;z-index:40;margin:0 -12px 8px;padding:12px 14px 10px;background:rgba(2,7,12,.96);backdrop-filter:blur(18px);border-bottom:1px solid rgba(70,120,150,.22)}.brand{font-size:19px;font-weight:1000;font-style:italic;letter-spacing:.08em;color:var(--lime);text-align:center}.tag{font-size:11px;color:#d4dde4;text-align:center;margin-top:4px}.section{font-size:11px;letter-spacing:.12em;color:#7f94a4;font-weight:900;margin:15px 2px 7px}.hero{padding:16px 2px 8px}.hero h1{font-size:28px;line-height:1.05;margin:0 0 6px}.hero p{font-size:13px;color:var(--muted);margin:0}.tool .stButton button{min-height:70px!important;border-radius:14px!important;border:1px solid #1b3548!important;background:linear-gradient(100deg,#0b1822,#07111a)!important;color:#fff!important;font-weight:900!important;font-size:14px!important;text-align:left!important;justify-content:flex-start!important;white-space:pre-line!important;padding:11px 14px!important}.tool.gold .stButton button{border-left:3px solid #f2ad22!important}.tool.purple .stButton button{border-left:3px solid #9b54d7!important}.tool.blue .stButton button{border-left:3px solid #29b8f3!important}.tool.green .stButton button{border-left:3px solid #57ca4f!important}.tool.pink .stButton button{border-left:3px solid #f45a98!important}.tool.yellow .stButton button{border-left:3px solid #f2cd39!important}.ask{border:1px solid #17567d;border-radius:14px;background:linear-gradient(110deg,#082640,#071520);padding:14px;margin:12px 0}.ask b{font-size:16px}.ask span{display:block;color:#b7c7d3;font-size:12px;margin-top:4px}.league{border:1px solid #1b384d;border-radius:12px;background:#08151f;padding:13px;margin:10px 0}.league b{font-size:16px}.muted{color:var(--muted);font-size:12px}.posbar{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin:8px 0}.pos{padding:7px 2px;border-radius:6px;text-align:center;color:white;font-size:10px;font-weight:1000}.QB{background:var(--qb)}.RB{background:var(--rb)}.WR{background:var(--wr)}.TE{background:var(--te)}.FLEX{background:var(--flex)}.K{background:var(--k)}.DEF{background:var(--def)}.rankh,.rankr{display:grid;grid-template-columns:30px minmax(0,1fr) 40px 42px 42px;gap:5px;align-items:center}.rankh{font-size:9px;color:#93a4b2;padding:6px 5px;border-bottom:1px solid #173044}.rankr{margin:2px 0;padding:8px 6px;border-radius:6px;color:#fff;border:1px solid rgba(255,255,255,.05)}.rankr.QB{background:#a82328}.rankr.RB{background:#c65e05}.rankr.WR{background:#0e6fa8}.rankr.TE{background:#317e35}.rankr.FLEX{background:#6d3998}.rk{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;background:rgba(0,0,0,.18);font-size:10px;font-weight:900}.pn{font-size:12px;font-weight:1000;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pn a{color:white;text-decoration:none}.cell{font-size:10px;font-weight:900;text-align:center}.boardwrap{overflow-x:auto;background:#040d14;border:1px solid #19354a;border-radius:8px;padding:5px}.board{display:grid;gap:3px;min-width:780px}.bc{min-height:56px;border-radius:5px;padding:4px;text-align:center;color:#fff;border:1px solid rgba(255,255,255,.06)}.bc.empty{background:#0b1720}.bp{font-size:9px;font-weight:1000;line-height:1.05}.bp a{color:white;text-decoration:none}.bpos{font-size:8px;margin-top:6px}.profile-title{text-align:center;font-size:20px;font-weight:1000}.profile-sub{text-align:center;color:#c7d2da;font-size:10px}.tabs{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #1b3142;margin:4px 0 8px}.tab{padding:9px 0;text-align:center;font-size:10px;font-weight:900}.tab.active{border-bottom:2px solid var(--lime)}.pcard{border:1px solid #1d3b50;border-radius:8px;background:#07151f;padding:8px}.ptop{display:grid;grid-template-columns:100px 1fr;gap:8px;align-items:end}.headshot{height:86px;display:flex;align-items:flex-end;justify-content:center;overflow:hidden}.headshot img{max-width:100%;max-height:86px}.stats4{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;text-align:center}.sv{font-size:17px;font-weight:1000;color:#f2ae22}.sv.red{color:#ff4d64}.sl{font-size:8px}.bio{display:grid;grid-template-columns:repeat(4,1fr);gap:3px;background:#051019;border-radius:5px;padding:5px;margin-top:5px;text-align:center;font-size:8px}.yrbar{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;margin:6px 0}.yr{padding:6px;border:1px solid #254258;border-radius:5px;text-align:center;font-size:10px;background:#0a1b27}.yr.active{background:#0e68ad}.gh,.gr{display:grid;grid-template-columns:24px 38px 50px 38px 34px 30px 43px 24px;gap:2px;align-items:center}.gh{font-size:8px;color:#9cacb8;font-weight:900;padding:4px 2px}.gr{font-size:8px;padding:4px 2px;border-bottom:1px solid #142a3b}.fp{color:#2ac8ff;font-weight:1000}.stButton button{border-radius:10px!important;font-weight:900!important;background:#0b1721!important;border-color:#223d50!important;color:#fff!important}input,textarea,[data-baseweb="select"]>div{background:#081721!important;color:#fff!important;border-color:#213b4f!important;border-radius:9px!important}.nav{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:min(100%,560px);z-index:50;background:rgba(2,7,12,.97);border-top:1px solid #183247;padding:6px 8px 8px;backdrop-filter:blur(18px)}.navgrid{display:grid;grid-template-columns:repeat(5,1fr);text-align:center}.ni{font-size:10px;color:#b9c4cc}.ni span{display:block;font-size:18px}.ni.active{color:var(--lime);font-weight:900}@media(max-width:390px){.block-container{padding-left:8px!important;padding-right:8px!important}.topbar{margin-left:-8px!important;margin-right:-8px!important}.hero h1{font-size:25px}.tool .stButton button{min-height:64px!important;font-size:13px!important}}
</style>'''
st.markdown(CSS,unsafe_allow_html=True)

def norm(v):
    v=unicodedata.normalize('NFKD',str(v or '')).encode('ascii','ignore').decode().lower(); v=re.sub(r'\b(jr|sr|ii|iii|iv)\b\.?','',v); return re.sub(r'[^a-z0-9]+','',v)
@st.cache_data(show_spinner=False)
def rankings():
    df=pd.read_csv(RANKINGS_PATH)
    for c in ['adp','overall_rank','position_rank','bye']:
        if c in df: df[c]=pd.to_numeric(df[c],errors='coerce')
    df['position']=df['position'].astype(str).str.upper(); return df.sort_values(['adp','overall_rank'],na_position='last').reset_index(drop=True)
@st.cache_data(show_spinner=False)
def history():
    if not DB_PATH.exists(): return pd.DataFrame()
    try:
        with sqlite3.connect(DB_PATH) as con:return pd.read_sql_query('select * from draft_roi_scores',con)
    except:return pd.DataFrame()
@st.cache_data(show_spinner=False,ttl=3600)
def weekly(year):
    try: df=pd.read_csv(f'https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_week_{year}.csv',low_memory=False)
    except: return pd.DataFrame()
    nc=next((c for c in ['player_display_name','player_name','display_name','name'] if c in df.columns),None)
    if not nc:return pd.DataFrame()
    df['_key']=df[nc].map(norm); return df
@st.cache_data(show_spinner=False,ttl=86400)
def meta():
    try: df=pd.read_csv('https://github.com/nflverse/nflverse-data/releases/download/players/players.csv',low_memory=False)
    except: return pd.DataFrame()
    nc=next((c for c in ['display_name','full_name','player_name'] if c in df.columns),None)
    if nc: df['_key']=df[nc].map(norm)
    return df
R=rankings(); H=history()
for k,v in {'page':'Home','selected':'','return_page':'Home','draft':None,'mock_tab':'Players','watchlist':[]}.items():
    if k not in st.session_state: st.session_state[k]=v

def go(p): st.session_state.page=p; st.rerun()
try:
    qp=st.query_params.get('player','')
    if qp: st.session_state.selected=qp; st.session_state.return_page=st.session_state.page; st.session_state.page='Profile'; st.query_params.clear()
except: pass

def topbar(title='SHIVA INTELLIGENCE',tag='Your Draft Command Center'):
    st.markdown(f'<div class="topbar"><div class="brand">{title}</div><div class="tag">{tag}</div></div>',unsafe_allow_html=True)
def nav(active):
    items=[('⌂','Home'),('◉','Draft'),('♙','Players'),('♧','Team'),('•••','More')]; h='<div class="nav"><div class="navgrid">'
    for ico,l in items:h+=f'<div class="ni {"active" if l==active else ""}"><span>{ico}</span>{l}</div>'
    st.markdown(h+'</div></div>',unsafe_allow_html=True)
def clspos(p): p=str(p).upper(); return p if p in {'QB','RB','WR','TE','FLEX','K','DEF'} else 'FLEX'
def posbar(): st.markdown('<div class="posbar">'+''.join(f'<div class="pos {p}">{p}</div>' for p in ['QB','RB','WR','TE','FLEX','K','DEF'])+'</div>',unsafe_allow_html=True)
def rows(df):
    st.markdown('<div class="rankh"><div>RK</div><div>PLAYER</div><div>POS</div><div>TEAM</div><div>ADP</div></div>',unsafe_allow_html=True)
    for i,(_,r) in enumerate(df.iterrows(),1):
        p=clspos(r.get('position')); name=str(r.get('player_name','')); adp='—' if pd.isna(r.get('adp')) else f'{float(r.adp):.1f}'
        st.markdown(f'<div class="rankr {p}"><div class="rk">{i}</div><div class="pn"><a href="?player={quote(name)}">{name}</a></div><div class="cell">{p}</div><div class="cell">{r.get("team","—")}</div><div class="cell">{adp}</div></div>',unsafe_allow_html=True)

def home():
    topbar(); st.markdown('<div class="hero"><h1>Draft smarter.<br>Win your league.</h1><p>2026 rankings, live mock drafting, player trends, historical league context and Shiva GPT in one mobile-first command center.</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="section">DRAFT TOOLS</div>',unsafe_allow_html=True)
    tools=[('🏆  DRAFT BOARD\n2026 rankings & ADP','Draft Board','gold'),('◈  MOCK DRAFT\nPractice your slot & build a plan','Mock Draft','purple'),('◎  PLAYER PROFILES\nStats, trends & weekly game logs','Players','blue'),('★  MY TEAM HQ\nLeague history & watch list','Team','green'),('⌁  SLEEPERS\nLate-round upside targets','Sleepers','yellow'),('▤  CHEAT SHEETS\nFast draft-day rankings','Draft Board','pink')]
    for i,(lab,p,c) in enumerate(tools):
        st.markdown(f'<div class="tool {c}">',unsafe_allow_html=True)
        if st.button(lab,key=f'tool_{i}',use_container_width=True): go(p)
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="ask"><b>🤖 ASK SHIVA GPT</b><span>Ask a draft question, compare players, or pressure-test your next pick.</span></div>',unsafe_allow_html=True)
    if st.button('OPEN ASK SHIVA',use_container_width=True): go('Ask')
    st.markdown('<div class="league"><div class="muted">MY LEAGUE</div><b>Shiva Champion League</b><div class="muted">10-Team · Full PPR</div></div>',unsafe_allow_html=True); nav('Home')

def draft_board_page():
    topbar('DRAFT BOARD','2026 Rankings'); c1,c2=st.columns([2,1]); q=c1.text_input('Search',placeholder='Search players...',label_visibility='collapsed'); pos=c2.selectbox('Position',['ALL','QB','RB','WR','TE'],label_visibility='collapsed'); posbar(); df=R.copy()
    if pos!='ALL': df=df[df.position.eq(pos)]
    if q: df=df[df.player_name.astype(str).str.contains(q,case=False,na=False)]
    rows(df.head(75)); nav('Draft')

def players_page():
    topbar('PLAYER PROFILES','Stats & Trends'); q=st.text_input('Search',placeholder='Search player...',label_visibility='collapsed'); df=R.copy()
    if q: df=df[df.player_name.astype(str).str.contains(q,case=False,na=False)]
    posbar(); rows(df.head(75)); nav('Players')

def profile():
    name=st.session_state.selected; rr=R[R.player_name.astype(str).map(norm).eq(norm(name))]; r=rr.iloc[0] if not rr.empty else None; team=str(r.team) if r is not None else '—'; pos=str(r.position) if r is not None else '—'; prank=(int(r.position_rank) if r is not None and pd.notna(r.get('position_rank')) else None)
    c1,c2,c3=st.columns([1,7,1])
    with c1:
        if st.button('‹',key='back'): go(st.session_state.return_page)
    with c2: st.markdown(f'<div class="profile-title">{name.upper()}</div><div class="profile-sub">{pos} · {team}</div>',unsafe_allow_html=True)
    with c3: st.markdown('⭐')
    st.markdown('<div class="tabs"><div class="tab active">OVERVIEW</div><div class="tab">STATS</div><div class="tab">GAME LOG</div><div class="tab">NEWS</div></div>',unsafe_allow_html=True)
    years=[]
    for y in range(2025,2013,-1):
        d=weekly(y)
        if not d.empty and (d['_key']==norm(name)).any(): years.append(y)
    if not years: years=[2025]
    year=st.selectbox('Season',years,format_func=lambda y:f'{y} (Year)',label_visibility='collapsed'); w=weekly(year)
    if not w.empty:
        w=w[w['_key'].eq(norm(name))].copy()
        if 'season_type' in w:
            reg=w[w.season_type.astype(str).str.upper().eq('REG')]
            if not reg.empty:w=reg
    fp='fantasy_points_ppr' if 'fantasy_points_ppr' in w else ('fantasy_points' if 'fantasy_points' in w else None); pts=pd.to_numeric(w[fp],errors='coerce').fillna(0) if fp and not w.empty else pd.Series(dtype=float); total=float(pts.sum()) if len(pts) else 0; ppg=float(pts.mean()) if len(pts) else 0; games=len(w)
    M=meta(); m=None
    if not M.empty and '_key' in M:
        mm=M[M['_key'].eq(norm(name))]; m=mm.iloc[0] if not mm.empty else None
    def mv(*cols):
        if m is None:return '—'
        for c in cols:
            if c in m.index and pd.notna(m[c]) and str(m[c]).strip() not in {'','nan'}:return str(m[c])
        return '—'
    head=mv('headshot','headshot_url'); img=f'<img src="{head}">' if str(head).startswith('http') else ''
    st.markdown(f'<div class="pcard"><div class="ptop"><div class="headshot">{img}</div><div class="stats4"><div><div class="sv">{total:.1f}</div><div class="sl">FPTS</div></div><div><div class="sv">{ppg:.1f}</div><div class="sl">PPG</div></div><div><div class="sv">{games}</div><div class="sl">GAMES</div></div><div><div class="sv red">{"—" if prank is None else pos+str(prank)}</div><div class="sl">RANK</div></div></div></div><div class="bio"><div>Height: {mv("height")}</div><div>Weight: {mv("weight")} lbs</div><div>College: {mv("college_name","college")}</div><div>Age: {mv("age")}</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="yrbar">'+''.join(f'<div class="yr {"active" if y==year else ""}">{y}</div>' for y in years[:5])+'</div>',unsafe_allow_html=True)
    if w.empty or not fp: st.info(f'No weekly data available for {name} in {year}.')
    else:
        if 'week' in w:w=w.sort_values('week')
        st.markdown('<div class="gh"><div>WK</div><div>OPP</div><div>RES</div><div>FPTS</div><div>RUSH</div><div>REC</div><div>REC YDS</div><div>TD</div></div>',unsafe_allow_html=True); oppc=next((c for c in ['opponent_team','opponent','opp'] if c in w),None)
        for _,x in w.iterrows():
            def num(c):
                try:return int(float(x.get(c,0) or 0))
                except:return 0
            f=float(pd.to_numeric(pd.Series([x.get(fp,0)]),errors='coerce').fillna(0).iloc[0]); td=num('rushing_tds')+num('receiving_tds')+num('passing_tds'); st.markdown(f'<div class="gr"><div>{num("week")}</div><div>{x.get(oppc,"—") if oppc else "—"}</div><div>{x.get("result","—")}</div><div class="fp">{f:.1f}</div><div>{num("rushing_yards")}</div><div>{num("receptions")}</div><div>{num("receiving_yards")}</div><div>{td}</div></div>',unsafe_allow_html=True)
    nav('Players')

def mock():
    topbar('MOCK DRAFT','ESPN-style snake draft simulator')
    if not st.session_state.draft:
        with st.form('setup'):
            c1,c2=st.columns(2); teams=c1.selectbox('Teams',[10,12]); slot=c2.number_input('Draft Position',1,int(teams),1); c3,c4=st.columns(2); rounds=c3.selectbox('Rounds',[15,16,17,18],index=1); scoring=c4.selectbox('Scoring',['PPR','Half PPR','Standard']); start=st.form_submit_button('START MOCK',use_container_width=True)
        if start:
            cfg=DraftConfig(teams=int(teams),rounds=int(rounds),user_slot=int(slot),scoring=scoring); picks,nxt=advance_cpus(R,[],1,cfg); st.session_state.draft={'config':cfg.__dict__,'picks':picks,'next_pick':nxt}; st.rerun()
        nav('Draft'); return
    d=st.session_state.draft; cfg=DraftConfig(**d['config']); c1,c2,c3=st.columns(3)
    if c1.button('PLAYERS',use_container_width=True):st.session_state.mock_tab='Players'
    if c2.button('BOARD',use_container_width=True):st.session_state.mock_tab='Board'
    if c3.button('RESET',use_container_width=True):st.session_state.draft=None; st.rerun()
    if st.session_state.mock_tab=='Players':
        posbar(); df=score_board(R,d['picks'],cfg.user_slot,d['next_pick']).head(35); rows(df)
        for i,(_,r) in enumerate(df.head(12).iterrows(),1):
            if st.button(f'DRAFT {r.player_name}',key=f'draft_{i}',use_container_width=True) and pick_team(d['next_pick'],cfg.teams)==cfg.user_slot:
                d['picks'].append(make_pick(r.to_dict(),d['next_pick'],cfg.teams)); d['next_pick']+=1; d['picks'],d['next_pick']=advance_cpus(R,d['picks'],d['next_pick'],cfg); st.session_state.draft=d; st.rerun()
    else:
        matrix=board_matrix(d['picks'],cfg.teams,cfg.rounds); cells=[]
        for rnd,row in enumerate(matrix,1):
            for tm,p in enumerate(row,1):
                if p:
                    n=str(p.get('player_name','')); ps=clspos(p.get('position')); cells.append(f'<div class="bc {ps}"><div class="bp"><a href="?player={quote(n)}">{n}</a></div><div class="bpos">{ps}</div></div>')
                else:cells.append('<div class="bc empty"></div>')
        st.markdown(f'<div class="boardwrap"><div class="board" style="grid-template-columns:repeat({cfg.teams},1fr)">{"".join(cells)}</div></div>',unsafe_allow_html=True)
    nav('Draft')

def team():
    topbar('MY TEAM HQ','Watch list & league context'); sel=st.multiselect('Watch list',R.player_name.tolist(),default=st.session_state.watchlist); st.session_state.watchlist=sel; rows(R[R.player_name.isin(sel)].sort_values('adp').head(50)); nav('Team')
def sleepers(): topbar('SLEEPERS','Late-round upside'); rows(R[(R.adp>=45)&R.position.isin(['QB','RB','WR','TE'])].head(40)); nav('More')
def ask():
    topbar('ASK SHIVA GPT','Draft Intelligence'); q=st.text_area('Question',placeholder='I already drafted two RBs. Who should I target at 3.04?')
    if st.button('ASK SHIVA',use_container_width=True) and q.strip():
        key=os.getenv('OPENAI_API_KEY','')
        try:key=str(st.secrets.get('OPENAI_API_KEY',key))
        except:pass
        if not key:st.warning('Add OPENAI_API_KEY in Streamlit secrets.')
        else:
            ctx=build_context(rankings=R,watchlist=st.session_state.watchlist,draft=st.session_state.draft,history_summary=f'{len(H)} historical rows')
            try:st.write(ask_shiva(key,MODEL,q.strip(),ctx))
            except Exception as e:st.error(str(e))
    nav('Home')

p=st.session_state.page
if p=='Home':home()
elif p=='Draft Board':draft_board_page()
elif p=='Players':players_page()
elif p=='Profile':profile()
elif p=='Mock Draft':mock()
elif p=='Team':team()
elif p=='Sleepers':sleepers()
elif p=='Ask':ask()
else:home()

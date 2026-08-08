from __future__ import annotations
import os, re, sqlite3, unicodedata
from pathlib import Path
from urllib.parse import quote
import pandas as pd
import streamlit as st
from shiva_ai import ask_shiva, build_context
from shiva_draft import DraftConfig, advance_cpus, board_matrix, make_pick, pick_team, score_board

ROOT=Path(__file__).resolve().parent
RANKINGS=ROOT/'current_rankings.csv'; DB=ROOT/'shiva_draft_roi.sqlite'; MODEL='gpt-5-mini'
st.set_page_config(page_title='Shiva Intelligence',page_icon='🏆',layout='centered',initial_sidebar_state='collapsed')

st.markdown(r'''<style>
:root{--bg:#03101a;--panel:#071824;--line:#1c3b52;--lime:#d9ff00;--qb:#b42026;--rb:#d66a05;--wr:#0d78b7;--te:#348d38;--flex:#7d3fb5;--k:#3a4751;--def:#6e461f}
html,body,.stApp{background:linear-gradient(180deg,#02101b,#02080d)!important;color:#fff!important}.block-container{max-width:720px!important;padding:10px 16px 92px!important}#MainMenu,header,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}[data-testid="stHorizontalBlock"]{gap:14px!important}.appbar{padding:6px 4px 14px;border-bottom:1px solid #153449;margin-bottom:14px}.brand{font-size:27px;font-weight:1000;font-style:italic;letter-spacing:.06em;color:var(--lime)}.sub{font-size:15px;color:#e6edf2;margin-top:2px}.cardbtn .stButton button{height:178px!important;border-radius:16px!important;border:2px solid #2b526e!important;background:linear-gradient(145deg,#0b1b27,#07111a)!important;color:#fff!important;font-weight:1000!important;font-size:19px!important;white-space:pre-line!important;line-height:1.45!important}.gold .stButton button{border-color:#f0a000!important;background:linear-gradient(145deg,#281b00,#0a1118)!important}.purple .stButton button{border-color:#a64eff!important;background:linear-gradient(145deg,#22102c,#0a1118)!important}.cyan .stButton button{border-color:#29c7ff!important;background:linear-gradient(145deg,#062d3f,#0a1118)!important}.green .stButton button{border-color:#5add38!important;background:linear-gradient(145deg,#0d2b11,#0a1118)!important}.yellow .stButton button{border-color:#e7a700!important;background:linear-gradient(145deg,#302400,#0a1118)!important}.pink .stButton button{border-color:#f54484!important;background:linear-gradient(145deg,#30101d,#0a1118)!important}.askbox{border:2px solid #14709b;border-radius:16px;background:linear-gradient(135deg,#08243c,#071725);padding:20px;margin:18px 0}.asktitle{font-size:23px;font-weight:1000}.asksub{color:#d0dce5;font-size:15px;margin-top:5px}.league{border:1.5px solid #2a5068;border-radius:16px;background:#081724;padding:19px;margin:16px 0}.label{font-size:12px;color:#a8bbc8;font-weight:800}.league-name{font-size:22px;font-weight:1000;margin:6px 0}.news-title{font-size:20px;color:var(--lime);font-weight:1000;margin:28px 0 10px}.news-card{border:1.5px solid #23485f;border-radius:14px;background:#071824;padding:16px;margin:10px 0}.news-card b{font-size:16px}.news-card p{font-size:13px;color:#c6d1d9}.bottom{position:fixed;bottom:0;left:50%;transform:translateX(-50%);width:min(100%,720px);background:rgba(2,8,13,.97);border-top:1px solid #17364a;z-index:50;padding:8px 10px}.bottomgrid{display:grid;grid-template-columns:repeat(5,1fr);text-align:center}.bn{font-size:12px;color:#d8e0e6}.bn span{font-size:22px;display:block}.bn.active{color:var(--lime);font-weight:900}input,textarea,[data-baseweb="select"]>div{background:#081824!important;color:#fff!important;border-color:#23485f!important;border-radius:10px!important}.stButton button{border-radius:10px!important;font-weight:900!important}.poslegend{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin:12px 0}.pill{padding:8px 4px;border-radius:8px;text-align:center;color:#fff;font-weight:1000;font-size:12px}.QB{background:var(--qb)}.RB{background:var(--rb)}.WR{background:var(--wr)}.TE{background:var(--te)}.FLEX{background:var(--flex)}.K{background:var(--k)}.DEF{background:var(--def)}.rankhead,.rankrow{display:grid;grid-template-columns:38px minmax(0,1fr) 45px 48px 48px;gap:6px;align-items:center}.rankhead{font-size:10px;color:#c5d1d9;padding:5px}.rankrow{border-radius:8px;margin:4px 0;padding:10px;color:#fff}.rankrow.QB{background:#a81f24}.rankrow.RB{background:#d46804}.rankrow.WR{background:#0d77b3}.rankrow.TE{background:#338a36}.rankrow.FLEX{background:#7540a9}.rnum{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:rgba(0,0,0,.2);font-weight:1000}.rname{font-size:14px;font-weight:1000}.rname a{color:#fff;text-decoration:none}.rcell{text-align:center;font-size:12px;font-weight:900}.profile-title{font-size:24px;font-weight:1000;text-align:center}.profile-sub{text-align:center;color:#d6dfe5;font-size:12px}.profile-tabs{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #1d3648;margin:5px 0 10px}.pt{padding:10px 0;text-align:center;font-weight:900;font-size:12px}.pt.active{border-bottom:2px solid var(--lime)}.profile-card{border:1px solid #1f4057;border-radius:12px;background:#071620;padding:10px}.profile-top{display:grid;grid-template-columns:120px 1fr;gap:12px;align-items:center}.headshot{height:100px;display:flex;align-items:end;justify-content:center;overflow:hidden}.headshot img{max-width:100%;max-height:100px}.stats4{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;text-align:center}.sv{font-size:22px;font-weight:1000;color:#f2a51b}.sv.rank{color:#ff4560}.sl{font-size:9px}.bio{display:grid;grid-template-columns:repeat(4,1fr);font-size:10px;text-align:center;background:#05101a;border-radius:8px;padding:6px;margin-top:6px}.yearbar{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:8px 0}.yr{padding:7px;border:1px solid #29475c;background:#0a1b27;border-radius:7px;text-align:center;font-size:12px;font-weight:900}.yr.active{background:#0d69b1}.gameh,.gamer{display:grid;grid-template-columns:30px 46px 65px 46px 42px 36px 56px 30px;gap:4px;align-items:center}.gameh{font-size:9px;color:#d5dee4;font-weight:900;padding:4px 2px}.gamer{font-size:10px;padding:5px 2px;border-bottom:1px solid #173043}.fp{color:#22c9ff;font-weight:1000}.teamrow{display:grid;grid-template-columns:minmax(0,1fr) 42px 64px 56px;gap:7px;align-items:center;padding:11px 9px;border-bottom:1px solid #173043;background:#071824}.tmname{font-weight:1000}.tmmeta{font-size:11px;color:#acbbc6}.tmval{text-align:center;font-weight:900}.tmhead{font-size:10px;color:#9eb0bc;background:#06131e}.boardwrap{overflow-x:auto;border:1px solid #1d4056;border-radius:10px;background:#05101a;padding:6px}.board{display:grid;gap:3px;min-width:820px}.bcell{min-height:58px;border-radius:5px;padding:4px;color:#fff;text-align:center;font-size:9px}.bcell.QB{background:#a51e23}.bcell.RB{background:#ca6105}.bcell.WR{background:#0b6fa8}.bcell.TE{background:#347f34}.bcell.FLEX{background:#6c399b}.bcell.empty{background:#0b1720}.bp{font-weight:1000;font-size:9px}.bcell a{color:#fff;text-decoration:none}@media(max-width:520px){.block-container{padding:8px 10px 88px!important}.brand{font-size:21px}.sub{font-size:12px}.cardbtn .stButton button{height:126px!important;font-size:14px!important}.asktitle{font-size:18px}.profile-top{grid-template-columns:100px 1fr}.sv{font-size:17px}.gameh,.gamer{grid-template-columns:25px 38px 50px 40px 34px 30px 45px 24px;font-size:8px}.rname{font-size:12px}}
</style>''',unsafe_allow_html=True)

def norm(v):
    v=unicodedata.normalize('NFKD',str(v or '')).encode('ascii','ignore').decode().lower(); v=re.sub(r'\b(jr|sr|ii|iii|iv)\b\.?','',v); return re.sub(r'[^a-z0-9]+','',v)
@st.cache_data(show_spinner=False)
def rankings():
    df=pd.read_csv(RANKINGS)
    for c in ['adp','overall_rank','position_rank','bye']:
        if c in df.columns: df[c]=pd.to_numeric(df[c],errors='coerce')
    df['position']=df['position'].astype(str).str.upper().str.strip(); return df.sort_values(['adp','overall_rank'],na_position='last').reset_index(drop=True)
@st.cache_data(show_spinner=False)
def history():
    if not DB.exists(): return pd.DataFrame()
    try:
        with sqlite3.connect(DB) as con:return pd.read_sql_query('select * from draft_roi_scores',con)
    except Exception:return pd.DataFrame()
@st.cache_data(show_spinner=False,ttl=3600)
def weekly(year):
    try:df=pd.read_csv(f'https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_week_{year}.csv',low_memory=False)
    except Exception:return pd.DataFrame()
    nc=next((c for c in ['player_display_name','player_name','display_name','name'] if c in df.columns),None)
    if not nc:return pd.DataFrame()
    df['_name_key']=df[nc].map(norm); return df
@st.cache_data(show_spinner=False,ttl=86400)
def metadata():
    try:df=pd.read_csv('https://github.com/nflverse/nflverse-data/releases/download/players/players.csv',low_memory=False)
    except Exception:return pd.DataFrame()
    nc=next((c for c in ['display_name','full_name','player_name'] if c in df.columns),None)
    if nc:df['_name_key']=df[nc].map(norm)
    return df
R=rankings(); H=history()
for k,v in {'page':'Home','selected':'','return_page':'Home','draft':None,'mock_tab':'Players'}.items():
    if k not in st.session_state:st.session_state[k]=v

def go(p):st.session_state.page=p; st.rerun()
try:
    qp=st.query_params.get('player','')
    if qp:st.session_state.selected=qp; st.session_state.return_page=st.session_state.page; st.session_state.page='Profile'; st.query_params.clear()
except Exception:pass

def appbar():st.markdown('<div class="appbar"><div class="brand">SHIVA INTELLIGENCE</div><div class="sub">Your Draft Command Center</div></div>',unsafe_allow_html=True)
def bottom(active):
    h='<div class="bottom"><div class="bottomgrid">'
    for ico,label in [('⌂','Home'),('◉','Draft'),('♙','Players'),('♧','Team'),('•••','More')]:h+=f'<div class="bn {"active" if label==active else ""}"><span>{ico}</span>{label}</div>'
    st.markdown(h+'</div></div>',unsafe_allow_html=True)
def clspos(p):
    p=str(p).upper(); return p if p in {'QB','RB','WR','TE','FLEX','K','DEF'} else 'FLEX'
def poslegend():st.markdown('<div class="poslegend">'+''.join(f'<div class="pill {p}">{p}</div>' for p in ['QB','RB','WR','TE','FLEX','K','DEF'])+'</div>',unsafe_allow_html=True)
def rows(df):
    st.markdown('<div class="rankhead"><div>RK</div><div>PLAYER</div><div>POS</div><div>TEAM</div><div>ADP</div></div>',unsafe_allow_html=True)
    for i,(_,r) in enumerate(df.iterrows(),1):
        p=clspos(r.get('position','FLEX')); name=str(r.get('player_name','')); adp='—' if pd.isna(r.get('adp')) else f'{float(r.get("adp")):.1f}'
        st.markdown(f'<div class="rankrow {p}"><div class="rnum">{i}</div><div class="rname"><a href="?player={quote(name)}">{name}</a></div><div class="rcell">{p}</div><div class="rcell">{r.get("team","—")}</div><div class="rcell">{adp}</div></div>',unsafe_allow_html=True)

def home():
    appbar(); cards=[[("🏆\nDRAFT BOARD\n2026 Rankings",'Draft Board','gold'),("👥\nMOCK DRAFT\nPractice & Plan",'Mock Draft','purple'),("👤\nPLAYER PROFILES\nStats & Trends",'Players','cyan')],[("⭐\nMY TEAM HQ\nRoster & Lineup",'Team','green'),("🥷\nSLEEPERS\nHidden Gems",'Sleepers','yellow'),("📋\nCHEAT SHEETS\nKey Rankings",'Draft Board','pink')]]
    for ri,row in enumerate(cards):
        cols=st.columns(3)
        for c,(label,page,klass) in zip(cols,row):
            with c:
                st.markdown(f'<div class="cardbtn {klass}">',unsafe_allow_html=True)
                if st.button(label,key=f'h_{ri}_{page}',use_container_width=True):go(page)
                st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="askbox"><div class="asktitle">◉ &nbsp; ASK SHIVA GPT</div><div class="asksub">Ask questions, get advice, win your league. &nbsp; ›</div></div>',unsafe_allow_html=True)
    if st.button('ASK SHIVA GPT',key='askhome',use_container_width=True):go('Ask')
    st.markdown('<div class="league"><div class="label">MY LEAGUE</div><div class="league-name">Shiva</div><div class="sub">10-Team · Full PPR</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="news-title">LIVE FANTASY NEWS</div>',unsafe_allow_html=True)
    for t,b in [('Rookie QB Carson Beck delivers efficient debut for Cardinals','Carson Beck completed 15 of 19 passes for 188 yards and a touchdown in his debut.'),('2026 Indianapolis Colts training camp: Latest intel, updates','Follow current camp intel, position battles and potential fantasy breakouts.'),('2026 Los Angeles Rams training camp: Latest intel, updates','Follow current camp intel, position battles and potential fantasy breakouts.')]:st.markdown(f'<div class="news-card"><b>{t}</b><p>{b}</p></div>',unsafe_allow_html=True)
    bottom('Home')

def draft_board():
    appbar(); st.subheader('DRAFT BOARD'); st.caption('2026 Rankings'); c1,c2=st.columns([2,1]); q=c1.text_input('Search',placeholder='Search players...',label_visibility='collapsed'); pos=c2.selectbox('Position',['ALL','QB','RB','WR','TE'],label_visibility='collapsed'); poslegend(); df=R.copy();
    if pos!='ALL':df=df[df.position.eq(pos)]
    if q:df=df[df.player_name.astype(str).str.contains(q,case=False,na=False)]
    rows(df.head(60)); bottom('Draft')

def players_page():
    appbar(); st.subheader('PLAYER PROFILES'); st.caption('Stats & Trends'); q=st.text_input('Search player',placeholder='Search player...',label_visibility='collapsed'); df=R.copy();
    if q:df=df[df.player_name.astype(str).str.contains(q,case=False,na=False)]
    poslegend(); rows(df.head(60)); bottom('Players')

def profile():
    name=st.session_state.selected; rr=R[R.player_name.astype(str).map(norm).eq(norm(name))]; r=rr.iloc[0] if not rr.empty else None; team=str(r.team) if r is not None else '—'; pos=str(r.position) if r is not None else '—'; prank=int(r.position_rank) if r is not None and pd.notna(r.get('position_rank')) else None
    c1,c2,c3=st.columns([1,7,1]);
    with c1:
        if st.button('‹',key='pback'):go(st.session_state.return_page)
    with c2:st.markdown(f'<div class="profile-title">{name.upper()}</div><div class="profile-sub">{pos} • {team}</div>',unsafe_allow_html=True)
    with c3:st.markdown('⭐')
    st.markdown('<div class="profile-tabs"><div class="pt active">OVERVIEW</div><div class="pt">STATS</div><div class="pt">GAME LOG</div><div class="pt">NEWS</div></div>',unsafe_allow_html=True)
    years=[]
    for y in range(2025,2013,-1):
        df=weekly(y)
        if not df.empty and (df['_name_key']==norm(name)).any():years.append(y)
    if not years:years=[2025]
    year=st.selectbox('Season',years,format_func=lambda x:f'{x} (Year)',label_visibility='collapsed'); w=weekly(year)
    if not w.empty:
        w=w[w['_name_key'].eq(norm(name))].copy();
        if 'season_type' in w.columns:
            reg=w[w.season_type.astype(str).str.upper().eq('REG')]
            if not reg.empty:w=reg
    fp='fantasy_points_ppr' if 'fantasy_points_ppr' in w.columns else ('fantasy_points' if 'fantasy_points' in w.columns else None); pts=pd.to_numeric(w[fp],errors='coerce').fillna(0) if fp and not w.empty else pd.Series(dtype=float); total=float(pts.sum()) if len(pts) else 0; ppg=float(pts.mean()) if len(pts) else 0; games=len(w); meta=metadata(); m=None
    if not meta.empty and '_name_key' in meta.columns:
        mm=meta[meta['_name_key'].eq(norm(name))]
        if not mm.empty:m=mm.iloc[0]
    def mv(*cols):
        if m is None:return '—'
        for c in cols:
            if c in m.index and pd.notna(m[c]) and str(m[c]).strip() not in {'','nan'}:return str(m[c])
        return '—'
    head=mv('headshot','headshot_url'); img=f'<img src="{head}">' if head.startswith('http') else ''
    st.markdown(f'<div class="profile-card"><div class="profile-top"><div class="headshot">{img}</div><div class="stats4"><div><div class="sv">{total:.1f}</div><div class="sl">FPTS</div></div><div><div class="sv">{ppg:.1f}</div><div class="sl">PPG</div></div><div><div class="sv">{games}</div><div class="sl">GAMES</div></div><div><div class="sv rank">{"—" if prank is None else pos+str(prank)}</div><div class="sl">RANK</div></div></div></div><div class="bio"><div>Height: {mv("height")}</div><div>Weight: {mv("weight")} lbs</div><div>College: {mv("college_name","college")}</div><div>Age: {mv("age")}</div></div></div>',unsafe_allow_html=True); st.markdown('<div class="yearbar">'+''.join(f'<div class="yr {"active" if y==year else ""}">{y}</div>' for y in years[:5])+'</div>',unsafe_allow_html=True)
    if w.empty or not fp:st.info(f'No weekly data available for {name} in {year}.')
    else:
        if 'week' in w.columns:w=w.sort_values('week')
        st.markdown('<div class="gameh"><div>WK</div><div>OPP</div><div>RESULT</div><div>FPTS</div><div>RUSH</div><div>REC</div><div>REC YDS</div><div>TD</div></div>',unsafe_allow_html=True); oppc=next((c for c in ['opponent_team','opponent','opp'] if c in w.columns),None)
        for _,x in w.iterrows():
            def num(c):
                try:return int(float(x.get(c,0) or 0))
                except:return 0
            wk=num('week'); opp=str(x.get(oppc,'—')) if oppc else '—'; f=float(pd.to_numeric(pd.Series([x.get(fp,0)]),errors='coerce').fillna(0).iloc[0]); rush=num('rushing_yards'); rec=num('receptions'); ry=num('receiving_yards'); td=num('rushing_tds')+num('receiving_tds')+num('passing_tds'); res=str(x.get('result','—')); st.markdown(f'<div class="gamer"><div>{wk}</div><div>{opp}</div><div>{res}</div><div class="fp">{f:.1f}</div><div>{rush}</div><div>{rec}</div><div>{ry}</div><div>{td}</div></div>',unsafe_allow_html=True)
    bottom('Players')

def team_page():
    appbar(); st.subheader('MY TEAM HQ'); st.caption('Historical roster & performance')
    if H.empty:st.warning('Historical league database is unavailable.'); bottom('Team'); return
    lc=next((c for c in ['league_name','league'] if c in H.columns),None); mc=next((c for c in ['manager_name','owner_name','manager','owner'] if c in H.columns),None); yc=next((c for c in ['season','year'] if c in H.columns),None)
    if not all([lc,mc,yc]):st.warning('Historical database is missing league / manager / season fields.'); bottom('Team'); return
    c1,c2,c3=st.columns(3); leagues=sorted(H[lc].dropna().astype(str).unique()); league=c1.selectbox('League',leagues); h1=H[H[lc].astype(str).eq(str(league))]; managers=sorted(h1[mc].dropna().astype(str).unique()); manager=c2.selectbox('Manager / Owner',managers); h2=h1[h1[mc].astype(str).eq(str(manager))]; years=sorted(pd.to_numeric(h2[yc],errors='coerce').dropna().astype(int).unique(),reverse=True); year=c3.selectbox('Year',years); team=h2[pd.to_numeric(h2[yc],errors='coerce').eq(int(year))].copy(); pc=next((c for c in ['player_name','player'] if c in team.columns),None); posc=next((c for c in ['position','pos'] if c in team.columns),None); ppgc=next((c for c in ['ppg','points_per_game','fantasy_ppg'] if c in team.columns),None); rkc=next((c for c in ['position_finish_total','position_rank','pos_rank'] if c in team.columns),None); rc=next((c for c in ['round','draft_round'] if c in team.columns),None)
    if pc is None:st.info('No roster rows for this selection.'); bottom('Team'); return
    if rc:team[rc]=pd.to_numeric(team[rc],errors='coerce'); team=team.sort_values(rc,na_position='last')
    st.markdown('<div class="teamrow tmhead"><div>PLAYER</div><div>POS</div><div>POS RK</div><div>PPG</div></div>',unsafe_allow_html=True)
    for _,x in team.iterrows():
        name=str(x.get(pc,'—')); pos=str(x.get(posc,'—')) if posc else '—'; rk=x.get(rkc,'—') if rkc else '—'; ppg=x.get(ppgc,'—') if ppgc else '—'
        try:ppg=f'{float(ppg):.1f}'
        except:ppg=str(ppg)
        try:rk=int(float(rk))
        except:pass
        st.markdown(f'<div class="teamrow"><div><div class="tmname"><a style="color:white;text-decoration:none" href="?player={quote(name)}">{name}</a></div><div class="tmmeta">{league} · {manager} · {year}</div></div><div class="tmval">{pos}</div><div class="tmval">{rk}</div><div class="tmval">{ppg}</div></div>',unsafe_allow_html=True)
    bottom('Team')

def mock_page():
    appbar(); st.subheader('MOCK DRAFT')
    if not st.session_state.draft:
        with st.form('setup'):
            c1,c2=st.columns(2); teams=c1.selectbox('Teams',[10,12]); slot=c2.number_input('Draft Position',1,int(teams),1); c3,c4=st.columns(2); rounds=c3.selectbox('Rounds',[15,16,17,18],index=1); scoring=c4.selectbox('Scoring',['PPR','Half PPR','Standard']); start=st.form_submit_button('START MOCK',use_container_width=True)
        if start:
            cfg=DraftConfig(teams=int(teams),rounds=int(rounds),user_slot=int(slot),scoring=scoring); picks,next_pick=advance_cpus(R,[],1,cfg); st.session_state.draft={'config':cfg.__dict__,'picks':picks,'next_pick':next_pick}; st.rerun()
        bottom('Draft'); return
    d=st.session_state.draft; cfg=DraftConfig(**d['config']); c1,c2=st.columns(2)
    if c1.button('PLAYERS',use_container_width=True):st.session_state.mock_tab='Players'
    if c2.button('BOARD',use_container_width=True):st.session_state.mock_tab='Board'
    if st.session_state.mock_tab=='Players':
        poslegend(); df=score_board(R,d['picks'],cfg.user_slot,d['next_pick']).head(35); rows(df)
        for i,(_,r) in enumerate(df.head(12).iterrows(),1):
            if st.button(f'Draft {r.player_name}',key=f'd_{i}',use_container_width=True) and pick_team(d['next_pick'],cfg.teams)==cfg.user_slot:
                d['picks'].append(make_pick(r.to_dict(),d['next_pick'],cfg.teams)); d['next_pick']+=1; d['picks'],d['next_pick']=advance_cpus(R,d['picks'],d['next_pick'],cfg); st.session_state.draft=d; st.rerun()
    else:
        matrix=board_matrix(d['picks'],cfg.teams,cfg.rounds); cells=[]
        for rnd,row in enumerate(matrix,1):
            for team,p in enumerate(row,1):
                if p:
                    name=str(p.get('player_name','')); pos=clspos(p.get('position','FLEX')); cells.append(f'<div class="bcell {pos}"><div class="bp"><a href="?player={quote(name)}">{name}</a></div><div>{pos}</div></div>')
                else:cells.append('<div class="bcell empty"></div>')
        st.markdown(f'<div class="boardwrap"><div class="board" style="grid-template-columns:repeat({cfg.teams},1fr)">{"".join(cells)}</div></div>',unsafe_allow_html=True)
    bottom('Draft')

def sleepers():appbar(); st.subheader('SLEEPERS'); rows(R[(R.adp>=45)&R.position.isin(['QB','RB','WR','TE'])].head(35)); bottom('More')
def ask():
    appbar(); st.subheader('ASK SHIVA GPT'); q=st.text_area('Question',placeholder='Who should I draft at 3.04?')
    if st.button('ASK SHIVA',use_container_width=True) and q.strip():
        key=os.getenv('OPENAI_API_KEY','')
        try:key=str(st.secrets.get('OPENAI_API_KEY',key))
        except Exception:pass
        if not key:st.warning('Add OPENAI_API_KEY in Streamlit secrets.')
        else:
            ctx=build_context(rankings=R,watchlist=[],draft=None,history_summary=f'{len(H)} historical rows')
            try:st.write(ask_shiva(key,MODEL,q.strip(),ctx))
            except Exception as e:st.error(str(e))
    bottom('Home')

p=st.session_state.page
if p=='Home':home()
elif p=='Draft Board':draft_board()
elif p=='Players':players_page()
elif p=='Profile':profile()
elif p=='Team':team_page()
elif p=='Mock Draft':mock_page()
elif p=='Sleepers':sleepers()
elif p=='Ask':ask()
else:home()

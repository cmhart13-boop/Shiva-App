from __future__ import annotations

from pathlib import Path

source_path = Path(__file__).resolve().parent / "shiva_redesign.py"
source = source_path.read_text(encoding="utf-8")

SMOOTH_CSS = r'''
<style>
:root{--bg:#02070c;--panel:#07131c;--panel2:#0a1822;--line:#18364a;--lime:#d9ff00;--cyan:#28c5ff;--gold:#ffb61f;--purple:#ad63ff;--green:#55d64b;--pink:#ff5b9d}
html,body,.stApp{background:radial-gradient(circle at 50% -15%,rgba(22,120,180,.13),transparent 34%),linear-gradient(180deg,#02070c 0%,#041019 100%)!important}
.block-container{max-width:560px!important;padding:0 14px 90px!important}
[data-testid="stHorizontalBlock"]{gap:9px!important}
.appbar{position:sticky;top:0;z-index:30;margin:0 -14px 10px;padding:12px 14px 11px;background:rgba(2,7,12,.94);backdrop-filter:blur(18px);border-bottom:1px solid rgba(68,126,164,.24);text-align:center}
.brand{font-size:20px!important;line-height:1!important;text-align:center;color:var(--lime)!important;letter-spacing:.08em!important}
.sub{font-size:11px!important;text-align:center;color:#dce5eb!important;margin-top:5px!important}
.stButton button{min-height:46px!important;border-radius:12px!important;border:1px solid #1c3a4f!important;background:rgba(7,20,30,.86)!important;color:#f7fbff!important;box-shadow:none!important;transition:.15s ease!important}
.stButton button:active{transform:scale(.99)}
.featurebtn .stButton button{min-height:74px!important;width:100%!important;border-radius:16px!important;padding:12px 16px!important;text-align:left!important;justify-content:flex-start!important;white-space:pre-line!important;font-size:15px!important;line-height:1.2!important;font-weight:900!important;background:linear-gradient(100deg,rgba(10,24,34,.98),rgba(5,14,22,.92))!important;border-color:#1a3a4f!important}
.featurebtn .stButton button p{text-align:left!important;white-space:pre-line!important;line-height:1.25!important}
.featurebtn.gold .stButton button{border-left:3px solid var(--gold)!important}.featurebtn.purple .stButton button{border-left:3px solid var(--purple)!important}.featurebtn.cyan .stButton button{border-left:3px solid var(--cyan)!important}.featurebtn.green .stButton button{border-left:3px solid var(--green)!important}.featurebtn.yellow .stButton button{border-left:3px solid #ffd43b!important}.featurebtn.pink .stButton button{border-left:3px solid var(--pink)!important}
.quick-title{font-size:10px;color:#8298a7;letter-spacing:.14em;font-weight:900;margin:16px 2px 7px;text-transform:uppercase}
.askbox{border:1px solid #1c5276!important;border-radius:16px!important;background:linear-gradient(105deg,#08253c,#061521)!important;padding:15px 16px!important;margin:14px 0 8px!important}.asktitle{font-size:17px!important}.asksub{font-size:12px!important;color:#bfd0dc!important;margin-top:4px!important}
.league{border:1px solid #1b3b50!important;border-radius:14px!important;background:linear-gradient(100deg,#081620,#061018)!important;padding:15px 16px!important;margin:12px 0!important}.league-name{font-size:17px!important;margin:4px 0!important}.label{font-size:10px!important;letter-spacing:.1em!important}
.news-title{font-size:12px!important;color:#8ca1af!important;letter-spacing:.13em!important;margin:22px 2px 8px!important}.news-card{border:0!important;border-top:1px solid #173044!important;border-radius:0!important;background:transparent!important;padding:13px 2px!important;margin:0!important}.news-card b{font-size:14px!important}.news-card p{font-size:12px!important;margin-bottom:0!important;color:#9fb0bc!important}
.bottom{width:min(100%,560px)!important;padding:7px 8px 8px!important;background:rgba(2,7,12,.96)!important;border-top:1px solid rgba(51,101,135,.35)!important;backdrop-filter:blur(18px)}.bn{font-size:10px!important;color:#b8c5ce!important}.bn span{font-size:18px!important;margin-bottom:2px!important}.bn.active{color:var(--lime)!important}
.poslegend{gap:6px!important;margin:10px 0!important}.pill{padding:7px 3px!important;border-radius:7px!important;font-size:11px!important}
.rankhead{padding:6px 7px!important;border-bottom:1px solid #183347!important}.rankrow{border-radius:6px!important;margin:2px 0!important;padding:8px 7px!important;border:1px solid rgba(255,255,255,.06)!important}.rnum{width:26px!important;height:26px!important;font-size:11px!important}.rname{font-size:13px!important}.rcell{font-size:11px!important}
.profile-tabs{margin:2px 0 7px!important}.pt{font-size:10px!important;padding:9px 0!important}.profile-card{border-radius:8px!important;border-color:#19374b!important;background:linear-gradient(145deg,#07151f,#061018)!important;padding:8px!important}.profile-title{font-size:20px!important}.profile-sub{font-size:10px!important}.profile-top{grid-template-columns:108px 1fr!important;gap:8px!important}.headshot{height:84px!important}.headshot img{max-height:84px!important}.sv{font-size:18px!important}.bio{border-radius:5px!important;font-size:9px!important;padding:5px!important}.yearbar{gap:6px!important}.yr{border-radius:5px!important;padding:6px!important;font-size:10px!important}.gameh,.gamer{border-bottom:1px solid #142a3b!important}.gamer{padding:4px 2px!important}
.teamrow{background:transparent!important;padding:9px 5px!important}.boardwrap{border-radius:8px!important;background:#040d14!important}
@media(max-width:520px){.block-container{padding-left:10px!important;padding-right:10px!important}.appbar{margin-left:-10px!important;margin-right:-10px!important}.featurebtn .stButton button{min-height:68px!important;font-size:14px!important}.profile-top{grid-template-columns:96px 1fr!important}}
</style>
'''

source = source.replace("</style>''',unsafe_allow_html=True)", "</style>" + SMOOTH_CSS + "''',unsafe_allow_html=True)", 1)

start = source.index("def home():")
end = source.index("\ndef draft_board():", start)
NEW_HOME = r'''def home():
    appbar()
    st.markdown('<div class="quick-title">Draft tools</div>', unsafe_allow_html=True)
    tools=[
        ('🏆  DRAFT BOARD\n2026 rankings and ADP','Draft Board','gold'),
        ('◈  MOCK DRAFT\nPractice your slot and build a plan','Mock Draft','purple'),
        ('◎  PLAYER PROFILES\nStats, trends and weekly game logs','Players','cyan'),
        ('★  MY TEAM HQ\nRoster history and league context','Team','green'),
        ('⌁  SLEEPERS\nLate-round values and upside targets','Sleepers','yellow'),
        ('▤  CHEAT SHEETS\nFast rankings for draft day','Draft Board','pink'),
    ]
    for i,(label,page,klass) in enumerate(tools):
        st.markdown(f'<div class="featurebtn {klass}">', unsafe_allow_html=True)
        if st.button(label,key=f'smooth_{i}_{page}',use_container_width=True): go(page)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="askbox"><div class="asktitle">◉ &nbsp; ASK SHIVA GPT</div><div class="asksub">Ask a draft question, compare players, or pressure-test your next pick. &nbsp; ›</div></div>',unsafe_allow_html=True)
    if st.button('OPEN ASK SHIVA',key='askhome',use_container_width=True): go('Ask')
    st.markdown('<div class="league"><div class="label">MY LEAGUE</div><div class="league-name">Shiva</div><div class="sub">10-Team · Full PPR</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="news-title">LIVE FANTASY NEWS</div>',unsafe_allow_html=True)
    for t,b in [('Rookie QB Carson Beck delivers efficient debut for Cardinals','Carson Beck completed 15 of 19 passes for 188 yards and a touchdown in his debut.'),('2026 Indianapolis Colts training camp: Latest intel, updates','Follow current camp intel, position battles and potential fantasy breakouts.'),('2026 Los Angeles Rams training camp: Latest intel, updates','Follow current camp intel, position battles and potential fantasy breakouts.')]: st.markdown(f'<div class="news-card"><b>{t}</b><p>{b}</p></div>',unsafe_allow_html=True)
    bottom('Home')
'''
source = source[:start] + NEW_HOME + source[end:]

exec(compile(source, str(source_path), "exec"), globals(), globals())

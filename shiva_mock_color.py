from __future__ import annotations

from pathlib import Path

source_path = Path(__file__).resolve().parent / "shiva_espn.py"
source = source_path.read_text(encoding="utf-8")

MOCK_COLOR_CSS = r'''
<style>
/* Mock draft setup: preserve 2x2 layout, add distinct ESPN-style color treatments */
.st-key-mock_teams [data-baseweb="select"] > div {
    background: linear-gradient(135deg,#123f66,#0b263e) !important;
    border: 1px solid #2c91d0 !important;
    box-shadow: inset 0 0 0 1px rgba(44,145,208,.12), 0 6px 20px rgba(19,112,173,.12) !important;
}
.st-key-mock_slot [data-testid="stNumberInput"] input {
    background: linear-gradient(135deg,#46255f,#28143a) !important;
    border-color: #9b5bd0 !important;
    color: #fff !important;
}
.st-key-mock_slot [data-testid="stNumberInput"] button {
    background: #321a46 !important;
    border-color: #704493 !important;
    color: #fff !important;
}
.st-key-mock_rounds [data-baseweb="select"] > div {
    background: linear-gradient(135deg,#754116,#3c230f) !important;
    border: 1px solid #e58b35 !important;
    box-shadow: inset 0 0 0 1px rgba(229,139,53,.10), 0 6px 20px rgba(184,95,20,.10) !important;
}
.st-key-mock_scoring [data-baseweb="select"] > div {
    background: linear-gradient(135deg,#154b37,#0b2a20) !important;
    border: 1px solid #43b983 !important;
    box-shadow: inset 0 0 0 1px rgba(67,185,131,.10), 0 6px 20px rgba(39,147,99,.10) !important;
}
.st-key-mock_teams label,
.st-key-mock_slot label,
.st-key-mock_rounds label,
.st-key-mock_scoring label {
    color: #f8fbff !important;
    font-weight: 800 !important;
}
.st-key-mock_teams [data-baseweb="select"] span,
.st-key-mock_rounds [data-baseweb="select"] span,
.st-key-mock_scoring [data-baseweb="select"] span {
    color: #fff !important;
    font-weight: 800 !important;
}
.st-key-mock_teams svg,
.st-key-mock_rounds svg,
.st-key-mock_scoring svg { fill:#fff !important; }
.st-key-mock_start button {
    background: linear-gradient(90deg,#0d78ba,#6942b8) !important;
    border: 1px solid #48a8dc !important;
    color: #fff !important;
    box-shadow: 0 8px 22px rgba(40,100,190,.18) !important;
}
</style>
'''

source = source.replace("</style>'''\nst.markdown(CSS,unsafe_allow_html=True)", "</style>'''\nst.markdown(CSS,unsafe_allow_html=True)\nst.markdown(MOCK_COLOR_CSS,unsafe_allow_html=True)", 1)

old = """            c1,c2=st.columns(2); teams=c1.selectbox('Teams',[10,12]); slot=c2.number_input('Draft Position',1,int(teams),1); c3,c4=st.columns(2); rounds=c3.selectbox('Rounds',[15,16,17,18],index=1); scoring=c4.selectbox('Scoring',['PPR','Half PPR','Standard']); start=st.form_submit_button('START MOCK',use_container_width=True)"""
new = """            c1,c2=st.columns(2)
            with c1.container(key='mock_teams'):
                teams=st.selectbox('Teams',[10,12])
            with c2.container(key='mock_slot'):
                slot=st.number_input('Draft Position',1,int(teams),1)
            c3,c4=st.columns(2)
            with c3.container(key='mock_rounds'):
                rounds=st.selectbox('Rounds',[15,16,17,18],index=1)
            with c4.container(key='mock_scoring'):
                scoring=st.selectbox('Scoring',['PPR','Half PPR','Standard'])
            with st.container(key='mock_start'):
                start=st.form_submit_button('START MOCK',use_container_width=True)"""

if old not in source:
    raise RuntimeError('Mock setup block not found; refusing unrelated rewrite.')
source = source.replace(old, new, 1)

exec(compile(source, str(source_path), "exec"), globals(), globals())

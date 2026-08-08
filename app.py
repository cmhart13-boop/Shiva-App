from __future__ import annotations

from pathlib import Path
from player_profiles import render_player_profile, render_top_board

source_path = Path(__file__).resolve().parent / "main_app.py"
source = source_path.read_text(encoding="utf-8")

SPLASH = r'''
import base64
import time

if "_shiva_splash_seen" not in st.session_state:
    _asset_path = Path(__file__).resolve().parent / "assets" / "shiva_splash.b64"
    _splash_b64 = _asset_path.read_text(encoding="utf-8").strip()
    _splash = st.empty()
    _splash.markdown(
        f"""
        <style>
        .shiva-splash-overlay {{
            position: fixed;
            inset: 0;
            z-index: 2147483647;
            background: #05070c;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        .shiva-splash-overlay img {{
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            object-position: center center;
            display: block;
        }}
        @media (min-width: 520px) {{
            .shiva-splash-overlay img {{
                width: min(100vw, 480px);
                height: 100vh;
                object-fit: cover;
            }}
        }}
        </style>
        <div class="shiva-splash-overlay">
            <img src="data:image/jpeg;base64,{_splash_b64}" alt="Shiva loading screen" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(2.5)
    _splash.empty()
    st.session_state["_shiva_splash_seen"] = True
'''

source = source.replace('CSS = r"""', SPLASH + '\n\nCSS = r"""', 1)
source = source.replace(
    'st.error("Add OPENAI_API_KEY in Streamlit → App Settings → Secrets to activate Ask Shiva.")',
    'st.warning("Ask Shiva is ready. Add your OpenAI API key in Streamlit → App Settings → Secrets to turn on GPT answers.")',
    1,
)
source = source.replace(
    'if st.session_state.page == "Shiva Intelligence":',
    'if st.session_state.page == "Player Profile":\n    render_player_profile(st.session_state.get("selected_player", ""), rankings, history)\n\nelif st.session_state.page == "Shiva Intelligence":',
    1,
)
old_home_metrics = '''    top_rb = rankings[rankings.position.eq("RB")].head(1)\n    top_wr = rankings[rankings.position.eq("WR")].head(1)\n    st.markdown(f\'\'\'<div class="metric-grid"><div class="metric"><div class="metric-label">Players Loaded</div><div class="metric-value green">{len(rankings)}</div></div><div class="metric"><div class="metric-label">Historical Rows</div><div class="metric-value blue">{len(history):,}</div></div><div class="metric"><div class="metric-label">Top RB</div><div class="metric-value" style="font-size:14px">{top_rb.iloc[0].player_name if not top_rb.empty else \'—\'}</div></div><div class="metric"><div class="metric-label">Top WR</div><div class="metric-value" style="font-size:14px">{top_wr.iloc[0].player_name if not top_wr.empty else \'—\'}</div></div></div>\'\'\', unsafe_allow_html=True)'''
source = source.replace(old_home_metrics, '    render_top_board(rankings, "Shiva Intelligence")', 1)
exec(compile(source, str(source_path), "exec"), globals(), globals())

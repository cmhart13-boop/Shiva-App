from __future__ import annotations

from pathlib import Path

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
exec(compile(source, str(source_path), "exec"), globals(), globals())

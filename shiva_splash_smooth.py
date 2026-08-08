from __future__ import annotations

import base64
import time
from pathlib import Path

import streamlit as st

if "_shiva_splash_seen" not in st.session_state:
    asset_path = Path(__file__).resolve().parent / "assets" / "shiva_splash.b64"
    splash_b64 = asset_path.read_text(encoding="utf-8").strip()
    splash = st.empty()
    splash.markdown(
        f"""
        <style>
        .shiva-splash-overlay {{
            position: fixed;
            inset: 0;
            z-index: 2147483647;
            background: #020713;
            overflow: hidden;
        }}
        .shiva-splash-overlay img {{
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            object-position: center center;
            display: block;
        }}
        @media (min-width: 600px) {{
            .shiva-splash-overlay {{
                display: flex;
                justify-content: center;
                background: #020713;
            }}
            .shiva-splash-overlay img {{
                width: min(100vw, 560px);
            }}
        }}
        </style>
        <div class="shiva-splash-overlay">
            <img src="data:image/jpeg;base64,{splash_b64}" alt="Shiva Intelligence loading screen" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(2.5)
    splash.empty()
    st.session_state["_shiva_splash_seen"] = True

from shiva_smooth import *

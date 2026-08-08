from __future__ import annotations

import html
import re
import unicodedata
from typing import Any

import pandas as pd
import streamlit as st


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _int(value: Any, default: int | None = None) -> int | None:
    n = _num(value)
    return int(n) if n is not None else default


@st.cache_data(show_spinner=False, ttl=3600)
def _weekly(season: int) -> pd.DataFrame:
    url = f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_week_{int(season)}.csv"
    try:
        df = pd.read_csv(url)
    except Exception:
        return pd.DataFrame()
    name_col = next((c for c in ["player_display_name", "player_name", "display_name", "name"] if c in df.columns), None)
    if not name_col:
        return pd.DataFrame()
    df["_name_key"] = df[name_col].map(_norm)
    return df


@st.cache_data(show_spinner=False, ttl=21600)
def _roster(season: int) -> pd.DataFrame:
    url = f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{int(season)}.csv"
    try:
        df = pd.read_csv(url)
    except Exception:
        return pd.DataFrame()
    name_col = next((c for c in ["full_name", "player_name", "display_name", "name"] if c in df.columns), None)
    if not name_col:
        return pd.DataFrame()
    df["_name_key"] = df[name_col].map(_norm)
    return df


def _first_existing(row: pd.Series | None, names: list[str], default: Any = None) -> Any:
    if row is None:
        return default
    for c in names:
        if c in row.index and pd.notna(row[c]):
            return row[c]
    return default


def _player_roster_row(name: str, season: int) -> pd.Series | None:
    for yr in [season, 2026, 2025, 2024]:
        roster = _roster(yr)
        if roster.empty:
            continue
        match = roster[roster["_name_key"].eq(_norm(name))]
        if not match.empty:
            return match.iloc[0]
    return None


def _headshot_url(roster_row: pd.Series | None) -> str:
    direct = _first_existing(roster_row, ["headshot_url", "headshot", "player_headshot"])
    if direct:
        return str(direct)
    espn_id = _int(_first_existing(roster_row, ["espn_id", "espn_player_id"]))
    if espn_id:
        return f"https://a.espncdn.com/i/headshots/nfl/players/full/{espn_id}.png"
    return ""


def _team_logo(team: str) -> str:
    t = str(team or "").strip().lower()
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{t}.png" if t else ""


def _css() -> None:
    st.markdown(
        """
        <style>
        .block-container{padding-top:.5rem!important;max-width:920px!important}
        .pp-hero{position:relative;overflow:hidden;min-height:286px;border-radius:24px 24px 0 0;
          background:linear-gradient(180deg,#183047 0%,#202124 60%,#202124 100%);padding:34px 34px 18px;color:#fff}
        .pp-watermark{position:absolute;right:2%;top:-5%;font-size:13rem;font-weight:900;color:rgba(255,255,255,.025);line-height:1}
        .pp-name{position:relative;z-index:2;font-size:2.1rem;font-weight:900;letter-spacing:-.03em;margin:0 0 4px}
        .pp-meta{position:relative;z-index:2;font-size:1.25rem;color:#f3f3f3;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
        .pp-team-logo{width:34px;height:34px;object-fit:contain}
        .pp-headshot{position:absolute;z-index:1;right:2%;bottom:0;height:255px;max-width:48%;object-fit:contain;object-position:bottom right}
        .pp-metrics{position:relative;z-index:3;margin-top:150px;border:2px solid #47494b;border-radius:22px;background:#262728ee;
          display:grid;grid-template-columns:repeat(4,1fr);overflow:hidden;padding:18px 8px}
        .pp-metric{text-align:center;padding:0 5px}.pp-metric-value{font-size:2rem;font-weight:800;color:#fff;line-height:1.05}
        .pp-metric-label{font-size:.9rem;color:#aaa;margin-top:8px;text-transform:uppercase;white-space:nowrap}
        .pp-card{background:#242526;border-radius:22px;padding:26px 30px;margin-top:20px;color:#fff}
        .pp-card-top{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
        .pp-card-title{font-size:1.35rem;font-weight:850}.pp-subtle{color:#aaa}
        .pp-section-rule{border-top:1px dotted #505254;margin:18px 0}
        .pp-table-wrap{overflow-x:auto;margin:0 -30px -26px}.pp-table{width:100%;border-collapse:collapse;min-width:640px}
        .pp-table th{font-size:.9rem;color:#fff;text-align:center;padding:14px 10px;background:#1f2021;border-bottom:2px solid #343638}
        .pp-table td{text-align:center;padding:18px 10px;color:#b7b7b7;border-bottom:1px solid #282a2b;font-size:1rem}
        .pp-table tr:nth-child(odd) td{background:#292a2b}.pp-table tr:nth-child(even) td{background:#222324}
        .pp-table td.strong{font-weight:800;color:#c8c8c8}.pp-empty{padding:28px 8px;color:#aaa;text-align:center}
        div[role="radiogroup"]{display:flex!important;gap:0!important;justify-content:space-between!important;border-top:1px solid #3a3c3e;border-bottom:1px solid #3a3c3e;padding:10px 0 4px;margin-top:0}
        div[role="radiogroup"] label{font-weight:700!important;color:#a8a8a8!important}
        div[role="radiogroup"] label[data-baseweb="radio"]>div:first-child{display:none!important}
        @media(max-width:700px){
          .block-container{padding-left:0!important;padding-right:0!important}.pp-hero{border-radius:0;min-height:250px;padding:25px 18px 14px}
          .pp-name{font-size:1.75rem}.pp-meta{font-size:1.05rem}.pp-headshot{height:220px;max-width:53%}
          .pp-metrics{margin-top:126px;padding:14px 2px}.pp-metric-value{font-size:1.55rem}.pp-metric-label{font-size:.69rem}
          .pp-card{border-radius:18px;padding:22px 18px}.pp-table-wrap{margin-left:-18px;margin-right:-18px;margin-bottom:-22px}
          div[role="radiogroup"]{overflow-x:auto!important;justify-content:flex-start!important;gap:14px!important;padding-left:10px;padding-right:10px}
          div[role="radiogroup"] label{white-space:nowrap!important;font-size:.86rem!important}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def open_profile(name: str, return_page: str) -> None:
    st.session_state["selected_player"] = str(name)
    st.session_state["profile_return_page"] = return_page
    st.session_state["page"] = "Player Profile"
    st.rerun()


def render_top_board(rankings: pd.DataFrame, return_page: str = "Shiva Intelligence") -> None:
    st.markdown("### 2026 Top of the Board")
    st.caption("Tap a player for the full profile, prior-season summary and week-by-week scoring.")
    for i, (_, row) in enumerate(rankings.head(8).iterrows(), start=1):
        st.caption(f"#{i} overall · {row.position} · {row.team} · ADP {float(row.adp):.1f}")
        if st.button(str(row.player_name), key=f"top_board_profile_{i}", use_container_width=True):
            open_profile(str(row.player_name), return_page)


def _season_weekly(name: str, season: int) -> pd.DataFrame:
    weekly = _weekly(season)
    if weekly.empty:
        return weekly
    weekly = weekly[weekly["_name_key"].eq(_norm(name))].copy()
    if "season_type" in weekly.columns:
        reg = weekly[weekly["season_type"].astype(str).str.upper().eq("REG")]
        if not reg.empty:
            weekly = reg
    if "week" in weekly.columns:
        weekly["week"] = pd.to_numeric(weekly["week"], errors="coerce")
        weekly = weekly.sort_values("week")
    return weekly


def _fp_col(df: pd.DataFrame) -> str | None:
    return "fantasy_points_ppr" if "fantasy_points_ppr" in df.columns else ("fantasy_points" if "fantasy_points" in df.columns else None)


def _sum(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or df.empty:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


def _avg(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns or df.empty:
        return 0.0
    s = pd.to_numeric(df[col], errors="coerce")
    return float(s.mean()) if s.notna().any() else 0.0


def _hero(name: str, team: str, pos: str, pos_rank: int | None, adp: float | None, roster_row: pd.Series | None, current_weekly: pd.DataFrame) -> None:
    headshot = _headshot_url(roster_row)
    team_logo = _team_logo(team)
    jersey = _int(_first_existing(roster_row, ["jersey_number", "jersey", "number"]))
    fp = _fp_col(current_weekly)
    current_total = _sum(current_weekly, fp) if fp else 0.0
    current_avg = _avg(current_weekly, fp) if fp else 0.0
    rank_text = str(pos_rank) if pos_rank is not None else "—"
    adp_text = f"{adp:.1f}" if adp is not None else "—"
    team_logo_html = f'<img class="pp-team-logo" src="{html.escape(team_logo)}" />' if team_logo else ""
    headshot_html = f'<img class="pp-headshot" src="{html.escape(headshot)}" />' if headshot else ""
    number = f"#{jersey}" if jersey is not None else ""
    st.markdown(
        f"""
        <div class="pp-hero">
          <div class="pp-watermark">{html.escape(team)}</div>
          <div class="pp-name">{html.escape(str(name).upper())}</div>
          <div class="pp-meta">{team_logo_html}<span>{html.escape(team)} &nbsp;•&nbsp; {html.escape(pos)}{(' &nbsp;•&nbsp; ' + number) if number else ''}</span></div>
          {headshot_html}
          <div class="pp-metrics">
            <div class="pp-metric"><div class="pp-metric-value">{rank_text}</div><div class="pp-metric-label">POS RANK</div></div>
            <div class="pp-metric"><div class="pp-metric-value">{current_avg:.1f}</div><div class="pp-metric-label">AVG FPTS</div></div>
            <div class="pp-metric"><div class="pp-metric-value">{current_total:.1f}</div><div class="pp-metric-label">2026 FPTS</div></div>
            <div class="pp-metric"><div class="pp-metric-value">{adp_text}</div><div class="pp-metric-label">2026 ADP</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _game_log(name: str, pos: str, season: int, weekly: pd.DataFrame) -> None:
    fp = _fp_col(weekly)
    st.markdown('<div class="pp-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="pp-card-top"><div class="pp-card-title">{season} REGULAR SEASON</div><div class="pp-subtle">ESPN Full PPR</div></div><div class="pp-section-rule"></div>', unsafe_allow_html=True)
    if weekly.empty or not fp:
        st.markdown(f'<div class="pp-empty">No regular-season weekly data is available yet for {html.escape(name)} in {season}.</div></div>', unsafe_allow_html=True)
        return

    if pos.upper() == "QB":
        headers = ["WK", "OPP", "FPTS", "PASS YDS", "PASS TD", "I/F"]
        rows = []
        for _, w in weekly.iterrows():
            rows.append([
                _int(w.get("week"), 0), str(w.get("opponent_team", "—")), _num(w.get(fp), 0.0),
                _int(w.get("passing_yards"), 0), _int(w.get("passing_tds"), 0),
                f"{_int(w.get('interceptions'), 0)}/{_int(w.get('sack_fumbles_lost'), 0)}",
            ])
    elif pos.upper() in {"RB", "FB"}:
        headers = ["WK", "OPP", "FPTS", "RUSH YDS", "REC YDS", "TD"]
        rows = []
        for _, w in weekly.iterrows():
            rows.append([
                _int(w.get("week"), 0), str(w.get("opponent_team", "—")), _num(w.get(fp), 0.0),
                _int(w.get("rushing_yards"), 0), _int(w.get("receiving_yards"), 0),
                _int(w.get("rushing_tds"), 0) + _int(w.get("receiving_tds"), 0),
            ])
    else:
        headers = ["WK", "OPP", "FPTS", "REC", "YDS", "TD"]
        rows = []
        for _, w in weekly.iterrows():
            rows.append([
                _int(w.get("week"), 0), str(w.get("opponent_team", "—")), _num(w.get(fp), 0.0),
                _int(w.get("receptions"), 0), _int(w.get("receiving_yards"), 0), _int(w.get("receiving_tds"), 0),
            ])

    head = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body = ""
    for r in rows:
        cells = []
        for i, val in enumerate(r):
            if i == 2 and isinstance(val, (int, float)):
                text = f"{float(val):.1f}"
                cls = ' class="strong"'
            else:
                text = str(val)
                cls = ""
            cells.append(f"<td{cls}>{html.escape(text)}</td>")
        body += "<tr>" + "".join(cells) + "</tr>"
    st.markdown(f'<div class="pp-table-wrap"><table class="pp-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></div>', unsafe_allow_html=True)


def _stats_view(pos: str, season: int, weekly: pd.DataFrame) -> None:
    fp = _fp_col(weekly)
    total = _sum(weekly, fp) if fp else 0.0
    ppg = _avg(weekly, fp) if fp else 0.0
    games = int(len(weekly))
    st.markdown('<div class="pp-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="pp-card-title">{season} STATS</div><div class="pp-section-rule"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Games", games)
    c2.metric("PPR Points", f"{total:.1f}")
    c3.metric("PPR / Game", f"{ppg:.1f}")
    p = pos.upper()
    if p == "QB":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pass Yds", f"{_sum(weekly, 'passing_yards'):.0f}")
        c2.metric("Pass TD", f"{_sum(weekly, 'passing_tds'):.0f}")
        c3.metric("INT", f"{_sum(weekly, 'interceptions'):.0f}")
        c4.metric("Rush Yds", f"{_sum(weekly, 'rushing_yards'):.0f}")
    elif p in {"RB", "FB"}:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Carries", f"{_sum(weekly, 'carries'):.0f}")
        c2.metric("Rush Yds", f"{_sum(weekly, 'rushing_yards'):.0f}")
        c3.metric("Receptions", f"{_sum(weekly, 'receptions'):.0f}")
        c4.metric("Rec Yds", f"{_sum(weekly, 'receiving_yards'):.0f}")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Targets", f"{_sum(weekly, 'targets'):.0f}")
        c2.metric("Receptions", f"{_sum(weekly, 'receptions'):.0f}")
        c3.metric("Rec Yds", f"{_sum(weekly, 'receiving_yards'):.0f}")
        c4.metric("Rec TD", f"{_sum(weekly, 'receiving_tds'):.0f}")
    st.markdown('</div>', unsafe_allow_html=True)


def render_player_profile(name: str, rankings: pd.DataFrame, history: pd.DataFrame) -> None:
    _css()
    if st.button("← Back", key="player_profile_back"):
        st.session_state["page"] = st.session_state.get("profile_return_page", "Shiva Intelligence")
        st.rerun()

    ranked = rankings[rankings.player_name.astype(str).map(_norm).eq(_norm(name))] if not rankings.empty and "player_name" in rankings.columns else pd.DataFrame()
    row = ranked.iloc[0] if not ranked.empty else None
    team = str(_first_existing(row, ["team", "recent_team"], ""))
    pos = str(_first_existing(row, ["position", "pos"], ""))
    adp = _num(_first_existing(row, ["adp", "espn_adp"]))
    pos_rank = _int(_first_existing(row, ["position_rank", "pos_rank", "rank"])))

    hist = history.copy() if history is not None else pd.DataFrame()
    if not hist.empty and "player_name" in hist.columns:
        hist = hist[hist.player_name.map(_norm).eq(_norm(name))]
    seasons = sorted({int(x) for x in hist.get("season", pd.Series(dtype=float)).dropna().tolist() if int(x) <= 2025}, reverse=True)
    if not seasons:
        seasons = list(range(2025, 2012, -1))

    current_weekly = _season_weekly(name, 2026)
    roster_row = _player_roster_row(name, 2026)
    if not team:
        team = str(_first_existing(roster_row, ["team", "recent_team"], ""))
    if not pos:
        pos = str(_first_existing(roster_row, ["position", "pos"], ""))

    _hero(name, team, pos, pos_rank, adp, roster_row, current_weekly)

    tab = st.radio(
        "Player profile section",
        ["Overview", "News", "Stats", "Odds", "Game Log", "Projections"],
        index=4,
        horizontal=True,
        label_visibility="collapsed",
        key=f"profile_tab_{_norm(name)}",
    )

    left, right = st.columns([3, 1])
    with right:
        season = st.selectbox("Season", seasons, key=f"profile_year_{_norm(name)}", label_visibility="collapsed")
    weekly = _season_weekly(name, int(season))

    if tab == "Game Log":
        _game_log(name, pos, int(season), weekly)
    elif tab == "Stats":
        _stats_view(pos, int(season), weekly)
    elif tab == "Overview":
        _stats_view(pos, int(season), weekly)
        st.markdown('<div class="pp-card"><div class="pp-card-title">PLAYER OVERVIEW</div><div class="pp-section-rule"></div>', unsafe_allow_html=True)
        st.write(f"{name} · {team} · {pos}")
        if adp is not None:
            st.write(f"2026 ADP: {adp:.1f}")
        if pos_rank is not None:
            st.write(f"2026 position rank: {pos}{pos_rank}")
        st.markdown('</div>', unsafe_allow_html=True)
    elif tab == "Projections":
        proj_cols = [c for c in ["projected_points", "projection", "projected_fantasy_points", "fpts"] if row is not None and c in row.index and pd.notna(row[c])]
        st.markdown('<div class="pp-card"><div class="pp-card-title">2026 PROJECTIONS</div><div class="pp-section-rule"></div>', unsafe_allow_html=True)
        if proj_cols:
            st.metric("Projected PPR Points", f"{float(row[proj_cols[0]]):.1f}")
        else:
            st.info("No verified projection value is present in the app's current rankings feed for this player. No projection is being fabricated.")
        st.markdown('</div>', unsafe_allow_html=True)
    elif tab == "News":
        st.markdown('<div class="pp-card"><div class="pp-card-title">PLAYER NEWS</div><div class="pp-section-rule"></div>', unsafe_allow_html=True)
        st.info("A verified live player-news source is not connected to this app yet. The profile will not invent news headlines.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pp-card"><div class="pp-card-title">ODDS</div><div class="pp-section-rule"></div>', unsafe_allow_html=True)
        st.info("No verified live odds feed is connected. Odds are intentionally left blank rather than estimated.")
        st.markdown('</div>', unsafe_allow_html=True)

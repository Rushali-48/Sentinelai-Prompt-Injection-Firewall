import time
from datetime import datetime

import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SentinelAI | Prompt Injection Firewall",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "history": [],
    "last_result": None,
    "request_count": 0,
    "api_url": "http://127.0.0.1:8000/chat",
    "input_mode": "Message",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CUSTOM UI
# ============================================================

st.markdown(
    """
    <style>
        /* ---------- App ---------- */
        .stApp {
            background:
                radial-gradient(circle at 85% 5%, rgba(76, 175, 160, 0.10), transparent 24%),
                radial-gradient(circle at 10% 25%, rgba(80, 110, 255, 0.06), transparent 22%),
                #f7f9fc;
        }

        .block-container {
            max-width: min(1680px, 96vw);
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }

        /* ---------- Header ---------- */
        .hero {
            padding: 1.45rem 1.65rem;
            border: 1px solid #e5e9f2;
            border-radius: 22px;
            background: linear-gradient(135deg, #ffffff 0%, #f7fbfb 100%);
            box-shadow: 0 10px 30px rgba(25, 35, 55, 0.06);
            margin-bottom: 1rem;
        }

        .hero-row {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .shield {
            width: 54px;
            height: 54px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #101828;
            color: white;
            font-size: 27px;
        }

        .hero h1 {
            margin: 0;
            font-size: 2rem;
            color: #101828;
            letter-spacing: -0.5px;
        }

        .hero p {
            margin: 5px 0 0 0;
            color: #667085;
            font-size: 0.96rem;
        }

        /* ---------- Status cards ---------- */
        .status-card {
            border-radius: 17px;
            padding: 1rem 1.1rem;
            border: 1px solid #e5e9f2;
            background: white;
            min-height: 105px;
            box-shadow: 0 6px 20px rgba(25, 35, 55, 0.04);
        }

        .status-label {
            color: #667085;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: .7px;
        }

        .status-value {
            color: #101828;
            font-size: 1.45rem;
            font-weight: 800;
            margin-top: 5px;
        }

        .status-sub {
            color: #667085;
            font-size: .78rem;
            margin-top: 2px;
        }

        /* ---------- Security banner ---------- */
        .decision {
            border-radius: 18px;
            padding: 1.15rem 1.3rem;
            margin: .35rem 0 1rem 0;
            border: 1px solid #e5e9f2;
            background: white;
        }

        .decision-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #101828;
        }

        .decision-text {
            color: #667085;
            margin-top: 3px;
        }

        .decision.sanitize {
            border-left: 6px solid #d97706;
        }

        .decision.allow {
            border-left: 6px solid #15803d;
        }

        .decision.block {
            border-left: 6px solid #dc2626;
        }

        /* ---------- Attack pills ---------- */
        .attack-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 9px 0 2px 0;
        }

        .attack-pill {
            display: inline-block;
            padding: 7px 11px;
            border-radius: 999px;
            background: #fff3e8;
            color: #9a4f00;
            border: 1px solid #ffd8b0;
            font-size: .82rem;
            font-weight: 750;
        }

        /* ---------- Source chips ---------- */
        .source-chip {
            display: inline-block;
            margin: 4px 6px 4px 0;
            padding: 6px 9px;
            border-radius: 9px;
            background: #f2f4f7;
            color: #344054;
            font-size: .78rem;
            border: 1px solid #eaecf0;
        }

        /* ---------- Explanation ---------- */
        .reason-box {
            background: #f8fafc;
            border: 1px solid #e4e7ec;
            border-radius: 14px;
            padding: 1rem 1.05rem;
            color: #344054;
            line-height: 1.55;
        }

        /* ---------- Footer ---------- */
        .footer {
            text-align: center;
            color: #98a2b3;
            font-size: .76rem;
            padding-top: 1.2rem;
        }

        /* ---------- Compact analysis panel (right column, beside the form) ---------- */
        .mini-panel {
            border: 1px solid #e5e9f2;
            border-radius: 16px;
            background: white;
            padding: .9rem 1rem;
            box-shadow: 0 6px 20px rgba(25, 35, 55, 0.04);
        }

        .mini-decision {
            border-radius: 12px;
            padding: .7rem .85rem;
            margin-bottom: .7rem;
            border: 1px solid #e5e9f2;
            background: #f8fafc;
        }
        .mini-decision.allow { border-left: 4px solid #15803d; background: #f3fbf5; }
        .mini-decision.sanitize { border-left: 4px solid #d97706; background: #fffaf0; }
        .mini-decision.block { border-left: 4px solid #dc2626; background: #fff5f5; }

        .mini-decision-title { font-size: .95rem; font-weight: 800; color: #101828; }
        .mini-decision-meta { font-size: .74rem; color: #667085; margin-top: 3px; line-height: 1.4; }

        .mini-section-title {
            font-size: .7rem; font-weight: 800; color: #667085;
            text-transform: uppercase; letter-spacing: .6px;
            margin: .65rem 0 .3rem;
        }

        .mini-pill-wrap { display: flex; flex-wrap: wrap; gap: 5px; }
        .mini-pill {
            display: inline-block; padding: 3px 8px; border-radius: 999px;
            background: #fff3e8; color: #9a4f00; border: 1px solid #ffd8b0;
            font-size: .68rem; font-weight: 750;
        }
        .mini-risk {
            display: inline-block; padding: 2px 8px; border-radius: 6px;
            font-size: .68rem; font-weight: 800;
        }
        .mini-risk.low { background: #dcfce7; color: #15803d; }
        .mini-risk.medium { background: #ffedd5; color: #9a4f00; }
        .mini-risk.high { background: #fee2e2; color: #b42318; }

        .mini-reason {
            background: #f8fafc; border: 1px solid #e4e7ec; border-radius: 10px;
            padding: .5rem .6rem; color: #344054; font-size: .72rem; line-height: 1.5;
        }

        .mini-span {
            background: #fff5f5; border: 1px solid #fecaca; border-left: 3px solid #ef4444;
            border-radius: 8px; padding: .4rem .55rem; margin-top: .35rem;
            color: #7f1d1d; font-size: .68rem; line-height: 1.4; word-break: break-word;
        }

        .mini-metric-row {
            display: flex; justify-content: space-between; align-items: center;
            font-size: .72rem; color: #344054; padding: 3px 0;
        }
        .mini-metric-row b { color: #101828; }

        .empty-panel {
            display: flex; align-items: center; justify-content: center; text-align: center;
            min-height: 300px; color: #98a2b3; flex-direction: column;
        }
        .empty-panel .icon { font-size: 30px; margin-bottom: 8px; }
        .empty-panel .title { color: #344054; font-size: .92rem; font-weight: 750; }
        .empty-panel .sub { font-size: .74rem; margin-top: 4px; line-height: 1.5; max-width: 260px; }

        /* ---------- Sidebar: how-it-works steps (small, readable) ---------- */
        .side-step {
            font-size: .74rem;
            line-height: 1.5;
            color: #344054;
            margin-bottom: .5rem;
        }
        .side-step b { color: #101828; }


        /* ---------- Compact layout tuning ---------- */
        .block-container {
            max-width: min(1680px, 96vw);
            padding-top: 0.45rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1.1rem !important;
            padding-right: 1.1rem !important;
        }

        /* Reduce vertical gaps created by Streamlit elements */
        div[data-testid="stVerticalBlock"] {
            gap: 0.45rem;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.8rem;
        }

        .hero {
            padding: 0.85rem 1.2rem;
            border-radius: 18px;
            margin-bottom: 0.55rem;
        }

        .hero-row {
            gap: 11px;
        }

        .shield {
            width: 48px;
            height: 48px;
            border-radius: 13px;
            font-size: 23px;
        }

        .hero h1 {
            font-size: 1.75rem;
        }

        .hero p {
            margin-top: 2px;
            font-size: 0.84rem;
        }

        .status-card {
            min-height: 82px;
            padding: 0.72rem 0.9rem;
            border-radius: 14px;
        }

        .status-label {
            font-size: 0.68rem;
        }

        .status-value {
            font-size: 1.18rem;
            margin-top: 2px;
        }

        .status-sub {
            font-size: 0.70rem;
        }

        /* Tighten headings and section spacing */
        h1, h2, h3 {
            margin-top: 0.15rem !important;
            margin-bottom: 0.35rem !important;
        }

        .stSubheader {
            margin-top: 0 !important;
            margin-bottom: 0.3rem !important;
        }

        hr {
            margin: 0.55rem 0 !important;
        }

        /* Compact input area without changing its content */
        textarea {
            max-height: 155px !important;
        }

        /* Compact result card */
        .mini-panel {
            padding: 0.72rem 0.82rem;
            border-radius: 14px;
        }

        .mini-decision {
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.45rem;
        }

        .mini-section-title {
            margin: 0.45rem 0 0.22rem;
        }

        .mini-reason {
            padding: 0.42rem 0.52rem;
        }

        .mini-span {
            padding: 0.34rem 0.48rem;
            margin-top: 0.25rem;
        }

        .empty-panel {
            min-height: 210px;
        }

        /* Compact audit area */
        [data-testid="stTabs"] {
            margin-top: -0.15rem;
        }

        [data-testid="stTextArea"] textarea {
            max-height: 165px !important;
        }

        /* Compact sidebar styling without controlling open/closed state */
        section[data-testid="stSidebar"] {
            padding-top: 0.45rem;
        }

        section[data-testid="stSidebar"] hr {
            margin: 0.45rem 0 !important;
        }


        /* ---------- Compact professional analysis ---------- */
        .mini-panel {
            background: rgba(255,255,255,.82) !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 16px !important;
            padding: .72rem .82rem !important;
            box-shadow: 0 6px 20px rgba(20, 35, 60, .045) !important;
        }

        .analysis-row {
            display: grid;
            grid-template-columns: 112px minmax(0, 1fr);
            align-items: start;
            column-gap: 10px;
            padding: .28rem 0;
            border-bottom: 1px solid #edf1f6;
            font-size: .76rem;
            line-height: 1.42;
        }

        .analysis-row:last-child {
            border-bottom: 0;
        }

        .analysis-row-top {
            align-items: start;
        }

        .analysis-label {
            color: #667085;
            font-weight: 800;
            white-space: nowrap;
        }

        .analysis-value {
            color: #344054;
            min-width: 0;
            overflow-wrap: anywhere;
        }

        .analysis-value.emphasis {
            color: #9a4d00;
            font-weight: 750;
        }

        .risk-text {
            font-weight: 800;
        }

        .risk-text.low { color: #15803d; }
        .risk-text.medium { color: #b45309; }
        .risk-text.high { color: #c62828; }

        .reason-inline {
            color: #475467;
        }

        .malicious-inline {
            color: #a52828;
            background: #fff5f5;
            border: 1px solid #fecaca;
            border-left: 3px solid #ef4444;
            border-radius: 8px;
            padding: .34rem .48rem;
        }

        .span-item {
            display: inline;
        }

        .source-inline {
            color: #475467;
            font-weight: 650;
        }

        .meta-dot {
            color: #98a2b3;
            padding: 0 .2rem;
        }

        .mini-decision {
            border-radius: 11px !important;
            margin-bottom: .45rem !important;
            padding: .58rem .7rem !important;
        }

        .mini-decision-title {
            font-size: .9rem !important;
        }

        .mini-decision-meta {
            font-size: .7rem !important;
        }

        /* Give the whole app a subtle dashboard background rather than flat white. */
        .stApp {
            background:
                radial-gradient(circle at 88% 8%, rgba(79, 125, 255, .055), transparent 24%),
                radial-gradient(circle at 8% 45%, rgba(50, 180, 170, .045), transparent 22%),
                #f4f7fb !important;
        }

        /* Keep the main workspace cards distinct from the page background. */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255,255,255,.88) !important;
            border: 1px solid #dce4ef !important;
            box-shadow: 0 8px 24px rgba(20, 35, 60, .045) !important;
        }

        /* Avoid a giant empty result area before/after analysis. */
        .empty-panel {
            min-height: 180px !important;
        }


        /* Compact fields only: Attack type, Risk level, Input source */
        .compact-result-row {
            display: flex;
            align-items: baseline;
            gap: 8px;
            padding: .22rem 0;
            font-size: .76rem;
            line-height: 1.35;
        }

        .compact-result-label {
            flex: 0 0 auto;
            color: #667085;
            font-weight: 800;
            white-space: nowrap;
        }

        .compact-result-value {
            min-width: 0;
            overflow-wrap: anywhere;
            font-weight: 700;
        }

        .attack-value {
            color: #9a4d00;
        }

        .risk-value.low { color: #15803d; }
        .risk-value.medium { color: #b45309; }
        .risk-value.high { color: #c62828; }

        .source-value {
            color: #475467;
        }

        .input-source-row {
            border-top: 1px solid #edf1f6;
            margin-top: .35rem;
            padding-top: .42rem;
        }

        /* Keep Reason and Malicious span(s) as their existing block UI. */
        .mini-reason {
            padding: .55rem .62rem !important;
            border: 1px solid #dfe5ed !important;
            border-radius: 10px !important;
            background: #f8fafc !important;
            color: #475467 !important;
            line-height: 1.48 !important;
        }

        .mini-span {
            padding: .48rem .58rem !important;
            border: 1px solid #fecaca !important;
            border-left: 3px solid #ef4444 !important;
            border-radius: 9px !important;
            background: #fff7f7 !important;
            color: #a52828 !important;
            line-height: 1.42 !important;
        }


        /* ============================================================
           FINAL VISUAL POLISH
           CSS only — no application/content changes
           ============================================================ */

        /* Streamlit top chrome: keep the native sidebar toggle, but
           remove the large empty band above the application. */
        header[data-testid="stHeader"] {
            height: 2.35rem !important;
            min-height: 2.35rem !important;
            background: transparent !important;
            border-bottom: 0 !important;
        }

        /* Keep Streamlit's header/toolbar DOM intact so its native sidebar
           open/close controls continue to work. */

        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0 !important;
        }

        .block-container {
            max-width: 1640px !important;
            padding-top: .25rem !important;
            padding-bottom: .8rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Softer professional dashboard background */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main {
            background:
                radial-gradient(circle at 88% 0%, rgba(67, 112, 220, .065), transparent 25%),
                radial-gradient(circle at 8% 55%, rgba(58, 132, 150, .04), transparent 22%),
                #e9eef5 !important;
        }

        /* Keep the sidebar visually connected to the same light dashboard theme. */
        section[data-testid="stSidebar"] {
            background: #edf1f6 !important;
            border-right: 1px solid #dbe2ec !important;
        }

        /* Slightly softened cards so the page is not dominated by pure white. */
        .hero,
        .status-card,
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(248, 250, 253, .94) !important;
        }

        /* Header/hero: compact but not clipped */
        .hero {
            padding: .72rem 1.05rem !important;
            margin-bottom: .55rem !important;
            min-height: 92px !important;
            border-radius: 18px !important;
        }

        .hero-row {
            gap: 12px !important;
        }

        .shield {
            width: 48px !important;
            height: 48px !important;
            flex: 0 0 48px !important;
        }

        .hero h1 {
            font-size: 1.72rem !important;
            line-height: 1.05 !important;
            margin: 0 !important;
        }

        .hero p {
            font-size: .82rem !important;
            margin-top: 3px !important;
            line-height: 1.3 !important;
        }

        /* Status cards: aligned, compact and separated from workspace */
        .status-card {
            min-height: 86px !important;
            padding: .68rem .82rem !important;
            border-radius: 14px !important;
        }

        .status-value {
            font-size: 1.12rem !important;
        }

        /* Add a small, consistent visual gap before the two main panels */
        [data-testid="stVerticalBlockBorderWrapper"] {
            margin-top: .35rem !important;
            background: rgba(255,255,255,.92) !important;
            border: 1px solid #d8e1ed !important;
            border-radius: 16px !important;
            box-shadow: 0 7px 22px rgba(23, 43, 77, .055) !important;
        }

        /* Equal workspace columns already exist; make their cards feel
           balanced rather than making one side visually heavier. */
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0 !important;
        }

        /* Main section headings */
        h3 {
            font-size: 1.38rem !important;
            line-height: 1.15 !important;
            margin: .05rem 0 .45rem !important;
        }

        /* Existing message field: actually enforce the compact height */
        [data-testid="stTextArea"] textarea {
            height: 165px !important;
            min-height: 165px !important;
            max-height: 165px !important;
        }

        /* Don't let the input controls create unnecessary vertical gaps */
        [data-testid="stRadio"] {
            margin-bottom: .05rem !important;
        }

        /* Existing Analysis Results block: keep its structure, just give
           each field enough breathing room to avoid the cramped appearance. */
        .mini-panel {
            padding: .78rem .86rem !important;
        }

        .mini-decision {
            margin-bottom: .55rem !important;
            padding: .66rem .76rem !important;
        }

        .mini-decision-title {
            font-size: .92rem !important;
        }

        .mini-decision-meta {
            margin-top: 4px !important;
            font-size: .71rem !important;
        }

        .compact-result-row {
            padding: .32rem 0 !important;
            line-height: 1.45 !important;
        }

        .compact-result-label {
            color: #596780 !important;
            min-width: 105px;
        }

        .compact-result-value {
            font-weight: 750 !important;
        }

        /* Preserve the existing Reason block */
        .mini-section-title {
            margin: .48rem 0 .25rem !important;
            font-size: .72rem !important;
            letter-spacing: .45px !important;
        }

        .mini-reason {
            padding: .58rem .65rem !important;
            line-height: 1.48 !important;
            border-radius: 10px !important;
        }

        /* Preserve the existing Malicious Span block */
        .mini-span {
            padding: .5rem .62rem !important;
            margin-top: .3rem !important;
            line-height: 1.45 !important;
            border-radius: 9px !important;
        }

        /* Input source stays inside the Analysis Results panel */
        .input-source-row {
            margin-top: .45rem !important;
            padding-top: .5rem !important;
        }

        /* Empty analysis state should occupy the same visual weight without
           creating a huge blank area. */
        .empty-panel {
            min-height: 185px !important;
        }

        /* Sidebar appearance only. Streamlit owns the open/close state. */
        section[data-testid="stSidebar"] {
            padding-top: .35rem !important;
            background: #e9eef5 !important;
            border-right: 1px solid #d5deea !important;
        }

        section[data-testid="stSidebar"] hr {
            margin: .4rem 0 !important;
        }

        /* Do not hide, disable, resize, transform, or override Streamlit's
           native sidebar controls. */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"] {
            pointer-events: auto !important;
            z-index: 1000000 !important;
        }

        /* When Streamlit renders the collapsed-state control, keep it above
           the dashboard and clickable. */
        [data-testid="stSidebarCollapsedControl"] {
            position: fixed !important;
            top: .45rem !important;
            left: .45rem !important;
            z-index: 1000000 !important;
        }

        header[data-testid="stHeader"] {
            overflow: visible !important;
            z-index: 999999 !important;
        }

        /* Primary action: professional, compact, not oversized */
        .stButton > button[kind="primary"] {
            min-height: 42px !important;
            border-radius: 10px !important;
            font-weight: 800 !important;
        }

        /* ---------- Balanced workspace panels ---------- */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255,255,255,.78);
            border: 1px solid #dfe6f1 !important;
            border-radius: 16px !important;
            padding: .8rem !important;
            box-shadow: 0 5px 18px rgba(25,35,55,.035);
        }

        .mini-panel {
            border: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
            padding: 0 !important;
        }

        .mini-decision {
            padding: .62rem .72rem;
            margin-bottom: .42rem;
        }

        .mini-section-title {
            margin: .45rem 0 .2rem;
        }

        .mini-reason {
            padding: .48rem .58rem;
            font-size: .71rem;
            line-height: 1.42;
        }

        .mini-span {
            padding: .38rem .5rem;
            margin-top: .27rem;
            font-size: .69rem;
            line-height: 1.38;
        }

        /* Equal, readable workspace headings */
        h3 {
            font-size: 1.45rem !important;
            line-height: 1.15 !important;
            margin-top: 0 !important;
            margin-bottom: .4rem !important;
        }

        /* Keep the existing message area compact */
        textarea {
            height: 155px !important;
            min-height: 155px !important;
            max-height: 155px !important;
        }

        /* Existing source information inside analysis card */
        .analysis-sources {
            border-top: 1px solid #e7ebf2;
            margin-top: .6rem;
            padding-top: .45rem;
        }

        .analysis-sources-title {
            font-size: .69rem;
            font-weight: 800;
            color: #667085;
            text-transform: uppercase;
            letter-spacing: .6px;
            margin-bottom: .2rem;
        }

        /* ---------- Hide Streamlit chrome ---------- */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

SUPPORTED_EXTENSIONS = [
    "txt",
    "md",
    "pdf",
    "docx",
    "html",
    "htm",
    "py",
    "js",
    "ts",
    "java",
    "cpp",
    "c",
    "h",
    "cs",
    "go",
    "rs",
    "php",
    "rb",
    "sql",
    "json",
    "xml",
    "yaml",
    "yml",
    "sh",
    "bat",
    "png",
    "jpg",
    "jpeg",
    "webp",
    "bmp",
    "tiff",
    "tif",
]


def normalize_result(result):
    """Make backend responses safe for the UI."""
    if not isinstance(result, dict):
        return {}

    result.setdefault("decision", "UNKNOWN")
    result.setdefault("status", "unknown")
    result.setdefault("attack_types", [])
    result.setdefault("malicious_spans", [])
    result.setdefault("risk_level", "low")
    result.setdefault("reason", "")
    result.setdefault("original_content", "")
    result.setdefault("sanitized_content", None)
    result.setdefault("ai_response", None)
    result.setdefault("sources", [])

    return result


def decision_label(decision):
    if decision == "ALLOW":
        return "SAFE TO PROCEED"
    if decision == "SANITIZE":
        return "THREAT REMOVED"
    if decision == "BLOCK":
        return "REQUEST BLOCKED"
    return decision


def risk_label(risk):
    return str(risk or "low").upper()


def source_summary(sources):
    if not sources:
        return "Direct input"

    names = []
    for source in sources:
        source_type = source.get("source_type", "unknown")
        source_name = source.get("source_name")
        names.append(source_name or source_type)

    return ", ".join(names)


def call_backend(text_value, uploaded_file):
    """Send exactly the input types supported by the existing FastAPI /chat endpoint."""
    files = None
    data = {}

    if text_value and text_value.strip():
        data["content"] = text_value

    if uploaded_file is not None:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            )
        }

    started = time.perf_counter()

    response = requests.post(
        st.session_state.api_url,
        data=data,
        files=files,
        timeout=180,
    )

    elapsed = time.perf_counter() - started

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}

    if response.status_code != 200:
        detail = payload.get("detail", "SentinelAI API request failed.")
        raise RuntimeError(f"{detail} (HTTP {response.status_code})")

    return normalize_result(payload), elapsed


def save_history(result, elapsed, source_label):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "decision": result.get("decision", "UNKNOWN"),
        "attack_types": result.get("attack_types", []),
        "risk_level": result.get("risk_level", "low"),
        "source": source_label,
        "elapsed": elapsed,
        "result": result,
    }

    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:8]
    st.session_state.request_count += 1
    st.session_state.last_result = result


def render_sources(sources):
    if not sources:
        st.caption("Source: direct text input")
        return

    chips = []
    for item in sources:
        source_type = item.get("source_type", "unknown")
        source_name = item.get("source_name")

        if source_name:
            label = f"{source_type} · {source_name}"
        else:
            label = source_type

        chips.append(f'<span class="source-chip">{label}</span>')

    st.markdown(
        "".join(chips),
        unsafe_allow_html=True,
    )


def render_compact_analysis(result, elapsed):
    """Compact analysis result shown beside the submit form."""
    decision = result.get("decision", "UNKNOWN")
    attacks = result.get("attack_types") or []
    risk = str(result.get("risk_level", "low")).lower()
    reason = result.get("reason", "")
    spans = result.get("malicious_spans") or []
    detector = result.get("detector") or {}

    css_class = {"ALLOW": "allow", "SANITIZE": "sanitize", "BLOCK": "block"}.get(
        decision, ""
    )
    icon = {"ALLOW": "✓", "SANITIZE": "⚠", "BLOCK": "⛔"}.get(decision, "•")
    risk_class = risk if risk in ("low", "medium", "high") else "low"

    attack_text = (
        ", ".join(a.replace("_", " ").title() for a in attacks)
        if attacks
        else "None identified"
    )

    source_values = []
    for source in result.get("sources", []) or []:
        if isinstance(source, dict):
            # FastAPI returns source_type/source_name, while some older
            # responses may use type/name. Support both without changing
            # the backend contract.
            source_type = str(
                source.get("source_type") or source.get("type") or ""
            ).strip()
            source_name = str(
                source.get("source_name") or source.get("name") or ""
            ).strip()
            source_values.append(
                f"{source_type} · {source_name}" if source_name else source_type
            )
        else:
            source_values.append(str(source))
    source_text = ", ".join(x for x in source_values if x) or "Not provided"

    import html

    st.markdown('<div class="mini-panel">', unsafe_allow_html=True)

    # Existing decision block — unchanged.
    st.markdown(
        f"""
        <div class="mini-decision {css_class}">
            <div class="mini-decision-title">{icon} {html.escape(decision_label(decision))}</div>
            <div class="mini-decision-meta">
                Decision: <b>{html.escape(decision)}</b> &nbsp;·&nbsp; Analysis time: <b>{elapsed:.2f}s</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Existing DeBERTa information, kept in its existing block/format.
    if detector:
        st.markdown(
            '<div class="mini-section-title">DeBERTa screening</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="mini-metric-row"><span>Malicious probability</span>
                <b>{float(detector.get("malicious_probability", 0)):.2%}</b></div>
            <div class="mini-metric-row"><span>Threshold</span>
                <b>{float(detector.get("threshold", 0)):.2f}</b></div>
            """,
            unsafe_allow_html=True,
        )

    # Requested compact label:value presentation.
    st.markdown(
        f"""
        <div class="compact-result-row">
            <span class="compact-result-label">Attack type(s):</span>
            <span class="compact-result-value attack-value">{html.escape(attack_text)}</span>
        </div>
        <div class="compact-result-row">
            <span class="compact-result-label">Risk level:</span>
            <span class="compact-result-value risk-value {risk_class}">{html.escape(risk_label(risk))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KEEP Reason as its existing block UI.
    if reason:
        st.markdown(
            '<div class="mini-section-title">Reason</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="mini-reason">{html.escape(str(reason))}</div>',
            unsafe_allow_html=True,
        )

    # KEEP Malicious span(s) as its existing block UI.
    if spans:
        st.markdown(
            '<div class="mini-section-title">Malicious span(s)</div>',
            unsafe_allow_html=True,
        )
        for span in spans:
            if span:
                st.markdown(
                    f'<div class="mini-span">{html.escape(str(span))}</div>',
                    unsafe_allow_html=True,
                )

    # Input sources stay inside the same result panel, but use compact label:value.
    st.markdown(
        f"""
        <div class="compact-result-row input-source-row">
            <span class="compact-result-label">Input source(s):</span>
            <span class="compact-result-value source-value">{html.escape(source_text)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


def render_empty_panel():
    st.markdown(
        """
        <div class="mini-panel">
            <div class="empty-panel">
                <div class="icon">🛡️</div>
                <div class="title">Ready to scan</div>
                <div class="sub">Submit content on the left to see the DeBERTa screening,
                attack type, risk level and reasoning here.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_audit_details(result):
    """Detail view shown full-width below the form: input sources, content
    transformation, downstream response, validator. The decision/attack
    summary itself lives in render_compact_analysis() above, so it is not
    repeated here."""
    decision = result.get("decision", "UNKNOWN")

    # Content transformation
    st.subheader("What SentinelAI changed")

    original = result.get("original_content") or ""
    sanitized = result.get("sanitized_content")

    tab1, tab2 = st.tabs(["Original input", "Clean content"])

    with tab1:
        st.text_area(
            "Content received by the firewall",
            original,
            height=240,
            key=f"original_{id(result)}",
        )

    with tab2:
        if decision == "BLOCK":
            st.error(
                result.get(
                    "message",
                    "The content was blocked and was not forwarded to the downstream AI.",
                )
            )
        else:
            st.text_area(
                "Content allowed to continue",
                sanitized if sanitized is not None else original,
                height=240,
                key=f"clean_{id(result)}",
            )

    # Downstream response
    st.divider()
    st.subheader("Downstream AI response")

    ai_response = result.get("ai_response")

    if decision == "BLOCK":
        st.warning(
            "The downstream AI was not called because the firewall blocked the request."
        )
    elif ai_response:
        st.markdown(
            '<div class="reason-box">'
            + str(ai_response).replace("\n", "<br>")
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No downstream response was returned.")

    # Validator
    validator = result.get("validator")
    if validator:
        with st.expander("Validation & audit details"):
            v1, v2, v3 = st.columns(3)
            v1.metric(
                "Validation",
                str(validator.get("validation_status", "unknown")).upper(),
            )
            v2.metric(
                "Valid",
                "YES" if validator.get("is_valid") else "NO",
            )
            v3.metric(
                "Decision",
                decision,
            )

            if validator.get("reason"):
                st.caption(validator["reason"])


def render_history():
    st.subheader("Recent security events")

    if not st.session_state.history:
        st.caption("No requests processed in this session yet.")
        return

    for idx, item in enumerate(st.session_state.history):
        attacks = (
            ", ".join(item["attack_types"])
            if item["attack_types"]
            else "No attack type"
        )
        title = f"{item['time']}  ·  {item['decision']}  ·  {attacks}"

        with st.expander(title, expanded=(idx == 0)):
            st.write(f"**Source:** {item['source']}")
            st.write(f"**Risk:** {item['risk_level']}")
            st.write(f"**Processing time:** {item['elapsed']:.2f}s")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🛡️ SentinelAI")
    st.caption("Agentic Prompt Injection Firewall")

    st.divider()

    st.markdown("### Backend")
    st.session_state.api_url = st.text_input(
        "FastAPI endpoint",
        value=st.session_state.api_url,
        help="Your existing FastAPI /chat endpoint.",
    )

    st.markdown("### Session")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Requests", st.session_state.request_count)
    with c2:
        st.metric("History", len(st.session_state.history))

    if st.button("Clear session", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_result = None
        st.session_state.request_count = 0
        st.rerun()

    st.divider()

    st.markdown("### Supported sources")
    st.caption("Text · TXT · Markdown · PDF · DOCX · HTML · source code · images / OCR")

    st.divider()

    with st.expander("ℹ️ How the firewall works"):
        st.markdown(
            """
            <div class="side-step"><b>01 · Input processing</b><br>Text, documents, source code
            and images are standardized into one content representation.</div>
            <div class="side-step"><b>02 · DeBERTa screening</b><br>The fine-tuned binary
            detector performs the first security screen.</div>
            <div class="side-step"><b>03 · RAG-grounded analysis</b><br>Retrieved attack
            examples provide evidence for attack type and malicious spans.</div>
            <div class="side-step"><b>04 · Sanitization</b><br>Only the identified malicious
            spans are removed.</div>
            <div class="side-step"><b>05 · Validation</b><br>The cleaned content is checked
            before it can continue.</div>
            <div class="side-step"><b>06 · Downstream AI</b><br>Only validated content reaches
            the downstream model.</div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("Only content that passes the firewall is sent downstream.")


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-row">
            <div class="shield">🛡️</div>
            <div>
                <h1>SentinelAI</h1>
                <p>Agentic Prompt Injection Firewall · Inspect → Detect → Sanitize → Validate → Respond</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TOP STATUS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        """
        <div class="status-card">
            <div class="status-label">Protection</div>
            <div class="status-value">Active</div>
            <div class="status-sub">DeBERTa + RAG + Validator</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="status-card">
            <div class="status-label">Input modes</div>
            <div class="status-value">Multi-source</div>
            <div class="status-sub">Text + files + OCR</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="status-card">
            <div class="status-label">Policy</div>
            <div class="status-value">Safe-first</div>
            <div class="status-sub">Unsafe content never proceeds</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    last = st.session_state.last_result
    last_decision = last.get("decision", "—") if last else "—"
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-label">Last decision</div>
            <div class="status-value">{last_decision}</div>
            <div class="status-sub">Current browser session</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# INPUT WORKSPACE
# ============================================================

left, right = st.columns([1, 1], gap="medium")

with left:
    with st.container(border=True):
        st.subheader("Submit content")

        input_mode = st.radio(
            "Choose an input source",
            ["Message", "File", "Message + File"],
            horizontal=True,
            key="input_mode",
            label_visibility="collapsed",
        )

        text_value = ""
        uploaded_file = None

        if input_mode in ["Message", "Message + File"]:
            text_value = st.text_area(
                "Message",
                placeholder=(
                    "Paste a user request, email, document excerpt, webpage text, "
                    "or any content you want SentinelAI to inspect..."
                ),
                height=230,
            )

        if input_mode in ["File", "Message + File"]:
            uploaded_file = st.file_uploader(
                "Drop a file here",
                type=SUPPORTED_EXTENSIONS,
                help=(
                    "Supported: PDF, DOCX, TXT, Markdown, HTML, source code, "
                    "PNG/JPG and other supported image formats."
                ),
            )

            if uploaded_file:
                size_kb = len(uploaded_file.getvalue()) / 1024
                st.caption(
                    f"Attached: **{uploaded_file.name}** · "
                    f"{uploaded_file.type or 'file'} · {size_kb:.1f} KB"
                )

        submit = st.button(
            "🔍 Run SentinelAI Security Scan",
            type="primary",
            use_container_width=True,
        )

        if submit:
            if not text_value.strip() and uploaded_file is None:
                st.warning("Enter a message, upload a file, or provide both.")
            else:
                try:
                    with st.spinner("SentinelAI is inspecting the content..."):
                        result, elapsed = call_backend(text_value, uploaded_file)

                    save_history(
                        result,
                        elapsed,
                        source_summary(result.get("sources", [])),
                    )

                    st.rerun()

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Cannot connect to FastAPI. Start your backend first, "
                        "then run the Streamlit UI."
                    )
                except requests.exceptions.Timeout:
                    st.error("The security scan timed out. Please try again.")
                except Exception as exc:
                    st.error(f"SentinelAI request failed: {exc}")

with right:
    with st.container(border=True):
        st.subheader("Analysis results")

        if st.session_state.last_result:
            _elapsed = (
                st.session_state.history[0]["elapsed"]
                if st.session_state.history
                else 0
            )
            render_compact_analysis(st.session_state.last_result, _elapsed)
        else:
            render_empty_panel()

# ============================================================
# AUDIT DETAILS (original/sanitized content, downstream response, validator)
# ============================================================

if st.session_state.last_result:
    st.divider()
    render_audit_details(st.session_state.last_result)


# ============================================================
# HISTORY
# ============================================================

st.divider()
render_history()


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        SentinelAI · Prompt Injection Firewall · Security decisions are enforced
        before downstream AI processing.
    </div>
    """,
    unsafe_allow_html=True,
)

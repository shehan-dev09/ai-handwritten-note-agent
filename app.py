import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from trend_agent import (
    UNIVERSITY_SUBJECTS,
    discover_viral_topics,
    get_instant_ranked_topics,
)
from note_generator import (
    NOTE_TEMPLATES,
    generate_5_page_study_guide,
    build_interactive_studio_html,
)

load_dotenv()

st.set_page_config(
    page_title="NIWNOTES — University Sketchnote & Social Learning Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_secret_or_env(key_name: str) -> str:
    """Safely fetches a secret from Streamlit Cloud Secrets or falls back to .env."""
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return os.getenv(key_name, "").strip()


def format_subject_label(subject_name: str) -> str:
    """Bulletproof subject label formatter that never raises KeyError."""
    subject_meta = UNIVERSITY_SUBJECTS.get(subject_name, {})
    code = subject_meta.get("code")
    if not code:
        words = [w for w in subject_name.replace("&", " ").split() if w]
        code = "".join(w[0].upper() for w in words[:3]) or "UNI"
    return f"[{code}]  {subject_name}"


# Woday.app Inspired Daylight macOS Design System + Mobile Responsive CSS
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

    :root {
        --bg-canvas: #F7F6F2;
        --bg-card: #FFFFFF;
        --bg-subtle: #F3F2EE;
        --bg-hover: #EAE8E1;
        --text-primary: #141413;
        --text-secondary: #5E5D59;
        --text-muted: #8E8D87;
        --accent-dark: #141413;
        --accent-coral: #FF5A36;
        --accent-coral-soft: rgba(255, 90, 54, 0.1);
        --accent-green: #15803D;
        --accent-green-soft: #DCFCE7;
        --border-hairline: rgba(20, 20, 19, 0.08);
        --border-strong: rgba(20, 20, 19, 0.18);
        --shadow-card: 0 4px 20px -2px rgba(20, 20, 19, 0.04), 0 1px 3px -1px rgba(20, 20, 19, 0.03);
    }

    html, body, .stApp {
        background-color: var(--bg-canvas) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        overflow-x: hidden !important;
    }

    #MainMenu, footer, header {visibility: hidden;}

    .block-container {
        max-width: 1280px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    /* WODAY TOP NAVIGATION BAR */
    .woday-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-hairline);
        border-radius: 999px;
        padding: 10px 20px;
        margin-bottom: 24px;
        box-shadow: var(--shadow-card);
        gap: 12px;
        flex-wrap: wrap;
    }
    .woday-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .woday-logo-mark {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: var(--text-primary);
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 1.05rem;
        letter-spacing: -0.03em;
        flex-shrink: 0;
    }
    .woday-brand-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 1.12rem;
        color: var(--text-primary);
        letter-spacing: -0.03em;
    }
    .woday-brand-tag {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-muted);
        padding-left: 10px;
        border-left: 1px solid var(--border-hairline);
    }
    .woday-nav-pills {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .woday-pill {
        font-family: 'Inter', sans-serif;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 6px 13px;
        border-radius: 999px;
        background: var(--bg-subtle);
        color: var(--text-secondary);
        border: 1px solid var(--border-hairline);
        white-space: nowrap;
    }
    .woday-pill-live {
        background: var(--accent-green-soft);
        color: var(--accent-green);
        border-color: rgba(21, 128, 61, 0.2);
    }

    /* WODAY HERO SECTION */
    .woday-hero {
        text-align: center;
        max-width: 780px;
        margin: 0 auto 28px auto;
        padding: 6px 12px;
    }
    .woday-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #FFFFFF;
        border: 1px solid var(--border-hairline);
        border-radius: 999px;
        padding: 5px 14px;
        font-size: 0.76rem;
        font-weight: 700;
        color: var(--text-secondary);
        box-shadow: var(--shadow-card);
        margin-bottom: 14px;
    }
    .woday-eyebrow span {
        color: var(--accent-coral);
        font-weight: 800;
    }
    .woday-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 2.55rem !important;
        font-weight: 800 !important;
        line-height: 1.12 !important;
        letter-spacing: -0.035em !important;
        color: var(--text-primary) !important;
        margin: 0 0 10px 0 !important;
    }
    .woday-subtitle {
        font-size: 0.98rem !important;
        line-height: 1.55 !important;
        color: var(--text-secondary) !important;
        margin: 0 auto !important;
        max-width: 640px !important;
    }

    /* BENTO CONTAINER STYLING */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-hairline) !important;
        border-radius: 22px !important;
        padding: 20px !important;
        box-shadow: var(--shadow-card) !important;
    }

    /* SECTION HEADERS */
    .section-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        gap: 8px;
        flex-wrap: wrap;
    }
    .section-step-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.92rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.015em;
    }
    .section-step-num {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        background: var(--bg-subtle);
        color: var(--text-secondary);
        padding: 3px 8px;
        border-radius: 7px;
        border: 1px solid var(--border-hairline);
    }
    .section-meta-hint {
        font-size: 0.74rem;
        font-weight: 600;
        color: var(--text-muted);
    }

    /* TOPIC LEADERBOARD RANK CARDS */
    .rank-card {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding: 13px 15px;
        border-radius: 15px;
        background: var(--bg-subtle);
        border: 1.5px solid transparent;
        transition: all 0.16s ease;
        margin-bottom: 6px;
    }
    .rank-card-active {
        background: #FFFFFF;
        border-color: var(--text-primary);
        box-shadow: 0 8px 20px -4px rgba(20, 20, 19, 0.08);
    }
    .rank-left {
        display: flex;
        align-items: flex-start;
        gap: 11px;
        min-width: 0;
        flex: 1;
    }
    .rank-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.76rem;
        font-weight: 700;
        min-width: 34px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #FFFFFF;
        color: var(--text-secondary);
        border: 1px solid var(--border-hairline);
        flex-shrink: 0;
    }
    .rank-badge-active {
        background: var(--text-primary);
        color: #FFFFFF;
        border-color: var(--text-primary);
    }
    .rank-content {
        min-width: 0;
        flex: 1;
    }
    .rank-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.89rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.32;
        margin-bottom: 3px;
        word-wrap: break-word;
    }
    .rank-why {
        font-size: 0.75rem;
        color: var(--text-secondary);
        line-height: 1.38;
    }
    .rank-cat-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.66rem;
        font-weight: 700;
        padding: 4px 8px;
        border-radius: 999px;
        background: #FFFFFF;
        color: var(--text-secondary);
        border: 1px solid var(--border-hairline);
        white-space: nowrap;
        flex-shrink: 0;
    }
    .rank-cat-pill-active {
        background: var(--accent-coral-soft);
        color: var(--accent-coral);
        border-color: rgba(255, 90, 54, 0.25);
    }

    /* TEMPLATE MINIATURE PREVIEW CARDS (2x2 GRID) */
    .tpl-preview-shell {
        border-radius: 15px;
        padding: 10px;
        background: var(--bg-subtle);
        border: 2px solid transparent;
        transition: all 0.16s ease;
        margin-bottom: 6px;
    }
    .tpl-preview-shell-active {
        background: #FFFFFF;
        border-color: var(--text-primary);
        box-shadow: 0 8px 20px -4px rgba(20, 20, 19, 0.08);
    }
    .tpl-meta-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 8px;
        padding: 0 2px;
        gap: 6px;
    }
    .tpl-meta-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.8rem;
        font-weight: 800;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .tpl-meta-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 999px;
        background: #FFFFFF;
        color: var(--text-secondary);
        border: 1px solid var(--border-hairline);
        flex-shrink: 0;
    }
    .tpl-meta-badge-active {
        background: var(--text-primary);
        color: #FFFFFF;
        border-color: var(--text-primary);
    }

    /* STREAMLIT WIDGET OVERRIDES */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        background-color: var(--bg-subtle) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-hairline) !important;
        border-radius: 12px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }

    /* BUTTON OVERRIDES */
    .stButton > button {
        border-radius: 11px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        padding: 0.48rem 0.85rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--text-primary) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--text-primary) !important;
        box-shadow: 0 4px 12px rgba(20, 20, 19, 0.14) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #292826 !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="secondary"] {
        background: var(--bg-subtle) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-hairline) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: var(--bg-hover) !important;
        border-color: var(--border-strong) !important;
    }

    /* SUMMARY CONFIG BAR */
    .config-summary-strip {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        background: var(--bg-subtle);
        border: 1px solid var(--border-hairline);
        border-radius: 14px;
        padding: 10px 14px;
        margin: 10px 0 12px 0;
        font-size: 0.78rem;
        color: var(--text-secondary);
    }
    .config-summary-strip strong {
        color: var(--text-primary);
        font-weight: 700;
    }

    /* MOBILE RESPONSIVE BREAKPOINTS */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.8rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-bottom: 2rem !important;
        }
        .woday-nav {
            border-radius: 18px;
            padding: 10px 14px;
            justify-content: center;
            text-align: center;
        }
        .woday-brand-tag {
            display: none;
        }
        .woday-nav-pills {
            width: 100%;
            justify-content: center;
        }
        .woday-title {
            font-size: 1.75rem !important;
            line-height: 1.18 !important;
        }
        .woday-subtitle {
            font-size: 0.86rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 14px !important;
            border-radius: 16px !important;
        }
        .rank-card {
            flex-direction: column;
            gap: 8px;
            padding: 11px 12px;
        }
        .rank-cat-pill {
            align-self: flex-start;
        }
        .config-summary-strip {
            flex-direction: column;
            align-items: flex-start;
            gap: 6px;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


def render_template_mini_preview(tpl_key: str, is_active: bool) -> str:
    """
    Renders a single-line unindented HTML/CSS miniature notebook card.
    Avoids Markdown code-block escaping and SVG <defs> stripping in Streamlit.
    """
    themes = {
        "classic_cream": {
            "name": "Classic Cream",
            "bg": "#FDFBF7",
            "grid": "repeating-linear-gradient(to bottom, transparent 0px, transparent 15px, #E2E8F0 16px)",
            "margin": "rgba(239, 68, 68, 0.35)",
            "ink": "#0F172A",
            "muted": "#475569",
            "accent": "#EA580C",
            "hi_bg": "#FEF08A",
            "hi_ink": "#854D0E",
            "box_bg": "#FFFFFF",
            "box_border": "#1E293B",
            "pill_bg": "#FFF7ED",
        },
        "dark_neon": {
            "name": "Obsidian Dark",
            "bg": "#0F172A",
            "grid": "radial-gradient(#334155 1px, transparent 1px)",
            "grid_size": "12px 12px",
            "margin": "rgba(56, 189, 248, 0.28)",
            "ink": "#F8FAFC",
            "muted": "#94A3B8",
            "accent": "#38BDF8",
            "hi_bg": "rgba(16, 185, 129, 0.22)",
            "hi_ink": "#6EE7B7",
            "box_bg": "#1E293B",
            "box_border": "#38BDF8",
            "pill_bg": "#0F172A",
        },
        "blueprint_grid": {
            "name": "Blueprint Grid",
            "bg": "#EFF6FF",
            "grid": "linear-gradient(to right, #DBEAFE 1px, transparent 1px), linear-gradient(to bottom, #DBEAFE 1px, transparent 1px)",
            "grid_size": "14px 14px",
            "margin": "rgba(37, 99, 235, 0.28)",
            "ink": "#1E3A8A",
            "muted": "#3B82F6",
            "accent": "#2563EB",
            "hi_bg": "#DBEAFE",
            "hi_ink": "#1E40AF",
            "box_bg": "#FFFFFF",
            "box_border": "#1E3A8A",
            "pill_bg": "#EFF6FF",
        },
        "cornell_academic": {
            "name": "Cornell Exam",
            "bg": "#FAF8F5",
            "grid": "repeating-linear-gradient(to bottom, transparent 0px, transparent 15px, #E7E5E4 16px)",
            "margin": "rgba(124, 58, 237, 0.35)",
            "ink": "#1C1917",
            "muted": "#57534E",
            "accent": "#7C3AED",
            "hi_bg": "#F3E8FF",
            "hi_ink": "#6D28D9",
            "box_bg": "#FFFFFF",
            "box_border": "#4C1D95",
            "pill_bg": "#FAF5FF",
        },
    }
    t = themes.get(tpl_key, themes["classic_cream"])
    shell_cls = "tpl-preview-shell tpl-preview-shell-active" if is_active else "tpl-preview-shell"
    badge_cls = "tpl-meta-badge tpl-meta-badge-active" if is_active else "tpl-meta-badge"
    badge_txt = "ACTIVE" if is_active else "SELECT"
    bg_size = f"background-size:{t['grid_size']};" if "grid_size" in t else ""

    return (
        f'<div class="{shell_cls}">'
        f'<div style="background-color:{t["bg"]};background-image:{t["grid"]};{bg_size}border-radius:10px;padding:10px 12px 10px 22px;position:relative;border:1px solid rgba(20,20,19,0.12);height:132px;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;font-family:\'Plus Jakarta Sans\',sans-serif;">'
        f'<div style="position:absolute;left:14px;top:0;bottom:0;width:1.5px;background:{t["margin"]};"></div>'
        f'<div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
        f'<span style="font-size:9px;font-weight:800;color:{t["accent"]};letter-spacing:0.04em;">NIWNOTES STUDIO</span>'
        f'<span style="font-size:8px;font-weight:700;color:{t["muted"]};font-family:\'JetBrains Mono\',monospace;">01/05</span>'
        f'</div>'
        f'<div style="font-size:12px;font-weight:800;color:{t["ink"]};line-height:1.15;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">Core Architecture Note</div>'
        f'<div style="display:inline-block;background:{t["hi_bg"]};color:{t["hi_ink"]};font-size:8.5px;font-weight:700;padding:2px 6px;border-radius:4px;">Key Concept Summary</div>'
        f'</div>'
        f'<div style="background:{t["box_bg"]};border:1.5px solid {t["box_border"]};border-radius:7px;padding:5px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;">'
        f'<div style="background:{t["pill_bg"]};border:1px solid {t["accent"]};border-radius:4px;padding:2px 3px;font-size:8px;font-weight:700;color:{t["ink"]};text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">01 Input</div>'
        f'<div style="background:{t["pill_bg"]};border:1px solid {t["accent"]};border-radius:4px;padding:2px 3px;font-size:8px;font-weight:700;color:{t["ink"]};text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">02 Process</div>'
        f'<div style="background:{t["pill_bg"]};border:1px solid {t["accent"]};border-radius:4px;padding:2px 3px;font-size:8px;font-weight:700;color:{t["ink"]};text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">03 Output</div>'
        f'</div>'
        f'</div>'
        f'<div class="tpl-meta-bar">'
        f'<span class="tpl-meta-name">{t["name"]}</span>'
        f'<span class="{badge_cls}">{badge_txt}</span>'
        f'</div>'
        f'</div>'
    )


# ------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ------------------------------------------------------------------
default_subject = "AI & Machine Learning"
if "selected_subject" not in st.session_state:
    st.session_state["selected_subject"] = default_subject

if "viral_topics" not in st.session_state:
    st.session_state["viral_topics"] = get_instant_ranked_topics(default_subject)

if "selected_topic_idx" not in st.session_state:
    st.session_state["selected_topic_idx"] = 0

if "selected_topic" not in st.session_state:
    initial_topics = st.session_state["viral_topics"]
    st.session_state["selected_topic"] = (
        initial_topics[0].title if initial_topics else "Agentic AI Workflows"
    )

if "selected_template" not in st.session_state:
    st.session_state["selected_template"] = "classic_cream"

if "selected_language" not in st.session_state:
    st.session_state["selected_language"] = "Sinhala_Mix"

if "selected_pages" not in st.session_state:
    st.session_state["selected_pages"] = 5

env_gemini_key = get_secret_or_env("GEMINI_API_KEY")

# ------------------------------------------------------------------
# TOP NAVIGATION BAR & HERO HEADER
# ------------------------------------------------------------------
api_badge_html = (
    '<span class="woday-pill woday-pill-live">Engine Ready</span>'
    if env_gemini_key
    else '<span class="woday-pill">API Key Needed</span>'
)

st.markdown(
    f"""
<div class="woday-nav">
    <div class="woday-brand">
        <div class="woday-logo-mark">N</div>
        <span class="woday-brand-name">NIWNOTES</span>
        <span class="woday-brand-tag">University Social Learning Studio</span>
    </div>
    <div class="woday-nav-pills">
        <span class="woday-pill">8 University Tracks</span>
        <span class="woday-pill">5 / 10 / 30 Pages</span>
        <span class="woday-pill">Instant GPU Export</span>
        {api_badge_html}
    </div>
</div>

<div class="woday-hero">
    <div class="woday-eyebrow"><span>NIWNOTES 3.0</span> Built for University Students & Tech Creators</div>
    <h1 class="woday-title">Turn complex lectures into shareable handwritten study decks.</h1>
    <p class="woday-subtitle">
        Pick your university subject, select a top-ranked topic or enter your own lecture title, and generate a crisp handwritten carousel with ready-to-post LinkedIn and Facebook captions.
    </p>
</div>
""",
    unsafe_allow_html=True,
)

if not env_gemini_key:
    with st.expander("Configure Free Gemini API Key", expanded=True):
        user_key = st.text_input(
            "Enter your Google AI Studio API Key (AIzaSy...)",
            type="password",
            placeholder="AIzaSy...",
        )
        if user_key:
            env_gemini_key = user_key.strip()

# ------------------------------------------------------------------
# MAIN TWO-COLUMN BENTO WORKSPACE
# ------------------------------------------------------------------
left_col, right_col = st.columns([1.08, 0.92], gap="large")

with left_col:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-header-row">
                <div class="section-step-badge">
                    <span class="section-step-num">STEP 01</span>
                    <span>Subject & Topic Ranking Leaderboard</span>
                </div>
                <span class="section-meta-hint">Ranked #01 to #05</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        subj_col, refresh_col = st.columns([3.3, 1.2], gap="small")
        subject_list = list(UNIVERSITY_SUBJECTS.keys())

        with subj_col:
            current_subj_index = (
                subject_list.index(st.session_state["selected_subject"])
                if st.session_state["selected_subject"] in subject_list
                else 0
            )
            chosen_subject = st.selectbox(
                "University Subject Track",
                options=subject_list,
                index=current_subj_index,
                format_func=format_subject_label,
                label_visibility="collapsed",
            )

            if chosen_subject != st.session_state["selected_subject"]:
                st.session_state["selected_subject"] = chosen_subject
                instant_list = get_instant_ranked_topics(chosen_subject)
                st.session_state["viral_topics"] = instant_list
                st.session_state["selected_topic_idx"] = 0
                if instant_list:
                    st.session_state["selected_topic"] = instant_list[0].title
                st.rerun()

        with refresh_col:
            if st.button(
                "Live Scan",
                use_container_width=True,
                help="Fetch live trending signals for this subject using AI",
            ):
                with st.spinner("Ranking live signals..."):
                    live_topics = discover_viral_topics(
                        api_key=env_gemini_key,
                        subject_category=st.session_state["selected_subject"],
                    )
                    st.session_state["viral_topics"] = live_topics
                    st.session_state["selected_topic_idx"] = 0
                    if live_topics:
                        st.session_state["selected_topic"] = live_topics[0].title
                    st.rerun()

        topics = st.session_state.get("viral_topics", [])
        active_idx = st.session_state.get("selected_topic_idx", 0)

        for idx, t in enumerate(topics[:5]):
            is_selected = idx == active_idx
            card_cls = "rank-card rank-card-active" if is_selected else "rank-card"
            badge_cls = "rank-badge rank-badge-active" if is_selected else "rank-badge"
            cat_cls = (
                "rank-cat-pill rank-cat-pill-active" if is_selected else "rank-cat-pill"
            )

            st.markdown(
                f"""
                <div class="{card_cls}">
                    <div class="rank-left">
                        <div class="{badge_cls}">#0{idx + 1}</div>
                        <div class="rank-content">
                            <div class="rank-title">{t.title}</div>
                            <div class="rank-why">{t.why_viral}</div>
                        </div>
                    </div>
                    <span class="{cat_cls}">{t.category}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_label = (
                f"Selected Rank #0{idx + 1}"
                if is_selected
                else f"Choose Rank #0{idx + 1}"
            )
            if st.button(
                btn_label,
                key=f"pick_rank_{idx}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_topic_idx"] = idx
                st.session_state["selected_topic"] = t.title
                st.rerun()

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        custom_topic = st.text_input(
            "Or type any custom University Lecture / Exam Topic:",
            value=st.session_state.get("selected_topic", ""),
            placeholder="e.g., Operating System Deadlocks, Dijkstra's Algorithm, TCP Congestion Control...",
        )
        if custom_topic != st.session_state.get("selected_topic", ""):
            st.session_state["selected_topic"] = custom_topic


with right_col:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-header-row">
                <div class="section-step-badge">
                    <span class="section-step-num">STEP 02</span>
                    <span>Handwritten Notebook Template</span>
                </div>
                <span class="section-meta-hint">Visual Sample Preview</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        template_keys = list(NOTE_TEMPLATES.keys())
        grid_row_1 = st.columns(2, gap="small")
        grid_row_2 = st.columns(2, gap="small")
        grid_cols = [grid_row_1[0], grid_row_1[1], grid_row_2[0], grid_row_2[1]]

        for idx, tpl_key in enumerate(template_keys[:4]):
            is_tpl_active = st.session_state.get("selected_template") == tpl_key
            tpl_info = NOTE_TEMPLATES.get(tpl_key, {})
            tpl_short_name = tpl_info.get("short_name", tpl_key.replace("_", " ").title())
            with grid_cols[idx]:
                st.markdown(
                    render_template_mini_preview(tpl_key, is_tpl_active),
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Use {tpl_short_name}",
                    key=f"tpl_btn_{tpl_key}",
                    type="primary" if is_tpl_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["selected_template"] = tpl_key
                    st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            """
            <div class="section-header-row">
                <div class="section-step-badge">
                    <span class="section-step-num">STEP 03</span>
                    <span>Note & Social Caption Language</span>
                </div>
                <span class="section-meta-hint">Syncs Slides + Caption</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        lang_col1, lang_col2 = st.columns(2, gap="small")
        curr_lang = st.session_state.get("selected_language", "Sinhala_Mix")

        with lang_col1:
            if st.button(
                "Sinhala + English (Kuppi Mode)",
                type="primary" if curr_lang == "Sinhala_Mix" else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_language"] = "Sinhala_Mix"
                st.rerun()

        with lang_col2:
            if st.button(
                "100% Pure Academic English",
                type="primary" if curr_lang == "English" else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_language"] = "English"
                st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="section-header-row">
                <div class="section-step-badge">
                    <span class="section-step-num">STEP 04</span>
                    <span>Study Deck Length</span>
                </div>
                <span class="section-meta-hint">Parallel AI Synthesis</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        p_col1, p_col2, p_col3 = st.columns(3, gap="small")
        curr_pages = st.session_state.get("selected_pages", 5)

        with p_col1:
            if st.button(
                "5 Pages (Quick)",
                type="primary" if curr_pages == 5 else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_pages"] = 5
                st.rerun()

        with p_col2:
            if st.button(
                "10 Pages (Deep)",
                type="primary" if curr_pages == 10 else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_pages"] = 10
                st.rerun()

        with p_col3:
            if st.button(
                "30 Pages (Master)",
                type="primary" if curr_pages == 30 else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_pages"] = 30
                st.rerun()

        active_tpl_name = NOTE_TEMPLATES.get(
            st.session_state["selected_template"], {}
        ).get("short_name", "Classic Cream")
        active_lang_label = (
            "Sinhala Kuppi Mix" if curr_lang == "Sinhala_Mix" else "Pure English"
        )

        st.markdown(
            f"""
            <div class="config-summary-strip">
                <span>Template: <strong>{active_tpl_name}</strong></span>
                <span>Language: <strong>{active_lang_label}</strong></span>
                <span>Deck Size: <strong>{curr_pages} Slides</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        generate_clicked = st.button(
            f"Generate {curr_pages}-Page NIWNOTES Study Deck",
            type="primary",
            use_container_width=True,
        )

# ------------------------------------------------------------------
# GENERATION PIPELINE
# ------------------------------------------------------------------
if generate_clicked:
    topic_to_run = st.session_state.get("selected_topic", "").strip()
    if not env_gemini_key:
        st.error("Please configure your free Gemini API key above to generate notes.")
    elif not topic_to_run:
        st.warning("Please select a ranked topic or type a custom lecture topic first.")
    else:
        pages_target = st.session_state.get("selected_pages", 5)
        lang_target = st.session_state.get("selected_language", "Sinhala_Mix")
        subj_target = st.session_state.get("selected_subject", default_subject)

        with st.spinner(
            f"Synthesizing {pages_target}-page handwritten study guide for '{topic_to_run}'..."
        ):
            try:
                study_guide = generate_5_page_study_guide(
                    topic=topic_to_run,
                    language=lang_target,
                    api_key=env_gemini_key,
                    subject_category=subj_target,
                    num_pages=pages_target,
                )
                st.session_state["generated_guide"] = study_guide
                st.session_state["generated_topic"] = topic_to_run
                st.session_state["generated_subject"] = subj_target
            except Exception as err:
                st.error(f"Generation failed: {err}")

# ------------------------------------------------------------------
# INTERACTIVE LIVE HTML/CSS STUDIO
# ------------------------------------------------------------------
if "generated_guide" in st.session_state:
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    studio_html = build_interactive_studio_html(
        study_data=st.session_state["generated_guide"],
        topic=st.session_state.get(
            "generated_topic", st.session_state.get("selected_topic", "Study_Notes")
        ),
        template_key=st.session_state.get("selected_template", "classic_cream"),
        subject_category=st.session_state.get(
            "generated_subject", st.session_state.get("selected_subject", default_subject)
        ),
        language=st.session_state.get("selected_language", "Sinhala_Mix"),
    )
    components.html(studio_html, height=1320, scrolling=True)
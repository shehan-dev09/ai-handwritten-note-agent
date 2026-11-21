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
    normalize_template_key,
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


# Woday.app Inspired Daylight macOS Design System + Mobile/Tablet Responsive CSS
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Caveat:wght@600;700&family=Kalam:wght@400;700&display=swap');

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
        max-width: 1320px !important;
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        overflow-x: hidden !important;
    }

    /* WODAY TOP NAVIGATION BAR */
    .woday-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-hairline);
        border-radius: 999px;
        padding: 10px 20px;
        margin-bottom: 22px;
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
        max-width: 800px;
        margin: 0 auto 26px auto;
        padding: 4px 12px;
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
        margin-bottom: 12px;
    }
    .woday-eyebrow span {
        color: var(--accent-coral);
        font-weight: 800;
    }
    .woday-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: clamp(1.8rem, 4vw, 2.55rem) !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
        letter-spacing: -0.035em !important;
        color: var(--text-primary) !important;
        margin: 0 0 10px 0 !important;
    }
    .woday-subtitle {
        font-size: 0.95rem !important;
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
    .tpl-tag-pill {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.02em;
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
        min-height: 40px !important;
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

    /* IFRAME FULL CONTAINER WIDTH */
    iframe[title="streamlit.components.v1.html"] {
        width: 100% !important;
        border: none !important;
        border-radius: 20px !important;
    }

    /* TABLET RESPONSIVE BREAKPOINT (769px to 1024px) */
    @media (min-width: 769px) and (max-width: 1024px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
        }
        .woday-title {
            font-size: 2.1rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 16px !important;
        }
        .rank-card {
            padding: 10px 12px;
        }
    }

    /* MOBILE RESPONSIVE BREAKPOINTS (< 768px) */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.6rem !important;
            padding-left: 0.55rem !important;
            padding-right: 0.55rem !important;
            padding-bottom: 2rem !important;
        }
        .woday-nav {
            border-radius: 18px;
            padding: 9px 12px;
            justify-content: center;
            text-align: center;
            gap: 8px;
        }
        .woday-brand-tag {
            display: none;
        }
        .woday-nav-pills {
            width: 100%;
            justify-content: center;
            gap: 6px;
        }
        .woday-title {
            font-size: 1.7rem !important;
            line-height: 1.18 !important;
        }
        .woday-subtitle {
            font-size: 0.85rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 13px !important;
            border-radius: 16px !important;
        }
        .rank-card {
            flex-direction: column;
            gap: 6px;
            padding: 10px 11px;
        }
        .rank-cat-pill {
            align-self: flex-start;
        }
        .config-summary-strip {
            flex-direction: column;
            align-items: flex-start;
            gap: 5px;
        }
        .stButton > button {
            min-height: 42px !important;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


def render_template_mini_preview(tpl_key: str, is_active: bool) -> str:
    """
    Renders a clean, compact HTML/CSS miniature notebook card.
    Accurately represents 2 Realistic physical paper styles (Ruled paper, Kraft journal)
    with handwritten lines, and 2 Digital stylus styles (iPad GoodNotes, Notability Cyber Dark).
    """
    norm_key = normalize_template_key(tpl_key)

    themes = {
        "classic_ruled": {
            "name": "Ruled Notebook",
            "type_tag": "REALISTIC",
            "type_bg": "rgba(220, 38, 38, 0.12)",
            "type_color": "#DC2626",
            "bg": "#FCFBF7",
            "grid": "repeating-linear-gradient(to bottom, transparent 0px, transparent 15px, rgba(160, 185, 215, 0.45) 16px)",
            "margin": "rgba(239, 68, 68, 0.55)",
            "ink": "#152E5A",
            "accent": "#DC2626",
            "hi_bg": "#FEF08A",
            "hi_ink": "#713F12",
            "box_bg": "#FEF08A",
            "box_border": "#EAB308",
            "hole": True,
        },
        "vintage_kraft": {
            "name": "Quad Grid Pad",
            "type_tag": "REALISTIC",
            "type_bg": "rgba(180, 83, 9, 0.12)",
            "type_color": "#B45309",
            "bg": "#F7F1E5",
            "grid": "linear-gradient(to right, rgba(139, 94, 60, 0.14) 1px, transparent 1px), linear-gradient(to bottom, rgba(139, 94, 60, 0.14) 1px, transparent 1px)",
            "grid_size": "14px 14px",
            "margin": "rgba(180, 83, 9, 0.4)",
            "ink": "#1F1610",
            "accent": "#C2410C",
            "hi_bg": "#FDE68A",
            "hi_ink": "#451A03",
            "box_bg": "#FFFBEB",
            "box_border": "#B45309",
            "hole": False,
        },
        "digital_ipad": {
            "name": "iPad GoodNotes",
            "type_tag": "DIGITAL",
            "type_bg": "rgba(37, 99, 235, 0.12)",
            "type_color": "#2563EB",
            "bg": "#F8FAFC",
            "grid": "radial-gradient(#CBD5E1 1px, transparent 1px)",
            "grid_size": "12px 12px",
            "margin": "rgba(99, 102, 241, 0.3)",
            "ink": "#0F172A",
            "accent": "#2563EB",
            "hi_bg": "#C7D2FE",
            "hi_ink": "#312E81",
            "box_bg": "#FFFFFF",
            "box_border": "#CBD5E1",
            "pill_bg": "#F1F5F9",
            "hole": False,
        },
        "digital_dark": {
            "name": "Cyber Dark",
            "type_tag": "DIGITAL",
            "type_color": "#38BDF8",
            "type_bg": "rgba(56, 189, 248, 0.15)",
            "bg": "#0B0F19",
            "grid": "radial-gradient(rgba(56, 189, 248, 0.22) 1px, transparent 1px)",
            "grid_size": "12px 12px",
            "margin": "rgba(56, 189, 248, 0.28)",
            "ink": "#F8FAFC",
            "accent": "#38BDF8",
            "hi_bg": "rgba(56, 189, 248, 0.25)",
            "hi_ink": "#E0F2FE",
            "box_bg": "#111827",
            "box_border": "rgba(56, 189, 248, 0.4)",
            "pill_bg": "#1E293B",
            "hole": False,
        },
    }

    t = themes.get(norm_key, themes["classic_ruled"])
    shell_cls = "tpl-preview-shell tpl-preview-shell-active" if is_active else "tpl-preview-shell"
    badge_cls = "tpl-meta-badge tpl-meta-badge-active" if is_active else "tpl-meta-badge"
    badge_txt = "ACTIVE" if is_active else "SELECT"
    bg_size = f"background-size:{t['grid_size']};" if "grid_size" in t else ""

    hole_html = (
        '<div style="position:absolute;left:4px;top:20px;width:7px;height:7px;border-radius:50%;background:#D1D5DB;box-shadow:inset 1px 1px 2px rgba(0,0,0,0.4);"></div>'
        '<div style="position:absolute;left:4px;top:60px;width:7px;height:7px;border-radius:50%;background:#D1D5DB;box-shadow:inset 1px 1px 2px rgba(0,0,0,0.4);"></div>'
        '<div style="position:absolute;left:4px;top:100px;width:7px;height:7px;border-radius:50%;background:#D1D5DB;box-shadow:inset 1px 1px 2px rgba(0,0,0,0.4);"></div>'
        if t.get("hole")
        else ""
    )

    if t.get("type_tag") == "REALISTIC":
        # Pure physical handwritten paper preview: text on lines with highlighter and sticky note
        content_doodle = (
            f'<div style="margin: 4px 0 0 0; display: flex; flex-direction: column; gap: 4px;">'
            f'<div style="display: flex; align-items: baseline; gap: 5px;">'
            f'<span style="font-size: 8.5px; font-weight: 800; color: {t["accent"]};">01.</span>'
            f'<span style="font-size: 8px; color: {t["ink"]}; font-weight: 600;">Main note written on paper lines</span>'
            f'</div>'
            f'<div style="display: flex; align-items: baseline; gap: 5px;">'
            f'<span style="font-size: 8.5px; font-weight: 800; color: {t["accent"]};">02.</span>'
            f'<span style="background: {t["hi_bg"]}; color: {t["hi_ink"]}; font-size: 7.5px; font-weight: 700; padding: 1px 4px; border-radius: 2px;">Highlighted Key Formula</span>'
            f'</div>'
            f'<div style="background: {t["box_bg"]}; border: 1px dashed {t["accent"]}; border-radius: 4px; padding: 2px 4px; font-size: 7.5px; font-weight: 700; color: {t["ink"]};">'
            f'📌 Post-It / Taped Pro-Tip Note'
            f'</div>'
            f'</div>'
        )
    else:
        # Digital tablet preview: tablet flow cards
        content_doodle = (
            f'<div style="background:{t["box_bg"]};border:1.2px solid {t["box_border"]};border-radius:6px;padding:4px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:3px;margin-top:4px;">'
            f'<div style="background:{t["pill_bg"]};border:1px solid {t["accent"]};border-radius:3px;padding:2px 2px;font-size:7.5px;font-weight:700;color:{t["ink"]};text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">01 Input</div>'
            f'<div style="background:{t["pill_bg"]};border:1px solid {t["accent"]};border-radius:3px;padding:2px 2px;font-size:7.5px;font-weight:700;color:{t["ink"]};text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">02 Process</div>'
            f'<div style="background:{t["pill_bg"]};border:1px solid {t["accent"]};border-radius:3px;padding:2px 2px;font-size:7.5px;font-weight:700;color:{t["ink"]};text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">03 Output</div>'
            f'</div>'
        )

    return (
        f'<div class="{shell_cls}">'
        f'<div style="background-color:{t["bg"]};background-image:{t["grid"]};{bg_size}border-radius:10px;padding:9px 10px 9px 20px;position:relative;border:1px solid rgba(20,20,19,0.12);height:130px;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;font-family:\'Plus Jakarta Sans\',sans-serif;">'
        f'{hole_html}'
        f'<div style="position:absolute;left:15px;top:0;bottom:0;width:1.5px;background:{t["margin"]};"></div>'
        f'<div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">'
        f'<span style="font-size:8.5px;font-weight:800;color:{t["accent"]};letter-spacing:0.03em;">NIWNOTES</span>'
        f'<span class="tpl-tag-pill" style="background:{t["type_bg"]};color:{t["type_color"]};">{t["type_tag"]}</span>'
        f'</div>'
        f'<div style="font-size:11.5px;font-weight:800;color:{t["ink"]};line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">Actual Lecture Note</div>'
        f'</div>'
        f'{content_doodle}'
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
    st.session_state["selected_template"] = "classic_ruled"
else:
    # Normalize any legacy key
    st.session_state["selected_template"] = normalize_template_key(
        st.session_state["selected_template"]
    )

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
        <span class="woday-brand-tag">University Handwritten Study Studio</span>
    </div>
    <div class="woday-nav-pills">
        <span class="woday-pill">8 University Tracks</span>
        <span class="woday-pill">2 Paper + 2 Digital Styles</span>
        <span class="woday-pill">Instant GPU Export</span>
        {api_badge_html}
    </div>
</div>

<div class="woday-hero">
    <div class="woday-eyebrow"><span>NIWNOTES 3.5</span> Authentic Human Handwriting Studio</div>
    <h1 class="woday-title">Turn complex lectures into authentic handwritten study decks.</h1>
    <p class="woday-subtitle">
        Pick your university subject, select a top-ranked topic or type a custom lecture, and synthesize a genuine pen-and-paper handwritten carousel with ready-to-post LinkedIn & Facebook captions.
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
                    <span>Handwritten Templates (2 Realistic + 2 Digital)</span>
                </div>
                <span class="section-meta-hint">Human Touch Styles</span>
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
                    <span>Handwritten Note Language</span>
                </div>
                <span class="section-meta-hint">Authentic Script</span>
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
                <span class="section-meta-hint">Multi-Page Carousel</span>
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

        active_tpl_meta = NOTE_TEMPLATES.get(
            st.session_state["selected_template"], NOTE_TEMPLATES["classic_ruled"]
        )
        active_tpl_name = active_tpl_meta.get("name", "Classic Ruled Paper")
        active_tpl_cat = active_tpl_meta.get("category", "Realistic")
        active_lang_label = (
            "Sinhala Kuppi Mix" if curr_lang == "Sinhala_Mix" else "Pure English"
        )

        st.markdown(
            f"""
            <div class="config-summary-strip">
                <span>Template: <strong>{active_tpl_name} ({active_tpl_cat})</strong></span>
                <span>Language: <strong>{active_lang_label}</strong></span>
                <span>Deck: <strong>{curr_pages} Slides</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        generate_clicked = st.button(
            f"Synthesize {curr_pages}-Page Handwritten Study Deck",
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
        template_key=st.session_state.get("selected_template", "classic_ruled"),
        subject_category=st.session_state.get(
            "generated_subject", st.session_state.get("selected_subject", default_subject)
        ),
        language=st.session_state.get("selected_language", "Sinhala_Mix"),
    )
    components.html(studio_html, height=1420, scrolling=True)

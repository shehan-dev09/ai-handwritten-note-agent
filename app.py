import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from trend_agent import (
    UNIVERSITY_SUBJECTS,
    get_default_ranked_topics,
    get_working_models,
    discover_viral_topics,
)
from note_generator import (
    NOTE_TEMPLATES,
    generate_5_page_study_guide,
    build_interactive_studio_html,
)

load_dotenv()

# =====================================================================
# 1. Page Configuration
# =====================================================================
st.set_page_config(
    page_title="NIWNOTES - University Study Notes & Carousel Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# 2. Woday-Inspired macOS Light Mode CSS Design System
# =====================================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@500;600;700&family=Caveat:wght@700&display=swap');

    :root {
        --bg-canvas: #F7F6F2;
        --bg-card: #FFFFFF;
        --bg-subtle: #F3F2EE;
        --text-main: #141413;
        --text-muted: #575653;
        --text-soft: #8A8884;
        --border-hairline: rgba(20, 20, 19, 0.08);
        --accent-coral: #FF5A36;
    }

    .stApp {
        background-color: var(--bg-canvas) !important;
        color: var(--text-main) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}

    .block-container {
        max-width: 1280px !important;
        padding-top: 1.4rem !important;
        padding-bottom: 4rem !important;
    }

    /* Top Navigation Bar */
    .woday-nav {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(16px);
        border: 1px solid var(--border-hairline);
        border-radius: 999px;
        padding: 10px 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -4px rgba(20, 20, 19, 0.04);
    }
    .woday-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 1.15rem;
        color: var(--text-main);
        letter-spacing: -0.03em;
    }
    .woday-logo-box {
        width: 32px;
        height: 32px;
        border-radius: 9px;
        background: var(--text-main);
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 800;
    }
    .woday-nav-pills {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .woday-pill {
        background: var(--bg-subtle);
        color: var(--text-muted);
        font-size: 0.78rem;
        font-weight: 600;
        padding: 6px 13px;
        border-radius: 999px;
        border: 1px solid var(--border-hairline);
    }
    .woday-pill-active {
        background: #DCFCE7;
        color: #15803D;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 6px 13px;
        border-radius: 999px;
    }

    /* Hero Header */
    .woday-hero {
        text-align: center;
        max-width: 780px;
        margin: 0 auto 24px auto;
    }
    .woday-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #FFFFFF;
        border: 1px solid var(--border-hairline);
        border-radius: 999px;
        padding: 5px 14px;
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-muted);
        margin-bottom: 12px;
    }
    .woday-eyebrow-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent-coral);
    }
    .woday-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.55rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.1;
        color: var(--text-main);
        margin-bottom: 8px;
    }
    .woday-subtitle {
        font-size: 0.98rem;
        color: var(--text-muted);
        line-height: 1.55;
    }

    /* Bento Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-hairline) !important;
        border-radius: 22px !important;
        padding: 18px !important;
        box-shadow: 0 12px 32px -8px rgba(20, 20, 19, 0.05) !important;
    }

    .mac-card-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 12px;
        margin-bottom: 14px;
        border-bottom: 1px solid var(--border-hairline);
    }
    .mac-dots {
        display: flex;
        gap: 6px;
    }
    .mac-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .mac-dot-r { background: #FF5F56; }
    .mac-dot-y { background: #FFBD2E; }
    .mac-dot-g { background: #27C93F; }
    .mac-card-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.73rem;
        font-weight: 600;
        color: var(--text-soft);
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .section-step-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .step-num-badge {
        background: var(--text-main);
        color: #FFFFFF;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
    }

    /* Topic Ranking Card */
    .rank-card {
        background: #FAF9F5;
        border: 1.5px solid rgba(20, 20, 19, 0.08);
        border-radius: 14px;
        padding: 11px 14px;
        margin-bottom: 6px;
    }
    .rank-card-active {
        background: #FFFFFF;
        border: 2px solid #141413;
        box-shadow: 0 6px 18px -4px rgba(20, 20, 19, 0.10);
    }
    .rank-top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .rank-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
        background: #141413;
        color: #FFFFFF;
    }
    .rank-number-top {
        background: #FF5A36;
        color: #FFFFFF;
    }
    .rank-cat-badge {
        font-size: 0.7rem;
        font-weight: 600;
        color: #575653;
        background: #EAE8E1;
        padding: 2px 9px;
        border-radius: 999px;
    }
    .rank-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
        color: #141413;
        line-height: 1.3;
        margin-bottom: 3px;
    }
    .rank-summary {
        font-size: 0.77rem;
        color: #575653;
        line-height: 1.38;
    }

    /* Template Visual Preview Card (Vector SVG - Zero Overlap) */
    .tpl-preview-card {
        border-radius: 16px;
        padding: 10px 10px 12px 10px;
        border: 1.5px solid rgba(20, 20, 19, 0.09);
        background: #FFFFFF;
        margin-bottom: 8px;
        transition: all 0.16s ease;
    }
    .tpl-preview-card-active {
        border: 2.5px solid #141413;
        background: #FFFFFF;
        box-shadow: 0 8px 22px -4px rgba(20, 20, 19, 0.12);
    }
    .tpl-svg-wrap {
        width: 100%;
        border-radius: 11px;
        overflow: hidden;
        margin-bottom: 9px;
        border: 1px solid rgba(20, 20, 19, 0.08);
        display: block;
    }
    .tpl-svg-wrap svg {
        width: 100%;
        height: auto;
        display: block;
    }
    .tpl-footer-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2px;
    }
    .tpl-meta-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.88rem;
        font-weight: 800;
        color: #141413;
    }
    .tpl-meta-badge {
        font-size: 0.75rem;
        color: #787774;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background-color: #141413 !important;
        color: #FFFFFF !important;
        border: 1px solid #141413 !important;
        border-radius: 12px !important;
        padding: 0.52rem 0.9rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
        box-shadow: 0 4px 12px rgba(20, 20, 19, 0.12) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #141413 !important;
        border: 1px solid rgba(20, 20, 19, 0.12) !important;
        border-radius: 12px !important;
        padding: 0.52rem 0.9rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #F3F2EE !important;
        border-color: #141413 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def render_template_mini_preview(tpl_key: str, is_active: bool) -> str:
    """
    Renders a pixel-perfect, scalable Vector SVG miniature preview for each notebook template.
    Uses a fixed SVG coordinate system (viewBox='0 0 280 132') with zero emojis and zero text wrapping.
    """
    visual_map = {
        "classic_cream": {
            "short_name": "Classic Cream",
            "sub_label": "Warm Dot-Grid",
            "bg": "#FAF6EE",
            "pattern": """
                <pattern id="pat_classic" width="18" height="18" patternUnits="userSpaceOnUse">
                    <circle cx="9" cy="9" r="1.1" fill="#D6D1C7"/>
                </pattern>
            """,
            "pat_id": "url(#pat_classic)",
            "margin_color": "#F87171",
            "title_color": "#1E293B",
            "hl_bg": "#FDE047",
            "hl_text": "#1E293B",
            "core_bg": "#FFFFFF",
            "core_border": "#DC2626",
            "core_text": "#B91C1C",
            "p1_bg": "#FFFFFF",
            "p1_border": "#1E293B",
            "p1_text": "#1E293B",
            "p2_bg": "#FFFFFF",
            "p2_border": "#2563EB",
            "p2_text": "#1D4ED8",
            "p3_bg": "#FEF9C3",
            "p3_border": "#D97706",
            "p3_text": "#B45309",
        },
        "dark_neon": {
            "short_name": "Obsidian Dark",
            "sub_label": "Dark Dot-Grid",
            "bg": "#0F172A",
            "pattern": """
                <pattern id="pat_dark" width="18" height="18" patternUnits="userSpaceOnUse">
                    <circle cx="9" cy="9" r="1.1" fill="#334155"/>
                </pattern>
            """,
            "pat_id": "url(#pat_dark)",
            "margin_color": "#10B981",
            "title_color": "#F8FAFC",
            "hl_bg": "#064E3B",
            "hl_text": "#ECFDF5",
            "core_bg": "#0F172A",
            "core_border": "#22C55E",
            "core_text": "#4ADE80",
            "p1_bg": "#1E293B",
            "p1_border": "#475569",
            "p1_text": "#E2E8F0",
            "p2_bg": "#0F172A",
            "p2_border": "#38BDF8",
            "p2_text": "#38BDF8",
            "p3_bg": "#052E16",
            "p3_border": "#22C55E",
            "p3_text": "#4ADE80",
        },
        "blueprint_grid": {
            "short_name": "Blueprint Grid",
            "sub_label": "Engineering Graph",
            "bg": "#F2F8FF",
            "pattern": """
                <pattern id="pat_grid" width="18" height="18" patternUnits="userSpaceOnUse">
                    <path d="M 18 0 L 0 0 0 18" fill="none" stroke="#DCEBFA" stroke-width="1"/>
                </pattern>
            """,
            "pat_id": "url(#pat_grid)",
            "margin_color": "#60A5FA",
            "title_color": "#0369A1",
            "hl_bg": "#BAE6FD",
            "hl_text": "#0C4A6E",
            "core_bg": "#FFFFFF",
            "core_border": "#EA580C",
            "core_text": "#C2410C",
            "p1_bg": "#FFFFFF",
            "p1_border": "#0284C7",
            "p1_text": "#0369A1",
            "p2_bg": "#FFFFFF",
            "p2_border": "#2563EB",
            "p2_text": "#1D4ED8",
            "p3_bg": "#FFF7ED",
            "p3_border": "#EA580C",
            "p3_text": "#C2410C",
        },
        "cornell_academic": {
            "short_name": "Cornell Exam",
            "sub_label": "Ruled Ivory Sheet",
            "bg": "#FCFBF9",
            "pattern": """
                <pattern id="pat_ruled" width="280" height="22" patternUnits="userSpaceOnUse">
                    <line x1="0" y1="21" x2="280" y2="21" stroke="#E7E5E4" stroke-width="1"/>
                </pattern>
            """,
            "pat_id": "url(#pat_ruled)",
            "margin_color": "#A855F7",
            "title_color": "#3B0764",
            "hl_bg": "#E9D5FF",
            "hl_text": "#3B0764",
            "core_bg": "#FFFFFF",
            "core_border": "#BE123C",
            "core_text": "#9F1239",
            "p1_bg": "#FFFFFF",
            "p1_border": "#581C87",
            "p1_text": "#3B0764",
            "p2_bg": "#FFFFFF",
            "p2_border": "#7E22CE",
            "p2_text": "#6B21A8",
            "p3_bg": "#FAF5FF",
            "p3_border": "#A855F7",
            "p3_text": "#7E22CE",
        },
    }

    v = visual_map.get(tpl_key, visual_map["classic_cream"])
    active_cls = "tpl-preview-card-active" if is_active else ""
    right_label = "Active" if is_active else v["sub_label"]

    return f"""
    <div class="tpl-preview-card {active_cls}">
        <div class="tpl-svg-wrap">
            <svg viewBox="0 0 280 132" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    {v["pattern"]}
                </defs>
                <rect width="280" height="132" fill="{v["bg"]}"/>
                <rect width="280" height="132" fill="{v["pat_id"]}"/>
                <line x1="20" y1="0" x2="20" y2="132" stroke="{v["margin_color"]}" stroke-width="1.8" opacity="0.85"/>

                <text x="31" y="30" fill="{v["title_color"]}" font-family="'Caveat', cursive, sans-serif" font-size="21" font-weight="700" font-style="italic">
                    01 // System Architecture
                </text>

                <rect x="31" y="45" width="122" height="26" rx="6" fill="{v["hl_bg"]}"/>
                <text x="92" y="58.5" fill="{v["hl_text"]}" font-family="'Caveat', cursive, sans-serif" font-size="15.5" font-weight="700" text-anchor="middle" dominant-baseline="central">
                    Highlighted Key
                </text>

                <rect x="163" y="45" width="84" height="26" rx="6" fill="{v["core_bg"]}" stroke="{v["core_border"]}" stroke-width="1.5"/>
                <text x="205" y="58.5" fill="{v["core_text"]}" font-family="'Plus Jakarta Sans', sans-serif" font-size="11.5" font-weight="700" text-anchor="middle" dominant-baseline="central">
                    Core Box
                </text>

                <rect x="31" y="88" width="72" height="25" rx="6" fill="{v["p1_bg"]}" stroke="{v["p1_border"]}" stroke-width="1.3"/>
                <text x="67" y="100.5" fill="{v["p1_text"]}" font-family="'JetBrains Mono', monospace" font-size="9.8" font-weight="700" text-anchor="middle" dominant-baseline="central">
                    01 Input
                </text>

                <rect x="109" y="88" width="80" height="25" rx="6" fill="{v["p2_bg"]}" stroke="{v["p2_border"]}" stroke-width="1.3"/>
                <text x="149" y="100.5" fill="{v["p2_text"]}" font-family="'JetBrains Mono', monospace" font-size="9.8" font-weight="700" text-anchor="middle" dominant-baseline="central">
                    02 Process
                </text>

                <rect x="195" y="88" width="74" height="25" rx="6" fill="{v["p3_bg"]}" stroke="{v["p3_border"]}" stroke-width="1.3"/>
                <text x="232" y="100.5" fill="{v["p3_text"]}" font-family="'JetBrains Mono', monospace" font-size="9.8" font-weight="700" text-anchor="middle" dominant-baseline="central">
                    03 Output
                </text>
            </svg>
        </div>
        <div class="tpl-footer-row">
            <span class="tpl-meta-name">{v["short_name"]}</span>
            <span class="tpl-meta-badge">{right_label}</span>
        </div>
    </div>
    """


# =====================================================================
# 3. Session State Initialization
# =====================================================================
env_api_key = os.getenv("GEMINI_API_KEY", "")
if not env_api_key:
    try:
        env_api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        env_api_key = ""

if "selected_subject" not in st.session_state:
    st.session_state.selected_subject = "AI & Machine Learning"
if "ranked_topics" not in st.session_state:
    st.session_state.ranked_topics = get_default_ranked_topics("AI & Machine Learning")
if "selected_rank_idx" not in st.session_state:
    st.session_state.selected_rank_idx = 0
if "selected_template" not in st.session_state:
    st.session_state.selected_template = "classic_cream"
if "selected_language" not in st.session_state:
    st.session_state.selected_language = "Sinhala_Mix"
if "selected_page_count" not in st.session_state:
    st.session_state.selected_page_count = 5
if "carousel_data" not in st.session_state:
    st.session_state.carousel_data = None
if "active_topic_title" not in st.session_state:
    st.session_state.active_topic_title = ""

# =====================================================================
# 4. Top Woday-Styled Header
# =====================================================================
st.markdown(
    """
<div class="woday-nav">
    <div class="woday-brand">
        <div class="woday-logo-box">N</div>
        <span>NIWNOTES</span>
    </div>
    <div class="woday-nav-pills">
        <span class="woday-pill">8 University Tracks</span>
        <span class="woday-pill">5 / 10 / 30 Pages</span>
        <span class="woday-pill-active">Turbo Zero-Wait Studio</span>
    </div>
</div>

<div class="woday-hero">
    <div class="woday-eyebrow">
        <span class="woday-eyebrow-dot"></span>
        <span>All-in-One University Sketchnote &amp; Social Learning Studio</span>
    </div>
    <div class="woday-title">Study Notes, Ranked &amp; Visualized.</div>
    <div class="woday-subtitle">
        Pick a top-ranked university topic, preview your notebook aesthetic, choose <strong>5, 10, or 30 pages</strong>,
        and generate handwritten carousels with matching <strong>Kuppiya Sinhala + English</strong> or <strong>English</strong> captions in seconds.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

if not env_api_key:
    with st.expander("Configure Gemini API Key", expanded=True):
        api_key = st.text_input(
            "Enter your Google Gemini API Key (Free at aistudio.google.com)",
            type="password",
        )
else:
    api_key = env_api_key

# =====================================================================
# 5. Two-Column Woday Bento Control Workspace
# =====================================================================
left_col, right_col = st.columns([1.12, 1.0], gap="large")

with left_col:
    with st.container(border=True):
        st.markdown(
            """
        <div class="mac-card-bar">
            <div class="mac-dots">
                <div class="mac-dot mac-dot-r"></div>
                <div class="mac-dot mac-dot-y"></div>
                <div class="mac-dot mac-dot-g"></div>
            </div>
            <div class="mac-card-label">Curriculum &amp; Ranked Topics (#01 - #05)</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-step-title"><span class="step-num-badge">01</span> Select University Subject Track</div>',
            unsafe_allow_html=True,
        )

        subject_list = list(UNIVERSITY_SUBJECTS.keys())
        sub_col1, sub_col2 = st.columns([3.2, 1.2])
        with sub_col1:
            chosen_subject = st.selectbox(
                "Subject Category",
                options=subject_list,
                index=subject_list.index(st.session_state.selected_subject),
                format_func=lambda s: f"[{UNIVERSITY_SUBJECTS[s]['code']}]  {s}",
                label_visibility="collapsed",
            )
            if chosen_subject != st.session_state.selected_subject:
                st.session_state.selected_subject = chosen_subject
                st.session_state.ranked_topics = get_default_ranked_topics(chosen_subject)
                st.session_state.selected_rank_idx = 0
                st.rerun()

        with sub_col2:
            if st.button("Live Refresh", use_container_width=True):
                if api_key:
                    with st.spinner("Scanning live trends..."):
                        models = get_working_models(api_key)
                        res = discover_viral_topics(models, st.session_state.selected_subject, api_key)
                        st.session_state.ranked_topics = res.topics
                        st.session_state.selected_rank_idx = 0
                        st.rerun()

        st.markdown(
            '<div class="section-step-title" style="margin-top:8px;"><span class="step-num-badge">02</span> Top 5 Ranked Topics (Click to Select)</div>',
            unsafe_allow_html=True,
        )

        for idx, t_item in enumerate(st.session_state.ranked_topics[:5]):
            is_selected = idx == st.session_state.selected_rank_idx
            card_cls = "rank-card rank-card-active" if is_selected else "rank-card"
            num_cls = "rank-number rank-number-top" if idx == 0 else "rank-number"

            r_col_card, r_col_btn = st.columns([4.3, 1.0])
            with r_col_card:
                st.markdown(
                    f"""
                <div class="{card_cls}">
                    <div class="rank-top-row">
                        <span class="{num_cls}">RANK #{idx + 1:02d}</span>
                        <span class="rank-cat-badge">{t_item.category}</span>
                    </div>
                    <div class="rank-title">{t_item.title}</div>
                    <div class="rank-summary">{t_item.summary}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            with r_col_btn:
                st.write("")
                btn_label = "Selected" if is_selected else f"Pick #{idx + 1}"
                if st.button(
                    btn_label,
                    key=f"pick_rank_{idx}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.selected_rank_idx = idx
                    st.rerun()

        custom_topic = st.text_input(
            "Custom University Lecture Topic (Optional Override)",
            placeholder="e.g., Dijkstra's Shortest Path, Deadlock Prevention in OS, Transformer Attention...",
        )

with right_col:
    with st.container(border=True):
        st.markdown(
            """
        <div class="mac-card-bar">
            <div class="mac-dots">
                <div class="mac-dot mac-dot-r"></div>
                <div class="mac-dot mac-dot-y"></div>
                <div class="mac-dot mac-dot-g"></div>
            </div>
            <div class="mac-card-label">Visual Style, Language &amp; Page Count</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-step-title"><span class="step-num-badge">03</span> Pick a Note Template</div>',
            unsafe_allow_html=True,
        )

        tpl_short_names = {
            "classic_cream": "Classic Cream",
            "dark_neon": "Obsidian Dark",
            "blueprint_grid": "Blueprint Grid",
            "cornell_academic": "Cornell Exam",
        }
        tpl_keys = list(NOTE_TEMPLATES.keys())
        tpl_grid_1 = st.columns(2)
        tpl_grid_2 = st.columns(2)
        tpl_cols = [tpl_grid_1[0], tpl_grid_1[1], tpl_grid_2[0], tpl_grid_2[1]]

        for idx, t_key in enumerate(tpl_keys):
            with tpl_cols[idx]:
                is_tpl_active = st.session_state.selected_template == t_key
                st.markdown(render_template_mini_preview(t_key, is_tpl_active), unsafe_allow_html=True)
                btn_lbl = "Selected" if is_tpl_active else f"Use {tpl_short_names[t_key]}"
                if st.button(
                    btn_lbl,
                    key=f"tpl_btn_{t_key}",
                    type="primary" if is_tpl_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.selected_template = t_key
                    st.rerun()

        st.markdown("<hr style='margin: 12px 0; border-color: rgba(20,20,19,0.08);'>", unsafe_allow_html=True)

        st.markdown(
            '<div class="section-step-title"><span class="step-num-badge">04</span> Note &amp; Social Caption Language</div>',
            unsafe_allow_html=True,
        )

        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            is_sinhala = st.session_state.selected_language == "Sinhala_Mix"
            if st.button(
                "Sinhala + English (Kuppiya Mix)",
                type="primary" if is_sinhala else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_language = "Sinhala_Mix"
                st.rerun()
        with lang_col2:
            is_english = st.session_state.selected_language == "English"
            if st.button(
                "100% Academic English",
                type="primary" if is_english else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_language = "English"
                st.rerun()

        st.markdown("<hr style='margin: 12px 0; border-color: rgba(20,20,19,0.08);'>", unsafe_allow_html=True)

        st.markdown(
            '<div class="section-step-title"><span class="step-num-badge">05</span> Study Deck Length (Number of Pages)</div>',
            unsafe_allow_html=True,
        )

        pg_col1, pg_col2, pg_col3 = st.columns(3)
        for col_obj, pg_val, pg_desc in [
            (pg_col1, 5, "5 Pages (Quick)"),
            (pg_col2, 10, "10 Pages (Deep)"),
            (pg_col3, 30, "30 Pages (Full Book)"),
        ]:
            with col_obj:
                is_pg_active = st.session_state.selected_page_count == pg_val
                if st.button(
                    pg_desc,
                    key=f"pg_btn_{pg_val}",
                    type="primary" if is_pg_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.selected_page_count = pg_val
                    st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        active_ranked_topic = st.session_state.ranked_topics[st.session_state.selected_rank_idx].title
        final_topic = custom_topic.strip() if custom_topic.strip() else active_ranked_topic

        if st.button(
            f"Generate {st.session_state.selected_page_count}-Page Study Carousel",
            type="primary",
            use_container_width=True,
        ):
            if not api_key:
                st.error("Please configure your Gemini API key first.")
            else:
                with st.spinner(
                    f"Generating {st.session_state.selected_page_count}-page study guide on '{final_topic[:45]}'..."
                ):
                    try:
                        carousel_data = generate_5_page_study_guide(
                            topic=final_topic,
                            language=st.session_state.selected_language,
                            api_key=api_key,
                            subject_category=st.session_state.selected_subject,
                            num_pages=st.session_state.selected_page_count,
                        )
                        st.session_state.carousel_data = carousel_data
                        st.session_state.active_topic_title = final_topic
                    except Exception as e:
                        st.error(f"Error during generation: {e}")

# =====================================================================
# 6. Zero-Wait Interactive Sketchnote & Social Post Studio
# =====================================================================
if st.session_state.carousel_data:
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    studio_html = build_interactive_studio_html(
        carousel_data=st.session_state.carousel_data,
        topic=st.session_state.active_topic_title,
        template_id=st.session_state.selected_template,
        subject_category=st.session_state.selected_subject,
        language=st.session_state.selected_language,
    )
    components.html(studio_html, height=1020, scrolling=True)
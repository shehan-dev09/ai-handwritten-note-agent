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

/* Template Miniature Sample Cards (Pure HTML/CSS, Zero Line-Wrap) */
.tpl-card {
    border-radius: 16px;
    padding: 10px 10px 12px 10px;
    border: 1.5px solid rgba(20, 20, 19, 0.09);
    background: #FFFFFF;
    margin-bottom: 8px;
    transition: all 0.16s ease;
}
.tpl-card-active {
    border: 2.5px solid #141413;
    background: #FFFFFF;
    box-shadow: 0 8px 22px -4px rgba(20, 20, 19, 0.12);
}
.tpl-sheet {
    height: 118px;
    border-radius: 10px;
    padding: 10px 12px 10px 22px;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(20, 20, 19, 0.10);
    margin-bottom: 9px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.tpl-margin-line {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 13px;
    width: 2px;
}
.tpl-head-title {
    font-family: 'Caveat', cursive, sans-serif;
    font-size: 1.18rem;
    font-weight: 700;
    line-height: 1.05;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.tpl-mid-row {
    display: flex;
    align-items: center;
    gap: 6px;
}
.tpl-hl-tag {
    font-family: 'Caveat', cursive, sans-serif;
    font-size: 0.92rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 5px;
    line-height: 1.1;
    white-space: nowrap;
}
.tpl-core-tag {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.66rem;
    font-weight: 700;
    padding: 3px 7px;
    border-radius: 5px;
    line-height: 1.1;
    white-space: nowrap;
}
.tpl-step-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
    width: 100%;
}
.tpl-step-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    font-weight: 700;
    padding: 4px 3px;
    border-radius: 5px;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.1;
}
.tpl-footer-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 2px;
}
.tpl-meta-name {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.86rem;
    font-weight: 800;
    color: #141413;
}
.tpl-meta-badge {
    font-size: 0.73rem;
    color: #787774;
    font-weight: 600;
}

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
    Renders a clean HTML/CSS miniature preview card for each template.
    Uses unindented markup so Streamlit never converts it to a Markdown code block,
    and strict CSS grid + nowrap so '01 Input', '02 Process', '03 Output' never wrap.
    """
    styles = {
        "classic_cream": {
            "short_name": "Classic Cream",
            "sub_label": "Warm Dot-Grid",
            "sheet_style": "background-color:#FAF6EE; background-image:radial-gradient(#D6D1C7 1.2px, transparent 1.2px); background-size:16px 16px;",
            "margin_bg": "#F87171",
            "title_color": "#1E293B",
            "hl_style": "background:#FDE047; color:#1E293B;",
            "core_style": "background:#FFFFFF; border:1.5px solid #DC2626; color:#B91C1C;",
            "p1_style": "background:#FFFFFF; border:1.2px solid #1E293B; color:#1E293B;",
            "p2_style": "background:#FFFFFF; border:1.2px solid #2563EB; color:#1D4ED8;",
            "p3_style": "background:#FEF9C3; border:1.2px solid #D97706; color:#B45309;",
        },
        "dark_neon": {
            "short_name": "Obsidian Dark",
            "sub_label": "Dark Dot-Grid",
            "sheet_style": "background-color:#0F172A; background-image:radial-gradient(#334155 1.2px, transparent 1.2px); background-size:16px 16px;",
            "margin_bg": "#10B981",
            "title_color": "#F8FAFC",
            "hl_style": "background:#064E3B; color:#ECFDF5;",
            "core_style": "background:#0F172A; border:1.5px solid #22C55E; color:#4ADE80;",
            "p1_style": "background:#1E293B; border:1.2px solid #475569; color:#E2E8F0;",
            "p2_style": "background:#0F172A; border:1.2px solid #38BDF8; color:#38BDF8;",
            "p3_style": "background:#052E16; border:1.2px solid #22C55E; color:#4ADE80;",
        },
        "blueprint_grid": {
            "short_name": "Blueprint Grid",
            "sub_label": "Engineering Graph",
            "sheet_style": "background-color:#F2F8FF; background-image:linear-gradient(to right, #DCEBFA 1px, transparent 1px), linear-gradient(to bottom, #DCEBFA 1px, transparent 1px); background-size:16px 16px;",
            "margin_bg": "#60A5FA",
            "title_color": "#0369A1",
            "hl_style": "background:#BAE6FD; color:#0C4A6E;",
            "core_style": "background:#FFFFFF; border:1.5px solid #EA580C; color:#C2410C;",
            "p1_style": "background:#FFFFFF; border:1.2px solid #0284C7; color:#0369A1;",
            "p2_style": "background:#FFFFFF; border:1.2px solid #2563EB; color:#1D4ED8;",
            "p3_style": "background:#FFF7ED; border:1.2px solid #EA580C; color:#C2410C;",
        },
        "cornell_academic": {
            "short_name": "Cornell Exam",
            "sub_label": "Ruled Ivory Sheet",
            "sheet_style": "background-color:#FCFBF9; background-image:repeating-linear-gradient(transparent, transparent 21px, #E7E5E4 21px, #E7E5E4 22px); background-size:100% 22px;",
            "margin_bg": "#A855F7",
            "title_color": "#3B0764",
            "hl_style": "background:#E9D5FF; color:#3B0764;",
            "core_style": "background:#FFFFFF; border:1.5px solid #BE123C; color:#9F1239;",
            "p1_style": "background:#FFFFFF; border:1.2px solid #581C87; color:#3B0764;",
            "p2_style": "background:#FFFFFF; border:1.2px solid #7E22CE; color:#6B21A8;",
            "p3_style": "background:#FAF5FF; border:1.2px solid #A855F7; color:#7E22CE;",
        },
    }

    s = styles.get(tpl_key, styles["classic_cream"])
    active_cls = "tpl-card-active" if is_active else ""
    status_text = "Active" if is_active else s["sub_label"]

    return (
        f'<div class="tpl-card {active_cls}">'
        f'<div class="tpl-sheet" style="{s["sheet_style"]}">'
        f'<div class="tpl-margin-line" style="background:{s["margin_bg"]};"></div>'
        f'<div class="tpl-head-title" style="color:{s["title_color"]};">01 // System Architecture</div>'
        f'<div class="tpl-mid-row">'
        f'<span class="tpl-hl-tag" style="{s["hl_style"]}">Highlighted Key</span>'
        f'<span class="tpl-core-tag" style="{s["core_style"]}">Core Box</span>'
        f'</div>'
        f'<div class="tpl-step-grid">'
        f'<div class="tpl-step-pill" style="{s["p1_style"]}">01 Input</div>'
        f'<div class="tpl-step-pill" style="{s["p2_style"]}">02 Process</div>'
        f'<div class="tpl-step-pill" style="{s["p3_style"]}">03 Output</div>'
        f'</div>'
        f'</div>'
        f'<div class="tpl-footer-row">'
        f'<span class="tpl-meta-name">{s["short_name"]}</span>'
        f'<span class="tpl-meta-badge">{status_text}</span>'
        f'</div>'
        f'</div>'
    )


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
                    f'<div class="{card_cls}">'
                    f'<div class="rank-top-row">'
                    f'<span class="{num_cls}">RANK #{idx + 1:02d}</span>'
                    f'<span class="rank-cat-badge">{t_item.category}</span>'
                    f'</div>'
                    f'<div class="rank-title">{t_item.title}</div>'
                    f'<div class="rank-summary">{t_item.summary}</div>'
                    f'</div>',
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
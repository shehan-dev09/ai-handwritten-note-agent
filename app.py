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
    page_title="NIWNOTES — University Study Notes & Carousel Studio",
    page_icon="📓",
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
        font-size: 16px;
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

    /* Template Visual Preview Card */
    .tpl-preview-card {
        border-radius: 14px;
        padding: 10px;
        border: 2px solid rgba(20, 20, 19, 0.09);
        background: #FAF9F5;
        margin-bottom: 6px;
    }
    .tpl-preview-card-active {
        border: 2.5px solid #141413;
        background: #FFFFFF;
        box-shadow: 0 8px 20px -4px rgba(20, 20, 19, 0.12);
    }
    .tpl-mini-sheet {
        height: 92px;
        border-radius: 9px;
        padding: 9px 11px;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.12);
        margin-bottom: 8px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .tpl-mini-title {
        font-family: 'Caveat', cursive;
        font-size: 1.1rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .tpl-mini-hl {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 4px;
        width: fit-content;
    }
    .tpl-mini-box {
        font-size: 0.66rem;
        font-weight: 700;
        padding: 3px 7px;
        border-radius: 5px;
        display: flex;
        justify-content: space-between;
    }
    .tpl-meta-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.83rem;
        font-weight: 700;
        color: #141413;
    }
    .tpl-meta-badge {
        font-size: 0.69rem;
        color: #575653;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background-color: #141413 !important;
        color: #FFFFFF !important;
        border: 1px solid #141413 !important;
        border-radius: 11px !important;
        padding: 0.5rem 0.9rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.83rem !important;
        box-shadow: 0 4px 12px rgba(20, 20, 19, 0.12) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #F3F2EE !important;
        color: #141413 !important;
        border: 1px solid rgba(20, 20, 19, 0.10) !important;
        border-radius: 11px !important;
        padding: 0.5rem 0.9rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.83rem !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #EAE8E1 !important;
        border-color: #141413 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


def render_template_mini_preview(tpl_key: str, is_active: bool) -> str:
    """Renders a miniature visual notebook preview card for the template selector."""
    t = NOTE_TEMPLATES[tpl_key]
    active_cls = "tpl-preview-card-active" if is_active else ""
    status_pill = "● Selected" if is_active else "Preview"

    return f"""
    <div class="tpl-preview-card {active_cls}">
        <div class="tpl-mini-sheet" style="background-color:{t['paper_bg']}; background-image:{t['line_css']}; background-size:18px 18px;">
            <div class="tpl-mini-title" style="color:{t['title_color']};">
                Page 01 • Core Architecture
            </div>
            <div class="tpl-mini-hl" style="background:{t['highlight_bg']}; color:{t['text_color']};">
                ★ Key Exam Concept Highlight
            </div>
            <div class="tpl-mini-box" style="background:{t['box_bg']}; border:1.5px solid {t['box_border']}; color:{t['accent_color']};">
                <span>⚡ 01 → 02 → 03 Flow</span>
                <span>💡 Tip</span>
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div class="tpl-meta-name">{t['name']}</div>
                <div class="tpl-meta-badge">{t['badge']}</div>
            </div>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; font-weight:700; color:{'#16A34A' if is_active else '#8A8884'};">
                {status_pill}
            </span>
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
        <div class="woday-logo-box">📓</div>
        <span>NIWNOTES</span>
    </div>
    <div class="woday-nav-pills">
        <span class="woday-pill">🎓 8 University Tracks</span>
        <span class="woday-pill">📑 5 • 10 • 30 Pages</span>
        <span class="woday-pill-active">⚡ Turbo Zero-Wait Studio</span>
    </div>
</div>

<div class="woday-hero">
    <div class="woday-eyebrow">
        <span class="woday-eyebrow-dot"></span>
        <span>All-in-One University Sketchnote & Social Learning Studio</span>
    </div>
    <div class="woday-title">Study Notes, Ranked & Visualized.</div>
    <div class="woday-subtitle">
        Pick a top-ranked university topic, preview your notebook aesthetic, choose <strong>5, 10, or 30 pages</strong>,
        and generate handwritten carousels with matching <strong>Kuppiya Sinhala + English</strong> or <strong>English</strong> captions in seconds.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

if not env_api_key:
    with st.expander("🔑 Configure Gemini API Key", expanded=True):
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
            <div class="mac-card-label">Curriculum & Ranked Topics (#01 – #05)</div>
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
                format_func=lambda s: f"{UNIVERSITY_SUBJECTS[s]['icon']}  {s}",
                label_visibility="collapsed",
            )
            if chosen_subject != st.session_state.selected_subject:
                st.session_state.selected_subject = chosen_subject
                st.session_state.ranked_topics = get_default_ranked_topics(chosen_subject)
                st.session_state.selected_rank_idx = 0
                st.rerun()

        with sub_col2:
            if st.button("🔄 Live Refresh", use_container_width=True):
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
                btn_label = "✓ Active" if is_selected else f"Pick #{idx + 1}"
                if st.button(
                    btn_label,
                    key=f"pick_rank_{idx}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.selected_rank_idx = idx
                    st.rerun()

        custom_topic = st.text_input(
            "✏️ Or Type Any Custom University Lecture Topic (Optional Override)",
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
            <div class="mac-card-label">Visual Style, Language & Page Count</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-step-title"><span class="step-num-badge">03</span> Choose Notebook Template (Visual Sample)</div>',
            unsafe_allow_html=True,
        )

        tpl_keys = list(NOTE_TEMPLATES.keys())
        tpl_grid_1 = st.columns(2)
        tpl_grid_2 = st.columns(2)
        tpl_cols = [tpl_grid_1[0], tpl_grid_1[1], tpl_grid_2[0], tpl_grid_2[1]]

        for idx, t_key in enumerate(tpl_keys):
            with tpl_cols[idx]:
                is_tpl_active = st.session_state.selected_template == t_key
                st.markdown(render_template_mini_preview(t_key, is_tpl_active), unsafe_allow_html=True)
                btn_lbl = f"✓ {NOTE_TEMPLATES[t_key]['name'][:16]}" if is_tpl_active else "Use Template"
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
            '<div class="section-step-title"><span class="step-num-badge">04</span> Note & Social Caption Language</div>',
            unsafe_allow_html=True,
        )

        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            is_sinhala = st.session_state.selected_language == "Sinhala_Mix"
            if st.button(
                "🇱🇰 Sinhala + English (Kuppiya Mix)",
                type="primary" if is_sinhala else "secondary",
                use_container_width=True,
            ):
                st.session_state.selected_language = "Sinhala_Mix"
                st.rerun()
        with lang_col2:
            is_english = st.session_state.selected_language == "English"
            if st.button(
                "🇬🇧 100% Academic English",
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
            (pg_col1, 5, "📄 5 Pages (Quick)"),
            (pg_col2, 10, "📑 10 Pages (Deep)"),
            (pg_col3, 30, "📚 30 Pages (Full Book)"),
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
            f"⚡ Generate {st.session_state.selected_page_count}-Page Study Carousel Now",
            type="primary",
            use_container_width=True,
        ):
            if not api_key:
                st.error("Please configure your Gemini API key first.")
            else:
                with st.spinner(
                    f"⚡ Turbo Engine: Writing {st.session_state.selected_page_count}-page study guide on '{final_topic[:45]}'..."
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
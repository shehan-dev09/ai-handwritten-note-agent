import io
import os
import time
import zipfile
from dotenv import load_dotenv
from note_generator import (
    NOTE_TEMPLATES,
    generate_5_page_study_guide,
    get_working_models,
    render_all_pages,
)
import streamlit as st
from trend_agent import UNIVERSITY_SUBJECTS, discover_viral_topics

load_dotenv()

# =====================================================================
# AUTO-SYNC CLEAN LIGHT THEME IN .streamlit/config.toml
# =====================================================================
os.makedirs(".streamlit", exist_ok=True)
config_path = os.path.join(".streamlit", "config.toml")
expected_config = (
    '[theme]\n'
    'base = "light"\n'
    'primaryColor = "#141413"\n'
    'backgroundColor = "#F7F6F2"\n'
    'secondaryBackgroundColor = "#FFFFFF"\n'
    'textColor = "#141413"\n'
    'font = "sans serif"\n\n'
    '[server]\n'
    'headless = true\n'
)
if not os.path.exists(config_path) or open(config_path, "r", encoding="utf-8").read() != expected_config:
    with open(config_path, "w", encoding="utf-8") as cf:
        cf.write(expected_config)

# =====================================================================
# PAGE CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="NIWNOTES — All-in-One University Study Note Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# WODAY.APP INSPIRED CLEAN macOS DESIGN SYSTEM
# =====================================================================
WODAY_CLEAN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root, html, body, .stApp {
    --canvas-bg: #F7F6F2;
    --card-bg: #FFFFFF;
    --surface-subtle: #F3F2EE;
    --ink-primary: #141413;
    --ink-secondary: #575653;
    --ink-muted: #8A8884;
    --accent-coral: #FF5A36;
    --accent-blue: #2563EB;
    --accent-green: #16A34A;
    --border-hairline: rgba(20, 20, 19, 0.08);
    --border-strong: rgba(20, 20, 19, 0.14);
    --shadow-card: 0 14px 34px -12px rgba(20, 20, 19, 0.06),
                   0 2px 6px -1px rgba(20, 20, 19, 0.04);
    --shadow-pill: 0 2px 8px rgba(20, 20, 19, 0.05);
}

/* ---------- Warm Daylight Canvas ---------- */
.stApp {
    background:
        radial-gradient(ellipse 65% 38% at 50% -8%, rgba(255, 168, 120, 0.14), transparent 65%),
        radial-gradient(ellipse 45% 30% at 85% 12%, rgba(96, 165, 250, 0.08), transparent 60%),
        var(--canvas-bg) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--ink-primary) !important;
    overflow-x: hidden !important;
}

/* Hide Default Streamlit Chrome */
#MainMenu,
footer,
header[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stToolbar"] {
    display: none !important;
}

.block-container {
    max-width: 1380px !important;
    padding: 1.25rem 1.75rem 3rem 1.75rem !important;
    margin: 0 auto !important;
}

/* ---------- Floating macOS Pill Navigation Bar ---------- */
.woday-nav-wrap {
    display: flex;
    justify-content: center;
    margin-bottom: 1.4rem;
}

.woday-navbar {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    padding: 0.65rem 1rem 0.65rem 0.85rem;
    background: rgba(255, 255, 255, 0.86);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
            backdrop-filter: blur(16px) saturate(180%);
    border: 1px solid var(--border-hairline);
    border-radius: 16px;
    box-shadow: var(--shadow-pill);
}

.woday-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}

.woday-logo-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    background: var(--ink-primary);
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 6px rgba(20, 20, 19, 0.18);
}

.woday-brand-name {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 0.98rem;
    letter-spacing: -0.02em;
    color: var(--ink-primary);
}

.woday-brand-tag {
    font-size: 0.76rem;
    font-weight: 500;
    color: var(--ink-secondary);
    background: var(--surface-subtle);
    padding: 0.22rem 0.65rem;
    border-radius: 99px;
}

.woday-nav-pills {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.74rem;
    font-weight: 500;
    color: var(--ink-secondary);
    background: var(--surface-subtle);
    border: 1px solid var(--border-hairline);
    padding: 0.28rem 0.72rem;
    border-radius: 99px;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent-green);
}

/* ---------- Centered Clean Editorial Hero ---------- */
.woday-hero {
    text-align: center;
    max-width: 760px;
    margin: 0 auto 1.65rem auto;
    padding: 0.25rem 0.5rem;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: #FFFFFF;
    border: 1px solid var(--border-hairline);
    box-shadow: var(--shadow-pill);
    padding: 0.3rem 0.85rem;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--ink-secondary);
    margin-bottom: 0.85rem;
}

.hero-badge-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--accent-coral);
}

.hero-headline {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: clamp(1.95rem, 3.6vw, 2.85rem);
    line-height: 1.08;
    letter-spacing: -0.035em;
    color: var(--ink-primary);
    margin: 0 0 0.65rem 0;
}

.hero-subtitle {
    font-size: 0.96rem;
    line-height: 1.55;
    color: var(--ink-secondary);
    max-width: 600px;
    margin: 0 auto;
    font-weight: 400;
}

/* ---------- Elevated macOS Bento Cards ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 20px !important;
    padding: 1.4rem 1.45rem !important;
    box-shadow: var(--shadow-card) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
    gap: 0.75rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* ---------- Card Header & macOS Window Bar ---------- */
.card-step-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ink-secondary);
    background: var(--surface-subtle);
    padding: 0.22rem 0.6rem;
    border-radius: 6px;
    margin-bottom: 0.3rem;
}

.card-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink-primary);
    margin: 0 0 0.15rem 0;
}

.macos-window-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 0.75rem;
    margin-bottom: 0.65rem;
    border-bottom: 1px solid var(--border-hairline);
}

.traffic-lights {
    display: flex;
    align-items: center;
    gap: 7px;
}

.tl-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}
.tl-red { background: #FF5F56; border: 1px solid rgba(0,0,0,0.06); }
.tl-yellow { background: #FFBD2E; border: 1px solid rgba(0,0,0,0.06); }
.tl-green { background: #27C93F; border: 1px solid rgba(0,0,0,0.06); }

.window-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--ink-muted);
}

/* ---------- Template Swatch Bar ---------- */
.template-card-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--surface-subtle);
    border: 1px solid var(--border-hairline);
    border-radius: 11px;
    padding: 0.5rem 0.8rem;
    font-size: 0.76rem;
    font-weight: 600;
    color: var(--ink-primary);
}

.swatch-row {
    display: flex;
    align-items: center;
    gap: 6px;
}

.swatch-chip {
    width: 15px;
    height: 15px;
    border-radius: 5px;
    border: 1px solid rgba(20, 20, 19, 0.18);
}

/* ---------- Clean Inputs & Selectboxes ---------- */
[data-testid="stWidgetLabel"] p, label {
    color: var(--ink-secondary) !important;
    font-size: 0.79rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.15rem !important;
}

[data-baseweb="input"],
[data-baseweb="select"] > div {
    background-color: var(--surface-subtle) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 11px !important;
    color: var(--ink-primary) !important;
    min-height: 41px !important;
    box-shadow: none !important;
    transition: all 0.16s ease !important;
}

[data-baseweb="input"]:hover,
[data-baseweb="select"] > div:hover {
    border-color: var(--border-strong) !important;
    background-color: #EFECE6 !important;
}

[data-baseweb="input"]:focus-within,
[data-baseweb="select"] > div:focus-within {
    background-color: #FFFFFF !important;
    border-color: var(--ink-primary) !important;
    box-shadow: 0 0 0 3px rgba(20, 20, 19, 0.07) !important;
}

[data-baseweb="base-input"] {
    background: transparent !important;
    border: none !important;
}

[data-baseweb="input"] input {
    color: var(--ink-primary) !important;
    font-size: 0.86rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 0.8rem !important;
    caret-color: var(--ink-primary) !important;
}

div[data-baseweb="popover"] ul {
    background: #FFFFFF !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 28px rgba(20, 20, 19, 0.1) !important;
}

/* ---------- Tactile macOS Buttons ---------- */
[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button {
    background: #FFFFFF !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 11px !important;
    color: var(--ink-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    min-height: 40px !important;
    padding: 0.45rem 0.9rem !important;
    box-shadow: 0 1px 2px rgba(20, 20, 19, 0.04) !important;
    transition: all 0.16s ease !important;
}

[data-testid="stButton"] > button p,
[data-testid="stDownloadButton"] > button p {
    color: var(--ink-primary) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}

[data-testid="stButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover {
    background: var(--surface-subtle) !important;
    border-color: rgba(20, 20, 19, 0.28) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(20, 20, 19, 0.06) !important;
}

/* Primary Charcoal Pill Button (Woday CTA Style) */
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stDownloadButton"] > button[kind="primary"] {
    background: var(--ink-primary) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--ink-primary) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    min-height: 44px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 8px 20px -6px rgba(20, 20, 19, 0.35) !important;
}

[data-testid="stButton"] > button[kind="primary"] p,
[data-testid="stButton"] > button[kind="primary"] span,
[data-testid="stDownloadButton"] > button[kind="primary"] p,
[data-testid="stDownloadButton"] > button[kind="primary"] span {
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

[data-testid="stButton"] > button[kind="primary"]:hover,
[data-testid="stDownloadButton"] > button[kind="primary"]:hover {
    background: #272725 !important;
    border-color: #272725 !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25),
                0 12px 24px -6px rgba(20, 20, 19, 0.45) !important;
}

/* ---------- macOS Segmented Pill Tabs ---------- */
[data-baseweb="tab-list"] {
    background: var(--surface-subtle) !important;
    padding: 4px !important;
    border-radius: 12px !important;
    gap: 4px !important;
    border-bottom: none !important;
    width: fit-content !important;
    margin-bottom: 0.4rem !important;
}

button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: var(--ink-secondary) !important;
    padding: 0.4rem 0.95rem !important;
    border-radius: 9px !important;
    background: transparent !important;
    border: none !important;
    margin: 0 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: #FFFFFF !important;
    color: var(--ink-primary) !important;
    box-shadow: 0 2px 6px rgba(20, 20, 19, 0.08) !important;
}

button[data-baseweb="tab"][aria-selected="true"] p {
    color: var(--ink-primary) !important;
    font-weight: 600 !important;
}

[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] {
    display: none !important;
}

/* ---------- Slide Images & Code Blocks ---------- */
[data-testid="stImage"] img {
    border-radius: 12px !important;
    border: 1px solid var(--border-strong) !important;
    box-shadow: 0 8px 20px -8px rgba(20, 20, 19, 0.12) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stImage"] img:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 28px -8px rgba(20, 20, 19, 0.18) !important;
}

[data-testid="stCode"],
[data-testid="stCodeBlock"],
pre {
    background: var(--surface-subtle) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    color: var(--ink-primary) !important;
}

hr {
    border-color: var(--border-hairline) !important;
    margin: 0.65rem 0 !important;
}

/* ---------- Mobile Responsiveness ---------- */
@media (max-width: 768px) {
    .block-container {
        padding: 0.75rem 0.85rem 2rem 0.85rem !important;
    }
    .woday-brand-tag {
        display: none !important;
    }
    .hero-headline {
        font-size: 1.75rem;
    }
    .hero-subtitle {
        font-size: 0.86rem;
    }
    [data-baseweb="tab-list"] {
        width: 100% !important;
        overflow-x: auto !important;
    }
}
</style>
"""

st.markdown(WODAY_CLEAN_CSS, unsafe_allow_html=True)


# =====================================================================
# CACHED HELPERS FOR INSTANT SPEED
# =====================================================================
@st.cache_data(ttl=900, show_spinner=False)
def cached_discover_topics(api_key: str, subject_category: str):
    models = get_working_models(api_key)
    return discover_viral_topics(
        working_models=models, subject_category=subject_category, api_key=api_key
    )


def load_existing_output():
    if not os.path.exists("output"):
        return None, [], ""
    subfolders = [
        os.path.join("output", d)
        for d in os.listdir("output")
        if os.path.isdir(os.path.join("output", d))
    ]
    candidates = sorted(subfolders, key=os.path.getmtime, reverse=True) + ["output"]
    for folder in candidates:
        pages = [os.path.join(folder, f"note_page_{i}.png") for i in range(1, 6)]
        if all(os.path.exists(p) for p in pages):
            caption_path = os.path.join(folder, "caption.txt")
            caption_text = (
                open(caption_path, "r", encoding="utf-8").read()
                if os.path.exists(caption_path)
                else ""
            )
            topic_label = (
                os.path.basename(folder).replace("_", " ")
                if folder != "output"
                else "Retrieval-Augmented Generation (RAG)"
            )
            return topic_label, pages, caption_text
    return None, [], ""


if "viral_topics" not in st.session_state:
    st.session_state.viral_topics = []
if "last_render_sec" not in st.session_state:
    st.session_state.last_render_sec = None
if "active_topic" not in st.session_state:
    loaded_topic, loaded_imgs, loaded_cap = load_existing_output()
    st.session_state.active_topic = loaded_topic
    st.session_state.image_paths = loaded_imgs
    st.session_state.social_caption = loaded_cap

default_api_key = os.getenv("GEMINI_API_KEY", "")
if not default_api_key:
    try:
        default_api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        default_api_key = ""


# =====================================================================
# TOP FLOATING macOS NAVBAR + CLEAN EDITORIAL HERO
# =====================================================================
speed_label = (
    f"Rendered in {st.session_state.last_render_sec:.1f}s"
    if st.session_state.last_render_sec
    else "Parallel Engine Ready"
)

st.markdown(
    f"""
    <div class="woday-nav-wrap">
        <div class="woday-navbar">
            <div class="woday-brand">
                <div class="woday-logo-icon">N</div>
                <span class="woday-brand-name">NIWNOTES</span>
                <span class="woday-brand-tag">University Study Studio</span>
            </div>
            <div class="woday-nav-pills">
                <span class="status-pill">
                    <span class="status-dot"></span>
                    {speed_label}
                </span>
                <span class="status-pill">8 Campus Tracks</span>
                <span class="status-pill">4 Note Styles</span>
            </div>
        </div>
    </div>

    <div class="woday-hero">
        <div class="hero-badge">
            <span class="hero-badge-dot"></span>
            <span>All-in-One University Study Notes &amp; Social Carousel Maker</span>
        </div>
        <h1 class="hero-headline">Your campus lectures, turned into clear visual notes.</h1>
        <p class="hero-subtitle">
            Pick your university discipline, discover trending topics or type any lecture concept, and generate a 5-page handwritten study post in seconds.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2-PANE BENTO WORKSPACE
# =====================================================================
left_pane, right_pane = st.columns([1.05, 2.25], gap="medium")

with left_pane:
    with st.container(border=True):
        st.markdown(
            """
            <div class="macos-window-bar">
                <div class="traffic-lights">
                    <span class="tl-dot tl-red"></span>
                    <span class="tl-dot tl-yellow"></span>
                    <span class="tl-dot tl-green"></span>
                </div>
                <span class="window-label">composer.niwnotes</span>
            </div>
            <div>
                <span class="card-step-pill">Step 01 · Academic Track</span>
                <div class="card-title">Subject &amp; Topic Discovery</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        subject_list = list(UNIVERSITY_SUBJECTS.keys())
        selected_subject = st.selectbox(
            "University Subject Discipline",
            options=subject_list,
            index=0,
        )

        input_mode = st.selectbox(
            "Topic Source",
            options=[
                "Type Lecture / Exam Topic Manually",
                "Discover Trending Topics for this Subject",
            ],
            index=0,
        )

        if input_mode == "Discover Trending Topics for this Subject":
            if st.button(
                f"Find Trending {selected_subject.split('&')[0].strip()} Topics",
                use_container_width=True,
            ):
                if not default_api_key:
                    st.error("Please enter your Gemini API Key below first.")
                else:
                    with st.spinner(f"Scanning live feeds for {selected_subject}..."):
                        st.session_state.viral_topics = cached_discover_topics(
                            default_api_key, selected_subject
                        )

            if st.session_state.viral_topics:
                topic_titles = [t.topic_title for t in st.session_state.viral_topics]
                final_topic = st.selectbox(
                    "Select a Trending Topic", options=topic_titles
                )
                matched = next(
                    (
                        t
                        for t in st.session_state.viral_topics
                        if t.topic_title == final_topic
                    ),
                    None,
                )
                if matched:
                    st.caption(f"Why it matters: {matched.why_it_is_viral}")
            else:
                final_topic = st.text_input(
                    "Or Enter Topic Directly",
                    value="What is RAG (Retrieval-Augmented Generation) in AI?",
                )
        else:
            default_examples = {
                "AI & Machine Learning": "What is RAG (Retrieval-Augmented Generation) in AI?",
                "Software Engineering & Full-Stack": "Microservices vs Monolithic Architecture Explained",
                "Cybersecurity & Ethical Hacking": "How Zero-Trust Security Architecture Works",
                "Data Science & Big Data Analytics": "Apache Kafka Real-Time Data Streaming Explained",
                "Cloud Computing & DevOps": "How Kubernetes Pod Scheduling & Auto-Scaling Works",
                "Computer Networks & Distributed Systems": "CAP Theorem & Consensus in Distributed Systems",
                "IoT, Robotics & Embedded Systems": "MQTT Protocol vs HTTP in IoT Edge Devices",
                "UI/UX & Product Engineering": "Design Tokens & Atomic Design System Architecture",
            }
            final_topic = st.text_input(
                "Lecture Concept or Technical Topic",
                value=default_examples.get(selected_subject, "What is RAG in AI?"),
            )

        st.markdown("<hr/>", unsafe_allow_html=True)

        st.markdown(
            """
            <div>
                <span class="card-step-pill">Step 02 · Note Aesthetics</span>
                <div class="card-title">Template &amp; Language</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        template_keys = list(NOTE_TEMPLATES.keys())
        selected_template = st.selectbox(
            "Notebook Paper Template",
            options=template_keys,
            format_func=lambda k: f"{NOTE_TEMPLATES[k]['name']} — {NOTE_TEMPLATES[k]['badge']}",
            index=0,
        )

        t_meta = NOTE_TEMPLATES[selected_template]
        st.markdown(
            f"""
            <div class="template-card-bar">
                <span>{t_meta['name']}</span>
                <div class="swatch-row">
                    <span class="swatch-chip" style="background:{t_meta['paper_bg']};"></span>
                    <span class="swatch-chip" style="background:{t_meta['ink_blue']};"></span>
                    <span class="swatch-chip" style="background:{t_meta['ink_red']};"></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_lang, col_author = st.columns([1.35, 1.0], gap="small")
        with col_lang:
            lang_choice = st.selectbox(
                "Explanation Language",
                options=[
                    "Sinhala + English Tech Terms",
                    "100% English (Global)",
                ],
                index=0,
            )
            selected_language = (
                "Sinhala_Mix" if "Sinhala" in lang_choice else "English"
            )
        with col_author:
            author_handle = st.text_input("Author Handle", value="@NIWNOTES")

        if not default_api_key:
            api_key_input = st.text_input("Gemini API Key", type="password")
        else:
            api_key_input = default_api_key

        generate_btn = st.button(
            "Create 5-Page Study Carousel",
            type="primary",
            use_container_width=True,
        )

        if generate_btn:
            if not api_key_input:
                st.error("Missing GEMINI_API_KEY.")
            elif not final_topic.strip():
                st.warning("Please enter a study topic.")
            else:
                t_start = time.perf_counter()
                os.environ["GEMINI_API_KEY"] = api_key_input
                safe_folder = "".join(
                    c if c.isalnum() else "_" for c in final_topic
                )[:35].strip("_")
                out_dir = os.path.join("output", safe_folder)

                with st.status(
                    "Creating your 5-page NIWNOTES study post...", expanded=True
                ) as status:
                    st.write(
                        f"1/2 Writing {selected_subject} study guide..."
                    )
                    guide = generate_5_page_study_guide(
                        topic=final_topic,
                        language=selected_language,
                        api_key=api_key_input,
                        subject_category=selected_subject,
                    )
                    st.write(
                        f"2/2 Rendering 5 slides in parallel ({t_meta['name']})..."
                    )
                    img_paths = render_all_pages(
                        guide=guide,
                        author=author_handle,
                        output_dir=out_dir,
                        template_id=selected_template,
                    )
                    caption_file = os.path.join(out_dir, "caption.txt")
                    with open(caption_file, "w", encoding="utf-8") as f:
                        f.write(guide.social_caption)

                    elapsed = time.perf_counter() - t_start
                    st.session_state.last_render_sec = elapsed
                    st.session_state.active_topic = guide.topic_name
                    st.session_state.image_paths = img_paths
                    st.session_state.social_caption = guide.social_caption
                    status.update(
                        label=f"Ready in {elapsed:.1f}s!", state="complete"
                    )
                st.rerun()

# =====================================================================
# RIGHT PANE: macOS PREVIEW CANVAS & EXPORT
# =====================================================================
with right_pane:
    with st.container(border=True):
        st.markdown(
            """
            <div class="macos-window-bar">
                <div class="traffic-lights">
                    <span class="tl-dot tl-red"></span>
                    <span class="tl-dot tl-yellow"></span>
                    <span class="tl-dot tl-green"></span>
                </div>
                <span class="window-label">preview — 1000×1250px (4:5 Social Portrait)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.image_paths:
            img_paths = st.session_state.image_paths
            caption_text = st.session_state.social_caption
            topic_title = st.session_state.active_topic

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in img_paths:
                    if os.path.exists(p):
                        zf.write(p, arcname=os.path.basename(p))
                if caption_text:
                    zf.writestr("caption.txt", caption_text)
            zip_buffer.seek(0)

            top_l, top_r = st.columns([2.15, 0.95], vertical_alignment="center")
            with top_l:
                st.markdown(
                    f"""
                    <div>
                        <span class="card-step-pill">Active Study Deck · 5 Slides</span>
                        <div class="card-title" style="font-size:1.4rem;">{topic_title}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with top_r:
                st.download_button(
                    label="Download Bundle (.ZIP)",
                    data=zip_buffer,
                    file_name="niwnotes_study_carousel.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                )

            tab_grid, tab_inspect, tab_copy = st.tabs(
                [
                    "5-Slide Overview",
                    "Large Slide Reader",
                    "Social Post Copy",
                ]
            )

            with tab_grid:
                cols = st.columns(5, gap="small")
                for idx, img_path in enumerate(img_paths):
                    with cols[idx]:
                        if os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                            with open(img_path, "rb") as img_file:
                                st.download_button(
                                    label=f"Slide 0{idx+1}",
                                    data=img_file,
                                    file_name=f"niwnotes_slide_{idx+1}.png",
                                    mime="image/png",
                                    key=f"dl_slide_{idx+1}",
                                    use_container_width=True,
                                )

            with tab_inspect:
                slide_num = st.selectbox(
                    "Choose Slide to Read",
                    options=[1, 2, 3, 4, 5],
                    format_func=lambda x: f"Slide 0{x} of 05",
                )
                selected_img = img_paths[slide_num - 1]
                if os.path.exists(selected_img):
                    _, center_col, _ = st.columns([0.35, 2.3, 0.35])
                    with center_col:
                        st.image(selected_img, use_container_width=True)

            with tab_copy:
                st.markdown(
                    '<span class="card-step-pill">LinkedIn &amp; Facebook Caption (Click top-right icon to copy)</span>',
                    unsafe_allow_html=True,
                )
                st.code(caption_text, language="markdown")
        else:
            st.markdown(
                """
                <div style="padding: 4.5rem 1.5rem; text-align: center;">
                    <div style="width:48px;height:48px;border-radius:14px;background:#F3F2EE;color:#141413;
                                display:inline-flex;align-items:center;justify-content:center;
                                font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;font-size:1.3rem;margin-bottom:0.9rem;">
                        N
                    </div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:700;font-size:1.25rem;color:#141413;margin-bottom:0.35rem;">
                        No study deck in workspace yet
                    </div>
                    <div style="font-size: 0.9rem; color: #575653; max-width: 420px; margin: 0 auto;">
                        Select your university subject and notebook style on the left, then click <b>Create 5-Page Study Carousel</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
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
# PAGE CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="NIWNOTES // University Study Post Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# NIWNOTES STUDIO CSS (GREEN x BLACK GLASSMORPHISM // MOBILE + WEB)
# =====================================================================
STUDIO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

:root, html, body, .stApp {
    --bg: #020504;
    --g: #00FF88;
    --lime: #B6FF3C;
    --text-hi: #ECFFF5;
    --text-mid: rgba(214, 255, 232, 0.72);
    --edge: rgba(0, 255, 136, 0.26);
    --glass: linear-gradient(155deg, rgba(10, 26, 18, 0.84) 0%, rgba(3, 9, 6, 0.92) 100%);
    --glass-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12),
                    0 20px 50px -20px rgba(0, 0, 0, 0.92),
                    0 0 36px -16px rgba(0, 255, 136, 0.25);
}

.stApp {
    background:
        radial-gradient(ellipse 70% 45% at 15% -10%, rgba(0, 255, 136, 0.16), transparent 60%),
        radial-gradient(ellipse 55% 40% at 95% 20%, rgba(182, 255, 60, 0.08), transparent 60%),
        var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-hi) !important;
    overflow-x: hidden !important;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(0, 255, 136, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 136, 0.04) 1px, transparent 1px);
    background-size: 52px 52px;
    -webkit-mask-image: radial-gradient(ellipse 85% 70% at 50% 25%, #000 20%, transparent 75%);
            mask-image: radial-gradient(ellipse 85% 70% at 50% 25%, #000 20%, transparent 75%);
    z-index: 0;
}

#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stToolbar"] {
    display: none !important;
}

.block-container {
    max-width: 1420px !important;
    padding: 1.1rem 1.6rem 2.4rem 1.6rem !important;
    margin: 0 auto !important;
    position: relative;
    z-index: 1;
}

/* Glass Cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--glass) !important;
    -webkit-backdrop-filter: blur(20px) saturate(160%);
            backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid var(--edge) !important;
    border-radius: 18px !important;
    padding: 1.3rem 1.35rem !important;
    box-shadow: var(--glass-shadow) !important;
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

/* Navbar */
.studio-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    padding: 0.75rem 1.2rem;
    background: var(--glass);
    border: 1px solid var(--edge);
    border-radius: 13px;
    box-shadow: var(--glass-shadow);
    margin-bottom: 0.2rem;
}

.nav-brand { display: flex; align-items: center; gap: 10px; }
.brand-mark {
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--g);
    box-shadow: 0 0 12px var(--g);
}
.brand-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; font-size: 0.92rem;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--text-hi);
}
.brand-sub { font-size: 0.78rem; color: var(--text-mid); }
.nav-meta {
    display: flex; align-items: center; gap: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: var(--text-mid);
}
.nav-meta .live { color: var(--g); font-weight: 600; }

/* Hero */
.hero {
    padding: 1rem 0.15rem 0.95rem 0.15rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 1rem;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: clamp(1.9rem, 3.8vw, 3.1rem);
    line-height: 0.98;
    letter-spacing: -0.04em;
    margin: 0.25rem 0 0 0;
    background: linear-gradient(180deg, #FFFFFF 15%, #B8FFD9 60%, #00FF88 120%);
    -webkit-background-clip: text; background-clip: text;
    color: transparent;
}
.hero-title .outline {
    -webkit-text-fill-color: transparent;
    -webkit-text-stroke: 1.5px var(--g);
}
.hero-sub {
    max-width: 460px; margin: 0;
    color: var(--text-mid); font-size: 0.85rem; line-height: 1.55;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.15em;
    color: var(--g);
    display: block; margin-bottom: 0.2rem;
}
.panel-heading {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.2rem; font-weight: 600;
    color: var(--text-hi); margin: 0;
}
.workspace-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(1.15rem, 2vw, 1.55rem);
    font-weight: 700; color: var(--text-hi); margin: 0;
}

/* Template Preview Pill */
.template-preview-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(0, 255, 136, 0.07);
    border: 1px solid rgba(0, 255, 136, 0.24);
    border-radius: 10px;
    padding: 0.45rem 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-hi);
}
.swatch-group { display: flex; gap: 6px; align-items: center; }
.swatch-dot { width: 14px; height: 14px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.3); }

/* Inputs & Selectboxes */
[data-testid="stWidgetLabel"] p, label {
    color: var(--text-mid) !important;
    font-size: 0.77rem !important;
    font-weight: 500 !important;
}

[data-baseweb="input"], [data-baseweb="select"] > div {
    background-color: rgba(2, 10, 7, 0.82) !important;
    border: 1px solid rgba(0, 255, 136, 0.25) !important;
    border-radius: 11px !important;
    color: var(--text-hi) !important;
    min-height: 41px !important;
}

[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within {
    border-color: #00FF88 !important;
    box-shadow: 0 0 0 2px rgba(0, 255, 136, 0.18) !important;
}

[data-baseweb="base-input"] { background: transparent !important; border: none !important; }
[data-baseweb="input"] input {
    color: var(--text-hi) !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 0.8rem !important;
    caret-color: #00FF88 !important;
}

div[data-baseweb="popover"] ul {
    background: #040D09 !important;
    border: 1px solid rgba(0, 255, 136, 0.32) !important;
    border-radius: 11px !important;
}

/* Buttons */
[data-testid="stButton"] > button, [data-testid="stDownloadButton"] > button {
    background: rgba(0, 255, 136, 0.07) !important;
    border: 1px solid rgba(0, 255, 136, 0.28) !important;
    border-radius: 11px !important;
    color: var(--text-hi) !important;
    font-weight: 500 !important;
    font-size: 0.81rem !important;
    min-height: 41px !important;
    transition: all 0.18s ease !important;
}
[data-testid="stButton"] > button p, [data-testid="stDownloadButton"] > button p {
    color: var(--text-hi) !important;
    font-size: 0.81rem !important;
}
[data-testid="stButton"] > button:hover, [data-testid="stDownloadButton"] > button:hover {
    border-color: #00FF88 !important;
    background: rgba(0, 255, 136, 0.15) !important;
    box-shadow: 0 0 20px -5px rgba(0, 255, 136, 0.6) !important;
}

[data-testid="stButton"] > button[kind="primary"], [data-testid="stDownloadButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #00FF88 0%, #B6FF3C 130%) !important;
    color: #02120A !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    font-weight: 700 !important;
    min-height: 44px !important;
    box-shadow: 0 0 28px -5px rgba(0, 255, 136, 0.65) !important;
}
[data-testid="stButton"] > button[kind="primary"] p,
[data-testid="stButton"] > button[kind="primary"] span,
[data-testid="stDownloadButton"] > button[kind="primary"] p,
[data-testid="stDownloadButton"] > button[kind="primary"] span {
    color: #02120A !important;
    font-weight: 700 !important;
}

/* Tabs */
[data-baseweb="tab-list"] {
    gap: 6px !important;
    border-bottom: 1px solid rgba(0, 255, 136, 0.16) !important;
    padding-bottom: 8px !important;
}
button[data-baseweb="tab"] {
    font-size: 0.79rem !important;
    color: var(--text-mid) !important;
    padding: 0.45rem 0.9rem !important;
    border-radius: 9px !important;
    background: transparent !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00FF88 !important;
    background: rgba(0, 255, 136, 0.12) !important;
    border: 1px solid rgba(0, 255, 136, 0.38) !important;
}
button[data-baseweb="tab"][aria-selected="true"] p {
    color: #00FF88 !important;
    font-weight: 600 !important;
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }

[data-testid="stImage"] img {
    border-radius: 10px !important;
    border: 1px solid rgba(0, 255, 136, 0.25) !important;
    box-shadow: 0 10px 26px -10px rgba(0, 0, 0, 0.85);
}

hr { border-color: rgba(0, 255, 136, 0.14) !important; margin: 0.5rem 0 !important; }

@media (max-width: 768px) {
    .block-container { padding: 0.65rem 0.75rem 1.75rem 0.75rem !important; }
    .brand-sub { display: none !important; }
    .hero-title { font-size: 1.8rem; }
}
</style>
"""

st.markdown(STUDIO_CSS, unsafe_allow_html=True)


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
# TOP NAVBAR + NIWNOTES HERO
# =====================================================================
speed_badge = (
    f"LAST RENDER: {st.session_state.last_render_sec:.1f}S"
    if st.session_state.last_render_sec
    else "PARALLEL ENGINE // 4X FASTER"
)

st.markdown(
    f"""
    <div class="studio-navbar">
        <div class="nav-brand">
            <div class="brand-mark"></div>
            <span class="brand-title">NIWNOTES</span>
            <span style="color:rgba(255,255,255,0.2);">/</span>
            <span class="brand-sub">University Social Learning &amp; Study Carousel Studio</span>
        </div>
        <div class="nav-meta">
            <span class="live">&#9679; {speed_badge}</span>
            <span>8 SUBJECT TRACKS // 4 TEMPLATES</span>
        </div>
    </div>
    <div class="hero">
        <div>
            <span class="section-label">NIWNOTES // CAMPUS KNOWLEDGE TO SOCIAL CAROUSELS</span>
            <div class="hero-title">Turn university lectures into <span class="outline">viral notes.</span></div>
        </div>
        <p class="hero-sub">Select your university subject track, discover trending topics or type your lecture concept, pick a note template, and export a 5-slide teaching post.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2-PANE WORKSPACE
# =====================================================================
left_pane, right_pane = st.columns([1.08, 2.22], gap="medium")

with left_pane:
    with st.container(border=True):
        st.markdown(
            """
            <div>
                <span class="section-label">01 // UNIVERSITY SUBJECT &amp; TOPIC</span>
                <div class="panel-heading">Campus Track &amp; Discovery</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        subject_list = list(UNIVERSITY_SUBJECTS.keys())
        selected_subject = st.selectbox(
            "Select Your University Subject Category",
            options=subject_list,
            index=0,
        )

        input_mode = st.selectbox(
            "Topic Selection Mode",
            options=[
                "Manual Lecture / Exam Topic Entry",
                "Scan Trending Topics for this Subject",
            ],
            index=0,
        )

        if input_mode == "Scan Trending Topics for this Subject":
            if st.button(
                f"Scan Trending {selected_subject.split('&')[0].strip()} Topics",
                use_container_width=True,
            ):
                if not default_api_key:
                    st.error("Please enter your Gemini API Key below first.")
                else:
                    with st.spinner(
                        f"Scanning live feeds for {selected_subject}..."
                    ):
                        st.session_state.viral_topics = cached_discover_topics(
                            default_api_key, selected_subject
                        )

            if st.session_state.viral_topics:
                topic_titles = [t.topic_title for t in st.session_state.viral_topics]
                final_topic = st.selectbox(
                    "Choose a Trending Study Topic", options=topic_titles
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
                    st.caption(f"Why learn this: {matched.why_it_is_viral}")
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
                "Enter Lecture Concept or Technical Topic",
                value=default_examples.get(selected_subject, "What is RAG in AI?"),
            )

        st.markdown("<hr/>", unsafe_allow_html=True)

        st.markdown(
            """
            <div>
                <span class="section-label">02 // VISUAL TEMPLATE &amp; LANGUAGE</span>
                <div class="panel-heading">Note Style &amp; Branding</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        template_keys = list(NOTE_TEMPLATES.keys())
        selected_template = st.selectbox(
            "Choose Handwritten Note Template",
            options=template_keys,
            format_func=lambda k: f"{NOTE_TEMPLATES[k]['name']} ({NOTE_TEMPLATES[k]['badge']})",
            index=0,
        )

        t_meta = NOTE_TEMPLATES[selected_template]
        st.markdown(
            f"""
            <div class="template-preview-bar">
                <span>STYLE: {t_meta['name'].upper()}</span>
                <div class="swatch-group">
                    <span class="swatch-dot" style="background:{t_meta['paper_bg']};"></span>
                    <span class="swatch-dot" style="background:{t_meta['ink_blue']};"></span>
                    <span class="swatch-dot" style="background:{t_meta['ink_red']};"></span>
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
            author_handle = st.text_input("Creator Handle", value="@NIWNOTES")

        if not default_api_key:
            api_key_input = st.text_input("Gemini API Key", type="password")
        else:
            api_key_input = default_api_key

        generate_btn = st.button(
            "Generate 5-Page NIWNOTES Post",
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
                    "Running Parallel NIWNOTES Pipeline...", expanded=True
                ) as status:
                    st.write(
                        f"1/2 Synthesizing 5-page {selected_subject} curriculum..."
                    )
                    guide = generate_5_page_study_guide(
                        topic=final_topic,
                        language=selected_language,
                        api_key=api_key_input,
                        subject_category=selected_subject,
                    )
                    st.write(
                        f"2/2 Parallel rendering 5 slides ({t_meta['name']})..."
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
                        label=f"Completed in {elapsed:.1f}s!", state="complete"
                    )
                st.rerun()

# =====================================================================
# RIGHT PANE: LIVE CAROUSEL CANVAS & EXPORT
# =====================================================================
with right_pane:
    with st.container(border=True):
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

            top_l, top_r = st.columns([2.1, 1.0], vertical_alignment="center")
            with top_l:
                st.markdown(
                    f"""
                    <div>
                        <span class="section-label">NIWNOTES WORKSPACE // 5-SLIDE SOCIAL POST</span>
                        <div class="workspace-title">{topic_title}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with top_r:
                st.download_button(
                    label="Download All 5 Slides (.ZIP)",
                    data=zip_buffer,
                    file_name="niwnotes_study_carousel.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                )

            tab_grid, tab_inspect, tab_copy = st.tabs(
                [
                    "5-Slide Carousel Grid",
                    "Full-Size Slide Inspector",
                    "Social Media Caption",
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
                    "Select Slide to Inspect in High Resolution",
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
                    '<span class="section-label">READY-TO-POST LINKEDIN &amp; FACEBOOK CAPTION (CLICK COPY ICON)</span>',
                    unsafe_allow_html=True,
                )
                st.code(caption_text, language="markdown")
        else:
            st.markdown(
                """
                <div style="padding: 4.5rem 1.5rem; text-align: center;">
                    <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:3.2rem;
                                color:transparent;-webkit-text-stroke:1.5px rgba(0,255,136,0.55);margin-bottom:1rem;">
                        NIWNOTES
                    </div>
                    <div class="section-label" style="margin-bottom:0.5rem;">NO STUDY CAROUSEL LOADED</div>
                    <div style="font-size: 0.9rem; color: rgba(214,255,232,0.65); max-width: 440px; margin: 0 auto;">
                        Select your university subject track and template on the left panel, then click <b style="color:#00FF88;">Generate 5-Page NIWNOTES Post</b>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
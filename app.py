import io
import os
import zipfile
from dotenv import load_dotenv
from note_generator import (
    generate_5_page_study_guide,
    get_working_models,
    render_all_pages,
)
import streamlit as st
from trend_agent import discover_viral_topics

load_dotenv()

# =====================================================================
# PAGE CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="AI/ML Sketchnote Studio | Autonomous Content Engine",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# REUSABLE VISUAL DESIGN SYSTEM (CSS INJECTION)
# =====================================================================
DESIGN_SYSTEM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

:root {
    --bg-obsidian: #050811;
    --bg-surface: #0B1120;
    --bg-glass: rgba(15, 23, 42, 0.62);
    --bg-glass-hover: rgba(22, 33, 58, 0.78);
    --accent-cyan: #0EA5E9;
    --accent-cyan-bright: #00E5FF;
    --accent-blue: #2563EB;
    --accent-emerald: #10B981;
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --border-hairline: rgba(255, 255, 255, 0.08);
    --border-glow: rgba(14, 165, 233, 0.45);
    --shadow-card: 0 20px 40px -15px rgba(0, 0, 0, 0.75);
    --shadow-glow: 0 0 28px -4px rgba(14, 165, 233, 0.45);
    --radius-lg: 16px;
    --radius-md: 12px;
    --radius-pill: 9999px;
}

/* Global App Background & Architectural Grid */
.stApp {
    background-color: var(--bg-obsidian) !important;
    background-image: 
        radial-gradient(circle at 50% -10%, rgba(14, 165, 233, 0.18) 0%, rgba(37, 99, 235, 0.06) 35%, transparent 70%),
        linear-gradient(to right, rgba(255, 255, 255, 0.025) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.025) 1px, transparent 1px) !important;
    background-size: 100% 100%, 48px 48px, 48px 48px !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
}

/* Hide default Streamlit chrome clutter */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {
    background: rgba(5, 8, 17, 0.75) !important;
    backdrop-filter: blur(12px) !important;
    border-bottom: 1px solid var(--border-hairline) !important;
}

/* Main Container Spacing */
.block-container {
    max-width: 1320px !important;
    padding-top: 2.5rem !important;
    padding-bottom: 4rem !important;
}

/* Typography Hierarchy */
h1, h2, h3, .display-title {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.03em !important;
    color: var(--text-primary) !important;
}

/* Glassmorphic Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(11, 17, 32, 0.92) 0%, rgba(5, 8, 17, 0.96) 100%) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid var(--border-hairline) !important;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 2rem !important;
}

/* Custom Navigation & Hero Header */
.nav-pill-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.25rem;
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-pill);
    margin-bottom: 2.2rem;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.6);
}

.brand-cluster {
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: var(--text-primary);
}

.brand-orb {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-cyan-bright), var(--accent-blue));
    box-shadow: 0 0 12px var(--accent-cyan-bright);
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 14px;
    border-radius: var(--radius-pill);
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34D399;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: var(--accent-emerald);
    box-shadow: 0 0 8px var(--accent-emerald);
}

.hero-card {
    position: relative;
    padding: 2.6rem 2.8rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.75) 0%, rgba(11, 17, 32, 0.45) 100%);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-hairline);
    box-shadow: var(--shadow-card), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    margin-bottom: 2rem;
    overflow: hidden;
}

.hero-card::before {
    content: "";
    position: absolute;
    top: -50%;
    right: -10%;
    width: 420px;
    height: 420px;
    background: radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, transparent 70%);
    pointer-events: none;
}

.hero-eyebrow {
    display: inline-block;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--accent-cyan-bright);
    background: rgba(14, 165, 233, 0.1);
    border: 1px solid rgba(14, 165, 233, 0.25);
    padding: 4px 12px;
    border-radius: var(--radius-pill);
    margin-bottom: 1rem;
}

.hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1.15;
    margin: 0 0 0.75rem 0;
    background: linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 65%, #38BDF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: var(--text-secondary);
    font-size: 1.02rem;
    line-height: 1.6;
    max-width: 780px;
    margin: 0;
}

/* Glass Surface Cards & Metric Tiles */
.glass-panel {
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-lg);
    padding: 1.5rem 1.75rem;
    box-shadow: var(--shadow-card);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    margin-bottom: 1.25rem;
}

.glass-panel:hover {
    border-color: rgba(14, 165, 233, 0.28);
    background: var(--bg-glass-hover);
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-top: 1.6rem;
}

.metric-tile {
    background: rgba(5, 8, 17, 0.55);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-md);
    padding: 0.9rem 1.2rem;
    display: flex;
    flex-direction: column;
}

.metric-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 4px;
}

.metric-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
}

/* Input Fields & Form Controls */
.stTextInput > div > div > input {
    background-color: rgba(11, 17, 32, 0.85) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.18) !important;
    background-color: rgba(15, 23, 42, 0.95) !important;
}

/* Radio Buttons */
.stRadio > div {
    background: rgba(11, 17, 32, 0.65);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-md);
    padding: 0.6rem 0.9rem;
}

/* Primary & Secondary Buttons */
.stButton > button, .stDownloadButton > button {
    border-radius: var(--radius-md) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.01em !important;
    padding: 0.68rem 1.4rem !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid var(--border-hairline) !important;
    background: rgba(15, 23, 42, 0.85) !important;
    color: var(--text-primary) !important;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: var(--border-glow) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px -6px rgba(14, 165, 233, 0.35) !important;
    color: #FFFFFF !important;
}

/* Primary Action Button (Glowing Cyan-Blue Gradient) */
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-blue) 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    box-shadow: var(--shadow-glow), inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
    color: #FFFFFF !important;
}

.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--accent-cyan-bright) 0%, var(--accent-cyan) 100%) !important;
    box-shadow: 0 0 35px -2px rgba(0, 229, 255, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
    transform: translateY(-2px) !important;
}

/* Image Cards */
[data-testid="stImage"] img {
    border-radius: 12px !important;
    border: 1px solid var(--border-hairline) !important;
    box-shadow: 0 14px 30px -10px rgba(0, 0, 0, 0.7) !important;
    transition: transform 0.25s ease, border-color 0.25s ease !important;
}

[data-testid="stImage"] img:hover {
    transform: translateY(-4px) scale(1.01) !important;
    border-color: var(--border-glow) !important;
}

/* Code Block (Caption Box) */
.stCodeBlock, pre {
    background: rgba(11, 17, 32, 0.9) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: var(--radius-md) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Section Dividers */
hr {
    border-color: var(--border-hairline) !important;
    margin: 2rem 0 !important;
}

@media (max-width: 768px) {
    .hero-title { font-size: 1.85rem; }
    .metric-grid { grid-template-columns: 1fr; }
    .hero-card { padding: 1.75rem; }
}
</style>
"""

st.markdown(DESIGN_SYSTEM_CSS, unsafe_allow_html=True)

# =====================================================================
# SESSION STATE INITIALIZATION
# =====================================================================
if "viral_topics" not in st.session_state:
    st.session_state.viral_topics = []
if "generated_guide" not in st.session_state:
    st.session_state.generated_guide = None
if "image_paths" not in st.session_state:
    st.session_state.image_paths = []

# Resolve API Key
default_api_key = os.getenv("GEMINI_API_KEY", "")
if not default_api_key:
    try:
        default_api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        default_api_key = ""

# =====================================================================
# SIDEBAR CONTROL PANEL
# =====================================================================
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:0.5rem;">
            <div class="brand-orb"></div>
            <span style="font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.15rem; letter-spacing:-0.02em;">
                SKETCHNOTE AI
            </span>
        </div>
        <p style="color:#94A3B8; font-size:0.84rem; margin-bottom:1.5rem;">
            Autonomous Multi-Agent Content Studio
        </p>
        """,
        unsafe_allow_html=True,
    )

    author_handle = st.text_input(
        "✍️ Creator Handle / Signature",
        value="@YourName",
        help="Rendered on the bottom footer of every handwritten note page.",
    )

    lang_label = st.radio(
        "🌐 Output Language Mode",
        options=[
            "Sinhala + English Tech Terms",
            "100% English (Global)",
        ],
        index=0,
    )
    selected_language = (
        "Sinhala_Mix" if "Sinhala" in lang_label else "English"
    )

    if not default_api_key:
        api_key_input = st.text_input(
            "🔑 Gemini API Key",
            type="password",
            help="Enter your Google AI Studio API Key",
        )
    else:
        api_key_input = default_api_key
        st.markdown(
            """
            <div style="padding:10px 14px; border-radius:10px; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25); color:#34D399; font-size:0.82rem; margin-top:8px;">
                🔒 <b>Gemini API Connected</b> · Encrypted Session
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.8rem; text-transform:uppercase; letter-spacing:0.08em; color:#64748B; font-weight:600;'>Live Intelligence Feed</p>",
        unsafe_allow_html=True,
    )

    if st.button(
        "⚡ Scan Live Viral AI Topics", use_container_width=True
    ):
        if not api_key_input:
            st.error("Please provide a Gemini API Key first.")
        else:
            os.environ["GEMINI_API_KEY"] = api_key_input
            with st.spinner(
                "Scanning HuggingFace Daily Papers & HackerNews..."
            ):
                models = get_working_models(api_key_input)
                st.session_state.viral_topics = discover_viral_topics(models)

# =====================================================================
# TOP BAR & HERO SECTION
# =====================================================================
st.markdown(
    """
    <div class="nav-pill-bar">
        <div class="brand-cluster">
            <div class="brand-orb"></div>
            <span>AI/ML HANDWRITTEN NOTE ENGINE</span>
        </div>
        <div class="status-pill">
            <span class="pulse-dot"></span>
            <span>MULTI-AGENT SYSTEM ONLINE</span>
        </div>
    </div>

    <div class="hero-card">
        <div class="hero-eyebrow">AUTONOMOUS EDUCATIONAL PIPELINE</div>
        <h1 class="hero-title">Transform Complex AI/ML Concepts Into Viral Handwritten Carousels.</h1>
        <p class="hero-subtitle">
            Powered by real-time trend discovery, strict Pydantic schema validation, and a zero-drift SVG sketchnote rendering engine designed for high-engagement LinkedIn & Facebook carousels.
        </p>
        <div class="metric-grid">
            <div class="metric-tile">
                <span class="metric-label">Trend Sources</span>
                <span class="metric-value">HuggingFace & HackerNews</span>
            </div>
            <div class="metric-tile">
                <span class="metric-label">Output Format</span>
                <span class="metric-value">5-Page 1000×1250px PNG</span>
            </div>
            <div class="metric-tile">
                <span class="metric-label">Language Engine</span>
                <span class="metric-value">Sinhala Mix & English</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# TOPIC SELECTION & EXECUTION PANEL
# =====================================================================
st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
st.markdown(
    "<h3 style='margin-top:0; font-size:1.25rem;'>🎯 Configure Study Carousel Topic</h3>",
    unsafe_allow_html=True,
)

if st.session_state.viral_topics:
    topic_options = [
        f"{t.topic_title} — ({t.why_viral})"
        for t in st.session_state.viral_topics
    ] + ["✍️ Custom Topic (Enter manually below)"]
    chosen_option = st.radio(
        "🔥 Select a Live Trending Topic:", topic_options
    )

    if chosen_option == "✍️ Custom Topic (Enter manually below)":
        final_topic = st.text_input(
            "💡 Enter Custom AI/ML Topic",
            value="What is RAG (Retrieval-Augmented Generation) in AI?",
        )
    else:
        final_topic = chosen_option.split(" — (")[0]
else:
    final_topic = st.text_input(
        "💡 Enter Target AI/ML Topic (or click 'Scan Live Viral AI Topics' in the sidebar)",
        value="What is RAG (Retrieval-Augmented Generation) in AI?",
    )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

generate_btn = st.button(
    "🚀 Generate 5-Page Handwritten Carousel & Viral Copy",
    type="primary",
    use_container_width=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# =====================================================================
# PIPELINE EXECUTION
# =====================================================================
if generate_btn:
    if not api_key_input:
        st.error(
            "❌ Gemini API Key not found. Please add it to your `.env` file or sidebar."
        )
    elif not final_topic.strip():
        st.warning("⚠️ Please enter a valid AI/ML topic.")
    else:
        os.environ["GEMINI_API_KEY"] = api_key_input
        safe_folder = "".join(
            c if c.isalnum() else "_" for c in final_topic
        )[:35].strip("_")
        out_dir = os.path.join("output", safe_folder)

        with st.status(
            f"⚡ Executing Multi-Agent Workflow for: '{final_topic}'...",
            expanded=True,
        ) as status:
            st.write(
                "🧠 **Professor Agent:** Synthesizing 5-page curriculum, visual flowcharts & viral hook..."
            )
            guide = generate_5_page_study_guide(
                topic=final_topic,
                language=selected_language,
                api_key=api_key_input,
            )

            st.write(
                "🎨 **Sketchnote Renderer:** Drawing 5 high-resolution GoodNotes pages via headless Chromium..."
            )
            img_paths = render_all_pages(
                guide=guide, author=author_handle, output_dir=out_dir
            )

            caption_file = os.path.join(out_dir, "caption.txt")
            with open(caption_file, "w", encoding="utf-8") as f:
                f.write(guide.social_caption)

            st.session_state.generated_guide = guide
            st.session_state.image_paths = img_paths
            status.update(
                label="✅ 5-Page Handwritten Carousel & Caption Generated Successfully!",
                state="complete",
                expanded=False,
            )

# =====================================================================
# OUTPUT GALLERY & BUNDLE DOWNLOAD
# =====================================================================
if st.session_state.generated_guide and st.session_state.image_paths:
    guide = st.session_state.generated_guide
    img_paths = st.session_state.image_paths

    # Build ZIP Archive in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in img_paths:
            if os.path.exists(p):
                zf.write(p, arcname=os.path.basename(p))
        zf.writestr("caption.txt", guide.social_caption)
    zip_buffer.seek(0)

    st.markdown("<hr/>", unsafe_allow_html=True)

    header_left, header_right = st.columns([2.6, 1.4])
    with header_left:
        st.markdown(
            f"<h2 style='margin:0; font-size:1.6rem;'>📚 Generated Carousel: {guide.topic_name}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#94A3B8; font-size:0.9rem; margin-top:4px;'>High-resolution 1000×1250px handwritten note series ready for LinkedIn & Facebook.</p>",
            unsafe_allow_html=True,
        )
    with header_right:
        st.download_button(
            label="📦 Download Complete 5-Page Bundle (.ZIP)",
            data=zip_buffer,
            file_name="ai_sketchnote_carousel.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    cols = st.columns(5)
    for idx, img_path in enumerate(img_paths):
        with cols[idx]:
            if os.path.exists(img_path):
                st.image(
                    img_path,
                    caption=f"Slide 0{idx+1} / 05",
                    use_container_width=True,
                )
                with open(img_path, "rb") as img_file:
                    st.download_button(
                        label=f"⬇️ Save Page 0{idx+1}",
                        data=img_file,
                        file_name=f"note_page_{idx+1}.png",
                        mime="image/png",
                        key=f"dl_page_{idx+1}",
                        use_container_width=True,
                    )

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='margin-bottom:0.4rem; font-size:1.3rem;'>📝 Viral Social Media Copy (LinkedIn / Facebook)</h3>"
        "<p style='color:#94A3B8; font-size:0.88rem; margin-bottom:0.8rem;'>Click the copy icon in the top-right corner of the box below:</p>",
        unsafe_allow_html=True,
    )
    st.code(guide.social_caption, language="markdown")
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

st.set_page_config(
    page_title="AI/ML Handwritten Note Agent",
    page_icon="✍️",
    layout="wide",
)

# Initialize Session State so results persist when clicking download buttons
if "viral_topics" not in st.session_state:
    st.session_state.viral_topics = []
if "generated_guide" not in st.session_state:
    st.session_state.generated_guide = None
if "image_paths" not in st.session_state:
    st.session_state.image_paths = []

# Resolve API Key from .env, Streamlit Secrets, or Sidebar Input
default_api_key = os.getenv("GEMINI_API_KEY", "")
if not default_api_key:
    try:
        default_api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        default_api_key = ""

# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.title("⚙️ Agent Settings")
    st.markdown(
        "Configure your autonomous AI/ML Study Note & Social Post Generator."
    )

    author_handle = st.text_input(
        "✍️ Author Name / Handle",
        value="@YourName",
        help="Appears at the bottom right of every handwritten page.",
    )

    lang_label = st.radio(
        "🌐 Note Language Mode",
        options=[
            "Sinhala + English Technical Terms",
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
        st.success("🔒 Gemini API Key loaded securely")

    st.divider()
    st.markdown("### 🔍 Live Trend Agent")
    if st.button(
        "🔥 Discover Today's Viral AI Topics", use_container_width=True
    ):
        if not api_key_input:
            st.error("Please provide a Gemini API Key first.")
        else:
            os.environ["GEMINI_API_KEY"] = api_key_input
            with st.spinner(
                "Scanning HuggingFace Papers & HackerNews for live AI trends..."
            ):
                models = get_working_models(api_key_input)
                st.session_state.viral_topics = discover_viral_topics(models)

# ==========================================
# MAIN DASHBOARD AREA
# ==========================================
st.title("✍️ AI/ML Handwritten Sketchnote & Viral Content Agent")
st.caption(
    "Autonomous Multi-Agent System: Live Trend Discovery ➔ 5-Page GoodNotes Study Carousel ➔ Viral LinkedIn/Facebook Copy"
)

col_topic, col_action = st.columns([3, 1])

with col_topic:
    if st.session_state.viral_topics:
        st.subheader("🔥 Select a Trending Topic or Type Your Own")
        topic_options = [
            f"{t.topic_title} — ({t.why_viral})"
            for t in st.session_state.viral_topics
        ] + ["✍️ Custom Topic (Type below)"]
        chosen_option = st.radio("Trending AI/ML Topics Today:", topic_options)

        if chosen_option == "✍️ Custom Topic (Type below)":
            final_topic = st.text_input(
                "💡 Enter your custom AI/ML Topic:",
                value="What is RAG (Retrieval-Augmented Generation) in AI?",
            )
        else:
            final_topic = chosen_option.split(" — (")[0]
    else:
        final_topic = st.text_input(
            "💡 Enter an AI/ML Topic (or click 'Discover Today's Viral AI Topics' in the sidebar):",
            value="What is RAG (Retrieval-Augmented Generation) in AI?",
        )

generate_btn = st.button(
    "🚀 Generate 5-Page Handwritten Note Series",
    type="primary",
    use_container_width=True,
)

if generate_btn:
    if not api_key_input:
        st.error("❌ Please configure your GEMINI_API_KEY in `.env` or the sidebar.")
    elif not final_topic.strip():
        st.warning("⚠️ Please enter a valid AI/ML topic.")
    else:
        os.environ["GEMINI_API_KEY"] = api_key_input
        safe_folder = "".join(
            c if c.isalnum() else "_" for c in final_topic
        )[:35].strip("_")
        out_dir = os.path.join("output", safe_folder)

        with st.status(
            f"🤖 Multi-Agent Pipeline running for: '{final_topic}'...",
            expanded=True,
        ) as status:
            st.write(
                "🧠 **Professor Agent:** Structuring 5-page curriculum & viral social copy..."
            )
            guide = generate_5_page_study_guide(
                topic=final_topic,
                language=selected_language,
                api_key=api_key_input,
            )

            st.write(
                "🎨 **Designer Agent:** Rendering 5 high-res handwritten sketchnote pages..."
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
                label="✅ 5-Page Note Series & Viral Caption Ready!",
                state="complete",
                expanded=False,
            )

# ==========================================
# DISPLAY GENERATED OUTPUTS
# ==========================================
if st.session_state.generated_guide and st.session_state.image_paths:
    guide = st.session_state.generated_guide
    img_paths = st.session_state.image_paths

    st.divider()

    # Create in-memory ZIP archive of all 5 pages + caption.txt
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in img_paths:
            if os.path.exists(p):
                zf.write(p, arcname=os.path.basename(p))
        zf.writestr("caption.txt", guide.social_caption)
    zip_buffer.seek(0)

    head_col1, head_col2 = st.columns([2.5, 1.5])
    with head_col1:
        st.subheader(f"📚 5-Page Study Carousel: {guide.topic_name}")
    with head_col2:
        st.download_button(
            label="📦 Download All 5 Pages + Caption (.ZIP)",
            data=zip_buffer,
            file_name="handwritten_notes_bundle.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )

    # Display all 5 pages in clean columns
    cols = st.columns(5)
    for idx, img_path in enumerate(img_paths):
        with cols[idx]:
            if os.path.exists(img_path):
                st.image(
                    img_path,
                    caption=f"Page 0{idx+1}/05",
                    use_container_width=True,
                )
                with open(img_path, "rb") as img_file:
                    st.download_button(
                        label=f"⬇️ Page 0{idx+1}",
                        data=img_file,
                        file_name=f"note_page_{idx+1}.png",
                        mime="image/png",
                        key=f"dl_page_{idx+1}",
                        use_container_width=True,
                    )

    st.divider()
    st.subheader("📝 Viral Facebook / LinkedIn Caption (Click top-right icon to copy)")
    st.code(guide.social_caption, language="markdown")
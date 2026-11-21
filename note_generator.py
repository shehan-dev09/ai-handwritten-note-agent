from datetime import datetime
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from html2image import Html2Image
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

client = genai.Client(api_key=API_KEY)


# =====================================================================
# 1. STRICT PYDANTIC SCHEMAS
# =====================================================================
class DiagramStep(BaseModel):
    step_num: str = Field(description="Step number like 1, 2, 3, 4")
    title: str = Field(
        description="Short English technical term (max 2-3 words)"
    )
    detail: str = Field(description="Very short 3-5 word explanation")


class NotePage(BaseModel):
    page_number: int = Field(description="Page number from 1 to 5")
    page_tag: str = Field(
        description="Short English section tag, e.g., 'Part 1: Fundamentals'"
    )
    page_title: str = Field(
        description="Catchy title for this specific page (max 6 words)"
    )
    summary_text: str = Field(
        description="2-3 clear sentences introducing this page's concept. Wrap 1-2 short key terms (max 2 words each) in <mark> tags and 1 short term in <u> tags."
    )
    diagram_heading: str = Field(
        description="Heading for the visual diagram/flowchart on this page"
    )
    diagram_steps: list[DiagramStep] = Field(
        description="Exactly 4 sequential or related nodes for the visual diagram"
    )
    key_points_heading: str = Field(
        description="Subheading for the bullet points section"
    )
    key_points: list[str] = Field(
        description="Exactly 4 detailed educational bullet points. Start each with <b>English Term:</b> followed by explanation. Use <mark> or <u> tags only on short 1-2 word keywords."
    )
    box_title: str = Field(
        description="Title for the bottom green box (e.g., Real-World Example, Technical Concept, or Use Case)"
    )
    box_content: str = Field(
        description="2-3 practical sentences explaining the example or technical detail."
    )
    sticky_title: str = Field(
        description="Short title for the yellow sticky note (e.g., 'Pro Tip', 'Architecture Tip', 'Key Takeaway') WITHOUT emojis"
    )
    sticky_content: str = Field(
        description="2 short, high-value sentences for the yellow sticky note in the requested language."
    )


class StudyCarouselResponse(BaseModel):
    topic_name: str
    pages: list[NotePage] = Field(
        description="List of exactly 5 comprehensive study note pages"
    )
    social_caption: str = Field(
        description="Viral Facebook/LinkedIn caption written in a natural human tone with a strong hook, page-by-page breakdown summary, engaging question, and 5 hashtags."
    )


# =====================================================================
# 2. MODEL SELECTION & CONTENT GENERATION
# =====================================================================
def get_working_models() -> list:
    """Fetches active 3.x text models and prioritizes standard Flash models."""
    excluded_keywords = [
        "2.5",
        "2.0",
        "1.5",
        "1.0",
        "image",
        "vision",
        "embedding",
        "tts",
        "audio",
        "aqa",
        "robotics",
        "banana",
    ]
    try:
        all_models = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if (
                "generateContent" in m.supported_actions
                and "gemini" in name.lower()
            ):
                if not any(
                    bad_word in name.lower() for bad_word in excluded_keywords
                ):
                    all_models.append(name)

        all_models.sort(
            key=lambda x: (
                0
                if ("flash" in x and "lite" not in x)
                else (1 if "lite" in x else 2)
            )
        )
        return all_models if all_models else ["gemini-3.5-flash"]
    except Exception:
        return ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]


def generate_5_page_study_guide(
    topic: str, language: str = "Sinhala_Mix"
) -> StudyCarouselResponse:
    """Generates a complete 5-page study note series."""
    lang_instruction = (
        "Write all explanations (including sticky notes and examples) in simple, natural conversational Sinhala (Unicode script), but KEEP all technical AI/ML terms in English."
        if language == "Sinhala_Mix"
        else "Write completely in simple, clear, engaging English."
    )

    prompt = f"""
    You are a top 1% AI/ML Educator and Viral LinkedIn/Facebook Content Creator.
    Topic: {topic}
    Language Instruction: {lang_instruction}

    Create a complete, 100% technically accurate **5-Page Handwritten Study Note Series** so a reader can master this topic from scratch:
    - Page 1: Core Concept, Simple Analogy & What Problem It Solves
    - Page 2: Step-by-Step Architecture & Internal Workflow
    - Page 3: Key Technical Components & Deep Dive Mechanics
    - Page 4: Real-World Industry Use Cases, Tools & Implementation
    - Page 5: Limitations, Best Practices, Pitfalls & Summary Cheat-Sheet

    STRICT Formatting rules for text fields:
    - DO NOT use any emojis inside the note pages.
    - Use <mark>keyword</mark> for yellow highlighter effect (keep inside <mark> to 1 or 2 words MAX).
    - Use <u>keyword</u> for red-pen underline emphasis (keep inside <u> to 1 or 2 words MAX).
    - Use <b>Term:</b> to bold important starters in bullet points.
    """

    models_to_try = get_working_models()
    print(f"[INFO] Active Gemini models prioritized: {models_to_try[:5]}")

    for model_name in models_to_try:
        for attempt in range(1, 3):
            try:
                print(
                    f"[INFO] Generating 5-Page Study Guide using '{model_name}' (Attempt {attempt}/2)..."
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=StudyCarouselResponse,
                        temperature=0.5,
                    ),
                )
                return StudyCarouselResponse.model_validate_json(response.text)

            except Exception as e:
                err_str = str(e)
                if "503" in err_str:
                    print(
                        f"[WARNING] '{model_name}' server is busy (503). Waiting 3s..."
                    )
                    time.sleep(3)
                else:
                    print(
                        f"[WARNING] '{model_name}' failed ({type(e).__name__}). Switching to next model..."
                    )
                    break

    raise RuntimeError(
        "All Gemini models are currently busy. Please try again in a minute."
    )


# =====================================================================
# 3. ZERO-DRIFT CSS + INLINE SVG SKETCHNOTE ENGINE (100% ALIGNMENT LOCKED)
# =====================================================================
HTML_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Kalam:wght@400;700&family=Noto+Sans+Sinhala:wght@500;600;700&display=swap" rel="stylesheet">
<style>
    * { box-sizing: border-box; }
    body {
        margin: 0;
        padding: 0;
        background-color: #cfc8b8;
        display: flex;
        justify-content: center;
        align-items: center;
        width: 1000px;
        height: 1250px;
    }
    .page {
        width: 940px;
        height: 1190px;
        background-color: #fbf9f2;
        background-image: radial-gradient(#b8c4ce 1.4px, transparent 1.4px);
        background-size: 26px 26px;
        box-shadow: 
            0 15px 35px rgba(0, 0, 0, 0.22),
            inset 0 0 70px rgba(215, 200, 170, 0.3);
        border-radius: 8px;
        position: relative;
        padding: 40px 52px 55px 82px;
        overflow: hidden;
        font-family: 'Kalam', 'Noto Sans Sinhala', 'Nirmala UI', sans-serif;
        font-weight: 500;
        color: #16264c;
        font-size: 18.5px;
        line-height: 34px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .margin-line {
        position: absolute;
        top: 0; bottom: 0; left: 58px;
        width: 2px;
        background-color: rgba(225, 100, 100, 0.45);
        z-index: 1;
    }
    .paper-lighting {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(130deg, rgba(255,255,255,0.25) 0%, rgba(0,0,0,0.01) 55%, rgba(0,0,0,0.07) 100%);
        pointer-events: none;
        z-index: 20;
    }
    .content-wrapper {
        position: relative;
        z-index: 5;
    }
    .doodle-icon {
        width: 22px;
        height: 22px;
        vertical-align: middle;
        margin-right: 7px;
        flex-shrink: 0;
    }
    .top-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-family: 'Caveat', cursive;
        font-size: 24px;
        color: #475569;
    }
    .category-pill {
        background-color: #ffedd5;
        border: 2px solid #c2410c;
        color: #9a3412;
        padding: 1px 14px;
        border-radius: 22px 6px 20px 6px / 6px 20px 6px 22px;
        font-weight: 700;
    }
    .page-badge {
        background-color: #e2e8f0;
        border: 2px solid #334155;
        color: #0f172a;
        padding: 1px 14px;
        border-radius: 6px 18px 6px 18px / 18px 6px 18px 6px;
        font-weight: 700;
    }
    .title-row {
        margin-bottom: 18px;
    }
    /* Main Heading with Locked Hand-Drawn Double Red Underline */
    h1 {
        font-family: 'Kalam', 'Noto Sans Sinhala', 'Nirmala UI', sans-serif;
        font-weight: 700;
        font-size: 30px;
        color: #b91c1c;
        margin: 0;
        line-height: 40px;
        display: inline-block;
        position: relative;
        background: linear-gradient(100deg, rgba(254, 240, 138, 0) 1%, rgba(254, 240, 138, 0.85) 4%, rgba(253, 224, 71, 0.75) 95%, rgba(254, 240, 138, 0) 100%);
        padding: 0 8px 6px 8px;
    }
    h1::after {
        content: "";
        position: absolute;
        left: 0;
        right: -6px;
        bottom: -3px;
        height: 10px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 12' preserveAspectRatio='none'%3E%3Cpath d='M2 4 Q 150 1, 298 5' stroke='%23b91c1c' stroke-width='2.6' fill='none' stroke-linecap='round'/%3E%3Cpath d='M8 9 Q 150 7, 292 10' stroke='%23b91c1c' stroke-width='1.8' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
        background-size: 100% 100%;
    }
    .intro-box {
        margin-bottom: 18px;
        font-size: 19px;
        line-height: 35px;
    }
    /* Yellow Highlighter */
    mark {
        display: inline;
        background: linear-gradient(104deg, rgba(253, 224, 71, 0) 1%, rgba(253, 224, 71, 0.9) 4%, rgba(250, 204, 21, 0.85) 95%, rgba(253, 224, 71, 0) 100%);
        padding: 1px 6px;
        border-radius: 6px 2px 8px 3px;
        color: #0f172a;
        font-weight: 600;
        box-decoration-break: clone;
        -webkit-box-decoration-break: clone;
    }
    /* Red Pen Underline Locked Directly to the Word (Can NEVER drift!) */
    u {
        display: inline;
        text-decoration: none;
        color: #b91c1c;
        font-weight: 700;
        padding-bottom: 4px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 8' preserveAspectRatio='none'%3E%3Cpath d='M1 3 Q 60 7, 119 2' stroke='%23b91c1c' stroke-width='2.4' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-size: 100% 7px;
        background-position: 0 100%;
        box-decoration-break: clone;
        -webkit-box-decoration-break: clone;
    }
    /* Diagram Container with Locked Dashed Hand-Drawn Border */
    .diagram-container {
        background-color: rgba(255, 255, 255, 0.82);
        padding: 16px 18px 20px 18px;
        margin: 10px 0 20px 0;
        position: relative;
        border: 2.4px dashed #0f766e;
        border-radius: 16px 245px 14px 235px / 235px 14px 245px 16px;
    }
    .diagram-header {
        font-family: 'Kalam', 'Noto Sans Sinhala', 'Nirmala UI', sans-serif;
        font-size: 19.5px;
        font-weight: 700;
        color: #0f766e;
        margin-bottom: 20px;
        line-height: 26px;
        display: flex;
        align-items: center;
    }
    .flowchart {
        display: flex;
        align-items: stretch;
        justify-content: space-between;
        gap: 2px;
    }
    /* Flowchart Node with Locked Double-Stroke Sketchy Border */
    .flow-node {
        flex: 1;
        background-color: #ffffff;
        padding: 18px 8px 12px 8px;
        text-align: center;
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        border: 2.2px solid #1e3a8a;
        border-radius: 255px 12px 225px 12px / 12px 225px 12px 255px;
        box-shadow: 2px 3px 0px rgba(30, 58, 138, 0.12);
    }
    .flow-node::after {
        content: "";
        position: absolute;
        inset: -2px;
        border: 1.2px solid rgba(30, 58, 138, 0.65);
        border-radius: 12px 225px 12px 255px / 255px 12px 225px 12px;
        transform: rotate(-0.6deg);
        pointer-events: none;
    }
    /* Step Badge sits cleanly ON TOP of the border with a solid mask */
    .step-badge {
        position: absolute;
        top: -14px;
        left: 50%;
        transform: translateX(-50%);
        background: #fef08a;
        border: 2px solid #1e3a8a;
        box-shadow: 0 0 0 3px #ffffff;
        color: #b91c1c;
        font-family: 'Caveat', cursive;
        font-size: 18px;
        font-weight: 700;
        line-height: 18px;
        padding: 2px 10px;
        border-radius: 14px;
        z-index: 10;
    }
    .node-title {
        font-family: 'Kalam', sans-serif;
        font-weight: 700;
        font-size: 16.5px;
        line-height: 21px;
        color: #1e3a8a;
        margin-bottom: 5px;
    }
    .node-desc {
        font-size: 13.5px;
        line-height: 18px;
        color: #334155;
    }
    .flow-arrow {
        width: 30px;
        min-width: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .arrow-svg {
        width: 28px;
        height: 20px;
    }
    /* Subheading with Locked Hand-Drawn Double Red Underline */
    .section-title-wrap {
        margin: 4px 0 12px 0;
    }
    h3 {
        font-family: 'Kalam', 'Noto Sans Sinhala', 'Nirmala UI', sans-serif;
        color: #b91c1c;
        font-size: 21.5px;
        font-weight: 700;
        margin: 0;
        padding-bottom: 5px;
        line-height: 32px;
        display: inline-block;
        position: relative;
    }
    h3::after {
        content: "";
        position: absolute;
        left: 0;
        right: -8px;
        bottom: -2px;
        height: 8px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 250 10' preserveAspectRatio='none'%3E%3Cpath d='M2 3 Q 125 0, 248 4' stroke='%23b91c1c' stroke-width='2.4' fill='none' stroke-linecap='round'/%3E%3Cpath d='M6 8 Q 125 6, 242 8' stroke='%23b91c1c' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
        background-size: 100% 100%;
    }
    ul {
        list-style: none;
        padding: 0;
        margin: 0 0 18px 0;
    }
    li {
        display: flex;
        align-items: flex-start;
        margin-bottom: 9px;
        line-height: 33px;
        font-size: 18px;
    }
    .bullet-svg {
        width: 20px;
        min-width: 20px;
        height: 20px;
        margin-right: 10px;
        margin-top: 7px;
    }
    li b {
        color: #0c4a6e;
        font-weight: 700;
    }
    /* Bottom 2-Column Section */
    .bottom-grid {
        display: grid;
        grid-template-columns: 1.35fr 0.95fr;
        gap: 24px;
        align-items: start;
        margin-top: 6px;
    }
    /* Green Box with Locked Sketchy Double-Border (Can NEVER separate from background!) */
    .example-card {
        background-color: rgba(220, 252, 231, 0.65);
        padding: 14px 18px;
        color: #14532d;
        font-size: 17px;
        line-height: 29px;
        position: relative;
        border: 2.3px solid #15803d;
        border-radius: 235px 14px 215px 14px / 14px 215px 14px 235px;
        box-shadow: 2px 4px 10px rgba(21, 128, 61, 0.08);
    }
    .example-card::after {
        content: "";
        position: absolute;
        inset: -2px;
        border: 1.2px solid rgba(21, 128, 61, 0.65);
        border-radius: 14px 215px 14px 235px / 235px 14px 215px 14px;
        transform: rotate(0.4deg);
        pointer-events: none;
    }
    .example-title {
        font-weight: 700;
        font-size: 18.5px;
        color: #166534;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
    }
    /* Yellow Sticky Note */
    .sticky-note {
        background: linear-gradient(160deg, #fef08a 0%, #fde047 100%);
        padding: 16px 18px 16px 18px;
        box-shadow: 3px 6px 14px rgba(0, 0, 0, 0.14);
        border: 2px solid #ca8a04;
        transform: rotate(-1.4deg);
        position: relative;
        color: #1e293b;
        font-size: 16.5px;
        line-height: 27px;
        border-radius: 6px 220px 28px 6px / 220px 6px 6px 220px;
    }
    .tape {
        position: absolute;
        top: -11px;
        left: 50%;
        transform: translateX(-50%) rotate(1.5deg);
        width: 95px;
        height: 22px;
        background-color: rgba(255, 255, 255, 0.68);
        border: 1px dashed rgba(160, 160, 160, 0.5);
    }
    .sticky-title {
        font-weight: 700;
        color: #9a3412;
        font-size: 18.5px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
    }
    .footer {
        text-align: right;
        font-family: 'Caveat', cursive;
        font-size: 24px;
        color: #475569;
        margin-top: 8px;
        z-index: 15;
    }
</style>
</head>
<body>
    <div class="page" id="page">
        <div class="margin-line"></div>
        <div class="paper-lighting"></div>

        <div class="content-wrapper">
            <div class="top-meta">
                <span class="category-pill"># __PAGE_TAG__</span>
                <span>Date: __TODAY_DATE__</span>
                <span class="page-badge">Page 0__PAGE_NUM__ / 05</span>
            </div>

            <div class="title-row">
                <h1>__PAGE_TITLE__</h1>
            </div>

            <div class="intro-box">
                __SUMMARY_TEXT__
            </div>

            <div class="diagram-container">
                <div class="diagram-header">
                    <svg class="doodle-icon" viewBox="0 0 24 24" fill="none" stroke="#0f766e" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/>
                    </svg>
                    __DIAGRAM_HEADING__
                </div>
                <div class="flowchart">
                    __DIAGRAM_HTML__
                </div>
            </div>

            <div class="section-title-wrap">
                <h3>__KEY_POINTS_HEADING__</h3>
            </div>
            <ul>
                __BULLETS_HTML__
            </ul>

            <div class="bottom-grid">
                <div class="example-card">
                    <span class="example-title">
                        <svg class="doodle-icon" viewBox="0 0 24 24" fill="none" stroke="#166534" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                        </svg>
                        __BOX_TITLE__
                    </span>
                    __BOX_CONTENT__
                </div>

                <div class="sticky-note">
                    <div class="tape"></div>
                    <span class="sticky-title">
                        <svg class="doodle-icon" viewBox="0 0 24 24" fill="none" stroke="#9a3412" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"/>
                        </svg>
                        __STICKY_TITLE__
                    </span>
                    __STICKY_CONTENT__
                </div>
            </div>
        </div>

        <div class="footer">Notes by __AUTHOR__  |  Swipe ➔ (0__PAGE_NUM__/05)</div>
    </div>
</body>
</html>
"""


def render_all_pages(
    guide: StudyCarouselResponse,
    author: str = "@YourName",
    output_dir: str = "output",
):
    """Renders all 5 pages of the study guide into individual high-res PNG files with font-wait flags."""
    os.makedirs(output_dir, exist_ok=True)
    # Wait 3.5 seconds for Google Web Fonts to fully settle and silence Chrome extension warnings
    hti = Html2Image(
        size=(1000, 1250),
        output_path=output_dir,
        custom_flags=[
            "--virtual-time-budget=3500",
            "--disable-extensions",
            "--log-level=3",
        ],
    )
    today_date = datetime.now().strftime("%b %d, %Y")

    bullet_svg_icon = """
    <svg class="bullet-svg" viewBox="0 0 24 24" fill="none" stroke="#b91c1c" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 12h15M13 6l6 6-6 6"/>
    </svg>
    """

    arrow_svg_icon = """
    <div class="flow-arrow">
        <svg class="arrow-svg" viewBox="0 0 32 20" fill="none" stroke="#b91c1c" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 10 Q 16 6, 29 10"/>
            <path d="M21 4 L 30 10 L 22 16"/>
        </svg>
    </div>
    """

    for page in guide.pages:
        print(
            f"[INFO] Rendering Page 0{page.page_number}/05: '{page.page_title}'..."
        )

        # Build Diagram HTML
        diagram_html = ""
        for i, step in enumerate(page.diagram_steps):
            diagram_html += f"""
            <div class="flow-node">
                <div class="step-badge">#{step.step_num}</div>
                <div class="node-title">{step.title}</div>
                <div class="node-desc">{step.detail}</div>
            </div>
            """
            if i < len(page.diagram_steps) - 1:
                diagram_html += arrow_svg_icon

        # Build Bullets HTML
        bullets_html = "".join(
            [
                f"<li>{bullet_svg_icon}<div>{bp}</div></li>"
                for bp in page.key_points
            ]
        )

        # Populate HTML Template
        page_html = (
            HTML_PAGE_TEMPLATE.replace("__PAGE_NUM__", str(page.page_number))
            .replace("__PAGE_TAG__", page.page_tag)
            .replace("__TODAY_DATE__", today_date)
            .replace("__PAGE_TITLE__", page.page_title)
            .replace("__SUMMARY_TEXT__", page.summary_text)
            .replace("__DIAGRAM_HEADING__", page.diagram_heading)
            .replace("__DIAGRAM_HTML__", diagram_html)
            .replace("__KEY_POINTS_HEADING__", page.key_points_heading)
            .replace("__BULLETS_HTML__", bullets_html)
            .replace("__BOX_TITLE__", page.box_title)
            .replace("__BOX_CONTENT__", page.box_content)
            .replace("__STICKY_TITLE__", page.sticky_title)
            .replace("__STICKY_CONTENT__", page.sticky_content)
            .replace("__AUTHOR__", author)
        )

        filename = f"note_page_{page.page_number}.png"
        hti.screenshot(html_str=page_html, save_as=filename)
        print(f"[SUCCESS] Saved '{output_dir}/{filename}'")


def main():
    TOPIC = "What is RAG (Retrieval-Augmented Generation) in AI?"
    LANGUAGE = "Sinhala_Mix"  # Options: "Sinhala_Mix" or "English"
    AUTHOR_NAME = "Shehan Nadeesha"
    OUTPUT_DIR = "output"

    try:
        study_guide = generate_5_page_study_guide(
            topic=TOPIC, language=LANGUAGE
        )
        render_all_pages(
            guide=study_guide, author=AUTHOR_NAME, output_dir=OUTPUT_DIR
        )

        caption_path = os.path.join(OUTPUT_DIR, "caption.txt")
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write(study_guide.social_caption)
        print(f"\n[SUCCESS] Social media caption saved to '{caption_path}'")

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()
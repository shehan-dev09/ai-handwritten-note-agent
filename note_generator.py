from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from html2image import Html2Image
from pydantic import BaseModel, Field

load_dotenv()

# =====================================================================
# 1. VISUAL TEMPLATES REGISTRY (4 DISTINCT STUDENT NOTE STYLES)
# =====================================================================
NOTE_TEMPLATES = {
    "classic_cream": {
        "name": "Classic Cream Notebook",
        "badge": "Warm Dot-Grid + Yellow Marker",
        "paper_bg": "#FAF7F0",
        "dot_color": "#B8C4CE",
        "grid_css": "background-image: radial-gradient(#B8C4CE 1.4px, transparent 1.4px); background-size: 26px 26px;",
        "margin_line": "rgba(217, 48, 37, 0.32)",
        "ink_main": "#1A2233",
        "ink_title": "#0F172A",
        "ink_blue": "#0B57D0",
        "ink_red": "#D93025",
        "ink_green": "#137333",
        "mark_fill": "rgba(255, 226, 70, 0.78)",
        "box_stroke": "%23D93025",
        " box_fill": "rgba(217, 48, 37, 0.04)",
        "underline_stroke": "%230B57D0",
        "card_bg": "rgba(255, 255, 255, 0.85)",
        "card_border": "#1E293B",
        "step_bg": "#FFFDF7",
        "takeaway_bg": "#FEF9C3",
        "takeaway_border": "#CA8A04",
        "badge_bg": "#1E293B",
        "badge_text": "#FFFFFF",
    },
    "dark_neon": {
        "name": "Obsidian Neon Darkboard",
        "badge": "iPad Dark Slate + Emerald Glow",
        "paper_bg": "#0B101B",
        "dot_color": "#1E293B",
        "grid_css": "background-image: radial-gradient(#26334D 1.4px, transparent 1.4px); background-size: 26px 26px;",
        "margin_line": "rgba(0, 255, 136, 0.22)",
        "ink_main": "#E2E8F0",
        "ink_title": "#FFFFFF",
        "ink_blue": "#38BDF8",
        "ink_red": "#00FF88",
        "ink_green": "#A3E635",
        "mark_fill": "rgba(0, 255, 136, 0.25)",
        "box_stroke": "%2338BDF8",
        "box_fill": "rgba(56, 189, 248, 0.08)",
        "underline_stroke": "%2300FF88",
        "card_bg": "rgba(15, 23, 42, 0.88)",
        "card_border": "#334155",
        "step_bg": "#111C2D",
        "takeaway_bg": "rgba(0, 255, 136, 0.10)",
        "takeaway_border": "#00FF88",
        "badge_bg": "#00FF88",
        "badge_text": "#03120A",
    },
    "blueprint_grid": {
        "name": "Engineering Blueprint Grid",
        "badge": "Technical Graph + Navy Ink",
        "paper_bg": "#F0F6FC",
        "dot_color": "#BFD4EA",
        "grid_css": (
            "background-image: linear-gradient(rgba(14, 116, 144, 0.10) 1px, transparent 1px), "
            "linear-gradient(90deg, rgba(14, 116, 144, 0.10) 1px, transparent 1px); "
            "background-size: 26px 26px;"
        ),
        "margin_line": "rgba(2, 132, 199, 0.30)",
        "ink_main": "#0F172A",
        "ink_title": "#0369A1",
        "ink_blue": "#0284C7",
        "ink_red": "#EA580C",
        "ink_green": "#0D9488",
        "mark_fill": "rgba(125, 211, 252, 0.55)",
        "box_stroke": "%23EA580C",
        "box_fill": "rgba(234, 88, 12, 0.05)",
        "underline_stroke": "%230284C7",
        "card_bg": "rgba(255, 255, 255, 0.90)",
        "card_border": "#0369A1",
        "step_bg": "#FFFFFF",
        "takeaway_bg": "#E0F2FE",
        "takeaway_border": "#0284C7",
        "badge_bg": "#0369A1",
        "badge_text": "#FFFFFF",
    },
    "cornell_academic": {
        "name": "Cornell Exam Revision Sheet",
        "badge": "Academic Ivory + Violet Accents",
        "paper_bg": "#FDFCF7",
        "dot_color": "#D6D3C9",
        "grid_css": "background-image: linear-gradient(to bottom, transparent 29px, rgba(148, 163, 184, 0.22) 30px); background-size: 100% 30px;",
        "margin_line": "rgba(124, 58, 237, 0.30)",
        "ink_main": "#1E1B4B",
        "ink_title": "#311042",
        "ink_blue": "#6D28D9",
        "ink_red": "#BE123C",
        "ink_green": "#047857",
        "mark_fill": "rgba(233, 213, 255, 0.85)",
        "box_stroke": "%23BE123C",
        "box_fill": "rgba(190, 18, 60, 0.04)",
        "underline_stroke": "%236D28D9",
        "card_bg": "rgba(255, 255, 255, 0.92)",
        "card_border": "#4C1D95",
        "step_bg": "#FAF5FF",
        "takeaway_bg": "#F3E8FF",
        "takeaway_border": "#7C3AED",
        "badge_bg": "#4C1D95",
        "badge_text": "#FFFFFF",
    },
}


# =====================================================================
# 2. PYDANTIC SCHEMAS FOR STRICT 5-PAGE STUDY GUIDE
# =====================================================================
class DiagramStep(BaseModel):
    step_num: str = Field(description="Step number e.g. '01', '02', '03', '04'")
    title: str = Field(description="Short 2-3 word title in English")
    detail: str = Field(description="Brief 4-6 word explanation")


class NotePage(BaseModel):
    page_number: int = Field(description="Page number from 1 to 5")
    page_title: str = Field(description="Clear English heading for this slide")
    subtitle_tag: str = Field(
        description="Short category badge e.g. 'CONCEPT 01 // MENTAL MODEL'"
    )
    intro_definition: str = Field(
        description="2-3 sentences explaining the core idea clearly. Wrap 1-2 key terms in <mark>...</mark> or <b>...</b>."
    )
    bullet_points: list[str] = Field(
        description="Exactly 3 detailed, high-value study bullet points. Wrap key phrases in <mark>, <b>, or <u>.",
        min_length=3,
        max_length=3,
    )
    diagram_title: str = Field(description="Title for the 4-step visual architecture flow")
    diagram_steps: list[DiagramStep] = Field(
        description="Exactly 4 sequential steps for the visual flowchart",
        min_length=4,
        max_length=4,
    )
    key_takeaway: str = Field(
        description="1 memorable exam/interview takeaway or analogy sentence."
    )


class StudyCarouselResponse(BaseModel):
    topic_name: str = Field(description="Clean English title of the topic")
    pages: list[NotePage] = Field(
        description="Exactly 5 sequential study pages", min_length=5, max_length=5
    )
    social_caption: str = Field(
        description="Engaging human-written social media post caption with hook, summary, and hashtags."
    )


# =====================================================================
# 3. CACHED MODEL DISCOVERY (FAST FLASH-LITE PRIORITY)
# =====================================================================
@lru_cache(maxsize=4)
def get_working_models(api_key: str) -> list[str]:
    """Discovers active Gemini 3.x Flash models once and caches the result for instant reuse."""
    client = genai.Client(api_key=api_key)
    excluded = (
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
    )
    discovered = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name.lower() and not any(x in name.lower() for x in excluded):
                discovered.append(name)
    except Exception:
        pass

    # Prioritize fastest low-latency 3.x Flash models first for maximum speed
    priority_order = [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash",
    ]
    ordered = [m for m in priority_order if m in discovered]
    for m in discovered:
        if m not in ordered:
            ordered.append(m)

    return ordered if ordered else priority_order[:4]


# =====================================================================
# 4. CURRICULUM & COPY GENERATOR AGENT
# =====================================================================
def generate_5_page_study_guide(
    topic: str,
    language: str = "Sinhala_Mix",
    api_key: str = None,
    subject_category: str = "AI & Machine Learning",
) -> StudyCarouselResponse:
    """Generates a complete 5-page university study carousel + social media caption."""
    resolved_key = api_key or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=resolved_key)
    working_models = get_working_models(resolved_key)

    if language == "Sinhala_Mix":
        lang_rules = """
        LANGUAGE MODE: SINHALA + ENGLISH TECHNICAL MIX (University Kuppiya Style).
        - Write explanations in natural, clear conversational Sinhala Unicode script.
        - Keep ALL technical terms, acronyms, and engineering names in English script (e.g., Vector Database, API Gateway, TCP/IP, Big-O, Docker).
        - Write `page_title`, `subtitle_tag`, and `diagram_steps.title` in English.
        - Write the `social_caption` in natural human-like Sinhala + English mix ("Mn ada igena gaththa...", no robotic AI clichés) with relevant hashtags (#NIWNOTES #UniversityNotes).
        """
    else:
        lang_rules = """
        LANGUAGE MODE: 100% GLOBAL ENGLISH.
        - Write all explanations, bullet points, diagrams, and the social caption in crisp, beginner-friendly English.
        - Write the `social_caption` like a top university student sharing personal study notes on LinkedIn/Facebook with hashtags (#NIWNOTES #TechNotes).
        """

    prompt = f"""
    You are the Lead University Note Creator for 'NIWNOTES'.
    University Subject Track: "{subject_category}"
    Target Concept: "{topic}"

    Create a 5-page progressive handwritten study guide so any student or developer scrolling social media can master this topic from scratch:
    - Page 1: The Hook, Simple Definition & Real-World Mental Model
    - Page 2: Core Architecture & How It Works Step-by-Step
    - Page 3: Deep Dive into Key Components & Technical Mechanics
    - Page 4: Real-World Engineering Use Cases & Implementation Pattern
    - Page 5: Common Pitfalls, Best Practices & Exam/Interview Cheat Sheet

    {lang_rules}

    INLINE HIGHLIGHT RULES (CRITICAL):
    Inside `intro_definition` and `bullet_points`, highlight key terms using ONLY these 3 flat tags (NEVER nest tags inside each other):
    1. <mark>important concept</mark> (for marker highlight)
    2. <b>key term</b> (for hand-drawn ink box)
    3. <u>crucial phrase</u> (for pen underline)
    Keep tagged phrases short (1 to 4 words max).
    """

    last_err = None
    for model_name in working_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StudyCarouselResponse,
                    temperature=0.35,
                ),
            )
            return StudyCarouselResponse.model_validate_json(response.text)
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"Failed to generate study guide: {last_err}")


# =====================================================================
# 5. ZERO-DRIFT HTML/SVG SKETCHNOTE BUILDER (MULTI-TEMPLATE)
# =====================================================================
def clean_markup(text: str) -> str:
    """Ensures only clean, non-nested <mark>, <b>, and <u> tags exist."""
    if not text:
        return ""
    # Strip any disallowed HTML tags
    allowed = re.sub(r"<(?!/?(mark|b|u)\b)[^>]+>", "", text)
    # Prevent nested tags inside <mark> or <b>
    allowed = re.sub(
        r"<mark>(.*?)</mark>",
        lambda m: "<mark>" + re.sub(r"</?(b|u|mark)>", "", m.group(1)) + "</mark>",
        allowed,
    )
    return allowed


def build_page_html(
    page: NotePage,
    topic_name: str,
    author: str,
    template_id: str = "classic_cream",
) -> str:
    """Compiles a single NotePage into a 1000x1250px HTML/SVG canvas styled with the chosen template."""
    t = NOTE_TEMPLATES.get(template_id, NOTE_TEMPLATES["classic_cream"])

    intro_html = clean_markup(page.intro_definition)
    takeaway_html = clean_markup(page.key_takeaway)

    bullets_html = ""
    for idx, b in enumerate(page.bullet_points, 1):
        bullets_html += f"""
        <div class="bullet-row">
            <div class="bullet-icon">0{idx}</div>
            <div class="bullet-text">{clean_markup(b)}</div>
        </div>
        """

    steps_html = ""
    for i, step in enumerate(page.diagram_steps):
        arrow_svg = ""
        if i < len(page.diagram_steps) - 1:
            arrow_svg = f"""
            <div class="step-arrow">
                <svg width="28" height="24" viewBox="0 0 28 24" fill="none">
                    <path d="M2 12 C10 10, 18 14, 24 12 M18 6 L25 12 L18 18"
                          stroke="{t['ink_blue']}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            """
        steps_html += f"""
        <div class="step-card">
            <div class="step-num">{step.step_num}</div>
            <div class="step-title">{clean_markup(step.title)}</div>
            <div class="step-detail">{clean_markup(step.detail)}</div>
        </div>
        {arrow_svg}
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&family=Kalam:wght@400;700&family=Noto+Sans+Sinhala:wght@500;700&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    width: 1000px;
    height: 1250px;
    background-color: {t['paper_bg']};
    {t['grid_css']}
    font-family: 'Kalam', 'Noto Sans Sinhala', sans-serif;
    color: {t['ink_main']};
    position: relative;
    overflow: hidden;
    padding: 46px 54px 42px 78px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.margin-line {{
    position: absolute;
    top: 0; bottom: 0; left: 54px;
    width: 2px;
    background: {t['margin_line']};
}}
.top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2.5px solid {t['ink_title']};
    padding-bottom: 12px;
    margin-bottom: 14px;
}}
.brand-pill {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    font-weight: 700;
    background: {t['badge_bg']};
    color: {t['badge_text']};
    padding: 5px 14px;
    border-radius: 6px;
    letter-spacing: 0.08em;
}}
.page-counter {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    font-weight: 700;
    color: {t['ink_blue']};
}}
.header-block {{ margin-bottom: 16px; }}
.subtitle-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    color: {t['ink_red']};
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 4px;
}}
.main-title {{
    font-size: 40px;
    font-weight: 700;
    color: {t['ink_title']};
    line-height: 1.15;
}}
.intro-box {{
    background: {t['card_bg']};
    border: 2.5px solid {t['card_border']};
    border-radius: 14px;
    padding: 18px 22px;
    font-size: 23px;
    line-height: 1.52;
    margin-bottom: 18px;
    box-shadow: 4px 4px 0px {t['card_border']};
}}
.bullets-section {{
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 18px;
}}
.bullet-row {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: {t['card_bg']};
    border-left: 5px solid {t['ink_blue']};
    border-radius: 0 12px 12px 0;
    padding: 13px 18px;
}}
.bullet-icon {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    font-weight: 700;
    background: {t['ink_blue']};
    color: #FFFFFF;
    min-width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 2px;
}}
.bullet-text {{
    font-size: 22px;
    line-height: 1.5;
    flex: 1;
}}
/* Zero-Drift Inline Annotations */
mark {{
    background: linear-gradient(104deg, transparent 0.9%, {t['mark_fill']} 2.4%, {t['mark_fill']} 96%, transparent 98%);
    color: inherit;
    padding: 1px 6px;
    border-radius: 5px;
    -webkit-box-decoration-break: clone;
    box-decoration-break: clone;
}}
b {{
    font-weight: 700;
    color: {t['ink_red']};
    padding: 1px 7px;
    background-color: {t.get('box_fill', 'transparent')};
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' preserveAspectRatio='none' viewBox='0 0 120 40'><path d='M4 6 Q60 2 116 5 Q118 20 115 35 Q60 38 5 34 Q2 20 4 6 Z' fill='none' stroke='{t['box_stroke']}' stroke-width='2.6'/></svg>");
    background-size: 100% 100%;
    -webkit-box-decoration-break: clone;
    box-decoration-break: clone;
}}
u {{
    text-decoration: none;
    color: {t['ink_blue']};
    font-weight: 700;
    padding-bottom: 3px;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' preserveAspectRatio='none' viewBox='0 0 100 10'><path d='M2 7 Q50 2 98 6' fill='none' stroke='{t['underline_stroke']}' stroke-width='3' stroke-linecap='round'/></svg>");
    background-repeat: repeat-x;
    background-position: 0 100%;
    background-size: 100% 8px;
    -webkit-box-decoration-break: clone;
    box-decoration-break: clone;
}}
/* Flowchart Box */
.diagram-container {{
    background: {t['card_bg']};
    border: 2.5px dashed {t['ink_blue']};
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 16px;
}}
.diagram-header {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    color: {t['ink_blue']};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
}}
.steps-row {{
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    gap: 6px;
}}
.step-card {{
    flex: 1;
    background: {t['step_bg']};
    border: 2px solid {t['card_border']};
    border-radius: 10px;
    padding: 10px 10px;
    text-align: center;
}}
.step-num {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    color: {t['ink_red']};
    margin-bottom: 3px;
}}
.step-title {{
    font-size: 18px;
    font-weight: 700;
    color: {t['ink_title']};
    line-height: 1.2;
    margin-bottom: 4px;
}}
.step-detail {{
    font-size: 15px;
    line-height: 1.3;
    opacity: 0.9;
}}
.step-arrow {{
    display: flex;
    align-items: center;
    justify-content: center;
}}
/* Takeaway Footer */
.takeaway-box {{
    background: {t['takeaway_bg']};
    border: 2.5px solid {t['takeaway_border']};
    border-radius: 12px;
    padding: 13px 18px;
    font-size: 20px;
    line-height: 1.42;
    margin-bottom: 12px;
}}
.takeaway-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    color: {t['ink_red']};
    text-transform: uppercase;
    margin-right: 8px;
}}
.footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    opacity: 0.75;
    padding-top: 6px;
    border-top: 1px solid {t['dot_color']};
}}
</style>
</head>
<body>
    <div class="margin-line"></div>
    <div>
        <div class="top-bar">
            <span class="brand-pill">NIWNOTES // {topic_name[:38].upper()}</span>
            <span class="page-counter">SLIDE 0{page.page_number} / 05</span>
        </div>
        <div class="header-block">
            <div class="subtitle-tag">{page.subtitle_tag}</div>
            <div class="main-title">{page.page_title}</div>
        </div>
        <div class="intro-box">{intro_html}</div>
        <div class="bullets-section">{bullets_html}</div>
    </div>
    <div>
        <div class="diagram-container">
            <div class="diagram-header">&#9654; {page.diagram_title}</div>
            <div class="steps-row">{steps_html}</div>
        </div>
        <div class="takeaway-box">
            <span class="takeaway-label">[KEY TAKEAWAY]</span> {takeaway_html}
        </div>
        <div class="footer-bar">
            <span>NIWNOTES UNIVERSITY SOCIAL LEARNING</span>
            <span>CURATED BY {author}</span>
        </div>
    </div>
</body>
</html>"""


def _render_single_page(args: tuple) -> str:
    """Worker function for parallel Chromium rendering."""
    page, topic_name, author, output_dir, template_id = args
    html_content = build_page_html(page, topic_name, author, template_id)
    file_name = f"note_page_{page.page_number}.png"

    hti = Html2Image(
        size=(1000, 1250),
        output_path=output_dir,
        custom_flags=[
            "--virtual-time-budget=1000",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--hide-scrollbars",
            "--log-level=3",
        ],
    )
    hti.screenshot(html_str=html_content, save_as=file_name)
    return os.path.join(output_dir, file_name)


def render_all_pages(
    guide: StudyCarouselResponse,
    author: str = "@NIWNOTES",
    output_dir: str = "output",
    template_id: str = "classic_cream",
) -> list[str]:
    """Renders all 5 slides in parallel using ThreadPoolExecutor for 4x faster execution."""
    os.makedirs(output_dir, exist_ok=True)
    tasks = [
        (page, guide.topic_name, author, output_dir, template_id)
        for page in sorted(guide.pages, key=lambda p: p.page_number)
    ]

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(_render_single_page, tasks))

    return results
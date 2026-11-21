import os
import re
import time
import html
import base64
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from google.genai import types
from dotenv import load_dotenv

from trend_agent import get_genai_client, get_working_models

load_dotenv()


# =====================================================================
# 1. EMBEDDED AUTHENTIC HANDWRITING FONT (SINHALA + ENGLISH)
# =====================================================================
FONT_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "FontoshanHandwrite-Regular.ttf",
)
_FONT_B64 = ""
if os.path.exists(FONT_FILE_PATH):
    try:
        with open(FONT_FILE_PATH, "rb") as _f:
            _FONT_B64 = base64.b64encode(_f.read()).decode("ascii")
    except Exception as _err:
        print(f"Warning: Could not load Fontoshan font file: {_err}")


# =====================================================================
# 2. STRUCTURED PYDANTIC SCHEMAS FOR GEMINI
# =====================================================================
class DiagramStep(BaseModel):
    step_label: str = Field(
        description="Short 1-2 word stage label in English (e.g., 'Input', 'Process', 'Output')"
    )
    step_detail: str = Field(
        description="Concise 3-5 word explanation of this stage"
    )


class NotePage(BaseModel):
    page_number: int = Field(description="Page number within the current batch (1 to 5)")
    title: str = Field(description="Short, punchy English technical heading (max 6 words)")
    summary_banner: str = Field(
        description="1-sentence core takeaway for the top highlighter banner (max 16 words)"
    )
    bullet_points: List[str] = Field(
        description="3 concise study bullet points (12-18 words each). Wrap key technical terms in **double asterisks**."
    )
    diagram_title: str = Field(
        description="Title for the 3-step visual architecture flow box (in English)"
    )
    diagram_steps: List[DiagramStep] = Field(
        description="Exactly 3 sequential steps for the visual architecture diagram"
    )
    pro_tip: str = Field(
        description="1 practical exam tip, memory hook, or real-world engineering rule (max 18 words)"
    )


class BatchSlideDeckWithCaption(BaseModel):
    slides: List[NotePage] = Field(description="Exactly 5 sequential study note pages")
    social_caption: str = Field(
        description="High-conversion LinkedIn & Facebook post caption with hook, bullet summary, question CTA, and hashtags. Must match the chosen language."
    )


class BatchSlideDeckOnly(BaseModel):
    slides: List[NotePage] = Field(description="Exactly 5 sequential study note pages")


class StudyCarouselResponse(BaseModel):
    slides: List[NotePage]
    social_caption: str

    @property
    def pages(self) -> List[NotePage]:
        """Alias so both .slides and .pages work without error."""
        return self.slides


# =====================================================================
# 3. HANDWRITTEN NOTEBOOK TEMPLATES (2 REALISTIC + 2 DIGITAL)
# =====================================================================
NOTE_TEMPLATES: Dict[str, Dict] = {
    "classic_ruled": {
        "name": "Classic Ruled Paper",
        "short_name": "Ruled Notebook",
        "category": "Realistic",
        "badge": "Physical Paper",
        "desc": "Authentic physical ruled paper: blue ruling lines, red margin, ballpoint pen ink, Post-It sticky note, zero digital UI boxes.",
    },
    "vintage_kraft": {
        "name": "Engineering Quad Grid",
        "short_name": "Quad Grid Pad",
        "category": "Realistic",
        "badge": "Physical Paper",
        "desc": "Real engineering 5mm quad grid lecture pad with sepia ink, scotch-taped notes, and hand-drawn technical sketches.",
    },
    "digital_ipad": {
        "name": "iPad GoodNotes Stylus",
        "short_name": "iPad GoodNotes",
        "category": "Digital",
        "badge": "Apple Pencil",
        "desc": "Crisp modern tablet canvas with iPad status bar, modern tablet cards, electric stylus ink, and pastel highlighters.",
    },
    "digital_dark": {
        "name": "Notability Cyber Dark",
        "short_name": "Cyber Dark",
        "category": "Digital",
        "badge": "AMOLED Neon",
        "desc": "Deep slate tablet canvas with glowing neon stylus ink and glassmorphism cards.",
    },
}

TEMPLATE_ALIASES = {
    "classic_cream": "classic_ruled",
    "blueprint_grid": "vintage_kraft",
    "cornell_academic": "digital_ipad",
    "dark_neon": "digital_dark",
}


def normalize_template_key(key: str) -> str:
    """Normalizes template keys including legacy aliases."""
    return TEMPLATE_ALIASES.get(key, key if key in NOTE_TEMPLATES else "classic_ruled")


MODULE_OUTLINES = [
    """
    - Slide 1: Hook, Core Definition & Why It Matters in University/Industry
    - Slide 2: Fundamental Concepts & Underlying Theory
    - Slide 3: Core System Architecture & Data/Control Flow
    - Slide 4: Step-by-Step Execution & Algorithmic Mechanism
    - Slide 5: Real-World Production Use Cases & Summary
    """,
    """
    - Slide 1: Internal Data Structures & Mathematical/Logical Intuition
    - Slide 2: Bottlenecks, Scaling Limits & Performance Optimization
    - Slide 3: Security, Reliability & Fault-Tolerance Patterns
    - Slide 4: Industry Comparison (Modern Approach vs Legacy Approach)
    - Slide 5: Common Exam / Technical Interview Questions & Answers
    """,
    """
    - Slide 1: Production Implementation Blueprint & Tooling Ecosystem
    - Slide 2: Step-by-Step Code/Configuration Design Pattern
    - Slide 3: Debugging, Observability, Metrics & Testing Strategies
    - Slide 4: Common Engineering Anti-Patterns & Mistakes to Avoid
    - Slide 5: Best Practices Checklist for Capstone Projects
    """,
    """
    - Slide 1: Distributed Scaling, High Availability & Latency Tuning
    - Slide 2: Memory, Compute & Cost Optimization Techniques
    - Slide 3: Edge Cases, Race Conditions & Failure Recovery
    - Slide 4: Case Study: How Top Tech Companies Deploy This at Scale
    - Slide 5: Architecture Trade-offs Matrix (Pros vs Cons)
    """,
    """
    - Slide 1: Advanced Extensions & State-of-the-Art Research Directions
    - Slide 2: Cross-System Integration & API Contract Design
    - Slide 3: Governance, Compliance & Ethical Engineering Considerations
    - Slide 4: Hands-On Lab / Portfolio Project Idea for Students
    - Slide 5: Rapid Revision Cheat-Sheet & Formula/Concept Recall
    """,
    """
    - Slide 1: End-to-End System Synthesis & Big-Picture Mental Model
    - Slide 2: Senior Engineer System Design Interview Walkthrough
    - Slide 3: Troubleshooting Playbook (Symptom -> Root Cause -> Fix)
    - Slide 4: Future Roadmap & Emerging Standards (2025-2030)
    - Slide 5: Final Master Takeaways & Career Action Plan
    """,
]


# =====================================================================
# 4. LANGUAGE INSTRUCTIONS & PARALLEL AI GENERATION
# =====================================================================
def _build_language_instructions(language: str, include_caption: bool) -> str:
    if language == "Sinhala_Mix":
        caption_rule = (
            """
        SOCIAL MEDIA CAPTION RULES (MUST BE IN SINHALA + ENGLISH KUPPI MIX):
        - Write the LinkedIn/Facebook `social_caption` in natural Sri Lankan University Sinhala + English mix.
        - Structure:
          1. Strong Sinhala hook line about why this topic matters for IT/Engineering students.
          2. 3-4 short bullet points summarizing what is inside this note deck.
          3. Friendly Call-To-Action asking fellow students to Save/Share and comment their thoughts.
          4. 5 relevant hashtags (#NIWNOTES #Kuppiya #SriLankaTech #UniversityLife #TechNotes).
        - Do NOT use any emojis anywhere in the caption.
            """
            if include_caption
            else ""
        )
        return f"""
        LANGUAGE MODE: NATURAL SRI LANKAN UNIVERSITY "KUPPIYA" SINHALA + ENGLISH MIX (Sinhala_Mix).
        - Write `summary_banner`, `bullet_points`, `diagram_steps.step_detail`, and `pro_tip` in authentic, conversational Sri Lankan university Sinhala Unicode mixed naturally with English technical terms.
        - NEVER translate standard English technical terms into awkward dictionary Sinhala. Keep words like `Architecture`, `Latency`, `Cache`, `Thread`, `Database`, `API`, `Model`, `Token`, `Vector`, `Packet`, `Cluster`, `Container`, `Pipeline`, `Gradient` in English script.
        - Keep `title`, `diagram_title`, and `diagram_steps.step_label` in crisp English.
        - GOOD SINHALA MIX EXAMPLE: "සරලවම කිව්වොත් **RAG Architecture** එකෙන් කරන්නේ LLM එකට උත්තරයක් හදන්න කලින් අපේ **Vector Database** එකෙන් හරියටම ගැලපෙන **Context** එක අරන් දෙන එකයි. මේකෙන් **Hallucinations** සෑහෙන්න අඩු කරගන්න පුළුවන්."
        - Wrap 1-2 key technical terms in each bullet in **double asterisks** for realistic marker highlighting.
        - Do NOT use any emojis anywhere in the output.
        {caption_rule}
        """

    caption_rule = (
        """
        SOCIAL MEDIA CAPTION RULES (100% PURE PROFESSIONAL ENGLISH):
        - Write a high-converting LinkedIn/Facebook `social_caption` in 100% crisp English:
          1. Attention-grabbing academic/engineering hook.
          2. Quick bulleted breakdown of the slides.
          3. Engaging question for students and developers in the comments.
          4. 5 relevant hashtags (#NIWNOTES #ComputerScience #SoftwareEngineering #StudyGram #TechNotes).
        - Do NOT use any emojis anywhere in the caption.
        """
        if include_caption
        else ""
    )
    return f"""
    LANGUAGE MODE: 100% PURE ACADEMIC & INDUSTRY ENGLISH.
    - Write every single field (`title`, `summary_banner`, `bullet_points`, `diagram_title`, `diagram_steps`, and `pro_tip`) in clear, concise, high-impact English suitable for top-tier university revision notes.
    - Wrap 1-2 key technical terms in each bullet in **double asterisks** for realistic marker highlighting.
    - Do NOT use any emojis anywhere in the output.
    {caption_rule}
    """


def _generate_single_batch(
    api_key: str,
    topic: str,
    language: str,
    subject_category: str,
    batch_index: int,
    total_batches: int,
) -> tuple[List[NotePage], str]:
    client = get_genai_client(api_key)
    working_models = get_working_models(api_key)
    outline = MODULE_OUTLINES[batch_index % len(MODULE_OUTLINES)]
    start_page = batch_index * 5 + 1
    end_page = start_page + 4
    include_caption = batch_index == 0
    lang_rules = _build_language_instructions(language, include_caption=include_caption)
    target_schema = BatchSlideDeckWithCaption if include_caption else BatchSlideDeckOnly

    prompt = f"""
    You are an Elite University Professor and Visual Sketchnote Educator in '{subject_category}'.
    Create Batch {batch_index + 1} of {total_batches} (Pages {start_page} to {end_page}) of a handwritten study carousel on:
    TOPIC: "{topic}"

    MODULE SYLLABUS FOR THIS 5-PAGE BATCH:
    {outline}

    {lang_rules}

    STRICT FORMATTING & DENSITY RULES (ZERO OVERFLOW):
    1. Generate EXACTLY 5 slides (`page_number` 1 to 5).
    2. Each slide MUST have:
       - `title`: Max 6 words (English).
       - `summary_banner`: Max 16 words.
       - `bullet_points`: Exactly 3 bullet points, 12-18 words each. Wrap 1-2 key terms per bullet in **double asterisks** for marker highlighting.
       - `diagram_title`: Short title for the 3-step visual flow.
       - `diagram_steps`: Exactly 3 steps (`step_label` max 2 words, `step_detail` max 5 words).
       - `pro_tip`: Max 18 words.
    3. Do NOT include any emojis or emoticons anywhere.
    """

    num_models = len(working_models)
    ordered_models = [working_models[(batch_index + i) % num_models] for i in range(num_models)]

    last_error = None
    for attempt in range(2):
        for model_name in ordered_models:
            try:
                config_kwargs = {
                    "response_mime_type": "application/json",
                    "response_schema": target_schema,
                    "temperature": 0.35,
                }
                if "2.5" in model_name or "3." in model_name:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                parsed = response.parsed
                if parsed and parsed.slides and len(parsed.slides) >= 5:
                    slides = parsed.slides[:5]
                    for idx, s in enumerate(slides):
                        s.page_number = start_page + idx
                    caption = getattr(parsed, "social_caption", "") if include_caption else ""
                    return slides, caption
            except Exception as err:
                last_error = err
                err_str = str(err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    time.sleep(0.6)
                continue

    raise RuntimeError(f"Failed to synthesize batch {batch_index + 1}. Last error: {last_error}")


def generate_5_page_study_guide(
    topic: str,
    language: str = "Sinhala_Mix",
    api_key: str | None = None,
    subject_category: str = "AI & Machine Learning",
    num_pages: int = 5,
) -> StudyCarouselResponse:
    """
    Generates 5, 10, or 30 handwritten slides in parallel using multi-threaded batching
    and zero thinking-token overhead for rapid synthesis.
    """
    active_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not active_key:
        raise ValueError("Missing Gemini API Key. Please configure GEMINI_API_KEY.")

    if num_pages not in (5, 10, 30):
        num_pages = 5

    total_batches = num_pages // 5

    if total_batches == 1:
        slides, caption = _generate_single_batch(
            active_key, topic, language, subject_category, 0, 1
        )
        return StudyCarouselResponse(slides=slides, social_caption=caption)

    max_workers = min(total_batches, 6)
    batch_results: Dict[int, tuple[List[NotePage], str]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _generate_single_batch,
                active_key,
                topic,
                language,
                subject_category,
                b_idx,
                total_batches,
            ): b_idx
            for b_idx in range(total_batches)
        }
        for future in future_map:
            b_idx = future_map[future]
            batch_results[b_idx] = future.result()

    all_slides: List[NotePage] = []
    master_caption = ""
    for b_idx in range(total_batches):
        b_slides, b_caption = batch_results[b_idx]
        if b_idx == 0:
            master_caption = b_caption
        all_slides.extend(b_slides)

    for idx, slide in enumerate(all_slides, start=1):
        slide.page_number = idx

    return StudyCarouselResponse(slides=all_slides, social_caption=master_caption)


# =====================================================================
# 5. INSTANT BROWSER-NATIVE SKETCHNOTE STUDIO & CLIENT-SIDE GPU EXPORT
# =====================================================================
def _format_inline_highlights(text: str) -> str:
    escaped = html.escape(str(text or ""))
    return re.sub(
        r"\*\*(.+?)\*\*",
        r'<mark class="hl-mark">\1</mark>',
        escaped,
    )


def _extract_slide_fields(slide: Any, fallback_page_num: int) -> dict:
    """Safely extracts slide fields from either current or legacy NotePage objects."""
    page_number = getattr(slide, "page_number", fallback_page_num)
    title = getattr(slide, "title", f"Concept Slide {page_number}")
    summary_banner = getattr(slide, "summary_banner", None) or getattr(
        slide, "highlight", None
    ) or getattr(slide, "subtitle", "")
    bullet_points = getattr(slide, "bullet_points", None) or getattr(
        slide, "key_points", []
    )
    diagram_title = getattr(slide, "diagram_title", "System Architecture & Flow")
    diagram_steps = getattr(slide, "diagram_steps", [])
    pro_tip = getattr(slide, "pro_tip", None) or getattr(slide, "exam_note", "")

    normalized_steps = []
    for idx, step in enumerate(diagram_steps[:3]):
        lbl = getattr(step, "step_label", f"Step 0{idx + 1}")
        dtl = getattr(step, "step_detail", None) or getattr(
            step, "step_description", ""
        )
        normalized_steps.append((lbl, dtl))

    return {
        "page_number": page_number,
        "title": title,
        "summary_banner": summary_banner,
        "bullet_points": bullet_points[:3],
        "diagram_title": diagram_title,
        "diagram_steps": normalized_steps,
        "pro_tip": pro_tip,
    }


def _build_slide_card_html(
    slide: Any,
    total_pages: int,
    topic: str,
    subject_category: str,
    idx: int = 1,
    template_key: str = "classic_ruled",
) -> str:
    norm_key = normalize_template_key(template_key)
    is_realistic = norm_key in ("classic_ruled", "vintage_kraft")
    fields = _extract_slide_fields(slide, idx)

    # Bullet point rendering: In realistic mode, numbers are handwritten directly on paper lines
    bullet_prefix = "0" if is_realistic else "0"
    bullets_html = "".join(
        f'<li class="nc-bullet-item">'
        f'<span class="nc-bullet-dot">{bullet_prefix}{i + 1}.</span>'
        f'<div class="nc-bullet-text">{_format_inline_highlights(b)}</div>'
        f'</li>'
        for i, b in enumerate(fields["bullet_points"])
    )

    steps_parts = []
    for i, (lbl, dtl) in enumerate(fields["diagram_steps"]):
        steps_parts.append(
            f'<div class="nc-step-card">'
            f'<div class="nc-step-badge">0{i + 1}  {html.escape(str(lbl))}</div>'
            f'<div class="nc-step-detail">{_format_inline_highlights(dtl)}</div>'
            f'</div>'
        )
        if i < len(fields["diagram_steps"]) - 1:
            steps_parts.append(
                '<div class="nc-flow-arrow">'
                '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
                '<line x1="4" y1="12" x2="20" y2="12"></line>'
                '<polyline points="13 5 20 12 13 19"></polyline>'
                '</svg>'
                '</div>'
            )
    steps_html = "\n".join(steps_parts)

    # Template-specific realistic / digital physical elements
    decorations_html = ""
    protip_tape_html = ""
    top_bar_extra = ""

    if norm_key == "classic_ruled":
        decorations_html = """
        <div class="nc-binder-hole nc-hole-top"></div>
        <div class="nc-binder-hole nc-hole-mid"></div>
        <div class="nc-binder-hole nc-hole-bot"></div>
        <div class="nc-margin-line"></div>
        """
        protip_tape_html = '<span class="nc-pin-doodle">📌</span>'
    elif norm_key == "vintage_kraft":
        decorations_html = """
        <div class="nc-margin-line"></div>
        <div class="nc-kraft-texture-overlay"></div>
        """
        protip_tape_html = '<div class="nc-scotch-tape"></div>'
    elif norm_key == "digital_ipad":
        top_bar_extra = """
        <div class="nc-digital-statusbar">
            <span class="nc-ds-time">9:41 AM</span>
            <span class="nc-ds-title">GoodNotes 6  ✦  Study Deck</span>
            <span class="nc-ds-battery">✦ Apple Pencil 100% 🔋</span>
        </div>
        """
        protip_tape_html = '<span class="nc-sparkle-doodle">💡</span>'
    elif norm_key == "digital_dark":
        top_bar_extra = """
        <div class="nc-digital-statusbar nc-cyber-statusbar">
            <span class="nc-ds-time">23:42</span>
            <span class="nc-ds-title">NOTABILITY // CYBER DARK AMOLED</span>
            <span class="nc-ds-battery">⚡ STYLUS ACTIVE 100%</span>
        </div>
        """
        protip_tape_html = '<span class="nc-sparkle-doodle">⚡</span>'

    summary_tag_label = "KEY CONCEPT //" if is_realistic else "KEY IDEA"

    return f"""
    <div class="nc-canvas nc-theme-{norm_key}" id="nc-slide-{fields['page_number']}" data-page="{fields['page_number']}">
        {decorations_html}
        <div class="nc-inner">
            {top_bar_extra}
            <div class="nc-topbar">
                <div class="nc-subject-pill">NIWNOTES  //  {html.escape(subject_category.upper())}</div>
                <div class="nc-page-pill">PAGE {fields['page_number']:02d} OF {total_pages:02d}</div>
            </div>

            <div class="nc-topic-kicker">{html.escape(topic)}</div>
            <div class="nc-title-wrap">
                <h1 class="nc-title">{html.escape(fields['title'])}</h1>
                <svg class="nc-title-underline" width="220" height="10" viewBox="0 0 220 10" fill="none">
                    <path d="M2 6C45 2 90 9 135 5C180 1 205 8 218 5" stroke="var(--ink-accent)" stroke-width="2.6" stroke-linecap="round"/>
                </svg>
            </div>

            <div class="nc-summary-banner">
                <span class="nc-summary-tag">{summary_tag_label}</span>
                <p class="nc-summary-text">{_format_inline_highlights(fields['summary_banner'])}</p>
            </div>

            <ul class="nc-bullet-list">
                {bullets_html}
            </ul>

            <div class="nc-diagram-box">
                <div class="nc-diagram-header">
                    <span class="nc-diagram-dot"></span>
                    <span class="nc-diagram-title">{html.escape(fields['diagram_title'])}</span>
                </div>
                <div class="nc-diagram-grid">
                    {steps_html}
                </div>
            </div>

            <div class="nc-footer-row">
                <div class="nc-protip-box">
                    {protip_tape_html}
                    <span class="nc-protip-label">EXAM / PRO TIP:</span>
                    <span class="nc-protip-text">{_format_inline_highlights(fields['pro_tip'])}</span>
                </div>
                <div class="nc-watermark">NIWNOTES STUDIO</div>
            </div>
        </div>
    </div>
    """


def build_interactive_studio_html(
    study_data: Optional[StudyCarouselResponse] = None,
    topic: str = "Study_Notes",
    template_key: str = "classic_ruled",
    subject_category: str = "AI & Machine Learning",
    language: str = "Sinhala_Mix",
    pages: Optional[List[Any]] = None,
    caption: str = "",
    **kwargs,
) -> str:
    """
    Renders the entire multi-page handwritten note studio directly in the user's browser
    with authentic handwritten Sinhala + English fonts, 2 realistic paper templates + 2 digital stylus templates,
    responsive mobile/tablet scaling, and client-side GPU PNG/ZIP export.
    """
    norm_key = normalize_template_key(template_key)

    if study_data is not None:
        slide_list = getattr(study_data, "slides", None) or getattr(
            study_data, "pages", []
        )
        social_caption_text = getattr(study_data, "social_caption", "") or caption
    else:
        slide_list = pages or []
        social_caption_text = caption

    theme_css_map = {
        "classic_ruled": """
            --paper-bg: #FCFBF7;
            --paper-grid: repeating-linear-gradient(to bottom, transparent 0px, transparent 31px, rgba(160, 185, 215, 0.45) 32px);
            --paper-grid-size: 100% 32px;
            --margin-line: rgba(239, 68, 68, 0.65);
            --ink-primary: #152E5A;
            --ink-secondary: #1E3A8A;
            --ink-accent: #DC2626;
            --banner-bg: rgba(254, 240, 138, 0.35);
            --banner-border: #EAB308;
            --hl-bg: #FEF08A;
            --hl-ink: #713F12;
            --card-bg: transparent;
            --card-border: #152E5A;
            --step-bg: rgba(255, 255, 255, 0.6);
            --protip-bg: #FEF08A;
            --protip-border: #EAB308;
            --font-tilt: -0.2deg;
        """,
        "vintage_kraft": """
            --paper-bg: #F7F1E5;
            --paper-grid: linear-gradient(to right, rgba(139, 94, 60, 0.16) 1px, transparent 1px),
                          linear-gradient(to bottom, rgba(139, 94, 60, 0.16) 1px, transparent 1px);
            --paper-grid-size: 18px 18px;
            --margin-line: rgba(180, 83, 9, 0.48);
            --ink-primary: #1F1610;
            --ink-secondary: #4A3324;
            --ink-accent: #C2410C;
            --banner-bg: rgba(253, 230, 138, 0.35);
            --banner-border: #D97706;
            --hl-bg: #FDE68A;
            --hl-ink: #451A03;
            --card-bg: transparent;
            --card-border: #78350F;
            --step-bg: rgba(255, 255, 255, 0.55);
            --protip-bg: #FFFBEB;
            --protip-border: #B45309;
            --font-tilt: -0.3deg;
        """,
        "digital_ipad": """
            --paper-bg: #F8FAFC;
            --paper-grid: radial-gradient(#CBD5E1 1.25px, transparent 1.25px);
            --paper-grid-size: 22px 22px;
            --margin-line: rgba(99, 102, 241, 0.32);
            --ink-primary: #0F172A;
            --ink-secondary: #475569;
            --ink-accent: #2563EB;
            --banner-bg: #EEF2FF;
            --banner-border: #6366F1;
            --hl-bg: #C7D2FE;
            --hl-ink: #312E81;
            --card-bg: #FFFFFF;
            --card-border: #CBD5E1;
            --step-bg: #F1F5F9;
            --protip-bg: #ECFDF5;
            --protip-border: #10B981;
            --font-tilt: 0deg;
        """,
        "digital_dark": """
            --paper-bg: #0B0F19;
            --paper-grid: radial-gradient(rgba(56, 189, 248, 0.22) 1.25px, transparent 1.25px);
            --paper-grid-size: 24px 24px;
            --margin-line: rgba(56, 189, 248, 0.28);
            --ink-primary: #F8FAFC;
            --ink-secondary: #94A3B8;
            --ink-accent: #38BDF8;
            --banner-bg: rgba(56, 189, 248, 0.12);
            --banner-border: #38BDF8;
            --hl-bg: rgba(56, 189, 248, 0.25);
            --hl-ink: #E0F2FE;
            --card-bg: #111827;
            --card-border: rgba(56, 189, 248, 0.38);
            --step-bg: #1E293B;
            --protip-bg: rgba(16, 185, 129, 0.14);
            --protip-border: #10B981;
            --font-tilt: 0deg;
        """,
    }

    selected_theme_vars = theme_css_map.get(norm_key, theme_css_map["classic_ruled"])
    total_pages = len(slide_list)
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)[:35] or "NIWNOTES"

    slides_deck_html = "\n".join(
        _build_slide_card_html(s, total_pages, topic, subject_category, idx=i + 1, template_key=norm_key)
        for i, s in enumerate(slide_list)
    )

    thumbs_html = "\n".join(
        f"""
        <button class="thumb-pill {'active' if i == 0 else ''}" onclick="selectSlide({i + 1})" id="thumb-btn-{i + 1}">
            <span class="thumb-num">#{i + 1:02d}</span>
            <span class="thumb-title">{html.escape(getattr(s, 'title', f'Slide {i + 1}'))}</span>
        </button>
        """
        for i, s in enumerate(slide_list)
    )

    escaped_caption = html.escape(social_caption_text)
    lang_badge = "SINHALA + ENGLISH KUPPI MIX" if language == "Sinhala_Mix" else "100% PURE ENGLISH"
    tpl_meta = NOTE_TEMPLATES.get(norm_key, NOTE_TEMPLATES["classic_ruled"])
    tpl_style_badge = f"{tpl_meta['category'].upper()} // {tpl_meta['badge'].upper()}"

    # Base64 embedded font CSS block
    font_face_css = ""
    if _FONT_B64:
        font_face_css = f"""
        @font-face {{
            font-family: 'FontoshanHandwrite';
            src: url('data:font/truetype;charset=utf-8;base64,{_FONT_B64}') format('truetype');
            font-weight: normal;
            font-style: normal;
            font-display: swap;
        }}
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Kalam:wght@400;700&family=Architects+Daughter&family=Patrick+Hand&family=Maname&family=Yaldevi:wght@400;600;700&family=Noto+Sans+Sinhala:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>

<style>
    {font_face_css}

    :root {{
        {selected_theme_vars}
    }}

    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    html, body {{
        width: 100%;
        max-width: 100vw;
        overflow-x: hidden;
        background: transparent;
        color: #141413;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 0 0 20px 0;
    }}

    /* STUDIO WINDOW CONTAINER */
    .studio-window {{
        background: #FFFFFF;
        border: 1px solid rgba(20, 20, 19, 0.12);
        border-radius: 20px;
        box-shadow: 0 10px 30px -6px rgba(20, 20, 19, 0.08);
        overflow: hidden;
        width: 100%;
        box-sizing: border-box;
    }}

    .studio-titlebar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 18px;
        background: #F7F6F2;
        border-bottom: 1px solid rgba(20, 20, 19, 0.08);
        flex-wrap: wrap;
        gap: 10px;
        box-sizing: border-box;
    }}

    .macos-dots {{
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .dot {{
        width: 11px;
        height: 11px;
        border-radius: 999px;
    }}
    .dot-r {{ background: #FF5F56; }}
    .dot-y {{ background: #FFBD2E; }}
    .dot-g {{ background: #27C93F; }}

    .studio-bar-title {{
        font-size: 0.84rem;
        font-weight: 700;
        color: #5E5D59;
        letter-spacing: -0.01em;
    }}

    .studio-badge {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        background: #FFFFFF;
        color: var(--ink-accent);
        border: 1px solid rgba(20, 20, 19, 0.1);
        padding: 3px 8px;
        border-radius: 999px;
    }}

    .studio-actions {{
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }}

    .woday-btn {{
        appearance: none;
        border: 1px solid rgba(20, 20, 19, 0.14);
        background: #FFFFFF;
        color: #141413;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 0.78rem;
        padding: 8px 14px;
        border-radius: 999px;
        cursor: pointer;
        transition: all 0.16s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        white-space: nowrap;
    }}
    .woday-btn:hover {{
        background: #F3F2EE;
        transform: translateY(-1px);
    }}
    .woday-btn-primary {{
        background: #141413;
        color: #FFFFFF;
        border-color: #141413;
    }}
    .woday-btn-primary:hover {{
        background: #2C2B29;
    }}

    /* WORKSPACE GRID: FIXED ZERO-BLOWOUT FLEXIBLE COLUMNS */
    .studio-body {{
        display: grid;
        grid-template-columns: minmax(0, 1.18fr) minmax(0, 0.82fr);
        gap: 20px;
        padding: 18px;
        width: 100%;
        box-sizing: border-box;
    }}

    .studio-body > div {{
        min-width: 0;
        width: 100%;
        box-sizing: border-box;
    }}

    @media (max-width: 1060px) {{
        .studio-body {{
            grid-template-columns: 1fr;
            padding: 14px;
            gap: 18px;
        }}
    }}

    /* THUMBNAIL STRIP */
    .thumb-strip {{
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 8px;
        margin-bottom: 12px;
        scrollbar-width: thin;
        -webkit-overflow-scrolling: touch;
        width: 100%;
        box-sizing: border-box;
    }}

    .thumb-pill {{
        flex: 0 0 auto;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 12px;
        border-radius: 12px;
        border: 1px solid rgba(20, 20, 19, 0.1);
        background: #F7F6F2;
        color: #5E5D59;
        cursor: pointer;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.76rem;
        font-weight: 700;
        transition: all 0.15s ease;
        max-width: 200px;
    }}
    .thumb-pill.active {{
        background: #141413;
        color: #FFFFFF;
        border-color: #141413;
    }}
    .thumb-num {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        opacity: 0.85;
    }}
    .thumb-title {{
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* RESPONSIVE INSPECTOR STAGE */
    .inspector-stage {{
        background: #F3F2EE;
        border: 1px solid rgba(20, 20, 19, 0.08);
        border-radius: 18px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        box-sizing: border-box;
    }}

    .inspector-viewport {{
        width: 100%;
        max-width: 520px;
        aspect-ratio: 1000 / 1250;
        position: relative;
        overflow: hidden;
        border-radius: 14px;
        box-shadow: 0 16px 36px -8px rgba(15, 23, 42, 0.22);
        background: var(--paper-bg);
        margin: 0 auto;
    }}

    .inspector-scale-wrap {{
        width: 1000px;
        height: 1250px;
        position: absolute;
        top: 0;
        left: 0;
        transform-origin: top left;
    }}

    .stage-nav-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        max-width: 520px;
        margin-top: 14px;
        gap: 8px;
    }}

    .stage-counter {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        color: #5E5D59;
    }}

    /* =================================================================
       ACTUAL 1000x1250 HANDWRITTEN NOTE CANVAS (EXPORTED AT 1:1 PIXELS)
       ================================================================= */
    .offscreen-deck {{
        position: fixed;
        left: -99999px;
        top: 0;
        pointer-events: none;
    }}

    .nc-canvas {{
        width: 1000px;
        height: 1250px;
        background-color: var(--paper-bg);
        background-image: var(--paper-grid);
        background-size: var(--paper-grid-size);
        position: relative;
        overflow: hidden;
        color: var(--ink-primary);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        text-shadow: 0 0 0.4px rgba(20, 20, 19, 0.25);
    }}

    /* REALISTIC TEMPLATES: PHYSICAL PAPER LOOK (NO CARDS, PURE HANDWRITING) */
    .nc-theme-classic_ruled,
    .nc-theme-vintage_kraft {{
        box-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 18px 45px -8px rgba(0,0,0,0.22);
        border-radius: 3px;
    }}

    /* MARGIN LINE & BINDER HOLES (PHYSICAL PAPER FEATURES) */
    .nc-margin-line {{
        position: absolute;
        top: 0;
        bottom: 0;
        left: 82px;
        width: 2.2px;
        background: var(--margin-line);
        box-shadow: 1px 0 0 rgba(239, 68, 68, 0.15);
        z-index: 2;
    }}

    .nc-binder-hole {{
        position: absolute;
        left: 22px;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: radial-gradient(circle at 35% 35%, #DDD6C8 0%, #B4AC98 65%, #8E8570 100%);
        box-shadow: inset 2px 2px 5px rgba(0,0,0,0.45), 1px 1px 2px rgba(255,255,255,0.7);
        border: 1px solid rgba(0,0,0,0.12);
        z-index: 5;
    }}
    .nc-hole-top {{ top: 140px; }}
    .nc-hole-mid {{ top: 625px; }}
    .nc-hole-bot {{ top: 1100px; }}

    /* SCOTCH TAPE STRIP (VINTAGE KRAFT STICKY EFFECT) */
    .nc-scotch-tape {{
        position: absolute;
        top: -12px;
        left: 36px;
        width: 96px;
        height: 22px;
        background: rgba(255, 255, 235, 0.74);
        border: 1px solid rgba(210, 195, 160, 0.5);
        transform: rotate(-2.2deg);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        backdrop-filter: blur(1px);
        z-index: 8;
    }}

    /* DIGITAL TABLET STATUS BAR (IPAD / NOTABILITY) */
    .nc-digital-statusbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 6px 14px;
        background: rgba(241, 245, 249, 0.75);
        border-bottom: 1.5px solid rgba(203, 213, 225, 0.6);
        border-radius: 12px 12px 0 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 700;
        color: var(--ink-secondary);
        margin-bottom: 8px;
    }}
    .nc-cyber-statusbar {{
        background: rgba(17, 24, 39, 0.85);
        border-bottom: 1.5px solid rgba(56, 189, 248, 0.3);
        color: var(--ink-accent);
    }}

    .nc-inner {{
        position: relative;
        z-index: 3;
        padding: 38px 48px 36px 98px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}

    .nc-topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px dashed rgba(148, 163, 184, 0.4);
        padding-bottom: 12px;
    }}

    .nc-theme-classic_ruled .nc-topbar,
    .nc-theme-vintage_kraft .nc-topbar {{
        border-bottom: 2px solid var(--margin-line);
        padding-bottom: 8px;
    }}

    .nc-subject-pill {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 700;
        color: var(--ink-accent);
        letter-spacing: 0.04em;
    }}
    .nc-theme-classic_ruled .nc-subject-pill,
    .nc-theme-vintage_kraft .nc-subject-pill {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 22px;
        font-weight: 700;
        color: var(--ink-secondary);
        letter-spacing: 0;
    }}

    .nc-page-pill {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 700;
        background: var(--card-bg);
        color: var(--ink-primary);
        border: 2px solid var(--card-border);
        padding: 4px 13px;
        border-radius: 999px;
        box-shadow: 2px 2px 0px var(--card-border);
    }}
    .nc-theme-classic_ruled .nc-page-pill,
    .nc-theme-vintage_kraft .nc-page-pill {{
        background: transparent;
        border: 1.8px solid var(--ink-primary);
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 19px;
        font-weight: 800;
        color: var(--ink-primary);
        box-shadow: none;
        padding: 2px 10px;
    }}

    .nc-topic-kicker {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', 'Patrick Hand', cursive;
        font-size: 25px;
        font-weight: 700;
        color: var(--ink-accent);
        margin-top: 4px;
    }}

    .nc-title-wrap {{
        position: relative;
        margin-bottom: 4px;
    }}

    .nc-title {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', 'Architects Daughter', 'Maname', 'Yaldevi', 'Noto Sans Sinhala', sans-serif;
        font-size: 38px;
        font-weight: 700;
        line-height: 1.18;
        color: var(--ink-primary);
        letter-spacing: -0.015em;
        margin-bottom: 2px;
    }}

    .nc-title-underline {{
        display: block;
        margin-top: -2px;
        opacity: 0.85;
    }}

    /* HIGHLIGHTER BANNER / KEY CONCEPT */
    .nc-summary-banner {{
        background: var(--banner-bg);
        border-left: 6px solid var(--banner-border);
        border-radius: 14px;
        padding: 13px 18px;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        margin: 4px 0;
    }}

    /* REALISTIC TEMPLATES: NATURAL PAPER SUMMARY (NO CARDS) */
    .nc-theme-classic_ruled .nc-summary-banner,
    .nc-theme-vintage_kraft .nc-summary-banner {{
        background: transparent;
        border: none;
        border-left: 5px solid var(--banner-border);
        border-radius: 0;
        box-shadow: none;
        padding: 6px 14px;
        margin: 4px 0;
    }}

    .nc-summary-tag {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 700;
        background: var(--banner-border);
        color: #FFFFFF;
        padding: 3px 8px;
        border-radius: 6px;
        flex-shrink: 0;
        margin-top: 3px;
    }}

    .nc-theme-classic_ruled .nc-summary-tag,
    .nc-theme-vintage_kraft .nc-summary-tag {{
        background: transparent;
        color: var(--ink-accent);
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 19px;
        font-weight: 800;
        padding: 0;
        border-radius: 0;
        letter-spacing: 0.03em;
    }}

    .nc-summary-text {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', 'Patrick Hand', 'Maname', 'Yaldevi', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 21px;
        font-weight: 600;
        line-height: 1.38;
        color: var(--ink-primary);
    }}

    /* BULLET LIST */
    .nc-bullet-list {{
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 11px;
        margin: 6px 0;
    }}

    .nc-bullet-item {{
        display: flex;
        align-items: flex-start;
        gap: 14px;
        background: var(--card-bg);
        border: 2px solid rgba(148, 163, 184, 0.28);
        border-radius: 14px;
        padding: 13px 18px;
    }}

    /* REALISTIC TEMPLATES: WRITE DIRECTLY ON PAPER LINES (NO WHITE BOXES!) */
    .nc-theme-classic_ruled .nc-bullet-item,
    .nc-theme-vintage_kraft .nc-bullet-item {{
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 4px 0 !important;
        box-shadow: none !important;
        gap: 12px !important;
    }}

    .nc-bullet-dot {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 700;
        background: var(--ink-accent);
        color: #FFFFFF;
        min-width: 32px;
        height: 32px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
        border-radius: 50% 45% 48% 52% / 48% 52% 45% 50%;
        transform: rotate(-1.5deg);
    }}

    .nc-theme-classic_ruled .nc-bullet-dot,
    .nc-theme-vintage_kraft .nc-bullet-dot {{
        background: transparent !important;
        color: var(--ink-accent) !important;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        min-width: 30px !important;
        height: auto !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        transform: none !important;
        margin-top: -3px !important;
    }}

    .nc-bullet-text {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', 'Patrick Hand', 'Maname', 'Yaldevi', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 21px;
        font-weight: 600;
        line-height: 1.4;
        color: var(--ink-primary);
    }}

    .hl-mark {{
        background: var(--hl-bg);
        color: var(--hl-ink);
        padding: 2px 7px;
        border-radius: 4px 7px 3px 6px;
        font-weight: 700;
        display: inline;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        -webkit-box-decoration-break: clone;
        box-decoration-break: clone;
    }}

    /* 3-STEP VISUAL ARCHITECTURE FLOW BOX */
    .nc-diagram-box {{
        background: var(--card-bg);
        border: 2px solid var(--card-border);
        border-radius: 16px;
        padding: 14px 18px;
        box-shadow: 4px 4px 0px var(--card-border);
        margin: 6px 0;
    }}

    /* REALISTIC TEMPLATES: HAND-SKETCHED DIAGRAM BOX (ORGANIC PEN STROKES) */
    .nc-theme-classic_ruled .nc-diagram-box,
    .nc-theme-vintage_kraft .nc-diagram-box {{
        background: transparent !important;
        border: 2px dashed rgba(21, 46, 90, 0.45) !important;
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px !important;
        box-shadow: none !important;
        padding: 12px 16px !important;
    }}

    .nc-theme-vintage_kraft .nc-diagram-box {{
        border: 2px dashed rgba(120, 53, 15, 0.45) !important;
    }}

    .nc-diagram-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 11px;
    }}

    .nc-diagram-dot {{
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: var(--ink-accent);
    }}

    .nc-diagram-title {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 700;
        color: var(--ink-primary);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    .nc-theme-classic_ruled .nc-diagram-title,
    .nc-theme-vintage_kraft .nc-diagram-title {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive !important;
        font-size: 21px !important;
        font-weight: 700 !important;
        color: var(--ink-accent) !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
    }}

    .nc-diagram-grid {{
        display: flex;
        align-items: stretch;
        justify-content: space-between;
        gap: 8px;
    }}

    .nc-step-card {{
        flex: 1;
        min-width: 0;
        background: var(--step-bg);
        border: 2px solid var(--ink-accent);
        border-radius: 11px;
        padding: 10px 12px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }}

    /* REALISTIC TEMPLATES: HAND-DRAWN SKETCH BOXES FOR DIAGRAM STEPS */
    .nc-theme-classic_ruled .nc-step-card,
    .nc-theme-vintage_kraft .nc-step-card {{
        background: rgba(255, 255, 255, 0.55) !important;
        border: 2px solid var(--ink-primary) !important;
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px !important;
        box-shadow: 2px 2px 0px rgba(0, 0, 0, 0.12) !important;
        padding: 9px 11px !important;
    }}

    .nc-step-badge {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 13.5px;
        font-weight: 700;
        color: var(--ink-accent);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .nc-theme-classic_ruled .nc-step-badge,
    .nc-theme-vintage_kraft .nc-step-badge {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        color: var(--ink-accent) !important;
        border-bottom: 1.5px dashed var(--ink-accent);
        padding-bottom: 2px;
    }}

    .nc-step-detail {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', 'Patrick Hand', 'Maname', 'Yaldevi', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 18px;
        font-weight: 600;
        line-height: 1.34;
        color: var(--ink-primary);
    }}

    .nc-flow-arrow {{
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--ink-accent);
        flex-shrink: 0;
        opacity: 0.85;
    }}

    /* FOOTER & PRO TIP */
    .nc-footer-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        padding-top: 6px;
    }}

    .nc-protip-box {{
        flex: 1;
        background: var(--protip-bg);
        border: 2px solid var(--card-border);
        border-radius: 12px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        position: relative;
    }}

    /* REALISTIC TEMPLATE 1: REAL YELLOW 3M POST-IT STICKY NOTE */
    .nc-theme-classic_ruled .nc-protip-box {{
        background: #FEF08A !important;
        border: none !important;
        border-radius: 3px 3px 18px 3px !important;
        box-shadow: 2px 8px 18px -2px rgba(0,0,0,0.2) !important;
        transform: rotate(-1.5deg) !important;
        padding: 10px 16px !important;
    }}
    .nc-theme-classic_ruled .nc-protip-label {{
        background: #EAB308 !important;
        color: #713F12 !important;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        padding: 2px 7px !important;
        border-radius: 4px !important;
    }}

    /* REALISTIC TEMPLATE 2: TAPED KRAFT PAPER SNIPPET */
    .nc-theme-vintage_kraft .nc-protip-box {{
        background: #FFFBEB !important;
        border: 1.5px dashed #B45309 !important;
        border-radius: 4px !important;
        box-shadow: 2px 8px 16px -2px rgba(0,0,0,0.15) !important;
        transform: rotate(0.8deg) !important;
        padding: 10px 16px !important;
    }}
    .nc-theme-vintage_kraft .nc-protip-label {{
        background: #B45309 !important;
        color: #FFFFFF !important;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        padding: 2px 7px !important;
        border-radius: 4px !important;
    }}

    .nc-protip-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 700;
        background: var(--ink-primary);
        color: var(--paper-bg);
        padding: 3px 7px;
        border-radius: 5px;
        white-space: nowrap;
        flex-shrink: 0;
    }}

    .nc-protip-text {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', 'Patrick Hand', 'Maname', 'Yaldevi', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 18px;
        font-weight: 600;
        color: var(--ink-primary);
        line-height: 1.32;
    }}

    .nc-watermark {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 700;
        color: var(--ink-secondary);
        white-space: nowrap;
        opacity: 0.85;
    }}
    .nc-theme-classic_ruled .nc-watermark,
    .nc-theme-vintage_kraft .nc-watermark {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 18px;
        font-weight: 700;
        color: var(--ink-secondary);
        opacity: 0.75;
    }}

    /* RIGHT COLUMN: SOCIAL CAPTION & EXPORT KIT */
    .social-panel {{
        background: #F7F6F2;
        border: 1px solid rgba(20, 20, 19, 0.08);
        border-radius: 18px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        width: 100%;
        box-sizing: border-box;
    }}

    .social-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }}

    .social-title {{
        font-size: 0.92rem;
        font-weight: 800;
        color: #141413;
    }}

    .social-lang-tag {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        background: #FFFFFF;
        color: #FF5A36;
        border: 1px solid rgba(255, 90, 54, 0.25);
        padding: 4px 10px;
        border-radius: 999px;
    }}

    .caption-textarea {{
        width: 100%;
        min-height: 260px;
        border: 1px solid rgba(20, 20, 19, 0.12);
        border-radius: 12px;
        background: #FFFFFF;
        padding: 12px 14px;
        font-family: 'Plus Jakarta Sans', 'Noto Sans Sinhala', sans-serif;
        font-size: 0.88rem;
        line-height: 1.55;
        color: #141413;
        resize: vertical;
        box-sizing: border-box;
    }}

    .quick-grid-title {{
        font-size: 0.8rem;
        font-weight: 800;
        color: #5E5D59;
        margin-top: 4px;
    }}

    .mini-slide-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
        gap: 8px;
        max-height: 200px;
        overflow-y: auto;
        padding: 2px;
    }}

    .mini-slide-btn {{
        background: #FFFFFF;
        border: 1px solid rgba(20, 20, 19, 0.1);
        border-radius: 10px;
        padding: 8px;
        text-align: left;
        cursor: pointer;
        transition: all 0.14s ease;
    }}
    .mini-slide-btn:hover {{
        border-color: #141413;
        transform: translateY(-1px);
    }}
    .mini-slide-btn span {{
        display: block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        color: #FF5A36;
    }}
    .mini-slide-btn p {{
        font-size: 0.72rem;
        font-weight: 600;
        color: #141413;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 2px;
    }}

    /* MOBILE RESPONSIVE TWEAKS */
    @media (max-width: 640px) {{
        .studio-titlebar {{
            padding: 11px 13px;
        }}
        .studio-bar-title {{
            font-size: 0.76rem;
            width: 100%;
        }}
        .studio-actions {{
            width: 100%;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
        }}
        .woday-btn {{
            width: 100%;
            padding: 8px 10px;
            font-size: 0.72rem;
        }}
        .inspector-stage {{
            padding: 10px;
            border-radius: 16px;
        }}
        .stage-nav-bar .woday-btn {{
            width: auto;
            padding: 6px 12px;
        }}
        .social-panel {{
            padding: 13px;
        }}
        .caption-textarea {{
            min-height: 210px;
            font-size: 0.82rem;
        }}
    }}
</style>
</head>
<body>

<div class="studio-window">
    <div class="studio-titlebar">
        <div class="macos-dots">
            <span class="dot dot-r"></span>
            <span class="dot dot-y"></span>
            <span class="dot dot-g"></span>
            <span class="studio-bar-title" style="margin-left:6px;">NIWNOTES Studio — {html.escape(topic)}</span>
            <span class="studio-badge">{tpl_style_badge}</span>
        </div>
        <div class="studio-actions">
            <button class="woday-btn" onclick="downloadCurrentSlidePNG()" id="dl-single-btn">
                Download Slide (.PNG)
            </button>
            <button class="woday-btn woday-btn-primary" onclick="downloadAllSlidesZIP()" id="dl-zip-btn">
                Export All {total_pages} (.ZIP)
            </button>
        </div>
    </div>

    <div class="studio-body">
        <div>
            <div class="thumb-strip">
                {thumbs_html}
            </div>

            <div class="inspector-stage">
                <div class="inspector-viewport" id="inspector-viewport">
                    <div class="inspector-scale-wrap" id="live-inspector-slot"></div>
                </div>

                <div class="stage-nav-bar">
                    <button class="woday-btn" onclick="stepSlide(-1)">Previous</button>
                    <span class="stage-counter" id="stage-counter-label">SLIDE 01 / {total_pages:02d}</span>
                    <button class="woday-btn" onclick="stepSlide(1)">Next</button>
                </div>
            </div>
        </div>

        <div class="social-panel">
            <div class="social-header">
                <span class="social-title">LinkedIn & Facebook Study Caption</span>
                <span class="social-lang-tag">{lang_badge}</span>
            </div>

            <textarea class="caption-textarea" id="social-caption-box">{escaped_caption}</textarea>

            <button class="woday-btn woday-btn-primary" onclick="copyCaptionText()" id="copy-caption-btn" style="width:100%;">
                Copy Social Caption to Clipboard
            </button>

            <div class="quick-grid-title">Quick Slide Jumper ({total_pages} Pages)</div>
            <div class="mini-slide-grid">
                {"".join(
                    f'<button class="mini-slide-btn" onclick="selectSlide({i + 1})"><span>PAGE {i + 1:02d}</span><p>{html.escape(getattr(s, "title", f"Slide {i + 1}"))}</p></button>'
                    for i, s in enumerate(slide_list)
                )}
            </div>
        </div>
    </div>
</div>

<div class="offscreen-deck" id="offscreen-deck">
    {slides_deck_html}
</div>

<script>
    let currentSlide = 1;
    const totalSlides = {total_pages};
    const fileSlug = "{safe_slug}";

    function updateInspectorScale() {{
        const viewport = document.getElementById('inspector-viewport');
        const scaleWrap = document.getElementById('live-inspector-slot');
        if (!viewport || !scaleWrap) return;
        const vw = viewport.clientWidth;
        if (vw <= 0) return;
        const scale = vw / 1000;
        scaleWrap.style.transform = `scale(${{scale}})`;
        viewport.style.height = `${{Math.round(1250 * scale)}}px`;
    }}

    function selectSlide(pageNumber) {{
        if (pageNumber < 1) pageNumber = totalSlides;
        if (pageNumber > totalSlides) pageNumber = 1;
        currentSlide = pageNumber;

        const sourceNode = document.getElementById('nc-slide-' + currentSlide);
        const slot = document.getElementById('live-inspector-slot');
        if (sourceNode && slot) {{
            slot.innerHTML = '';
            const clone = sourceNode.cloneNode(true);
            clone.id = 'nc-slide-preview-active';
            slot.appendChild(clone);
        }}

        document.getElementById('stage-counter-label').textContent =
            'SLIDE ' + String(currentSlide).padStart(2, '0') + ' / ' + String(totalSlides).padStart(2, '0');

        for (let i = 1; i <= totalSlides; i++) {{
            const btn = document.getElementById('thumb-btn-' + i);
            if (btn) {{
                if (i === currentSlide) {{
                    btn.classList.add('active');
                    btn.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
                }} else {{
                    btn.classList.remove('active');
                }}
            }}
        }}
        updateInspectorScale();
    }}

    function stepSlide(delta) {{
        selectSlide(currentSlide + delta);
    }}

    function copyCaptionText() {{
        const box = document.getElementById('social-caption-box');
        const btn = document.getElementById('copy-caption-btn');
        box.select();
        navigator.clipboard.writeText(box.value);
        const oldText = btn.textContent;
        btn.textContent = 'Copied to Clipboard!';
        setTimeout(() => {{ btn.textContent = oldText; }}, 1800);
    }}

    async function downloadCurrentSlidePNG() {{
        const btn = document.getElementById('dl-single-btn');
        const oldText = btn.textContent;
        btn.textContent = 'Rendering PNG...';
        try {{
            await document.fonts.ready;
            const node = document.getElementById('nc-slide-' + currentSlide);
            const dataUrl = await htmlToImage.toPng(node, {{
                width: 1000,
                height: 1250,
                pixelRatio: 1.5,
                cacheBust: true
            }});
            const link = document.createElement('a');
            link.download = `${{fileSlug}}_Slide_${{String(currentSlide).padStart(2, '0')}}.png`;
            link.href = dataUrl;
            link.click();
        }} catch (e) {{
            console.error(e);
        }} finally {{
            btn.textContent = oldText;
        }}
    }}

    async function downloadAllSlidesZIP() {{
        const btn = document.getElementById('dl-zip-btn');
        const oldText = btn.textContent;
        try {{
            await document.fonts.ready;
            const zip = new JSZip();
            for (let i = 1; i <= totalSlides; i++) {{
                btn.textContent = `Rendering ${{i}}/${{totalSlides}}...`;
                const node = document.getElementById('nc-slide-' + i);
                const dataUrl = await htmlToImage.toPng(node, {{
                    width: 1000,
                    height: 1250,
                    pixelRatio: 1.5,
                    cacheBust: true
                }});
                const base64Data = dataUrl.split(',')[1];
                zip.file(`${{fileSlug}}_Slide_${{String(i).padStart(2, '0')}}.png`, base64Data, {{ base64: true }});
            }}
            const captionText = document.getElementById('social-caption-box').value;
            zip.file(`${{fileSlug}}_Social_Caption.txt`, captionText);

            btn.textContent = 'Packing ZIP...';
            const content = await zip.generateAsync({{ type: 'blob' }});
            const link = document.createElement('a');
            link.download = `${{fileSlug}}_NIWNOTES_${{totalSlides}}Pages.zip`;
            link.href = URL.createObjectURL(content);
            link.click();
        }} catch (e) {{
            console.error(e);
        }} finally {{
            btn.textContent = oldText;
        }}
    }}

    // Touch swipe support on mobile slide viewport
    (function initTouchSwipe() {{
        const vp = document.getElementById('inspector-viewport');
        if (!vp) return;
        let startX = 0;
        vp.addEventListener('touchstart', (e) => {{
            if (e.changedTouches && e.changedTouches.length > 0) {{
                startX = e.changedTouches[0].screenX;
            }}
        }}, {{ passive: true }});
        vp.addEventListener('touchend', (e) => {{
            if (e.changedTouches && e.changedTouches.length > 0) {{
                const endX = e.changedTouches[0].screenX;
                const diff = startX - endX;
                if (Math.abs(diff) > 45) {{
                    stepSlide(diff > 0 ? 1 : -1);
                }}
            }}
        }}, {{ passive: true }});
    }})();

    window.addEventListener('resize', updateInspectorScale);
    window.addEventListener('orientationchange', updateInspectorScale);
    if (window.ResizeObserver) {{
        const ro = new ResizeObserver(updateInspectorScale);
        const vp = document.getElementById('inspector-viewport');
        if (vp) ro.observe(vp);
    }}

    selectSlide(1);
    requestAnimationFrame(updateInspectorScale);
</script>
</body>
</html>
"""


# =====================================================================
# 6. STANDALONE & CLI COMPATIBILITY EXPORT
# =====================================================================
def render_all_pages(guide: Any, author: str = "@Student", output_dir: str = "output"):
    """Saves the generated study guide HTML and caption for CLI use (main.py)."""
    os.makedirs(output_dir, exist_ok=True)
    html_content = build_interactive_studio_html(
        study_data=guide,
        topic=getattr(guide, "topic", "Handwritten_Notes"),
        subject_category="Computer Science",
    )
    with open(os.path.join(output_dir, "notes_studio.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    caption_text = getattr(guide, "social_caption", "")
    if caption_text:
        with open(os.path.join(output_dir, "caption.txt"), "w", encoding="utf-8") as f:
            f.write(caption_text)

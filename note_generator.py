import os
import re
import time
import html
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from google.genai import types
from dotenv import load_dotenv

from trend_agent import get_genai_client, get_working_models

load_dotenv()


# =====================================================================
# 1. STRUCTURED PYDANTIC SCHEMAS FOR GEMINI
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
# 2. HANDWRITTEN NOTEBOOK TEMPLATES
# =====================================================================
NOTE_TEMPLATES: Dict[str, Dict] = {
    "classic_cream": {
        "name": "Classic Cream Lined",
        "short_name": "Classic Cream",
        "badge": "Best Seller",
        "desc": "Warm academic notebook paper with crimson margin and yellow highlighter.",
    },
    "dark_neon": {
        "name": "Obsidian Cyber Dark",
        "short_name": "Obsidian Dark",
        "badge": "High Contrast",
        "desc": "Deep slate dotted grid with cyan & emerald neon technical ink.",
    },
    "blueprint_grid": {
        "name": "Engineering Blueprint",
        "short_name": "Blueprint Grid",
        "badge": "STEM Favorite",
        "desc": "Crisp Cobalt architect graph paper with technical blue ink.",
    },
    "cornell_academic": {
        "name": "Cornell Exam Prep",
        "short_name": "Cornell Exam",
        "badge": "Exam Ready",
        "desc": "Structured ivory study sheet with royal purple accents.",
    },
}


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
# 3. LANGUAGE INSTRUCTIONS & PARALLEL AI GENERATION
# =====================================================================
def _build_language_instructions(language: str, include_caption: bool) -> str:
    if language == "Sinhala_Mix":
        caption_rule = (
            """
        SOCIAL MEDIA CAPTION RULES (MUST BE IN SINHALA + ENGLISH KUPPI MIX):
        - Write the LinkedIn/Facebook `social_caption` in the exact same natural Sri Lankan University Sinhala + English mix.
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
       - `bullet_points`: Exactly 3 bullet points, 12-18 words each. Wrap 1-2 key terms per bullet in **double asterisks** for yellow marker highlighting.
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
# 4. INSTANT BROWSER-NATIVE SKETCHNOTE STUDIO & CLIENT-SIDE GPU EXPORT
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
) -> str:
    fields = _extract_slide_fields(slide, idx)
    bullets_html = "".join(
        f'<li class="nc-bullet-item"><span class="nc-bullet-dot">0{i + 1}</span>'
        f'<div class="nc-bullet-text">{_format_inline_highlights(b)}</div></li>'
        for i, b in enumerate(fields["bullet_points"])
    )

    steps_html = ""
    for i, (lbl, dtl) in enumerate(fields["diagram_steps"]):
        steps_html += f"""
        <div class="nc-step-card">
            <div class="nc-step-badge">0{i + 1} {html.escape(str(lbl))}</div>
            <div class="nc-step-detail">{_format_inline_highlights(dtl)}</div>
        </div>
        """

    return f"""
    <div class="nc-canvas" id="nc-slide-{fields['page_number']}" data-page="{fields['page_number']}">
        <div class="nc-margin-line"></div>
        <div class="nc-inner">
            <div class="nc-topbar">
                <div class="nc-subject-pill">NIWNOTES  //  {html.escape(subject_category.upper())}</div>
                <div class="nc-page-pill">PAGE {fields['page_number']:02d} OF {total_pages:02d}</div>
            </div>

            <div class="nc-topic-kicker">{html.escape(topic)}</div>
            <h1 class="nc-title">{html.escape(fields['title'])}</h1>

            <div class="nc-summary-banner">
                <span class="nc-summary-tag">KEY IDEA</span>
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
                    <span class="nc-protip-label">EXAM / PRO TIP</span>
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
    template_key: str = "classic_cream",
    subject_category: str = "AI & Machine Learning",
    language: str = "Sinhala_Mix",
    pages: Optional[List[Any]] = None,
    caption: str = "",
    **kwargs,
) -> str:
    """
    Renders the entire multi-page handwritten note studio directly in the user's browser
    with 0ms server-side rendering wait, responsive mobile scaling, and GPU-accelerated
    1000x1250 PNG & ZIP export.
    Supports both (study_data=...) and (pages=..., caption=...) calling conventions.
    """
    if study_data is not None:
        slide_list = getattr(study_data, "slides", None) or getattr(
            study_data, "pages", []
        )
        social_caption_text = getattr(study_data, "social_caption", "") or caption
    else:
        slide_list = pages or []
        social_caption_text = caption

    theme_css_map = {
        "classic_cream": """
            --paper-bg: #FDFBF7;
            --paper-grid: repeating-linear-gradient(to bottom, transparent 0px, transparent 31px, rgba(148, 163, 184, 0.24) 32px);
            --paper-grid-size: 100% 32px;
            --margin-line: rgba(239, 68, 68, 0.35);
            --ink-primary: #0F172A;
            --ink-secondary: #334155;
            --ink-accent: #EA580C;
            --banner-bg: #FFFBEB;
            --banner-border: #F59E0B;
            --hl-bg: #FEF08A;
            --hl-ink: #713F12;
            --card-bg: #FFFFFF;
            --card-border: #1E293B;
            --step-bg: #FFF7ED;
            --protip-bg: #F1F5F9;
        """,
        "dark_neon": """
            --paper-bg: #0F172A;
            --paper-grid: radial-gradient(#334155 1.25px, transparent 1.25px);
            --paper-grid-size: 24px 24px;
            --margin-line: rgba(56, 189, 248, 0.28);
            --ink-primary: #F8FAFC;
            --ink-secondary: #CBD5E1;
            --ink-accent: #38BDF8;
            --banner-bg: rgba(16, 185, 129, 0.14);
            --banner-border: #10B981;
            --hl-bg: rgba(56, 189, 248, 0.25);
            --hl-ink: #E0F2FE;
            --card-bg: #1E293B;
            --card-border: #38BDF8;
            --step-bg: #0F172A;
            --protip-bg: #1E293B;
        """,
        "blueprint_grid": """
            --paper-bg: #EFF6FF;
            --paper-grid: linear-gradient(to right, rgba(191, 219, 254, 0.55) 1px, transparent 1px),
                          linear-gradient(to bottom, rgba(191, 219, 254, 0.55) 1px, transparent 1px);
            --paper-grid-size: 24px 24px;
            --margin-line: rgba(37, 99, 235, 0.28);
            --ink-primary: #1E3A8A;
            --ink-secondary: #1E40AF;
            --ink-accent: #2563EB;
            --banner-bg: #DBEAFE;
            --banner-border: #2563EB;
            --hl-bg: #BFDBFE;
            --hl-ink: #1E3A8A;
            --card-bg: #FFFFFF;
            --card-border: #1E3A8A;
            --step-bg: #EFF6FF;
            --protip-bg: #DBEAFE;
        """,
        "cornell_academic": """
            --paper-bg: #FAF8F5;
            --paper-grid: repeating-linear-gradient(to bottom, transparent 0px, transparent 31px, rgba(214, 211, 209, 0.45) 32px);
            --paper-grid-size: 100% 32px;
            --margin-line: rgba(124, 58, 237, 0.32);
            --ink-primary: #1C1917;
            --ink-secondary: #44403C;
            --ink-accent: #7C3AED;
            --banner-bg: #F3E8FF;
            --banner-border: #7C3AED;
            --hl-bg: #E9D5FF;
            --hl-ink: #581C87;
            --card-bg: #FFFFFF;
            --card-border: #4C1D95;
            --step-bg: #FAF5FF;
            --protip-bg: #F5F5F4;
        """,
    }
    selected_theme_vars = theme_css_map.get(template_key, theme_css_map["classic_cream"])
    total_pages = len(slide_list)
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)[:35] or "NIWNOTES"

    slides_deck_html = "\n".join(
        _build_slide_card_html(s, total_pages, topic, subject_category, idx=i + 1)
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

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Kalam:wght@400;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Noto+Sans+Sinhala:wght@500;600;700;800&family=JetBrains+Mono:wght@600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>

<style>
    :root {{
        {selected_theme_vars}
    }}

    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}

    body {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background: transparent;
        color: #141413;
        padding: 4px 2px 24px 2px;
        overflow-x: hidden;
    }}

    /* WODAY STUDIO SHELL */
    .studio-window {{
        background: #FFFFFF;
        border: 1px solid rgba(20, 20, 19, 0.09);
        border-radius: 24px;
        box-shadow: 0 12px 34px -8px rgba(20, 20, 19, 0.06);
        overflow: hidden;
    }}

    .studio-titlebar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 22px;
        background: #F7F6F2;
        border-bottom: 1px solid rgba(20, 20, 19, 0.08);
        flex-wrap: wrap;
        gap: 12px;
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

    .studio-actions {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }}

    .woday-btn {{
        appearance: none;
        border: 1px solid rgba(20, 20, 19, 0.14);
        background: #FFFFFF;
        color: #141413;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 0.8rem;
        padding: 9px 15px;
        border-radius: 999px;
        cursor: pointer;
        transition: all 0.16s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
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

    /* WORKSPACE GRID */
    .studio-body {{
        display: grid;
        grid-template-columns: 1.25fr 0.95fr;
        gap: 24px;
        padding: 22px;
    }}

    @media (max-width: 960px) {{
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
        padding-bottom: 10px;
        margin-bottom: 14px;
        scrollbar-width: thin;
        -webkit-overflow-scrolling: touch;
    }}

    .thumb-pill {{
        flex: 0 0 auto;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 13px;
        border-radius: 12px;
        border: 1px solid rgba(20, 20, 19, 0.1);
        background: #F7F6F2;
        color: #5E5D59;
        cursor: pointer;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.78rem;
        font-weight: 700;
        transition: all 0.15s ease;
        max-width: 210px;
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

    /* STAGE VIEWPORT (RESPONSIVE DYNAMIC SCALING OF 1000x1250 CANVAS) */
    .inspector-stage {{
        background: #F3F2EE;
        border: 1px solid rgba(20, 20, 19, 0.08);
        border-radius: 20px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}

    .inspector-viewport {{
        width: 100%;
        max-width: 480px;
        height: 600px;
        position: relative;
        overflow: hidden;
        border-radius: 14px;
        box-shadow: 0 16px 38px -10px rgba(15, 23, 42, 0.22);
        background: var(--paper-bg);
    }}

    .inspector-scale-wrap {{
        width: 1000px;
        height: 1250px;
        transform: scale(0.48);
        transform-origin: top left;
    }}

    .stage-nav-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        max-width: 480px;
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
    }}

    .nc-margin-line {{
        position: absolute;
        top: 0;
        bottom: 0;
        left: 78px;
        width: 2.5px;
        background: var(--margin-line);
        z-index: 1;
    }}

    .nc-inner {{
        position: relative;
        z-index: 2;
        padding: 48px 56px 44px 104px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}

    .nc-topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 2px dashed rgba(148, 163, 184, 0.35);
        padding-bottom: 14px;
    }}

    .nc-subject-pill {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 700;
        color: var(--ink-accent);
        letter-spacing: 0.04em;
    }}

    .nc-page-pill {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 700;
        background: var(--card-bg);
        color: var(--ink-primary);
        border: 2px solid var(--card-border);
        padding: 5px 14px;
        border-radius: 999px;
        box-shadow: 3px 3px 0px var(--card-border);
    }}

    .nc-topic-kicker {{
        font-family: 'Caveat', cursive;
        font-size: 28px;
        font-weight: 700;
        color: var(--ink-accent);
        margin-top: 6px;
    }}

    .nc-title {{
        font-family: 'Plus Jakarta Sans', 'Noto Sans Sinhala', sans-serif;
        font-size: 44px;
        font-weight: 800;
        line-height: 1.15;
        color: var(--ink-primary);
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }}

    .nc-summary-banner {{
        background: var(--banner-bg);
        border-left: 6px solid var(--banner-border);
        border-radius: 14px;
        padding: 16px 20px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
    }}

    .nc-summary-tag {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 700;
        background: var(--banner-border);
        color: #FFFFFF;
        padding: 4px 9px;
        border-radius: 6px;
        flex-shrink: 0;
        margin-top: 3px;
    }}

    .nc-summary-text {{
        font-family: 'Kalam', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 24px;
        font-weight: 600;
        line-height: 1.42;
        color: var(--ink-primary);
    }}

    .nc-bullet-list {{
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin: 8px 0;
    }}

    .nc-bullet-item {{
        display: flex;
        align-items: flex-start;
        gap: 16px;
        background: var(--card-bg);
        border: 2px solid rgba(148, 163, 184, 0.28);
        border-radius: 16px;
        padding: 16px 20px;
    }}

    .nc-bullet-dot {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 700;
        background: var(--ink-accent);
        color: #FFFFFF;
        min-width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
    }}

    .nc-bullet-text {{
        font-family: 'Kalam', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 24px;
        font-weight: 500;
        line-height: 1.46;
        color: var(--ink-primary);
    }}

    .hl-mark {{
        background: var(--hl-bg);
        color: var(--hl-ink);
        padding: 1px 7px;
        border-radius: 6px;
        font-weight: 700;
    }}

    /* 3-STEP VISUAL ARCHITECTURE FLOW BOX */
    .nc-diagram-box {{
        background: var(--card-bg);
        border: 2.5px solid var(--card-border);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 5px 5px 0px var(--card-border);
    }}

    .nc-diagram-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 14px;
    }}

    .nc-diagram-dot {{
        width: 12px;
        height: 12px;
        border-radius: 999px;
        background: var(--ink-accent);
    }}

    .nc-diagram-title {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 17px;
        font-weight: 700;
        color: var(--ink-primary);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    .nc-diagram-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
    }}

    .nc-step-card {{
        background: var(--step-bg);
        border: 2px solid var(--ink-accent);
        border-radius: 12px;
        padding: 12px 14px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 0;
    }}

    .nc-step-badge {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        font-weight: 700;
        color: var(--ink-accent);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .nc-step-detail {{
        font-family: 'Kalam', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 20px;
        font-weight: 600;
        line-height: 1.35;
        color: var(--ink-primary);
    }}

    .nc-footer-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        padding-top: 10px;
    }}

    .nc-protip-box {{
        flex: 1;
        background: var(--protip-bg);
        border: 2px solid var(--card-border);
        border-radius: 12px;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .nc-protip-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        font-weight: 700;
        background: var(--ink-primary);
        color: var(--paper-bg);
        padding: 4px 8px;
        border-radius: 6px;
        white-space: nowrap;
        flex-shrink: 0;
    }}

    .nc-protip-text {{
        font-family: 'Kalam', 'Noto Sans Sinhala', cursive, sans-serif;
        font-size: 20px;
        font-weight: 600;
        color: var(--ink-primary);
        line-height: 1.35;
    }}

    .nc-watermark {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        font-weight: 700;
        color: var(--ink-secondary);
        white-space: nowrap;
    }}

    /* RIGHT COLUMN: SOCIAL CAPTION & EXPORT KIT */
    .social-panel {{
        background: #F7F6F2;
        border: 1px solid rgba(20, 20, 19, 0.08);
        border-radius: 20px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 14px;
    }}

    .social-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }}

    .social-title {{
        font-size: 0.95rem;
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
        min-height: 290px;
        border: 1px solid rgba(20, 20, 19, 0.12);
        border-radius: 14px;
        background: #FFFFFF;
        padding: 14px 16px;
        font-family: 'Plus Jakarta Sans', 'Noto Sans Sinhala', sans-serif;
        font-size: 0.88rem;
        line-height: 1.6;
        color: #141413;
        resize: vertical;
    }}

    .quick-grid-title {{
        font-size: 0.82rem;
        font-weight: 800;
        color: #5E5D59;
        margin-top: 6px;
    }}

    .mini-slide-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
        gap: 8px;
        max-height: 210px;
        overflow-y: auto;
        padding: 4px;
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
        font-size: 0.7rem;
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

    /* MOBILE VIEW BREAKPOINTS */
    @media (max-width: 640px) {{
        .studio-titlebar {{
            padding: 12px 14px;
        }}
        .studio-bar-title {{
            font-size: 0.76rem;
            width: 100%;
        }}
        .studio-actions {{
            width: 100%;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }}
        .woday-btn {{
            width: 100%;
            padding: 8px 10px;
            font-size: 0.74rem;
        }}
        .inspector-stage {{
            padding: 10px;
            border-radius: 16px;
        }}
        .stage-nav-bar .woday-btn {{
            width: auto;
            padding: 7px 13px;
        }}
        .social-panel {{
            padding: 14px;
        }}
        .caption-textarea {{
            min-height: 220px;
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
            <span class="studio-bar-title" style="margin-left:8px;">NIWNOTES Studio — {html.escape(topic)} ({total_pages} Slides)</span>
        </div>
        <div class="studio-actions">
            <button class="woday-btn" onclick="downloadCurrentSlidePNG()" id="dl-single-btn">
                Download Current (.PNG)
            </button>
            <button class="woday-btn woday-btn-primary" onclick="downloadAllSlidesZIP()" id="dl-zip-btn">
                Download All {total_pages} Slides (.ZIP)
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
                <span class="social-title">LinkedIn & Facebook Study Post Caption</span>
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
        btn.textContent = 'Copied to Clipboard';
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
    if (window.ResizeObserver) {{
        const ro = new ResizeObserver(updateInspectorScale);
        const vp = document.getElementById('inspector-viewport');
        if (vp) ro.observe(vp);
    }}

    selectSlide(1);
</script>
</body>
</html>
"""
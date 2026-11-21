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
# 1. EMBEDDED ASSETS (AUTHENTIC FONTS & REAL PAPER TEXTURES)
# =====================================================================
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# 1.1 Authentic Sinhala + English Handwriting Font
FONT_FILE_PATH = os.path.join(ASSETS_DIR, "FontoshanHandwrite-Regular.ttf")
_FONT_B64 = ""
if os.path.exists(FONT_FILE_PATH):
    try:
        with open(FONT_FILE_PATH, "rb") as _f:
            _FONT_B64 = base64.b64encode(_f.read()).decode("ascii")
    except Exception as _err:
        print(f"Warning: Could not load Fontoshan font file: {_err}")

# 1.2 Real Ruled Notebook Paper Texture (Base64)
RULED_PAPER_PATH = os.path.join(ASSETS_DIR, "real_ruled_paper.jpg")
_RULED_PAPER_B64 = ""
if os.path.exists(RULED_PAPER_PATH):
    try:
        with open(RULED_PAPER_PATH, "rb") as _f:
            _RULED_PAPER_B64 = base64.b64encode(_f.read()).decode("ascii")
    except Exception as _err:
        print(f"Warning: Could not load ruled paper texture: {_err}")

# 1.3 Real Kraft / Quad Grid Paper Texture (Base64)
KRAFT_PAPER_PATH = os.path.join(ASSETS_DIR, "real_kraft_paper.jpg")
_KRAFT_PAPER_B64 = ""
if os.path.exists(KRAFT_PAPER_PATH):
    try:
        with open(KRAFT_PAPER_PATH, "rb") as _f:
            _KRAFT_PAPER_B64 = base64.b64encode(_f.read()).decode("ascii")
    except Exception as _err:
        print(f"Warning: Could not load kraft paper texture: {_err}")


# =====================================================================
# 2. EMOJI STRIPPER UTILITY (ENSURES PURE HANDWRITING)
# =====================================================================
def strip_emojis(text: str) -> str:
    """Removes any unicode emojis, pictographs, or dingbats from text."""
    if not text:
        return ""
    emoji_pattern = re.compile(
        r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\uFE00-\uFE0F]",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", str(text))
    return re.sub(r" {2,}", " ", cleaned).strip()


# =====================================================================
# 3. STRUCTURED PYDANTIC SCHEMAS FOR GEMINI
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
# 4. HANDWRITTEN NOTEBOOK TEMPLATES (2 REALISTIC + 2 DIGITAL)
# =====================================================================
NOTE_TEMPLATES: Dict[str, Dict] = {
    "classic_ruled": {
        "name": "Classic Ruled Paper",
        "short_name": "Ruled Notebook",
        "category": "Realistic",
        "badge": "Physical Paper",
        "desc": "Real photographic college-ruled paper with blue ruling, red margin, 3 binder punch holes, and ballpoint ink.",
    },
    "vintage_kraft": {
        "name": "Engineering Quad Grid",
        "short_name": "Quad Grid Pad",
        "category": "Realistic",
        "badge": "Physical Paper",
        "desc": "Real photographic 5mm quad grid kraft pad with sepia ink, scotch tape note, and hand-sketched diagrams.",
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
# 5. LANGUAGE INSTRUCTIONS & PARALLEL AI GENERATION
# =====================================================================
def _build_language_instructions(language: str, include_caption: bool) -> str:
    if language == "Sinhala_Mix":
        caption_rule = (
            """
        SOCIAL MEDIA CAPTION RULES (MUST BE IN PROPER SINHALA SCRIPT + ENGLISH TECHNICAL WORDS):
        - Write the LinkedIn/Facebook `social_caption` in natural Sri Lankan University Sinhala script (සිංහල අක්ෂර) with English technical terms.
        - Structure:
          1. Strong Sinhala hook line about why this topic matters for IT/Engineering students (in Sinhala script).
          2. 3-4 short bullet points summarizing what is inside this note deck (in Sinhala script).
          3. Friendly Call-To-Action asking fellow students to Save/Share and comment their thoughts (in Sinhala script).
          4. 5 relevant hashtags (#NIWNOTES #Kuppiya #SriLankaTech #UniversityLife #TechNotes).
        - Do NOT use Singlish. Do NOT use emojis anywhere in the caption.
            """
            if include_caption
            else ""
        )
        return f"""
        LANGUAGE MODE: REAL SINHALA SCRIPT WITH ENGLISH TECHNICAL WORDS (Sinhala_Mix).
        
        CRITICAL SCRIPT REQUIREMENT (STRICTLY ENFORCED):
        - You MUST write all Sinhala explanations in REAL SINHALA UNICODE SCRIPT (සිංහල අකුරු - e.g., "සරලවම කිව්වොත් මේකෙන් කරන්නේ...", "විභාග ප්‍රශ්න වලට නිතරම අහන...").
        - ABSOLUTELY NEVER WRITE IN SINGLISH (Latin / English letters for Sinhala words like "Agentic AI kiyanne LLM ekak thawa agent kenek wage task ekak karana eka"). SINGLISH IS STRICTLY FORBIDDEN!
        - Keep `title`, `diagram_title`, and `diagram_steps.step_label` in crisp English.
        - In `summary_banner`, `bullet_points`, `diagram_steps.step_detail`, and `pro_tip`:
          Write full conversational sentences in PROPER SINHALA SCRIPT (සිංහල අකුරු), while retaining core technical terminology in English letters (e.g. `LLM`, `Agentic AI`, `Autonomous Agents`, `Multi-Agent Orchestration`, `Vector Database`, `Context`, `Pipeline`, `Latency`, `Cache`).

        CORRECT EXAMPLES (FOLLOW THIS EXACT STYLE):
        - Bullet 1: "**Autonomous Agents** කියන්නේ සාමාන්‍ය Chatbot එකක් නෙමෙයි, දීපු Goal එකකට අනුව තනිවම තීරණ අරගෙන complex tasks automate කරන systems වලටයි."
        - Bullet 2: "**Multi-Agent Orchestration** මගින් විශේෂිත task එකකට වෙන වෙනම agents ලා set එකක් සම්බන්ධ කරලා සම්පූර්ණ workflow එකම run කරන්න පුළුවන්."
        - Summary Banner: "Agentic AI කියන්නේ **LLM Core** එකක් dynamic tools සහ autonomous reasoning loops සමග ක්‍රියාත්මක වන ආකාරයයි."
        - Pro Tip: "විභාගයේදී **Agent Execution Loop** එක විස්තර කරන විට Plan, Act, සහ Feedback stages පැහැදිලිව සඳහන් කරන්න."

        FORBIDDEN SINGLISH EXAMPLES (NEVER GENERATE THIS):
        - "Meka simple chat ekak nemei, Autonomous Agents use karala complex task automate karanna puluwan system ekak." (REJECTED!)
        - "Agentic AI kiyanne LLM ekak thawa agent kenek wage task ekak karana eka." (REJECTED!)

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
                        # Clean any stray emojis
                        s.title = strip_emojis(s.title)
                        s.summary_banner = strip_emojis(s.summary_banner)
                        s.bullet_points = [strip_emojis(b) for b in s.bullet_points]
                        s.diagram_title = strip_emojis(s.diagram_title)
                        for stp in s.diagram_steps:
                            stp.step_label = strip_emojis(stp.step_label)
                            stp.step_detail = strip_emojis(stp.step_detail)
                        s.pro_tip = strip_emojis(s.pro_tip)

                    caption = getattr(parsed, "social_caption", "") if include_caption else ""
                    caption = strip_emojis(caption)
                    return slides, caption
            except Exception as err:
                last_error = err
                err_str = str(err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    time.sleep(0.6)
                continue

    raise RuntimeError(f"Failed to synthesize batch {batch_index + 1}. Last error: {last_error}")


# =====================================================================
# 6. EXTRA PAGE: HIGH-YIELD KEYWORD EXPLANATION & EXAM CHEAT-SHEET
# =====================================================================
def _synthesize_terminology_deep_dive_slide(
    all_slides: List[NotePage],
    topic: str,
    language: str,
    subject_category: str,
    page_num: int,
) -> NotePage:
    """
    Extracts all highlighted keywords across the generated study deck and synthesizes
    an extra high-yield technical glossary slide for student revision.
    """
    # Extract unique highlighted terms in order
    terms: List[str] = []
    for s in all_slides:
        for b in s.bullet_points:
            found = re.findall(r"\*\*(.+?)\*\*", b)
            for item in found:
                t_clean = strip_emojis(item).strip()
                if t_clean and t_clean not in terms:
                    terms.append(t_clean)

    # Pick distinct terms (preserving any extracted terms, and supplementing if needed)
    fallback_pool = [topic, "Architecture", "System Workflow", "Optimization"]
    combined_terms = [t for t in terms if t]
    for fb in fallback_pool:
        if fb not in combined_terms:
            combined_terms.append(fb)
    top_terms = combined_terms[:6]

    if language == "Sinhala_Mix":
        b1_term = top_terms[0] if len(top_terms) > 0 else "Core Concept"
        b2_term = top_terms[1] if len(top_terms) > 1 else "Mechanism"
        b3_term = top_terms[2] if len(top_terms) > 2 else "Optimization"

        bullets = [
            f"**{b1_term}**: මූලික න්‍යායික සංකල්පය වන අතර, පද්ධතියේ ප්‍රධාන කාර්යභාරය සහ දත්ත ගලායාම තීරණය කරයි.",
            f"**{b2_term}**: ප්‍රායෝගිකව ක්‍රියාත්මක වන ප්‍රධාන මෙහෙයුම් යාන්ත්‍රණය වන අතර, දෝෂ අවම කිරීමට අත්‍යවශ්‍ය වේ.",
            f"**{b3_term}**: විභාග ප්‍රශ්න වලට නිතර අසන ප්‍රධාන මාතෘකාවක් වන අතර, පද්ධතියේ කාර්යක්ෂමතාව සහ Latency පාලනය කරයි.",
        ]
        pro_tip = "විභාගයේදී මෙම Keywords නිවැරදිව සඳහන් කර System Trade-offs පැහැදිලි කිරීමෙන් උපරිම ලකුණු ලබාගත හැක."
        summary = "මෙම පාඩම් මාලාවේ Highlight කර ඇති ප්‍රධාන තාක්ෂණික වචන සහ විභාග සංකල්ප සාරාංශය."
    else:
        b1_term = top_terms[0] if len(top_terms) > 0 else "Core Concept"
        b2_term = top_terms[1] if len(top_terms) > 1 else "Mechanism"
        b3_term = top_terms[2] if len(top_terms) > 2 else "Optimization"

        bullets = [
            f"**{b1_term}**: Foundational theoretical concept defining the primary data contracts and operational boundaries.",
            f"**{b2_term}**: Core architectural execution mechanism responsible for deterministic reliability and scale.",
            f"**{b3_term}**: Frequently tested exam topic focused on system trade-offs, bottleneck mitigation, and latency limits.",
        ]
        pro_tip = "Exam Revision Rule: Always anchor your answers to core keywords and explicitly cite their system trade-offs."
        summary = "Comprehensive technical glossary and high-yield concept breakdown for exam & interview revision."

    return NotePage(
        page_number=page_num,
        title="Key Terminology Deep Dive",
        summary_banner=summary,
        bullet_points=bullets,
        diagram_title="Exam Recall & Concept Mental Model",
        diagram_steps=[
            DiagramStep(step_label="01 Concept", step_detail="Theoretical foundation & boundary"),
            DiagramStep(step_label="02 Mechanism", step_detail="Production execution flow"),
            DiagramStep(step_label="03 Tradeoffs", step_detail="Latency vs accuracy limits"),
        ],
        pro_tip=pro_tip,
    )


def generate_5_page_study_guide(
    topic: str,
    language: str = "Sinhala_Mix",
    api_key: str | None = None,
    subject_category: str = "AI & Machine Learning",
    num_pages: int = 5,
) -> StudyCarouselResponse:
    """
    Generates 5, 10, or 30 handwritten slides in parallel plus 1 extra high-yield
    terminology deep-dive revision page (e.g., 5+1=6 pages, 10+1=11 pages, 30+1=31 pages).
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
        # Synthesize extra terminology deep-dive page
        glossary_slide = _synthesize_terminology_deep_dive_slide(
            all_slides=slides,
            topic=topic,
            language=language,
            subject_category=subject_category,
            page_num=len(slides) + 1,
        )
        slides.append(glossary_slide)
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

    # Synthesize extra terminology deep-dive page
    glossary_slide = _synthesize_terminology_deep_dive_slide(
        all_slides=all_slides,
        topic=topic,
        language=language,
        subject_category=subject_category,
        page_num=len(all_slides) + 1,
    )
    all_slides.append(glossary_slide)

    for idx, slide in enumerate(all_slides, start=1):
        slide.page_number = idx

    return StudyCarouselResponse(slides=all_slides, social_caption=master_caption)


# =====================================================================
# 7. AUTHENTIC HAND-DRAWN TECHNICAL SKETCHES & DIAGRAMS (VARIED PER SLIDE)
# =====================================================================
def _render_authentic_handwritten_diagram(
    fields: dict,
    page_num: int,
    total_pages: int,
    norm_key: str,
) -> str:
    """
    Renders an organic, varied hand-sketched technical diagram tailored to the slide's
    actual step content. Eliminates repetitive generic graphs and makes every page
    look like an authentic student or engineering lecture note.
    """
    raw_title = fields.get("diagram_title", "Technical Architecture Flow")
    diag_title = html.escape(str(raw_title))
    steps = fields.get("diagram_steps", [])
    if not steps:
        return ""

    lbl1, dtl1 = steps[0] if len(steps) > 0 else ("Input", "Initial state & parameters")
    lbl2, dtl2 = steps[1] if len(steps) > 1 else ("Process", "Execution logic & transformation")
    lbl3, dtl3 = steps[2] if len(steps) > 2 else ("Output", "Deterministic verified result")

    lbl1_h, dtl1_h = html.escape(str(lbl1)), _format_inline_highlights(dtl1)
    lbl2_h, dtl2_h = html.escape(str(lbl2)), _format_inline_highlights(dtl2)
    lbl3_h, dtl3_h = html.escape(str(lbl3)), _format_inline_highlights(dtl3)

    is_glossary = "deep dive" in str(fields.get("title", "")).lower() or page_num == total_pages
    archetype_id = 6 if is_glossary else (((page_num - 1) % 5) + 1)

    # Archetype 1: Horizontal Pipeline Flow (Step 1 ──► Step 2 ──► Step 3)
    if archetype_id == 1:
        return f"""
        <div class="nc-paper-diagram-box">
            <div class="nc-pdiag-title">&#x2500;&#x2500; Fig 01: {diag_title} &#x2500;&#x2500;</div>
            <div class="nc-pdiag-flow-horizontal">
                <div class="nc-sketch-node">
                    <span class="nc-snode-num">&#9312; Step 1</span>
                    <div class="nc-snode-title">{lbl1_h}</div>
                    <div class="nc-snode-body">{dtl1_h}</div>
                </div>
                <div class="nc-sketch-arrow">
                    <svg width="34" height="20" viewBox="0 0 34 20" fill="none">
                        <path d="M2 10 C10 8 20 12 30 10 M24 4 L31 10 L24 16" stroke="var(--ink-accent)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="nc-sketch-node">
                    <span class="nc-snode-num">&#9313; Step 2</span>
                    <div class="nc-snode-title">{lbl2_h}</div>
                    <div class="nc-snode-body">{dtl2_h}</div>
                </div>
                <div class="nc-sketch-arrow">
                    <svg width="34" height="20" viewBox="0 0 34 20" fill="none">
                        <path d="M2 10 C10 8 20 12 30 10 M24 4 L31 10 L24 16" stroke="var(--ink-accent)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div class="nc-sketch-node">
                    <span class="nc-snode-num">&#9314; Step 3</span>
                    <div class="nc-snode-title">{lbl3_h}</div>
                    <div class="nc-snode-body">{dtl3_h}</div>
                </div>
            </div>
        </div>
        """

    # Archetype 2: Layered Component Architecture Stack (Tiers)
    elif archetype_id == 2:
        return f"""
        <div class="nc-paper-diagram-box">
            <div class="nc-pdiag-title">&#x2500;&#x2500; Fig 02: {diag_title} &#x2500;&#x2500;</div>
            <div class="nc-pdiag-stack-wrap">
                <div class="nc-sketch-tier">
                    <span class="nc-tier-badge">Tier 1: Frontend &amp; Input</span>
                    <span class="nc-tier-label">{lbl1_h}:</span>
                    <span class="nc-tier-detail">{dtl1_h}</span>
                </div>
                <div class="nc-tier-arrow-down">
                    <svg width="18" height="14" viewBox="0 0 18 14" fill="none">
                        <path d="M9 1 V11 M4 7 L9 12 L14 7" stroke="var(--ink-accent)" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="nc-sketch-tier nc-tier-core">
                    <span class="nc-tier-badge">Tier 2: Processing Engine</span>
                    <span class="nc-tier-label">{lbl2_h}:</span>
                    <span class="nc-tier-detail">{dtl2_h}</span>
                </div>
                <div class="nc-tier-arrow-down">
                    <svg width="18" height="14" viewBox="0 0 18 14" fill="none">
                        <path d="M9 1 V11 M4 7 L9 12 L14 7" stroke="var(--ink-accent)" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="nc-sketch-tier">
                    <span class="nc-tier-badge">Tier 3: Storage &amp; Output</span>
                    <span class="nc-tier-label">{lbl3_h}:</span>
                    <span class="nc-tier-detail">{dtl3_h}</span>
                </div>
            </div>
        </div>
        """

    # Archetype 3: Iterative Closed-Loop Cycle / Workflow Loop
    elif archetype_id == 3:
        return f"""
        <div class="nc-paper-diagram-box">
            <div class="nc-pdiag-title">&#x2500;&#x2500; Fig 03: {diag_title} (Execution Loop) &#x2500;&#x2500;</div>
            <div class="nc-pdiag-cycle-wrap">
                <div class="nc-cycle-top-row">
                    <div class="nc-sketch-node nc-cycle-node">
                        <span class="nc-snode-num">&#9312; Plan &amp; Reason</span>
                        <div class="nc-snode-title">{lbl1_h}</div>
                        <div class="nc-snode-body">{dtl1_h}</div>
                    </div>
                    <div class="nc-cycle-arrow-top">
                        <svg width="50" height="22" viewBox="0 0 50 22" fill="none">
                            <path d="M4 11 C18 4 32 4 46 11 M38 5 L47 12 L39 17" stroke="var(--ink-accent)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <div class="nc-sketch-node nc-cycle-node">
                        <span class="nc-snode-num">&#9313; Act &amp; Execute</span>
                        <div class="nc-snode-title">{lbl2_h}</div>
                        <div class="nc-snode-body">{dtl2_h}</div>
                    </div>
                </div>
                <div class="nc-cycle-return-row">
                    <svg width="100%" height="28" viewBox="0 0 460 28" fill="none">
                        <path d="M410 2 C410 22 280 24 230 24 C150 24 50 24 50 2 M44 8 L50 2 L56 7" stroke="var(--ink-primary)" stroke-width="2" stroke-dasharray="4,3" stroke-linecap="round"/>
                        <text x="160" y="20" font-family="'FontoshanHandwrite', cursive" font-size="14" fill="var(--ink-secondary)">&#x21bb; Feedback &amp; Verification Loop</text>
                    </svg>
                    <div class="nc-sketch-node nc-cycle-bottom-node">
                        <span class="nc-snode-num">&#9314; Evaluate &amp; Store:</span> <strong>{lbl3_h}</strong> &#8212; {dtl3_h}
                    </div>
                </div>
            </div>
        </div>
        """

    # Archetype 4: Decision Branching / Router Guardrail
    elif archetype_id == 4:
        return f"""
        <div class="nc-paper-diagram-box">
            <div class="nc-pdiag-title">&#x2500;&#x2500; Fig 04: {diag_title} &#x2500;&#x2500;</div>
            <div class="nc-pdiag-branch-wrap">
                <div class="nc-sketch-node nc-branch-input">
                    <span class="nc-snode-num">&#9312; Input / Trigger</span>
                    <div class="nc-snode-title">{lbl1_h}</div>
                    <div class="nc-snode-body">{dtl1_h}</div>
                </div>
                <div class="nc-branch-fork-svg">
                    <svg width="34" height="68" viewBox="0 0 34 68" fill="none">
                        <path d="M2 34 C14 34 18 16 30 16 M24 11 L31 16 L24 21" stroke="var(--ink-accent)" stroke-width="2.2" stroke-linecap="round"/>
                        <path d="M2 34 C14 34 18 52 30 52 M24 47 L31 52 L24 57" stroke="var(--ink-primary)" stroke-width="2.2" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="nc-branch-paths">
                    <div class="nc-sketch-node nc-branch-sub">
                        <span class="nc-snode-num">&#9313; Primary Execution:</span> <strong>{lbl2_h}</strong> &#8212; {dtl2_h}
                    </div>
                    <div class="nc-sketch-node nc-branch-sub nc-branch-fallback">
                        <span class="nc-snode-num">&#9314; Guardrail &amp; Fallback:</span> <strong>{lbl3_h}</strong> &#8212; {dtl3_h}
                    </div>
                </div>
            </div>
        </div>
        """

    # Archetype 5: Trade-Off & Deployment Balance Matrix
    elif archetype_id == 5:
        return f"""
        <div class="nc-paper-diagram-box">
            <div class="nc-pdiag-title">&#x2500;&#x2500; Fig 05: {diag_title} &#x2500;&#x2500;</div>
            <div class="nc-pdiag-matrix-wrap">
                <div class="nc-matrix-col">
                    <div class="nc-sketch-node nc-matrix-card">
                        <span class="nc-snode-num">&#9878; Performance &amp; Latency</span>
                        <div class="nc-snode-title">{lbl1_h}</div>
                        <div class="nc-snode-body">{dtl1_h}</div>
                    </div>
                </div>
                <div class="nc-matrix-divider">
                    <svg width="22" height="74" viewBox="0 0 22 74" fill="none">
                        <line x1="11" y1="2" x2="11" y2="72" stroke="var(--ink-secondary)" stroke-width="1.8" stroke-dasharray="3,3"/>
                        <text x="3" y="40" font-family="'FontoshanHandwrite', cursive" font-size="13" font-weight="bold" fill="var(--ink-accent)">VS</text>
                    </svg>
                </div>
                <div class="nc-matrix-col">
                    <div class="nc-sketch-node nc-matrix-card">
                        <span class="nc-snode-num">&#10004; Accuracy &amp; Reliability</span>
                        <div class="nc-snode-title">{lbl2_h}</div>
                        <div class="nc-snode-body">{dtl2_h}</div>
                    </div>
                </div>
            </div>
            <div class="nc-matrix-footer-note">
                <span class="nc-snode-num">&#9733; Deployment Rule:</span> <strong>{lbl3_h}</strong> &#8212; {dtl3_h}
            </div>
        </div>
        """

    # Archetype 6: Revision / Glossary Deep Dive Concept Cards
    else:
        return f"""
        <div class="nc-paper-diagram-box">
            <div class="nc-pdiag-title">&#x2500;&#x2500; Revision Recall Map: Core Concepts &#x2500;&#x2500;</div>
            <div class="nc-pdiag-flow-horizontal">
                <div class="nc-sketch-node">
                    <span class="nc-snode-num">&#9733; 01 Concept</span>
                    <div class="nc-snode-title">{lbl1_h}</div>
                    <div class="nc-snode-body">{dtl1_h}</div>
                </div>
                <div class="nc-sketch-node">
                    <span class="nc-snode-num">&#9881; 02 Execution</span>
                    <div class="nc-snode-title">{lbl2_h}</div>
                    <div class="nc-snode-body">{dtl2_h}</div>
                </div>
                <div class="nc-sketch-node">
                    <span class="nc-snode-num">&#9878; 03 Trade-offs</span>
                    <div class="nc-snode-title">{lbl3_h}</div>
                    <div class="nc-snode-body">{dtl3_h}</div>
                </div>
            </div>
        </div>
        """


# =====================================================================
# 8. HTML SLIDE BUILDER WITH AUTHENTIC PAPER CANVAS
# =====================================================================
def _format_inline_highlights(text: str) -> str:
    cleaned = strip_emojis(text)
    escaped = html.escape(str(cleaned or ""))
    return re.sub(
        r"\*\*(.+?)\*\*",
        r'<mark class="hl-mark">\1</mark>',
        escaped,
    )


def _extract_slide_fields(slide: Any, fallback_page_num: int) -> dict:
    """Safely extracts slide fields from either current or legacy NotePage objects."""
    page_number = getattr(slide, "page_number", fallback_page_num)
    title = strip_emojis(getattr(slide, "title", f"Concept Slide {page_number}"))
    summary_banner = strip_emojis(
        getattr(slide, "summary_banner", None)
        or getattr(slide, "highlight", None)
        or getattr(slide, "subtitle", "")
    )
    bullet_points = [
        strip_emojis(b)
        for b in (getattr(slide, "bullet_points", None) or getattr(slide, "key_points", []))
    ]
    diagram_title = strip_emojis(
        getattr(slide, "diagram_title", "System Architecture & Flow")
    )
    diagram_steps = getattr(slide, "diagram_steps", [])
    pro_tip = strip_emojis(
        getattr(slide, "pro_tip", None) or getattr(slide, "exam_note", "")
    )

    normalized_steps = []
    for idx, step in enumerate(diagram_steps[:3]):
        lbl = strip_emojis(getattr(step, "step_label", f"Step 0{idx + 1}"))
        dtl = strip_emojis(
            getattr(step, "step_detail", None) or getattr(step, "step_description", "")
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


def _build_realistic_slide_html(
    fields: dict,
    total_pages: int,
    topic: str,
    subject_category: str,
    norm_key: str,
) -> str:
    """
    Renders 100% PURE PHYSICAL PAPER NOTE.
    Zero digital pills, zero container boxes around bullets, zero monospace fonts,
    zero digital watermarks. Uses real photographic paper ruling, handwritten ink,
    an authentic hand-sketched diagram, and a realistic 3M Post-It sticky note.
    """
    page_num = fields["page_number"]

    # Clean physical notebook features: Pristine margin line (zero clunky fake 3D holes!)
    decorations_html = '<div class="nc-margin-line"></div>'
    postit_top_decor = '<div class="nc-postit-tape"></div>'

    # Bullets written directly on the paper ruling lines (zero web cards!)
    bullets_html = "".join(
        f'<li class="nc-paper-bullet-item">'
        f'<span class="nc-pbullet-mark">&#8212; 0{i + 1}.</span>'
        f'<div class="nc-pbullet-text">{_format_inline_highlights(b)}</div>'
        f'</li>'
        for i, b in enumerate(fields["bullet_points"])
    )

    # Dynamic, varied hand-sketched technical diagram for this specific slide
    diagram_html = _render_authentic_handwritten_diagram(fields, page_num, total_pages, norm_key)

    return f"""
    <div class="nc-canvas nc-theme-{norm_key}" id="nc-slide-{page_num}" data-page="{page_num}">
        {decorations_html}
        <div class="nc-inner nc-paper-inner">
            <div class="nc-paper-header">
                <span class="nc-ph-meta">Course: {html.escape(subject_category)}  //  {html.escape(topic)}</span>
                <span class="nc-ph-page">Page {page_num:02d} / {total_pages:02d}</span>
            </div>
            <div class="nc-paper-header-rule"></div>

            <div class="nc-paper-title-wrap">
                <h1 class="nc-paper-title">#0{page_num}. {html.escape(fields['title'])}</h1>
                <svg class="nc-paper-title-underline" width="280" height="8" viewBox="0 0 280 8" fill="none">
                    <path d="M2 5 C60 1 120 7 180 4 C220 2 260 6 278 4" stroke="var(--ink-accent)" stroke-width="2.6" stroke-linecap="round"/>
                </svg>
            </div>

            <div class="nc-paper-concept">
                <span class="nc-concept-tag">&#9733; Core Concept:</span>
                <span class="nc-concept-body">{_format_inline_highlights(fields['summary_banner'])}</span>
            </div>

            <ul class="nc-paper-bullets">
                {bullets_html}
            </ul>

            {diagram_html}

            <div class="nc-paper-footer">
                <div class="nc-paper-postit">
                    {postit_top_decor}
                    <div class="nc-postit-header">&#10022; Exam Revision Tip:</div>
                    <div class="nc-postit-body">{_format_inline_highlights(fields['pro_tip'])}</div>
                </div>
            </div>
        </div>
    </div>
    """


def _build_digital_slide_html(
    fields: dict,
    total_pages: int,
    topic: str,
    subject_category: str,
    norm_key: str,
) -> str:
    """Renders sleek digital tablet study cards (iPad GoodNotes / Notability Cyber Dark)."""
    page_num = fields["page_number"]

    bullets_html = "".join(
        f'<li class="nc-bullet-item">'
        f'<span class="nc-bullet-dot">0{i + 1}.</span>'
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

    top_bar_extra = ""
    if norm_key == "digital_ipad":
        top_bar_extra = """
        <div class="nc-digital-statusbar">
            <span class="nc-ds-time">9:41 AM</span>
            <span class="nc-ds-title">GoodNotes 6  //  Study Deck</span>
            <span class="nc-ds-battery">APPLE PENCIL 100% CHARGED</span>
        </div>
        """
    elif norm_key == "digital_dark":
        top_bar_extra = """
        <div class="nc-digital-statusbar nc-cyber-statusbar">
            <span class="nc-ds-time">23:42</span>
            <span class="nc-ds-title">NOTABILITY // CYBER DARK AMOLED</span>
            <span class="nc-ds-battery">STYLUS ACTIVE</span>
        </div>
        """

    return f"""
    <div class="nc-canvas nc-theme-{norm_key}" id="nc-slide-{page_num}" data-page="{page_num}">
        <div class="nc-inner">
            {top_bar_extra}
            <div class="nc-topbar">
                <div class="nc-subject-pill">NIWNOTES  //  {html.escape(subject_category.upper())}</div>
                <div class="nc-page-pill">PAGE {page_num:02d} OF {total_pages:02d}</div>
            </div>

            <div class="nc-topic-kicker">{html.escape(topic)}</div>
            <div class="nc-title-wrap">
                <h1 class="nc-title">{html.escape(fields['title'])}</h1>
                <svg class="nc-title-underline" width="220" height="10" viewBox="0 0 220 10" fill="none">
                    <path d="M2 6C45 2 90 9 135 5C180 1 205 8 218 5" stroke="var(--ink-accent)" stroke-width="2.6" stroke-linecap="round"/>
                </svg>
            </div>

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
                <div class="nc-diagram-grid-wrap">
                    <div class="nc-diagram-grid">
                        {steps_html}
                    </div>
                </div>
            </div>

            <div class="nc-footer-row">
                <div class="nc-protip-box">
                    <span class="nc-protip-label">EXAM TIP:</span>
                    <span class="nc-protip-text">{_format_inline_highlights(fields['pro_tip'])}</span>
                </div>
                <div class="nc-watermark">NIWNOTES STUDIO</div>
            </div>
        </div>
    </div>
    """


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

    if is_realistic:
        return _build_realistic_slide_html(fields, total_pages, topic, subject_category, norm_key)
    else:
        return _build_digital_slide_html(fields, total_pages, topic, subject_category, norm_key)


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
    Renders the multi-page handwritten note studio with authentic high-res real paper textures,
    hand-drawn SVG diagrams, extra glossary deep-dive page, and zero emojis.
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
        "classic_ruled": f"""
            --real-paper-bg: url('data:image/jpeg;base64,{_RULED_PAPER_B64}');
            --paper-bg: #FCFBF7;
            --margin-line: rgba(225, 68, 68, 0.7);
            --ink-primary: #152E5A;
            --ink-secondary: #1E3A8A;
            --ink-accent: #DC2626;
            --banner-bg: rgba(254, 240, 138, 0.35);
            --banner-border: #EAB308;
            --hl-bg: #FEF08A;
            --hl-ink: #713F12;
            --card-bg: transparent;
            --card-border: #152E5A;
            --step-bg: rgba(255, 255, 255, 0.65);
            --protip-bg: #FEF08A;
            --protip-border: #EAB308;
            --font-tilt: -0.2deg;
        """,
        "vintage_kraft": f"""
            --real-paper-bg: url('data:image/jpeg;base64,{_KRAFT_PAPER_B64}');
            --paper-bg: #F7F1E5;
            --margin-line: rgba(180, 83, 9, 0.5);
            --ink-primary: #1F1610;
            --ink-secondary: #4A3324;
            --ink-accent: #C2410C;
            --banner-bg: rgba(253, 230, 138, 0.35);
            --banner-border: #D97706;
            --hl-bg: #FDE68A;
            --hl-ink: #451A03;
            --card-bg: transparent;
            --card-border: #78350F;
            --step-bg: rgba(255, 255, 255, 0.58);
            --protip-bg: #FFFBEB;
            --protip-border: #B45309;
            --font-tilt: -0.3deg;
        """,
        "digital_ipad": """
            --real-paper-bg: none;
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
            --real-paper-bg: none;
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

    escaped_caption = html.escape(strip_emojis(social_caption_text))
    lang_badge = "SINHALA + ENGLISH KUPPI MIX" if language == "Sinhala_Mix" else "100% PURE ENGLISH"
    tpl_meta = NOTE_TEMPLATES.get(norm_key, NOTE_TEMPLATES["classic_ruled"])
    tpl_style_badge = f"{tpl_meta['category'].upper()} // {tpl_meta['badge'].upper()}"

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
        position: relative;
        overflow: hidden;
        color: var(--ink-primary);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        text-shadow: 0 0 0.4px rgba(20, 20, 19, 0.25);
    }}

    /* REALISTIC TEMPLATES: REAL HIGH-RESOLUTION PHOTOGRAPHIC PAPER BACKGROUNDS */
    .nc-theme-classic_ruled {{
        background-color: #FCFBF7;
        background-image: var(--real-paper-bg);
        background-size: 1000px 1250px;
        background-repeat: no-repeat;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 18px 45px -8px rgba(0,0,0,0.22);
        border-radius: 3px;
    }}

    .nc-theme-vintage_kraft {{
        background-color: #F7F1E5;
        background-image: var(--real-paper-bg);
        background-size: 1000px 1250px;
        background-repeat: no-repeat;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 18px 45px -8px rgba(0,0,0,0.22);
        border-radius: 3px;
    }}

    /* DIGITAL TEMPLATES: MODERN MATTE CANVAS */
    .nc-theme-digital_ipad {{
        background-color: var(--paper-bg);
        background-image: var(--paper-grid);
        background-size: var(--paper-grid-size);
    }}

    .nc-theme-digital_dark {{
        background-color: var(--paper-bg);
        background-image: var(--paper-grid);
        background-size: var(--paper-grid-size);
    }}

    /* MARGIN LINE & BINDER HOLES (PHYSICAL PAPER FEATURES) */
    .nc-margin-line {{
        position: absolute;
        top: 0;
        bottom: 0;
        left: 82px;
        width: 2.2px;
        background: var(--margin-line);
        box-shadow: 1px 0 0 rgba(225, 68, 68, 0.2);
        z-index: 2;
    }}

    .nc-binder-hole {{
        display: none !important;
    }}

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

    .nc-pushpin-vector {{
        position: absolute;
        top: -10px;
        left: 20px;
        z-index: 8;
        transform: rotate(-10deg);
    }}

    /* DIGITAL TABLET STATUS BAR (IPAD / NOTABILITY - ZERO EMOJIS) */
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

    .nc-diagram-grid-wrap {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }}

    .nc-diagram-grid {{
        display: flex;
        align-items: stretch;
        justify-content: space-between;
        gap: 8px;
        flex: 1;
    }}

    .nc-sketch-slot {{
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        padding-left: 8px;
        border-left: 1.5px dashed rgba(20, 20, 19, 0.15);
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
        display: none !important;
    }}

    /* =====================================================================
       AUTHENTIC PHYSICAL PAPER NOTE STYLES (100% PURE HANDWRITING)
       ===================================================================== */
    .nc-paper-inner {{
        position: relative;
        z-index: 3;
        padding: 34px 44px 30px 104px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
    }}

    .nc-paper-header {{
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        color: var(--ink-secondary);
        padding-bottom: 2px;
    }}

    .nc-ph-meta {{
        font-size: 21px;
        font-weight: 700;
        color: var(--ink-secondary);
        letter-spacing: 0.01em;
    }}

    .nc-ph-page {{
        font-size: 20px;
        font-weight: 700;
        color: var(--ink-primary);
    }}

    .nc-paper-header-rule {{
        width: 100%;
        height: 1.8px;
        background: var(--margin-line);
        opacity: 0.65;
        margin-bottom: 6px;
    }}

    .nc-paper-title-wrap {{
        margin: 2px 0 6px 0;
    }}

    .nc-paper-title {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 38px;
        font-weight: 800;
        line-height: 1.15;
        color: var(--ink-primary);
        margin: 0;
    }}

    .nc-paper-title-underline {{
        display: block;
        margin-top: 2px;
    }}

    .nc-paper-concept {{
        display: flex;
        align-items: flex-start;
        gap: 8px;
        margin: 6px 0 10px 0;
        padding: 4px 8px;
        background: var(--banner-bg);
        border-left: 4px solid var(--banner-border);
        border-radius: 2px 6px 6px 2px;
    }}

    .nc-concept-tag {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 22px;
        font-weight: 800;
        color: var(--ink-accent);
        flex-shrink: 0;
    }}

    .nc-concept-body {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 21px;
        font-weight: 600;
        line-height: 1.38;
        color: var(--ink-primary);
    }}

    .nc-paper-bullets {{
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin: 6px 0 10px 0;
        padding: 0;
    }}

    .nc-paper-bullet-item {{
        display: flex;
        align-items: flex-start;
        gap: 10px;
        background: transparent !important;
        border: none !important;
        padding: 2px 0;
    }}

    .nc-pbullet-mark {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 24px;
        font-weight: 800;
        color: var(--ink-accent);
        min-width: 38px;
        flex-shrink: 0;
        line-height: 1.35;
    }}

    .nc-pbullet-text {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 21px;
        font-weight: 600;
        line-height: 1.42;
        color: var(--ink-primary);
    }}

    /* AUTHENTIC HANDWRITTEN DIAGRAM CONTAINER */
    .nc-paper-diagram-box {{
        margin: 8px 0;
        padding: 10px 14px;
        border: 1.8px dashed rgba(21, 46, 90, 0.45);
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;
        background: rgba(255, 255, 255, 0.4);
        box-shadow: 1px 2px 4px rgba(0, 0, 0, 0.04);
    }}

    .nc-theme-vintage_kraft .nc-paper-diagram-box {{
        border-color: rgba(120, 53, 15, 0.45);
        background: rgba(255, 255, 255, 0.25);
    }}

    .nc-pdiag-title {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 20px;
        font-weight: 800;
        color: var(--ink-accent);
        text-align: center;
        margin-bottom: 8px;
        letter-spacing: 0.02em;
    }}

    /* DIAGRAM NODES (ORGANIC HAND-DRAWN SKETCH BOXES) */
    .nc-sketch-node {{
        background: rgba(255, 255, 255, 0.65);
        border: 2px solid var(--ink-primary);
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;
        padding: 8px 12px;
        box-shadow: 2px 2px 0px rgba(0, 0, 0, 0.08);
    }}

    .nc-snode-num {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 17px;
        font-weight: 800;
        color: var(--ink-accent);
        display: inline-block;
        margin-bottom: 2px;
    }}

    .nc-snode-title {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 19px;
        font-weight: 800;
        color: var(--ink-primary);
        line-height: 1.2;
        margin-bottom: 3px;
        border-bottom: 1.2px dashed rgba(21, 46, 90, 0.3);
        padding-bottom: 2px;
    }}

    .nc-snode-body {{
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 16.5px;
        font-weight: 600;
        color: var(--ink-secondary);
        line-height: 1.3;
    }}

    /* FLOW 1: HORIZONTAL PIPELINE */
    .nc-pdiag-flow-horizontal {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }}

    .nc-pdiag-flow-horizontal .nc-sketch-node {{
        flex: 1;
        min-width: 0;
    }}

    .nc-sketch-arrow {{
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }}

    /* FLOW 2: ARCHITECTURE STACK */
    .nc-pdiag-stack-wrap {{
        display: flex;
        flex-direction: column;
        gap: 4px;
    }}

    .nc-sketch-tier {{
        background: rgba(255, 255, 255, 0.65);
        border: 1.8px solid var(--ink-primary);
        border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px;
        padding: 6px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
    }}

    .nc-tier-core {{
        background: rgba(254, 240, 138, 0.45);
        border-color: var(--ink-accent);
    }}

    .nc-tier-badge {{
        font-size: 15px;
        font-weight: 800;
        color: var(--ink-accent);
        border-right: 1.5px dashed var(--ink-accent);
        padding-right: 8px;
        flex-shrink: 0;
    }}

    .nc-tier-label {{
        font-size: 18px;
        font-weight: 800;
        color: var(--ink-primary);
        flex-shrink: 0;
    }}

    .nc-tier-detail {{
        font-size: 16.5px;
        font-weight: 600;
        color: var(--ink-secondary);
        line-height: 1.25;
    }}

    .nc-tier-arrow-down {{
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
    }}

    /* FLOW 3: CYCLIC FEEDBACK LOOP */
    .nc-pdiag-cycle-wrap {{
        display: flex;
        flex-direction: column;
        gap: 6px;
    }}

    .nc-cycle-top-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }}

    .nc-cycle-node {{
        flex: 1;
        min-width: 0;
    }}

    .nc-cycle-arrow-top {{
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .nc-cycle-return-row {{
        position: relative;
        text-align: center;
    }}

    .nc-cycle-bottom-node {{
        margin-top: -6px;
        padding: 6px 12px;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 17px;
    }}

    /* FLOW 4: BRANCHING FLOW */
    .nc-pdiag-branch-wrap {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .nc-branch-input {{
        flex: 1.1;
    }}

    .nc-branch-fork-svg {{
        flex-shrink: 0;
    }}

    .nc-branch-paths {{
        flex: 1.9;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }}

    .nc-branch-sub {{
        padding: 6px 10px;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 16.5px;
    }}

    .nc-branch-fallback {{
        border-style: dashed;
        background: rgba(255, 255, 255, 0.45);
    }}

    /* FLOW 5: TRADE-OFF MATRIX */
    .nc-pdiag-matrix-wrap {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
    }}

    .nc-matrix-col {{
        flex: 1;
    }}

    .nc-matrix-card {{
        min-height: 70px;
    }}

    .nc-matrix-divider {{
        flex-shrink: 0;
    }}

    .nc-matrix-footer-note {{
        margin-top: 6px;
        padding: 5px 10px;
        background: rgba(254, 240, 138, 0.4);
        border: 1.2px dashed var(--banner-border);
        border-radius: 4px;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        font-size: 16.5px;
        color: var(--ink-primary);
    }}

    /* PHYSICAL POST-IT STICKY NOTE (AUTHENTIC HANDWRITTEN EXAM TIP) */
    .nc-paper-footer {{
        display: flex;
        align-items: flex-end;
        justify-content: flex-start;
        padding-top: 2px;
        margin-top: 4px;
    }}

    .nc-paper-postit {{
        position: relative;
        width: auto;
        max-width: 540px;
        padding: 10px 18px 12px 20px;
        font-family: 'FontoshanHandwrite', 'Caveat', 'Kalam', cursive;
        box-sizing: border-box;
    }}

    .nc-theme-classic_ruled .nc-paper-postit {{
        background: #FEF08A;
        border-radius: 2px 2px 14px 2px;
        box-shadow: 2px 6px 14px -2px rgba(0, 0, 0, 0.18), 0 2px 4px rgba(0, 0, 0, 0.08);
        transform: rotate(-1.3deg);
        border-top: 3px solid #EAB308;
    }}

    .nc-theme-vintage_kraft .nc-paper-postit {{
        background: #FFFBEB;
        border: 1.5px dashed #B45309;
        border-radius: 3px;
        box-shadow: 2px 6px 14px -2px rgba(0, 0, 0, 0.14);
        transform: rotate(0.9deg);
    }}

    .nc-postit-tape {{
        position: absolute;
        top: -8px;
        left: 28px;
        width: 72px;
        height: 16px;
        background: rgba(255, 255, 240, 0.72);
        border: 1px solid rgba(220, 205, 170, 0.45);
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        transform: rotate(-1.5deg);
        backdrop-filter: blur(1px);
        z-index: 10;
    }}

    .nc-postit-header {{
        font-size: 19px;
        font-weight: 800;
        color: var(--ink-accent);
        margin-bottom: 2px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}

    .nc-postit-body {{
        font-size: 18.5px;
        font-weight: 600;
        line-height: 1.36;
        color: var(--ink-primary);
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
# 9. STANDALONE & CLI COMPATIBILITY EXPORT
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

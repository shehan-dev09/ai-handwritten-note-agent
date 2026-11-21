import os
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google.genai import types
from dotenv import load_dotenv
from trend_agent import get_working_models, get_genai_client

load_dotenv()

# =====================================================================
# 1. Multi-Template Theme Definitions (Synced with UI Preview Cards)
# =====================================================================
NOTE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "classic_cream": {
        "name": "Classic Cream",
        "badge": "Warm Dot-Grid",
        "description": "Warm cream dot-grid notebook with red margin line, yellow marker highlights, and spiral holes.",
        "paper_bg": "#FAF6EE",
        "line_css": "radial-gradient(#D6D1C7 1.5px, transparent 1.5px)",
        "bg_size": "26px 26px",
        "margin_line": "3px double #F87171",
        "text_color": "#1E293B",
        "sub_text_color": "#475569",
        "title_color": "#0F172A",
        "accent_color": "#2563EB",
        "secondary_accent": "#DC2626",
        "highlight_bg": "rgba(253, 224, 71, 0.72)",
        "box_bg": "#FFFFFF",
        "box_border": "#1E293B",
        "step_bg": "#F8FAFC",
        "pro_tip_bg": "#FEF9C3",
        "pro_tip_border": "#D97706",
        "pro_tip_text": "#713F12",
        "show_holes": True,
        "cornell_layout": False,
    },
    "dark_neon": {
        "name": "Obsidian Dark",
        "badge": "Dark Dot-Grid",
        "description": "Deep obsidian slate canvas with subtle dot-grid, emerald and sky-blue accents.",
        "paper_bg": "#0F172A",
        "line_css": "radial-gradient(#334155 1.5px, transparent 1.5px)",
        "bg_size": "26px 26px",
        "margin_line": "2px solid #10B981",
        "text_color": "#F1F5F9",
        "sub_text_color": "#94A3B8",
        "title_color": "#F8FAFC",
        "accent_color": "#38BDF8",
        "secondary_accent": "#22C55E",
        "highlight_bg": "rgba(6, 78, 59, 0.85)",
        "box_bg": "#1E293B",
        "box_border": "#22C55E",
        "step_bg": "#0F172A",
        "pro_tip_bg": "#052E16",
        "pro_tip_border": "#22C55E",
        "pro_tip_text": "#DCFCE7",
        "show_holes": False,
        "cornell_layout": False,
    },
    "blueprint_grid": {
        "name": "Blueprint Grid",
        "badge": "Engineering Graph",
        "description": "Crisp engineering graph paper with cobalt blue ink and orange structural callouts.",
        "paper_bg": "#F2F8FF",
        "line_css": (
            "linear-gradient(to right, #DCEBFA 1px, transparent 1px), "
            "linear-gradient(to bottom, #DCEBFA 1px, transparent 1px)"
        ),
        "bg_size": "26px 26px",
        "margin_line": "2px solid #60A5FA",
        "text_color": "#0F172A",
        "sub_text_color": "#334155",
        "title_color": "#0369A1",
        "accent_color": "#0284C7",
        "secondary_accent": "#EA580C",
        "highlight_bg": "rgba(186, 230, 253, 0.75)",
        "box_bg": "#FFFFFF",
        "box_border": "#0284C7",
        "step_bg": "#F0F9FF",
        "pro_tip_bg": "#FFF7ED",
        "pro_tip_border": "#EA580C",
        "pro_tip_text": "#9A3412",
        "show_holes": False,
        "cornell_layout": False,
    },
    "cornell_academic": {
        "name": "Cornell Exam",
        "badge": "Ruled Ivory Sheet",
        "description": "Structured academic ruled ivory paper with violet ink and crimson exam blocks.",
        "paper_bg": "#FCFBF9",
        "line_css": "repeating-linear-gradient(transparent, transparent 37px, #E7E5E4 37px, #E7E5E4 38px)",
        "bg_size": "100% 38px",
        "margin_line": "3px solid #A855F7",
        "text_color": "#1C1917",
        "sub_text_color": "#57534E",
        "title_color": "#3B0764",
        "accent_color": "#7E22CE",
        "secondary_accent": "#BE123C",
        "highlight_bg": "rgba(233, 213, 255, 0.70)",
        "box_bg": "#FFFFFF",
        "box_border": "#581C87",
        "step_bg": "#FAF5FF",
        "pro_tip_bg": "#FFF1F2",
        "pro_tip_border": "#BE123C",
        "pro_tip_text": "#881337",
        "show_holes": False,
        "cornell_layout": True,
    },
}


# =====================================================================
# 2. Structured Output Schemas (Optimized for Speed)
# =====================================================================
class DiagramStep(BaseModel):
    step_num: str = Field(description="Step number like '01', '02', '03'")
    label: str = Field(description="Short title of this step (2-4 words in English, no emojis)")
    detail: str = Field(description="Concise 1-line explanation of what happens in this step (no emojis)")


class NotePage(BaseModel):
    page_number: int = Field(description="Page number")
    title: str = Field(description="Big handwritten header title for the page (no emojis)")
    subtitle: str = Field(description="Short 1-line subtitle explaining the core focus (no emojis)")
    key_points: List[str] = Field(
        description="3 or 4 bullet points. Keep each bullet concise (max 18 words), wrap 1-2 key terms in <hl>tags</hl>, and do not use emojis."
    )
    diagram_title: str = Field(description="Title of the visual workflow diagram box on this page (no emojis)")
    diagram_steps: List[DiagramStep] = Field(
        description="3 or 4 sequential steps for the visual architecture/flowchart diagram"
    )
    pro_tip: str = Field(description="A short exam tip, memory trick, or real-world takeaway (no emojis)")
    footer_tag: str = Field(description="Short category tag for the bottom right (no emojis)")


class BatchSlideDeckWithCaption(BaseModel):
    pages: List[NotePage] = Field(description="Exactly 5 sequential pages for this study module")
    linkedin_caption: str = Field(
        description="Engaging LinkedIn/Facebook study post caption in the requested language without any emojis"
    )
    hashtags: List[str] = Field(description="5-8 relevant university and tech hashtags")


class BatchSlideDeckOnly(BaseModel):
    pages: List[NotePage] = Field(description="Exactly 5 sequential pages for this study module")


class StudyCarouselResponse(BaseModel):
    pages: List[NotePage] = Field(description="All sequential pages for the study carousel")
    linkedin_caption: str = Field(description="Engaging LinkedIn/Facebook study post caption")
    hashtags: List[str] = Field(description="5-8 relevant university and tech hashtags")


# =====================================================================
# 3. Progressive Curriculum Outlines for 5, 10, and 30 Pages
# =====================================================================
MODULE_OUTLINES = [
    {
        "module_name": "Module 1: Core Foundations & Architecture",
        "slides": [
            "Slide 1: Hook, Core Definition & Why This Topic Matters in Exams & Industry",
            "Slide 2: Fundamental Concepts, Key Terminology & Underlying Theory",
            "Slide 3: Step-by-Step Internal Architecture & Core Data/Execution Flow",
            "Slide 4: Practical Implementation Example & Real-World System Use Case",
            "Slide 5: Foundation Summary, Best Practices & Key Exam Takeaways",
        ],
    },
    {
        "module_name": "Module 2: Deep Internals, Algorithms & Optimization",
        "slides": [
            "Slide 6: Mathematical / Algorithmic Mechanics & Internal State Management",
            "Slide 7: Memory, Latency & Performance Optimization Techniques",
            "Slide 8: Edge Cases, Bottlenecks & Failure Modes",
            "Slide 9: Side-by-Side Comparison with Alternative Approaches & Trade-offs",
            "Slide 10: Production Engineering Patterns & Advanced Exam Questions",
        ],
    },
    {
        "module_name": "Module 3: System Design, Scaling & High Availability",
        "slides": [
            "Slide 11: End-to-End Distributed System Design & Component Topology",
            "Slide 12: Horizontal Scaling, Load Balancing & Caching Strategies",
            "Slide 13: Concurrency, Synchronization & Fault Tolerance Mechanisms",
            "Slide 14: Monitoring, Observability, Metrics & Debugging Workflows",
            "Slide 15: System Design Interview & Viva Examination Checklist",
        ],
    },
    {
        "module_name": "Module 4: Security, Reliability & Governance",
        "slides": [
            "Slide 16: Threat Model, Attack Surface & Common Vulnerabilities",
            "Slide 17: Defensive Architecture, Encryption & Access Control Patterns",
            "Slide 18: Automated Testing, Verification & Quality Assurance Pipelines",
            "Slide 19: Disaster Recovery, Backups & High-Availability Failover",
            "Slide 20: Security & Reliability Hardening Cheat Sheet",
        ],
    },
    {
        "module_name": "Module 5: Case Studies, Hands-On Patterns & Debugging",
        "slides": [
            "Slide 21: Industry Case Study #1 - How Top Tech Teams Implement This",
            "Slide 22: Industry Case Study #2 - Scaling Challenges & Lessons Learned",
            "Slide 23: Clean Implementation Blueprint & Design Pattern Breakdown",
            "Slide 24: Common Anti-Patterns, Bugs & How to Troubleshoot Them Fast",
            "Slide 25: Practical Lab / Project Implementation Roadmap for Students",
        ],
    },
    {
        "module_name": "Module 6: Master Revision, Viva Prep & Future Trends",
        "slides": [
            "Slide 26: Next-Generation Research Trends & Future Evolution (2026+)",
            "Slide 27: Top 5 University Exam & Technical Interview Questions Answered",
            "Slide 28: Rapid-Fire Formula / Concept Comparison Cheat Sheet",
            "Slide 29: Mental Models & Memory Anchors for Instant Recall",
            "Slide 30: Ultimate Master Summary & Career Action Plan",
        ],
    },
]


def _build_language_instructions(language: str, include_caption: bool = True) -> str:
    """Builds natural language instructions for both the note slides and the social caption."""
    if language == "Sinhala_Mix":
        caption_rule = (
            "- **SOCIAL CAPTION LANGUAGE (MUST MATCH)**: Write `linkedin_caption` in the EXACT SAME natural Sri Lankan university 'Kuppiya' Sinhala Unicode + English technical mix. Do NOT use any emojis."
            if include_caption
            else ""
        )
        return f"""
        LANGUAGE STYLE: NATURAL SRI LANKAN UNIVERSITY "KUPPIYA" SINHALA + ENGLISH TECH MIX:
        - Write explanations in natural, conversational Sri Lankan university student Sinhala (Unicode script) mixed seamlessly with English technical keywords-exactly how a top senior student explains a tough lecture in a campus 'Kuppiya' study session.
        - NEVER translate technical terms into awkward dictionary Sinhala. Keep ALL technical terms, acronyms, data structures, protocols, and action verbs in English (e.g., 'Database Indexing', 'API Gateway', 'Backpropagation', 'Latency', 'Cache Miss', 'Deadlock', 'Container').
        - Example good bullet style: "<hl>RAG Architecture</hl> එකෙන් වෙන්නේ LLM එකට අපේම Private PDF හෝ Database එකක තියෙන නිවැරදි data දීලා <hl>Hallucinations</hl> නැති කරන එකයි."
        - Example good bullet style: "සරලවම කිව්වොත් <hl>Load Balancer</hl> එකෙන් කරන්නේ එකම Server එකට එන ලොකු Traffic එක Servers කිහිපයක් අතරේ සමානව බෙදලා <hl>High Availability</hl> තියාගන්න එකයි."
        - Keep main `title`, `diagram_title`, and `diagram_steps.label` in clear English, while `subtitle`, `key_points`, `diagram_steps.detail`, and `pro_tip` use this natural Sinhala + English Kuppiya mix.
        - STRICT RULE: Do NOT include any emojis anywhere in the slides or caption.
        {caption_rule}
        """
    else:
        caption_rule = (
            "- **SOCIAL CAPTION LANGUAGE (MUST MATCH)**: Write `linkedin_caption` in 100% professional, engaging English tailored for LinkedIn and Facebook tech communities. Do NOT use any emojis."
            if include_caption
            else ""
        )
        return f"""
        LANGUAGE STYLE: 100% CRISP ACADEMIC & PROFESSIONAL ENGLISH:
        - Write all titles, subtitles, bullet points, diagram steps, and pro-tips in clear, high-impact English suitable for university revision and global tech portfolios.
        - STRICT RULE: Do NOT include any emojis anywhere in the slides or caption.
        {caption_rule}
        """


def _generate_batch_of_5(
    client: Any,
    working_models: List[str],
    topic: str,
    subject_category: str,
    language: str,
    batch_index: int,
    total_pages: int,
) -> Dict[str, Any]:
    """Generates a single 5-page module with thinking_budget=0 for sub-3-second latency."""
    outline = MODULE_OUTLINES[batch_index % len(MODULE_OUTLINES)]
    start_page = batch_index * 5 + 1
    end_page = start_page + 4
    include_caption = batch_index == 0
    schema_cls = BatchSlideDeckWithCaption if include_caption else BatchSlideDeckOnly
    lang_instructions = _build_language_instructions(language, include_caption=include_caption)
    slides_plan = "\n".join([f"- Page {start_page + i}: {desc}" for i, desc in enumerate(outline["slides"])])

    prompt = f"""
    You are a top-performing University Honors Student & Visual Sketchnote Creator specializing in "{subject_category}".
    Create pages {start_page} to {end_page} (out of a {total_pages}-page study guide) on the topic: "{topic}".
    Current Module Focus: {outline["module_name"]}

    {lang_instructions}

    Formatting Rules for High-Speed Sketchnotes:
    1. Generate EXACTLY 5 pages numbered {start_page} through {end_page}:
    {slides_plan}
    2. In `key_points` (3 or 4 bullets per page, max 18 words per bullet), wrap 1 or 2 core technical phrases per bullet inside `<hl>...</hl>` tags so they get a marker highlight.
    3. Keep `diagram_steps` (3 or 4 steps per page) concise: `label` should be 2-4 words in English, and `detail` should be a 1-sentence explanation.
    4. Do NOT output any emojis in any field.
    """

    num_models = len(working_models)
    ordered_models = [working_models[(batch_index + i) % num_models] for i in range(num_models)]

    last_error = None
    for model_name in ordered_models:
        try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema_cls,
                        temperature=0.35,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )
            except Exception:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema_cls,
                        temperature=0.35,
                    ),
                )
            parsed = schema_cls.model_validate_json(response.text)
            for idx, p in enumerate(parsed.pages):
                p.page_number = start_page + idx

            return {
                "pages": parsed.pages,
                "linkedin_caption": getattr(parsed, "linkedin_caption", ""),
                "hashtags": getattr(parsed, "hashtags", []),
            }
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Batch {batch_index + 1} failed across all models. Last error: {last_error}")


def generate_5_page_study_guide(
    topic: str,
    language: str = "Sinhala_Mix",
    api_key: str = None,
    subject_category: str = "AI & Machine Learning",
    num_pages: int = 5,
) -> StudyCarouselResponse:
    """
    Generates a 5, 10, or 30-page handwritten study deck.
    Uses Gemini Flash-Lite with thinking_budget=0 and parallel batch execution.
    """
    active_key = api_key or os.getenv("GEMINI_API_KEY")
    client = get_genai_client(active_key)
    working_models = get_working_models(active_key)

    valid_pages = num_pages if num_pages in (5, 10, 30) else 5
    num_batches = valid_pages // 5

    if num_batches == 1:
        batch_res = _generate_batch_of_5(
            client, working_models, topic, subject_category, language, 0, valid_pages
        )
        return StudyCarouselResponse(
            pages=batch_res["pages"],
            linkedin_caption=batch_res["linkedin_caption"],
            hashtags=batch_res["hashtags"],
        )

    batch_results: Dict[int, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(num_batches, 6)) as executor:
        future_map = {
            executor.submit(
                _generate_batch_of_5,
                client,
                working_models,
                topic,
                subject_category,
                language,
                b_idx,
                valid_pages,
            ): b_idx
            for b_idx in range(num_batches)
        }
        for future in future_map:
            b_idx = future_map[future]
            batch_results[b_idx] = future.result()

    all_pages: List[NotePage] = []
    for b_idx in range(num_batches):
        all_pages.extend(batch_results[b_idx]["pages"])

    first_batch = batch_results[0]
    return StudyCarouselResponse(
        pages=all_pages,
        linkedin_caption=first_batch["linkedin_caption"],
        hashtags=first_batch["hashtags"],
    )


# =====================================================================
# 4. HTML/CSS Sketchnote Page Builder & Zero-Wait Interactive Studio
# =====================================================================
def _format_highlight(text: str) -> str:
    return (
        text.replace("<hl>", '<span class="hl">')
        .replace("</hl>", "</span>")
        .replace("**", "")
    )


def _get_template_css(t: Dict[str, Any]) -> str:
    """Returns the CSS stylesheet for a 1000x1250 handwritten note page."""
    return f"""
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        .niw-page {{
            width: 1000px;
            height: 1250px;
            background-color: {t["paper_bg"]};
            background-image: {t["line_css"]};
            background-size: {t["bg_size"]};
            font-family: 'Patrick Hand', 'Noto Sans Sinhala', sans-serif;
            color: {t["text_color"]};
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: {"36px 55px 38px 75px" if not t["show_holes"] else "36px 55px 38px 108px"};
            border: 1px solid rgba(0,0,0,0.08);
            text-align: left;
            user-select: none;
        }}
        .niw-page::before {{
            content: '';
            position: absolute;
            top: 0;
            bottom: 0;
            left: {"52px" if not t["show_holes"] else "86px"};
            width: 4px;
            border-left: {t["margin_line"]};
            z-index: 1;
        }}
        .niw-holes {{
            position: absolute;
            left: 26px;
            top: 60px;
            bottom: 60px;
            width: 32px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            z-index: 2;
        }}
        .niw-hole {{
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #E2E8F0;
            box-shadow: inset 2px 2px 5px rgba(0,0,0,0.28);
            border: 1px solid #CBD5E1;
        }}
        .niw-cornell-banner {{
            background: {t["box_bg"]};
            border: 2.5px solid {t["box_border"]};
            border-radius: 10px;
            padding: 8px 18px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: {t["title_color"]};
            box-shadow: 3px 3px 0px {t["accent_color"]};
        }}
        .niw-top-section {{
            position: relative;
            z-index: 3;
        }}
        .niw-meta-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            border-bottom: 2px dashed rgba(148, 163, 184, 0.45);
            padding-bottom: 6px;
        }}
        .niw-topic-pill {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 15px;
            font-weight: 700;
            color: {t["accent_color"]};
            background: {t["step_bg"]};
            padding: 5px 14px;
            border-radius: 20px;
            border: 2px solid {t["accent_color"]};
            max-width: 72%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .niw-page-badge {{
            font-family: 'Caveat', cursive;
            font-size: 28px;
            font-weight: 700;
            color: {t["secondary_accent"]};
            background: {t["box_bg"]};
            padding: 2px 16px;
            border: 2.5px solid {t["secondary_accent"]};
            border-radius: 18px 6px 16px 6px;
            transform: rotate(1.5deg);
            box-shadow: 3px 3px 0px rgba(0,0,0,0.12);
        }}
        .niw-title {{
            font-family: 'Caveat', 'Noto Sans Sinhala', cursive;
            font-size: 46px;
            font-weight: 700;
            color: {t["title_color"]};
            line-height: 1.12;
            margin-bottom: 6px;
        }}
        .niw-subtitle {{
            font-size: 22px;
            color: {t["sub_text_color"]};
            font-weight: 600;
            line-height: 1.32;
            margin-bottom: 14px;
            padding-left: 10px;
            border-left: 4px solid {t["secondary_accent"]};
        }}
        .niw-points-list {{
            display: flex;
            flex-direction: column;
            gap: 11px;
            margin-bottom: 14px;
        }}
        .niw-point-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            font-size: 22px;
            line-height: 1.4;
            color: {t["text_color"]};
        }}
        .niw-bullet-marker {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
            color: {t["secondary_accent"]};
            font-size: 20px;
            line-height: 1.35;
            flex-shrink: 0;
        }}
        .hl {{
            background: linear-gradient(104deg, rgba(253, 224, 71, 0) 0.9%, {t["highlight_bg"]} 2.4%, {t["highlight_bg"]} 96%, rgba(253, 224, 71, 0) 98%);
            padding: 1px 7px;
            border-radius: 5px;
            font-weight: 700;
            color: {t["text_color"]};
            box-decoration-break: clone;
            -webkit-box-decoration-break: clone;
        }}
        .niw-diagram-card {{
            position: relative;
            z-index: 3;
            background: {t["box_bg"]};
            border: 3px solid {t["box_border"]};
            border-radius: 18px 8px 20px 8px;
            padding: 18px 22px;
            box-shadow: 6px 6px 0px {t["accent_color"]};
            margin-bottom: 14px;
        }}
        .niw-diagram-header {{
            font-family: 'Caveat', cursive;
            font-size: 31px;
            font-weight: 700;
            color: {t["accent_color"]};
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 2px dashed rgba(148, 163, 184, 0.35);
            padding-bottom: 4px;
        }}
        .niw-steps-container {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .niw-step-row {{
            display: flex;
            align-items: center;
            gap: 14px;
            background: {t["step_bg"]};
            border: 2px solid rgba(148, 163, 184, 0.45);
            border-radius: 12px;
            padding: 9px 14px;
        }}
        .niw-step-badge {{
            background: {t["accent_color"]};
            color: #FFFFFF;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 800;
            font-size: 16px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .niw-step-content {{
            display: flex;
            flex-direction: column;
        }}
        .niw-step-label {{
            font-weight: 700;
            font-size: 20px;
            color: {t["title_color"]};
            line-height: 1.2;
        }}
        .niw-step-detail {{
            font-size: 18px;
            color: {t["sub_text_color"]};
            line-height: 1.3;
        }}
        .niw-step-arrow {{
            text-align: center;
            font-family: 'JetBrains Mono', monospace;
            font-size: 15px;
            line-height: 0.9;
            color: {t["secondary_accent"]};
            font-weight: 700;
        }}
        .niw-bottom-section {{
            position: relative;
            z-index: 3;
        }}
        .niw-pro-tip-box {{
            background: {t["pro_tip_bg"]};
            border: 2.5px solid {t["pro_tip_border"]};
            border-radius: 12px 20px 10px 18px;
            padding: 12px 18px;
            display: flex;
            align-items: center;
            gap: 14px;
            box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.10);
            transform: rotate(-0.35deg);
            margin-bottom: 12px;
        }}
        .niw-tip-badge {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            font-weight: 800;
            background: {t["pro_tip_border"]};
            color: #FFFFFF;
            padding: 4px 9px;
            border-radius: 6px;
            flex-shrink: 0;
        }}
        .niw-pro-tip-text {{
            font-size: 20px;
            font-weight: 600;
            color: {t["pro_tip_text"]};
            line-height: 1.35;
        }}
        .niw-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 14px;
            font-weight: 700;
            color: #64748B;
            padding-top: 6px;
            border-top: 2px solid rgba(148, 163, 184, 0.3);
        }}
    """


def _build_page_inner_html(
    page: NotePage,
    total_pages: int,
    topic: str,
    template_id: str,
    element_id: str,
) -> str:
    """Builds the inner `<div class="niw-page">` markup for a single slide without emojis."""
    t = NOTE_TEMPLATES.get(template_id, NOTE_TEMPLATES["classic_cream"])

    bullets_html = ""
    for pt in page.key_points[:4]:
        formatted_pt = _format_highlight(pt)
        bullets_html += f"""
        <div class="niw-point-item">
            <div class="niw-bullet-marker">&gt;</div>
            <div class="niw-point-text">{formatted_pt}</div>
        </div>
        """

    steps_html = ""
    steps_slice = page.diagram_steps[:4]
    for idx, step in enumerate(steps_slice):
        arrow_html = '<div class="niw-step-arrow">|</div>' if idx < len(steps_slice) - 1 else ""
        steps_html += f"""
        <div class="niw-step-row">
            <div class="niw-step-badge">{step.step_num}</div>
            <div class="niw-step-content">
                <div class="niw-step-label">{step.label}</div>
                <div class="niw-step-detail">{_format_highlight(step.detail)}</div>
            </div>
        </div>
        {arrow_html}
        """

    holes_html = ""
    if t["show_holes"]:
        holes_html = '<div class="niw-holes">' + "".join(['<div class="niw-hole"></div>' for _ in range(11)]) + "</div>"

    cornell_header = ""
    if t["cornell_layout"]:
        cornell_header = f"""
        <div class="niw-cornell-banner">
            <div>CORNELL REVISION SYSTEM // NIWNOTES</div>
            <div>MODULE SHEET {page.page_number} OF {total_pages}</div>
        </div>
        """

    return f"""
    <div class="niw-page" id="{element_id}" data-page="{page.page_number}">
        {holes_html}
        <div class="niw-top-section">
            {cornell_header}
            <div class="niw-meta-bar">
                <div class="niw-topic-pill">TOPIC // {topic[:62]}</div>
                <div class="niw-page-badge">Page {page.page_number} / {total_pages}</div>
            </div>
            <div class="niw-title">{page.page_number:02d} // {page.title}</div>
            <div class="niw-subtitle">{_format_highlight(page.subtitle)}</div>
            <div class="niw-points-list">
                {bullets_html}
            </div>
        </div>

        <div class="niw-diagram-card">
            <div class="niw-diagram-header">FLOW // {page.diagram_title}</div>
            <div class="niw-steps-container">
                {steps_html}
            </div>
        </div>

        <div class="niw-bottom-section">
            <div class="niw-pro-tip-box">
                <div class="niw-tip-badge">CORE</div>
                <div class="niw-pro-tip-text"><strong>Key Takeaway:</strong> {_format_highlight(page.pro_tip)}</div>
            </div>
            <div class="niw-footer">
                <div>NIWNOTES // UNIVERSITY SOCIAL LEARNING</div>
                <div>#{page.footer_tag.replace(" ", "")} // Next -&gt;</div>
            </div>
        </div>
    </div>
    """


def build_interactive_studio_html(
    carousel_data: StudyCarouselResponse,
    topic: str,
    template_id: str = "classic_cream",
    subject_category: str = "AI & Machine Learning",
    language: str = "Sinhala_Mix",
) -> str:
    """
    Builds a self-contained, zero-wait Woday-styled Interactive Studio HTML component without emojis.
    """
    t = NOTE_TEMPLATES.get(template_id, NOTE_TEMPLATES["classic_cream"])
    page_css = _get_template_css(t)
    total_pages = len(carousel_data.pages)

    full_caption = f"{carousel_data.linkedin_caption}\n\n" + " ".join(
        [f"#{h.strip('#')}" for h in carousel_data.hashtags]
    )
    caption_json = json.dumps(full_caption)
    lang_label = "SI/EN Kuppiya Mix" if language == "Sinhala_Mix" else "100% Academic English"

    thumbs_html = ""
    inspector_slides_html = ""

    for idx, page in enumerate(carousel_data.pages):
        active_cls = "active" if idx == 0 else ""
        slide_dom_id = f"niw-export-slide-{idx}"
        thumb_inner = _build_page_inner_html(
            page, total_pages, topic, template_id, f"niw-thumb-slide-{idx}"
        )
        export_inner = _build_page_inner_html(
            page, total_pages, topic, template_id, slide_dom_id
        )

        thumbs_html += f"""
        <div class="studio-thumb-card {active_cls}" onclick="selectSlide({idx})" id="thumb-btn-{idx}">
            <div class="studio-thumb-header">
                <span class="studio-thumb-num">#{page.page_number:02d}</span>
                <span class="studio-thumb-title">{page.title[:22]}</span>
            </div>
            <div class="studio-thumb-viewport">
                <div class="studio-thumb-scaler">
                    {thumb_inner}
                </div>
            </div>
        </div>
        """

        inspector_slides_html += f"""
        <div class="inspector-slide-frame {active_cls}" id="inspector-frame-{idx}">
            <div class="inspector-scaler">
                {export_inner}
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@700&family=Patrick+Hand&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Noto+Sans+Sinhala:wght@500;700&family=JetBrains+Mono:wght@600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <style>
        {page_css}

        body {{
            background: transparent;
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            color: #141413;
            margin: 0;
            padding: 4px 2px 20px 2px;
        }}

        .studio-bar {{
            background: #FFFFFF;
            border: 1px solid rgba(20, 20, 19, 0.09);
            border-radius: 18px;
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            box-shadow: 0 8px 24px -6px rgba(20, 20, 19, 0.05);
            margin-bottom: 16px;
        }}
        .studio-bar-left {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .studio-badge-green {{
            background: #DCFCE7;
            color: #15803D;
            font-weight: 800;
            font-size: 12px;
            padding: 5px 12px;
            border-radius: 999px;
        }}
        .studio-badge-gray {{
            background: #F3F2EE;
            color: #575653;
            font-weight: 700;
            font-size: 12px;
            padding: 5px 12px;
            border-radius: 999px;
            border: 1px solid rgba(20,20,19,0.07);
        }}
        .studio-actions {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .btn-woday-primary {{
            background: #141413;
            color: #FFFFFF;
            border: none;
            border-radius: 12px;
            padding: 10px 18px;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.16s ease;
            box-shadow: 0 4px 12px rgba(20, 20, 19, 0.14);
        }}
        .btn-woday-primary:hover {{
            background: #292826;
            transform: translateY(-1px);
        }}
        .btn-woday-secondary {{
            background: #F3F2EE;
            color: #141413;
            border: 1px solid rgba(20, 20, 19, 0.12);
            border-radius: 12px;
            padding: 10px 16px;
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.16s ease;
        }}
        .btn-woday-secondary:hover {{
            background: #EAE8E1;
        }}

        .studio-thumb-strip {{
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding: 6px 4px 14px 4px;
            margin-bottom: 18px;
            scrollbar-width: thin;
        }}
        .studio-thumb-card {{
            background: #FFFFFF;
            border: 2px solid rgba(20, 20, 19, 0.08);
            border-radius: 14px;
            padding: 8px;
            width: 176px;
            flex-shrink: 0;
            cursor: pointer;
            transition: all 0.16s ease;
            box-shadow: 0 4px 12px rgba(20, 20, 19, 0.04);
        }}
        .studio-thumb-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(20, 20, 19, 0.25);
        }}
        .studio-thumb-card.active {{
            border-color: #141413;
            box-shadow: 0 0 0 3px rgba(20, 20, 19, 0.12);
            background: #FAF9F5;
        }}
        .studio-thumb-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            gap: 4px;
        }}
        .studio-thumb-num {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            background: #141413;
            color: #FFFFFF;
            padding: 2px 7px;
            border-radius: 6px;
        }}
        .studio-thumb-title {{
            font-size: 11px;
            font-weight: 700;
            color: #575653;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .studio-thumb-viewport {{
            width: 156px;
            height: 195px;
            overflow: hidden;
            border-radius: 8px;
            position: relative;
            border: 1px solid rgba(0,0,0,0.06);
        }}
        .studio-thumb-scaler {{
            transform: scale(0.156);
            transform-origin: top left;
            width: 1000px;
            height: 1250px;
            pointer-events: none;
        }}

        .studio-main-grid {{
            display: grid;
            grid-template-columns: 520px 1fr;
            gap: 20px;
            align-items: start;
        }}
        @media (max-width: 980px) {{
            .studio-main-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .inspector-card {{
            background: #FFFFFF;
            border: 1px solid rgba(20, 20, 19, 0.09);
            border-radius: 20px;
            padding: 16px;
            box-shadow: 0 12px 30px -8px rgba(20, 20, 19, 0.06);
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .inspector-toolbar {{
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .inspector-slide-counter {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            font-weight: 700;
            color: #141413;
            background: #F3F2EE;
            padding: 6px 12px;
            border-radius: 8px;
        }}
        .inspector-viewport {{
            width: 480px;
            height: 600px;
            overflow: hidden;
            border-radius: 12px;
            border: 1px solid rgba(20, 20, 19, 0.10);
            box-shadow: 0 10px 24px rgba(0,0,0,0.08);
            position: relative;
        }}
        .inspector-slide-frame {{
            display: none;
            width: 480px;
            height: 600px;
        }}
        .inspector-slide-frame.active {{
            display: block;
        }}
        .inspector-scaler {{
            transform: scale(0.48);
            transform-origin: top left;
            width: 1000px;
            height: 1250px;
        }}

        .caption-card {{
            background: #FFFFFF;
            border: 1px solid rgba(20, 20, 19, 0.09);
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 12px 30px -8px rgba(20, 20, 19, 0.06);
        }}
        .caption-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .caption-title {{
            font-size: 17px;
            font-weight: 800;
            color: #141413;
        }}
        .caption-textarea {{
            width: 100%;
            height: 410px;
            background: #F7F6F2;
            border: 1px solid rgba(20, 20, 19, 0.10);
            border-radius: 14px;
            padding: 16px;
            font-family: 'Plus Jakarta Sans', 'Noto Sans Sinhala', sans-serif;
            font-size: 14px;
            line-height: 1.65;
            color: #141413;
            resize: vertical;
            margin-bottom: 14px;
        }}
        .hashtag-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .hashtag-pill {{
            background: #F3F2EE;
            color: #141413;
            font-size: 12px;
            font-weight: 700;
            padding: 5px 11px;
            border-radius: 999px;
            border: 1px solid rgba(20, 20, 19, 0.08);
        }}
    </style>
    </head>
    <body>

        <div class="studio-bar">
            <div class="studio-bar-left">
                <span class="studio-badge-green">LIVE RENDER</span>
                <span class="studio-badge-gray">{t["name"]}</span>
                <span class="studio-badge-gray">{total_pages} Pages</span>
                <span class="studio-badge-gray">{lang_label}</span>
            </div>
            <div class="studio-actions">
                <button class="btn-woday-secondary" id="btn-dl-single" onclick="downloadActiveSlide()">
                    Download Current Slide (.PNG)
                </button>
                <button class="btn-woday-primary" id="btn-dl-zip" onclick="downloadAllSlidesZip()">
                    Download All {total_pages} Slides (.ZIP)
                </button>
            </div>
        </div>

        <div class="studio-thumb-strip">
            {thumbs_html}
        </div>

        <div class="studio-main-grid">
            <div class="inspector-card">
                <div class="inspector-toolbar">
                    <button class="btn-woday-secondary" onclick="stepSlide(-1)">Prev</button>
                    <span class="inspector-slide-counter" id="slide-counter-label">Slide 01 / {total_pages:02d}</span>
                    <button class="btn-woday-secondary" onclick="stepSlide(1)">Next</button>
                </div>
                <div class="inspector-viewport">
                    {inspector_slides_html}
                </div>
            </div>

            <div class="caption-card">
                <div class="caption-header">
                    <div>
                        <div class="caption-title">LinkedIn &amp; Facebook Study Post</div>
                        <div style="font-size:12px; color:#575653; margin-top:2px;">
                            Matched to selected language ({lang_label})
                        </div>
                    </div>
                    <button class="btn-woday-primary" id="btn-copy-caption" onclick="copyCaption()">
                        Copy Caption &amp; Hashtags
                    </button>
                </div>

                <textarea class="caption-textarea" id="caption-box">{full_caption}</textarea>

                <div class="hashtag-row">
                    {"".join([f'<span class="hashtag-pill">#{h.strip("#")}</span>' for h in carousel_data.hashtags])}
                </div>
            </div>
        </div>

        <script>
            let activeSlideIndex = 0;
            const totalSlides = {total_pages};
            const defaultCaption = {caption_json};

            function selectSlide(idx) {{
                if (idx < 0 || idx >= totalSlides) return;
                activeSlideIndex = idx;

                for (let i = 0; i < totalSlides; i++) {{
                    const thumb = document.getElementById('thumb-btn-' + i);
                    const frame = document.getElementById('inspector-frame-' + i);
                    if (i === idx) {{
                        thumb.classList.add('active');
                        frame.classList.add('active');
                    }} else {{
                        thumb.classList.remove('active');
                        frame.classList.remove('active');
                    }}
                }}

                const numStr = String(idx + 1).padStart(2, '0');
                const totStr = String(totalSlides).padStart(2, '0');
                document.getElementById('slide-counter-label').innerText = `Slide ${{numStr}} / ${{totStr}}`;
            }}

            function stepSlide(delta) {{
                let next = activeSlideIndex + delta;
                if (next < 0) next = totalSlides - 1;
                if (next >= totalSlides) next = 0;
                selectSlide(next);
            }}

            async function downloadActiveSlide() {{
                const btn = document.getElementById('btn-dl-single');
                const origText = btn.innerText;
                btn.innerText = 'Exporting PNG...';
                try {{
                    await document.fonts.ready;
                    const node = document.getElementById('niw-export-slide-' + activeSlideIndex);
                    const dataUrl = await htmlToImage.toPng(node, {{
                        width: 1000,
                        height: 1250,
                        pixelRatio: 1.25,
                        cacheBust: true
                    }});
                    const link = document.createElement('a');
                    link.download = `NIWNOTES_Slide_${{String(activeSlideIndex + 1).padStart(2, '0')}}.png`;
                    link.href = dataUrl;
                    link.click();
                    btn.innerText = 'Downloaded PNG';
                }} catch (err) {{
                    console.error(err);
                    btn.innerText = 'Retry Download';
                }}
                setTimeout(() => {{ btn.innerText = origText; }}, 2000);
            }}

            async function downloadAllSlidesZip() {{
                const btn = document.getElementById('btn-dl-zip');
                const origText = btn.innerText;
                try {{
                    await document.fonts.ready;
                    const zip = new JSZip();
                    for (let i = 0; i < totalSlides; i++) {{
                        btn.innerText = `Rendering ${{i + 1}} / ${{totalSlides}}...`;
                        const frame = document.getElementById('inspector-frame-' + i);
                        const wasActive = frame.classList.contains('active');
                        if (!wasActive) {{
                            frame.style.display = 'block';
                            frame.style.position = 'fixed';
                            frame.style.left = '-9999px';
                        }}

                        const node = document.getElementById('niw-export-slide-' + i);
                        const dataUrl = await htmlToImage.toPng(node, {{
                            width: 1000,
                            height: 1250,
                            pixelRatio: 1.25
                        }});
                        const base64Data = dataUrl.split(',')[1];
                        zip.file(`NIWNOTES_Slide_${{String(i + 1).padStart(2, '0')}}.png`, base64Data, {{base64: true}});

                        if (!wasActive) {{
                            frame.style.display = '';
                            frame.style.position = '';
                            frame.style.left = '';
                        }}
                    }}
                    zip.file('social_post_caption.txt', document.getElementById('caption-box').value);
                    btn.innerText = 'Packing ZIP...';
                    const content = await zip.generateAsync({{type: 'blob'}});
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(content);
                    link.download = `NIWNOTES_${{totalSlides}}_Pages_Study_Pack.zip`;
                    link.click();
                    btn.innerText = 'ZIP Downloaded';
                }} catch (err) {{
                    console.error(err);
                    btn.innerText = 'Retry ZIP';
                }}
                setTimeout(() => {{ btn.innerText = origText; }}, 2400);
            }}

            function copyCaption() {{
                const btn = document.getElementById('btn-copy-caption');
                const txt = document.getElementById('caption-box').value;
                navigator.clipboard.writeText(txt);
                btn.innerText = 'Copied to Clipboard';
                setTimeout(() => {{ btn.innerText = 'Copy Caption & Hashtags'; }}, 2000);
            }}
        </script>
    </body>
    </html>
    """
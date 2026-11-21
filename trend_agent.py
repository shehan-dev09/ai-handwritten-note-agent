from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from note_generator import get_working_models
from pydantic import BaseModel, Field
import requests

load_dotenv()

# =====================================================================
# UNIVERSITY SUBJECT TRACKS & LIVE API QUERIES
# =====================================================================
UNIVERSITY_SUBJECTS = {
    "AI & Machine Learning": {
        "hn_query": "LLM OR AI Agent OR Machine Learning OR Deep Learning OR RAG",
        "devto_tag": "ai",
        "use_hf": True,
    },
    "Software Engineering & Full-Stack": {
        "hn_query": "Software Architecture OR React OR Nextjs OR Backend OR Microservices",
        "devto_tag": "webdev",
        "use_hf": False,
    },
    "Cybersecurity & Ethical Hacking": {
        "hn_query": "Cybersecurity OR Zero Trust OR Vulnerability OR Cryptography OR Pentesting",
        "devto_tag": "security",
        "use_hf": False,
    },
    "Data Science & Big Data Analytics": {
        "hn_query": "Data Engineering OR SQL OR Apache Spark OR Pandas OR Data Pipeline",
        "devto_tag": "datascience",
        "use_hf": False,
    },
    "Cloud Computing & DevOps": {
        "hn_query": "Kubernetes OR Docker OR AWS OR Terraform OR CI CD",
        "devto_tag": "devops",
        "use_hf": False,
    },
    "Computer Networks & Distributed Systems": {
        "hn_query": "Distributed Systems OR TCP IP OR gRPC OR Load Balancing OR Consensus",
        "devto_tag": "architecture",
        "use_hf": False,
    },
    "IoT, Robotics & Embedded Systems": {
        "hn_query": "Robotics OR Embedded OR RTOS OR Arduino OR Edge AI",
        "devto_tag": "iot",
        "use_hf": False,
    },
    "UI/UX & Product Engineering": {
        "hn_query": "Design Systems OR UI UX OR Frontend Performance OR Accessibility",
        "devto_tag": "ux",
        "use_hf": False,
    },
}


class ViralTopic(BaseModel):
    topic_title: str = Field(
        description="Clear, specific technical concept title suitable for a 5-page university study note"
    )
    category: str = Field(
        description="Sub-discipline tag (e.g. GenAI, Backend, Cloud, Security)"
    )
    why_it_is_viral: str = Field(
        description="1 short sentence on why students and engineers should learn this now"
    )
    beginner_hook: str = Field(
        description="Engaging hook question for social media post"
    )


class TrendingTopicsList(BaseModel):
    topics: list[ViralTopic] = Field(
        description="Top 5 trending study topics for university students",
        min_length=5,
        max_length=5,
    )


def _fetch_hf() -> list[str]:
    try:
        resp = requests.get("https://huggingface.co/api/daily_papers", timeout=4)
        if resp.status_code == 200:
            return [
                f"[HF Research] {item.get('title', '')}" for item in resp.json()[:8]
            ]
    except Exception:
        pass
    return []


def _fetch_hn(query: str) -> list[str]:
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={requests.utils.quote(query)}&tags=story&hitsPerPage=10"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            return [
                f"[Tech Trend] {hit.get('title', '')}"
                for hit in resp.json().get("hits", [])
                if hit.get("title")
            ]
    except Exception:
        pass
    return []


def _fetch_devto(tag: str) -> list[str]:
    try:
        url = f"https://dev.to/api/articles?tag={tag}&top=7&per_page=10"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            return [
                f"[Developer Guide] {art.get('title', '')}" for art in resp.json()[:8]
            ]
    except Exception:
        pass
    return []


def fetch_raw_subject_news(subject_category: str = "AI & Machine Learning") -> str:
    """Concurrently scrapes live technical feeds for the selected university subject in <2 seconds."""
    cfg = UNIVERSITY_SUBJECTS.get(
        subject_category, UNIVERSITY_SUBJECTS["AI & Machine Learning"]
    )
    headlines = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(_fetch_hn, cfg["hn_query"]),
            executor.submit(_fetch_devto, cfg["devto_tag"]),
        ]
        if cfg["use_hf"]:
            futures.append(executor.submit(_fetch_hf))

        for fut in futures:
            headlines.extend(fut.result())

    if not headlines:
        return f"Core university concepts and modern industry architectures in {subject_category}."

    return "\n".join(headlines[:20])


def discover_viral_topics(
    working_models: list[str],
    subject_category: str = "AI & Machine Learning",
    api_key: str = None,
) -> list[ViralTopic]:
    """Uses Gemini 3.x to extract 5 high-value study topics for the chosen university subject."""
    resolved_key = api_key or os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=resolved_key)
    raw_news = fetch_raw_subject_news(subject_category)

    prompt = f"""
    You are an Academic & Industry Curriculum Scout for 'NIWNOTES', a university student learning platform.
    Target University Discipline: "{subject_category}"

    Live Technical Feed Signals:
    {raw_news}

    Select exactly 5 high-impact, educational concepts in "{subject_category}" that university students
    can turn into viral 5-page study carousels on LinkedIn and Facebook.
    Make each topic title crystal clear and focused on teaching a core concept (e.g. "How X Works: Architecture & Use Cases").
    """

    for model_name in working_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TrendingTopicsList,
                    temperature=0.4,
                ),
            )
            parsed = TrendingTopicsList.model_validate_json(response.text)
            return parsed.topics
        except Exception:
            continue

    raise RuntimeError(
        "All Gemini models failed while discovering topics. Please retry."
    )
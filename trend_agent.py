import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import requests

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

client = genai.Client(api_key=API_KEY)


class ViralTopic(BaseModel):
    topic_title: str = Field(
        description="Clear, educational AI/ML topic title suitable for a 5-page study note"
    )
    why_viral: str = Field(
        description="1 short sentence on why this topic is trending and valuable right now"
    )


class TrendingTopicsList(BaseModel):
    topics: list[ViralTopic] = Field(
        description="List of exactly 5 high-impact viral AI/ML topics"
    )


def fetch_raw_ai_news() -> list[str]:
    """Fetches real-time trending AI/ML discussions from HuggingFace Papers & HackerNews (100% Free, No API Keys)."""
    headlines = []
    headers = {"User-Agent": "Mozilla/5.0 (AI-Study-Note-Agent/1.0)"}

    # 1. Fetch from HuggingFace Daily Trending Papers API
    try:
        resp = requests.get(
            "https://huggingface.co/api/daily_papers",
            headers=headers,
            timeout=8,
        )
        if resp.status_code == 200:
            papers = resp.json()
            for item in papers[:10]:
                title = item.get("title")
                if title:
                    headlines.append(f"[HuggingFace Trending] {title}")
    except Exception:
        pass

    # 2. Fetch from HackerNews Algolia API (Latest AI/LLM stories)
    try:
        hn_url = "https://hn.algolia.com/api/v1/search?query=LLM+OR+AI+Agent+OR+Machine+Learning&tags=story&hitsPerPage=12"
        resp = requests.get(hn_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            for hit in hits:
                title = hit.get("title")
                if title:
                    headlines.append(f"[HackerNews AI] {title}")
    except Exception:
        pass

    return headlines


def discover_viral_topics(working_models: list[str]) -> list[ViralTopic]:
    """Analyzes live AI news and curates 5 beginner-friendly viral study note topics."""
    print(
        "[INFO] Trend Researcher Agent is scanning HuggingFace & HackerNews for live AI trends..."
    )
    raw_headlines = fetch_raw_ai_news()

    news_context = (
        "\n".join(raw_headlines)
        if raw_headlines
        else "General trending AI/ML topics in 2026"
    )

    prompt = f"""
    You are an AI/ML Trend Researcher Agent for a viral LinkedIn & Facebook Tech Educator.
    Below are live trending headlines from the AI community today:
    {news_context}

    Based on these live trends (and current high-demand AI/ML concepts), extract 5 killer educational topics that can be explained as a 5-page handwritten study note series.
    - Make sure the topics are conceptual and educational (e.g., "How MCP (Model Context Protocol) Works", "Agentic RAG vs Traditional RAG", "LoRA & QLoRA Fine-Tuning Explained", "How Reasoning LLMs Work", etc.) rather than just company gossip.
    """

    for model_name in working_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TrendingTopicsList,
                    temperature=0.6,
                ),
            )
            parsed = TrendingTopicsList.model_validate_json(response.text)
            return parsed.topics
        except Exception:
            continue

    # Fallback topics if all servers are busy
    return [
        ViralTopic(
            topic_title="Agentic RAG vs Traditional RAG",
            why_viral="Everyone is upgrading basic RAG pipelines to autonomous AI agents.",
        ),
        ViralTopic(
            topic_title="How MCP (Model Context Protocol) Works",
            why_viral="The new standard for connecting AI models to external tools and data.",
        ),
        ViralTopic(
            topic_title="Fine-Tuning LLMs with LoRA & QLoRA",
            why_viral="Essential technique for training custom AI models on consumer GPUs.",
        ),
        ViralTopic(
            topic_title="Vector Databases & Embeddings Explained",
            why_viral="The backbone of semantic search and modern AI memory systems.",
        ),
        ViralTopic(
            topic_title="How Reasoning Models (Chain-of-Thought) Work",
            why_viral="Thinking models are dominating coding and math benchmarks.",
        ),
    ]
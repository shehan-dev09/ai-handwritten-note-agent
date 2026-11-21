import os
from functools import lru_cache
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor
import requests
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class ViralTopic(BaseModel):
    title: str = Field(description="Clean, high-impact academic/industry topic title")
    category: str = Field(description="Sub-discipline badge (e.g., LLM Systems, Cloud Native, Zero-Trust)")
    why_viral: str = Field(description="1-sentence explanation of why students and engineers must learn this now")


class ViralTopicsList(BaseModel):
    topics: List[ViralTopic]


# University Subject Catalog with Pre-Ranked Instant Leaderboard Topics (Emoji-Free)
UNIVERSITY_SUBJECTS: Dict[str, Dict] = {
    "AI & Machine Learning": {
        "code": "AI",
        "icon": "[AI]",
        "hn_query": "LLM OR Transformer OR Agentic AI",
        "devto_tag": "ai",
        "use_hf": True,
        "default_ranked": [
            ViralTopic(
                title="Agentic AI Workflows & Multi-Agent Orchestration",
                category="Autonomous AI",
                why_viral="Top skill requested in AI engineering internships and modern research labs.",
            ),
            ViralTopic(
                title="Retrieval-Augmented Generation (RAG) Architecture",
                category="LLM Systems",
                why_viral="Standard enterprise pattern for grounding LLMs on private university or company data.",
            ),
            ViralTopic(
                title="Transformer Self-Attention & KV-Cache Optimization",
                category="Deep Learning",
                why_viral="Core university exam topic and technical interview favorite for ML roles.",
            ),
            ViralTopic(
                title="LoRA & QLoRA Parameter-Efficient Fine-Tuning",
                category="Model Training",
                why_viral="Enables students to fine-tune billion-parameter models on a single free GPU.",
            ),
            ViralTopic(
                title="Vision-Language Models (VLMs) & Multimodal Reasoning",
                category="Multimodal AI",
                why_viral="Bridges computer vision and NLP for next-generation document and video intelligence.",
            ),
        ],
    },
    "Software Engineering & Full-Stack": {
        "code": "SE",
        "icon": "[SE]",
        "hn_query": "System Design OR Microservices OR TypeScript OR Rust",
        "devto_tag": "webdev",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Event-Driven Microservices with Kafka & RabbitMQ",
                category="System Design",
                why_viral="Essential architecture pattern for scalable backend engineering interviews.",
            ),
            ViralTopic(
                title="Clean Architecture & Domain-Driven Design (DDD)",
                category="Software Architecture",
                why_viral="Separates business logic from frameworks for maintainable university capstone projects.",
            ),
            ViralTopic(
                title="React Server Components & Next.js App Router Internals",
                category="Full-Stack Web",
                why_viral="Redefines modern frontend-to-backend rendering and hydration performance.",
            ),
            ViralTopic(
                title="Database Indexing, B-Trees & Query Execution Plans",
                category="Database Internals",
                why_viral="High-yield DBMS exam concept that directly solves production latency bottlenecks.",
            ),
            ViralTopic(
                title="OAuth 2.1, Passkeys & Modern Session Security",
                category="Auth Systems",
                why_viral="Every full-stack developer must implement secure, token-based authentication.",
            ),
        ],
    },
    "Cybersecurity & Ethical Hacking": {
        "code": "SEC",
        "icon": "[SEC]",
        "hn_query": "Cybersecurity OR Zero Trust OR OWASP OR Vulnerability",
        "devto_tag": "security",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Zero-Trust Network Architecture (ZTNA) Explained",
                category="Network Security",
                why_viral="Replaced traditional perimeter firewalls as the global enterprise security standard.",
            ),
            ViralTopic(
                title="OWASP Top 10: Prompt Injection & Broken Access Control",
                category="AppSec",
                why_viral="Critical vulnerability taxonomy for ethical hacking labs and security audits.",
            ),
            ViralTopic(
                title="Public Key Infrastructure (PKI), TLS 1.3 & mTLS Handshakes",
                category="Cryptography",
                why_viral="Foundation of secure internet communication and university cryptography exams.",
            ),
            ViralTopic(
                title="Linux Privilege Escalation & Container Escape Vectors",
                category="Red Teaming",
                why_viral="Core practical skill for Capture The Flag (CTF) competitions and OS security.",
            ),
            ViralTopic(
                title="SIEM Threat Hunting & MITRE ATT&CK Framework",
                category="SOC Operations",
                why_viral="Blue-team methodology used by security analysts to detect advanced intrusions.",
            ),
        ],
    },
    "Data Science & Big Data Analytics": {
        "code": "DS",
        "icon": "[DS]",
        "hn_query": "Data Engineering OR DuckDB OR Apache Spark OR Polars",
        "devto_tag": "datascience",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Medallion Lakehouse Architecture (Bronze, Silver, Gold)",
                category="Data Engineering",
                why_viral="Industry blueprint for organizing raw data into analytics-ready warehouse tables.",
            ),
            ViralTopic(
                title="Apache Spark Distributed Execution & Shuffle Optimization",
                category="Big Data",
                why_viral="Key big-data syllabus module for processing terabyte-scale datasets in memory.",
            ),
            ViralTopic(
                title="Vector Databases & HNSW Approximate Nearest Neighbor Search",
                category="Data Indexing",
                why_viral="Powers semantic search and recommendation systems at millisecond latency.",
            ),
            ViralTopic(
                title="Feature Engineering, Data Leakage & Cross-Validation",
                category="Applied ML",
                why_viral="Determines 80% of real-world predictive model accuracy in Kaggle and research.",
            ),
            ViralTopic(
                title="Bayesian A/B Testing & Causal Inference in Product Analytics",
                category="Statistical Modeling",
                why_viral="Separates correlation from causation in high-stakes data science decisions.",
            ),
        ],
    },
    "Cloud Computing & DevOps": {
        "code": "CLD",
        "icon": "[CLD]",
        "hn_query": "Kubernetes OR Docker OR Terraform OR eBPF",
        "devto_tag": "devops",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Kubernetes Pod Scheduling, Control Plane & CNI Networking",
                category="Container Orchestration",
                why_viral="De-facto operating system of the cloud for deploying resilient microservices.",
            ),
            ViralTopic(
                title="GitOps Continuous Delivery with ArgoCD & Terraform IaC",
                category="DevOps Automation",
                why_viral="Automates cloud infrastructure provisioning with auditable Git pull requests.",
            ),
            ViralTopic(
                title="eBPF Observability & High-Performance Linux Kernel Tracing",
                category="Cloud Native",
                why_viral="Revolutionizes networking, security monitoring, and profiling without kernel changes.",
            ),
            ViralTopic(
                title="Multi-Stage Docker Builds & Distroless Image Hardening",
                category="Containerization",
                why_viral="Reduces production container size by 90% while eliminating CVE attack surfaces.",
            ),
            ViralTopic(
                title="Serverless Cold Starts, Edge Workers & Distributed Caching",
                category="Cloud Architecture",
                why_viral="Balances cost efficiency and sub-50ms global latency for modern web apps.",
            ),
        ],
    },
    "Computer Networks & Distributed Systems": {
        "code": "NET",
        "icon": "[NET]",
        "hn_query": "Distributed Systems OR Raft Consensus OR QUIC OR HTTP3",
        "devto_tag": "compsci",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Raft & Paxos Distributed Consensus Algorithms",
                category="Distributed Systems",
                why_viral="Explains how fault-tolerant databases agree on state even when nodes crash.",
            ),
            ViralTopic(
                title="CAP Theorem, PACELC & Eventual Consistency Trade-offs",
                category="System Theory",
                why_viral="Foundational theorem tested in every distributed computing university exam.",
            ),
            ViralTopic(
                title="HTTP/3, QUIC Protocol & UDP Multiplexing Internals",
                category="Network Protocols",
                why_viral="Eliminates TCP head-of-line blocking for faster mobile and lossy network transfers.",
            ),
            ViralTopic(
                title="Consistent Hashing & Virtual Nodes in Load Balancers",
                category="Scalability",
                why_viral="Prevents massive cache stampedes when scaling distributed storage clusters.",
            ),
            ViralTopic(
                title="gRPC, Protocol Buffers & Bidirectional Streaming",
                category="IPC Frameworks",
                why_viral="High-performance binary alternative to REST JSON for internal microservice calls.",
            ),
        ],
    },
    "IoT, Robotics & Embedded Systems": {
        "code": "IOT",
        "icon": "[IOT]",
        "hn_query": "Embedded Systems OR ROS2 OR RISC-V OR Edge AI",
        "devto_tag": "iot",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="RTOS Task Scheduling, Priority Inversion & Mutexes",
                category="Embedded OS",
                why_viral="Critical for deterministic real-time behavior in robotics, drones, and automotive ECUs.",
            ),
            ViralTopic(
                title="MQTT vs CoAP Protocols for Low-Power IoT Sensor Meshes",
                category="IoT Networking",
                why_viral="Enables reliable telemetry over constrained bandwidth and battery-powered nodes.",
            ),
            ViralTopic(
                title="TinyML & Quantized Neural Networks on Microcontrollers",
                category="Edge AI",
                why_viral="Runs voice and anomaly detection directly on ESP32 and ARM Cortex-M chips.",
            ),
            ViralTopic(
                title="ROS 2 (Robot Operating System) Nodes, Topics & DDS Middleware",
                category="Robotics",
                why_viral="Global standard framework for building autonomous mobile robots and SLAM pipelines.",
            ),
            ViralTopic(
                title="RISC-V Open Instruction Set Architecture & Custom Accelerators",
                category="Computer Architecture",
                why_viral="Reshaping semiconductor design with open-source hardware extensibility.",
            ),
        ],
    },
    "UI/UX & Product Engineering": {
        "code": "UX",
        "icon": "[UX]",
        "hn_query": "Design Systems OR UI UX OR Web Accessibility OR Figma",
        "devto_tag": "design",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Design Tokens & Multi-Brand Component Architecture",
                category="Design Systems",
                why_viral="Bridges Figma variables directly to production CSS and mobile design systems.",
            ),
            ViralTopic(
                title="Cognitive Load Theory, Hick's Law & Fitts's Law in UI",
                category="Human-Computer Interaction",
                why_viral="Core HCI university principles that make interfaces intuitive and frictionless.",
            ),
            ViralTopic(
                title="WCAG 2.2 Accessibility, ARIA Roles & Keyboard Navigation",
                category="Inclusive Design",
                why_viral="Mandatory engineering standard for building usable, legally compliant web products.",
            ),
            ViralTopic(
                title="Optimistic UI Updates & Skeleton Perceived Performance",
                category="Interaction Design",
                why_viral="Makes web applications feel instantaneous even over slow network connections.",
            ),
            ViralTopic(
                title="Jobs-To-Be-Done (JTBD) & Continuous Product Discovery",
                category="Product Strategy",
                why_viral="Helps student founders build features users actually need instead of guessing.",
            ),
        ],
    },
}


@lru_cache(maxsize=4)
def get_genai_client(api_key: str) -> genai.Client:
    """Caches the Gemini API client to avoid repeated TLS/session initialization overhead."""
    return genai.Client(api_key=api_key)


@lru_cache(maxsize=4)
def get_working_models(api_key: str) -> List[str]:
    """
    Prioritizes ultra-low-latency Flash-Lite models first for maximum speed,
    followed by standard Flash models. Cached per API key.
    """
    client = get_genai_client(api_key)
    preferred_order = [
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-2.0-flash",
    ]
    available = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name and "tts" not in name and "image" not in name:
                available.append(name)
    except Exception:
        return preferred_order

     prioritized = [m for m in preferred_order if m in available]
    for m in available:
        if "flash" in m and m not in prioritized:
            prioritized.append(m)

    return prioritized if prioritized else preferred_order


def get_instant_ranked_topics(subject_category: str) -> List[ViralTopic]:
    """Returns curated top-5 ranked university topics in 0ms without network wait."""
    subject_cfg = UNIVERSITY_SUBJECTS.get(
        subject_category, UNIVERSITY_SUBJECTS["AI & Machine Learning"]
    )
    return subject_cfg.get("default_ranked", [])


def fetch_raw_subject_news(subject_category: str) -> str:
    """
    Concurrently fetches live Signals from HuggingFace, HackerNews, and Dev.to
    with a strict 3.5-second timeout so UI refreshes never hang.
    """
    subject_cfg = UNIVERSITY_SUBJECTS.get(
        subject_category, UNIVERSITY_SUBJECTS["AI & Machine Learning"]
    )
    news_items: List[str] = []

    def _fetch_hf():
        if not subject_cfg.get("use_hf", False):
            return []
        try:
            resp = requests.get("https://huggingface.co/api/daily_papers", timeout=3.5)
            if resp.status_code == 200:
                return [
                    f"[Paper] {item.get('title', '')}"
                    for item in resp.json()[:5]
                    if item.get("title")
                ]
        except Exception:
            pass
        return []

    def _fetch_hn():
        try:
            q = requests.utils.quote(subject_cfg.get("hn_query", subject_category))
            resp = requests.get(
                f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage=6",
                timeout=3.5,
            )
            if resp.status_code == 200:
                return [
                    f"[Tech News] {hit.get('title', '')}"
                    for hit in resp.json().get("hits", [])
                    if hit.get("title")
                ]
        except Exception:
            pass
        return []

    def _fetch_devto():
        try:
            tag = subject_cfg.get("devto_tag", "programming")
            resp = requests.get(
                f"https://dev.to/api/articles?tag={tag}&top=2&per_page=6",
                timeout=3.5,
            )
            if resp.status_code == 200:
                return [
                    f"[Article] {art.get('title', '')} - {art.get('description', '')}"
                    for art in resp.json()
                    if art.get("title")
                ]
        except Exception:
            pass
        return []

    with ThreadPoolExecutor(max_workers=3) as pool:
        f_hf = pool.submit(_fetch_hf)
        f_hn = pool.submit(_fetch_hn)
        f_dev = pool.submit(_fetch_devto)
        news_items.extend(f_hf.result())
        news_items.extend(f_hn.result())
        news_items.extend(f_dev.result())

    if not news_items:
        return "\n".join(
            [f"[Curated] {t.title} - {t.why_viral}" for t in subject_cfg.get("default_ranked", [])]
        )

    return "\n".join(news_items)


def discover_viral_topics(
    api_key: str | None = None,
    subject_category: str = "AI & Machine Learning",
) -> List[ViralTopic]:
    """
    Uses Gemini with thinking_budget=0 for fast live topic ranking.
    Falls back immediately to curated ranked topics if quota is reached.
    """
    active_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not active_key:
        return get_instant_ranked_topics(subject_category)

    client = get_genai_client(active_key)
    raw_news = fetch_raw_subject_news(subject_category)

    prompt = f"""
    You are an Academic Curriculum & Tech Trend Curator for University Students studying '{subject_category}'.
    Analyze the following live technical signals and rank the Top 5 most valuable, high-impact topics for university study notes and LinkedIn/Facebook educational carousels.
    Do NOT use any emojis in titles, categories, or descriptions.

    Live Signals for {subject_category}:
    {raw_news}

    Return 5 ranked topics ordered from #1 (highest impact) to #5.
    """

    for model_name in get_working_models(active_key):
        try:
            config_kwargs = {
                "response_mime_type": "application/json",
                "response_schema": ViralTopicsList,
                "temperature": 0.3,
            }
            if "2.5" in model_name or "3." in model_name:
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            parsed: ViralTopicsList = response.parsed
            if parsed and parsed.topics:
                return parsed.topics[:5]
        except Exception:
            continue

    return get_instant_ranked_topics(subject_category)
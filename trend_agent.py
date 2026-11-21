import os
import requests
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


# =====================================================================
# Structured Output Schema for Trending University Topics
# =====================================================================
class ViralTopic(BaseModel):
    title: str = Field(description="Catchy, clear title of the trending topic or lecture concept")
    category: str = Field(description="Sub-topic or academic module badge")
    summary: str = Field(description="2-sentence explanation of why this is important for students right now")
    source_Inspiration: str = Field(description="Where this trend is coming from or core curriculum pillar")


class TrendingTopicsList(BaseModel):
    topics: List[ViralTopic] = Field(description="List of the top 5 trending topics for the selected subject")


# =====================================================================
# University Subject Catalog + Instant Curated Ranked Topics (#1 - #5)
# =====================================================================
UNIVERSITY_SUBJECTS: Dict[str, Dict[str, Any]] = {
    "AI & Machine Learning": {
        "code": "AI",
        "hn_query": "LLM OR AI agent OR transformer OR RAG",
        "devto_tag": "ai",
        "use_hf": True,
        "default_ranked": [
            ViralTopic(
                title="Retrieval-Augmented Generation (RAG) & Vector Databases",
                category="Applied GenAI",
                summary="How modern AI systems connect LLMs with private knowledge bases using embeddings and cosine similarity to eliminate hallucinations.",
                source_Inspiration="University AI Lab & Industry Standard"
            ),
            ViralTopic(
                title="Multi-Agent AI Workflows & Tool-Calling Architectures",
                category="Agentic Systems",
                summary="Designing autonomous AI agents that plan tasks, call external APIs, and collaborate using ReAct and supervisor-worker patterns.",
                source_Inspiration="HuggingFace Daily & AI Engineering"
            ),
            ViralTopic(
                title="Transformer Self-Attention Mechanism From Scratch",
                category="Deep Learning Core",
                summary="Breaking down Query, Key, and Value (QKV) matrices, scaled dot-product attention, and positional encoding for university exams.",
                source_Inspiration="CS224N / Deep Learning Curriculum"
            ),
            ViralTopic(
                title="LoRA & QLoRA: Parameter-Efficient Fine-Tuning (PEFT)",
                category="Model Optimization",
                summary="How to fine-tune billion-parameter open-source LLMs on a single consumer GPU by freezing weights and training low-rank adapters.",
                source_Inspiration="ML Systems Research"
            ),
            ViralTopic(
                title="Convolutional Neural Networks (CNNs) & Vision Transformers (ViT)",
                category="Computer Vision",
                summary="Comparing spatial convolution filters with patch-based self-attention for image classification and object detection.",
                source_Inspiration="Computer Vision Module"
            ),
        ],
    },
    "Software Engineering & Full-Stack": {
        "code": "SE",
        "hn_query": "software architecture OR microservices OR react OR backend",
        "devto_tag": "webdev",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Clean Architecture & SOLID Principles in Production",
                category="Software Design",
                summary="Structuring maintainable codebases using dependency inversion, single responsibility, and decoupled domain layers.",
                source_Inspiration="Software Engineering Core"
            ),
            ViralTopic(
                title="Microservices vs Modular Monoliths: System Design Guide",
                category="System Architecture",
                summary="Understanding service boundaries, API gateways, event-driven messaging (Kafka/RabbitMQ), and when to avoid premature distribution.",
                source_Inspiration="High-Scale System Design"
            ),
            ViralTopic(
                title="REST vs GraphQL vs gRPC: Modern API Design Patterns",
                category="Backend Engineering",
                summary="Comparing payload efficiency, HTTP/2 multiplexing with Protocol Buffers, and schema-driven API queries for full-stack apps.",
                source_Inspiration="Full-Stack Engineering Track"
            ),
            ViralTopic(
                title="Database Indexing, B-Trees & ACID Transaction Isolation",
                category="Database Internals",
                summary="How relational databases execute fast lookups using B+ Trees and prevent race conditions with MVCC and isolation levels.",
                source_Inspiration="DBMS University Exam Essential"
            ),
            ViralTopic(
                title="JWT Authentication, OAuth 2.0 & Session Security",
                category="Web Security",
                summary="Complete authentication lifecycle using Access/Refresh tokens, PKCE flows, and HTTPOnly cookies in modern web applications.",
                source_Inspiration="Web Development Best Practices"
            ),
        ],
    },
    "Cybersecurity & Ethical Hacking": {
        "code": "SEC",
        "hn_query": "cybersecurity OR zero-day OR cryptography OR OWASP",
        "devto_tag": "security",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="OWASP Top 10: SQL Injection, XSS & CSRF Defense",
                category="Application Security",
                summary="How attackers exploit unsanitized inputs in web apps and how parameterized queries, CSP headers, and CSRF tokens stop them.",
                source_Inspiration="OWASP Foundation & AppSec"
            ),
            ViralTopic(
                title="Zero-Trust Security Architecture & Mutual TLS (mTLS)",
                category="Network Security",
                summary="Moving from perimeter firewalls to 'Never Trust, Always Verify' using continuous identity verification and micro-segmentation.",
                source_Inspiration="Enterprise Security Standard"
            ),
            ViralTopic(
                title="Public Key Cryptography: RSA, Diffie-Hellman & Elliptic Curves",
                category="Applied Cryptography",
                summary="How asymmetric key exchange, digital signatures, and TLS 1.3 handshakes secure internet traffic against eavesdropping.",
                source_Inspiration="Cryptography & Network Security"
            ),
            ViralTopic(
                title="Privilege Escalation & Active Directory Attack Vectors",
                category="Ethical Hacking / Red Team",
                summary="Understanding Kerberoasting, Pass-the-Hash, and Linux SUID misconfigurations during penetration testing engagements.",
                source_Inspiration="Ethical Hacking Lab"
            ),
            ViralTopic(
                title="SIEM, SOC Operations & Incident Response Playbooks",
                category="Blue Team Defense",
                summary="Detecting lateral movement, analyzing log telemetry, and executing the PICERL incident response lifecycle under attack.",
                source_Inspiration="Cyber Defense Curriculum"
            ),
        ],
    },
    "Data Science & Big Data Analytics": {
        "code": "DS",
        "hn_query": "data science OR apache spark OR duckdb OR data engineering",
        "devto_tag": "datascience",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Medallion Data Lakehouse Architecture (Bronze, Silver, Gold)",
                category="Data Engineering",
                summary="Combining the flexibility of Data Lakes with ACID transactions of Data Warehouses using Delta Lake and Apache Iceberg.",
                source_Inspiration="Modern Data Stack"
            ),
            ViralTopic(
                title="Apache Spark Internals: RDDs, DAG Scheduler & Lazy Evaluation",
                category="Big Data Processing",
                summary="How Spark distributes petabyte-scale data transformations across cluster worker nodes using in-memory DAG execution.",
                source_Inspiration="Big Data Analytics Module"
            ),
            ViralTopic(
                title="Gradient Boosting Machines: XGBoost, LightGBM & CatBoost",
                category="Tabular ML",
                summary="Why decision tree ensembles dominate structured data competitions through sequential residual fitting and regularization.",
                source_Inspiration="Applied Data Science"
            ),
            ViralTopic(
                title="Dimensionality Reduction: PCA, t-SNE & UMAP Explained",
                category="Statistical Learning",
                summary="Compressing high-dimensional feature spaces using eigenvectors and manifold learning while preserving critical variance.",
                source_Inspiration="Mathematics for Data Science"
            ),
            ViralTopic(
                title="A/B Testing, Hypothesis Testing & Bayesian Inference",
                category="Statistical Decision Making",
                summary="Calculating p-values, statistical power, confidence intervals, and avoiding false positives in product experiments.",
                source_Inspiration="Probability & Statistics Core"
            ),
        ],
    },
    "Cloud Computing & DevOps": {
        "code": "CLD",
        "hn_query": "kubernetes OR docker OR terraform OR devops OR cloud native",
        "devto_tag": "devops",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Kubernetes Architecture: Control Plane, Kubelet & Pods",
                category="Container Orchestration",
                summary="How the API Server, etcd, Scheduler, and Worker Nodes orchestrate self-healing, auto-scaling container clusters.",
                source_Inspiration="CNCF / Cloud Native Track"
            ),
            ViralTopic(
                title="Docker Internals: Linux Namespaces, cgroups & UnionFS",
                category="Containerization",
                summary="Why containers are lightweight processes rather than full VMs, and how multi-stage Dockerfiles shrink production images.",
                source_Inspiration="DevOps Engineering Core"
            ),
            ViralTopic(
                title="Infrastructure as Code (IaC) with Terraform & State Locking",
                category="Cloud Automation",
                summary="Provisioning reproducible AWS/GCP infrastructure declaratively using HCL modules, execution plans, and remote state backends.",
                source_Inspiration="Cloud Architecture Module"
            ),
            ViralTopic(
                title="CI/CD Pipelines: Blue-Green vs Canary Deployments",
                category="Release Engineering",
                summary="Automating build, test, security scanning, and zero-downtime production rollouts with GitHub Actions and ArgoCD.",
                source_Inspiration="Site Reliability Engineering"
            ),
            ViralTopic(
                title="Serverless Computing & Event-Driven Cloud Architectures",
                category="Cloud Native",
                summary="Building scale-to-zero backends using AWS Lambda, API Gateway, SQS queues, and understanding cold-start trade-offs.",
                source_Inspiration="Distributed Cloud Systems"
            ),
        ],
    },
    "Computer Networks & Distributed Systems": {
        "code": "NET",
        "hn_query": "distributed systems OR consensus OR raft OR TCP QUIC",
        "devto_tag": "architecture",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="CAP Theorem, PACELC & Eventual Consistency in Distributed DBs",
                category="Distributed Systems",
                summary="Why distributed data stores must trade off Consistency and Availability during network partitions, and how Quorum reads/writes work.",
                source_Inspiration="Distributed Systems Core"
            ),
            ViralTopic(
                title="Raft & Paxos Consensus Algorithms Explained Visually",
                category="Fault Tolerance",
                summary="How a cluster of unreliable servers agrees on a single source of truth using Leader Election, Log Replication, and Heartbeats.",
                source_Inspiration="MIT 6.824 / Distributed Computing"
            ),
            ViralTopic(
                title="TCP 3-Way Handshake, Congestion Control & HTTP/3 (QUIC)",
                category="Network Protocols",
                summary="Comparing reliable TCP byte streams with UDP-based QUIC multiplexing to eliminate head-of-line blocking on the modern web.",
                source_Inspiration="Computer Networks Exam Essential"
            ),
            ViralTopic(
                title="Consistent Hashing & Load Balancing at Global Scale",
                category="Scalability",
                summary="How distributed caches (Redis/Cassandra) and CDNs route millions of requests across dynamic server rings with minimal rehashing.",
                source_Inspiration="System Design & Networking"
            ),
            ViralTopic(
                title="OSI 7-Layer Model vs TCP/IP Stack: Complete Packet Journey",
                category="Networking Fundamentals",
                summary="Tracing how an HTTP request is encapsulated into TCP segments, IP packets, and Ethernet frames using ARP, DNS, and NAT.",
                source_Inspiration="Networking Fundamentals"
            ),
        ],
    },
    "IoT, Robotics & Embedded Systems": {
        "code": "IOT",
        "hn_query": "embedded systems OR RTOS OR robotics OR ESP32 OR MQTT",
        "devto_tag": "iot",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Real-Time Operating Systems (FreeRTOS): Tasks, Queues & Semaphores",
                category="Embedded Systems",
                summary="Deterministic task scheduling, priority inversion prevention, and inter-task communication on microcontrollers.",
                source_Inspiration="Embedded Systems Curriculum"
            ),
            ViralTopic(
                title="MQTT vs CoAP: Lightweight Protocols for IoT Sensor Networks",
                category="IoT Architecture",
                summary="How Publish-Subscribe brokers and Quality of Service (QoS 0, 1, 2) enable reliable telemetry over low-bandwidth links.",
                source_Inspiration="Internet of Things Module"
            ),
            ViralTopic(
                title="ROS 2 (Robot Operating System): Nodes, Topics & DDS Middleware",
                category="Robotics Engineering",
                summary="Building modular autonomous robots where sensor, perception, and actuator nodes communicate in real time.",
                source_Inspiration="Robotics & Automation Lab"
            ),
            ViralTopic(
                title="Hardware Communication Protocols: I2C, SPI & UART Compared",
                category="Microcontroller Interfacing",
                summary="Understanding clock synchronization, master-slave addressing, wiring topologies, and baud rates for embedded sensors.",
                source_Inspiration="Digital Electronics & Interfacing"
            ),
            ViralTopic(
                title="Edge AI & TinyML: Running Neural Networks on Microcontrollers",
                category="Edge Intelligence",
                summary="Using INT8 quantization and TensorFlow Lite Micro to run real-time voice and vision models on milliwatt-power chips.",
                source_Inspiration="Next-Gen IoT Research"
            ),
        ],
    },
    "UI/UX & Product Engineering": {
        "code": "UX",
        "hn_query": "design systems OR UX research OR frontend accessibility OR product design",
        "devto_tag": "design",
        "use_hf": False,
        "default_ranked": [
            ViralTopic(
                title="Design Systems Architecture: Design Tokens & Atomic Components",
                category="Design Engineering",
                summary="Bridging Figma and code using semantic color/spacing tokens and reusable Atomic Design primitives (Atoms, Molecules, Organisms).",
                source_Inspiration="Product Design Engineering"
            ),
            ViralTopic(
                title="Nielsen's 10 Usability Heuristics & Cognitive Load Theory",
                category="HCI / UX Fundamentals",
                summary="Applying Human-Computer Interaction laws (Hick's Law, Fitts's Law, Jakob's Law) to design intuitive, friction-free interfaces.",
                source_Inspiration="Human-Computer Interaction (HCI)"
            ),
            ViralTopic(
                title="WCAG 2.2 Web Accessibility: ARIA Roles, Contrast & Keyboard Nav",
                category="Inclusive Design",
                summary="Engineering accessible web applications for screen readers and assistive technologies using semantic HTML and focus management.",
                source_Inspiration="Frontend & UX Standards"
            ),
            ViralTopic(
                title="User Research to Wireframes: Double Diamond Product Workflow",
                category="Product Discovery",
                summary="Moving from user interviews and Jobs-To-Be-Done (JTBD) to low-fidelity wireframes, interactive prototypes, and usability testing.",
                source_Inspiration="Product Management & UX"
            ),
            ViralTopic(
                title="Micro-Interactions, Perceived Performance & Skeleton States",
                category="Interaction Design",
                summary="How optimistic UI updates, spring physics animations, and skeleton loaders make web and mobile apps feel instant.",
                source_Inspiration="Modern UI Engineering"
            ),
        ],
    },
}


def get_default_ranked_topics(subject_category: str) -> List[ViralTopic]:
    """Returns the instant top-5 ranked study topics for a subject without waiting on network calls."""
    subject_cfg = UNIVERSITY_SUBJECTS.get(subject_category, UNIVERSITY_SUBJECTS["AI & Machine Learning"])
    return subject_cfg["default_ranked"]


@lru_cache(maxsize=8)
def get_genai_client(api_key: str) -> genai.Client:
    """Reuses a single HTTP/TLS connection pool per API key for faster requests."""
    return genai.Client(api_key=api_key)


@lru_cache(maxsize=8)
def get_working_models(api_key: str) -> List[str]:
    """
    Discovers and caches available Gemini Flash models for the given API key.
    Prioritizes 'flash-lite' models first for 2x-3x faster response times.
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

    try:
        available_names = set()
        for m in client.models.list():
            short_name = m.name.replace("models/", "")
            if "gemini" in short_name and "flash" in short_name and "tts" not in short_name and "image" not in short_name:
                available_names.add(short_name)

        ranked: List[str] = []
        for pref in preferred_order:
            if pref in available_names:
                ranked.append(pref)

        for name in sorted(available_names):
            if name not in ranked:
                ranked.append(name)

        if ranked:
            return ranked
    except Exception:
        pass

    return ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]


def _fetch_hf_papers() -> List[str]:
    """Fetches daily AI research papers from HuggingFace."""
    items: List[str] = []
    try:
        resp = requests.get("https://huggingface.co/api/daily_papers", timeout=3)
        if resp.status_code == 200:
            for item in resp.json()[:5]:
                title = item.get("title", "").replace("\n", " ")
                summary = item.get("paper", {}).get("summary", "").replace("\n", " ")[:180]
                if title:
                    items.append(f"[Research Paper] {title} - {summary}")
    except Exception:
        pass
    return items


def _fetch_hn_stories(query: str) -> List[str]:
    """Fetches trending discussions from HackerNews Algolia API for the subject."""
    items: List[str] = []
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={requests.utils.quote(query)}&tags=story&hitsPerPage=6"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            for hit in resp.json().get("hits", []):
                title = hit.get("title", "")
                if title:
                    items.append(f"[Tech Discussion] {title}")
    except Exception:
        pass
    return items


def _fetch_devto_articles(tag: str) -> List[str]:
    """Fetches top developer tutorials and engineering posts from Dev.to API."""
    items: List[str] = []
    try:
        url = f"https://dev.to/api/articles?tag={tag}&top=7&per_page=6"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            for article in resp.json():
                title = article.get("title", "")
                desc = article.get("description", "")
                if title:
                    items.append(f"[Engineering Guide] {title}: {desc}")
    except Exception:
        pass
    return items


def fetch_raw_subject_news(subject_category: str) -> str:
    """Fetches live articles for a university subject concurrently in under 3 seconds."""
    subject_cfg = UNIVERSITY_SUBJECTS.get(subject_category, UNIVERSITY_SUBJECTS["AI & Machine Learning"])
    collected: List[str] = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(_fetch_hn_stories, subject_cfg["hn_query"]),
            executor.submit(_fetch_devto_articles, subject_cfg["devto_tag"]),
        ]
        if subject_cfg.get("use_hf"):
            futures.append(executor.submit(_fetch_hf_papers))

        for future in futures:
            collected.extend(future.result())

    if not collected:
        return "\n".join(
            [f"[Core Curriculum] {t.title} - {t.summary}" for t in subject_cfg["default_ranked"]]
        )

    return "\n".join(collected)


def discover_viral_topics(
    working_models: List[str],
    subject_category: str = "AI & Machine Learning",
    api_key: str = None,
) -> TrendingTopicsList:
    """Uses Gemini Flash-Lite (with thinking_budget=0) to curate the top 5 study topics."""
    active_key = api_key or os.getenv("GEMINI_API_KEY")
    client = get_genai_client(active_key)

    raw_news = fetch_raw_subject_news(subject_category)

    prompt = f"""
    You are an Academic & Tech Curriculum Strategist for University Students studying '{subject_category}'.
    Analyze the following live industry discussions, papers, and engineering articles:

    {raw_news}

    Select and synthesize the TOP 5 most valuable, exam-relevant, and career-boosting topics for university students to turn into visual study notes and share on LinkedIn/Facebook.
    Rank them from #1 (most impactful right now) to #5.
    Make the titles crystal clear, academic yet engaging, and educational. Do not use any emojis.
    """

    for model_name in working_models:
        try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TrendingTopicsList,
                        temperature=0.3,
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                    ),
                )
            except Exception:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TrendingTopicsList,
                        temperature=0.3,
                    ),
                )
            return TrendingTopicsList.model_validate_json(response.text)
        except Exception:
            continue

    return TrendingTopicsList(topics=get_default_ranked_topics(subject_category))
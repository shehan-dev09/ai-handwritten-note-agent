import io
import os
import zipfile
from dotenv import load_dotenv
from note_generator import (
    generate_5_page_study_guide,
    get_working_models,
    render_all_pages,
)
import streamlit as st
from trend_agent import discover_viral_topics

load_dotenv()

# =====================================================================
# AUTO-ENFORCE GREEN THEME IN .streamlit/config.toml
# =====================================================================
os.makedirs(".streamlit", exist_ok=True)
config_path = os.path.join(".streamlit", "config.toml")
expected_config = (
    '[theme]\n'
    'base = "dark"\n'
    'primaryColor = "#00FF88"\n'
    'backgroundColor = "#020504"\n'
    'secondaryBackgroundColor = "#07120D"\n'
    'textColor = "#ECFFF5"\n'
    'font = "sans serif"\n\n'
    '[server]\n'
    'headless = true\n'
)
if not os.path.exists(config_path) or open(config_path, "r", encoding="utf-8").read() != expected_config:
    with open(config_path, "w", encoding="utf-8") as cf:
        cf.write(expected_config)

# =====================================================================
# PAGE CONFIGURATION
# =====================================================================
st.set_page_config(
    page_title="Genesis Note Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================================================================
# TYPOGRAPHIC GLASSMORPHISM // GREEN x BLACK (ZERO RED BLEED + MOBILE)
# =====================================================================
STUDIO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

:root,
html,
body,
.stApp,
[data-testid="stAppViewContainer"] {
    --bg: #020504;
    --g: #00FF88;
    --g-soft: #2DFFA8;
    --lime: #B6FF3C;
    --text-hi: #ECFFF5;
    --text-mid: rgba(214, 255, 232, 0.70);
    --text-low: rgba(214, 255, 232, 0.42);
    --edge: rgba(0, 255, 136, 0.26);
    --glass: linear-gradient(155deg, rgba(10, 26, 18, 0.82) 0%, rgba(3, 9, 6, 0.90) 100%);
    --glass-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12),
                    0 20px 50px -20px rgba(0, 0, 0, 0.92),
                    0 0 36px -16px rgba(0, 255, 136, 0.25);
    --primary-color: #00FF88 !important;
    accent-color: #00FF88 !important;
}

/* ---------- Canvas Background & Subtle Grid ---------- */
.stApp {
    background:
        radial-gradient(ellipse 70% 45% at 15% -10%, rgba(0, 255, 136, 0.15), transparent 60%),
        radial-gradient(ellipse 55% 40% at 95% 20%, rgba(182, 255, 60, 0.07), transparent 60%),
        radial-gradient(ellipse 50% 40% at 50% 115%, rgba(0, 255, 136, 0.12), transparent 60%),
        var(--bg) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-hi) !important;
    overflow-x: hidden !important;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(0, 255, 136, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 136, 0.04) 1px, transparent 1px);
    background-size: 52px 52px;
    -webkit-mask-image: radial-gradient(ellipse 85% 70% at 50% 25%, #000 20%, transparent 75%);
            mask-image: radial-gradient(ellipse 85% 70% at 50% 25%, #000 20%, transparent 75%);
    z-index: 0;
}

/* Hide Native Streamlit Chrome */
#MainMenu,
footer,
header[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stToolbar"] {
    display: none !important;
}

/* ---------- Main Container Spacing ---------- */
.block-container {
    max-width: 1420px !important;
    padding: 1.15rem 1.75rem 2.5rem 1.75rem !important;
    margin: 0 auto !important;
    position: relative;
    z-index: 1;
}

/* ---------- Glass Studio Cards ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--glass) !important;
    -webkit-backdrop-filter: blur(20px) saturate(160%);
            backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid var(--edge) !important;
    border-radius: 18px !important;
    padding: 1.35rem 1.4rem !important;
    box-shadow: var(--glass-shadow) !important;
    box-sizing: border-box !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
    gap: 0.8rem !important;
}

/* Prevent nested containers from stacking borders or padding */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    border-radius: 0 !important;
    -webkit-backdrop-filter: none !important;
            backdrop-filter: none !important;
}

/* ---------- Top Navbar ---------- */
.studio-navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    padding: 0.75rem 1.15rem;
    background: var(--glass);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
            backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid var(--edge);
    border-radius: 13px;
    box-shadow: var(--glass-shadow);
    margin-bottom: 0.25rem;
}

.nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}

.brand-mark {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--g);
    box-shadow: 0 0 12px var(--g);
    flex-shrink: 0;
}

.brand-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 0.84rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-hi);
}

.brand-divider {
    color: rgba(255, 255, 255, 0.22);
}

.brand-sub {
    font-size: 0.78rem;
    color: var(--text-mid);
}

.nav-meta {
    display: flex;
    align-items: center;
    gap: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.05em;
    color: var(--text-mid);
}

.nav-meta .live {
    color: var(--g);
    text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    font-weight: 600;
}

/* ---------- Balanced Typographic Hero ---------- */
.hero {
    padding: 1.2rem 0.15rem 1.05rem 0.15rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 1rem;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: clamp(1.95rem, 4vw, 3.25rem);
    line-height: 0.98;
    letter-spacing: -0.04em;
    margin: 0.3rem 0 0 0;
    background: linear-gradient(180deg, #FFFFFF 15%, #B8FFD9 60%, #00FF88 120%);
    -webkit-background-clip: text;
            background-clip: text;
    color: transparent;
    filter: drop-shadow(0 0 22px rgba(0, 255, 136, 0.18));
}

.hero-title .outline {
    -webkit-text-fill-color: transparent;
    -webkit-text-stroke: 1.5px var(--g);
    filter: drop-shadow(0 0 16px rgba(0, 255, 136, 0.55));
}

.hero-sub {
    max-width: 440px;
    margin: 0;
    color: var(--text-mid);
    font-size: 0.86rem;
    line-height: 1.55;
}

/* ---------- Panel Headers & Section Labels ---------- */
.panel-header-group {
    margin-bottom: 0.25rem;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--g);
    text-shadow: 0 0 12px rgba(0, 255, 136, 0.45);
    display: block;
    margin-bottom: 0.22rem;
}

.panel-heading {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--text-hi);
    margin: 0;
    line-height: 1.25;
}

.workspace-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(1.2rem, 2.1vw, 1.6rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-hi);
    margin: 0;
    line-height: 1.2;
}

/* ---------- Widget Labels ---------- */
[data-testid="stWidgetLabel"] p,
label {
    color: var(--text-mid) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}

/* =====================================================================
   RADIO BUTTONS: 100% DIRECT BASEWEB OVERRIDE (NO .stRadio DEPENDENCY)
   ===================================================================== */
[data-testid="stRadio"] div[role="radiogroup"],
div[role="radiogroup"] {
    background: rgba(2, 10, 7, 0.65) !important;
    border: 1px solid rgba(0, 255, 136, 0.18) !important;
    border-radius: 12px !important;
    padding: 0.45rem !important;
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 0.45rem !important;
}

/* Individual Radio Option Pill */
label[data-baseweb="radio"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(0, 255, 136, 0.12) !important;
    border-radius: 9px !important;
    padding: 0.42rem 0.75rem !important;
    margin: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    flex: 1 1 auto !important;
}

label[data-baseweb="radio"]:hover {
    border-color: rgba(0, 255, 136, 0.4) !important;
    background: rgba(0, 255, 136, 0.06) !important;
}

/* Active/Selected Radio Pill */
label[data-baseweb="radio"]:has(input:checked),
label[data-baseweb="radio"]:has(input[aria-checked="true"]) {
    background: rgba(0, 255, 136, 0.12) !important;
    border-color: #00FF88 !important;
    box-shadow: 0 0 18px -6px rgba(0, 255, 136, 0.5) !important;
}

/* Unchecked Radio Circle (Outer) - Override all 4 BaseWeb longhand borders */
label[data-baseweb="radio"] > div:first-of-type {
    background-color: #03100A !important;
    background-image: none !important;
    border-width: 2px !important;
    border-style: solid !important;
    border-color: rgba(0, 255, 136, 0.55) !important;
    border-top-color: rgba(0, 255, 136, 0.55) !important;
    border-right-color: rgba(0, 255, 136, 0.55) !important;
    border-bottom-color: rgba(0, 255, 136, 0.55) !important;
    border-left-color: rgba(0, 255, 136, 0.55) !important;
    width: 16px !important;
    height: 16px !important;
    min-width: 16px !important;
    min-height: 16px !important;
    margin: 0 !important;
    box-shadow: none !important;
}

/* Unchecked Radio Inner Dot */
label[data-baseweb="radio"] > div:first-of-type > div {
    background-color: transparent !important;
    width: 6px !important;
    height: 6px !important;
}

/* Checked Radio Circle (Outer) -> Neon Green #00FF88 */
label[data-baseweb="radio"]:has(input:checked) > div:first-of-type,
label[data-baseweb="radio"]:has(input[aria-checked="true"]) > div:first-of-type {
    background-color: #00FF88 !important;
    border-color: #00FF88 !important;
    border-top-color: #00FF88 !important;
    border-right-color: #00FF88 !important;
    border-bottom-color: #00FF88 !important;
    border-left-color: #00FF88 !important;
    box-shadow: 0 0 10px rgba(0, 255, 136, 0.8) !important;
}

/* Checked Radio Inner Dot -> Obsidian #02120A */
label[data-baseweb="radio"]:has(input:checked) > div:first-of-type > div,
label[data-baseweb="radio"]:has(input[aria-checked="true"]) > div:first-of-type > div {
    background-color: #02120A !important;
    width: 6px !important;
    height: 6px !important;
}

/* Radio Option Text */
label[data-baseweb="radio"] p,
label[data-baseweb="radio"] span {
    color: var(--text-hi) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    margin: 0 !important;
}

label[data-baseweb="radio"]:has(input:checked) p,
label[data-baseweb="radio"]:has(input[aria-checked="true"]) p {
    color: #00FF88 !important;
    font-weight: 600 !important;
}

/* =====================================================================
   TEXT INPUTS & SELECTBOXES: DIRECT BASEWEB OVERRIDES
   ===================================================================== */
[data-testid="stTextInput"] [data-baseweb="input"],
[data-baseweb="input"] {
    background-color: rgba(2, 10, 7, 0.78) !important;
    border-width: 1px !important;
    border-style: solid !important;
    border-color: rgba(0, 255, 136, 0.24) !important;
    border-top-color: rgba(0, 255, 136, 0.24) !important;
    border-right-color: rgba(0, 255, 136, 0.24) !important;
    border-bottom-color: rgba(0, 255, 136, 0.24) !important;
    border-left-color: rgba(0, 255, 136, 0.24) !important;
    border-radius: 11px !important;
    box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.6) !important;
    padding: 0 !important;
    min-height: 42px !important;
}

[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-baseweb="input"]:focus-within {
    border-color: #00FF88 !important;
    border-top-color: #00FF88 !important;
    border-right-color: #00FF88 !important;
    border-bottom-color: #00FF88 !important;
    border-left-color: #00FF88 !important;
    box-shadow: 0 0 0 2px rgba(0, 255, 136, 0.18), 0 0 18px -4px rgba(0, 255, 136, 0.5) !important;
}

[data-baseweb="base-input"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

[data-baseweb="input"] input {
    background-color: transparent !important;
    border: none !important;
    color: var(--text-hi) !important;
    font-size: 0.86rem !important;
    padding: 0.55rem 0.85rem !important;
    caret-color: #00FF88 !important;
    outline: none !important;
}

[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-baseweb="select"] > div {
    background-color: rgba(2, 10, 7, 0.78) !important;
    border-width: 1px !important;
    border-style: solid !important;
    border-color: rgba(0, 255, 136, 0.24) !important;
    border-top-color: rgba(0, 255, 136, 0.24) !important;
    border-right-color: rgba(0, 255, 136, 0.24) !important;
    border-bottom-color: rgba(0, 255, 136, 0.24) !important;
    border-left-color: rgba(0, 255, 136, 0.24) !important;
    border-radius: 11px !important;
    color: var(--text-hi) !important;
    min-height: 42px !important;
    padding: 0.15rem 0.6rem !important;
    font-size: 0.86rem !important;
}

[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-baseweb="select"] > div:focus-within {
    border-color: #00FF88 !important;
    border-top-color: #00FF88 !important;
    border-right-color: #00FF88 !important;
    border-bottom-color: #00FF88 !important;
    border-left-color: #00FF88 !important;
    box-shadow: 0 0 0 2px rgba(0, 255, 136, 0.18) !important;
}

div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {
    background: #040D09 !important;
    border: 1px solid rgba(0, 255, 136, 0.3) !important;
    border-radius: 11px !important;
}

/* =====================================================================
   BUTTONS: SECONDARY & PRIMARY
   ===================================================================== */
[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button,
button[data-testid="stBaseButton-secondary"] {
    background: rgba(0, 255, 136, 0.06) !important;
    border: 1px solid rgba(0, 255, 136, 0.26) !important;
    border-radius: 11px !important;
    color: var(--text-hi) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.81rem !important;
    min-height: 41px !important;
    padding: 0.45rem 0.85rem !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stButton"] > button p,
[data-testid="stDownloadButton"] > button p {
    color: var(--text-hi) !important;
    font-weight: 500 !important;
    font-size: 0.81rem !important;
    margin: 0 !important;
    white-space: nowrap !important;
}

[data-testid="stButton"] > button:hover,
[data-testid="stButton"] > button:focus,
[data-testid="stButton"] > button:focus-visible,
[data-testid="stButton"] > button:active,
[data-testid="stDownloadButton"] > button:hover,
[data-testid="stDownloadButton"] > button:focus,
[data-testid="stDownloadButton"] > button:focus-visible,
[data-testid="stDownloadButton"] > button:active {
    border-color: #00FF88 !important;
    background: rgba(0, 255, 136, 0.14) !important;
    color: var(--text-hi) !important;
    box-shadow: 0 0 22px -6px rgba(0, 255, 136, 0.65) !important;
    outline: none !important;
}

/* Primary Buttons */
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stDownloadButton"] > button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #00FF88 0%, #B6FF3C 130%) !important;
    color: #02120A !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    min-height: 44px !important;
    box-shadow: 0 0 28px -5px rgba(0, 255, 136, 0.65),
                inset 0 1px 0 rgba(255, 255, 255, 0.55) !important;
}

[data-testid="stButton"] > button[kind="primary"] p,
[data-testid="stButton"] > button[kind="primary"] span,
[data-testid="stDownloadButton"] > button[kind="primary"] p,
[data-testid="stDownloadButton"] > button[kind="primary"] span,
button[data-testid="stBaseButton-primary"] p,
button[data-testid="stBaseButton-primary"] span {
    color: #02120A !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
}

[data-testid="stButton"] > button[kind="primary"]:hover,
[data-testid="stButton"] > button[kind="primary"]:focus,
[data-testid="stButton"] > button[kind="primary"]:active,
[data-testid="stDownloadButton"] > button[kind="primary"]:hover,
[data-testid="stDownloadButton"] > button[kind="primary"]:focus,
[data-testid="stDownloadButton"] > button[kind="primary"]:active {
    background: linear-gradient(135deg, #4AFFA8 0%, #C5FF5E 130%) !important;
    color: #02120A !important;
    border-color: #FFFFFF !important;
    box-shadow: 0 0 40px -3px rgba(0, 255, 136, 0.9) !important;
    outline: none !important;
}

/* =====================================================================
   TABS: DIRECT BASEWEB OVERRIDES (ZERO RED HIGHLIGHT BAR)
   ===================================================================== */
[data-baseweb="tab-list"] {
    gap: 6px !important;
    border-bottom: 1px solid rgba(0, 255, 136, 0.16) !important;
    padding-bottom: 8px !important;
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
    scrollbar-width: none !important;
}

[data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none !important;
}

button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.79rem !important;
    font-weight: 500 !important;
    color: var(--text-mid) !important;
    padding: 0.45rem 0.9rem !important;
    border-radius: 9px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    height: auto !important;
    white-space: nowrap !important;
    margin: 0 !important;
}

button[data-baseweb="tab"]:hover,
button[data-baseweb="tab"]:focus {
    color: var(--text-hi) !important;
    background: rgba(0, 255, 136, 0.06) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #00FF88 !important;
    background: rgba(0, 255, 136, 0.12) !important;
    border: 1px solid rgba(0, 255, 136, 0.38) !important;
    box-shadow: 0 0 18px -6px rgba(0, 255, 136, 0.5) !important;
}

button[data-baseweb="tab"][aria-selected="true"] p {
    color: #00FF88 !important;
    font-weight: 600 !important;
}

[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] {
    display: none !important;
    background-color: transparent !important;
}

[data-baseweb="tab-panel"] {
    padding-top: 0.85rem !important;
}

/* ---------- Carousel Slide Previews & Code Block ---------- */
[data-testid="stImage"] img {
    border-radius: 10px !important;
    border: 1px solid rgba(0, 255, 136, 0.25) !important;
    box-shadow: 0 10px 26px -10px rgba(0, 0, 0, 0.8), 0 0 22px -10px rgba(0, 255, 136, 0.45);
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

[data-testid="stImage"] img:hover {
    border-color: #00FF88 !important;
    box-shadow: 0 14px 32px -8px rgba(0, 0, 0, 0.9), 0 0 32px -6px rgba(0, 255, 136, 0.75);
    transform: translateY(-2px);
}

[data-testid="stCode"],
[data-testid="stCodeBlock"],
pre {
    background: rgba(2, 10, 7, 0.78) !important;
    border: 1px solid rgba(0, 255, 136, 0.22) !important;
    border-radius: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
}

hr {
    border-color: rgba(0, 255, 136, 0.14) !important;
    margin: 0.6rem 0 !important;
}

[data-testid="stAlert"] {
    background: rgba(2, 14, 9, 0.82) !important;
    border: 1px solid rgba(0, 255, 136, 0.28) !important;
    border-radius: 11px !important;
    color: var(--text-hi) !important;
}

/* ---------- Mobile & Tablet Responsive Breakpoints ---------- */
@media (max-width: 1024px) {
    .block-container {
        padding: 0.9rem 1.1rem 2rem 1.1rem !important;
    }
    .hero {
        padding: 1rem 0.1rem 0.85rem 0.1rem;
    }
    .hero-title {
        font-size: clamp(1.85rem, 5vw, 2.6rem);
    }
}

@media (max-width: 768px) {
    .block-container {
        padding: 0.65rem 0.75rem 1.75rem 0.75rem !important;
    }
    .studio-navbar {
        padding: 0.65rem 0.85rem;
        border-radius: 11px;
    }
    .brand-divider,
    .brand-sub {
        display: none !important;
    }
    .nav-meta {
        font-size: 0.62rem;
        gap: 10px;
    }
    .hero {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.55rem;
        padding: 0.85rem 0.05rem 0.75rem 0.05rem;
    }
    .hero-title {
        font-size: 1.85rem;
        line-height: 1.02;
    }
    .hero-sub {
        font-size: 0.82rem;
        max-width: 100%;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 1.05rem 1rem !important;
        border-radius: 14px !important;
    }
    .panel-heading {
        font-size: 1.15rem;
    }
    .workspace-title {
        font-size: 1.2rem;
        margin-bottom: 0.35rem;
    }
    div[role="radiogroup"] {
        flex-direction: column !important;
        align-items: stretch !important;
    }
    label[data-baseweb="radio"] {
        width: 100% !important;
    }
}
</style>
"""

st.markdown(STUDIO_CSS, unsafe_allow_html=True)


# =====================================================================
# HELPER: AUTO-LOAD EXISTING OUTPUT ON STARTUP SO CANVAS IS NEVER EMPTY
# =====================================================================
def load_existing_output():
    """Finds the most recent generated 5-page note set in output/ to populate the workspace immediately."""
    if not os.path.exists("output"):
        return None, [], ""

    subfolders = [
        os.path.join("output", d)
        for d in os.listdir("output")
        if os.path.isdir(os.path.join("output", d))
    ]
    candidates = sorted(subfolders, key=os.path.getmtime, reverse=True) + ["output"]

    for folder in candidates:
        pages = [os.path.join(folder, f"note_page_{i}.png") for i in range(1, 6)]
        if all(os.path.exists(p) for p in pages):
            caption_path = os.path.join(folder, "caption.txt")
            caption_text = ""
            if os.path.exists(caption_path):
                with open(caption_path, "r", encoding="utf-8") as f:
                    caption_text = f.read()
            topic_label = (
                os.path.basename(folder).replace("_", " ")
                if folder != "output"
                else "Retrieval-Augmented Generation (RAG)"
            )
            return topic_label, pages, caption_text

    return None, [], ""


if "viral_topics" not in st.session_state:
    st.session_state.viral_topics = []

if "active_topic" not in st.session_state:
    loaded_topic, loaded_imgs, loaded_cap = load_existing_output()
    st.session_state.active_topic = loaded_topic
    st.session_state.image_paths = loaded_imgs
    st.session_state.social_caption = loaded_cap

# Resolve API Key
default_api_key = os.getenv("GEMINI_API_KEY", "")
if not default_api_key:
    try:
        default_api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        default_api_key = ""


# =====================================================================
# TOP GLASS NAVBAR + RESPONSIVE TYPOGRAPHIC HERO
# =====================================================================
st.markdown(
    """
    <div class="studio-navbar">
        <div class="nav-brand">
            <div class="brand-mark"></div>
            <span class="brand-title">Genesis Note Studio</span>
            <span class="brand-divider">/</span>
            <span class="brand-sub">Autonomous AI/ML Sketchnote &amp; Copy Engine</span>
        </div>
        <div class="nav-meta">
            <span class="live">&#9679; GEMINI 3.x PIPELINE READY</span>
            <span>1000x1250PX CAROUSEL</span>
        </div>
    </div>
    <div class="hero">
        <div>
            <span class="section-label">Typographic Glass // Green x Black Edition</span>
            <div class="hero-title">Turn any concept into a <span class="outline">carousel.</span></div>
        </div>
        <p class="hero-sub">Pick an AI/ML topic, select your language mode, and synthesize five export-ready handwritten study slides with social copy.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2-PANE STUDIO WORKSPACE LAYOUT (LEFT: CONTROLS | RIGHT: CANVAS)
# =====================================================================
left_pane, right_pane = st.columns([1.05, 2.25], gap="medium")

with left_pane:
    with st.container(border=True):
        st.markdown(
            """
            <div class="panel-header-group">
                <span class="section-label">01 // TOPIC DISCOVERY</span>
                <div class="panel-heading">Content Configuration</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        source_mode = st.radio(
            "Topic Input Method",
            options=["Manual Topic Entry", "Live Trend Scanner (HF / HN)"],
            horizontal=True,
        )

        if source_mode == "Live Trend Scanner (HF / HN)":
            if st.button("Scan Live AI/ML Trends", use_container_width=True):
                if not default_api_key:
                    st.error("API Key required.")
                else:
                    with st.spinner("Querying HuggingFace & HackerNews..."):
                        models = get_working_models(default_api_key)
                        st.session_state.viral_topics = discover_viral_topics(models)

            if st.session_state.viral_topics:
                topic_list = [t.topic_title for t in st.session_state.viral_topics]
                final_topic = st.selectbox(
                    "Select Discovered Viral Topic", options=topic_list
                )
            else:
                final_topic = st.text_input(
                    "Target Topic (Click Scan above to populate list)",
                    value="What is RAG (Retrieval-Augmented Generation) in AI?",
                )
        else:
            final_topic = st.text_input(
                "Target AI/ML Concept",
                value="What is RAG (Retrieval-Augmented Generation) in AI?",
            )

        st.markdown("<hr/>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="panel-header-group">
                <span class="section-label">02 // RENDERING PARAMETERS</span>
                <div class="panel-heading">Output &amp; Language</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        lang_choice = st.radio(
            "Language Mode",
            options=["Sinhala + English Technical Terms", "English Only (Global)"],
            index=0,
        )
        selected_language = "Sinhala_Mix" if "Sinhala" in lang_choice else "English"

        author_handle = st.text_input("Author Signature Handle", value="@YourName")

        if not default_api_key:
            api_key_input = st.text_input("Gemini API Key", type="password")
        else:
            api_key_input = default_api_key

        generate_btn = st.button(
            "Generate 5-Page Study Carousel",
            type="primary",
            use_container_width=True,
        )

        if generate_btn:
            if not api_key_input:
                st.error("Missing GEMINI_API_KEY.")
            elif not final_topic.strip():
                st.warning("Please specify a topic.")
            else:
                os.environ["GEMINI_API_KEY"] = api_key_input
                safe_folder = "".join(
                    c if c.isalnum() else "_" for c in final_topic
                )[:35].strip("_")
                out_dir = os.path.join("output", safe_folder)

                with st.spinner(
                    "Synthesizing 5-page curriculum & rendering SVG sketchnotes..."
                ):
                    guide = generate_5_page_study_guide(
                        topic=final_topic,
                        language=selected_language,
                        api_key=api_key_input,
                    )
                    img_paths = render_all_pages(
                        guide=guide, author=author_handle, output_dir=out_dir
                    )
                    caption_file = os.path.join(out_dir, "caption.txt")
                    with open(caption_file, "w", encoding="utf-8") as f:
                        f.write(guide.social_caption)

                    st.session_state.active_topic = guide.topic_name
                    st.session_state.image_paths = img_paths
                    st.session_state.social_caption = guide.social_caption
                    st.rerun()

# =====================================================================
# RIGHT PANE: LIVE CANVAS & EXPORT WORKSPACE
# =====================================================================
with right_pane:
    with st.container(border=True):
        if st.session_state.image_paths:
            img_paths = st.session_state.image_paths
            caption_text = st.session_state.social_caption
            topic_title = st.session_state.active_topic

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in img_paths:
                    if os.path.exists(p):
                        zf.write(p, arcname=os.path.basename(p))
                if caption_text:
                    zf.writestr("caption.txt", caption_text)
            zip_buffer.seek(0)

            top_l, top_r = st.columns([2.1, 1.0], vertical_alignment="center")
            with top_l:
                st.markdown(
                    f"""
                    <div class="panel-header-group" style="margin-bottom:0;">
                        <span class="section-label">WORKSPACE OUTPUT // 5-SLIDE CAROUSEL</span>
                        <div class="workspace-title">{topic_title}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with top_r:
                st.download_button(
                    label="Download Bundle (.ZIP)",
                    data=zip_buffer,
                    file_name="handwritten_carousel_bundle.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                )

            tab_grid, tab_inspect, tab_copy = st.tabs(
                ["5-Slide Carousel Grid", "High-Res Slide Inspector", "Social Post Copy"]
            )

            with tab_grid:
                cols = st.columns(5, gap="small")
                for idx, img_path in enumerate(img_paths):
                    with cols[idx]:
                        if os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                            with open(img_path, "rb") as img_file:
                                st.download_button(
                                    label=f"Slide 0{idx+1}",
                                    data=img_file,
                                    file_name=f"note_page_{idx+1}.png",
                                    mime="image/png",
                                    key=f"dl_slide_{idx+1}",
                                    use_container_width=True,
                                )

            with tab_inspect:
                slide_num = st.radio(
                    "Select Slide to Inspect",
                    options=[1, 2, 3, 4, 5],
                    format_func=lambda x: f"Page 0{x}",
                    horizontal=True,
                )
                selected_img = img_paths[slide_num - 1]
                if os.path.exists(selected_img):
                    _, center_col, _ = st.columns([0.35, 2.3, 0.35])
                    with center_col:
                        st.image(selected_img, use_container_width=True)

            with tab_copy:
                st.markdown(
                    '<span class="section-label">LINKEDIN &amp; FACEBOOK CAPTION (CLICK TOP-RIGHT ICON TO COPY)</span>',
                    unsafe_allow_html=True,
                )
                st.code(caption_text, language="markdown")

        else:
            st.markdown(
                """
                <div style="padding: 4.5rem 1.5rem; text-align: center;">
                    <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:3.2rem;letter-spacing:-0.04em;line-height:1;
                                color:transparent;-webkit-text-stroke:1.5px rgba(0,255,136,0.55);filter:drop-shadow(0 0 18px rgba(0,255,136,.35));margin-bottom:1rem;">
                        00 / 05
                    </div>
                    <div class="section-label" style="margin-bottom:0.5rem;">NO ACTIVE CAROUSEL IN WORKSPACE</div>
                    <div style="font-size: 0.9rem; color: rgba(214,255,232,0.65); max-width: 420px; margin: 0 auto;">
                        Configure a topic on the left panel and click <b style="color:#00FF88;">Generate 5-Page Study Carousel</b> to render slides.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
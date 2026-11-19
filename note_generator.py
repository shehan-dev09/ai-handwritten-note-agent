import json
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from html2image import Html2Image

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please check your .env file.")

client = genai.Client(api_key=API_KEY)


def get_working_models() -> list:
    """Fetches only active 3.x text models and filters out deprecated 2.x/image/audio models."""
    excluded_keywords = [
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
    ]
    try:
        all_models = []
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if (
                "generateContent" in m.supported_actions
                and "gemini" in name.lower()
            ):
                if not any(bad_word in name.lower() for bad_word in excluded_keywords):
                    all_models.append(name)

        # Prioritize lite and flash models for speed and higher availability
        all_models.sort(
            key=lambda x: (
                0 if "lite" in x else (1 if "flash" in x else 2)
            )
        )
        return all_models if all_models else ["gemini-3.8-flash"]
    except Exception:
        return [
            "gemini-3.8-flash-lite",
            "gemini-3.8-flash",
            "gemini-3.8-pro",
        ]


def generate_study_material(topic: str, language: str = "Sinhala_Mix") -> dict:
    """Generates educational note content with smart model switching."""
    lang_instruction = (
        "Explain in simple conversational Sinhala (using Sinhala Unicode script), but KEEP all technical AI/ML terms in English."
        if language == "Sinhala_Mix"
        else "Write completely in simple, easy-to-understand English."
    )

    prompt = f"""
    You are an expert AI/ML educator and viral LinkedIn/Facebook content creator.
    Topic: {topic}
    Language Instruction: {lang_instruction}

    Create content for a viral handwritten-style study note and a social media post.
    Return the output STRICTLY as a JSON object with the following keys:

    1. "title": A short, catchy title for the top of the note (max 6 words).
    2. "note_html": The body of the note formatted in simple HTML. 
       - Must be 100% technically accurate and easy for a beginner to understand.
       - Use <h3> for subheadings.
       - Use <ul> and <li> for bullet points (keep points short and clear, max 4-5 points).
       - Wrap important keywords in <mark> tags (this will act as a yellow highlighter).
       - Wrap key takeaways or practical examples in <div class="box"> tags.
       - DO NOT include <html> or <body> tags, just the inner HTML elements.
    3. "caption": A viral Facebook/LinkedIn caption written as if a human AI enthusiast wrote it.
       - Start with a strong, curiosity-inducing HOOK in the first 2 lines.
       - Maintain a friendly, personal, and authentic tone.
       - Add a brief summary and end with an engaging question to drive comments.
       - Include 5 relevant hashtags at the end.
    """

    models_to_try = get_working_models()
    print(f"[INFO] Active 3.x models detected: {models_to_try}")

    for model_name in models_to_try:
        for attempt in range(1, 3):  # Try 2 times per model before switching
            try:
                print(
                    f"[INFO] Generating content using '{model_name}' (Attempt {attempt}/2)..."
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                    ),
                )
                return json.loads(response.text)

            except APIError as e:
                if e.code == 503:
                    print(
                        f"[WARNING] '{model_name}' server is busy (503). Waiting 3s..."
                    )
                    time.sleep(3)
                elif e.code in [400, 404, 429]:
                    print(
                        f"[WARNING] '{model_name}' unavailable (Code {e.code}). Switching to next model..."
                    )
                    break  # Immediately switch to the next model
                else:
                    raise e

    raise RuntimeError(
        "All Gemini models are currently busy. Please try again shortly."
    )


def render_handwritten_note(
    title: str,
    note_html: str,
    author: str = "@YourName",
    output_filename: str = "handwritten_note.png",
):
    """Renders the HTML content into a realistic handwritten note image."""
    print("[INFO] Rendering handwritten note image...")

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Kalam:wght@400;700&family=Noto+Sans+Sinhala:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 40px;
            background-color: #e0e0e0;
            display: flex;
            justify-content: center;
        }}
        .paper {{
            width: 800px;
            min-height: 950px;
            background-color: #fffef7;
            background-image: repeating-linear-gradient(transparent, transparent 38px, #94c2f7 38px, #94c2f7 40px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            padding: 40px 50px 50px 90px;
            position: relative;
            box-sizing: border-box;
            font-family: 'Kalam', 'Noto Sans Sinhala', sans-serif;
            color: #0d1b52;
            font-size: 21px;
            line-height: 40px;
        }}
        .paper::before {{
            content: '';
            position: absolute;
            top: 0; bottom: 0; left: 70px;
            width: 3px;
            background-color: #ff9999;
        }}
        h1 {{
            font-family: 'Caveat', 'Noto Sans Sinhala', cursive;
            color: #b71c1c;
            font-size: 40px;
            margin-top: 0;
            margin-bottom: 20px;
            line-height: 40px;
            text-decoration: underline;
        }}
        h3 {{
            color: #b71c1c;
            margin-top: 20px;
            margin-bottom: 0px;
            font-size: 25px;
        }}
        ul {{
            margin-top: 0;
            padding-left: 25px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        mark {{
            background-color: #ffeb3b;
            padding: 2px 8px;
            border-radius: 5px;
            color: #000;
            font-weight: bold;
        }}
        .box {{
            border: 2px dashed #2e7d32;
            background-color: rgba(232, 245, 233, 0.6);
            padding: 15px;
            margin-top: 20px;
            border-radius: 10px;
            color: #1b5e20;
        }}
        .footer {{
            position: absolute;
            bottom: 15px;
            right: 30px;
            font-family: 'Caveat', cursive;
            font-size: 24px;
            color: #777;
        }}
    </style>
    </head>
    <body>
        <div class="paper">
            <h1>{title}</h1>
            {note_html}
            <div class="footer">Notes by {author} 📌</div>
        </div>
    </body>
    </html>
    """

    hti = Html2Image(size=(900, 1100))
    hti.screenshot(html_str=html_template, save_as=output_filename)
    print(f"[SUCCESS] Note image saved as '{output_filename}'")


def main():
    TOPIC = "What is RAG (Retrieval-Augmented Generation) in AI?"
    LANGUAGE = "Sinhala_Mix"
    AUTHOR_NAME = "@YourName"

    try:
        content = generate_study_material(topic=TOPIC, language=LANGUAGE)

        render_handwritten_note(
            title=content["title"],
            note_html=content["note_html"],
            author=AUTHOR_NAME,
            output_filename="handwritten_note.png",
        )

        caption_file = "caption.txt"
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(content["caption"])
        print(f"[SUCCESS] Social media caption saved as '{caption_file}'")

        print("\n--- GENERATED CAPTION PREVIEW ---")
        print(content["caption"])

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()
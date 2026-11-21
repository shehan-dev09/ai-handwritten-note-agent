import os
from note_generator import (
    generate_5_page_study_guide,
    get_working_models,
    render_all_pages,
)
from trend_agent import discover_viral_topics


def run_agent_pipeline():
    print("=" * 65)
    print("AI/ML HANDWRITTEN STUDY NOTE AGENT (MULTI-AGENT SYSTEM)")
    print("=" * 65)

    author_handle = (
        input("\nEnter your author name/handle (default: @YourName): ")
        .strip()
        or "Shehan Nadeesha"
    )

    print("\nSelect Note Language Mode:")
    print("  [1] Sinhala + English Technical Terms (Recommended for SL)")
    print("  [2] 100% English (Global Audience)")
    lang_choice = input("👉 Choose (1 or 2, default 1): ").strip()
    language = "English" if lang_choice == "2" else "Sinhala_Mix"

    print("\nSelect Topic Mode:")
    print("  [1] Auto-Discover Today's Viral AI/ML Topics (Trend Agent)")
    print("  [2] Enter My Own Custom AI/ML Topic")
    mode_choice = input("Choose (1 or 2, default 1): ").strip()

    if mode_choice == "2":
        selected_topic = input("\n Enter your AI/ML Topic: ").strip()
        if not selected_topic:
            selected_topic = (
                "What is RAG (Retrieval-Augmented Generation) in AI?"
            )
    else:
        models = get_working_models()
        viral_topics = discover_viral_topics(models)

        print("\n TOP 5 VIRAL AI/ML TOPICS TODAY:")
        print("-" * 65)
        for idx, item in enumerate(viral_topics, start=1):
            print(f"  [{idx}] {item.topic_title}")
            print(f"      └─ Why: {item.why_viral}")
        print("-" * 65)

        topic_idx = input("\n Pick a topic number (1-5, default 1): ").strip()
        try:
            choice_num = int(topic_idx)
            selected_topic = viral_topics[choice_num - 1].topic_title
        except Exception:
            selected_topic = viral_topics[0].topic_title

    print(
        f"\n Selected Topic: '{selected_topic}' | Language: '{language}'"
    )
    print("-" * 65)

    # Create safe subfolder inside output/ for this topic
    safe_folder_name = "".join(
        c if c.isalnum() else "_" for c in selected_topic
    )[:35].strip("_")
    output_dir = os.path.join("output", safe_folder_name)

    # Step 1: Generate 5-Page Study Guide + Caption
    study_guide = generate_5_page_study_guide(
        topic=selected_topic, language=language
    )

    # Step 2: Render all 5 pages
    render_all_pages(
        guide=study_guide, author=author_handle, output_dir=output_dir
    )

    # Step 3: Save Caption
    caption_path = os.path.join(output_dir, "caption.txt")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(study_guide.social_caption)

    print("\n" + "=" * 65)
    print(f" ALL DONE! Your 5-Page Note Series & Caption are saved in:")
    print(f" Folder: {output_dir}/")
    print("=" * 65)
    print("\n GENERATED SOCIAL MEDIA CAPTION:\n")
    print(study_guide.social_caption)
    print("\n" + "=" * 65)


if __name__ == "__main__":
    run_agent_pipeline()
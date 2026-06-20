"""
Facebook Reels Automation - Bilingual English/Japanese Content Generator
IMPROVED VERSION: Better backgrounds, English categories, no repeats, Velocity Japanese branding
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file. "
        "For GitHub Actions: Add AI_MODEL to repository secrets."
    )

if not POLLINATIONS_API_KEY:
    print("[warn] POLLINATIONS_API_KEY not set! AI generation will fail, using fallback phrases.")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (9:16 vertical)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# English category names (for American/European learners)
# Essential Japanese learning categories + Motivational categories
CATEGORIES_ENGLISH = [
    # Essential Japanese Learning (Priority)
    "Greetings", "Basic Phrases", "Common Expressions", "Travel Japanese", "Restaurant Japanese",
    "Shopping Japanese", "Emergency Japanese", "Family Terms", "Numbers Japanese", "Time Japanese",
    "Weather Japanese", "Direction Japanese", "Colors Japanese", "Body Japanese", "Feelings Japanese",
    # Motivational Categories
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
    # Extended Practical Categories
    "Work Japanese", "Hobbies Japanese", "Daily Routine", "Health Japanese", "Nature Japanese",
]

# Japanese translations for display
CATEGORIES_JAPANESE = {
    # Essential Japanese Learning (Priority)
    "Greetings": "挨拶",
    "Basic Phrases": "基本フレーズ",
    "Common Expressions": "一般的な表現",
    "Travel Japanese": "旅行日本語",
    "Restaurant Japanese": "レストラン日本語",
    "Shopping Japanese": "ショッピング日本語",
    "Emergency Japanese": "緊急日本語",
    "Family Terms": "家族用語",
    "Numbers Japanese": "数字日本語",
    "Time Japanese": "時間日本語",
    "Weather Japanese": "天気の日本語",
    "Direction Japanese": "方向の日本語",
    "Colors Japanese": "色の日本語",
    "Body Japanese": "体の日本語",
    "Feelings Japanese": "感情の日本語",
    # Motivational Categories
    "Motivation": "モチベーション",
    "Love": "愛",
    "Success": "成功",
    "Wisdom": "知恵",
    "Happiness": "幸せ",
    "Self Improvement": "自己啓発",
    "Gratitude": "感謝",
    "Friendship": "友情",
    "Hope": "希望",
    "Creativity": "創造性",
    "Inner Peace": "内なる平和",
    "Confidence": "自信",
    "Perseverance": "忍耐",
    "Inspiration": "インスピレーション",
    "Positive Life": "ポジティブな人生",
    "Courage": "勇気",
    "Kindness": "優しさ",
    "Patience": "我慢",
    "Forgiveness": "許し",
    "Strength": "力",
    "Joy": "喜び",
    "Balance": "バランス",
    "Growth": "成長",
    "Purpose": "目的",
    "Mindfulness": "マインドフルネス",
    # Extended Practical Categories
    "Work Japanese": "仕事の日本語",
    "Hobbies Japanese": "趣味の日本語",
    "Daily Routine": "日常の習慣",
    "Health Japanese": "健康の日本語",
    "Nature Japanese": "自然の日本語",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
JAPANESE_VOICE = "ja-JP-NanamiNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Recent categories file (for rotation - prevents category repeats)
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"
MAX_RECENT_CATEGORIES = 15  # Track last 15 categories to avoid repeats


# ============== PHRASE HISTORY MANAGEMENT (Prevent Repeats) ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "japanese": phrase["japanese"],
            "romaji": phrase.get("romaji", ""),
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CATEGORY ROTATION MANAGEMENT (Prevent Repeats) ==============

def load_recent_categories():
    """Load recently used categories"""
    if RECENT_CATEGORIES_FILE.exists():
        with open(RECENT_CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"recent_categories": [], "last_updated": None}


def save_recent_categories(data):
    """Save recent categories"""
    data["last_updated"] = datetime.now().isoformat()
    with open(RECENT_CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_available_category():
    """Get a category that hasn't been used recently - ensures rotation across ALL 35 categories"""
    recent_data = load_recent_categories()
    recent = recent_data.get("recent_categories", [])

    # Get all categories that are NOT in recent list
    available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent]

    # If all categories have been used recently, clear the oldest ones
    if not available:
        # Keep only the most recent 5, clear the rest
        recent_data["recent_categories"] = recent[-5:]
        save_recent_categories(recent_data)
        available = [cat for cat in CATEGORIES_ENGLISH if cat not in recent_data["recent_categories"]]
        print(f"[rotation] All categories used recently - cleared old ones, {len(available)} available")

    # Random selection from available (non-recent) categories
    selected = random.choice(available)

    # Add to recent list
    recent.append(selected)

    # Keep only the last MAX_RECENT_CATEGORIES
    if len(recent) > MAX_RECENT_CATEGORIES:
        recent = recent[-MAX_RECENT_CATEGORIES:]

    recent_data["recent_categories"] = recent
    save_recent_categories(recent_data)

    print(f"[rotation] Selected '{selected}' ({len(available)} available, {len(recent)} in recent history)")
    return selected


# ============== CONTENT GENERATION ==============

def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    """Generate unique bilingual phrases with natural pauses, ensuring no repeats"""

    category_japanese = CATEGORIES_JAPANESE[category_english]

    # Try AI first
    AI_MODELS_FALLBACK = [AI_MODEL, "openai", "mistral", "llama"]
    max_attempts = 3
    for attempt in range(max_attempts):
        for model_idx, model in enumerate(AI_MODELS_FALLBACK):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }

                prompt = f"""Create {num_phrases * 2} unique {category_english} phrases for English speakers learning Japanese.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Japanese text should be CLEAN - use standard Japanese (mix of Kanji, Hiragana, Katakana as appropriate)
7. Do NOT include multiple versions or slashes - just ONE clean Japanese translation

For each phrase:
1. English phrase (with commas for natural pauses)
2. Japanese translation (natural Japanese with appropriate Kanji/Hiragana/Katakana)
3. Romaji pronunciation guide (Hepburn Romanization, e.g., "konnichiwa")

Return as JSON array:
[{{"english": "...", "japanese": "...", "romaji": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.
IMPORTANT: Japanese text must be clean - no slashes, no multiple versions."""

                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a Japanese teacher. Create short, natural phrases with pauses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.9
                }

                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code != 200:
                    print(f"[content] Attempt {attempt + 1}, model '{model}' returned {response.status_code}: {response.text[:200]}")
                    continue

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                # Extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)

                # Filter out already-used phrases and ensure proper length
                unique_phrases = []
                for phrase in phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                    if len(unique_phrases) >= num_phrases:
                        break

                if len(unique_phrases) >= num_phrases:
                    add_phrases_to_history(unique_phrases[:num_phrases], category_english)
                    print(f"[content] Generated {len(unique_phrases[:num_phrases])} phrases via {model}")
                    return unique_phrases[:num_phrases]

            except Exception as e:
                print(f"[content] Attempt {attempt + 1}, model '{model}' failed: {e}")

    # Fallback to fresh phrases
    print("[content] All AI attempts exhausted. Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones, mixing from related categories if depleted"""
    from fallback_phrases import FALLBACK_PHRASES, RELATED_CATEGORIES

    fallbacks = FALLBACK_PHRASES.get(category, FALLBACK_PHRASES["Motivation"])
    fresh_phrases = [p for p in fallbacks if not is_phrase_used(p["english"])]

    if len(fresh_phrases) >= num_phrases:
        return fresh_phrases[:num_phrases]

    related = RELATED_CATEGORIES.get(category, [])
    for rel_cat in related:
        rel_phrases = FALLBACK_PHRASES.get(rel_cat, [])
        for p in rel_phrases:
            if len(fresh_phrases) >= num_phrases:
                break
            if not is_phrase_used(p["english"]):
                fresh_phrases.append(p)
        if len(fresh_phrases) >= num_phrases:
            break

    if len(fresh_phrases) >= num_phrases:
        return fresh_phrases[:num_phrases]

    all_available = []
    for cat_list in FALLBACK_PHRASES.values():
        for p in cat_list:
            if not is_phrase_used(p["english"]):
                all_available.append(p)
            if len(all_available) >= num_phrases:
                break
        if len(all_available) >= num_phrases:
            break

    if len(all_available) >= num_phrases:
        result = all_available[:num_phrases]
        add_phrases_to_history(result, category)
        return result

    result = fallbacks[:num_phrases]
    print(f"[content] WARNING: All phrases used, reusing {len(result)} fallback phrases")
    return result


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    """Generate audio using Edge TTS"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        japanese_file = output_dir / f"japanese_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        print(f"\n  Phrase {i+1}:")
        print(f"    EN: {phrase['english']}")
        print(f"    JP: {phrase['japanese']}")

        # Generate English audio
        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if en_success:
            print(f"    ✓ English: {english_file.name}")
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Japanese audio
        jp_success = asyncio.run(generate_single_audio(phrase["japanese"], JAPANESE_VOICE, str(japanese_file)))
        if jp_success:
            print(f"    ✓ Japanese: {japanese_file.name}")
        else:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(japanese_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        jp_duration = get_audio_duration(str(japanese_file))

        # Add pause between English and Japanese
        pause_between = 0.5
        total_duration = en_duration + pause_between + jp_duration

        print(f"    ⏱️  Total: {total_duration:.2f}s (EN: {en_duration:.2f}s + pause: {pause_between}s + JP: {jp_duration:.2f}s)")

        # Combine audio files
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(japanese_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{japanese_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))
        print(f"    ✓ Combined verified: {actual_duration:.2f}s")

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "japanese": str(japanese_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "jp_duration": jp_duration
        })

    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMAGE GENERATION ==============

def create_impressive_background(category_english: str):
    """Create stunning gradient background with geometric patterns and glow"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    # HIGH CONTRAST gradients for ALL 35 categories (very different colors like Motivation)
    category_colors = {
        "Motivation": [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)],  # Purple → Dark Purple → Pink → Light Purple
        "Love": [(255, 0, 100), (139, 0, 0), (255, 105, 180), (255, 192, 203)],  # Red → Dark Red → Hot Pink → Pink
        "Success": [(255, 215, 0), (0, 100, 0), (255, 140, 0), (34, 139, 34)],  # Gold → Dark Green → Orange → Forest Green
        "Wisdom": [(0, 0, 139), (255, 215, 0), (70, 130, 180), (255, 255, 0)],  # Dark Blue → Gold → Steel Blue → Yellow
        "Happiness": [(255, 255, 0), (255, 0, 255), (255, 165, 0), (147, 112, 219)],  # Yellow → Magenta → Orange → Purple
        "Self Improvement": [(0, 128, 0), (255, 215, 0), (0, 255, 0), (255, 140, 0)],  # Green → Gold → Lime → Orange
        "Gratitude": [(255, 127, 80), (75, 0, 130), (255, 160, 122), (138, 43, 226)],  # Coral → Dark Purple → Light Salmon → Blue Violet
        "Friendship": [(255, 192, 203), (0, 100, 80), (255, 105, 180), (0, 200, 160)],  # Pink → Dark Teal → Hot Pink → Medium Teal
        "Hope": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],  # Dark Blue → Yellow → Steel Blue → Gold
        "Creativity": [(255, 0, 127), (0, 0, 139), (255, 20, 147), (75, 0, 130)],  # Deep Pink → Dark Blue → Deep Pink → Dark Purple
        "Inner Peace": [(135, 206, 235), (0, 0, 100), (176, 224, 230), (75, 0, 130)],  # Sky Blue → Dark Blue → Powder Blue → Dark Purple
        "Confidence": [(255, 69, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],  # Red Orange → Dark Blue → Orange → Steel Blue
        "Perseverance": [(139, 69, 19), (255, 215, 0), (160, 82, 45), (255, 140, 0)],  # Saddle Brown → Gold → Sienna → Orange
        "Inspiration": [(255, 0, 255), (75, 0, 130), (255, 20, 147), (0, 0, 139)],  # Magenta → Dark Purple → Deep Pink → Dark Blue
        "Positive Life": [(50, 205, 50), (255, 0, 127), (144, 238, 144), (255, 20, 147)],  # Lime Green → Deep Pink → Light Green → Deep Pink
        "Courage": [(178, 34, 34), (255, 215, 0), (220, 20, 60), (255, 140, 0)],  # Firebrick → Gold → Crimson → Orange
        "Kindness": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],  # Light Salmon → Dark Purple → Light Salmon → Dark Purple
        "Patience": [(34, 139, 34), (255, 255, 0), (60, 179, 113), (255, 215, 0)],  # Forest Green → Yellow → Medium Sea Green → Gold
        "Forgiveness": [(230, 230, 250), (75, 0, 130), (216, 191, 216), (138, 43, 226)],  # Lavender → Dark Purple → Thistle → Blue Violet
        "Strength": [(100, 100, 100), (255, 69, 0), (150, 150, 150), (255, 140, 0)],  # Gray → Red Orange → Light Gray → Orange
        "Joy": [(255, 255, 0), (255, 0, 127), (255, 215, 0), (147, 112, 219)],  # Yellow → Deep Pink → Gold → Purple
        "Balance": [(60, 179, 113), (138, 43, 226), (152, 251, 152), (75, 0, 130)],  # Medium Sea Green → Dark Purple → Pale Green → Dark Purple
        "Growth": [(0, 100, 0), (255, 215, 0), (34, 139, 34), (255, 140, 0)],  # Dark Green → Gold → Forest Green → Orange
        "Purpose": [(75, 0, 130), (255, 215, 0), (138, 43, 226), (255, 140, 0)],  # Dark Purple → Gold → Blue Violet → Orange
        "Mindfulness": [(210, 180, 140), (75, 0, 130), (245, 245, 220), (138, 43, 226)],  # Tan → Dark Purple → Beige → Blue Violet
        # Essential Japanese Learning Categories
        "Greetings": [(70, 130, 180), (255, 140, 0), (255, 255, 0), (255, 99, 71)],  # Steel Blue → Orange → Yellow → Tomato
        "Basic Phrases": [(60, 179, 113), (255, 215, 0), (144, 238, 144), (255, 140, 0)],  # Medium Sea Green → Gold → Light Green → Orange
        "Common Expressions": [(138, 43, 226), (255, 20, 147), (75, 0, 130), (255, 105, 180)],  # Dark Violet → Deep Pink → Dark Purple → Hot Pink
        "Travel Japanese": [(0, 191, 255), (255, 255, 0), (70, 130, 180), (255, 215, 0)],  # Deep Sky Blue → Yellow → Steel Blue → Gold
        "Restaurant Japanese": [(255, 69, 0), (255, 215, 0), (220, 20, 60), (255, 140, 0)],  # Red Orange → Gold → Crimson → Orange
        "Shopping Japanese": [(255, 105, 180), (0, 100, 80), (255, 192, 203), (0, 200, 160)],  # Hot Pink → Dark Teal → Pink → Medium Teal
        "Emergency Japanese": [(255, 0, 0), (139, 0, 0), (255, 69, 0), (220, 20, 60)],  # Red → Dark Red → Red Orange → Crimson
        "Family Terms": [(255, 182, 193), (138, 43, 226), (255, 160, 122), (75, 0, 130)],  # Light Pink → Dark Purple → Light Salmon → Dark Purple
        "Numbers Japanese": [(255, 215, 0), (0, 0, 139), (255, 140, 0), (70, 130, 180)],  # Gold → Dark Blue → Orange → Steel Blue
        "Time Japanese": [(0, 0, 100), (255, 255, 0), (70, 130, 180), (255, 215, 0)],  # Dark Blue → Yellow → Steel Blue → Gold
    }

    colors = category_colors.get(category_english, [(138, 43, 226), (75, 0, 130), (255, 20, 147), (147, 112, 219)])

    # Create smooth multi-stop gradient
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.33:
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * (ratio * 3))
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * (ratio * 3))
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * (ratio * 3))
        elif ratio < 0.66:
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * ((ratio - 0.33) * 3))
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * ((ratio - 0.33) * 3))
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * ((ratio - 0.33) * 3))
        else:
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * ((ratio - 0.66) * 3))
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * ((ratio - 0.66) * 3))
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * ((ratio - 0.66) * 3))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    # Add subtle geometric pattern for depth (circles)
    for i in range(0, VIDEO_WIDTH, 120):
        for j in range(0, VIDEO_HEIGHT, 120):
            draw.ellipse(
                [(i + 30, j + 30), (i + 90, j + 90)],
                outline=(255, 255, 255, 20),
                width=1
            )

    # Add radial glow effect from center
    glow = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for radius in range(800, 0, -50):
        alpha = int(30 * (1 - radius / 800))
        glow_draw.ellipse(
            [(VIDEO_WIDTH//2 - radius, VIDEO_HEIGHT//3 - radius),
             (VIDEO_WIDTH//2 + radius, VIDEO_HEIGHT//3 + radius)],
            fill=(255, 255, 255, alpha)
        )

    # Composite glow over background
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, glow)

    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with impressive background"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_impressive_background(category_english)
    draw = ImageDraw.Draw(img)

    # Load fonts - Optimized for mobile viewing (INCREASED sizes)
    # English text fonts (bold, professional) - Linux/Windows fallback
    english_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux (GitHub Actions)
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Alternative Linux
        "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
        "C:/Windows/Fonts/segoeui.ttf",  # Windows Segoe UI
    ]

    # Japanese fonts (for Japanese characters only) - Bold versions
    japanese_font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # Linux (GitHub Actions)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",  # Alternative Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Alternative Linux
        "C:/Windows/Fonts/msgothic.ttc",  # Windows MS Gothic (Japanese)
        "C:/Windows/Fonts/msmincho.ttc",  # Windows MS Mincho (Japanese)
    ]

    def load_font(font_paths, size):
        """Load font with fallback"""
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (IOError, OSError):
                continue
        # Last resort - use default
        return ImageFont.load_default()

    # English text fonts (bold, professional)
    font_category = load_font(english_font_paths, 60)
    font_large = load_font(english_font_paths, 85)
    font_branding = load_font(english_font_paths, 52)

    # Japanese text fonts (supports Japanese characters, bold)
    font_japanese = load_font(japanese_font_paths, 65)  # Reduced from 75 to fit better

    # Romaji fonts - BOLD and LARGER for better visibility
    # Use English bold fonts for romaji (Latin characters)
    font_romaji = load_font(english_font_paths, 55)  # Increased size and uses bold font

    english = phrase_data.get("english", "")
    japanese = phrase_data.get("japanese", "")
    romaji = phrase_data.get("romaji", "")

    def wrap_text(text, font, max_width):
        """Wrap text to fit within max_width - handles both English and Japanese"""
        lines = []
        
        # For Japanese text (no spaces), split by character count
        # Japanese characters are wider, so use smaller limit
        is_japanese = any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in text)
        
        if is_japanese:
            # Japanese: split by character count (14 chars max per line for safe fit)
            max_chars = 14
            for i in range(0, len(text), max_chars):
                lines.append(text[i:i + max_chars])
        else:
            # English: split by words
            words = text.split()
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                width = bbox[2] - bbox[0]
                if width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
        
        return lines

    # Category at top
    category_text = category_english.upper()
    category_bbox = draw.textbbox((VIDEO_WIDTH // 2, 140), category_text, font=font_category, anchor="mm")
    padding = 25
    draw.rectangle(
        [(category_bbox[0] - padding, category_bbox[1] - padding),
         (category_bbox[2] + padding, category_bbox[3] + padding)],
        fill=(0, 0, 0, 200)
    )
    draw.text(
        (VIDEO_WIDTH // 2, 140),
        category_text,
        fill=(255, 255, 255),
        font=font_category,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    # English text
    english_y = 470  # Adjusted for larger fonts
    english_lines = wrap_text(english, font_large, VIDEO_WIDTH - 140)
    total_height = len(english_lines) * 95  # Increased from 75 for larger fonts

    draw.rectangle(
        [(60, english_y - 55), (VIDEO_WIDTH - 60, english_y + total_height + 15)],
        fill=(20, 30, 80, 220)
    )

    for i, line in enumerate(english_lines):
        y_pos = english_y + (i * 95)  # Increased spacing
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 255),
            font=font_large,
            anchor="mm",
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

    # Japanese text - with proper wrapping and container
    japanese_y = english_y + total_height + 110
    japanese_lines = wrap_text(japanese, font_japanese, VIDEO_WIDTH - 200)
    total_height = len(japanese_lines) * 75  # Spacing for 65px font

    # Add extra padding for Japanese text container
    japanese_padding = 60
    draw.rectangle(
        [(50, japanese_y - japanese_padding), (VIDEO_WIDTH - 50, japanese_y + total_height + japanese_padding - 10)],
        fill=(80, 30, 30, 220)
    )

    for i, line in enumerate(japanese_lines):
        y_pos = japanese_y + (i * 75)
        draw.text(
            (VIDEO_WIDTH // 2, y_pos),
            line,
            fill=(255, 255, 0),
            font=font_japanese,
            anchor="mm",
            stroke_width=3,
            stroke_fill=(0, 0, 0)
        )

    # Romaji with FILLED BOX - BOLDER text for better visibility
    romaji_y = japanese_y + total_height + 90  # Increased from 80
    romaji_text = f"[{romaji}]"
    romaji_lines = wrap_text(romaji_text, font_romaji, VIDEO_WIDTH - 160)

    if romaji_lines:
        romaji_total_height = len(romaji_lines) * 60  # Increased spacing for larger font
        draw.rectangle(
            [(70, romaji_y - 25), (VIDEO_WIDTH - 70, romaji_y + romaji_total_height + 15)],
            fill=(40, 40, 40, 230)
        )

        for i, romaji_line in enumerate(romaji_lines):
            y_pos = romaji_y + (i * 60)  # Increased spacing to match font size
            draw.text(
                (VIDEO_WIDTH // 2, y_pos),
                romaji_line,
                fill=(255, 255, 255),  # Brighter white for better contrast
                font=font_romaji,
                anchor="mm",
                stroke_width=3,  # Increased from 2 to 3 for much bolder text
                stroke_fill=(0, 0, 0, 220)
            )

    # Branding
    branding_y = VIDEO_HEIGHT - 100
    draw.rectangle(
        [(0, branding_y - 30), (VIDEO_WIDTH, branding_y + 50)],
        fill=(0, 0, 0, 180)
    )
    draw.text(
        (VIDEO_WIDTH // 2, branding_y),
        "VELOCITY JAPANESE",
        fill=(255, 255, 255),
        font=font_branding,
        anchor="mm",
        stroke_width=2,
        stroke_fill=(0, 0, 0)
    )

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    print(f"  ✓ Image: {Path(output_path).name}")
    return output_path


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating video from {len(image_files)} images...")
    print(f"[video] Ensuring complete audio playback and sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + JP: {audio_info.get('jp_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    # Concatenate clips
    print("[video] Concatenating clips...")
    temp_video = Path(output_file).parent / "temp_video.mp4"
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(temp_video)]
    subprocess.run(cmd, check=True, capture_output=True)

    # Add audio
    print("[video] Adding audio (ensuring complete playback)...")
    audio_duration = get_audio_duration(combined_audio)
    print(f"[video] Audio duration: {audio_duration:.2f}s")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(temp_video),
        "-i", str(combined_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Verify
    video_duration = get_audio_duration(str(output_file).replace(".mp4", ".mp4"))
    print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    # Cleanup
    for clip in temp_clips:
        if clip.exists():
            clip.unlink()
    if temp_video.exists():
        temp_video.unlink()
    if concat_file.exists():
        concat_file.unlink()


# ============== MAIN WORKFLOW ==============

def generate_reel(category_english: str = None):
    """Generate complete Facebook Reel"""

    if not category_english:
        # Use smart category rotation to prevent repeats
        category_english = get_available_category()

    print(f"\n{'='*80}")
    print(f"Category: {category_english} ({CATEGORIES_JAPANESE[category_english]})")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reel_dir = VIDEO_DIR / f"{category_english}_{timestamp}"
    reel_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print("[1/4] Generating unique phrases (checking history)...")
    phrases = generate_phrases(category_english, num_phrases=5)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['japanese']}")

    # Step 2: Generate images
    print("\n[2/4] Generating images with impressive backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = reel_dir / f"phrase_{i:02d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        print(f"  ✓ Image {i+1}: {phrase['english'][:40]}...")

    # Step 3: Generate audio
    print("\n[3/4] Generating audio (English + Japanese with 500ms pause)...")
    audio_files = generate_all_audio(phrases, str(reel_dir))

    final_audio = reel_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Step 4: Create video - CRITICAL: Sort images for correct order
    print("\n[4/4] Creating video...")
    output_video = reel_dir / "final_reel.mp4"

    image_files = sorted([str(p) for p in reel_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    # Save metadata
    metadata = {
        "category_english": category_english,
        "category_japanese": CATEGORIES_JAPANESE[category_english],
        "timestamp": timestamp,
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio)
    }

    with open(reel_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"✅ REEL COMPLETE!")
    print(f"  📁 {reel_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🏷️  Branding: Velocity Japanese")
    print(f"{'='*80}\n")

    return metadata


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🇯🇵 VELOCITY JAPANESE - FACEBOOK REELS AUTOMATION 🇯🇵")
    print("="*80)
    print("\n✨ IMPROVED FEATURES:")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Complete audio playback guaranteed")
    print("  ✓ English category names (for American/European learners)")
    print("  ✓ Velocity Japanese branding at bottom")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print(f"\n📊 AVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_JAPANESE[cat]})")
    print(f"\n📅 DAILY CAPACITY:")
    print(f"  • 4 reels per day = 20 unique phrases daily")
    print(f"  • {len(CATEGORIES_ENGLISH)} categories = Over 6 days before any category repeats")
    print(f"  • Phrase history is PERMANENT (never deletes)")
    print(f"  • AI generates FRESH phrases every time")
    print("="*80)

    generate_reel()

    print("\n" + "="*80)
    print("✅ READY FOR DAILY AUTOMATION!")
    print("="*80)
    print("\nTo generate 4 reels for today:")
    print("  from facebook_reels_automation import generate_daily_content")
    print("  generate_daily_content(times_per_day=4)")
    print("\nTo generate a single reel:")
    print("  generate_reel('Love')  # Or any category from the list above")
    print("="*80)

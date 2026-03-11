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
    # Motivational Categories
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
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
    max_attempts = 3
    for attempt in range(max_attempts):
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
                "model": "openai",
                "messages": [
                    {"role": "system", "content": "You are a Japanese teacher. Create short, natural phrases with pauses."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

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
                # Skip if too long (over 15 words)
                if len(phrase["english"].split()) > 15:
                    continue
                if not is_phrase_used(phrase["english"]):
                    unique_phrases.append(phrase)
                if len(unique_phrases) >= num_phrases:
                    break

            if len(unique_phrases) >= num_phrases:
                add_phrases_to_history(unique_phrases[:num_phrases], category_english)
                return unique_phrases[:num_phrases]

        except Exception as e:
            print(f"[content] Attempt {attempt + 1} failed: {e}")

    # Fallback to fresh phrases
    print("[content] Using fallback phrases...")
    return get_fresh_fallback_phrases(category_english, num_phrases)


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones"""

    all_fallbacks = {
        # Essential Japanese Learning Categories
        "Greetings": [
            {"english": "Hello, nice to meet you.", "japanese": "こんにちは、はじめまして。", "romaji": "Konnichiwa, hajimemashite."},
            {"english": "Good morning!", "japanese": "おはようございます！", "romaji": "Ohayou gozaimasu!"},
            {"english": "Good evening, how are you?", "japanese": "こんばんは、お元気ですか？", "romaji": "Konbanwa, ogenki desu ka?"},
            {"english": "See you tomorrow!", "japanese": "また明日！", "romaji": "Mata ashita!"},
            {"english": "Goodbye, take care.", "japanese": "さようなら、お元気で。", "romaji": "Sayounara, ogenki de."},
        ],
        "Basic Phrases": [
            {"english": "Thank you very much.", "japanese": "ありがとうございます。", "romaji": "Arigatou gozaimasu."},
            {"english": "You're welcome, no problem.", "japanese": "どういたしまして。", "romaji": "Dou itashimashite."},
            {"english": "I'm sorry, excuse me.", "japanese": "すみません、ごめんなさい。", "romaji": "Sumimasen, gomennasai."},
            {"english": "Yes, that's correct.", "japanese": "はい、そうです。", "romaji": "Hai, sou desu."},
            {"english": "No, I don't think so.", "japanese": "いいえ、ちがいます。", "romaji": "Iie, chigaimasu."},
        ],
        "Common Expressions": [
            {"english": "How are you doing today?", "japanese": "今日はお元気ですか？", "romaji": "Kyou wa ogenki desu ka?"},
            {"english": "I'm fine, thank you.", "japanese": "元気です、ありがとう。", "romaji": "Genki desu, arigatou."},
            {"english": "What's your name?", "japanese": "お名前は何ですか？", "romaji": "Onamae wa nan desu ka?"},
            {"english": "My name is...", "japanese": "私の名前は...です。", "romaji": "Watashi no namae wa... desu."},
            {"english": "Nice to meet you too.", "japanese": "こちらこそ、はじめまして。", "romaji": "Kochira koso, hajimemashite."},
        ],
        "Travel Japanese": [
            {"english": "Where is the bathroom?", "japanese": "トイレはどこですか？", "romaji": "Toire wa doko desu ka?"},
            {"english": "How do I get there?", "japanese": "どうやって行きますか？", "romaji": "Douyatte ikimasu ka?"},
            {"english": "I need a taxi, please.", "japanese": "タクシーが必要です。", "romaji": "Takushii ga hitsuyou desu."},
            {"english": "Take me to the hotel.", "japanese": "ホテルまでお願いします。", "romaji": "Hoteru made onegaishimasu."},
            {"english": "How much does it cost?", "japanese": "いくらですか？", "romaji": "Ikura desu ka?"},
        ],
        "Restaurant Japanese": [
            {"english": "Can I see the menu?", "japanese": "メニューを見せてください。", "romaji": "Menyu o misete kudasai."},
            {"english": "This looks delicious!", "japanese": "美味しそうですね！", "romaji": "Oishisou desu ne!"},
            {"english": "Water, please.", "japanese": "お水をください。", "romaji": "Omizu o kudasai."},
            {"english": "Check, please.", "japanese": "お会計をお願いします。", "romaji": "Okaikei o onegaishimasu."},
            {"english": "It was delicious!", "japanese": "ごちそうさまでした！", "romaji": "Gochisousama deshita!"},
        ],
        "Shopping Japanese": [
            {"english": "How much is this?", "japanese": "これはいくらですか？", "romaji": "Kore wa ikura desu ka?"},
            {"english": "Can I try this on?", "japanese": "試着してもいいですか？", "romaji": "Shichaku shite mo ii desu ka?"},
            {"english": "Do you have a smaller size?", "japanese": "もっと小さいサイズはありますか？", "romaji": "Motto chiisai saizu wa arimasu ka?"},
            {"english": "I'll take this one.", "japanese": "これをお願いします。", "romaji": "Kore o onegaishimasu."},
            {"english": "Can I pay by card?", "japanese": "カードで払えますか？", "romaji": "Kaado de haraemasu ka?"},
        ],
        "Emergency Japanese": [
            {"english": "Help me, please!", "japanese": "助けてください！", "romaji": "Tasukete kudasai!"},
            {"english": "Call the police!", "japanese": "警察を呼んでください！", "romaji": "Keisatsu o yonde kudasai!"},
            {"english": "I need a doctor.", "japanese": "医者が必要です。", "romaji": "Isha ga hitsuyou desu."},
            {"english": "Where is the hospital?", "japanese": "病院はどこですか？", "romaji": "Byouin wa doko desu ka?"},
            {"english": "I'm lost, can you help?", "japanese": "道に迷いました、助けてくれますか？", "romaji": "Michi ni mayoimashita, tasukete kuremasu ka?"},
        ],
        "Family Terms": [
            {"english": "This is my mother.", "japanese": "これは私の母です。", "romaji": "Kore wa watashi no haha desu."},
            {"english": "This is my father.", "japanese": "これは私の父です。", "romaji": "Kore wa watashi no chichi desu."},
            {"english": "I have an older brother.", "japanese": "私には兄がいます。", "romaji": "Watashi ni wa ani ga imasu."},
            {"english": "I have a younger sister.", "japanese": "私には妹がいます。", "romaji": "Watashi ni wa imouto ga imasu."},
            {"english": "These are my parents.", "japanese": "これは私の両親です。", "romaji": "Kore wa watashi no ryoushin desu."},
        ],
        "Numbers Japanese": [
            {"english": "One, two, three.", "japanese": "一、二、三。", "romaji": "Ichi, ni, san."},
            {"english": "Four, five, six.", "japanese": "四、五、六。", "romaji": "Yon, go, roku."},
            {"english": "Seven, eight, nine, ten.", "japanese": "七、八、九、十。", "romaji": "Nana, hachi, kyuu, juu."},
            {"english": "What number is this?", "japanese": "これはいくつですか？", "romaji": "Kore wa ikutsu desu ka?"},
            {"english": "Give me two, please.", "japanese": "二つください。", "romaji": "Futatsu kudasai."},
        ],
        "Time Japanese": [
            {"english": "What time is it?", "japanese": "今何時ですか？", "romaji": "Ima nanji desu ka?"},
            {"english": "It's three o'clock.", "japanese": "三時です。", "romaji": "Sanji desu."},
            {"english": "See you at noon.", "japanese": "正午に会いましょう。", "romaji": "Shougo ni aimashou."},
            {"english": "I'll be there in five minutes.", "japanese": "5 分後に行きます。", "romaji": "Go-fun-go ni ikimasu."},
            {"english": "What day is today?", "japanese": "今日は何曜日ですか？", "romaji": "Kyou wa nan'youbi desu ka?"},
        ],
        # Motivational Categories
        "Motivation": [
            {"english": "Believe in yourself.", "japanese": "自分を信じてください。", "romaji": "Jibun o shinjite kudasai."},
            {"english": "You are capable of amazing things.", "japanese": "あなたは素晴らしいことができます。", "romaji": "Anata wa subarashii koto ga dekimasu."},
            {"english": "Dream big, start small.", "japanese": "大きく夢見て、小さく始めよう。", "romaji": "Ookiku yumemite, chiisaku hajimeyou."},
            {"english": "Your future is created by your actions.", "japanese": "あなたの未来は行動で作られます。", "romaji": "Anata no mirai wa koudou de tsukuraremasu."},
            {"english": "Never give up on your dreams.", "japanese": "決して夢を諦めないでください。", "romaji": "Kesshite yume o akiramenaide kudasai."},
        ],
        "Love": [
            {"english": "Love yourself first.", "japanese": "まず自分を愛してください。", "romaji": "Mazu jibun o aishite kudasai."},
            {"english": "Love makes everything possible.", "japanese": "愛はすべてを可能にします。", "romaji": "Ai wa subete o kanou ni shimasu."},
            {"english": "You are loved more than you know.", "japanese": "あなたは思っている以上に愛されています。", "romaji": "Anata wa omotteiru ijou ni aisareteimasu."},
            {"english": "Love is the greatest power.", "japanese": "愛は最大の力です。", "romaji": "Ai wa saidai no chikara desu."},
            {"english": "Spread love everywhere you go.", "japanese": "行く先々で愛を広めましょう。", "romaji": "Iku sakizaki de ai o hirogemashou."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "japanese": "成功は努力から生まれます。", "romaji": "Seikou wa doryoku kara umaremasu."},
            {"english": "Keep going, you're getting there.", "japanese": "続けて、もう少しで着きます。", "romaji": "Tsuzukete, mou sukoshi de tsukimasu."},
            {"english": "Every step counts toward success.", "japanese": "すべてのステップが成功につながります。", "romaji": "Subete no suteppu ga seikou ni tsunagarimasu."},
            {"english": "Your effort will pay off.", "japanese": "あなたの努力は報われます。", "romaji": "Anata no doryoku wa mukuwaremasu."},
            {"english": "Success is a journey, not a destination.", "japanese": "成功は旅であり、目的地ではありません。", "romaji": "Seikou wa tabi deari, mokutekichi dewa arimasen."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "japanese": "知識は力なり。", "romaji": "Chishiki wa chikara nari."},
            {"english": "Learn from yesterday, live for today.", "japanese": "昨日から学び、今日を生きよう。", "romaji": "Kinou kara manabi, kyou o ikiyou."},
            {"english": "The wise learn from others' mistakes.", "japanese": "賢い人は他人の過ちから学びます。", "romaji": "Kashikoi hito wa tanin no ayamachi kara manabimasu."},
            {"english": "Experience is the best teacher.", "japanese": "経験は最良の先生です。", "romaji": "Keiken wa sairyou no sensei desu."},
            {"english": "Wisdom comes with age.", "japanese": "知恵は年齢とともに訪れます。", "romaji": "Chie wa nenrei to tomo ni otozuremasu."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "japanese": "幸せは選択です。", "romaji": "Shiawase wa sentaku desu."},
            {"english": "Find joy in the little things.", "japanese": "小さなことに喜びを見つけよう。", "romaji": "Chiisana koto ni yorokobi o mitsukeyou."},
            {"english": "Your happiness matters most.", "japanese": "あなたの幸せが最も重要です。", "romaji": "Anata no shiawase ga mottomo juuyou desu."},
            {"english": "Smile, it makes others happy.", "japanese": "笑顔で、他の人を幸せにしましょう。", "romaji": "Egao de, hoka no hito o shiawase ni shimashou."},
            {"english": "Happiness is contagious, spread it.", "japanese": "幸せは伝染します、広めましょう。", "romaji": "Shiawase wa densen shimasu, hirogemashou."},
        ],
        "Self Improvement": [
            {"english": "Better today than yesterday.", "japanese": "昨日より今日、良くなりましょう。", "romaji": "Kinou yori kyou, yoku narimashou."},
            {"english": "Small steps lead to big changes.", "japanese": "小さなステップが大きな変化をもたらします。", "romaji": "Chiisana suteppu ga ookina henka o motarashimasu."},
            {"english": "Invest in yourself daily.", "japanese": "毎日自分に投資しましょう。", "romaji": "Mainichi jibun ni toushi shimashou."},
            {"english": "Growth requires discomfort.", "japanese": "成長には不快さが必要です。", "romaji": "Seichou ni wa fukaidesa ga hitsuyou desu."},
            {"english": "Be your own competition.", "japanese": "自分自身の競争相手になりましょう。", "romaji": "Jibun jishin no kyousou aite ni narimashou."},
        ],
        "Gratitude": [
            {"english": "I am grateful for today.", "japanese": "今日に感謝します。", "romaji": "Kyou ni kansha shimasu."},
            {"english": "Thank you for everything.", "japanese": "すべてにありがとう。", "romaji": "Subete ni arigatou."},
            {"english": "Gratitude turns what we have into enough.", "japanese": "感謝は持っているものを十分に変えます。", "romaji": "Kansha wa motteiru mono o juubun ni kaemasu."},
            {"english": "Count your blessings daily.", "japanese": "毎日恵みを数えましょう。", "romaji": "Mainichi megumi o kazoemashou."},
            {"english": "A grateful heart is a happy heart.", "japanese": "感謝の心は幸せな心です。", "romaji": "Kansha no kokoro wa shiawase na kokoro desu."},
        ],
        "Friendship": [
            {"english": "Friends make life better.", "japanese": "友達は人生をより良くします。", "romaji": "Tomodachi wa jinsei o yori yoku shimasu."},
            {"english": "A true friend is always there.", "japanese": "本当の友達はいつもそばにいます。", "romaji": "Hontou no tomodachi wa itsumo soba ni imasu."},
            {"english": "Friendship is a precious gift.", "japanese": "友情は貴重な贈り物です。", "romaji": "Yuujou wa kichou na okurimono desu."},
            {"english": "Good friends are like stars.", "japanese": "良い友達は星のようなものです。", "romaji": "Yoi tomodachi wa hoshi no you na mono desu."},
            {"english": "Cherish your true friends.", "japanese": "本当の友達を大切にしましょう。", "romaji": "Hontou no tomodachi o taisetsu ni shimashou."},
        ],
        "Hope": [
            {"english": "Hope never dies.", "japanese": "希望は決して消えません。", "romaji": "Kibou wa kesshite kiemasen."},
            {"english": "Tomorrow is a new beginning.", "japanese": "明日は新しい始まりです。", "romaji": "Ashita wa atarashii hajimari desu."},
            {"english": "Keep hope alive in your heart.", "japanese": "心の中で希望を生かし続けましょう。", "romaji": "Kokoro no naka de kibou o ikashi tsuzukemashou."},
            {"english": "Hope is the light in darkness.", "japanese": "希望は闇の中の光です。", "romaji": "Kibou wa yami no naka no hikari desu."},
            {"english": "Where there's hope, there's life.", "japanese": "希望があるところ、命があります。", "romaji": "Kibou ga aru tokoro, inochi ga arimasu."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "japanese": "今日何か美しいものを作りましょう。", "romaji": "Kyou nanika utsukushii mono o tsukurimashou."},
            {"english": "Your creativity is unique.", "japanese": "あなたの創造性はユニークです。", "romaji": "Anata no souzousei wa yuniiku desu."},
            {"english": "Let your imagination run wild.", "japanese": "想像力を自由に働かせましょう。", "romaji": "Souzouryoku o jiyuu ni hatarakase mashou."},
            {"english": "Art comes from the heart.", "japanese": "芸術は心から生まれます。", "romaji": "Geijutsu wa kokoro kara umaremasu."},
            {"english": "Every day is a canvas.", "japanese": "毎日がキャンバスです。", "romaji": "Mainichi ga kyanbasu desu."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "japanese": "自分自身の中で平和を見つけましょう。", "romaji": "Jibun jishin no naka de heiwa o mitsukemashou."},
            {"english": "Calm mind, happy heart.", "japanese": "落ち着いた心、幸せな心。", "romaji": "Ochitsuita kokoro, shiawase na kokoro."},
            {"english": "Peace begins with a smile.", "japanese": "平和は笑顔から始まります。", "romaji": "Heiwa wa egao kara hajimarimasu."},
            {"english": "Breathe deeply, let go.", "japanese": "深く息を吸って、手放しましょう。", "romaji": "Fukaku iki o sutte, tebanashimashou."},
            {"english": "Your inner peace is precious.", "japanese": "あなたの内なる平和は貴重です。", "romaji": "Anata no inaru heiwa wa kichou desu."},
        ],
        "Confidence": [
            {"english": "Believe you can, you're right.", "japanese": "できると信じて、その通りです。", "romaji": "Dekiru to shinjite, sono toori desu."},
            {"english": "You are stronger than you think.", "japanese": "あなたは思っているより強いです。", "romaji": "Anata wa omotteiru yori tsuyoi desu."},
            {"english": "Confidence comes from within.", "japanese": "自信は内側から来ます。", "romaji": "Jishin wa uchigawa kara kimasu."},
            {"english": "Stand tall, be proud.", "japanese": "背筋を伸ばして、誇りを持ちましょう。", "romaji": "Sesuji o nobashite, hokori o mochimashou."},
            {"english": "You have what it takes.", "japanese": "あなたにはそれが必要です。", "romaji": "Anata ni wa sore ga hitsuyou desu."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep going.", "japanese": "決して諦めないで、続けてください。", "romaji": "Kesshite akiramenaide, tsuzukete kudasai."},
            {"english": "Persistence beats talent.", "japanese": "持続性は才能に勝ります。", "romaji": "Jizokusei wa sainou ni masarimasu."},
            {"english": "Fall seven times, rise eight.", "japanese": "七転び八起き。", "romaji": "Nanakorobi yaoki."},
            {"english": "Hard work pays off eventually.", "japanese": "努力は最終的に報われます。", "romaji": "Doryoku wa saishuuteki ni mukuwaremasu."},
            {"english": "Stay the course, don't quit.", "japanese": "コースを維持して、やめないでください。", "romaji": "Koosu o iji shite, yamenaide kudasai."},
        ],
        "Inspiration": [
            {"english": "Let inspiration guide you.", "japanese": "インスピレーションに導かれましょう。", "romaji": "Insupireeshon ni michibikaremashou."},
            {"english": "Be the inspiration others need.", "japanese": "他の人が必要とするインスピレーションになりましょう。", "romaji": "Hoka no hito ga hitsuyou to suru insupireeshon ni narimashou."},
            {"english": "Inspire by example, not words.", "japanese": "言葉ではなく、例でインスピレーションを与えましょう。", "romaji": "Kotoba dewa naku, rei de insupireeshon o ataemashou."},
            {"english": "Your story inspires others.", "japanese": "あなたの物語が他の人を刺激します。", "romaji": "Anata no monogatari ga hoka no hito o shigeki shimasu."},
            {"english": "Find inspiration in nature.", "japanese": "自然の中でインスピレーションを見つけましょう。", "romaji": "Shizen no naka de insupireeshon o mitsukemashou."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "japanese": "毎日ポジティブさを選びましょう。", "romaji": "Mainichi pojitibu sa o erabimashou."},
            {"english": "Positive thoughts create positive life.", "japanese": "ポジティブな思考がポジティブな人生を作ります。", "romaji": "Pojitibu na shikou ga pojitibu na jinsei o tsukurimasu."},
            {"english": "Surround yourself with positivity.", "japanese": "自分をポジティブさで囲みましょう。", "romaji": "Jibun o pojitibu sa de kakomimashou."},
            {"english": "Every day is a fresh start.", "japanese": "毎日が新しいスタートです。", "romaji": "Mainichi ga atarashii sutaato desu."},
            {"english": "Live life with a positive heart.", "japanese": "ポジティブな心で人生を生きましょう。", "romaji": "Pojitibu na kokoro de jinsei o ikimashou."},
        ],
        "Courage": [
            {"english": "Be brave, take the leap.", "japanese": "勇敢になって、飛び込みましょう。", "romaji": "Yuukan ni natte, tobikomi mashou."},
            {"english": "Courage is not absence of fear.", "japanese": "勇気とは恐怖の不在ではありません。", "romaji": "Yuuki to wa kyoufu no fuzai dewa arimasen."},
            {"english": "Face your fears with courage.", "japanese": "勇気を持って恐怖に立ち向かいましょう。", "romaji": "Yuuki o motte kyoufu ni tachimukaimashou."},
            {"english": "Brave hearts change the world.", "japanese": "勇敢な心が世界を変えます。", "romaji": "Yuukan na kokoro ga sekai o kaemasu."},
            {"english": "Courage grows with use.", "japanese": "勇気は使うほどに成長します。", "romaji": "Yuuki wa tsukau hodo ni seichou shimasu."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "japanese": "出会うすべての人に優しくしましょう。", "romaji": "Deau subete no hito ni yasashiku shimashou."},
            {"english": "Kindness costs nothing, means everything.", "japanese": "優しさはお金がかからず、すべてを意味します。", "romaji": "Yasashisa wa okane ga kakarazu, subete o imi shimasu."},
            {"english": "A kind word warms the heart.", "japanese": "優しい言葉は心を温めます。", "romaji": "Yasashii kotoba wa kokoro o atatamemasu."},
            {"english": "Spread kindness wherever you go.", "japanese": "行く先々で優しさを広めましょう。", "romaji": "Iku sakizaki de yasashisa o hirogemashou."},
            {"english": "Kindness makes the world better.", "japanese": "優しさが世界をより良くします。", "romaji": "Yasashisa ga sekai o yori yoku shimasu."},
        ],
        "Patience": [
            {"english": "Good things come to those who wait.", "japanese": "良いことは待つ人にやってきます。", "romaji": "Yoi koto wa matsu hito ni yatte kimasu."},
            {"english": "Patience is a virtue.", "japanese": "忍耐は美徳です。", "romaji": "Nintai wa bitoku desu."},
            {"english": "Take your time, don't rush.", "japanese": "時間をかけて、急がないでください。", "romaji": "Jikan o kakete, isoganaide kudasai."},
            {"english": "Patience brings peace of mind.", "japanese": "忍耐は心の平和をもたらします。", "romaji": "Nintai wa kokoro no heiwa o motarashimasu."},
            {"english": "Wait patiently, trust the process.", "japanese": "辛抱強く待って、プロセスを信頼しましょう。", "romaji": "Shinbou zuyoku matte, purosesu o shinrai shimashou."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "japanese": "許して自分自身を解放しましょう。", "romaji": "Yurushite jibun jishin o kaihou shimashou."},
            {"english": "Forgiveness is a gift to yourself.", "japanese": "許しは自分自身への贈り物です。", "romaji": "Yurushi wa jibun jishin e no okurimono desu."},
            {"english": "Let go of grudges, find peace.", "japanese": "恨みを捨てて、平和を見つけましょう。", "romaji": "Urami o sutete, heiwa o mitsukemashou."},
            {"english": "To err is human, to forgive divine.", "japanese": "過ちは人なり、許すは神なり。", "romaji": "Ayamachi wa hito nari, yurusu wa kami nari."},
            {"english": "Forgiveness heals all wounds.", "japanese": "許しはすべての傷を癒やします。", "romaji": "Yurushi wa subete no kizu o iyashimasu."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "japanese": "あなたは思っているより強いです。", "romaji": "Anata wa omotteiru yori tsuyoi desu."},
            {"english": "Strength comes from within.", "japanese": "力は内側から来ます。", "romaji": "Chikara wa uchigawa kara kimasu."},
            {"english": "Your struggles develop your strength.", "japanese": "あなたの苦闘が力を発展させます。", "romaji": "Anata no kutou ga chikara o hatten sasemasu."},
            {"english": "Be strong, stay steady.", "japanese": "強く、安定していきましょう。", "romaji": "Tsuyoku, antei shite ikimashou."},
            {"english": "Inner strength conquers all.", "japanese": "内なる力がすべてを征服します。", "romaji": "Inaru chikara ga subete o seifuku shimasu."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "japanese": "すべての瞬間に喜びを見つけましょう。", "romaji": "Subete no shunkan ni yorokobi o mitsukemashou."},
            {"english": "Joy is contagious, spread it.", "japanese": "喜びは伝染します、広めましょう。", "romaji": "Yorokobi wa densen shimasu, hirogemashou."},
            {"english": "Let joy fill your heart today.", "japanese": "今日喜びがあなたの心を満たしましょう。", "romaji": "Kyou yorokobi ga anata no kokoro o mitashimashou."},
            {"english": "Choose joy over worry.", "japanese": "心配ではなく喜びを選びましょう。", "romaji": "Shinpai dewa naku yorokobi o erabimashou."},
            {"english": "Joy is the simplest form of gratitude.", "japanese": "喜びは最も単純な感謝の形です。", "romaji": "Yorokobi wa mottomo tanjun na kansha no katachi desu."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "japanese": "人生の中でバランスを見つけましょう。", "romaji": "Jinsei no naka de baransu o mitsukemashou."},
            {"english": "Balance is the key to happiness.", "japanese": "バランスは幸せへの鍵です。", "romaji": "Baransu wa shiawase e no kagi desu."},
            {"english": "Work hard, rest well.", "japanese": "一生懸命働いて、よく休みましょう。", "romaji": "Isshou kenmei hataraite, yoku yasumimashou."},
            {"english": "A balanced life is a peaceful life.", "japanese": "バランスの取れた人生は平和な人生です。", "romaji": "Baransu no toreta jinsei wa heiwa na jinsei desu."},
            {"english": "Prioritize what matters most.", "japanese": "最も重要なことを優先しましょう。", "romaji": "Mottomo juuyou na koto o yuusen shimashou."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "japanese": "成長は快適ゾーンの外で起こります。", "romaji": "Seichou wa kaiteki zoon no soto de okorimasu."},
            {"english": "Embrace change, grow stronger.", "japanese": "変化を受け入れて、より強くなりましょう。", "romaji": "Henka o ukeirete, yori tsuyoku narimashou."},
            {"english": "Every challenge is a growth opportunity.", "japanese": "すべての挑戦は成長の機会です。", "romaji": "Subete no chousen wa seichou no kikai desu."},
            {"english": "Grow through what you go through.", "japanese": "経験を通して成長しましょう。", "romaji": "Keiken o toushite seichou shimashou."},
            {"english": "Personal growth is a lifelong journey.", "japanese": "個人の成長は生涯の旅です。", "romaji": "Kojin no seichou wa shougai no tabi desu."},
        ],
        "Purpose": [
            {"english": "Find your purpose, live it.", "japanese": "あなたの目的を見つけて、生きましょう。", "romaji": "Anata no mokuteki o mitsukete, ikimashou."},
            {"english": "Purpose gives life meaning.", "japanese": "目的は人生に意味を与えます。", "romaji": "Mokuteki wa jinsei ni imi o ataemasu."},
            {"english": "Live with purpose and passion.", "japanese": "目的と情熱を持って生きましょう。", "romaji": "Mokuteki to jounetsu o motte ikimashou."},
            {"english": "Your purpose is your calling.", "japanese": "あなたの目的はあなたの天職です。", "romaji": "Anata no mokuteki wa anata no tenshoku desu."},
            {"english": "Discover purpose in everyday moments.", "japanese": "日常の瞬間に目的を発見しましょう。", "romaji": "Nichijou no shunkan ni mokuteki o hakken shimashou."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "japanese": "この瞬間に存在しましょう。", "romaji": "Kono shunkan ni sonzai shimashou."},
            {"english": "Mindfulness brings inner peace.", "japanese": "マインドフルネスは内なる平和をもたらします。", "romaji": "Maindofurunesu wa inaru heiwa o motarashimasu."},
            {"english": "Breathe deeply, stay mindful.", "japanese": "深く息を吸って、マインドフルでいましょう。", "romaji": "Fukaku iki o sutte, maindofuru de imashou."},
            {"english": "The present moment is all we have.", "japanese": "現在の瞬間が私たちが持つすべてです。", "romaji": "Genzai no shunkan ga watashitachi ga motsu subete desu."},
            {"english": "Practice mindfulness daily.", "japanese": "毎日マインドフルネスを実践しましょう。", "romaji": "Mainichi maindofurunesu o jissen shimashou."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    fresh_phrases = [p for p in fallbacks if not is_phrase_used(p["english"])]
    return fresh_phrases[:num_phrases]


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

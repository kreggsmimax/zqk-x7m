# 🇯🇵 Velocity Japanese - Automated Facebook Reels Bot

**Automated Japanese learning content generator for social media**

Generates and posts 4x daily to Facebook, Instagram, and other platforms with:
- ✅ AI-generated Japanese phrases with English translations
- ✅ Professional text-to-speech (Edge TTS)
- ✅ Beautiful gradient backgrounds with text overlays
- ✅ Perfect audio-video synchronization
- ✅ Velocity Japanese branding
- ✅ **NEVER repeats phrases** (permanent history tracking)

---

## 📅 Daily Schedule (American EST/EDT)

| Post | Time (EST) | Time (UTC) | Theme |
|------|------------|------------|-------|
| 1 | 9:00 AM | 14:00 UTC | Morning motivation |
| 2 | 12:00 PM | 17:00 UTC | Lunch break |
| 3 | 3:00 PM | 20:00 UTC | Afternoon pick-me-up |
| 4 | 7:00 PM | 00:00 UTC | Evening inspiration |

---

## 🎬 Available Categories (35 Total)

### Essential Japanese Learning (Priority)
1. Greetings (挨拶)
2. Basic Phrases (基本フレーズ)
3. Common Expressions (一般的な表現)
4. Travel Japanese (旅行日本語)
5. Restaurant Japanese (レストラン日本語)
6. Shopping Japanese (ショッピング日本語)
7. Emergency Japanese (緊急日本語)
8. Family Terms (家族用語)
9. Numbers Japanese (数字日本語)
10. Time Japanese (時間日本語)

### Motivational Categories
11. Motivation (モチベーション)
12. Love (愛)
13. Success (成功)
14. Wisdom (知恵)
15. Happiness (幸せ)
16. Self Improvement (自己啓発)
17. Gratitude (感謝)
18. Friendship (友情)
19. Hope (希望)
20. Creativity (創造性)
21. Inner Peace (内なる平和)
22. Confidence (自信)
23. Perseverance (忍耐)
24. Inspiration (インスピレーション)
25. Positive Life (ポジティブな人生)
26. Courage (勇気)
27. Kindness (優しさ)
28. Patience (我慢)
29. Forgiveness (許し)
30. Strength (力)
31. Joy (喜び)
32. Balance (バランス)
33. Growth (成長)
34. Purpose (目的)
35. Mindfulness (マインドフルネス)

---

## 🚀 GitHub Actions Setup

### Step 1: Add Secrets to GitHub Repository

Go to your GitHub repository → Settings → Secrets and variables → Actions

**Required Secrets:**

```bash
# Pollinations AI (for content generation)
POLLINATIONS_API_KEY=sk_your_api_key_here

# Facebook (for Reels upload)
FACEBOOK_ACCESS_TOKEN=your_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram (for Reels upload)
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_ACCOUNT_ID=your_account_id

# Optional: Other platforms
VK_ACCESS_TOKEN=your_token
VK_GROUP_ID=your_group_id
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_SECRET=your_secret
```

### Step 2: Enable GitHub Actions

1. Go to Actions tab in your GitHub repository
2. Enable workflows if disabled
3. The workflow will automatically run 4x daily

### Step 3: Manual Testing

You can manually trigger the workflow:
1. Go to Actions → "Velocity Japanese - Daily 4x Upload"
2. Click "Run workflow"
3. Select branch (main/master)
4. Click "Run workflow"

---

## 💻 Local Testing

### Prerequisites

```bash
# Install Python 3.11+
# Install FFmpeg
# Install dependencies
pip install -r requirements.txt
```

### Generate Single Reel

```bash
python facebook_reels_automation.py
```

### Generate Daily Content (4 reels)

```bash
python -c "from facebook_reels_automation import generate_daily_content; generate_daily_content(times_per_day=4)"
```

### Upload to Social Media

```bash
cd upload
python ../upload_all_platforms.py
```

---

## 📁 Project Structure

```
velocity Japanese/
├── .env                              # API keys and credentials
├── .github/
│   └── workflows/
│       └── daily_4x_upload.yml      # GitHub Actions workflow
├── facebook_reels_automation.py     # Main generation script
├── upload_all_platforms.py          # Unified upload script
├── upload/
│   ├── upload_upload_facebook.py
│   ├── upload_instagram.py
│   ├── upload_vk.py
│   └── ...
├── output/
│   ├── video/                       # Generated reels
│   ├── history/                     # Phrase history (NEVER delete!)
│   └── daily_summary_*.json        # Daily generation logs
└── requirements.txt
```

---

## 🔧 Configuration

### Timezone Adjustment

The workflow uses EST/EDT (UTC-5). To change timezone:

1. Edit `.github/workflows/daily_4x_upload.yml`
2. Modify cron schedules:
   ```yaml
   # For PST (UTC-8):
   - cron: '0 17 * * *'  # 9 AM PST
   - cron: '0 20 * * *'  # 12 PM PST
   - cron: '0 23 * * *'  # 3 PM PST
   - cron: '0 3 * * *'   # 7 PM PST
   ```

### Posting Frequency

To change from 4x to 3x daily:

1. Edit `.github/workflows/daily_4x_upload.yml`
2. Remove one cron schedule
3. Update `generate_daily_content(times_per_day=3)` in script

---

## 🎬 Video Specifications

- **Resolution:** 1080x1920 (9:16 vertical)
- **Format:** MP4 (H.264 + AAC)
- **Duration:** ~30-50 seconds (5 phrases)
- **Frame Rate:** 30 FPS
- **Audio:** Edge TTS (GuyNeural EN, NanamiNeural JA)

---

## 📊 Phrase History

All generated phrases are stored in:
```
output/history/all_generated_phrases.json
```

**This file is PERMANENT and should NEVER be deleted.**

It ensures:
- ✅ No phrase is ever repeated
- ✅ Fresh content every day
- ✅ Tracking of all generated content

---

## 🐛 Troubleshooting

### Video Generation Fails

```bash
# Check FFmpeg installation
ffmpeg -version

# Reinstall if needed
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS
```

### Audio Upload Fails

```bash
# Check .env file
cat .env | grep FACEBOOK
cat .env | grep INSTAGRAM

# Verify tokens are valid
# Regenerate if expired
```

### GitHub Actions Fails

1. Check Actions tab for error logs
2. Verify all secrets are set correctly
3. Check artifact uploads for generated files
4. Review logs for specific error messages

---

## 📈 Performance Metrics

- **Generation Time:** ~2-3 minutes per reel
- **Upload Time:** ~1-2 minutes per platform
- **Total Workflow:** ~5-10 minutes per post
- **Daily Capacity:** 4 posts × 5 phrases = 20 phrases/day
- **Category Rotation:** 35 categories = 9+ days before repeat

---

## 🎯 Key Features

### ✅ Perfect Audio-Video Sync
- Each image displays for exact audio duration
- English + 500ms pause + Japanese timing preserved
- No early transitions or cut-offs

### ✅ Natural Speech
- Phrases include commas for breathing room
- Example: "Dream big, start small"
- TTS sounds natural, not robotic

### ✅ Professional Design
- Multi-stop gradient backgrounds
- Distinct colors: Navy (EN) / Maroon (JA) / Gray (Romanization)
- Velocity Japanese branding on every frame

### ✅ Never Repeats
- Permanent phrase history tracking
- AI generates fresh content every time
- Checks all phrases before generation

---

## 📞 Support

For issues or questions:
1. Check GitHub Actions logs
2. Review error messages in output
3. Verify all API credentials
4. Check phrase history for duplicates

---

## 📄 License

This project is for educational purposes. Respect platform API terms of service.

---

**Made with ❤️ for Japanese learners worldwide**

🇯🇵 Learn Japanese with Velocity Japanese! 🇯🇵

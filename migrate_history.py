"""
Migrate phrase history from Korean to Japanese format
Converts 'korean' -> 'japanese' and 'romanization' -> 'romaji'
Also adds a note that these are legacy Korean phrases
"""
import json
from pathlib import Path

HISTORY_FILE = Path("output/history/all_generated_phrases.json")

if HISTORY_FILE.exists():
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    updated_count = 0
    for phrase in data.get("phrases", []):
        # Convert Korean fields to Japanese fields
        if "korean" in phrase:
            phrase["japanese"] = phrase.pop("korean")
            phrase["is_legacy_korean"] = True  # Mark as legacy
            updated_count += 1
        if "romanization" in phrase:
            phrase["romaji"] = phrase.pop("romanization")
    
    # Save updated history
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Migrated {updated_count} phrases from Korean to Japanese format")
    print(f"   - 'korean' → 'japanese'")
    print(f"   - 'romanization' → 'romaji'")
    print(f"   - Legacy Korean phrases marked with 'is_legacy_korean: True'")
    print(f"\n💡 These legacy phrases won't block new Japanese content generation")
else:
    print("No phrase history found to migrate")

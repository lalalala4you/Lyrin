#!/usr/bin/env python3
"""Seed the singing tutorials database with curated content."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "syncroony.db")

TUTORIALS = [
    # Whistle Voice tutorials
    {
        "category": "🪽 Whistle Voice (ホイッスルボイス)",
        "title": "How to Find Your Whistle Voice — Beginner's Guide",
        "youtube_video_id": "b2NZldAdT1I",
        "description": "Step-by-step whistle register discovery. Start with sirens and build upward."
    },
    {
        "category": "🪽 Whistle Voice (ホイッスルボイス)",
        "title": "Whistle Voice Exercises — Build Range & Control",
        "youtube_video_id": "FmnJe2evL_M",
        "description": "Daily exercises to strengthen your whistle register. Mariah Carey-style technique."
    },
    {
        "category": "🪽 Whistle Voice (ホイッスルボイス)",
        "title": "Mariah Carey Whistle Register Analysis",
        "youtube_video_id": "q8LAVqGn4Qo",
        "description": "Break down the Queen of Whistle Voice's technique. Learn from the master."
    },
    # Mixed Voice
    {
        "category": "🎵 Mixed Voice (ミックスボイス)",
        "title": "Mixed Voice Explained — Connect Chest & Head Voice",
        "youtube_video_id": "wVJiOjtO5lg",
        "description": "The essential technique for smooth transitions between registers."
    },
    {
        "category": "🎵 Mixed Voice (ミックスボイス)",
        "title": "Daily Mixed Voice Warmup Routine",
        "youtube_video_id": "JgMJJvEDnDU",
        "description": "15-minute daily routine to build mixed voice strength and consistency."
    },
    # Vibrato & Control
    {
        "category": "🌊 Vibrato & Vocal Control",
        "title": "How to Develop Natural Vibrato",
        "youtube_video_id": "JNLaFkUmCts",
        "description": "Stop forcing vibrato — learn to let it happen naturally with proper breath support."
    },
    {
        "category": "🌊 Vibrato & Vocal Control",
        "title": "Enka-style Vibrato Technique (演歌のビブラート)",
        "youtube_video_id": "N_L0D6S4QJM",
        "description": "Japanese enka vibrato — long, controlled oscillation. Essential for 美空ひばり style."
    },
    # Belting
    {
        "category": "🔊 Belting & Power Vocals",
        "title": "Safe Belting Technique — Power Without Strain",
        "youtube_video_id": "I5EbwB6nBns",
        "description": "Learn to belt without hurting your voice. Proper breath support and placement."
    },
    # Breath Support
    {
        "category": "💨 Breath Support Fundamentals",
        "title": "Diaphragmatic Breathing for Singers",
        "youtube_video_id": "k_-Ww9_uk9o",
        "description": "Master the foundation of all great singing — proper breath support."
    },
]

def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS singing_tutorials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            youtube_video_id TEXT NOT NULL,
            description TEXT,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if already seeded
    c.execute("SELECT COUNT(*) FROM singing_tutorials")
    count = c.fetchone()[0]
    if count > 0:
        print(f"Already {count} tutorials in DB — skipping seed")
        conn.close()
        return
    
    for t in TUTORIALS:
        c.execute("""
            INSERT INTO singing_tutorials (category, title, youtube_video_id, description)
            VALUES (?, ?, ?, ?)
        """, (t["category"], t["title"], t["youtube_video_id"], t["description"]))
    
    conn.commit()
    print(f"✅ Seeded {len(TUTORIALS)} singing tutorials across {len(set(t['category'] for t in TUTORIALS))} categories")
    conn.close()

if __name__ == "__main__":
    seed()

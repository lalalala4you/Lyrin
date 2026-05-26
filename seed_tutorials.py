#!/usr/bin/env python3
"""Seed the singing tutorials database with REAL verified YouTube videos."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "syncroony.db")

TUTORIALS = [
    {
        "category": "🪽 Whistle Voice",
        "title": "10 Easy Techniques to Sing Whistle Register Today!",
        "youtube_video_id": "PTOPxYJ4Xnk",
        "description": "Beginner-friendly whistle voice discovery. Start finding your whistle register with simple exercises."
    },
    {
        "category": "🪽 Whistle Voice",
        "title": "Why Does Mariah Carey Touch Her Ear on High Notes?",
        "youtube_video_id": "lIgPFurxqUM",
        "description": "Vocal coach breaks down Mariah's famous whistle register technique and ear-touching secret."
    },
    {
        "category": "🎵 Mixed Voice",
        "title": "Connecting Chest and Head Voice — Tyler Wysong",
        "youtube_video_id": "7i_B-VQaDr0",
        "description": "Master the bridge between registers. Essential for smooth, strain-free singing."
    },
    {
        "category": "🎵 Mixed Voice",
        "title": "Daily Mixed Voice Vocal Exercises for Singers",
        "youtube_video_id": "POy09B_r-34",
        "description": "Quick daily routine to strengthen your mixed voice coordination."
    },
    {
        "category": "🌊 Vibrato & Control",
        "title": "How to Sing with Vibrato Using a Straw",
        "youtube_video_id": "PbnM2-GggXw",
        "description": "Unique method to develop natural vibrato — all you need is a straw."
    },
    {
        "category": "🌊 Vibrato & Control",
        "title": "ビブラートの練習法！1週間で習得 (Enka/Karaoke Vibrato)",
        "youtube_video_id": "9YrxgXwASNM",
        "description": "Japanese enka-style vibrato training. 演歌・歌謡曲向けのビブラート練習。"
    },
    {
        "category": "🔊 Belting & Power",
        "title": "How to Belt High Notes Without Strain",
        "youtube_video_id": "3bylCYaXHgc",
        "description": "Chest voice vs mixed voice belting — learn to belt safely with proper technique."
    },
    {
        "category": "💨 Breath Support",
        "title": "SING From Your DIAPHRAGM in 59 Seconds!",
        "youtube_video_id": "LlZzIlE1NLQ",
        "description": "Quick, effective diaphragmatic breathing technique. The foundation of all great singing."
    },
]

def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("CREATE TABLE IF NOT EXISTS singing_tutorials (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, title TEXT NOT NULL, youtube_video_id TEXT NOT NULL, description TEXT, added_date TEXT DEFAULT CURRENT_TIMESTAMP)")
    
    # Clear old broken ones
    c.execute("DELETE FROM singing_tutorials")
    
    for t in TUTORIALS:
        c.execute("INSERT INTO singing_tutorials (category, title, youtube_video_id, description) VALUES (?, ?, ?, ?)",
                  (t["category"], t["title"], t["youtube_video_id"], t["description"]))
    
    conn.commit()
    print(f"✅ Seeded {len(TUTORIALS)} verified tutorials across {len(set(t['category'] for t in TUTORIALS))} categories")
    conn.close()

if __name__ == "__main__":
    seed()

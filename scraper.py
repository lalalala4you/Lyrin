#!/usr/bin/env python3
"""
Syncroony — Daily Music Trend Scanner
Fetches top songs from Apple Music charts, finds YouTube MVs, stores in SQLite.
"""
import json
import sqlite3
import os
import sys
import time
import re
import requests
from datetime import datetime, timezone, timedelta

SGT = timezone(timedelta(hours=8))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "syncroony.db")

CHARTS = {
    "global": "https://rss.marketingtools.apple.com/api/v2/us/music/most-played/10/songs.json",
    "japan": "https://rss.marketingtools.apple.com/api/v2/jp/music/most-played/10/songs.json",
    "singapore": "https://rss.marketingtools.apple.com/api/v2/sg/music/most-played/10/songs.json",
    "us": "https://rss.marketingtools.apple.com/api/v2/us/music/most-played/10/songs.json",
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_charts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            region TEXT NOT NULL,
            rank INTEGER NOT NULL,
            song_name TEXT NOT NULL,
            artist_name TEXT NOT NULL,
            album_art_url TEXT,
            apple_music_url TEXT,
            youtube_video_id TEXT,
            youtube_search_query TEXT,
            genres TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, region, rank)
        )
    """)
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
    c.execute("CREATE INDEX IF NOT EXISTS idx_charts_date ON daily_charts(date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_charts_region ON daily_charts(region)")
    conn.commit()
    return conn

def fetch_chart(url: str) -> list:
    resp = requests.get(url, headers={"User-Agent": "Syncroony/1.0"}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    songs = []
    for i, result in enumerate(data["feed"]["results"], 1):
        songs.append({
            "rank": i,
            "song_name": result["name"],
            "artist_name": result["artistName"],
            "album_art_url": result.get("artworkUrl100", "").replace("100x100", "600x600"),
            "apple_music_url": result.get("url", ""),
            "genres": ", ".join(g["name"] for g in result.get("genres", [])),
        })
    return songs

def search_youtube(song_name: str, artist_name: str) -> dict:
    query = f"{artist_name} {song_name} official music video"
    try:
        search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        resp = requests.get(search_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }, timeout=10)
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
        if video_ids:
            return {"youtube_video_id": video_ids[0], "youtube_search_query": query}
    except Exception as e:
        print(f"  ⚠️ YouTube search failed: {e}")
    return {"youtube_video_id": None, "youtube_search_query": query}

def scrape_all(date_str: str = None):
    if date_str is None:
        date_str = datetime.now(SGT).strftime("%Y-%m-%d")
    conn = init_db()
    c = conn.cursor()
    total = 0
    for region, url in CHARTS.items():
        print(f"\n📊 Fetching {region.upper()} chart...")
        try:
            songs = fetch_chart(url)
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            continue
        for song in songs:
            print(f"  #{song['rank']} {song['artist_name']} — {song['song_name'][:40]}")
            yt = search_youtube(song["song_name"], song["artist_name"])
            time.sleep(0.3)
            try:
                c.execute("""
                    INSERT OR REPLACE INTO daily_charts 
                    (date, region, rank, song_name, artist_name, album_art_url, 
                     apple_music_url, youtube_video_id, youtube_search_query, genres)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (date_str, region, song["rank"], song["song_name"],
                      song["artist_name"], song["album_art_url"],
                      song["apple_music_url"], yt["youtube_video_id"],
                      yt["youtube_search_query"], song["genres"]))
                total += 1
            except Exception as e:
                print(f"    ❌ DB error: {e}")
    conn.commit()
    c.execute("SELECT COUNT(DISTINCT song_name) FROM daily_charts WHERE date=?", (date_str,))
    unique = c.fetchone()[0]
    print(f"\n✅ Saved {total} entries ({unique} unique songs) for {date_str}")
    conn.close()
    return total

if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    scrape_all(date_arg)

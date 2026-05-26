#!/usr/bin/env python3
"""Generate the Syncroony static website from database."""
import sqlite3
import os
import json
from datetime import datetime, timezone, timedelta

SGT = timezone(timedelta(hours=8))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "syncroony.db")
SITE_DIR = os.path.join(BASE_DIR, "website")

def get_data():
    """Get all data needed for the website."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get available dates
    c.execute("SELECT DISTINCT date FROM daily_charts ORDER BY date DESC LIMIT 3")
    dates = [row["date"] for row in c.fetchall()]
    
    daily_data = {}
    for date in dates:
        c.execute("""
            SELECT * FROM daily_charts 
            WHERE date = ? AND region = 'global'
            ORDER BY rank ASC LIMIT 5
        """, (date,))
        daily_data[date] = [dict(row) for row in c.fetchall()]
    
    # Get tutorials
    c.execute("SELECT * FROM singing_tutorials ORDER BY category, id")
    tutorials = [dict(row) for row in c.fetchall()]
    
    # Get all-time stats
    c.execute("SELECT COUNT(DISTINCT date) as total_days FROM daily_charts")
    total_days = c.fetchone()["total_days"]
    
    c.execute("SELECT COUNT(DISTINCT song_name) as total_songs FROM daily_charts")
    total_songs = c.fetchone()["total_songs"]
    
    conn.close()
    
    return {
        "dates": dates,
        "daily_data": daily_data,
        "tutorials": tutorials,
        "stats": {"total_days": total_days, "total_songs": total_songs},
        "updated": datetime.now(SGT).strftime("%Y-%m-%d %H:%M SGT")
    }

def generate():
    """Generate the website."""
    data = get_data()
    
    # Read template
    template_path = os.path.join(SITE_DIR, "index.html")
    
    # Generate the full page
    html = generate_html(data)
    
    with open(template_path, "w") as f:
        f.write(html)
    
    # Also save data as JSON for dynamic loading
    js_dir = os.path.join(SITE_DIR, "js")
    os.makedirs(js_dir, exist_ok=True)
    with open(os.path.join(js_dir, "data.json"), "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Website generated: {template_path}")
    print(f"   {len(data['dates'])} days, {data['stats']['total_songs']} unique songs tracked")
    return template_path

def generate_html(data):
    """Generate the complete HTML page."""
    dates = data["dates"]
    
    # Format dates for display
    date_displays = {}
    for d in dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        date_displays[d] = dt.strftime("%B %d, %Y")
    
    # Build day tabs
    day_tabs = ""
    day_contents = ""
    colors = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff"]
    
    for i, date in enumerate(dates):
        active = "active" if i == 0 else ""
        day_tabs += f'<button class="day-tab {active}" onclick="switchDay(\'{date}\')">{date_displays[date]}</button>\n'
        
        songs = data["daily_data"].get(date, [])
        songs_html = ""
        for song in songs[:5]:
            vid_id = song.get("youtube_video_id", "")
            embed_html = ""
            if vid_id:
                embed_html = f'''<div class="video-wrapper">
                    <iframe src="https://www.youtube.com/embed/{vid_id}" 
                            frameborder="0" allowfullscreen 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
                    </iframe>
                </div>'''
            else:
                search_url = f"https://www.youtube.com/results?search_query={song.get('youtube_search_query', '').replace(' ', '+')}"
                embed_html = f'''<div class="video-wrapper no-video">
                    <a href="{search_url}" target="_blank" class="search-link">
                        🔍 Search on YouTube<br>
                        <small>{song.get('artist_name', '')} — {song.get('song_name', '')}</small>
                    </a>
                </div>'''
            
            rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][song["rank"]-1]
            genres = song.get("genres", "")
            
            songs_html += f'''
            <div class="song-card">
                <div class="song-rank">{rank_emoji} <span>#{song["rank"]}</span></div>
                <div class="song-info">
                    <div class="album-art">
                        <img src="{song.get("album_art_url", "")}" alt="{song["song_name"]}" 
                             onerror="this.style.display='none'" loading="lazy">
                    </div>
                    <div class="song-details">
                        <h3>{song["song_name"]}</h3>
                        <p class="artist">{song["artist_name"]}</p>
                        {f'<p class="genres">{genres}</p>' if genres else ''}
                    </div>
                </div>
                {embed_html}
            </div>'''
        
        day_contents += f'<div class="day-content {active}" id="day-{date}">{songs_html}</div>'
    
    # Build tutorials section
    tuts_html = ""
    tut_categories = {}
    for t in data["tutorials"]:
        cat = t["category"]
        if cat not in tut_categories:
            tut_categories[cat] = []
        tut_categories[cat].append(t)
    
    for cat, tuts in tut_categories.items():
        cat_id = cat.lower().replace(" ", "-")
        tuts_html += f'<div class="tutorial-category"><h3 id="{cat_id}">{cat}</h3><div class="tutorial-grid">'
        for t in tuts:
            tuts_html += f'''
            <div class="tutorial-card">
                <div class="video-wrapper">
                    <iframe src="https://www.youtube.com/embed/{t["youtube_video_id"]}" 
                            frameborder="0" allowfullscreen
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
                    </iframe>
                </div>
                <div class="tutorial-info">
                    <h4>{t["title"]}</h4>
                    {f'<p>{t["description"]}</p>' if t.get("description") else ''}
                </div>
            </div>'''
        tuts_html += '</div></div>'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎵 Syncroony — Daily Music Trends</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0d1b2a 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
        
        header {{
            text-align: center;
            padding: 60px 20px 40px;
            position: relative;
            overflow: hidden;
        }}
        header::before {{
            content: '';
            position: absolute;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle at 30% 50%, rgba(255,107,107,0.15) 0%, transparent 50%),
                        radial-gradient(circle at 70% 50%, rgba(77,150,255,0.15) 0%, transparent 50%);
            animation: rotate 20s linear infinite;
        }}
        @keyframes rotate {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        
        header h1 {{
            font-size: 3em;
            background: linear-gradient(135deg, #ff6b6b, #ffd93d, #6bcb77, #4d96ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            position: relative;
            margin-bottom: 10px;
        }}
        header .subtitle {{
            color: #888;
            font-size: 1.1em;
            position: relative;
        }}
        
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            margin-bottom: 40px;
            border: 1px solid rgba(255,255,255,0.06);
        }}
        .stat {{ text-align: center; }}
        .stat .num {{ font-size: 2em; font-weight: 800; color: #ffd93d; }}
        .stat .label {{ font-size: 0.85em; color: #888; margin-top: 4px; }}
        
        .day-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .day-tab {{
            padding: 12px 28px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.03);
            color: #aaa;
            border-radius: 30px;
            cursor: pointer;
            font-size: 0.95em;
            transition: all 0.3s;
        }}
        .day-tab:hover {{ border-color: rgba(255,255,255,0.3); color: #fff; }}
        .day-tab.active {{
            background: linear-gradient(135deg, rgba(255,107,107,0.3), rgba(77,150,255,0.3));
            border-color: rgba(255,107,107,0.5);
            color: #fff;
            font-weight: 600;
        }}
        
        .day-content {{ display: none; }}
        .day-content.active {{ display: block; }}
        
        .song-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.3s;
            display: grid;
            grid-template-columns: 60px 1fr 400px;
            gap: 20px;
            align-items: center;
        }}
        .song-card:hover {{
            border-color: rgba(255,255,255,0.15);
            background: rgba(255,255,255,0.05);
            transform: translateX(4px);
        }}
        .song-rank {{
            font-size: 1.2em;
            font-weight: 700;
            color: #ffd93d;
            text-align: center;
        }}
        .song-rank span {{ font-size: 0.7em; color: #888; display: block; }}
        .song-info {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        .album-art img {{
            width: 80px;
            height: 80px;
            border-radius: 12px;
            object-fit: cover;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }}
        .song-details h3 {{
            font-size: 1.1em;
            color: #fff;
            margin-bottom: 4px;
        }}
        .song-details .artist {{
            color: #aaa;
            font-size: 0.9em;
        }}
        .song-details .genres {{
            color: #666;
            font-size: 0.8em;
            margin-top: 4px;
        }}
        
        .video-wrapper {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
        }}
        .video-wrapper iframe {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            border: none;
        }}
        .video-wrapper.no-video {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: auto;
            padding: 0;
        }}
        .search-link {{
            display: block;
            text-align: center;
            color: #4d96ff;
            text-decoration: none;
            padding: 30px;
            font-size: 1.1em;
        }}
        .search-link:hover {{ color: #ffd93d; }}
        .search-link small {{ display: block; color: #888; margin-top: 6px; font-size: 0.8em; }}
        
        .section-title {{
            font-size: 2em;
            text-align: center;
            margin: 60px 0 30px;
            color: #fff;
        }}
        .section-title span {{ 
            background: linear-gradient(135deg, #6bcb77, #4d96ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .tutorial-category h3 {{
            font-size: 1.3em;
            color: #ffd93d;
            margin: 30px 0 16px;
            padding-left: 10px;
            border-left: 4px solid #ffd93d;
        }}
        .tutorial-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .tutorial-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s;
        }}
        .tutorial-card:hover {{
            border-color: rgba(255,255,255,0.2);
            transform: translateY(-4px);
        }}
        .tutorial-info {{
            padding: 16px;
        }}
        .tutorial-info h4 {{
            color: #fff;
            font-size: 1em;
            margin-bottom: 6px;
        }}
        .tutorial-info p {{
            color: #888;
            font-size: 0.85em;
            line-height: 1.5;
        }}
        
        footer {{
            text-align: center;
            padding: 40px;
            color: #555;
            font-size: 0.85em;
            margin-top: 60px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }}
        footer a {{ color: #4d96ff; text-decoration: none; }}
        
        @media (max-width: 768px) {{
            .song-card {{
                grid-template-columns: 40px 1fr;
            }}
            .song-card .video-wrapper {{
                grid-column: 1 / -1;
                padding-bottom: 56.25%;
                height: 0;
                position: relative;
            }}
            header h1 {{ font-size: 2em; }}
            .stats-bar {{ gap: 20px; }}
            .stat .num {{ font-size: 1.5em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎵 Syncroony</h1>
            <p class="subtitle">Daily Music Trends · Top 5 Hits · Singing Tutorials</p>
        </header>
        
        <div class="stats-bar">
            <div class="stat"><div class="num">{data["stats"]["total_days"]}</div><div class="label">Days Tracked</div></div>
            <div class="stat"><div class="num">{data["stats"]["total_songs"]}</div><div class="label">Unique Songs</div></div>
            <div class="stat"><div class="num">🌍</div><div class="label">Global + JP + SG</div></div>
        </div>
        
        <h2 style="text-align:center;color:#fff;margin-bottom:20px;">📊 Top 5 Daily Hits</h2>
        <div class="day-tabs">{day_tabs}</div>
        {day_contents}
        
        <h2 class="section-title">🎤 <span>Singing Tutorials</span></h2>
        {tuts_html if tuts_html else '<p style="text-align:center;color:#888;padding:40px;">🎬 Tutorials coming soon! Check back for whistle voice, mixed voice, and more.</p>'}
        
        <footer>
            <p>Powered by <a href="https://music.apple.com" target="_blank">Apple Music</a> & <a href="https://youtube.com" target="_blank">YouTube</a></p>
            <p>Curated by Rinちゃん ✨ · Updated daily · <span id="update-time">{data["updated"]}</span></p>
        </footer>
    </div>
    
    <script>
        function switchDay(date) {{
            document.querySelectorAll('.day-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.day-content').forEach(c => c.classList.remove('active'));
            document.querySelector(`[onclick*="${{date}}"]`).classList.add('active');
            document.getElementById(`day-${{date}}`).classList.add('active');
        }}
    </script>
</body>
</html>'''
    return html

if __name__ == "__main__":
    generate()

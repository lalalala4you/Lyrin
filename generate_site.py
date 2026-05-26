#!/usr/bin/env python3
"""Generate Syncroony site — warm theme + animated shapes + 2-column layout."""
import sqlite3, os
from datetime import datetime, timezone, timedelta

SGT = timezone(timedelta(hours=8))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "syncroony.db")
SITE_DIR = os.path.join(BASE_DIR, "website")

def get_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT DISTINCT date FROM daily_charts ORDER BY date DESC LIMIT 3")
    dates = [r["date"] for r in c.fetchall()]
    daily_data, regional = {}, {}
    for d in dates:
        daily_data[d] = {}
        for reg in ["global","singapore","spain","japan"]:
            c.execute("SELECT * FROM daily_charts WHERE date=? AND region=? ORDER BY rank LIMIT 5", (d, reg))
            daily_data[d][reg] = [dict(r) for r in c.fetchall()]
        c.execute("SELECT * FROM daily_charts WHERE date=? AND region!='global' AND rank=1", (d,))
        regional[d] = [dict(r) for r in c.fetchall()]
    c.execute("SELECT * FROM singing_tutorials ORDER BY category, id")
    tutorials = [dict(r) for r in c.fetchall()]
    c.execute("SELECT COUNT(DISTINCT date) as d, COUNT(DISTINCT song_name) as s FROM daily_charts")
    r = c.fetchone()
    # Per-region song counts
    region_counts = {}
    for reg in ["global","singapore","spain","japan"]:
        c.execute("SELECT COUNT(DISTINCT song_name) FROM daily_charts WHERE region=?",(reg,))
        region_counts[reg] = c.fetchone()[0]
    return {"dates": dates, "daily_data": daily_data, "regional": regional, "tutorials": tutorials,
            "stats": {"total_days": r["d"], "total_songs": r["s"], "region_counts": region_counts},
            "updated": datetime.now(SGT).strftime("%Y-%m-%d %H:%M SGT")}

def build():
    d = get_data()
    dates = d["dates"]
    
    # Region tabs
    regions = [("global","🌍 Global"),("singapore","🇸🇬 SG"),("spain","🇪🇸 ES"),("japan","🇯🇵 JP")]
    region_tabs = ""
    for i, (rid, rname) in enumerate(regions):
        act = "active" if i == 0 else ""
        region_tabs += f'<button class="tab rtab {act}" data-region="{rid}">{rname}</button>'
    
    # Date tabs
    date_tabs = ""
    for i, dt in enumerate(dates):
        lbl = datetime.strptime(dt, "%Y-%m-%d").strftime("%b %d")
        act = "active" if i == 0 else ""
        date_tabs += f'<button class="tab dtab {act}" data-date="{dt}">{lbl}</button>'
    
    # Song panels — region × date
    panels = ""
    for ri, (rid, rname) in enumerate(regions):
        for di, dt in enumerate(dates):
            act = "active" if (ri == 0 and di == 0) else ""
            cards = ""
            for s in d["daily_data"].get(dt, {}).get(rid, [])[:5]:
                vid = s.get("youtube_video_id","")
                rcls_num = {1:"r1",2:"r2",3:"r3"}.get(s["rank"],"rx")
                if vid:
                    vhtml = f'<div class="mv-wrap"><div class="mv"><iframe src="https://www.youtube.com/embed/{vid}?enablejsapi=1" allowfullscreen loading="lazy" data-vid="{vid}"></iframe><div class="mv-overlay" data-vid="{vid}"><div class="play-btn">▶</div></div></div><div class="mv-ext"><a href="https://www.youtube.com/watch?v={vid}" target="_blank">Open in YouTube ↗</a></div></div>'
                else:
                    vhtml = f'<div class="mv-wrap"><div class="mv"><a class="ytlink" href="https://www.youtube.com/results?search_query={s.get("youtube_search_query","").replace(" ","+")}" target="_blank">🔍 Search MV</a></div></div>'
                gen = s.get("genres","").split(",")[0].strip() if s.get("genres") else ""
                tags_html = ""
                if gen:
                    tags_html += f'<span class="tag">{gen}</span>'
                am_url = s.get("apple_music_url","")
                if am_url:
                    tags_html += f'<span class="tag am"><a href="{am_url}" target="_blank">♫ Music</a></span>'
                rank_display = "★" if s["rank"] == 1 else str(s["rank"])
                cards += f'''
            <div class="song {rcls_num}">
              <div class="r {rcls_num}">{rank_display}</div>
              <img class="art" src="{s.get("album_art_url","")}" loading="lazy" onerror="this.style.display='none'">
              <div class="meta">
                <div class="sn">{s["song_name"]}</div>
                <div class="sa">{s["artist_name"]}</div>
              </div>
              <div class="tags">{tags_html}</div>
              {vhtml}
            </div>'''
            panels += f'<div class="day {act}" data-region="{rid}" data-date="{dt}">{cards}</div>'
    
    # Tutorials
    tuts = ""
    cats = {}
    for t in d["tutorials"]:
        cats.setdefault(t["category"],[]).append(t)
    for cat, items in cats.items():
        tuts += f'<div class="tcat">{cat}</div>'
        for t in items:
            tuts += f'''
            <div class="tcard">
              <div class="tv"><iframe src="https://www.youtube.com/embed/{t["youtube_video_id"]}?enablejsapi=1" allowfullscreen loading="lazy" data-vid="{t["youtube_video_id"]}"></iframe><div class="mv-overlay" data-vid="{t["youtube_video_id"]}"><div class="play-btn">▶</div></div></div>
              <div class="tinfo"><div class="tt">{t["title"]}</div><div style="display:flex;align-items:center;gap:6px;padding:0 10px 8px"><a class="tlink" href="https://www.youtube.com/watch?v={t["youtube_video_id"]}" target="_blank">Watch on YouTube ↗</a></div></div>
            </div>'''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Syncroony — Daily Music Trends</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Helvetica Neue','Arial Rounded MT Bold',-apple-system,sans-serif;background:#fff8f2;color:#3d2b1f;overflow-x:hidden}}
.wrap{{max-width:1280px;margin:0 auto;padding:0 24px 40px;position:relative;z-index:1}}

/* Animated bg orbs — slow continuous drift across viewport */
.bg{{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;overflow:hidden}}
.bg .s{{position:absolute;border-radius:50%;animation-iteration-count:infinite;animation-timing-function:linear;filter:blur(2px)}}
.bg .s1{{width:400px;height:400px;background:radial-gradient(circle,#ffb347,#ffd700);opacity:.13;top:10%;left:5%;animation:drift1 26s linear infinite}}
.bg .s2{{width:260px;height:260px;background:radial-gradient(circle,#ff7b7b,#ffb3b3);opacity:.12;top:60%;left:75%;animation:drift2 30s linear infinite}}
.bg .s3{{width:200px;height:200px;background:radial-gradient(circle,#ffd93d,#ffeaa7);opacity:.14;top:85%;left:45%;animation:drift3 24s linear infinite}}
.bg .s4{{width:170px;height:170px;background:radial-gradient(circle,#f8a5c2,#fcd5e4);opacity:.11;top:40%;left:60%;animation:drift4 28s linear infinite}}
.bg .s5{{width:110px;height:110px;background:radial-gradient(circle,#ffcc80,#ffe0b2);opacity:.15;top:20%;left:85%;animation:drift1 22s linear infinite}}
.bg .s6{{width:230px;height:230px;background:radial-gradient(circle,#ff9a76,#ffc3a0);opacity:.10;top:5%;left:30%;animation:drift2 32s linear infinite}}
.bg .s7{{width:140px;height:140px;background:radial-gradient(circle,#ffeaa7,#fdcb6e);opacity:.13;top:50%;left:20%;animation:drift3 25s linear infinite}}
.bg .s8{{width:90px;height:90px;background:radial-gradient(circle,#fab1a0,#e17055);opacity:.14;top:75%;left:40%;animation:drift4 20s linear infinite}}
@keyframes drift1{{0%{{transform:translate(0,0) rotate(0deg) scale(1)}}20%{{transform:translate(8vw,15vh) rotate(5deg) scale(1.03)}}40%{{transform:translate(-12vw,-10vh) rotate(-8deg) scale(.97)}}60%{{transform:translate(5vw,-18vh) rotate(3deg) scale(1.04)}}80%{{transform:translate(-10vw,12vh) rotate(-6deg) scale(.96)}}100%{{transform:translate(0,0) rotate(0deg) scale(1)}}}}
@keyframes drift2{{0%{{transform:translate(0,0) rotate(0deg) scale(1)}}25%{{transform:translate(-14vw,8vh) rotate(-7deg) scale(1.05)}}50%{{transform:translate(10vw,-15vh) rotate(9deg) scale(.95)}}75%{{transform:translate(-8vw,-8vh) rotate(-5deg) scale(1.02)}}100%{{transform:translate(0,0) rotate(0deg) scale(1)}}}}
@keyframes drift3{{0%{{transform:translate(0,0) rotate(0deg) scale(1)}}30%{{transform:translate(15vw,-8vh) rotate(6deg) scale(.94)}}60%{{transform:translate(-10vw,14vh) rotate(-10deg) scale(1.06)}}100%{{transform:translate(0,0) rotate(0deg) scale(1)}}}}
@keyframes drift4{{0%{{transform:translate(0,0) rotate(0deg) scale(1)}}25%{{transform:translate(-10vw,-14vh) rotate(-9deg) scale(1.07)}}50%{{transform:translate(12vw,10vh) rotate(7deg) scale(.93)}}75%{{transform:translate(-5vw,15vh) rotate(-4deg) scale(1.03)}}100%{{transform:translate(0,0) rotate(0deg) scale(1)}}}}

/* Header */
header{{text-align:center;padding:50px 20px 20px;position:relative}}
header h1{{font-size:4.8em;font-weight:900;letter-spacing:-2px;position:relative;display:inline-block;font-family:'Helvetica Neue','Arial Rounded MT Bold',-apple-system,sans-serif;text-transform:lowercase;filter:drop-shadow(0 4px 12px rgba(232,135,58,.25));animation:glow 2.5s ease-in-out infinite}}
@keyframes glow{{0%,100%{{filter:drop-shadow(0 4px 12px rgba(232,135,58,.25))}}50%{{filter:drop-shadow(0 4px 24px rgba(240,160,80,.5))}}}}
header h1 .t1{{background:linear-gradient(135deg,#ff6b35,#f7931e,#ffb347);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
header h1 .t2{{background:linear-gradient(135deg,#f0a050,#ffb347,#ffd93d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
header .ico{{display:inline-block;animation:bounce 1.2s infinite;font-size:1em;background:linear-gradient(135deg,#f7931e,#ffb347,#ffd93d,#f0a050);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;filter:drop-shadow(0 0 8px rgba(255,179,71,.4))}}
@keyframes bounce{{0%,100%{{transform:translateY(0)}}40%{{transform:translateY(-12px)}}60%{{transform:translateY(-6px)}}}}
header .sub{{color:#c4a080;font-size:.85em;margin-top:6px;letter-spacing:1.2px;font-weight:500;text-transform:uppercase}}
header::after{{content:'';display:block;width:160px;height:4px;background:linear-gradient(90deg,transparent,#ff6b35,#f7931e,#f0a050,#ffd93d,transparent);margin:20px auto 0;border-radius:3px;animation:underline-pulse 2.5s ease-in-out infinite}}
@keyframes underline-pulse{{0%,100%{{width:160px;opacity:.8}}50%{{width:220px;opacity:1}}}}

/* Stats + Region cards — one centered row */
.top-bar{{display:flex;justify-content:center;align-items:stretch;gap:16px;margin:0 auto 24px;flex-wrap:wrap;max-width:900px}}
.top-bar .b{{background:#fff;border-radius:14px;padding:14px 26px;box-shadow:0 2px 12px rgba(200,140,60,.08);border:1px solid rgba(240,180,100,.15);text-align:center;min-width:100px;transition:transform .2s;display:flex;flex-direction:column;justify-content:center}}
.top-bar .b:hover{{transform:translateY(-2px)}}
.top-bar .b .bv{{font-size:1.6em;font-weight:800;color:#e8873a}}
.top-bar .b .bl{{font-size:.72em;color:#b8937a;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}}
/* Region card — same style, holds pill tabs */
.top-bar .region-card{{background:#fff;border-radius:14px;padding:10px 20px;box-shadow:0 2px 12px rgba(200,140,60,.08);border:1px solid rgba(240,180,100,.15);display:flex;align-items:center;gap:10px;transition:transform .2s}}
.top-bar .region-card:hover{{transform:translateY(-2px)}}
.region-card-label{{font-size:.72em;color:#b8937a;text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}}
.region-card .rtab{{padding:5px 13px;border:1.5px solid #e8c8a8;background:#fff;color:#8b6b4a;border-radius:16px;cursor:pointer;font-size:.78em;font-weight:600;transition:all .2s}}
.region-card .rtab:hover{{border-color:#e8873a;color:#e8873a}}
.region-card .rtab.active{{background:linear-gradient(135deg,#e8873a,#f0a050);border-color:#e8873a;color:#fff;box-shadow:0 2px 8px rgba(232,135,58,.25)}}

/* Main 2-column */
.main{{display:flex;gap:24px;align-items:flex-start}}
@media(max-width:860px){{.main{{flex-direction:column}}}}

/* Left: charts — warm golden card */
.charts{{flex:1;min-width:0;background:linear-gradient(175deg,#fffefa 0%,#fff7ed 30%,#fff3e0 100%);border-radius:14px;box-shadow:0 4px 24px rgba(200,130,40,.12),0 2px 6px rgba(255,180,60,.15),inset 0 1px 0 rgba(255,220,150,.3);border:1px solid rgba(240,180,100,.25);display:flex;flex-direction:column;max-height:calc(100vh - 40px);overflow:hidden}}
.charts-header{{padding:22px 22px 12px;flex-shrink:0;border-bottom:1px solid rgba(240,180,100,.15)}}
.charts-header h2{{font-size:1.2em;color:#b86e20;margin:0 0 14px;padding-left:8px;border-left:3px solid #f0a050}}
.charts-scroll{{flex:1;overflow-y:auto;padding:0 22px 22px}}

/* Date tabs in charts header */
.tabs{{display:flex;gap:6px;margin-bottom:0;flex-wrap:wrap}}
.dtab{{padding:6px 16px;border:1.5px solid #e8c8a8;background:#fff;color:#8b6b4a;border-radius:18px;cursor:pointer;font-size:.82em;font-weight:600;transition:all .2s}}
.dtab:hover{{border-color:#e8873a;color:#e8873a}}
.dtab.active{{background:linear-gradient(135deg,#e8873a,#f0a050);border-color:#e8873a;color:#fff;font-weight:600;box-shadow:0 2px 8px rgba(232,135,58,.25)}}
.day{{display:none}}
.day.active{{display:flex;flex-direction:column;gap:8px}}

/* Song cards — modern numbered circles */
.song{{display:flex;align-items:center;gap:8px;background:#fff;border-radius:10px;padding:10px 14px;box-shadow:0 1px 4px rgba(180,120,40,.05),0 2px 8px rgba(200,150,60,.06);border:1px solid rgba(240,180,100,.15);border-left:3px solid rgba(240,180,100,.3);transition:all .2s}}
.song:hover{{box-shadow:0 3px 12px rgba(200,140,60,.1),0 1px 4px rgba(255,180,60,.12);border-color:rgba(240,160,80,.3);border-left-color:rgba(240,160,80,.6);transform:translateY(-1px)}}
.song.r1{{border-left-color:#ff3b30;background:linear-gradient(135deg,#fff 0%,#fff6f5 50%,#fff 100%);background-size:200% 200%;animation:shimmer 3s ease-in-out infinite}}
@keyframes shimmer{{0%,100%{{background-position:0% 50%}}50%{{background-position:100% 50%}}}}
.song.r2{{border-left-color:#ff9500}}
.song.r3{{border-left-color:#ffcc00}}
.song .r{{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.85em;font-weight:900;color:#fff;flex-shrink:0;position:relative;z-index:0}}
.song .r::after{{content:'';position:absolute;inset:-3px;border-radius:50%;opacity:0;transition:opacity .4s;z-index:-1}}
.song:hover .r::after{{opacity:1;background:inherit;border-radius:50%;inset:-4px}}
.song .r.r1{{background:linear-gradient(135deg,#ff3b30,#ff6b4a);box-shadow:0 0 16px rgba(255,59,48,.45);animation:rankPulse 2s ease-in-out infinite;font-size:1em}}
.song .r.r1::after{{background:linear-gradient(135deg,#ff3b30,#ff6b4a);animation:rankGlow 2s ease-in-out infinite}}
@keyframes rankPulse{{0%,100%{{box-shadow:0 0 16px rgba(255,59,48,.45);transform:scale(1)}}50%{{box-shadow:0 0 28px rgba(255,59,48,.7);transform:scale(1.1)}}}}
@keyframes rankGlow{{0%,100%{{opacity:.3;inset:-4px}}50%{{opacity:.6;inset:-8px}}}}
.song .r.r2{{background:linear-gradient(135deg,#ff9500,#ffb340);box-shadow:0 0 10px rgba(255,149,0,.3)}}
.song .r.r3{{background:linear-gradient(135deg,#ffcc00,#ffe04d);box-shadow:0 0 8px rgba(255,204,0,.25);color:#8b6d00}}
.song .r.rx{{background:linear-gradient(135deg,#ffb899,#ffccb3);color:#8b5a3d}}
.song .art{{width:56px;height:56px;border-radius:10px;object-fit:cover;flex-shrink:0;box-shadow:0 2px 8px rgba(0,0,0,.12)}}
.song .meta{{flex:1;min-width:0;display:flex;flex-direction:column;gap:1px}}
.song .sn{{font-weight:800;font-size:.95em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.2px;color:#3d2b1f}}
.song .sa{{font-size:.82em;color:#b8937a;font-weight:500}}
.song .tags{{display:flex;gap:5px;flex-shrink:0;flex-wrap:wrap;max-width:150px}}
.song .tag{{font-size:.68em;padding:3px 9px;border-radius:10px;font-weight:600;letter-spacing:.3px;white-space:nowrap;background:rgba(240,160,80,.1);color:#b86e20;border:1px solid rgba(240,160,80,.15)}}
.song .tag.am{{background:rgba(255,45,85,.08);color:#e8345b;border:1px solid rgba(255,45,85,.12)}}
.song .tag.am a{{color:inherit;text-decoration:none}}
.song .mv-wrap{{display:flex;flex-direction:column;gap:2px;flex-shrink:0}}
.song .mv{{width:320px;position:relative;padding-bottom:56.25%;height:0;border-radius:6px;overflow:hidden;background:#faf5f0}}
.song .mv-overlay,.tv .mv-overlay{{position:absolute;inset:0;z-index:2;display:flex;align-items:center;justify-content:center;cursor:pointer;background:rgba(0,0,0,0);transition:background .3s}}
.song .mv-overlay:hover,.tv .mv-overlay:hover{{background:rgba(0,0,0,.35)}}
.song .mv-overlay .play-btn,.tv .mv-overlay .play-btn{{opacity:0;transform:scale(.8);transition:all .3s;background:rgba(255,255,255,.92);color:#e8873a;width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.4em;box-shadow:0 4px 20px rgba(0,0,0,.3)}}
.song .mv-overlay:hover .play-btn,.tv .mv-overlay:hover .play-btn{{opacity:1;transform:scale(1)}}
@media(max-width:860px){{.song .mv{{width:160px}}.song .tags{{display:none}}}}
.song .mv iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none}}
.song .mv .ytlink{{display:flex;align-items:center;justify-content:center;height:100%;color:#e8873a;text-decoration:none;font-size:.75em;font-weight:500}}
.song .mv-ext{{font-size:.63em;text-align:right;display:flex;align-items:center;gap:8px;justify-content:flex-end}}
.song .mv-ext a{{color:#c4a080;text-decoration:none;font-weight:500;transition:color .2s}}
.song .mv-ext a:hover{{color:#e8873a}}
.mv-popout{{cursor:pointer;color:#c4a080;font-size:.85em;transition:color .2s;border:none;background:none;padding:0}}
.mv-popout:hover{{color:#e8873a}}

/* Video popout modal */
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;justify-content:center;align-items:center}}
.modal-overlay.show{{display:flex}}
.modal-box{{position:relative;width:85vw;max-width:1100px;border-radius:12px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.5)}}
.modal-box .modal-close{{position:absolute;top:12px;right:16px;z-index:10;background:rgba(0,0,0,.6);color:#fff;border:none;font-size:1.4em;width:36px;height:36px;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s}}
.modal-box .modal-close:hover{{background:rgba(255,45,48,.8)}}
.modal-box .modal-vid{{position:relative;padding-bottom:56.25%;height:0}}

/* Regional pulse */
.pulse{{margin-top:12px;padding-top:10px;border-top:1px dashed rgba(240,180,100,.2)}}
.pulse-label{{font-size:.72em;font-weight:700;color:#b8937a;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.pulse-row{{display:flex;gap:8px;flex-wrap:wrap}}
.pulse-card{{display:flex;align-items:center;gap:6px;background:linear-gradient(135deg,#fffdf7,#fff9ef);border-radius:8px;padding:8px 10px;border:1px solid rgba(240,180,100,.12);flex:1;min-width:130px;transition:all .2s;text-decoration:none;color:inherit}}
.pulse-card:hover{{box-shadow:0 1px 6px rgba(200,140,60,.08);border-color:rgba(240,160,80,.25)}}
.pf{{font-size:1em;flex-shrink:0}}
.pa{{width:28px;height:28px;border-radius:6px;object-fit:cover;flex-shrink:0}}
.pm{{min-width:0}}
.pm-s{{font-size:.72em;font-weight:700;color:#5c3d2e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.pm-a{{font-size:.65em;color:#b8937a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}

/* Right: tutorials — rose card */
.tutorials{{width:360px;flex-shrink:0;background:linear-gradient(175deg,#fff5f5 0%,#fff0f0 30%,#ffebee 100%);border-radius:14px;padding:22px;box-shadow:0 4px 24px rgba(180,100,100,.12),0 2px 6px rgba(220,140,140,.12),inset 0 1px 0 rgba(255,200,200,.25);border:1px solid rgba(220,150,150,.2);position:sticky;top:16px;max-height:calc(100vh - 32px);overflow-y:auto}}
@media(max-width:860px){{.tutorials{{width:100%;max-height:none;position:static}}}}
.tutorials h2{{font-size:1.2em;color:#c0392b;margin-bottom:16px;padding-left:8px;border-left:3px solid #e74c3c}}
.tcat{{font-size:.82em;font-weight:800;color:#c0392b;margin:14px 0 6px;text-transform:uppercase;letter-spacing:.8px;font-family:'Helvetica Neue',-apple-system,sans-serif}}
.tcard{{margin-bottom:10px;border-radius:10px;overflow:hidden;background:#fffbfb;border:1px solid rgba(220,150,150,.15);transition:all .2s}}
.tcard:hover{{box-shadow:0 2px 10px rgba(180,100,100,.12)}}
.tcard .tv{{position:relative;padding-bottom:56.25%;height:0}}
.tcard .tv iframe{{position:absolute;top:0;left:0;width:100%;height:100%;border:none}}
.tcard .tt{{padding:6px 10px 2px;font-size:.78em;font-weight:600;color:#5c3d2e;line-height:1.3}}
.tcard .tlink{{display:block;padding:0 10px 8px;font-size:.7em;color:#c0392b;text-decoration:none;font-weight:500;transition:color .2s}}
.tcard .tlink:hover{{color:#e74c3c}}

footer{{text-align:center;padding:28px;color:#c4a080;font-size:.78em;margin-top:24px;border-top:1px solid #f0d8c0}}
footer a{{color:#e8873a;text-decoration:none}}
</style>
</head>
<body>
<div class="bg">
  <div class="s s1"></div><div class="s s2"></div><div class="s s3"></div>
  <div class="s s4"></div><div class="s s5"></div><div class="s s6"></div>
  <div class="s s7"></div><div class="s s8"></div>
</div>
<div class="wrap">
<header>
  <h1><span class="t1">Sync</span><span class="ico">🎵</span><span class="t2">roony</span></h1>
  <p class="sub">Daily Music Trends · Top 5 Hits · Singing Tutorials</p>
</header>
<div class="top-bar">
  <div class="b"><div class="bv">{d["stats"]["total_days"]}</div><div class="bl">Days Tracked</div></div>
  <div class="b"><div class="bv">{d["stats"]["total_songs"]}</div><div class="bl">Unique Songs</div></div>
  <div class="region-card">
    <span class="region-card-label">Region</span>
    {region_tabs}
  </div>
</div>
<div class="main">
  <div class="charts">
    <div class="charts-header">
      <h2>📊 Top 5 Charts</h2>
      <div class="tabs">{date_tabs}</div>
    </div>
    <div class="charts-scroll">{panels}</div>
  </div>
  <div class="tutorials">
    <h2>🎤 Singing Skills</h2>
    {tuts}
  </div>
</div>
<footer>
  <p>Powered by Apple Music & YouTube · Curated by Rinちゃん ✨ · {d["updated"]}</p>
</footer>
</div>
<div class="modal-overlay" id="modal">
  <div class="modal-box">
    <button class="modal-close" id="modalClose">✕</button>
    <div class="modal-vid" id="modalVid"></div>
  </div>
</div>
<script>
// Region + date tab switching
let curRegion='global',curDate='{dates[0]}';
function refresh(){{
  document.querySelectorAll('.day').forEach(d=>d.classList.remove('active'));
  var t=document.querySelector('.day[data-region="'+curRegion+'"][data-date="'+curDate+'"]');
  if(t)t.classList.add('active');
}}
refresh();
document.querySelectorAll('.rtab').forEach(function(t){{t.addEventListener('click',function(){{
  document.querySelectorAll('.rtab').forEach(function(x){{x.classList.remove('active');}});
  this.classList.add('active');curRegion=this.dataset.region;refresh();
}});}});
document.querySelectorAll('.dtab').forEach(function(t){{t.addEventListener('click',function(){{
  document.querySelectorAll('.dtab').forEach(function(x){{x.classList.remove('active');}});
  this.classList.add('active');curDate=this.dataset.date;refresh();
}});}});

// Single-play: pause others when clicking overlay
var allVidFrames=[];
function collectVidFrames(){{allVidFrames=document.querySelectorAll('.mv iframe[data-vid]');}}
collectVidFrames();setInterval(collectVidFrames,3000);
function pauseAllOthers(excludeFrame){{
  allVidFrames.forEach(function(f){{
    if(f!==excludeFrame&&f.contentWindow){{f.contentWindow.postMessage('{{"event":"command","func":"pauseVideo","args":[]}}','*');}}
  }});
}}
document.addEventListener('click',function(e){{
  var ov=e.target.closest('.mv-overlay');
  if(ov){{
    e.preventDefault();e.stopPropagation();
    var vid=ov.dataset.vid;
    var iframe=ov.parentElement.querySelector('iframe');
    // Pause all others first
    pauseAllOthers(iframe);
    // Open modal
    document.getElementById('modalVid').innerHTML='<iframe src="https://www.youtube.com/embed/'+vid+'?autoplay=1&enablejsapi=1" allowfullscreen allow="autoplay" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none"></iframe>';
    document.getElementById('modal').classList.add('show');
  }}
}});

// Modal close handlers
document.getElementById('modalClose').addEventListener('click',function(){{document.getElementById('modalVid').innerHTML='';document.getElementById('modal').classList.remove('show');}});
document.getElementById('modal').addEventListener('click',function(e){{if(e.target===this){{document.getElementById('modalVid').innerHTML='';this.classList.remove('show');}}}});
document.addEventListener('keydown',function(e){{if(e.key==='Escape'){{document.getElementById('modalVid').innerHTML='';document.getElementById('modal').classList.remove('show');}}}});
</script>
</body>
</html>'''
    with open(os.path.join(SITE_DIR, "index.html"), "w") as f:
        f.write(html)
    print(f"✅ {len(dates)} days · {d['stats']['total_songs']} songs · {len(d['tutorials'])} tutorials")

if __name__ == "__main__":
    build()

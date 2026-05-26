#!/bin/bash
# Syncroony daily pipeline — run via cron
cd /Users/yilin/.openclaw/workspace/syncroony
echo "🎵 Syncroony Daily Pipeline — $(date '+%Y-%m-%d %H:%M SGT')"
python3 scraper.py && python3 generate_site.py && echo "✅ Pipeline complete"

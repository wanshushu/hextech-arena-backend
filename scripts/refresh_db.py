#!/usr/bin/env python3
"""
Local database refresh script
Run this periodically to update the database, then push to GitHub to trigger Railway redeploy.
"""
import asyncio
import sys
from pathlib import Path

# Add parent dir to path so we can import backend
sys.path.insert(0, str(Path(__file__).parent))

from backend.main import refresh_cache, _refresh_ddragon


async def main():
    print("🔄 Starting database refresh...")
    print()

    # 1. Data Dragon 数据（快速，~10秒）
    print("📦 [1/2] Fetching Data Dragon data (champions/items/runes)...")
    await _refresh_ddragon()
    print("   ✅ Data Dragon done!")
    print()

    # 2. aramgg 爬虫数据（较慢，~5-10分钟）
    print("🕷️  [2/2] Scraping aram.gg for ARAM stats...")
    print("   This takes ~5-10 minutes.")
    await refresh_cache()
    print("   ✅ aram.gg done!")
    print()

    print("🎉 All data updated!")
    print("   Commit and push to trigger Railway redeploy:")
    print("   git add backend/hextech.db")
    print("   git commit -m 'Update database'")
    print("   git push origin main")


if __name__ == "__main__":
    asyncio.run(main())

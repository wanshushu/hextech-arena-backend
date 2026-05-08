"""
HexTech Arena Backend — FastAPI + Playwright scraper for aramgg.com
实时爬取英雄联盟海克斯大乱斗数据
"""
import asyncio
import logging
import math
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .database import (
    init_db,
    upsert_champion,
    upsert_augments,
    upsert_items,
    get_all_champions,
    get_champion_by_id,
    get_tier_list as db_get_tier_list,
    get_champion_count,
    log_refresh,
    get_last_refresh,
    set_meta,
    get_meta,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HexTech Arena API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ─── HTTP helpers ─────────────────────────────────────────────────────────────
async def fetch_html(url: str, use_playwright: bool = False) -> str:
    if use_playwright:
        return await _fetch_playwright(url)

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.warning(f"httpx failed ({e}), trying Playwright")
        return await _fetch_playwright(url)


async def _fetch_playwright(url: str, is_detail: bool = False) -> str:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        try:
            # For detail pages, wait for the specific content to appear
            await page.wait_for_selector("h1", timeout=15000)
        except Exception:
            pass
        html = await page.content()
        await browser.close()
        return html


# ─── HTML parsing helpers ────────────────────────────────────────────────────
def clean_html_text(html: str) -> str:
    return re.sub(r'<[^>]+>', '', html).strip()


def extract_text_after(html: str, pattern: str, length: int = 3000, occurrence: int = 1) -> str:
    """Extract text chunk after pattern's nth occurrence (1-indexed)."""
    m = re.search(re.escape(pattern), html)
    if not m:
        return ""
    # Find the nth occurrence
    idx = m.start()
    for _ in range(occurrence - 1):
        next_m = re.search(re.escape(pattern), html[idx + 1:])
        if not next_m:
            return ""
        idx = idx + 1 + next_m.start()
    return html[idx:idx + length]


def extract_items_from_chunk(chunk: str) -> List[str]:
    """Extract item names from HTML chunk by parsing img alt attributes."""
    alts = re.findall(r'alt="([^"]{2,60})"', chunk)
    seen = set()
    unique = []
    for alt in alts:
        alt = alt.strip()
        # Filter out: "图标" keyword, URLs, empty, very short, and common non-item patterns
        if not alt:
            continue
        if alt.startswith("http"):
            continue
        if "图标" in alt:
            continue
        if len(alt) < 2:
            continue
        # Skip champion names (usually 2-4 Chinese chars, will be deduplicated later)
        if alt in seen:
            continue
        seen.add(alt)
        unique.append(alt)
    return unique


# ─── Scraping ─────────────────────────────────────────────────────────────────
async def scrape_tier_list() -> Dict[str, List[Dict]]:
    logger.info("Scraping tier list...")
    url = "https://aramgg.com/zh-CN"
    html = await fetch_html(url, use_playwright=True)

    tiers: Dict[str, List[Dict]] = {"T1": [], "T2": [], "T3": [], "T4": [], "T5": []}

    row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
    for row in row_pattern.finditer(html):
        row_html = row.group()

        # Extract champion id from /zh-CN/champion-stats/{id}
        id_m = re.search(r'/zh-CN/champion-stats/(\d+)"', row_html)
        if not id_m:
            continue
        champ_id = id_m.group(1)

        # Extract champion name - from the span with class "text-sm font-medium"
        name_m = re.search(r'class="text-sm font-medium[^"]*"[^>]*>([^<]{2,20})</span>', row_html)
        champ_name = name_m.group(1).strip() if name_m else ""

        # Extract tier - handle HTML entity: T<!-- -->1
        tier_m = re.search(r'T<!-- -->([1-5])', row_html)
        if not tier_m:
            continue
        tier = "T" + tier_m.group(1)

        # Extract winrate - green stat-value
        wr_m = re.search(r'class="stat-value[^"]*"[^>]*>(\d+\.\d+)%', row_html)
        if not wr_m:
            wr_m = re.search(r'(\d+\.\d+)%</span>', row_html)
        wr = (wr_m.group(1) + "%") if wr_m else ""

        # Extract pickrate
        pr_m = re.search(r'class="hidden lg:table-cell[^>]*>.*?(\d+\.\d+)%', row_html, re.DOTALL)
        pr = (pr_m.group(1) + "%") if pr_m else ""

        if champ_name and tier:
            tiers[tier].append({
                "id": champ_id,
                "name": champ_name,
                "tier": tier,
                "winrate": wr,
                "pickrate": pr,
            })

    # Deduplicate by id
    for tier in tiers:
        seen = set()
        unique = []
        for c in tiers[tier]:
            if c["id"] not in seen:
                seen.add(c["id"])
                unique.append(c)
        tiers[tier] = unique

    logger.info(f"T1={len(tiers['T1'])} T2={len(tiers['T2'])} T3={len(tiers['T3'])} "
                f"T4={len(tiers['T4'])} T5={len(tiers['T5'])}")
    return tiers


async def scrape_champion_detail(champ_id: str) -> Optional[Dict]:
    url = f"https://aramgg.com/zh-CN/champion-stats/{champ_id}"
    logger.info(f"Scraping champion {champ_id}")
    html = await fetch_html(url, use_playwright=True)

    h1_m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if not h1_m:
        return None
    parts = h1_m.group(1).strip().split()
    name = parts[-1] if parts else ""
    title = " ".join(parts[:-1]) if len(parts) > 1 else ""

    patch_m = re.search(r'版本[:\s]*([\d.]+)', html)
    patch = patch_m.group(1) if patch_m else ""

    tier_m = re.search(r'T<!-- -->([1-5])', html)
    if not tier_m:
        tier_m = re.search(r'\b(T[1-5])\b', html)
    tier = ("T" + tier_m.group(1)) if tier_m else ""

    wr_m = re.search(r'class="stat-value[^"]*"[^>]*>(\d+\.\d+)%', html)
    if not wr_m:
        wr_m = re.search(r'>(\d+\.\d+)%<', html)
    wr = (wr_m.group(1) + "%") if wr_m else ""

    pr_m = re.search(r'选取率[^>]*>([^<]+)<', html)
    if not pr_m:
        pr_m = re.search(r'pickrate[^>]*>([^<]+)<', html)
    pr = pr_m.group(1).strip() if pr_m else ""

    # Parse augments table
    augments: List[Dict] = []
    table_m = re.search(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    if table_m:
        table_html = table_m.group(1)
        row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        for row_html in row_matches[:12]:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
            if len(cells) >= 4:
                name_text = clean_html_text(cells[1])
                tier_text = clean_html_text(cells[2])
                wr_text = clean_html_text(cells[3])
                pr_text = clean_html_text(cells[4]) if len(cells) > 4 else ""
                if name_text and len(name_text) > 1:
                    augments.append({
                        "name": name_text,
                        "tier": tier_text,
                        "winrate": wr_text,
                        "pickrate": pr_text,
                    })

    # Parse items - second occurrence of each section (first is in JSON-LD structured data)
    core_items = extract_items_from_chunk(extract_text_after(html, "核心装备", 6000, 2))
    situ_items = extract_items_from_chunk(extract_text_after(html, "情境装备", 6000, 2))
    start_items = extract_items_from_chunk(extract_text_after(html, "出门装", 4000, 2))

    return {
        "id": champ_id,
        "name": name,
        "title": title,
        "patch": patch,
        "tier": tier,
        "winrate": wr,
        "pickrate": pr,
        "top_augments": augments,
        "core_items": core_items,
        "situational_items": situ_items,
        "starting_items": start_items,
    }


async def refresh_cache():
    """Refresh full database cache"""
    logger.info("Starting full cache refresh...")

    try:
        tier_list = await scrape_tier_list()
        log_refresh("running", f"T1:{len(tier_list['T1'])} T2:{len(tier_list['T2'])}")

        champions_crawled = 0
        all_ids = [c["id"] for tier in tier_list.values() for c in tier]

        for cid in all_ids:
            detail = await scrape_champion_detail(cid)
            if detail:
                upsert_champion(detail)
                upsert_augments(detail["id"], detail.get("top_augments", []))
                upsert_items(detail["id"], "core", detail.get("core_items", []))
                upsert_items(detail["id"], "situational", detail.get("situational_items", []))
                upsert_items(detail["id"], "starting", detail.get("starting_items", []))
                champions_crawled += 1
            await asyncio.sleep(0.3)

        set_meta("last_refresh", datetime.now().isoformat())
        log_refresh("completed", f"T1:{len(tier_list['T1'])}", champions_crawled)
        logger.info(f"Cache refresh completed: {champions_crawled} champions")

    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        log_refresh("failed", str(e))


# ─── Startup ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(refresh_cache())


# ─── API Routes ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "HexTech Arena API", "version": "1.0.0", "status": "ok"}


@app.get("/health")
async def health():
    last = get_last_refresh()
    return {
        "status": "ok",
        "last_refresh": last,
        "champion_count": get_champion_count(),
        "tier_counts": {t: len(db_get_tier_list()[t]) for t in ["T1", "T2", "T3", "T4", "T5"]},
    }


@app.get("/tier-list")
async def get_tier_list_api():
    return {
        "updated_at": get_meta("last_refresh") or "",
        "tiers": db_get_tier_list(),
    }


@app.get("/champions")
async def get_champions_api(
    tier: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    champions = get_all_champions(tier=tier, search=search, limit=page_size, offset=offset)
    total = get_champion_count(tier=tier, search=search)
    return {
        "champions": champions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@app.get("/champions/{champ_id}")
async def get_champion_api(champ_id: str):
    champion = get_champion_by_id(champ_id)
    if not champion:
        raise HTTPException(status_code=404, detail=f"Champion {champ_id} not found")
    return champion


@app.post("/refresh")
async def force_refresh():
    asyncio.create_task(refresh_cache())
    return {"message": "Refresh started"}

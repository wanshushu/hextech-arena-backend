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
    upsert_global_augments,
    get_all_augment_names,
    # Data Dragon
    set_ddragon_meta,
    get_ddragon_meta,
    upsert_ddragon_champions,
    upsert_ddragon_items,
    upsert_ddragon_runes,
    get_ddragon_champions,
    get_ddragon_champion_by_key,
    get_ddragon_champion_by_id,
    get_ddragon_items,
    get_ddragon_item_by_id,
    get_ddragon_runes,
    get_ddragon_runes_by_tree,
)
from . import ddragon
from .riot_api import RiotAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Riot API 配置（优先读环境变量，否则用默认值）
RIOT_API_KEY = os.environ.get("RIOT_API_KEY", "RGAPI-5de719fd-c7b0-490f-8b9a-34c66b58467f")
RIOT_REGION = os.environ.get("RIOT_REGION", "asia")
RIOT_PLATFORM = os.environ.get("RIOT_PLATFORM", "kr")

riot_client: Optional[RiotAPI] = None


def get_riot_client() -> RiotAPI:
    global riot_client
    if riot_client is None:
        riot_client = RiotAPI(
            api_key=RIOT_API_KEY,
            region=RIOT_REGION,
            platform=RIOT_PLATFORM,
        )
    return riot_client

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
    """Fetch HTML page. Uses httpx by default. Set use_playwright=true to force Playwright (not recommended on Railway)."""
    # Try httpx first (works on all platforms)
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.warning(f"httpx failed: {e}")
        # Fall back to Playwright only if explicitly requested and not on Railway
        if use_playwright:
            try:
                return await _fetch_playwright(url)
            except Exception as pw_err:
                logger.error(f"Playwright also failed: {pw_err}")
        raise


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
        # Filter out non-item patterns
        if not alt:
            continue
        if alt.startswith("http"):
            continue
        if "图标" in alt:
            continue
        if len(alt) < 2:
            continue
        # Skip champion names (contain spaces, e.g., "北地之怒 瑟庄妮")
        if " " in alt:
            continue
        # Skip augments (contain "强化" or "海克斯")
        if "强化" in alt or "海克斯" in alt:
            continue
        if alt in seen:
            continue
        seen.add(alt)
        unique.append(alt)
    return unique


async def scrape_global_augments() -> List[str]:
    """Scrape the global augments ranking page to get all unique augment names."""
    logger.info("Scraping global augments ranking...")
    url = "https://aramgg.com/zh-CN/augments"
    html = await fetch_html(url, use_playwright=False)

    seen = set()
    augment_names = []

    # Find img tags and check their surrounding context for augment keywords
    img_pattern = re.compile(r'<img[^>]*alt=\"([^\"]{2,30})\"[^>]*>', re.DOTALL)
    for m in img_pattern.finditer(html):
        alt = m.group(1).strip()
        start = max(0, m.start() - 100)
        end = min(len(html), m.end() + 100)
        context = html[start:end].lower()

        # Only include if in augment context
        if not any(kw in context for kw in ['强化', 'augment', '海克斯']):
            continue
        if not alt or len(alt) < 2:
            continue
        if alt.startswith("http"):
            continue
        if "图标" in alt:
            continue
        if alt in seen:
            continue
        seen.add(alt)
        augment_names.append(alt)

    logger.info(f"Found {len(augment_names)} global augments")
    return augment_names


# ─── Scraping ─────────────────────────────────────────────────────────────────
async def scrape_tier_list() -> Dict[str, List[Dict]]:
    logger.info("Scraping tier list...")
    url = "https://aramgg.com/zh-CN"
    html = await fetch_html(url, use_playwright=False)

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
    html = await fetch_html(url, use_playwright=False)

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
    import os
    from backend.database import DATABASE_PATH
    logger.info(f"Database path: {DATABASE_PATH}")
    logger.info(f"Database exists: {os.path.exists(DATABASE_PATH)}")
    if os.path.exists(DATABASE_PATH):
        logger.info(f"Database size: {os.path.getsize(DATABASE_PATH)} bytes")
    init_db()
    logger.info("API ready. Data loaded from database.")


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


# ─── Data Dragon API ───────────────────────────────────────────────────────

@app.get("/ddragon/version")
async def ddragon_version():
    """当前 Data Dragon 数据版本"""
    version = get_ddragon_meta("ddragon_version")
    updated = get_ddragon_meta("ddragon_updated_at")
    return {"version": version, "updated_at": updated}


@app.get("/ddragon/champions")
async def ddragon_champions_list():
    """所有英雄基础数据（来自 Data Dragon）"""
    champions = get_ddragon_champions()
    if not champions:
        raise HTTPException(status_code=404, detail="Data Dragon data not loaded. Run refresh first.")
    return {"champions": champions, "total": len(champions)}


@app.get("/ddragon/champions/{key}")
async def ddragon_champion_detail(key: str):
    """单个英雄详情，合并 aramgg 统计数据 + Data Dragon 基础数据"""
    # 先查 aramgg 统计数据（通过 key 匹配 id）
    ddragon_champ = get_ddragon_champion_by_key(key)
    if not ddragon_champ:
        raise HTTPException(status_code=404, detail=f"Champion key {key} not found in Data Dragon")

    # 用 ddragon 的 key（数字）去查 aramgg 数据，因为 aramgg 用数字 id
    aramgg_champ = get_champion_by_id(key)

    result = {
        "key": key,
        "id": ddragon_champ["id"],
        "name": ddragon_champ["name"],
        "title": ddragon_champ["title"],
        "tags": ddragon_champ.get("tags", []),
        "stats": ddragon_champ.get("stats", {}),
        "spells": ddragon_champ.get("spells", []),
        "passive": ddragon_champ.get("passive", {}),
        "images": {
            "icon": ddragon_champ.get("image_url", ""),
            "loading": ddragon_champ.get("image_loading", ""),
            "splash": ddragon_champ.get("image_splash", ""),
        },
    }

    if aramgg_champ:
        result["tier"] = aramgg_champ.get("tier", "")
        result["winrate"] = aramgg_champ.get("winrate", "")
        result["pickrate"] = aramgg_champ.get("pickrate", "")
        result["top_augments"] = aramgg_champ.get("top_augments", [])
        result["all_augments"] = aramgg_champ.get("all_augments", [])
        result["core_items"] = aramgg_champ.get("core_items", [])
        result["situational_items"] = aramgg_champ.get("situational_items", [])
        result["starting_items"] = aramgg_champ.get("starting_items", [])
    else:
        result["tier"] = ""
        result["winrate"] = ""
        result["pickrate"] = ""

    return result


@app.get("/ddragon/items")
async def ddragon_items_list(search: Optional[str] = Query(None)):
    """装备数据（来自 Data Dragon）"""
    items = get_ddragon_items()
    if search:
        items = [i for i in items if search.lower() in i["name"].lower()]
    return {"items": items, "total": len(items)}


@app.get("/ddragon/items/{item_id}")
async def ddragon_item_detail(item_id: str):
    """单个装备详情"""
    item = get_ddragon_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@app.get("/ddragon/runes")
async def ddragon_runes_list():
    """符文树数据"""
    runes = get_ddragon_runes()
    if not runes:
        raise HTTPException(status_code=404, detail="Rune data not loaded.")

    # 按符文树分组
    trees = {}
    for r in runes:
        tid = r["tree_id"]
        if tid not in trees:
            trees[tid] = {
                "tree_id": tid,
                "tree_name": r["tree_name"],
                "tree_icon": r["tree_icon"],
                "slots": {},
            }
        si = r["slot_index"]
        if si not in trees[tid]["slots"]:
            trees[tid]["slots"][si] = []
        trees[tid]["slots"][si].append({
            "id": r["id"],
            "name": r["name"],
            "icon_url": r["icon_url"],
            "short_desc": r["short_desc"],
        })

    # 转换 slots 为列表
    result = []
    for tid, tree in sorted(trees.items()):
        tree["slots"] = [tree["slots"][k] for k in sorted(tree["slots"].keys())]
        result.append(tree)

    return {"trees": result, "total": len(result)}


@app.post("/ddragon/refresh")
async def ddragon_refresh():
    """触发 Data Dragon 数据更新"""
    asyncio.create_task(_refresh_ddragon())
    return {"message": "Data Dragon refresh started"}


async def _refresh_ddragon():
    """后台任务：拉取 Data Dragon 数据"""
    try:
        logger.info("Starting Data Dragon refresh...")
        version = await ddragon.fetch_latest_version()
        logger.info(f"Latest Data Dragon version: {version}")

        # 英雄
        champions = await ddragon.fetch_champions(version)
        upsert_ddragon_champions(champions)

        # 装备
        items = await ddragon.fetch_items(version)
        upsert_ddragon_items(items)

        # 符文
        runes = await ddragon.fetch_runes(version)
        upsert_ddragon_runes(runes)

        # 更新元数据
        set_ddragon_meta("ddragon_version", version)
        set_ddragon_meta("ddragon_updated_at", datetime.now().isoformat())

        logger.info(f"Data Dragon refresh completed: {len(champions)} champions, {len(items)} items, {len(runes)} rune entries")
    except Exception as e:
        logger.error(f"Data Dragon refresh failed: {e}")


# ─── Riot API ──────────────────────────────────────────────────────────────

@app.get("/riot/status")
async def riot_status():
    """检查 Riot API Key 状态"""
    try:
        client = get_riot_client()
        # 测试一个简单请求
        account = await client.get_summoner_by_name("Hide on bush", "KR1")
        return {
            "status": "ok",
            "region": RIOT_REGION,
            "platform": RIOT_PLATFORM,
            "key_prefix": RIOT_API_KEY[:10] + "...",
            "test_result": "ok" if account else "no_test_account",
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/riot/summoner/{name}/{tag}")
async def riot_summoner(name: str, tag: str = "KR1"):
    """
    查询召唤师信息
    示例: /riot/summoner/Hide on bush/KR1
    """
    client = get_riot_client()
    try:
        account = await client.get_summoner_by_name(name, tag)
        if not account:
            raise HTTPException(status_code=404, detail=f"Summoner {name}#{tag} not found")

        summoner = await client.get_summoner_by_puuid(account["puuid"])
        if not summoner:
            raise HTTPException(status_code=404, detail="Summoner details not found")

        # 获取英雄熟练度 Top 5
        mastery = await client.get_champion_mastery(account["puuid"], count=5)

        # 将 champion_id 映射到名字
        ddragon_champs = get_ddragon_champions()
        id_to_name = {c["key"]: c["name"] for c in ddragon_champs}
        for m in mastery:
            m["champion_name"] = id_to_name.get(m["champion_id"], f"Unknown({m['champion_id']})")

        return {
            "account": account,
            "summoner": summoner,
            "top_mastery": mastery,
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/riot/live-game/{name}/{tag}")
async def riot_live_game(name: str, tag: str = "KR1"):
    """
    实时对局查询（核心功能！）
    输入召唤师名#标签，返回当前对局10个人的英雄攻略

    小程序用法：
    1. 用户输入 "Hide on bush#KR1"
    2. 返回当前 ARAM 对局中 10 个英雄的梯度、出装、海克斯推荐
    3. 用户在开局前快速查看攻略
    """
    client = get_riot_client()
    try:
        # 1. 查召唤师
        account = await client.get_summoner_by_name(name, tag)
        if not account:
            raise HTTPException(status_code=404, detail=f"Summoner {name}#{tag} not found")

        # 2. 查当前对局
        game = await client.get_current_game(account["puuid"])
        if not game:
            return {
                "status": "not_in_game",
                "summoner": name,
                "message": f"{name} 当前不在对局中",
            }

        # 3. 为每个参与者补充英雄攻略数据
        ddragon_champs = {c["key"]: c for c in get_ddragon_champions()}
        enriched_participants = []

        for p in game["participants"]:
            champ_key = p["champion_id"]
            dd_champ = ddragon_champs.get(champ_key, {})
            aramgg_champ = get_champion_by_id(champ_key) or {}

            enriched_participants.append({
                "summoner_name": p["summoner_name"],
                "team_id": p["team_id"],
                "champion": {
                    "key": champ_key,
                    "id": dd_champ.get("id", ""),
                    "name": dd_champ.get("name", f"未知({champ_key})"),
                    "title": dd_champ.get("title", ""),
                    "image": dd_champ.get("image_url", ""),
                    "tags": dd_champ.get("tags", []),
                },
                "aram": {
                    "tier": aramgg_champ.get("tier", ""),
                    "winrate": aramgg_champ.get("winrate", ""),
                    "pickrate": aramgg_champ.get("pickrate", ""),
                    "top_augments": aramgg_champ.get("top_augments", [])[:3],
                    "core_items": aramgg_champ.get("core_items", []),
                    "situational_items": aramgg_champ.get("situational_items", []),
                },
            })

        return {
            "status": "in_game",
            "game_mode": game["game_mode"],
            "game_id": game["game_id"],
            "participants": enriched_participants,
        }

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))


@app.get("/riot/match-history/{name}/{tag}")
async def riot_match_history(name: str, tag: str = "KR1", count: int = Query(5, ge=1, le=20)):
    """
    对局历史查询
    返回最近 N 场 ARAM 对局的详情
    """
    client = get_riot_client()
    try:
        account = await client.get_summoner_by_name(name, tag)
        if not account:
            raise HTTPException(status_code=404, detail=f"Summoner {name}#{tag} not found")

        match_ids = await client.get_match_ids(account["puuid"], count=count, queue_id=450)
        if not match_ids:
            return {"matches": [], "total": 0}

        matches = []
        for mid in match_ids[:count]:
            detail = await client.get_match_detail(mid)
            if detail:
                matches.append(detail)

        return {"matches": matches, "total": len(matches)}

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

"""
Riot Data Dragon 数据拉取模块
免费 CDN，无需 API Key，提供英雄/装备/符文/图片数据
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

DD_BASE = "https://ddragon.leagueoflegends.com"


# ─── 版本管理 ────────────────────────────────────────────────────────────────

async def fetch_latest_version() -> str:
    """获取最新游戏版本号"""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{DD_BASE}/api/versions.json")
        resp.raise_for_status()
        versions = resp.json()
        return versions[0]


# ─── 英雄数据 ────────────────────────────────────────────────────────────────

async def fetch_champions(version: str, lang: str = "zh_CN") -> Dict[str, Any]:
    """
    拉取所有英雄基础数据
    返回 {champion_key: {id, key, name, title, tags, stats, spells, passive, image_url}}
    """
    url = f"{DD_BASE}/cdn/{version}/data/{lang}/championFull.json"
    logger.info(f"Fetching champions from {url}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.json()

    champions = {}
    for champ_id, champ in raw["data"].items():
        spells = []
        for s in champ.get("spells", []):
            spells.append({
                "name": s["name"],
                "description": _strip_html(s.get("description", "")),
                "tooltip": _strip_html(s.get("tooltip", "")),
                "image": f"{DD_BASE}/cdn/{version}/img/spell/{s['image']['full']}",
            })

        passive = champ.get("passive", {})
        passive_data = {
            "name": passive.get("name", ""),
            "description": _strip_html(passive.get("description", "")),
            "image": f"{DD_BASE}/cdn/{version}/img/passive/{passive['image']['full']}" if passive.get("image") else "",
        }

        champions[champ["key"]] = {
            "id": champ_id,
            "key": champ["key"],
            "name": champ["name"],
            "title": champ["title"],
            "tags": champ.get("tags", []),
            "partype": champ.get("partype", ""),
            "stats": champ.get("stats", {}),
            "spells": spells,
            "passive": passive_data,
            "image_url": f"{DD_BASE}/cdn/{version}/img/champion/{champ_id}.png",
            "image_loading": f"{DD_BASE}/cdn/img/champion/loading/{champ_id}_0.jpg",
            "image_splash": f"{DD_BASE}/cdn/img/champion/splash/{champ_id}_0.jpg",
        }

    logger.info(f"Fetched {len(champions)} champions")
    return champions


# ─── 装备数据 ────────────────────────────────────────────────────────────────

async def fetch_items(version: str, lang: str = "zh_CN") -> Dict[str, Any]:
    """
    拉取所有装备数据
    返回 {item_id: {name, description, gold, tags, stats, into, from, image_url}}
    """
    url = f"{DD_BASE}/cdn/{version}/data/{lang}/item.json"
    logger.info(f"Fetching items from {url}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.json()

    items = {}
    for item_id, item in raw["data"].items():
        gold = item.get("gold", {})
        stats = item.get("stats", {})
        # 过滤掉没有实际购买价值的物品
        if not gold.get("purchasable", False) and gold.get("total", 0) == 0:
            continue

        items[item_id] = {
            "id": item_id,
            "name": item.get("name", ""),
            "description": _strip_html(item.get("description", "")),
            "plaintext": item.get("plaintext", ""),
            "gold_total": gold.get("total", 0),
            "gold_base": gold.get("base", 0),
            "gold_sell": gold.get("sell", 0),
            "tags": item.get("tags", []),
            "maps": item.get("maps", {}),
            "stats": _extract_stats(stats),
            "into": item.get("into", []),
            "from": item.get("from", []),
            "image_url": f"{DD_BASE}/cdn/{version}/img/item/{item_id}.png",
        }

    logger.info(f"Fetched {len(items)} items")
    return items


# ─── 符文数据 ────────────────────────────────────────────────────────────────

async def fetch_runes(version: str, lang: str = "zh_CN") -> List[Dict[str, Any]]:
    """
    拉取符文树数据
    返回 [{tree_id, tree_name, icon_url, slots: [{rune_id, name, icon_url, short_desc}]}]
    """
    url = f"{DD_BASE}/cdn/{version}/data/{lang}/runesReforged.json"
    logger.info(f"Fetching runes from {url}")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.json()

    trees = []
    for tree in raw:
        slots = []
        for slot in tree.get("slots", []):
            runes = []
            for r in slot.get("runes", []):
                runes.append({
                    "id": r["id"],
                    "name": r["name"],
                    "icon_url": f"https://ddragon.leagueoflegends.com/cdn/img/{r['icon']}",
                    "short_desc": _strip_html(r.get("shortDesc", "")),
                    "long_desc": _strip_html(r.get("longDesc", "")),
                })
            slots.append({"runes": runes})

        trees.append({
            "id": tree["id"],
            "name": tree["name"],
            "icon_url": f"https://ddragon.leagueoflegends.com/cdn/img/{tree['icon']}",
            "slots": slots,
        })

    logger.info(f"Fetched {len(trees)} rune trees")
    return trees


# ─── 召唤师技能 ──────────────────────────────────────────────────────────────

async def fetch_summoner_spells(version: str, lang: str = "zh_CN") -> Dict[str, Any]:
    """拉取召唤师技能数据"""
    url = f"{DD_BASE}/cdn/{version}/data/{lang}/summoner.json"
    logger.info(f"Fetching summoner spells from {url}")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        raw = resp.json()

    spells = {}
    for spell_id, spell in raw["data"].items():
        spells[spell_id] = {
            "id": spell_id,
            "key": spell.get("key", ""),
            "name": spell.get("name", ""),
            "description": _strip_html(spell.get("description", "")),
            "cooldown": spell.get("cooldown", []),
            "image_url": f"{DD_BASE}/cdn/{version}/img/spell/{spell['image']['full']}",
        }

    logger.info(f"Fetched {len(spells)} summoner spells")
    return spells


# ─── 辅助工具 ────────────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """移除 HTML 标签，保留纯文本"""
    import re
    # 替换 <br> 为换行
    text = re.sub(r'<br\s*/?>', '\n', text)
    # 移除其他 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 清理多余空白
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()


def _extract_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """提取有意义的装备属性，过滤掉全 0 的"""
    stat_names = {
        "FlatHPPoolMod": "生命值",
        "FlatMPPoolMod": "法力值",
        "FlatHPRegenMod": "生命回复",
        "FlatMPRegenMod": "法力回复",
        "FlatArmorMod": "护甲",
        "FlatSpellBlockMod": "魔法抗性",
        "FlatPhysicalDamageMod": "攻击力",
        "FlatMagicDamageMod": "法术强度",
        "FlatMovementSpeedMod": "移动速度",
        "PercentMovementSpeedMod": "移动速度%",
        "PercentAttackSpeedMod": "攻击速度%",
        "PercentLifeStealMod": "生命偷取%",
        "FlatCritChanceMod": "暴击率",
        "rPercentCooldownMod": "技能急速",
        "FlatArmorPenetrationMod": "护甲穿透",
        "rPercentArmorPenetrationMod": "护甲穿透%",
        "FlatMagicPenetrationMod": "法术穿透",
        "rPercentMagicPenetrationMod": "法术穿透%",
    }
    result = {}
    for key, label in stat_names.items():
        val = stats.get(key, 0)
        if val and val != 0:
            result[label] = val
    return result

"""
Riot Games API 模块
提供召唤师查询、实时对局、历史战绩等功能
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ─── 区域配置 ──────────────────────────────────────────────────────────────
# Riot API 分两种 endpoint：
#   - 平台路由 (platform): 召唤师/实时对局等（按服务器分）
#   - 区域路由 (region): 对局历史等（按大区分）

# 中国服 (Tencent) 用不同的 endpoint
CN_PLATFORM = "https://lol.qq.com/api/stats"  # 中国服特殊
CN_AREA = "https://asia.api.riotgames.com"     # 亚服通用

# 国际服区域路由
REGIONS = {
    "asia": "https://asia.api.riotgames.com",
    "americas": "https://americas.api.riotgames.com",
    "europe": "https://europe.api.riotgames.com",
}

# 平台路由
PLATFORMS = {
    "kr": "https://kr.api.riotgames.com",
    "jp1": "https://jp1.api.riotgames.com",
    "na1": "https://na1.api.riotgames.com",
    "euw1": "https://euw1.api.riotgames.com",
    "eun1": "https://eun1.api.riotgames.com",
    "br1": "https://br1.api.riotgames.com",
    "la1": "https://la1.api.riotgames.com",
    "la2": "https://la2.api.riotgames.com",
    "oc1": "https://oc1.api.riotgames.com",
    "ph2": "https://ph2.api.riotgames.com",
    "sg2": "https://sg2.api.riotgames.com",
    "th2": "https://th2.api.riotgames.com",
    "tw2": "https://tw2.api.riotgames.com",
    "vn2": "https://vn2.api.riotgames.com",
}


class RiotAPI:
    """Riot Games API 客户端"""

    def __init__(self, api_key: str, region: str = "asia", platform: str = "kr"):
        self.api_key = api_key
        self.region_base = REGIONS.get(region, REGIONS["asia"])
        self.platform_base = PLATFORMS.get(platform, PLATFORMS["kr"])
        self._headers = {"X-Riot-Token": api_key}

    async def _get(self, url: str, params: Optional[Dict] = None) -> Any:
        """通用 GET 请求，带错误处理"""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=self._headers, params=params)
            if resp.status_code == 401:
                raise ValueError("Riot API Key 无效或已过期")
            if resp.status_code == 403:
                raise ValueError("Riot API Key 已过期，请重新生成")
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", "10")
                raise RuntimeError(f"请求过于频繁，{retry_after}秒后重试")
            resp.raise_for_status()
            return resp.json()

    # ─── 召唤师查询 ──────────────────────────────────────────────────────

    async def get_summoner_by_name(self, name: str, tag: str = "KR1") -> Optional[Dict]:
        """
        通过 Riot ID（游戏名#标签）查询召唤师
        注意：中国服需要用不同的方式
        """
        url = f"{self.region_base}/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        data = await self._get(url)
        if not data:
            return None
        return {
            "puuid": data.get("puuid", ""),
            "game_name": data.get("gameName", ""),
            "tag_line": data.get("tagLine", ""),
        }

    async def get_summoner_by_puuid(self, puuid: str) -> Optional[Dict]:
        """通过 PUUID 查询召唤师详细信息"""
        url = f"{self.platform_base}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        data = await self._get(url)
        if not data:
            return None
        return {
            "id": data.get("id", ""),
            "account_id": data.get("accountId", ""),
            "puuid": data.get("puuid", ""),
            "name": data.get("name", ""),
            "profile_icon": data.get("profileIconId", 0),
            "summoner_level": data.get("summonerLevel", 0),
        }

    # ─── 实时对局（核心功能）──────────────────────────────────────────

    async def get_current_game(self, puuid: str) -> Optional[Dict]:
        """
        查询当前正在进行的对局
        这是小程序的核心功能：开局后秒查10个人的攻略
        """
        url = f"{self.platform_base}/lol/spectator/v5/active-games/by-summoner/{puuid}"
        data = await self._get(url)
        if not data:
            return None

        participants = []
        for p in data.get("participants", []):
            participants.append({
                "puuid": p.get("puuid", ""),
                "summoner_name": p.get("summonerName", ""),
                "champion_id": str(p.get("championId", 0)),
                "team_id": p.get("teamId", 0),
                "spell1": p.get("spell1Id", 0),
                "spell2": p.get("spell2Id", 0),
                "bot": p.get("bot", False),
            })

        return {
            "game_id": data.get("gameId", ""),
            "game_mode": data.get("gameMode", ""),
            "game_type": data.get("gameType", ""),
            "map_id": data.get("mapId", 0),
            "participants": participants,
        }

    # ─── 对局历史 ──────────────────────────────────────────────────────

    async def get_match_ids(self, puuid: str, count: int = 10,
                            queue_id: int = 450) -> List[str]:
        """
        获取对局 ID 列表
        queue_id: 450=ARAM, 420=排位, 400=匹配
        """
        url = f"{self.region_base}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"count": count, "type": "ranked"}
        if queue_id:
            params["queue"] = queue_id
        data = await self._get(url, params)
        return data or []

    async def get_match_detail(self, match_id: str) -> Optional[Dict]:
        """获取对局详情"""
        url = f"{self.region_base}/lol/match/v5/matches/{match_id}"
        data = await self._get(url)
        if not data:
            return None

        info = data.get("info", {})
        participants = []
        for p in info.get("participants", []):
            participants.append({
                "puuid": p.get("puuid", ""),
                "summoner_name": p.get("summonerName", ""),
                "champion_id": str(p.get("championId", 0)),
                "champion_name": p.get("championName", ""),
                "team_id": p.get("teamId", 0),
                "win": p.get("win", False),
                "kills": p.get("kills", 0),
                "deaths": p.get("deaths", 0),
                "assists": p.get("assists", 0),
                "total_damage": p.get("totalDamageDealtToChampions", 0),
                "gold": p.get("goldEarned", 0),
                "items": [p.get(f"item{i}", 0) for i in range(6)],
                "rune_primary": p.get("perks", {}).get("styles", [{}])[0].get("selections", [{}])[0].get("perk", 0) if p.get("perks") else 0,
            })

        return {
            "match_id": data.get("metadata", {}).get("matchId", ""),
            "game_mode": info.get("gameMode", ""),
            "game_duration": info.get("gameDuration", 0),
            "participants": participants,
        }

    # ─── 英雄熟练度 ──────────────────────────────────────────────────────

    async def get_champion_mastery(self, puuid: str, count: int = 5) -> List[Dict]:
        """获取英雄熟练度 Top N"""
        url = f"{self.platform_base}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top"
        params = {"count": count}
        data = await self._get(url, params)
        if not data:
            return []
        return [
            {
                "champion_id": str(m.get("championId", 0)),
                "champion_level": m.get("championLevel", 0),
                "champion_points": m.get("championPoints", 0),
            }
            for m in data
        ]

    # ─── 辅助方法 ──────────────────────────────────────────────────────

    async def lookup_and_get_current_game(self, game_name: str, tag_line: str) -> Optional[Dict]:
        """
        一步到位：输入 游戏名#标签 → 返回当前对局信息 + 每个英雄的攻略
        """
        # 1. 查 account
        account = await self.get_summoner_by_name(game_name, tag_line)
        if not account:
            return None

        # 2. 查 summoner
        summoner = await self.get_summoner_by_puuid(account["puuid"])
        if not summoner:
            return None

        # 3. 查当前对局
        game = await self.get_current_game(account["puuid"])
        if not game:
            return None

        # 4. 补充召唤师名字
        game["summoner"] = {
            "name": summoner["name"],
            "level": summoner["summoner_level"],
            "icon": summoner["profile_icon"],
        }

        return game

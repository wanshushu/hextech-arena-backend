"""
图片识别模块 - 从游戏截图中识别英雄名字
使用腾讯云 OCR 免费额度，或后端本地处理
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def match_champion_names(text: str, champions: List[Dict]) -> List[Dict]:
    """
    从 OCR 文本中匹配英雄名字
    champions: [{key, name, title, ...}]
    返回匹配到的英雄列表
    """
    # 构建名字查找表（名字 → 英雄数据）
    name_map: Dict[str, Dict] = {}
    for c in champions:
        name = c.get("name", "")
        if name:
            name_map[name] = c
        # 也用 title 匹配（如"暗裔剑魔"）
        title = c.get("title", "")
        if title:
            name_map[title] = c

    # 清洗文本
    text = text.replace("\n", " ").replace("\r", " ")
    # 移除常见干扰词
    noise_words = [
        "胜率", "选取率", "梯队", "T1", "T2", "T3", "T4", "T5",
        "VS", "vs", "蓝色方", "红色方", "胜利", "失败",
        "ARAM", "海克斯", "大乱斗", "ARAM", "ARAM",
        "击杀", "死亡", "助攻", "KDA", "金币", "伤害",
        "投降", "退出", "继续", "返回",
    ]
    cleaned = text
    for word in noise_words:
        cleaned = cleaned.replace(word, " ")

    # 按名字长度排序（长的优先匹配，避免"剑"匹配到"剑魔"）
    sorted_names = sorted(name_map.keys(), key=len, reverse=True)

    matched = []
    remaining = cleaned
    for name in sorted_names:
        if name in remaining:
            matched.append(name_map[name])
            remaining = remaining.replace(name, " ", 1)
            # ARAM 是 5v5，最多 10 个英雄
            if len(matched) >= 10:
                break

    return matched


def analyze_team_comp(blue_team: List[Dict], red_team: List[Dict]) -> Dict:
    """
    队伍组合分析
    分析两个队伍的阵容构成
    """
    def get_team_analysis(team: List[Dict]) -> Dict:
        if not team:
            return {"champions": [], "comp": {}, "strengths": [], "weaknesses": []}

        tags_count = {"Fighter": 0, "Tank": 0, "Mage": 0, "Assassin": 0,
                      "Marksman": 0, "Support": 0}
        total_winrate = 0
        tier_scores = {"T1": 5, "T2": 4, "T3": 3, "T4": 2, "T5": 1}
        total_tier_score = 0

        champions = []
        for c in team:
            tags = c.get("tags", [])
            for tag in tags:
                if tag in tags_count:
                    tags_count[tag] += 1

            wr_str = c.get("winrate", "0%").replace("%", "").replace(":", "0")
            try:
                total_winrate += float(wr_str)
            except:
                pass

            tier = c.get("tier", "T5")
            total_tier_score += tier_scores.get(tier, 1)

            champions.append({
                "name": c.get("name", ""),
                "tier": tier,
                "winrate": c.get("winrate", ""),
                "tags": tags,
            })

        avg_wr = total_winrate / len(team) if team else 0
        avg_tier = total_tier_score / len(team) if team else 0

        # 阵容构成分析
        comp = {
            "前排": tags_count["Tank"] + tags_count["Fighter"],
            "后排": tags_count["Mage"] + tags_count["Marksman"],
            "刺客": tags_count["Assassin"],
            "辅助": tags_count["Support"],
        }

        # 优劣势分析
        strengths = []
        weaknesses = []

        if comp["前排"] >= 2:
            strengths.append("前排充足，团战扛得住")
        elif comp["前排"] == 0:
            weaknesses.append("⚠️ 无前排，容易被秒")

        if comp["后排"] >= 2:
            strengths.append("后排输出充足")
        elif comp["后排"] == 0:
            weaknesses.append("⚠️ 缺乏持续输出")

        if comp["辅助"] >= 1:
            strengths.append("有辅助，团战续航强")

        if comp["刺客"] >= 2:
            strengths.append("刺客多，切后排能力强")
            if comp["后排"] < 2:
                weaknesses.append("⚠️ 刺客多但后排少，输出可能不足")

        return {
            "champions": champions,
            "comp": comp,
            "avg_winrate": round(avg_wr, 2),
            "avg_tier_score": round(avg_tier, 2),
            "strengths": strengths,
            "weaknesses": weaknesses,
        }

    blue_analysis = get_team_analysis(blue_team)
    red_analysis = get_team_analysis(red_team)

    # 判断哪边优势
    advantage = "均势"
    blue_score = blue_analysis["avg_tier_score"] + blue_analysis["avg_winrate"] / 20
    red_score = red_analysis["avg_tier_score"] + red_analysis["avg_winrate"] / 20

    if blue_score > red_score + 0.5:
        advantage = "🔵 蓝色方优势"
    elif red_score > blue_score + 0.5:
        advantage = "🔴 红色方优势"

    return {
        "blue": blue_analysis,
        "red": red_analysis,
        "advantage": advantage,
    }

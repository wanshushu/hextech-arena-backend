"""
HexTech Arena Backend — Pydantic models
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Augment(BaseModel):
    name: str
    tier: str
    winrate: str
    pickrate: str


class Champion(BaseModel):
    id: str
    name: str
    title: str = ""
    tier: str = ""
    winrate: str = ""
    pickrate: str = ""
    patch: str = ""
    top_augments: List[Dict[str, Any]] = []
    core_items: List[str] = []
    situational_items: List[str] = []
    starting_items: List[str] = []


class ChampionListItem(BaseModel):
    id: str
    name: str
    tier: str
    winrate: str
    pickrate: str


class ChampionSearchResponse(BaseModel):
    champions: List[ChampionListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class RefreshResponse(BaseModel):
    message: str
    champions_crawled: int
    status: str

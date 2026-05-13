# HexTech Arena - 海克斯大乱斗数据查询

> 项目状态：**运行中**
> 最后更新：2026-05-13

## 概述

英雄联盟大乱斗模式数据查询工具，提供英雄梯队、海克斯推荐、出装推荐等功能。

**访问地址：**
- H5 前端：https://wanshushu.github.io/hextech-arena-backend/
- API：https://web-production-fa0e7.up.railway.app/

## 技术架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GitHub Pages  │     │    Railway     │     │    aram.gg     │
│   (H5 前端)     │ ──▶ │   (FastAPI)    │ ──▶ │   (数据源)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                          SQLite DB
                      (预填充，241KB)
```

### 技术栈

- **前端**：纯 HTML/CSS/JS（H5，移动端适配）
- **后端**：Python FastAPI
- **爬虫**：httpx + Playwright（仅本地使用，Railway 不支持）
- **数据库**：SQLite（存储在 GitHub，跟代码一起部署）
- **部署**：Railway.app（后端）+ GitHub Pages（前端）

### 数据

- 172 个英雄
- 141 个海克斯
- 核心/情境/出门装备

## 项目结构

```
hextech-arena-backend/
├── backend/
│   ├── main.py          # FastAPI 后端
│   ├── database.py      # SQLite 操作
│   └── hextech.db       # 预填充数据库
├── scripts/
│   └── refresh_db.py    # 本地数据库更新脚本
├── index.html           # H5 前端
├── requirements.txt     # Python 依赖
├── Procfile            # Railway 启动命令
└── runtime.txt         # Python 3.11
```

## 常用操作

### 本地运行后端

```bash
cd ~/hextech-arena-backend
source venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 本地打开 H5 页面

```bash
open index.html
```

### 更新数据库（本地爬虫）

```bash
cd ~/hextech-arena-backend
source venv/bin/activate
python scripts/refresh_db.py
# 约 5-10 分钟
git add backend/hextech.db
git commit -m "Update database"
git push origin main
# Railway 自动 Redeploy
```

### Railway 相关

- **重启后端**：Railway 控制台 → Redeploy
- **查看日志**：Railway 控制台 → View Logs
- **无效化缓存**：Settings → Danger Zone → Invalidate Cache

### Git 操作

```bash
git remote set-url origin https://ghp_xxx@github.com/wanshushu/hextech-arena-backend.git
git push origin main
```

## 已知问题 / 待优化

### 高优先级

1. **数据更新流程繁琐**
   - 目前需要本地跑爬虫 → commit → push → Railway 自动部署
   - Railway 不支持 Playwright（无头浏览器），无法在服务端爬虫
   - 考虑：购买支持 Playwright 的 VPS 或 Railway + PostgreSQL 持久化

2. **API 没有认证**
   - 目前 CORS 是 `*`，任何人可以直接调用 API
   - 如果只是自己用没问题

### 中优先级

3. **H5 没有错误状态处理**
   - 网络断开时用户看不到友好提示
   - 可以加离线缓存或错误提示

4. **数据库每次重启重置**
   - Railway 容器重启后数据会丢失（虽然 .db 已提交，但万一 Railway 清空存储）
   - 目前方案：git 里有备份，影响不大

5. **pickrate 字段显示异常**
   - 有些英雄的 pickrate 显示 `:` 而不是正确数值
   - 可能是爬虫解析问题，但不影响核心功能

### 低优先级

6. **没有分页**
   - 英雄列表一次返回所有数据
   - 数据量小（172条），暂不需要

7. **没有搜索历史**
   - 可以加 LocalStorage 记住用户最近查看的英雄

8. **iOS App 已放弃**
   - 代码留在 `ios/` 目录，但不再维护

## 未来可能的改进方向

1. **AI 漫剧方向探索**（用户有想法）
   - 需要 AI 视频生成能力
   - 租用 GPU 服务器（如 Vast.ai、Lambda Lab）
   - 可能方向：AI 漫剧内容创作

2. **H5 端增强**
   - 加收藏/收藏功能
   - 加历史记录
   - 加数据对比功能

3. **数据可视化**
   - 英雄胜率趋势图
   - 海克斯选择热力图

## 相关文档

- [aram.gg](https://aram.gg/zh-CN) - 数据来源
- [Railway 文档](https://docs.railway.app/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 作者

huangyanlin / wanshushu

---

*最后更新于 2026-05-13*
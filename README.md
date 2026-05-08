# HexTech Arena - 海克斯大乱斗攻略 App

英雄联盟海克斯大乱斗模式英雄梯度、出装、符文数据 App。

## 项目结构

```
hextech-arena-backend/
├── backend/                 # Python FastAPI 后端
│   ├── main.py            # API 入口
│   ├── database.py        # SQLite 数据库层
│   ├── models.py           # Pydantic 模型
│   └── scrapers/           # 爬虫模块
├── ios/                    # iOS SwiftUI 前端
│   ├── project.yml         # XcodeGen 配置
│   └── HexTechArena/       # App 源码
├── scripts/                # 安装脚本
└── README.md
```

## 快速开始

### 1. 安装后端

```bash
cd ~/hextech-arena-backend
chmod +x scripts/setup-backend.sh
./scripts/setup-backend.sh
```

### 2. 启动后端服务

```bash
chmod +x scripts/run-backend.sh
./scripts/run-backend.sh
```

服务将在 `http://localhost:18789` 启动，首次启动会自动爬取 aram.gg 数据。

### 3. 安装 iOS App

```bash
cd ~/hextech-arena-backend/ios
chmod +x ../scripts/setup-ios.sh
../scripts/setup-ios.sh
```

在 Xcode 中打开 `HexTechArena.xcodeproj`，选择设备运行。

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET /` | | 服务状态 |
| `GET /health` | | 健康检查 + 数据统计 |
| `GET /tier-list` | | T1-T5 英雄梯度列表 |
| `GET /champions` | | 英雄列表（支持分页、搜索） |
| `GET /champions/{id}` | | 英雄详情 |
| `POST /refresh` | | 触发数据更新 |

## 功能

- T1-T5 英雄梯度榜
- 英雄详情（胜率、选取率、海克斯强化、装备）
- 英雄搜索
- 数据自动更新
- 手动刷新

## 技术栈

- **后端**: FastAPI + Playwright + SQLite
- **前端**: SwiftUI
- **数据来源**: aram.gg

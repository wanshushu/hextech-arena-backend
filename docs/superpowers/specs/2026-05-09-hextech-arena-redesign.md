# HexTech Arena - UI Redesign & Augment Selector

**Date:** 2026-05-09
**Status:** Draft

---

## 1. Overview

Redesign the HexTech Arena iOS app with an e-sports game aesthetic, and add a new Augment Selector feature that helps players choose the best augment at levels 7, 11, and 15.

---

## 2. UI Design - E-Sports Theme

### 2.1 Visual Style

- **Background:** Deep dark (#0a0a0f, #12122a)
- **Primary accent:** Neon red (#ff3366) — used for T1 tier, primary buttons
- **Secondary accent:** Cyan (#00f0ff) — tier labels, section headers
- **Success/recommend:** Neon green (#00ff88) — recommended augment indicator
- **Warning:** Red tint (#ff3366) — suggest refresh indicator
- **Card background:** #12122a with subtle border (#222)
- **Glow effects:** Box shadows with accent colors (e.g., `box-shadow: 0 0 12px #ff336688`)

### 2.2 Typography

- Hero names: Bold, 17-18px
- Tier labels: Bold, embedded in colored badge
- Stats: Colored values (green for winrate, cyan for pickrate)
- Section headers: 13-14px with accent color + glow

### 2.3 Tab Bar (Bottom)

Three tabs: 梯队 (Tier List), 搜索 (Search), 设置 (Settings)
- Active tab: Accent color icon + label
- Inactive: Gray icon + label

---

## 3. Screen Designs

### 3.1 Tier List Screen (主界面)

**Layout:**
- Top bar: App name "海克斯大乱斗" (neon cyan) + last refresh time (gray)
- Horizontal tier tabs: T1/T2/T3/T4/T5 — selected tier has colored background + glow, others are dimmed
- Champion list: Cards showing avatar circle (gradient colored), name, winrate badge (green), pickrate badge (cyan), tier badge (colored)

**Champion Card:**
```
[Avatar Circle] [Name] [Winrate Badge] [Pickrate Badge]     [Tier Badge]
```
- Avatar: 48px circle with gradient background, first character of name
- T1: red gradient, T5: blue gradient

### 3.2 Champion Detail Screen

**Layout:**
- Back button + avatar + name + tier badge
- Stats row: 3 cards (Winrate / Pickrate / Version)
- TOP3 Augments section (existing data, cyan header)
- **NEW:** Augment Selector section (see 3.3)
- Bottom: data source attribution

### 3.3 Augment Selector (新功能)

**Purpose:** Help players decide which augment to pick at levels 7, 11, 15.

**Flow:**
1. User selects current level (7 / 11 / 15)
2. User selects the 3 augments shown in-game (from dropdown or multi-select)
3. User taps "分析推荐"
4. App shows recommendation + refresh suggestions

**UI Layout:**

```
[🎯 海克斯推荐]

[7级 ▼] [11级] [15级]    ← Level selector tabs

选择你看到的3个海克斯：
[Augment 1] [Augment 2] [Augment 3]    ← Tappable cards (multi-select)

[分析推荐]                    ← Primary button

✓ 推荐选择：「电能脉冲」       ← Green result box
  该英雄选择此海克斯胜率+2.3%

⚠️ 「护盾强化」胜率偏低(-0.8%)  ← Red warning box
  建议刷新（还有1次机会）
```

**Refresh Logic:**
- Each augment can only be refreshed ONCE
- After refresh: replaced augment marked as "已刷新过" (disabled, grayed out)
- New augment appears in slot, App re-analyzes with new set
- Refresh count per augment stored in local state (not persisted)

**States:**
- Augment card: default (dark), selected (cyan border), recommended (green border + badge), refreshed (grayed + strikethrough)
- Level tab: selected (accent color), unselected (dimmed)
- Analyze button: enabled when 3 augments selected, disabled otherwise

---

## 4. Data & Logic

### 4.1 Augment Recommendation Logic

For a given champion + 3 augments at a given level:

1. **Best choice:** Augment with highest win rate for that champion (from `augments` table). Mark with green border + "推荐选择" badge.

2. **Refresh suggestion:** If the **lowest-winrate augment** has win rate >1% below the best, suggest refreshing it (only if refresh available for that augment slot). Mark with red indicator + "建议刷新" message.

**Win rate threshold:** >1% below best = candidate for refresh suggestion.

**Algorithm:**
```
sorted = 3 augments sorted by winrate descending
best = sorted[0]  → recommend
if sorted[2].winrate < sorted[0].winrate - 1.0%:
    suggest_refresh = sorted[2]
```

**Edge case:** If all 3 augments are within 1% of each other, no refresh suggestion (all are reasonable choices).

### 4.2 Refresh State

- Stored in memory only (temporary, per-session)
- Key: `${champion_id}_${level}_${slot_index}` (0/1/2) → `{ refreshed: bool }`
- When an augment is refreshed: the slot becomes empty, user picks a new augment from the list, that slot is now marked as "已刷新过" (cannot be refreshed again)
- Replacement augment: user selects from augment list, stored as `replacement_augment`
- No persistence — resets when leaving champion detail

**State model:**
```swift
struct AugmentSlotState {
    let originalAugment: String  // the augment that was rolled away
    var replacementAugment: String?  // user's chosen replacement
    var isRefreshed: Bool  // true = this slot has been refreshed, no more refresh allowed
}
```

### 4.3 Augment Selection UI

- Use existing `top_augments` data as source options (the champion's known augments)
- User picks from a scrollable grid of augment cards with icon + name
- 3 slots arranged horizontally
- When refresh: tapped augment slides out, replacement augment slides in
- Refreshed slots show a "已刷新" badge and refresh button is disabled

### 4.3 Augment Selection UI

- Use existing `top_augments` data as source options
- User picks from a list of known augments (autocomplete or scrollable grid)
- 3 slots must all be filled before "分析推荐" is enabled

---

## 5. Component Inventory

### 5.1 TierTabBar
- 5 tabs (T1-T5), horizontal scroll
- States: selected (colored bg + glow), unselected (dark bg + gray border)

### 5.2 ChampionRow
- Avatar circle, name, winrate/pickrate badges, tier badge
- States: default, pressed (slight opacity change)

### 5.3 StatCard
- Title + value, colored value
- Used in detail screen stats row

### 5.4 AugmentCard (in selector)
- Icon + name
- States: default, selected, recommended, refreshed-disabled

### 5.5 LevelSelector
- 3 horizontal buttons (7/11/15)
- States: selected (green border + text), unselected (gray)

### 5.6 AnalyzeButton
- Full-width gradient button
- States: enabled (gradient), disabled (gray)

### 5.7 RecommendationResult
- Green box: "✓ 推荐选择：[name]"
- Red box: "⚠️ [name] 胜率偏低，建议刷新"

---

## 6. File Changes

### Backend
- `backend/main.py` — already has augment data, no changes needed

### iOS

**New files:**
- `Views/AugmentSelectorView.swift` — new view component
- `Models/AugmentSelector.swift` — state model for selector

**Modified files:**
- `Views/ChampionDetailView.swift` — add augment selector section
- `Views/TierListView.swift` — apply e-sports theme styling
- `Views/SearchView.swift` — apply e-sports theme styling
- `Models/Champion.swift` — already has augment models, may need refresh state model
- `Services/APIService.swift` — no changes needed

---

## 7. Implementation Notes

- Theme colors defined as SwiftUI Color extensions
- Use `NavigationStack` for navigation
- Augment selector state managed with `@State` in ChampionDetailView
- Augment list from `champion.topAugments` (existing API data)
- Recommendation logic: sort 3 augments by winrate, best = top, refresh candidate = bottom if >1% below best
# HexTech Arena - UI Redesign + Augment Selector

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply e-sports theme to all iOS views, and implement the Augment Selector feature for champion detail.

**Architecture:** SwiftUI views with shared Color theme extensions. Augment selector uses local @State for refresh tracking. Backend already has all needed data.

**Tech Stack:** SwiftUI (iOS 16+), Xcode, no new dependencies.

---

## File Structure

```
ios/HexTechArena/
├── Theme/
│   └── Colors.swift              # NEW - e-sports color palette
├── Views/
│   ├── TierListView.swift       # MODIFY - apply theme + gradient avatars
│   ├── ChampionDetailView.swift  # MODIFY - apply theme + add selector
│   ├── AugmentSelectorView.swift  # NEW - augment selector component
│   ├── SearchView.swift         # MODIFY - apply dark theme
│   └── SettingsView.swift       # MODIFY - apply dark theme
└── Models/
    └── Champion.swift            # MODIFY - add state models
```

---

## Implementation Plan

### Task 1: Create Color Theme Extension

**Files:**
- Create: `ios/HexTechArena/Theme/Colors.swift`

- [ ] **Step 1: Create directory and Colors.swift**

```bash
mkdir -p /Users/huangyanlin/hextech-arena-backend/ios/HexTechArena/Theme
```

Write file `ios/HexTechArena/Theme/Colors.swift`:

```swift
import SwiftUI

extension Color {
    // E-Sports Theme Colors
    static let esportsBg = Color(hex: "0a0a0f")
    static let esportsCard = Color(hex: "12122a")
    static let esportsBorder = Color(hex: "222222")

    static let esportsT1 = Color(hex: "FF3366")
    static let esportsT2 = Color(hex: "FFA94D")
    static let esportsT3 = Color(hex: "FFE066")
    static let esportsT4 = Color(hex: "69DB7C")
    static let esportsT5 = Color(hex: "74C0FC")

    static let esportsAccent = Color(hex: "00f0ff")
    static let esportsRecommend = Color(hex: "00ff88")
    static let esportsWarning = Color(hex: "FF3366")
    static let esportsText = Color.white
    static let esportsTextSecondary = Color(hex: "888888")

    static func tierColor(_ tier: String) -> Color {
        switch tier {
        case "T1": return .esportsT1
        case "T2": return .esportsT2
        case "T3": return .esportsT3
        case "T4": return .esportsT4
        case "T5": return .esportsT5
        default: return .gray
        }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add ios/HexTechArena/Theme/Colors.swift
git commit -m "feat(ios): add e-sports color theme"
```

---

### Task 2: Apply E-Sports Theme to TierListView

**Files:**
- Modify: `ios/HexTechArena/Views/TierListView.swift`

- [ ] **Step 1: Replace TierListView**

Replace the entire file content with:

```swift
import SwiftUI

struct TierListView: View {
    @State private var tierList: [String: [ChampionListItem]] = [:]
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var selectedTier = "T1"
    @State private var lastUpdated = ""

    var body: some View {
        NavigationStack {
            ZStack {
                Color.esportsBg.ignoresSafeArea()
                VStack(spacing: 0) {
                    if isLoading {
                        ProgressView("加载中...")
                            .tint(.esportsAccent)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if let error = errorMessage {
                        VStack(spacing: 16) {
                            Image(systemName: "wifi.exclamationmark")
                                .font(.system(size: 48))
                                .foregroundColor(.esportsTextSecondary)
                            Text(error)
                                .foregroundColor(.esportsTextSecondary)
                            Button("重试") {
                                Task { await loadData() }
                            }
                            .tint(.esportsAccent)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        HStack {
                            Text("海克斯大乱斗")
                                .font(.headline)
                                .fontWeight(.bold)
                                .foregroundColor(.esportsAccent)
                            Spacer()
                            Text(lastUpdated)
                                .font(.caption)
                                .foregroundColor(.esportsTextSecondary)
                        }
                        .padding(.horizontal)
                        .padding(.top, 8)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 10) {
                                ForEach(["T1", "T2", "T3", "T4", "T5"], id: \.self) { tier in
                                    Button {
                                        selectedTier = tier
                                    } label: {
                                        Text(tier)
                                            .font(.headline)
                                            .fontWeight(.bold)
                                            .foregroundColor(selectedTier == tier ? .white : .esportsTextSecondary)
                                            .padding(.horizontal, 18)
                                            .padding(.vertical, 8)
                                            .background(
                                                Capsule()
                                                    .fill(selectedTier == tier ? Color.tierColor(tier) : Color.esportsCard)
                                            )
                                            .overlay(
                                                Capsule()
                                                    .stroke(selectedTier == tier ? Color.clear : Color.esportsBorder, lineWidth: 1)
                                            )
                                            .shadow(color: selectedTier == tier ? Color.tierColor(tier).opacity(0.5) : .clear, radius: 6)
                                    }
                                }
                            }
                            .padding(.horizontal)
                        }
                        .padding(.vertical, 12)

                        if let champions = tierList[selectedTier], !champions.isEmpty {
                            List(champions) { champion in
                                NavigationLink(destination: ChampionDetailView(championId: champion.id)) {
                                    ChampionRowView(champion: champion)
                                }
                                .listRowBackground(Color.esportsCard)
                            }
                            .listStyle(.plain)
                            .scrollContentBackground(.hidden)
                        } else {
                            VStack(spacing: 16) {
                                Image(systemName: "person.slash")
                                    .font(.system(size: 48))
                                    .foregroundColor(.esportsTextSecondary)
                                Text("暂无数据")
                                    .font(.headline)
                                    .foregroundColor(.esportsText)
                                Text("该梯队暂无英雄")
                                    .font(.subheadline)
                                    .foregroundColor(.esportsTextSecondary)
                            }
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                        }
                    }
                }
            }
            .navigationBarHidden(true)
            .task {
                await loadData()
            }
        }
    }

    private func loadData() async {
        isLoading = true
        errorMessage = nil
        do {
            let response = try await APIService.shared.fetchTierList()
            tierList = response.tiers
            lastUpdated = response.updatedAt
            isLoading = false
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }
}

struct ChampionRowView: View {
    let champion: ChampionListItem

    private var tierGradient: LinearGradient {
        let color = Color.tierColor(champion.tier)
        return LinearGradient(colors: [color, color.opacity(0.7)], startPoint: .topLeading, endPoint: .bottomTrailing)
    }

    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(tierGradient)
                .frame(width: 50, height: 50)
                .overlay(
                    Text(String(champion.name.prefix(1)))
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.white)
                )
                .shadow(color: Color.tierColor(champion.tier).opacity(0.4), radius: 6)

            VStack(alignment: .leading, spacing: 4) {
                Text(champion.name)
                    .font(.headline)
                    .foregroundColor(.esportsText)
                HStack(spacing: 8) {
                    StatBadge(label: "胜率", value: champion.winrate, color: .esportsRecommend)
                    StatBadge(label: "选取", value: champion.pickrate, color: .esportsAccent)
                }
            }

            Spacer()

            TierBadge(tier: champion.tier)
        }
        .padding(.vertical, 6)
    }
}

struct StatBadge: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 3) {
            Text(label)
                .font(.caption2)
                .foregroundColor(.esportsTextSecondary)
            Text(value)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 2)
        .background(color.opacity(0.15))
        .cornerRadius(4)
    }
}

struct TierBadge: View {
    let tier: String

    var body: some View {
        Text(tier)
            .font(.caption)
            .fontWeight(.bold)
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color.tierColor(tier))
            .clipShape(RoundedRectangle(cornerRadius: 6))
            .shadow(color: Color.tierColor(tier).opacity(0.4), radius: 4)
    }
}
```

- [ ] **Step 2: Build and verify**

Run: `xcodebuild -project ios/HexTechArena.xcodeproj -scheme HexTechArena -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 16 Pro' build 2>&1 | tail -5`

Expected: `BUILD SUCCEEDED`

- [ ] **Step 3: Commit**

```bash
git add ios/HexTechArena/Views/TierListView.swift
git commit -m "feat(ios): apply e-sports theme to TierListView"
```

---

### Task 3: Implement AugmentSelectorView + State Model FIRST

This must come before Task 4 (ChampionDetailView) because ChampionDetailView will reference AugmentSelectorView.

**Files:**
- Create: `ios/HexTechArena/Views/AugmentSelectorView.swift`
- Modify: `ios/HexTechArena/Models/Champion.swift`

- [ ] **Step 1: Add state model to Champion.swift**

Add at end of file:

```swift
// MARK: - Augment Selector State
struct AugmentSlotState: Identifiable {
    let id = UUID()
    var augmentName: String
    var isRefreshed: Bool = false
    var winrate: String = ""
}

struct AugmentSelectorState {
    var selectedLevel: Int = 7
    var slots: [AugmentSlotState] = []
    var recommendation: String = ""
    var refreshSuggestion: String = ""
    var isAnalyzed: Bool = false

    mutating func analyze(allAugments: [Augment]) {
        guard slots.count == 3 else { return }

        let winrateMap: [String: String] = Dictionary(uniqueKeysWithValues:
            allAugments.map { ($0.name, $0.winrate) }
        )

        var items: [(name: String, wr: Double)] = slots.compactMap { slot in
            let wrStr = winrateMap[slot.augmentName] ?? "0%"
            let wr = Double(wrStr.replacingOccurrences(of: "%", with: "")) ?? 0
            return (slot.augmentName, wr)
        }

        items.sort { $0.wr > $1.wr }
        recommendation = items[0].name

        let lowest = items[2]
        let best = items[0]
        refreshSuggestion = (lowest.wr < best.wr - 1.0) ? lowest.name : ""

        isAnalyzed = true
    }

    mutating func refreshSlot(at index: Int, allAugments: [Augment]) {
        guard index < slots.count else { return }
        let usedNames = Set(slots.map { $0.augmentName })
        slots[index].isRefreshed = true
        if let nextBest = allAugments.first(where: { !usedNames.contains($0.name) }) {
            slots[index] = AugmentSlotState(augmentName: nextBest.name, isRefreshed: true, winrate: nextBest.winrate)
        }
        analyze(allAugments: allAugments)
    }
}
```

- [ ] **Step 2: Create AugmentSelectorView.swift**

```swift
import SwiftUI

struct AugmentSelectorView: View {
    let championId: String
    let championAugments: [Augment]

    @State private var selectorState = AugmentSelectorState()

    private let levels = [7, 11, 15]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("🎯 海克斯推荐")
                    .font(.headline)
                    .foregroundColor(.esportsWarning)
                Spacer()
            }

            HStack(spacing: 10) {
                ForEach(levels, id: \.self) { level in
                    Button {
                        selectorState.selectedLevel = level
                        selectorState.isAnalyzed = false
                    } label: {
                        Text("\(level)")
                            .font(.headline)
                            .fontWeight(.bold)
                            .foregroundColor(selectorState.selectedLevel == level ? .esportsRecommend : .esportsTextSecondary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(selectorState.selectedLevel == level ? Color.esportsCard : Color.clear)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(selectorState.selectedLevel == level ? Color.esportsRecommend : Color.esportsBorder, lineWidth: 1)
                            )
                    }
                }
            }

            Text("从下方选择你看到的3个海克斯：")
                .font(.caption)
                .foregroundColor(.esportsTextSecondary)

            HStack(spacing: 10) {
                ForEach(Array(selectorState.slots.enumerated()), id: \.element.id) { index, slot in
                    AugmentSlotCard(
                        slot: slot,
                        isSelected: true,
                        onRefresh: selectorState.slots[index].isRefreshed ? nil : {
                            selectorState.refreshSlot(at: index, allAugments: championAugments)
                        }
                    )
                }
                ForEach(0..<(3 - selectorState.slots.count), id: \.self) { _ in
                    AugmentSlotEmpty()
                }
            }

            Button {
                selectorState.analyze(allAugments: championAugments)
            } label: {
                Text("分析推荐")
                    .font(.headline)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(
                        LinearGradient(colors: [.esportsWarning, Color(hex: "FF6699")], startPoint: .leading, endPoint: .trailing)
                    )
                    .cornerRadius(8)
                    .shadow(color: .esportsWarning.opacity(0.4), radius: 6)
            }
            .disabled(selectorState.slots.count < 3)

            if selectorState.isAnalyzed {
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.esportsRecommend)
                        Text("推荐选择：「\(selectorState.recommendation)」")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundColor(.esportsRecommend)
                    }
                    if let augment = championAugments.first(where: { $0.name == selectorState.recommendation }) {
                        Text("胜率 \(augment.winrate)，表现最佳")
                            .font(.caption)
                            .foregroundColor(.esportsTextSecondary)
                    }
                }
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.esportsRecommend.opacity(0.1))
                .cornerRadius(8)
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.esportsRecommend.opacity(0.3), lineWidth: 1))

                if !selectorState.refreshSuggestion.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.esportsWarning)
                            Text("「\(selectorState.refreshSuggestion)」胜率偏低")
                                .font(.subheadline)
                                .foregroundColor(.esportsWarning)
                        }
                        Text("建议刷新（有1次机会）")
                            .font(.caption)
                            .foregroundColor(.esportsTextSecondary)
                    }
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.esportsWarning.opacity(0.1))
                    .cornerRadius(8)
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.esportsWarning.opacity(0.3), lineWidth: 1))
                }
            }
        }
        .padding()
        .background(Color.esportsCard)
        .cornerRadius(16)
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.esportsBorder, lineWidth: 1))
        .onAppear {
            // Pre-fill with first 3 augments for demo
            selectorState.slots = championAugments.prefix(3).map {
                AugmentSlotState(augmentName: $0.name, winrate: $0.winrate)
            }
        }
    }
}

struct AugmentSlotCard: View {
    let slot: AugmentSlotState
    let isSelected: Bool
    let onRefresh: (() -> Void)?

    var body: some View {
        VStack(spacing: 4) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(slot.isRefreshed ? Color.gray.opacity(0.3) : Color.esportsCard)
                    .frame(height: 70)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(slot.isRefreshed ? Color.gray : Color.esportsAccent, lineWidth: 1)
                    )

                VStack(spacing: 4) {
                    Image(systemName: "sparkles")
                        .font(.system(size: 22))
                        .foregroundColor(slot.isRefreshed ? .gray : .esportsAccent)
                    Text(slot.augmentName)
                        .font(.caption2)
                        .foregroundColor(slot.isRefreshed ? .gray : .esportsText)
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                }
            }

            if slot.isRefreshed {
                Text("已刷新")
                    .font(.system(size: 9))
                    .foregroundColor(.gray)
            }
        }
    }
}

struct AugmentSlotEmpty: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(Color.esportsCard.opacity(0.5))
            .frame(height: 70)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(style: StrokeStyle(lineWidth: 1, dash: [4]))
                    .foregroundColor(Color.esportsBorder)
            )
            .overlay(
                Image(systemName: "plus")
                    .foregroundColor(.esportsTextSecondary)
            )
    }
}
```

- [ ] **Step 3: Build and verify**

Run: `xcodebuild -project ios/HexTechArena.xcodeproj -scheme HexTechArena -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 16 Pro' build 2>&1 | tail -5`

Expected: `BUILD SUCCEEDED`

- [ ] **Step 4: Commit**

```bash
git add ios/HexTechArena/Models/Champion.swift ios/HexTechArena/Views/AugmentSelectorView.swift
git commit -m "feat(ios): implement AugmentSelectorView with recommendation logic"
```

---

### Task 4: Apply E-Sports Theme to ChampionDetailView

**Files:**
- Modify: `ios/HexTechArena/Views/ChampionDetailView.swift`

- [ ] **Step 1: Replace ChampionDetailView**

Replace the entire file content with:

```swift
import SwiftUI

struct ChampionDetailView: View {
    let championId: String

    @State private var champion: Champion?
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        ZStack {
            Color.esportsBg.ignoresSafeArea()
            ScrollView {
                if isLoading {
                    ProgressView("加载中...")
                        .tint(.esportsAccent)
                        .frame(maxWidth: .infinity, minHeight: 300)
                } else if let error = errorMessage {
                    VStack(spacing: 16) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 48))
                            .foregroundColor(.esportsTextSecondary)
                        Text(error)
                            .foregroundColor(.esportsTextSecondary)
                    }
                    .frame(maxWidth: .infinity, minHeight: 300)
                } else if let champ = champion {
                    VStack(alignment: .leading, spacing: 20) {
                        // Header
                        VStack(spacing: 12) {
                            HStack {
                                Button { } label: {
                                    Image(systemName: "chevron.left")
                                        .foregroundColor(.esportsText)
                                }
                                Spacer()
                            }

                            Circle()
                                .fill(LinearGradient(colors: [Color.tierColor(champ.tier), Color.tierColor(champ.tier).opacity(0.7)], startPoint: .topLeading, endPoint: .bottomTrailing))
                                .frame(width: 80, height: 80)
                                .overlay(
                                    Text(String(champ.name.prefix(1)))
                                        .font(.largeTitle)
                                        .fontWeight(.bold)
                                        .foregroundColor(.white)
                                )
                                .shadow(color: Color.tierColor(champ.tier).opacity(0.5), radius: 10)

                            Text(champ.name)
                                .font(.title)
                                .fontWeight(.bold)
                                .foregroundColor(.esportsText)

                            if !champ.title.isEmpty {
                                Text(champ.title)
                                    .font(.subheadline)
                                    .foregroundColor(.esportsTextSecondary)
                            }

                            HStack(spacing: 16) {
                                StatCard(title: "胜率", value: champ.winrate, color: .esportsRecommend)
                                StatCard(title: "选取率", value: champ.pickrate, color: .esportsAccent)
                                StatCard(title: "梯队", value: champ.tier, color: Color.tierColor(champ.tier))
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.esportsCard)
                        .cornerRadius(16)

                        // Top Augments
                        if let augments = champ.topAugments, !augments.isEmpty {
                            ESportsSection(title: "🔮 海克斯强化 TOP3") {
                                ForEach(Array(augments.prefix(3).enumerated()), id: \.element.id) { index, augment in
                                    AugmentRowView(augment: augment, rank: index + 1)
                                }
                            }
                        }

                        // Core Items
                        if let items = champ.coreItems, !items.isEmpty {
                            ESportsSection(title: "⚔️ 核心装备") {
                                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                                    ForEach(items, id: \.self) { item in
                                        ItemBadge(name: item)
                                    }
                                }
                            }
                        }

                        // Situational Items
                        if let items = champ.situationalItems, !items.isEmpty {
                            ESportsSection(title: "❓ 情境装备") {
                                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                                    ForEach(items, id: \.self) { item in
                                        ItemBadge(name: item)
                                    }
                                }
                            }
                        }

                        // Starting Items
                        if let items = champ.startingItems, !items.isEmpty {
                            ESportsSection(title: "🏠 出门装") {
                                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                                    ForEach(items, id: \.self) { item in
                                        ItemBadge(name: item)
                                    }
                                }
                            }
                        }

                        // NEW: Augment Selector
                        AugmentSelectorView(championId: championId, championAugments: champ.topAugments ?? [])

                        if let patch = champ.patch, !patch.isEmpty {
                            HStack {
                                Spacer()
                                Text("数据来源: aram.gg | 版本 \(patch)")
                                    .font(.caption)
                                    .foregroundColor(.esportsTextSecondary)
                                Spacer()
                            }
                        }
                    }
                    .padding()
                }
            }
        }
        .navigationBarHidden(true)
        .task {
            await loadChampion()
        }
    }

    private func loadChampion() async {
        isLoading = true
        errorMessage = nil
        do {
            champion = try await APIService.shared.fetchChampionDetail(id: championId)
            isLoading = false
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let color: Color

    var body: some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.headline)
                .fontWeight(.bold)
                .foregroundColor(color)
            Text(title)
                .font(.caption)
                .foregroundColor(.esportsTextSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(Color.esportsCard)
        .cornerRadius(10)
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.esportsBorder, lineWidth: 1))
    }
}

struct ESportsSection<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .foregroundColor(.esportsAccent)
            content
        }
        .padding()
        .background(Color.esportsCard)
        .cornerRadius(16)
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.esportsBorder, lineWidth: 1))
    }
}

struct AugmentRowView: View {
    let augment: Augment
    let rank: Int

    var body: some View {
        HStack {
            Text("\(rank)")
                .font(.caption)
                .fontWeight(.bold)
                .foregroundColor(.esportsAccent)
                .frame(width: 20)

            Circle()
                .fill(Color.esportsCard)
                .frame(width: 36, height: 36)
                .overlay(
                    Image(systemName: "sparkles")
                        .foregroundColor(.esportsAccent)
                        .font(.system(size: 14))
                )

            VStack(alignment: .leading, spacing: 2) {
                Text(augment.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.esportsText)
                Text(augment.tier)
                    .font(.caption)
                    .foregroundColor(.esportsTextSecondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 2) {
                Text(augment.winrate)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.esportsRecommend)
                Text(augment.pickrate)
                    .font(.caption)
                    .foregroundColor(.esportsTextSecondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct ItemBadge: View {
    let name: String

    var body: some View {
        VStack(spacing: 4) {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.esportsCard)
                .frame(width: 50, height: 50)
                .overlay(
                    Image(systemName: "shield.fill")
                        .foregroundColor(Color(hex: "673AB7"))
                )
            Text(name)
                .font(.caption2)
                .lineLimit(2)
                .multilineTextAlignment(.center)
                .foregroundColor(.esportsText)
        }
    }
}
```

- [ ] **Step 2: Build and verify**

Run: `xcodebuild -project ios/HexTechArena.xcodeproj -scheme HexTechArena -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 16 Pro' build 2>&1 | tail -5`

Expected: `BUILD SUCCEEDED`

- [ ] **Step 3: Commit**

```bash
git add ios/HexTechArena/Views/ChampionDetailView.swift
git commit -m "feat(ios): apply e-sports theme to ChampionDetailView"
```

---

### Task 5: Apply E-Sports Theme to SearchView and SettingsView

**Files:**
- Modify: `ios/HexTechArena/Views/SearchView.swift`
- Modify: `ios/HexTechArena/Views/SettingsView.swift`

- [ ] **Step 1: Replace SearchView.swift**

```swift
import SwiftUI

struct SearchView: View {
    @State private var searchText = ""
    @State private var champions: [ChampionListItem] = []
    @State private var isLoading = false
    @State private var hasSearched = false

    var body: some View {
        ZStack {
            Color.esportsBg.ignoresSafeArea()
            NavigationStack {
                VStack(spacing: 0) {
                    if isLoading {
                        ProgressView("搜索中...")
                            .tint(.esportsAccent)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if champions.isEmpty && hasSearched {
                        VStack(spacing: 16) {
                            Image(systemName: "magnifyingglass")
                                .font(.system(size: 48))
                                .foregroundColor(.esportsTextSecondary)
                            Text("未找到英雄")
                                .font(.headline)
                                .foregroundColor(.esportsText)
                            Text("尝试其他关键词")
                                .font(.subheadline)
                                .foregroundColor(.esportsTextSecondary)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        List(champions) { champion in
                            NavigationLink(destination: ChampionDetailView(championId: champion.id)) {
                                ChampionRowView(champion: champion)
                            }
                            .listRowBackground(Color.esportsCard)
                        }
                        .listStyle(.plain)
                        .scrollContentBackground(.hidden)
                    }
                }
                .background(Color.esportsBg)
                .navigationTitle("搜索英雄")
                .navigationBarTitleDisplayMode(.inline)
                .searchable(text: $searchText, prompt: "输入英雄名称")
                .onChange(of: searchText) { newValue in
                    Task {
                        await search(query: newValue)
                    }
                }
                .navigationBarItems(trailing:
                    Button {
                        Task { await loadInitial() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(.esportsAccent)
                    }
                )
                .task {
                    await loadInitial()
                }
            }
        }
    }

    private func loadInitial() async {
        hasSearched = false
        do {
            let response = try await APIService.shared.fetchChampions(page: 1)
            champions = response.champions
        } catch {
            // Silently fail on initial load
        }
    }

    private func search(query: String) async {
        hasSearched = true
        if query.isEmpty {
            await loadInitial()
            return
        }

        isLoading = true
        do {
            let response = try await APIService.shared.fetchChampions(search: query, page: 1)
            champions = response.champions
        } catch {
            champions = []
        }
        isLoading = false
    }
}
```

- [ ] **Step 2: Replace SettingsView.swift**

```swift
import SwiftUI

struct SettingsView: View {
    @State private var healthInfo: HealthResponse?
    @State private var isRefreshing = false
    @State private var showingAlert = false
    @State private var alertMessage = ""

    var body: some View {
        ZStack {
            Color.esportsBg.ignoresSafeArea()
            NavigationStack {
                List {
                    Section {
                        if let health = healthInfo {
                            HStack {
                                Text("英雄数量")
                                    .foregroundColor(.esportsText)
                                Spacer()
                                Text("\(health.championCount)")
                                    .foregroundColor(.esportsRecommend)
                            }

                            if let lastRefresh = health.lastRefresh {
                                HStack {
                                    Text("最后更新")
                                        .foregroundColor(.esportsText)
                                    Spacer()
                                    Text(lastRefresh.timestamp)
                                        .font(.caption)
                                        .foregroundColor(.esportsTextSecondary)
                                }

                                HStack {
                                    Text("更新状态")
                                        .foregroundColor(.esportsText)
                                    Spacer()
                                    Text(lastRefresh.status == "completed" ? "已完成" : lastRefresh.status)
                                        .foregroundColor(lastRefresh.status == "completed" ? .esportsRecommend : .orange)
                                }

                                HStack {
                                    Text("本次爬取")
                                        .foregroundColor(.esportsText)
                                    Spacer()
                                    Text("\(lastRefresh.championsCrawled) 个英雄")
                                        .foregroundColor(.esportsTextSecondary)
                                }
                            }

                            if let counts = health.tierCounts as? [String: Int] {
                                HStack {
                                    Text("T1 英雄")
                                        .foregroundColor(.esportsText)
                                    Spacer()
                                    Text("\(counts["T1"] ?? 0)")
                                        .foregroundColor(.esportsT1)
                                }
                                HStack {
                                    Text("T2 英雄")
                                        .foregroundColor(.esportsText)
                                    Spacer()
                                    Text("\(counts["T2"] ?? 0)")
                                        .foregroundColor(.esportsT2)
                                }
                            }
                        } else {
                            HStack {
                                ProgressView()
                                    .tint(.esportsAccent)
                                Text("加载中...")
                                    .foregroundColor(.esportsTextSecondary)
                            }
                        }
                    }
                    .listRowBackground(Color.esportsCard)

                    Section {
                        Button {
                            Task { await triggerRefresh() }
                        } label: {
                            HStack {
                                if isRefreshing {
                                    ProgressView()
                                        .padding(.trailing, 4)
                                }
                                Text(isRefreshing ? "更新中..." : "手动更新数据")
                                    .foregroundColor(.esportsAccent)
                            }
                        }
                        .disabled(isRefreshing)
                    }
                    .listRowBackground(Color.esportsCard)

                    Section {
                        HStack {
                            Text("App 版本")
                                .foregroundColor(.esportsText)
                            Spacer()
                            Text("1.0.0")
                                .foregroundColor(.esportsTextSecondary)
                        }

                        HStack {
                            Text("数据来源")
                                .foregroundColor(.esportsText)
                            Spacer()
                            Text("aram.gg")
                                .foregroundColor(.esportsTextSecondary)
                        }

                        HStack {
                            Text("后端地址")
                                .foregroundColor(.esportsText)
                            Spacer()
                            Text("localhost:18789")
                                .font(.caption)
                                .foregroundColor(.esportsTextSecondary)
                        }
                    }
                    .listRowBackground(Color.esportsCard)

                    Section {
                        Link(destination: URL(string: "https://aramgg.com/zh-CN/champions")!) {
                            HStack {
                                Text("访问数据源网站")
                                    .foregroundColor(.esportsText)
                                Spacer()
                                Image(systemName: "arrow.up.right.square")
                                    .foregroundColor(.esportsAccent)
                            }
                        }
                    }
                    .listRowBackground(Color.esportsCard)
                }
                .scrollContentBackground(.hidden)
                .navigationTitle("设置")
                .navigationBarTitleDisplayMode(.inline)
                .navigationBarItems(trailing:
                    Button {
                        Task { await loadHealth() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(.esportsAccent)
                    }
                )
                .alert("提示", isPresented: $showingAlert) {
                    Button("确定", role: .cancel) {}
                } message: {
                    Text(alertMessage)
                }
                .task {
                    await loadHealth()
                }
            }
        }
    }

    private func loadHealth() async {
        do {
            healthInfo = try await APIService.shared.fetchHealth()
        } catch {
            alertMessage = "无法连接后端服务: \(error.localizedDescription)"
            showingAlert = true
        }
    }

    private func triggerRefresh() async {
        isRefreshing = true
        do {
            try await APIService.shared.triggerRefresh()
            alertMessage = "数据更新已启动，请稍后刷新页面查看"
            showingAlert = true
        } catch {
            alertMessage = "更新失败: \(error.localizedDescription)"
            showingAlert = true
        }
        isRefreshing = false
    }
}
```

- [ ] **Step 3: Build and verify**

Run: `xcodebuild -project ios/HexTechArena.xcodeproj -scheme HexTechArena -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 16 Pro' build 2>&1 | tail -5`

Expected: `BUILD SUCCEEDED`

- [ ] **Step 4: Commit**

```bash
git add ios/HexTechArena/Views/SearchView.swift ios/HexTechArena/Views/SettingsView.swift
git commit -m "feat(ios): apply e-sports theme to SearchView and SettingsView"
```

---

## Verification

After all tasks complete, open `ios/HexTechArena.xcodeproj` in Xcode, select iPhone simulator, press Cmd+R, and verify:
- Dark background on all screens
- Tier tabs show colored glow when selected
- Champion avatars have gradient based on tier
- Champion detail shows e-sports styled stats
- Core/Situational/Starting items sections visible
- Augment selector visible in champion detail
- Tapping "分析推荐" shows recommendation + refresh suggestion

---

## Notes

- All colors reference `Color.esports*` from Colors.swift
- No ContentUnavailableView used (iOS 16+ compatibility)
- onChange uses single-parameter closure (iOS 16 compatible)
- Augment selector uses in-memory state only (no persistence)
- Keep Core/Situational/Starting Items sections in champion detail (preserved from original)
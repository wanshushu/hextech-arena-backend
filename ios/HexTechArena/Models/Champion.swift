import Foundation

struct Champion: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let title: String
    let tier: String
    let winrate: String
    let pickrate: String
    let patch: String?
    var topAugments: [Augment]?
    var coreItems: [String]?
    var situationalItems: [String]?
    var startingItems: [String]?

    enum CodingKeys: String, CodingKey {
        case id, name, title, tier, winrate, pickrate, patch
        case topAugments = "top_augments"
        case coreItems = "core_items"
        case situationalItems = "situational_items"
        case startingItems = "starting_items"
    }
}

struct Augment: Codable, Identifiable, Hashable {
    var id: String { name }
    let name: String
    let tier: String
    let winrate: String
    let pickrate: String
}

struct ChampionListItem: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let tier: String
    let winrate: String
    let pickrate: String
}

struct ChampionSearchResponse: Codable {
    let champions: [ChampionListItem]
    let total: Int
    let page: Int
    let pageSize: Int
    let totalPages: Int

    enum CodingKeys: String, CodingKey {
        case champions, total, page
        case pageSize = "page_size"
        case totalPages = "total_pages"
    }
}

struct TierListResponse: Codable {
    let updatedAt: String
    let tiers: [String: [ChampionListItem]]

    enum CodingKeys: String, CodingKey {
        case updatedAt = "updated_at"
        case tiers
    }
}

struct HealthResponse: Codable {
    let status: String
    let lastRefresh: RefreshLog?
    let championCount: Int
    let tierCounts: [String: Int]

    enum CodingKeys: String, CodingKey {
        case status
        case lastRefresh = "last_refresh"
        case championCount = "champion_count"
        case tierCounts = "tier_counts"
    }
}

struct RefreshLog: Codable {
    let timestamp: String
    let status: String
    let tiersFound: String
    let championsCrawled: Int

    enum CodingKeys: String, CodingKey {
        case timestamp, status
        case tiersFound = "tiers_found"
        case championsCrawled = "champions_crawled"
    }
}

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

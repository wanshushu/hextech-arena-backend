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

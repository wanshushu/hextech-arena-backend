import SwiftUI

struct TierListView: View {
    @State private var tierList: [String: [ChampionListItem]] = [:]
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var selectedTier = "T1"
    @State private var lastUpdated = ""

    private let tierColors: [String: Color] = [
        "T1": Color(hex: "FF6B6B"),
        "T2": Color(hex: "FFA94D"),
        "T3": Color(hex: "FFE066"),
        "T4": Color(hex: "69DB7C"),
        "T5": Color(hex: "74C0FC"),
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if isLoading {
                    ProgressView("加载中...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let error = errorMessage {
                    VStack(spacing: 16) {
                        Image(systemName: "wifi.exclamationmark")
                            .font(.system(size: 48))
                            .foregroundColor(.secondary)
                        Text(error)
                            .foregroundColor(.secondary)
                        Button("重试") {
                            Task { await loadData() }
                        }
                        .buttonStyle(.bordered)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    // Tier tabs
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(["T1", "T2", "T3", "T4", "T5"], id: \.self) { tier in
                                Button {
                                    selectedTier = tier
                                } label: {
                                    Text(tier)
                                        .font(.headline)
                                        .fontWeight(.bold)
                                        .foregroundColor(selectedTier == tier ? .white : .primary)
                                        .padding(.horizontal, 20)
                                        .padding(.vertical, 8)
                                        .background(
                                            Capsule()
                                                .fill(selectedTier == tier ? (tierColors[tier] ?? .blue) : Color.gray.opacity(0.2))
                                        )
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                    .padding(.vertical, 12)
                    .background(Color(.systemGroupedBackground))

                    if let champions = tierList[selectedTier], !champions.isEmpty {
                        List(champions) { champion in
                            NavigationLink(destination: ChampionDetailView(championId: champion.id)) {
                                ChampionRowView(champion: champion)
                            }
                        }
                        .listStyle(.plain)
                    } else {
                        ContentUnavailableView(
                            "暂无数据",
                            systemImage: "person.slash",
                            description: Text("该梯队暂无英雄")
                        )
                    }
                }
            }
            .navigationTitle("海克斯大乱斗")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await loadData() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
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

    var body: some View {
        HStack(spacing: 12) {
            // Champion icon placeholder
            Circle()
                .fill(Color.gray.opacity(0.3))
                .frame(width: 50, height: 50)
                .overlay(
                    Text(String(champion.name.prefix(1)))
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)
                )

            VStack(alignment: .leading, spacing: 4) {
                Text(champion.name)
                    .font(.headline)
                HStack(spacing: 8) {
                    StatBadge(label: "胜率", value: champion.winrate, color: .green)
                    StatBadge(label: "选取", value: champion.pickrate, color: .blue)
                }
            }

            Spacer()

            TierBadge(tier: champion.tier)
        }
        .padding(.vertical, 4)
    }
}

struct StatBadge: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        HStack(spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundColor(.secondary)
            Text(value)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundColor(color)
        }
    }
}

struct TierBadge: View {
    let tier: String

    private let tierColors: [String: Color] = [
        "T1": Color(hex: "FF6B6B"),
        "T2": Color(hex: "FFA94D"),
        "T3": Color(hex: "FFE066"),
        "T4": Color(hex: "69DB7C"),
        "T5": Color(hex: "74C0FC"),
    ]

    var body: some View {
        Text(tier)
            .font(.caption)
            .fontWeight(.bold)
            .foregroundColor(.white)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(tierColors[tier] ?? .gray)
            .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}

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

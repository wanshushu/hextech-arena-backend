import SwiftUI

struct ChampionDetailView: View {
    let championId: String

    @Environment(\.dismiss) private var dismiss
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
                                Button {
                                    dismiss()
                                } label: {
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
                        AugmentSelectorView(championId: championId, championAugments: champ.allAugments ?? champ.topAugments ?? [])

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
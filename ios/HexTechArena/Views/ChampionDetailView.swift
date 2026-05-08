import SwiftUI

struct ChampionDetailView: View {
    let championId: String

    @State private var champion: Champion?
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            if isLoading {
                ProgressView("加载中...")
                    .frame(maxWidth: .infinity, minHeight: 300)
            } else if let error = errorMessage {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)
                    Text(error)
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, minHeight: 300)
            } else if let champ = champion {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    VStack(spacing: 12) {
                        Circle()
                            .fill(Color.gray.opacity(0.3))
                            .frame(width: 80, height: 80)
                            .overlay(
                                Text(String(champ.name.prefix(1)))
                                    .font(.largeTitle)
                                    .fontWeight(.bold)
                            )

                        Text(champ.name)
                            .font(.title)
                            .fontWeight(.bold)

                        if !champ.title.isEmpty {
                            Text(champ.title)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }

                        HStack(spacing: 16) {
                            StatCard(title: "胜率", value: champ.winrate, color: .green)
                            StatCard(title: "选取率", value: champ.pickrate, color: .blue)
                            StatCard(title: "梯队", value: champ.tier, color: tierColor(champ.tier))
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color(.systemGroupedBackground))
                    .cornerRadius(16)

                    // Top Augments
                    if let augments = champ.topAugments, !augments.isEmpty {
                        SectionView(title: "海克斯强化", systemImage: "sparkles") {
                            ForEach(augments) { augment in
                                AugmentRowView(augment: augment)
                            }
                        }
                    }

                    // Core Items
                    if let items = champ.coreItems, !items.isEmpty {
                        SectionView(title: "核心装备", systemImage: "bag.fill") {
                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                            ], spacing: 12) {
                                ForEach(items, id: \.self) { item in
                                    ItemBadge(name: item)
                                }
                            }
                        }
                    }

                    // Situational Items
                    if let items = champ.situationalItems, !items.isEmpty {
                        SectionView(title: "情境装备", systemImage: "questionmark.circle.fill") {
                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                            ], spacing: 12) {
                                ForEach(items, id: \.self) { item in
                                    ItemBadge(name: item)
                                }
                            }
                        }
                    }

                    // Starting Items
                    if let items = champ.startingItems, !items.isEmpty {
                        SectionView(title: "出门装", systemImage: "house.fill") {
                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                            ], spacing: 12) {
                                ForEach(items, id: \.self) { item in
                                    ItemBadge(name: item)
                                }
                            }
                        }
                    }

                    if let patch = champ.patch, !patch.isEmpty {
                        HStack {
                            Spacer()
                            Text("数据来源: aram.gg | 版本 \(patch)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Spacer()
                        }
                    }
                }
                .padding()
            }
        }
        .navigationTitle(champion?.name ?? "英雄详情")
        .navigationBarTitleDisplayMode(.inline)
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

    private func tierColor(_ tier: String) -> Color {
        switch tier {
        case "T1": return Color(hex: "FF6B6B")
        case "T2": return Color(hex: "FFA94D")
        case "T3": return Color(hex: "FFE066")
        case "T4": return Color(hex: "69DB7C")
        case "T5": return Color(hex: "74C0FC")
        default: return .gray
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
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(Color(.secondarySystemGroupedBackground))
        .cornerRadius(10)
    }
}

struct SectionView<Content: View>: View {
    let title: String
    let systemImage: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label(title, systemImage: systemImage)
                .font(.headline)
                .foregroundColor(Color(hex: "673AB7"))

            content
        }
        .padding()
        .background(Color(.secondarySystemGroupedBackground))
        .cornerRadius(16)
    }
}

struct AugmentRowView: View {
    let augment: Augment

    var body: some View {
        HStack {
            Circle()
                .fill(Color.gray.opacity(0.3))
                .frame(width: 40, height: 40)
                .overlay(
                    Image(systemName: "sparkles")
                        .foregroundColor(Color(hex: "673AB7"))
                )

            VStack(alignment: .leading, spacing: 2) {
                Text(augment.name)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(augment.tier)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 2) {
                Text(augment.winrate)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundColor(.green)
                Text(augment.pickrate)
                    .font(.caption)
                    .foregroundColor(.secondary)
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
                .fill(Color.gray.opacity(0.3))
                .frame(width: 50, height: 50)
                .overlay(
                    Image(systemName: "shield.fill")
                        .foregroundColor(Color(hex: "673AB7"))
                )
            Text(name)
                .font(.caption2)
                .lineLimit(2)
                .multilineTextAlignment(.center)
        }
    }
}

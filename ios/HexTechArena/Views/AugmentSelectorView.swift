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

                if let onRefresh = onRefresh {
                    VStack {
                        Spacer()
                        HStack {
                            Spacer()
                            Button {
                                onRefresh()
                            } label: {
                                Image(systemName: "arrow.clockwise")
                                    .font(.system(size: 10))
                                    .foregroundColor(.esportsWarning)
                                    .padding(4)
                                    .background(Color.black.opacity(0.6))
                                    .clipShape(Circle())
                            }
                            .padding(4)
                        }
                    }
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

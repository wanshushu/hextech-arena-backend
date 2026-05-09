import SwiftUI

struct AugmentSelectorView: View {
    let championId: String
    let championAugments: [Augment]

    @State private var selectorState = AugmentSelectorState()
    @State private var showingPicker = false
    @State private var pickerTargetSlot: Int = 0

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

            Text("点击下方卡牌，选择游戏里出现的3个海克斯：")
                .font(.caption)
                .foregroundColor(.esportsTextSecondary)

            // 3 Augment Slots - always 3 slots
            HStack(spacing: 10) {
                ForEach(0..<3, id: \.self) { index in
                    let slot = index < selectorState.slots.count ? selectorState.slots[index] : nil
                    if let slot = slot {
                        AugmentSlotCard(
                            slot: slot,
                            isSelected: true,
                            onTap: {
                                pickerTargetSlot = index
                                showingPicker = true
                            },
                            onRefresh: slot.isRefreshed ? nil : {
                                selectorState.refreshSlot(at: index, allAugments: championAugments)
                            }
                        )
                    } else {
                        AugmentSlotEmpty(onTap: {
                            pickerTargetSlot = index
                            showingPicker = true
                        })
                    }
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
        .sheet(isPresented: $showingPicker) {
            AugmentPickerSheet(
                allAugments: championAugments,
                currentSlotAugment: pickerTargetSlot < selectorState.slots.count ? selectorState.slots[pickerTargetSlot].augmentName : nil
            ) { selectedAugment in
                let newSlot = AugmentSlotState(augmentName: selectedAugment.name, winrate: selectedAugment.winrate)
                if pickerTargetSlot < selectorState.slots.count {
                    selectorState.slots[pickerTargetSlot] = newSlot
                } else {
                    // Fill intermediate empty slots if needed
                    while selectorState.slots.count < pickerTargetSlot {
                        selectorState.slots.append(AugmentSlotState(augmentName: "", winrate: ""))
                    }
                    selectorState.slots.append(newSlot)
                }
                selectorState.isAnalyzed = false
            }
        }
    }
}

struct AugmentPickerSheet: View {
    let allAugments: [Augment]
    let currentSlotAugment: String?
    let onSelect: (Augment) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var selectedAugment: Augment?

    var body: some View {
        NavigationStack {
            ZStack {
                Color.esportsBg.ignoresSafeArea()
                ScrollView {
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        ForEach(allAugments) { augment in
                            let isCurrentlySelected = currentSlotAugment == augment.name
                            Button {
                                selectedAugment = augment
                            } label: {
                                VStack(spacing: 6) {
                                    Circle()
                                        .fill(isCurrentlySelected ? Color.esportsRecommend.opacity(0.2) : Color.esportsCard)
                                        .frame(width: 60, height: 60)
                                        .overlay(
                                            Image(systemName: "sparkles")
                                                .font(.system(size: 24))
                                                .foregroundColor(isCurrentlySelected ? .esportsRecommend : .esportsAccent)
                                        )
                                        .overlay(
                                            Circle()
                                                .stroke(isCurrentlySelected ? Color.esportsRecommend : Color.clear, lineWidth: 2)
                                        )

                                    Text(augment.name)
                                        .font(.caption)
                                        .foregroundColor(.esportsText)
                                        .lineLimit(2)
                                        .multilineTextAlignment(.center)

                                    Text(augment.winrate)
                                        .font(.caption2)
                                        .foregroundColor(.esportsRecommend)
                                }
                                .padding(8)
                                .background(Color.esportsCard)
                                .cornerRadius(12)
                            }
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("选择海克斯")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                        .foregroundColor(.esportsAccent)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("确定") {
                        if let augment = selectedAugment {
                            onSelect(augment)
                        }
                        dismiss()
                    }
                    .foregroundColor(.esportsRecommend)
                    .disabled(selectedAugment == nil)
                }
            }
        }
    }
}

struct AugmentSlotCard: View {
    let slot: AugmentSlotState
    let isSelected: Bool
    let onTap: () -> Void
    let onRefresh: (() -> Void)?

    var body: some View {
        VStack(spacing: 4) {
            Button(action: onTap) {
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(slot.isRefreshed ? Color.gray.opacity(0.3) : Color.esportsCard)
                        .frame(height: 70)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(slot.isRefreshed ? Color.gray : Color.esportsAccent, lineWidth: isSelected ? 2 : 1)
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
            }
            .buttonStyle(.plain)

            HStack(spacing: 4) {
                if slot.isRefreshed {
                    Text("已刷新")
                        .font(.system(size: 9))
                        .foregroundColor(.gray)
                } else if let onRefresh = onRefresh {
                    Button {
                        onRefresh()
                    } label: {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 10))
                            .foregroundColor(.esportsWarning)
                            .padding(4)
                            .background(Color.black.opacity(0.4))
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }
            }
            .frame(height: 16)
        }
    }
}

struct AugmentSlotEmpty: View {
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.esportsCard.opacity(0.5))
                    .frame(height: 70)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(style: StrokeStyle(lineWidth: 1, dash: [4]))
                            .foregroundColor(Color.esportsBorder)
                    )

                Image(systemName: "plus")
                    .font(.system(size: 24))
                    .foregroundColor(.esportsTextSecondary)
            }
        }
        .buttonStyle(.plain)
    }
}

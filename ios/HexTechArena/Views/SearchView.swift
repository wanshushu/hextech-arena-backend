import SwiftUI

struct SearchView: View {
    @State private var searchText = ""
    @State private var champions: [ChampionListItem] = []
    @State private var isLoading = false
    @State private var hasSearched = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if isLoading {
                    ProgressView("搜索中...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if champions.isEmpty && hasSearched {
                    ContentUnavailableView(
                        "未找到英雄",
                        systemImage: "magnifyingglass",
                        description: Text("尝试其他关键词")
                    )
                } else {
                    List(champions) { champion in
                        NavigationLink(destination: ChampionDetailView(championId: champion.id)) {
                            ChampionRowView(champion: champion)
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("搜索英雄")
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $searchText, prompt: "输入英雄名称")
            .onChange(of: searchText) { _, newValue in
                Task {
                    await search(query: newValue)
                }
            }
            .task {
                await loadInitial()
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

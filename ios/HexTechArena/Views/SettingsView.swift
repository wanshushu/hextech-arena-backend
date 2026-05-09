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

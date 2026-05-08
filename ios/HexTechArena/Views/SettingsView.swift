import SwiftUI

struct SettingsView: View {
    @State private var healthInfo: HealthResponse?
    @State private var isRefreshing = false
    @State private var showingAlert = false
    @State private var alertMessage = ""

    var body: some View {
        NavigationStack {
            List {
                Section("数据状态") {
                    if let health = healthInfo {
                        HStack {
                            Text("英雄数量")
                            Spacer()
                            Text("\(health.championCount)")
                                .foregroundColor(.secondary)
                        }

                        if let lastRefresh = health.lastRefresh {
                            HStack {
                                Text("最后更新")
                                Spacer()
                                Text(lastRefresh.timestamp)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }

                            HStack {
                                Text("更新状态")
                                Spacer()
                                Text(lastRefresh.status == "completed" ? "已完成" : lastRefresh.status)
                                    .foregroundColor(lastRefresh.status == "completed" ? .green : .orange)
                            }

                            HStack {
                                Text("本次爬取")
                                Spacer()
                                Text("\(lastRefresh.championsCrawled) 个英雄")
                                    .foregroundColor(.secondary)
                            }
                        }

                        if let counts = health.tierCounts as? [String: Int] {
                            HStack {
                                Text("T1 英雄")
                                Spacer()
                                Text("\(counts["T1"] ?? 0)")
                                    .foregroundColor(Color(hex: "FF6B6B"))
                            }
                            HStack {
                                Text("T2 英雄")
                                Spacer()
                                Text("\(counts["T2"] ?? 0)")
                                    .foregroundColor(Color(hex: "FFA94D"))
                            }
                        }
                    } else {
                        HStack {
                            ProgressView()
                            Text("加载中...")
                                .foregroundColor(.secondary)
                        }
                    }
                }

                Section("数据更新") {
                    Button {
                        Task { await triggerRefresh() }
                    } label: {
                        HStack {
                            if isRefreshing {
                                ProgressView()
                                    .padding(.trailing, 4)
                            }
                            Text(isRefreshing ? "更新中..." : "手动更新数据")
                        }
                    }
                    .disabled(isRefreshing)
                }

                Section("关于") {
                    HStack {
                        Text("App 版本")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("数据来源")
                        Spacer()
                        Text("aram.gg")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("后端地址")
                        Spacer()
                        Text("localhost:18789")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Section {
                    Link(destination: URL(string: "https://aramgg.com/zh-CN/champions")!) {
                        HStack {
                            Text("访问数据源网站")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("设置")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await loadHealth() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
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

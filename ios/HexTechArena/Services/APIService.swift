import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case networkError(Error)
    case decodingError(Error)
    case serverError(Int)
    case unknown

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "无效的 URL"
        case .networkError(let e): return "网络错误: \(e.localizedDescription)"
        case .decodingError(let e): return "数据解析错误: \(e.localizedDescription)"
        case .serverError(let code): return "服务器错误: \(code)"
        case .unknown: return "未知错误"
        }
    }
}

actor APIService {
    static let shared = APIService()

    // ⚠️ 修改为你电脑的 IP 地址
    private let baseURL = "http://localhost:18789"

    private var jsonDecoder: JSONDecoder {
        let decoder = JSONDecoder()
        return decoder
    }

    private init() {}

    // MARK: - Health
    func fetchHealth() async throws -> HealthResponse {
        let data = try await get("/health")
        return try jsonDecoder.decode(HealthResponse.self, from: data)
    }

    // MARK: - Tier List
    func fetchTierList() async throws -> TierListResponse {
        let data = try await get("/tier-list")
        return try jsonDecoder.decode(TierListResponse.self, from: data)
    }

    // MARK: - Champions
    func fetchChampions(tier: String? = nil, search: String? = nil, page: Int = 1) async throws -> ChampionSearchResponse {
        var queryItems: [String] = []
        if let tier = tier { queryItems.append("tier=\(tier)") }
        if let search = search, !search.isEmpty { queryItems.append("search=\(search.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? search)") }
        queryItems.append("page=\(page)")

        let path = "/champions" + (queryItems.isEmpty ? "" : "?\(queryItems.joined(separator: "&"))")
        let data = try await get(path)
        return try jsonDecoder.decode(ChampionSearchResponse.self, from: data)
    }

    // MARK: - Champion Detail
    func fetchChampionDetail(id: String) async throws -> Champion {
        let data = try await get("/champions/\(id)")
        return try jsonDecoder.decode(Champion.self, from: data)
    }

    // MARK: - Refresh
    func triggerRefresh() async throws {
        let _: Data = try await post("/refresh", body: [:])
    }

    // MARK: - Private
    private func get(_ path: String) async throws -> Data {
        guard let url = URL(string: baseURL + path) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.unknown
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError(httpResponse.statusCode)
        }

        return data
    }

    private func post(_ path: String, body: [String: Any]) async throws -> Data {
        guard let url = URL(string: baseURL + path) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        request.timeoutInterval = 30

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.unknown
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            throw APIError.serverError(httpResponse.statusCode)
        }

        return data
    }
}

import SwiftUI

extension Color {
    // E-Sports Theme Colors
    static let esportsBg = Color(hex: "0a0a0f")
    static let esportsCard = Color(hex: "12122a")
    static let esportsBorder = Color(hex: "222222")

    static let esportsT1 = Color(hex: "FF3366")
    static let esportsT2 = Color(hex: "FFA94D")
    static let esportsT3 = Color(hex: "FFE066")
    static let esportsT4 = Color(hex: "69DB7C")
    static let esportsT5 = Color(hex: "74C0FC")

    static let esportsAccent = Color(hex: "00f0ff")
    static let esportsRecommend = Color(hex: "00ff88")
    static let esportsWarning = Color(hex: "FF3366")
    static let esportsText = Color.white
    static let esportsTextSecondary = Color(hex: "888888")

    static func tierColor(_ tier: String) -> Color {
        switch tier {
        case "T1": return .esportsT1
        case "T2": return .esportsT2
        case "T3": return .esportsT3
        case "T4": return .esportsT4
        case "T5": return .esportsT5
        default: return .gray
        }
    }
}

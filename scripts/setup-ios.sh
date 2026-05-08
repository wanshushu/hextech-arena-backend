#!/bin/bash
set -e

echo "========================================"
echo "  HexTech Arena iOS 安装脚本"
echo "========================================"
echo ""

IOS_DIR="$(cd "$(dirname "$0")/.." && pwd)/ios"
cd "$IOS_DIR"

echo "[1/4] 检查 XcodeGen..."
if ! command -v xcodegen &> /dev/null; then
    echo "  正在安装 XcodeGen..."
    brew install xcodegen
else
    echo "  XcodeGen 已安装"
fi

echo ""
echo "[2/4] 生成 Xcode 项目..."
xcodegen generate
echo "  项目已生成: ios/HexTechArena.xcodeproj"

echo ""
echo "[3/4] 安装 CocoaPods 依赖..."
if [ -f "Podfile" ]; then
    pod install
else
    echo "  无 Podfile，跳过"
fi

echo ""
echo "[4/4] 打开项目..."
echo "  请在 Xcode 中打开: $IOS_DIR/HexTechArena.xcodeproj"
open "$IOS_DIR/HexTechArena.xcodeproj"

echo ""
echo "========================================"
echo "  安装完成!"
echo "========================================"
echo ""
echo "在 Xcode 中:"
echo "  1. 选择你的 iOS 设备或模拟器"
echo "  2. 按 Cmd+R 运行"
echo ""
echo "注意: 确保后端服务正在运行 (localhost:18789)"
echo ""

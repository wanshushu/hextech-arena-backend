#!/bin/bash
set -e

echo "========================================"
echo "  HexTech Arena Backend 安装脚本"
echo "========================================"
echo ""

BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BACKEND_DIR"

echo "[1/5] 检查 Python 版本..."
python3 --version

echo ""
echo "[2/5] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  虚拟环境已创建"
else
    echo "  虚拟环境已存在"
fi

echo ""
echo "[3/5] 安装依赖..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

echo ""
echo "[4/5] 安装 Playwright 浏览器..."
playwright install chromium

echo ""
echo "[5/5] 初始化数据库..."
source venv/bin/activate
python3 -c "from backend.database import init_db; init_db(); print('  数据库初始化完成')"

echo ""
echo "========================================"
echo "  安装完成!"
echo "========================================"
echo ""
echo "启动后端服务:"
echo "  cd $BACKEND_DIR"
echo "  source venv/bin/activate"
echo "  uvicorn backend.main:app --host 0.0.0.0 --port 18789 --reload"
echo ""
echo "或使用快捷命令:"
echo "  ./scripts/run-backend.sh"
echo ""

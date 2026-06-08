"""
PythonAnywhere WSGI 配置文件
部署时将此文件内容复制到 PythonAnywhere 的 WSGI 配置中
"""
import sys
import os

# 添加项目路径（修改为你的 PythonAnywhere 用户名）
project_home = '/home/YOUR_USERNAME/hextech-arena-backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置环境变量
# Riot API Key 从环境变量读取，不要硬编码
# os.environ['RIOT_API_KEY'] = 'your_key_here'

# 导入 FastAPI 应用
from backend.main import app
application = app

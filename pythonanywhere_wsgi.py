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
os.environ['RIOT_API_KEY'] = 'RGAPI-5de719fd-c7b0-490f-8b9a-34c66b58467f'

# 导入 FastAPI 应用
from backend.main import app
application = app

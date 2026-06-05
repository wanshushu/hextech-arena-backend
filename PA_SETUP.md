# PythonAnywhere 部署指南

## 1. 注册
- 去 https://www.pythonanywhere.com 注册免费账号
- 选 **Beginner** 免费套餐

## 2. 打开 Bash 终端
登录后点 **Dashboard → Bash**（打开一个终端）

## 3. 克隆代码
```bash
cd ~
git clone https://github.com/wanshushu/hextech-arena-backend.git
cd hextech-arena-backend
```

## 4. 安装依赖
```bash
pip3 install --user -r requirements.txt
```

## 5. 初始化数据库
```bash
python3 -c "
from backend.database import init_db
init_db()
print('DB initialized')
"
```

## 6. 拉取 Data Dragon 数据
```bash
python3 -c "
import asyncio
from backend.main import _refresh_ddragon
asyncio.run(_refresh_ddragon())
print('Done')
"
```

## 7. 创建 Web App
1. 点 **Web** 标签页
2. 点 **"Add a new web app"**
3. 选 **"Manual configuration"**
4. 选 **Python 3.10**（或可用的最高版本）
5. 点 Next

## 8. 配置 WSGI
1. 在 Web 页面找到 **"WSGI configuration file"** 链接，点进去
2. 把内容**全部删除**，替换为：

```python
import sys
import os

project_home = '/home/YOUR_USERNAME/hextech-arena-backend'  # 改成你的用户名
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['RIOT_API_KEY'] = 'RGAPI-5de719fd-c7b0-490f-8b9a-34c66b58467f'

from backend.main import app
application = app
```

## 9. 设置虚拟环境（可选但推荐）
在 Web 页面的 **Virtualenv** 部分填入：
```
/home/YOUR_USERNAME/.local/lib/python3.10/site-packages
```

## 10. 点击 "Reload"
刷新后你的 API 就上线了！

地址格式：`https://YOUR_USERNAME.pythonanywhere.com`

## 11. 更新小程序 API 地址
修改 `miniprogram/app.js`：
```javascript
apiBase: 'https://YOUR_USERNAME.pythonanywhere.com'
```

## 注意事项
- 免费账号**每3个月需要重新激活**（PythonAnywhere 会发邮件提醒）
- 免费账号**出站网络限制**：只能访问白名单域名
  - `ddragon.leagueoflegends.com` ✅（需要确认）
  - `asia.api.riotgames.com` ✅（需要确认）
  - `aramgg.com` ✅（需要确认）
- 如果某个域名被限制，需要在 Web → "T" 图标里添加

## 日常更新
```bash
cd ~/hextech-arena-backend
git pull
# 然后去 Web 页面点 Reload
```

## 更新 Riot API Key
```bash
# 编辑 WSGI 文件里的 RIOT_API_KEY
# 然后去 Web 页面点 Reload
```

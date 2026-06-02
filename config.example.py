import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# 系统配置
SYSTEM_URL = "https://your-system-url.com"
LOGIN_USERNAME = "your_username"
LOGIN_PASSWORD = "your_password"

# 测试用例文件
EXCEL_FILE = BASE_DIR.parent / "测试用例.xlsx"

# 飞书配置
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-id")

# 浏览器配置
HEADLESS = True
TIMEOUT = 30000  # 30秒

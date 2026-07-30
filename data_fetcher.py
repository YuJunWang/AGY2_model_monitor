import json
import random
import time
from datetime import datetime

# ==============================================================================
# Antigravity 2.0 API Data Fetcher (Mock for now)
# ==============================================================================
# 目前 Antigravity 的 agentapi 尚未開放直接獲取 Quota 的 public endpoint。
# 這裡先建立好資料結構與介面，當未來 Antigravity 支援 `agentapi get-quota` 時，
# 只要替換這個函式內的 `subprocess.run` 即可，完全不需要更動 UI 程式碼！
# ==============================================================================

def fetch_usage_data():
    """
    從 Antigravity 獲取模型使用量。
    回傳格式為字典，包含 Gemini 與 External 模型的 5小時及每週額度。
    """
    # 模擬向 API 發送請求的延遲
    time.sleep(0.5)
    
    # 模擬解析出來的資料結構
    mock_data = {
        "gemini": {
            "5hr_used": random.randint(10, 50),
            "5hr_limit": 50,
            "weekly_used": random.randint(100, 300),
            "weekly_limit": 500
        },
        "external": {
            "5hr_used": random.randint(0, 10),
            "5hr_limit": 20,
            "weekly_used": random.randint(20, 50),
            "weekly_limit": 100
        },
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 計算百分比
    mock_data["gemini"]["5hr_percent"] = int((mock_data["gemini"]["5hr_used"] / mock_data["gemini"]["5hr_limit"]) * 100)
    mock_data["gemini"]["weekly_percent"] = int((mock_data["gemini"]["weekly_used"] / mock_data["gemini"]["weekly_limit"]) * 100)
    mock_data["external"]["5hr_percent"] = int((mock_data["external"]["5hr_used"] / mock_data["external"]["5hr_limit"]) * 100)
    mock_data["external"]["weekly_percent"] = int((mock_data["external"]["weekly_used"] / mock_data["external"]["weekly_limit"]) * 100)
    
    return mock_data

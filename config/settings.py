"""
專案配置管理模組
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Settings:
    """應用程式設定類別"""
    
    # Discord 設定
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    DISCORD_CHANNEL_NAME: str = os.getenv('DISCORD_CHANNEL_NAME', '測試')
    
    # 機器人設定
    CHECK_INTERVAL_MIN: int = int(os.getenv('CHECK_INTERVAL_MIN', 5))
    CHECK_INTERVAL_MAX: int = int(os.getenv('CHECK_INTERVAL_MAX', 10))
    
    # 平台開關
    ENABLE_TIXCRAFT: bool = os.getenv('ENABLE_TIXCRAFT', 'true').lower() == 'true'
    ENABLE_KKTIX: bool = os.getenv('ENABLE_KKTIX', 'true').lower() == 'true'
    ENABLE_IBON: bool = os.getenv('ENABLE_IBON', 'true').lower() == 'true'
    
    @classmethod
    def validate(cls) -> bool:
        """驗證必要的設定是否存在"""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN 未設定")
        return True

# 全域設定實例
settings = Settings()
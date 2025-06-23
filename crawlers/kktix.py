"""
KKTIX 票券平台爬蟲
"""
import requests
import json
import re
from bs4 import BeautifulSoup
from typing import List
from .base import BaseCrawler, TicketInfo

class KktixCrawler(BaseCrawler):
    """KKTIX 票券爬蟲"""
    
    def check_availability(self, url: str) -> List[TicketInfo]:
        """
        檢查 KKTIX 票券可用性
        
        Args:
            url: KKTIX 票券頁面URL
            
        Returns:
            票券資訊列表
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取含有票務信息的 JavaScript 內容
            inventory_script = soup.find('script', string=re.compile('window.inventory'))
            
            if not inventory_script:
                return [TicketInfo(name="未知活動", status="找不到票務資訊", available=False)]
            
            script_content = inventory_script.get_text() if inventory_script else ""
            if not script_content:
                return [TicketInfo(name="未知活動", status="無法取得腳本內容", available=False)]
            
            inventory_data = re.search(
                r'window\.inventory\s*=\s*({.*?});', 
                script_content, 
                re.DOTALL
            )
            
            if not inventory_data:
                return [TicketInfo(name="未知活動", status="無法解析票務資訊", available=False)]
            
            inventory = json.loads(inventory_data.group(1))
            register_status = inventory['inventory']['registerStatus']
            
            # 取得活動名稱
            title_tag = soup.find('title')
            event_name = title_tag.text.strip() if title_tag else "未知活動"
            
            # 判斷票務狀態
            if register_status == "OUT_OF_STOCK":
                status = "很抱歉，這個活動目前無法購買。"
                available = False
            elif register_status == "SOLD_OUT":
                status = "很抱歉，這個活動已經售完。"
                available = False
            else:
                status = "這個活動目前還可以購買。"
                available = True
            
            return [TicketInfo(name=event_name, status=status, available=available)]
            
        except Exception as e:
            print(f"檢查 KKTIX 票務時出現錯誤: {e}")
            return [TicketInfo(name="錯誤", status=f"檢查失敗: {e}", available=False)]
"""
Tixcraft 票券平台爬蟲
"""
import requests
from bs4 import BeautifulSoup
from typing import List
from .base import BaseCrawler, TicketInfo

class TixcraftCrawler(BaseCrawler):
    """Tixcraft 票券爬蟲"""
    
    def check_availability(self, url: str) -> List[TicketInfo]:
        """
        檢查 Tixcraft 票券可用性
        
        Args:
            url: Tixcraft 票券頁面URL
            
        Returns:
            票券資訊列表
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 尋找所有包含活動信息的表格行
            rows = soup.find_all('tr', class_='gridc fcTxt')
            tickets = []
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    date = cells[0].text.strip()
                    event_name = cells[1].text.strip()
                    status_td = cells[3]
                    status = status_td.text.strip() if status_td else "Unknown"
                    
                    # 判斷是否有票
                    available = status not in ["Sold out", "Find ticketsNo tickets available"]
                    
                    ticket = TicketInfo(
                        name=event_name,
                        status=status,
                        date=date,
                        available=available
                    )
                    tickets.append(ticket)
            
            return tickets
            
        except Exception as e:
            print(f"檢查 Tixcraft 票務時出現錯誤: {e}")
            return []
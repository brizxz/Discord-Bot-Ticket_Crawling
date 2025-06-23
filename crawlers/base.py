"""
票券爬蟲基礎類別
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class TicketInfo:
    """票券資訊數據類別"""
    name: str
    status: str
    date: Optional[str] = None
    price: Optional[str] = None
    available: bool = False

class BaseCrawler(ABC):
    """票券爬蟲基礎類別"""
    
    def __init__(self, urls: Dict[str, str]):
        """
        初始化爬蟲
        
        Args:
            urls: 事件名稱與URL的對應字典
        """
        self.urls = urls
    
    @abstractmethod
    def check_availability(self, url: str) -> List[TicketInfo]:
        """
        檢查指定URL的票券可用性
        
        Args:
            url: 要檢查的票券頁面URL
            
        Returns:
            票券資訊列表
        """
        pass
    
    def check_all_events(self) -> Dict[str, List[TicketInfo]]:
        """
        檢查所有事件的票券狀態
        
        Returns:
            事件名稱與票券資訊的對應字典
        """
        results = {}
        for event_name, url in self.urls.items():
            try:
                results[event_name] = self.check_availability(url)
            except Exception as e:
                print(f"檢查 {event_name} 時發生錯誤: {e}")
                results[event_name] = []
        return results
    
    def get_available_tickets(self) -> Dict[str, List[TicketInfo]]:
        """
        獲取所有有票的事件
        
        Returns:
            有票的事件名稱與票券資訊的對應字典
        """
        all_results = self.check_all_events()
        available_results = {}
        
        for event_name, tickets in all_results.items():
            available_tickets = [ticket for ticket in tickets if ticket.available]
            if available_tickets:
                available_results[event_name] = available_tickets
                
        return available_results
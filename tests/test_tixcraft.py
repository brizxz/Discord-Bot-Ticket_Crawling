#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tixcraft 爬蟲測試
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.tixcraft import TixcraftCrawler
from const.ticket import TICKET_URL1

def test_tixcraft_crawler():
    """測試 Tixcraft 爬蟲"""
    print("測試 Tixcraft 爬蟲...")
    
    crawler = TixcraftCrawler(TICKET_URL1)
    
    for event_name, url in TICKET_URL1.items():
        print(f"\n測試活動：{event_name}")
        print(f"URL: {url}")
        
        tickets = crawler.check_availability(url)
        
        if tickets:
            print(f"找到 {len(tickets)} 個票券資訊：")
            for i, ticket in enumerate(tickets, 1):
                print(f"  {i}. {ticket.name} ({ticket.date})")
                print(f"     狀態: {ticket.status}")
                print(f"     可購買: {'是' if ticket.available else '否'}")
        else:
            print("沒有找到票券資訊")
        
        print("-" * 50)

if __name__ == "__main__":
    test_tixcraft_crawler()
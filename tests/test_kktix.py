#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KKTIX 爬蟲測試
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.kktix import KktixCrawler
from const.kktix import KKTIX_URL

def test_kktix_crawler():
    """測試 KKTIX 爬蟲"""
    print("測試 KKTIX 爬蟲...")
    
    crawler = KktixCrawler(KKTIX_URL)
    
    for event_name, url in KKTIX_URL.items():
        print(f"\n測試活動：{event_name}")
        print(f"URL: {url}")
        
        tickets = crawler.check_availability(url)
        
        if tickets:
            print(f"找到 {len(tickets)} 個票券資訊：")
            for i, ticket in enumerate(tickets, 1):
                print(f"  {i}. {ticket.name}")
                print(f"     狀態: {ticket.status}")
                print(f"     可購買: {'是' if ticket.available else '否'}")
        else:
            print("沒有找到票券資訊")
        
        print("-" * 50)

if __name__ == "__main__":
    test_kktix_crawler()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
from bs4 import BeautifulSoup
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from const.ibon import TICKET_URLibon

def break_shadow_dom(driver):
    """
    打開shadow-root(closed)的函數
    """
    script = """
    (function() {
    const originalAttachShadow = Element.prototype.attachShadow;
    Element.prototype.attachShadow = function(options) {
        if (options && options.mode === 'closed') {
        options.mode = 'open';
        }
        return originalAttachShadow.call(this, options);
    };
    })();
    """

    # 注意：要在 get() 之前執行
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": script}
    )

def test_check_ibon_ticket_availability(url):
    """
    測試ibon票務狀態檢查功能，使用Selenium打開shadow DOM
    """
    options = Options()
    options.add_argument('--headless')  # 無頭模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    driver = None
    try:
        print(f"正在初始化Chrome WebDriver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        print("正在執行shadow DOM打開腳本...")
        break_shadow_dom(driver)
        
        print(f"正在請求URL: {url}")
        driver.get(url)
        
        # 檢查是否有警告對話框
        try:
            # 嘗試切換到警告
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"遇到警告框：{alert_text}")
            
            # 視為無票，結束測試
            print(f"檢測到警告訊息，視為無票：{alert_text}")
            
            # 保存截圖供後續分析
            try:
                driver.save_screenshot(f'ibon_alert_{url.split("=")[1][:8]}.png')
                print(f"警告截圖已保存為 ibon_alert_{url.split('=')[1][:8]}.png")
            except:
                pass
                
            return
        except:
            # 沒有警告框，繼續執行
            pass
            
        time.sleep(3)  # 等待頁面完全加載
        
        print(f"頁面標題: {driver.title}")
        
        # 首先嘗試從script標籤中提取JSON數據
        print("搜尋含有票務資訊的JavaScript...")
        json_data_elements = driver.find_elements(By.XPATH, "//script[contains(text(), 'jsonData')]")
        json_data_str = None
        
        for elem in json_data_elements:
            script_content = elem.get_attribute('textContent')
            if 'jsonData = ' in script_content:
                print("找到含有jsonData的script標籤")
                match = re.search(r'jsonData\s*=\s*\'(\[.*?\])\';', script_content, re.DOTALL)
                if match:
                    json_data_str = match.group(1)
                    print("成功提取jsonData")
                    break
        
        # 如果找到JSON數據，則解析它
        if json_data_str:
            json_data_str = json_data_str.replace('\\"', '"')
            print(f"JSON長度: {len(json_data_str)} 字符")
            print(f"JSON片段: {json_data_str[:100]}...")
            
            try:
                tickets = json.loads(json_data_str)
                print(f"解析到 {len(tickets)} 個票區")
                
                available_tickets = [ticket for ticket in tickets if ticket.get('AMOUNT') != '已售完' and ticket.get('BACKGROUND_COLOR') != 'disabled']
                
                if available_tickets:
                    print(f"有 {len(available_tickets)} 個票區有票!")
                    for i, ticket in enumerate(available_tickets[:5]):
                        print(f"票區 {i+1}: {ticket['NAME']}, 狀態: {ticket.get('AMOUNT', '未知')}")
                else:
                    print("所有票區已售完")
                    
                # 印出前幾個票區的資訊
                print("\n票區範例:")
                for i, ticket in enumerate(tickets[:3]):
                    print(f"{i+1}. 名稱: {ticket.get('NAME')}, 價格: {ticket.get('PRICE_STR')}, 狀態: {ticket.get('AMOUNT')}")
            except json.JSONDecodeError as e:
                print(f"JSON解析錯誤: {e}")
        
        # 嘗試從shadow DOM中獲取票區信息
        print("\n嘗試從shadow DOM中獲取票區信息...")
        shadow_elements = driver.execute_script("""
            const roots = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) {
                    roots.push(el.shadowRoot);
                    console.log('找到shadow root:', el.tagName);
                }
            });
            
            console.log('找到', roots.length, '個shadow roots');
            
            let ticketInfo = [];
            for (const root of roots) {
                const tickets = root.querySelectorAll('.ticket-item, .area-item');
                console.log('在shadow root中找到', tickets.length, '個票區元素');
                
                if (tickets.length > 0) {
                    tickets.forEach(ticket => {
                        const name = ticket.querySelector('.name')?.textContent;
                        const status = ticket.querySelector('.status')?.textContent || 
                                     ticket.querySelector('.amount')?.textContent;
                        if (name && status) {
                            ticketInfo.push({name, status});
                        }
                    });
                }
            }
            return ticketInfo;
        """)
        
        if shadow_elements and len(shadow_elements) > 0:
            print(f"從shadow DOM中找到 {len(shadow_elements)} 個票區元素")
            for i, ticket in enumerate(shadow_elements[:5]):
                print(f"{i+1}. 名稱: {ticket.get('name')}, 狀態: {ticket.get('status')}")
                
            available_tickets = [ticket for ticket in shadow_elements 
                                if ticket.get('status') and '售完' not in ticket.get('status')]
            
            if available_tickets:
                print(f"\n有 {len(available_tickets)} 個票區有票!")
                for i, ticket in enumerate(available_tickets[:5]):
                    print(f"票區 {i+1}: {ticket['name']}, 狀態: {ticket['status']}")
            else:
                print("\n所有票區已售完")
        else:
            print("在shadow DOM中沒有找到票區元素")
            
        # 檢查所有shadow roots
        print("\n列出所有shadow roots:")
        all_shadow_elements = driver.execute_script("""
            const roots = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) {
                    roots.push({
                        tag: el.tagName,
                        id: el.id,
                        class: el.className,
                        childrenCount: el.shadowRoot.childElementCount
                    });
                }
            });
            return roots;
        """)
        
        if all_shadow_elements:
            print(f"找到 {len(all_shadow_elements)} 個shadow roots元素")
            for i, elem in enumerate(all_shadow_elements[:5]):
                print(f"{i+1}. 標籤: {elem.get('tag')}, ID: {elem.get('id')}, 類名: {elem.get('class')}, 子元素數: {elem.get('childrenCount')}")
        else:
            print("沒有找到shadow roots")
        
        # 截圖保存
        print("\n保存截圖...")
        driver.save_screenshot(f'ibon_{url.split("=")[1][:8]}.png')
        print(f"截圖已保存為 ibon_{url.split('=')[1][:8]}.png")
        
    except Exception as e:
        print(f"測試過程中出現錯誤: {e}")
    
    finally:
        try:
            driver.quit()
            print("WebDriver已關閉")
        except:
            pass

def main():
    # 測試所有ibon URL
    for event_name, url in TICKET_URLibon.items():
        print("\n" + "="*50)
        print(f"測試活動: {event_name}")
        test_check_ibon_ticket_availability(url)
        print("="*50)

if __name__ == "__main__":
    main()
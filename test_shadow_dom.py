#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

def find_shadow_elements(url):
    """
    專門尋找和分析shadow DOM元素
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
            
            # 視為無票，結束分析
            print(f"檢測到警告訊息，視為無法分析：{alert_text}")
            
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
            
        time.sleep(5)  # 多等待幾秒確保頁面完全加載
        
        print(f"頁面標題: {driver.title}")
        
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
            for i, elem in enumerate(all_shadow_elements):
                print(f"{i+1}. 標籤: {elem.get('tag')}, ID: {elem.get('id')}, 類名: {elem.get('class')}, 子元素數: {elem.get('childrenCount')}")
        else:
            print("沒有找到shadow roots")
        
        # 遍歷每個shadow root並檢查其內部結構
        print("\n分析每個shadow root的內部結構:")
        shadow_structures = driver.execute_script("""
            const results = [];
            let index = 0;
            
            document.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) {
                    // 基本信息
                    const info = {
                        index: index++,
                        tag: el.tagName,
                        id: el.id || '(無id)',
                        class: el.className || '(無class)',
                        
                        // 分析內部結構
                        elements: {},
                        
                        // 尋找特定元素
                        ticketItems: []
                    };
                    
                    // 計算各種元素類型的數量
                    const shadow = el.shadowRoot;
                    const allElements = shadow.querySelectorAll('*');
                    const tags = {};
                    
                    allElements.forEach(elem => {
                        const tag = elem.tagName.toLowerCase();
                        tags[tag] = (tags[tag] || 0) + 1;
                    });
                    
                    info.elements = tags;
                    
                    // 尋找可能的票區信息
                    const ticketContainers = [
                        ...shadow.querySelectorAll('.ticket-item, .area-item, .ticket-container, .area-container, [class*="ticket"], [class*="area"]')
                    ];
                    
                    ticketContainers.forEach(container => {
                        // 嘗試找到票區名稱和狀態
                        const nameElem = container.querySelector('.name, .title, h3, h4, [class*="name"], [class*="title"]');
                        const statusElem = container.querySelector('.status, .amount, .availability, [class*="status"], [class*="amount"], [class*="availability"]');
                        
                        if (nameElem || statusElem) {
                            info.ticketItems.push({
                                name: nameElem ? nameElem.textContent.trim() : '(未找到名稱)',
                                status: statusElem ? statusElem.textContent.trim() : '(未找到狀態)',
                                containerClass: container.className,
                                html: container.innerHTML.substring(0, 150) + '...'  // 前150個字符
                            });
                        }
                    });
                    
                    // 如果沒找到明確的票區元素，嘗試其他方法
                    if (info.ticketItems.length === 0) {
                        // 尋找表格
                        const tables = shadow.querySelectorAll('table');
                        if (tables.length > 0) {
                            info.hasTables = tables.length;
                            
                            // 獲取第一個表格的內容
                            if (tables[0]) {
                                const rows = tables[0].querySelectorAll('tr');
                                const tableData = [];
                                
                                rows.forEach((row, i) => {
                                    if (i < 5) {  // 只獲取前5行
                                        const cells = row.querySelectorAll('td');
                                        const rowData = [];
                                        
                                        cells.forEach(cell => {
                                            rowData.push(cell.textContent.trim());
                                        });
                                        
                                        tableData.push(rowData);
                                    }
                                });
                                
                                info.tablePreview = tableData;
                            }
                        }
                    }
                    
                    results.push(info);
                }
            });
            
            return results;
        """)
        
        if shadow_structures:
            print(f"分析了 {len(shadow_structures)} 個shadow roots的內部結構")
            
            for structure in shadow_structures:
                print(f"\nShadow Root #{structure.get('index')} - {structure.get('tag')} (ID: {structure.get('id')}, Class: {structure.get('class')})")
                
                # 顯示元素統計
                elements = structure.get('elements', {})
                if elements:
                    print("元素統計:")
                    for tag, count in elements.items():
                        print(f"  - {tag}: {count}個")
                
                # 顯示找到的票區信息
                ticket_items = structure.get('ticketItems', [])
                if ticket_items:
                    print(f"找到 {len(ticket_items)} 個可能的票區信息:")
                    for i, item in enumerate(ticket_items[:5]):  # 只顯示前5個
                        print(f"  {i+1}. 名稱: {item.get('name')}, 狀態: {item.get('status')}")
                        print(f"     容器類名: {item.get('containerClass')}")
                        print(f"     HTML預覽: {item.get('html')[:100]}...")
                
                # 顯示表格預覽
                if structure.get('hasTables'):
                    print(f"找到 {structure.get('hasTables')} 個表格")
                    table_preview = structure.get('tablePreview', [])
                    if table_preview:
                        print("表格內容預覽:")
                        for row in table_preview:
                            print(f"  {' | '.join(row)}")
        
        # 截圖保存
        print("\n保存截圖...")
        driver.save_screenshot(f'ibon_shadow_{url.split("=")[1][:8]}.png')
        print(f"截圖已保存為 ibon_shadow_{url.split('=')[1][:8]}.png")
        
        # 完整頁面源碼保存
        with open(f'ibon_source_{url.split("=")[1][:8]}.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"頁面源碼已保存為 ibon_source_{url.split('=')[1][:8]}.html")
        
    except Exception as e:
        print(f"分析過程中出現錯誤: {e}")
    
    finally:
        try:
            driver.quit()
            print("WebDriver已關閉")
        except:
            pass

def main():
    # 只測試第一個URL
    if TICKET_URLibon:
        event_name, url = next(iter(TICKET_URLibon.items()))
        print(f"\n{'='*50}")
        print(f"分析活動: {event_name}")
        find_shadow_elements(url)
        print(f"{'='*50}")

if __name__ == "__main__":
    main() 
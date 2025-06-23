# -*- coding: utf-8 -*-
"""
原始的 Discord Bot 程式碼 (已重構)

此檔案保留作為參考，新的模組化程式碼位於：
- bot/discord_bot.py - 主要 Bot 邏輯
- crawlers/ - 各平台爬蟲實現
- config/settings.py - 配置管理

使用方法：
python main.py
"""

# 原始程式碼已移動到新的模組化結構中
# 請使用 main.py 來啟動程式

import discord
import asyncio
import requests
from bs4 import BeautifulSoup
import time
import re
import json
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from const.ticket import *
from const.kktix import *
from const.ibon import *

# Discord Bot Token
# TOKEN = "MTMzMzA3MDEwODkwOTc****2NDY1OA.Ga9uZ1._EettM*OS****ZAlIwT-kI4***7WUzT5OWb****wE3ogUng4Js"

# 初始化 Bot
intents = discord.Intents.default()
intents.messages = True
bot = discord.Client(intents=intents)

def check_ticket_availability(url):
    """
    檢查票務狀態的函數
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 尋找所有包含活動信息的表格行
    rows = soup.find_all('tr', class_='gridc fcTxt')
    ticket_info = []  # 保存所有活動信息
    for row in rows:
        # 提取日期、活動名稱和狀態
        date = row.find_all('td')[0].text.strip()
        event_name = row.find_all('td')[1].text.strip()
        status_td = row.find_all('td')[3]
        status = status_td.text.strip() if status_td else "Unknown"
        
        ticket_info.append((date, event_name, status))
    
    return ticket_info

def check_kk_ticket_availability(url):
    """
    檢查 KKTIX 活動票務狀態
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 提取含有票務信息的 JavaScript 內容
    inventory_script = soup.find('script', string=re.compile('window.inventory'))

    if inventory_script:
        inventory_data = re.search(r'window\.inventory\s*=\s*({.*?});', inventory_script.string, re.DOTALL)
        if inventory_data:
            inventory = json.loads(inventory_data.group(1))
            register_status = inventory['inventory']['registerStatus']

            if register_status == "OUT_OF_STOCK":
                return "很抱歉，這個活動目前無法購買。"
            elif register_status == "SOLD_OUT":
                return "很抱歉，這個活動已經售完。" 
            else:
                return "這個活動目前還可以購買。"
        else:
            return "無法解析 inventory 數據。"
    else:
        return "找不到 inventory 數據。"

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

def check_ibon_ticket_availability(url):
    """
    檢查 ibon 票務狀態，使用 Selenium 來獲取 shadow DOM 內容
    """
    options = Options()
    options.add_argument('--headless')  # 無頭模式
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    # 移除不支持的選項
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # 執行打開shadow DOM的script
        break_shadow_dom(driver)
        
        # 訪問URL
        driver.get(url)
        
        # 檢查是否有警告對話框
        try:
            # 嘗試切換到警告
            alert = driver.switch_to.alert
            alert_text = alert.text
            print(f"遇到警告框：{alert_text}")
            
            # 關閉瀏覽器並直接返回無票信息
            if driver:
                driver.quit()
            return f"檢測到警告訊息，視為無票：{alert_text}"
        except:
            # 沒有警告框，繼續執行
            pass
        
        time.sleep(3)  # 等待頁面完全加載
        
        # 綜合分析方法，結合JSON分析和shadow DOM分析
        ticket_status = driver.execute_script("""
            // 結果對象
            const result = {
                fromJson: null,
                fromShadow: null,
                fromTable: null
            };
            
            // 方法1: 從JSON數據分析
            try {
                let jsonData = null;
                const scripts = document.querySelectorAll('script');
                
                for (const script of scripts) {
                    const content = script.textContent || '';
                    if (content.includes('jsonData = ')) {
                        const match = content.match(/jsonData\\s*=\\s*'(\\[.*?\\])';/s);
                        if (match && match[1]) {
                            jsonData = JSON.parse(match[1]);
                            break;
                        }
                    }
                }
                
                if (jsonData) {
                    const availableTickets = jsonData.filter(
                        ticket => ticket.AMOUNT !== '已售完' && ticket.BACKGROUND_COLOR !== 'disabled'
                    );
                    
                    if (availableTickets.length > 0) {
                        result.fromJson = {
                            available: true,
                            count: availableTickets.length,
                            areas: availableTickets.map(t => t.NAME).slice(0, 5)
                        };
                    } else {
                        result.fromJson = {
                            available: false,
                            message: "所有票區已售完"
                        };
                    }
                }
            } catch (e) {
                console.error('JSON分析錯誤:', e);
            }
            
            // 方法2: 從shadow DOM分析
            try {
                const shadowTickets = [];
                
                document.querySelectorAll('*').forEach(el => {
                    if (el.shadowRoot) {
                        const shadow = el.shadowRoot;
                        
                        // 尋找可能的票區信息容器
                        const containers = shadow.querySelectorAll(
                            '.ticket-item, .area-item, .ticket-container, .area-container, ' +
                            '[class*="ticket"], [class*="area"], tr.gridc'
                        );
                        
                        containers.forEach(container => {
                            const nameElem = container.querySelector(
                                '.name, .title, h3, h4, [class*="name"], [class*="title"], td:first-child'
                            );
                            const statusElem = container.querySelector(
                                '.status, .amount, .availability, [class*="status"], [class*="amount"], td:nth-child(4)'
                            );
                            
                            if (nameElem || statusElem) {
                                const name = nameElem ? nameElem.textContent.trim() : '未知票區';
                                const status = statusElem ? statusElem.textContent.trim() : '未知狀態';
                                
                                shadowTickets.push({name, status});
                            }
                        });
                    }
                });
                
                if (shadowTickets.length > 0) {
                    // 排除已售完的票區
                    const availableShadowTickets = shadowTickets.filter(
                        ticket => !ticket.status.includes('售完') && 
                                !ticket.status.includes('Sold out') &&
                                !ticket.status.includes('disabled')
                    );
                    
                    if (availableShadowTickets.length > 0) {
                        result.fromShadow = {
                            available: true,
                            count: availableShadowTickets.length,
                            areas: availableShadowTickets.map(t => t.name).slice(0, 5)
                        };
                    } else {
                        result.fromShadow = {
                            available: false,
                            message: "shadow DOM分析：所有票區已售完"
                        };
                    }
                }
            } catch (e) {
                console.error('Shadow DOM分析錯誤:', e);
            }
            
            // 方法3: 直接從頁面表格分析
            try {
                const tables = document.querySelectorAll('table');
                const areaTable = Array.from(tables).find(table => 
                    table.id === 'AreaTable' || 
                    table.className.includes('area') || 
                    table.querySelector('tr.gridc')
                );
                
                if (areaTable) {
                    const rows = areaTable.querySelectorAll('tr.gridc');
                    const tableTickets = [];
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 4) {
                            const name = cells[1].textContent.trim();
                            const status = cells[3].textContent.trim();
                            tableTickets.push({name, status});
                        }
                    });
                    
                    if (tableTickets.length > 0) {
                        // 排除已售完的票區
                        const availableTableTickets = tableTickets.filter(
                            ticket => !ticket.status.includes('售完') && 
                                    !ticket.status.includes('Sold out')
                        );
                        
                        if (availableTableTickets.length > 0) {
                            result.fromTable = {
                                available: true,
                                count: availableTableTickets.length,
                                areas: availableTableTickets.map(t => t.name).slice(0, 5)
                            };
                        } else {
                            result.fromTable = {
                                available: false,
                                message: "表格分析：所有票區已售完"
                            };
                        }
                    }
                }
            } catch (e) {
                console.error('表格分析錯誤:', e);
            }
            
            return result;
        """)
        
        # 綜合分析結果
        available = False
        message = "無法確定票務狀態"
        areas = []
        
        # 優先使用JSON分析結果
        if ticket_status.get('fromJson'):
            json_result = ticket_status['fromJson']
            if json_result.get('available'):
                available = True
                areas = json_result.get('areas', [])
                message = f"有票可購買！可用票區: {', '.join(areas)}{'...' if len(areas) >= 5 else ''}"
            else:
                message = json_result.get('message', "所有票區已售完")
        
        # 如果JSON分析沒有結果，使用shadow DOM分析結果
        elif ticket_status.get('fromShadow'):
            shadow_result = ticket_status['fromShadow']
            if shadow_result.get('available'):
                available = True
                areas = shadow_result.get('areas', [])
                message = f"有票可購買！可用票區: {', '.join(areas)}{'...' if len(areas) >= 5 else ''}"
            else:
                message = shadow_result.get('message', "所有票區已售完")
        
        # 如果前兩種方法都沒有結果，使用表格分析結果
        elif ticket_status.get('fromTable'):
            table_result = ticket_status['fromTable']
            if table_result.get('available'):
                available = True
                areas = table_result.get('areas', [])
                message = f"有票可購買！可用票區: {', '.join(areas)}{'...' if len(areas) >= 5 else ''}"
            else:
                message = table_result.get('message', "所有票區已售完")
        
        # 如果有票可購買，保存截圖作為證據
        if available:
            try:
                screenshot_file = f'ibon_available_{time.strftime("%Y%m%d_%H%M%S")}.png'
                driver.save_screenshot(screenshot_file)
                print(f"發現有票！已保存截圖: {screenshot_file}")
            except Exception as e:
                print(f"保存截圖時出錯: {e}")
        
        return message
    
    except Exception as e:
        print(f"檢查ibon票務時出現錯誤: {e}")
        return f"檢查票務時出現錯誤: {e}"
    
    finally:
        try:
            if driver:
                driver.quit()
        except:
            pass

async def check_tickets():
    """
    Discord Bot 的任務函數，用於檢查票務狀態並發送通知。
    """
    await bot.wait_until_ready()
    channel = discord.utils.get(bot.get_all_channels(), name="測試")  # 替換為您的頻道名稱

    if not channel:
        print("無法找到通知頻道！請確認頻道名稱是否正確。")
        return

    while True:
        try:
            tou = True
            if tou is True:
                for event_name, url in TICKET_URL1.items():
                    ticket_info = check_ticket_availability(url)
                    print(ticket_info)
                    for date, event, status in ticket_info:
                        if status in ["Sold out", "Find ticketsNo tickets available"]:
                            # 可以選擇不通知售罄的活動
                            continue
                        elif status == "Find tickets":
                            # 發送通知
                            await channel.send(f"🎟️ {date} - {event} 現在有票了！快去購買！\n網址: {url}")
                        else:
                            print(f"{date} - {event}: 狀態未知 ({status})")
            kk = True
            if kk is True:
                for event_name, url in KKTIX_URL.items():
                    status = check_kk_ticket_availability(url)
                    if status == "這個活動目前還可以購買。":
                        # 發送通知
                        await channel.send(f"🎟️ {event_name} 現在有票了！快去購買！\n網址: {url}")
                    else:
                        print(f"{event_name}: {status}")
            ib = True
            if ib is True:
                for event_name, url in TICKET_URLibon.items():
                    status = check_ibon_ticket_availability(url)
                    print(f"{event_name}: {status}")
                    if "有票可購買" in status:
                        # 發送通知
                        await channel.send(f"🎟️ {event_name} 現在有票了！{status}\n網址: {url}")
            
        except Exception as e:
            print(f"檢查票務時出現錯誤：{e}")
        
        # 每 60 秒檢查一次
        await asyncio.sleep(random.randint(5,10))


@bot.event
async def on_ready():
    """
    Bot 啟動時的事件
    """
    print(f"{bot.user} 已上線！")
    # 啟動檢查票務狀態的任務
    bot.loop.create_task(check_tickets())


# 啟動 Bot
async def main():
    async with bot:
        await bot.start(TOKEN)

# 注意：此檔案已不再使用，請使用 python main.py 啟動新版本
if __name__ == "__main__":
    print("此版本已過時，請使用以下指令啟動新版本：")
    print("python main.py")
    print("或參考 README.md 進行設定")
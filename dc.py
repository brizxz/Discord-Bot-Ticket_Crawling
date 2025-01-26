import discord
import asyncio
import requests
from bs4 import BeautifulSoup
import time
import re
import json

from const.ticket import *
from const.kktix import *

# Discord Bot Token
TOKEN = "replace with your token"

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



async def check_tickets():
    """
    Discord Bot 的任務函數，用於檢查票務狀態並發送通知。
    """
    await bot.wait_until_ready()
    channel = discord.utils.get(bot.get_all_channels(), name="一般")  # 替換為您的頻道名稱

    if not channel:
        print("無法找到通知頻道！請確認頻道名稱是否正確。")
        return

    while True:
        try:
            tou = False
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
                
        except Exception as e:
            print(f"檢查票務時出現錯誤：{e}")
        
        # 每 60 秒檢查一次
        await asyncio.sleep(10)


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

asyncio.run(main())

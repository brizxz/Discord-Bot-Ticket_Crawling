import requests
from bs4 import BeautifulSoup
import json
import re
import time
import subprocess

from const.ticket import *

def send_notification(event_name):
    try:
        subprocess.run(['notify-send', '票務通知', f'{event_name} 現在有票可以購買！'])
    except FileNotFoundError:
        print(f"無法發送通知：{event_name} 現在有票可以購買！")

def check_ticket_availability(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 尋找所有包含活動信息的表格行
    rows = soup.find_all('tr', class_='gridc fcTxt')
    for row in rows:
        # 提取日期、活動名稱和狀態
        date = row.find_all('td')[0].text.strip()
        event_name = row.find_all('td')[1].text.strip()
        status_td = row.find_all('td')[3]
        status = status_td.text.strip() if status_td else "Unknown"
        print(f"日期: {date}")
        print(f"活動名稱: {event_name}")
        print(f"狀態: {status}")
        print("---")

        if status == "Sold out":
            print(f"{date} - {event_name}: 很抱歉，這個活動已經售完。")
        else:
            send_notification(event_name)

    

while True:
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}")
    for event_name, url in TICKET_URL.items():
        print(f"檢查活動: {event_name}")
        check_ticket_availability(url)
        
        
        time.sleep(10)

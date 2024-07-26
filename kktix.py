import requests
from bs4 import BeautifulSoup
import json
import re
import time
import subprocess

from const.kktix import *

def check_ticket_availability(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

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

def send_notification(event_name):
    try:
        subprocess.run(['notify-send', '票務通知', f'{event_name} 現在有票可以購買！'])
    except FileNotFoundError:
        print(f"無法發送通知：{event_name} 現在有票可以購買！")


while True:
    for event_name, url in KKTIX_URL.items():
        print(f"檢查活動: {event_name}")
        result = check_ticket_availability(url)
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {result}")
        
        if result == "這個活動目前還可以購買。":
            send_notification(event_name)
    
    time.sleep(10)

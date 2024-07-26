import requests
from bs4 import BeautifulSoup
import json
import re
import time

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
            else:
                return "這個活動目前還可以購買。"
        else:
            return "無法解析 inventory 數據。"
    else:
        return "找不到 inventory 數據。"

url = "https://kktix.com/events/84607d15/registrations/new"

while True:
    result = check_ticket_availability(url)
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {result}")
    time.sleep(10)

# ... existing code ...

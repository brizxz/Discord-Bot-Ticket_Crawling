#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord Bot 票券爬蟲主程式
使用方法：
1. 複製 .env.example 為 .env
2. 在 .env 中設定您的 Discord Bot Token
3. 執行：python main.py
"""
import asyncio
from bot import TicketBot

if __name__ == "__main__":
    print("Discord Bot 票券爬蟲啟動中...")
    print("請確認您已經設定好 .env 檔案中的 DISCORD_TOKEN")
    
    try:
        asyncio.run(TicketBot().start())
    except KeyboardInterrupt:
        print("\n收到中斷信號，正在關閉程式...")
    except Exception as e:
        print(f"程式執行出現錯誤：{e}")
        print("請檢查設定檔案和網路連線")
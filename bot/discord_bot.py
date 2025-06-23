"""
Discord Bot 票券監控主程式
"""
import discord
import asyncio
import random
from typing import Dict, Any
from config.settings import settings
from crawlers import TixcraftCrawler, KktixCrawler, IbonCrawler
from const.ticket import TICKET_URL1
from const.kktix import KKTIX_URL
from const.ibon import TICKET_URLibon

class TicketBot:
    """票券監控 Discord Bot"""
    
    def __init__(self):
        """初始化 Bot"""
        # 驗證設定
        settings.validate()
        
        # 初始化 Discord Bot
        intents = discord.Intents.default()
        intents.messages = True
        self.bot = discord.Client(intents=intents)
        
        # 初始化爬蟲
        self.crawlers = self._initialize_crawlers()
        
        # 設定事件處理器
        self._setup_event_handlers()
    
    def _initialize_crawlers(self) -> Dict[str, Any]:
        """初始化各平台爬蟲"""
        crawlers = {}
        
        if settings.ENABLE_TIXCRAFT:
            crawlers['tixcraft'] = TixcraftCrawler(TICKET_URL1)
        
        if settings.ENABLE_KKTIX:
            crawlers['kktix'] = KktixCrawler(KKTIX_URL)
        
        if settings.ENABLE_IBON:
            crawlers['ibon'] = IbonCrawler(TICKET_URLibon)
        
        return crawlers
    
    def _setup_event_handlers(self):
        """設定事件處理器"""
        
        @self.bot.event
        async def on_ready():
            """Bot 啟動事件"""
            print(f"{self.bot.user} 已上線！")
            # 啟動檢查票務狀態的任務
            self.bot.loop.create_task(self._check_tickets_task())
    
    async def _check_tickets_task(self):
        """票券檢查主任務"""
        await self.bot.wait_until_ready()
        
        # 取得通知頻道
        channel = discord.utils.get(
            self.bot.get_all_channels(), 
            name=settings.DISCORD_CHANNEL_NAME
        )
        
        if not channel:
            print(f"無法找到通知頻道：{settings.DISCORD_CHANNEL_NAME}")
            return
        
        print(f"開始監控票券，將在頻道 '{settings.DISCORD_CHANNEL_NAME}' 發送通知")
        
        while True:
            try:
                await self._check_all_platforms(channel)
            except Exception as e:
                print(f"檢查票務時出現錯誤：{e}")
            
            # 隨機等待時間，避免被封鎖
            wait_time = random.randint(
                settings.CHECK_INTERVAL_MIN, 
                settings.CHECK_INTERVAL_MAX
            )
            print(f"等待 {wait_time} 秒後進行下次檢查...")
            await asyncio.sleep(wait_time)
    
    async def _check_all_platforms(self, channel: discord.TextChannel):
        """檢查所有平台的票券狀態"""
        
        for platform_name, crawler in self.crawlers.items():
            try:
                print(f"檢查 {platform_name} 平台...")
                available_tickets = crawler.get_available_tickets()
                
                if available_tickets:
                    await self._send_notifications(
                        channel, 
                        platform_name, 
                        available_tickets
                    )
                else:
                    print(f"{platform_name}：目前沒有可用票券")
                    
            except Exception as e:
                print(f"檢查 {platform_name} 時出現錯誤: {e}")
    
    async def _send_notifications(
        self, 
        channel: discord.TextChannel, 
        platform_name: str, 
        available_tickets: Dict[str, Any]
    ):
        """發送票券通知"""
        
        for event_name, tickets in available_tickets.items():
            message_lines = [f"🎟️ **{platform_name.upper()} 有票通知！**"]
            message_lines.append(f"**活動：{event_name}**")
            
            for ticket in tickets[:3]:  # 最多顯示3個票區
                message_lines.append(f"• {ticket.name}: {ticket.status}")
            
            if len(tickets) > 3:
                message_lines.append(f"• ...還有 {len(tickets) - 3} 個票區有票")
            
            # 添加URL（如果有的話）
            if hasattr(self.crawlers[platform_name], 'urls'):
                urls = self.crawlers[platform_name].urls
                if event_name in urls:
                    message_lines.append(f"\n🔗 **購票連結：**")
                    message_lines.append(urls[event_name])
            
            message = "\n".join(message_lines)
            
            try:
                await channel.send(message)
                print(f"已發送通知：{event_name}")
            except Exception as e:
                print(f"發送通知時出現錯誤：{e}")
    
    async def start(self):
        """啟動 Bot"""
        try:
            await self.bot.start(settings.DISCORD_TOKEN)
        except discord.LoginFailure:
            print("Discord Token 無效，請檢查 .env 檔案中的 DISCORD_TOKEN 設定")
        except Exception as e:
            print(f"啟動 Bot 時出現錯誤：{e}")

async def main():
    """主程式入口點"""
    bot = TicketBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
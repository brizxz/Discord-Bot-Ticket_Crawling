"""
ibon 票券平台爬蟲
"""
import time
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from .base import BaseCrawler, TicketInfo

class IbonCrawler(BaseCrawler):
    """ibon 票券爬蟲（使用 Selenium 處理 shadow DOM）"""
    
    def __init__(self, urls: dict):
        super().__init__(urls)
        self.driver_options = self._setup_driver_options()
    
    def _setup_driver_options(self) -> Options:
        """設定 Chrome 瀏覽器選項"""
        options = Options()
        options.add_argument('--headless')  # 無頭模式
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        return options
    
    def _break_shadow_dom(self, driver: webdriver.Chrome) -> None:
        """打開 shadow-root(closed) 的函數"""
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
    
    def check_availability(self, url: str) -> List[TicketInfo]:
        """
        檢查 ibon 票券可用性
        
        Args:
            url: ibon 票券頁面URL
            
        Returns:
            票券資訊列表
        """
        driver = None
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=self.driver_options
            )
            
            # 執行打開 shadow DOM 的腳本
            self._break_shadow_dom(driver)
            
            # 訪問URL
            driver.get(url)
            
            # 檢查是否有警告對話框
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"遇到警告框：{alert_text}")
                return [TicketInfo(
                    name="系統警告",
                    status=f"檢測到警告訊息，視為無票：{alert_text}",
                    available=False
                )]
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
                
                return result;
            """)
            
            # 解析結果
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
            
            # 如果有票可購買，保存截圖作為證據
            if available:
                try:
                    screenshot_file = f'ibon_available_{time.strftime("%Y%m%d_%H%M%S")}.png'
                    driver.save_screenshot(screenshot_file)
                    print(f"發現有票！已保存截圖: {screenshot_file}")
                except Exception as e:
                    print(f"保存截圖時出錯: {e}")
            
            return [TicketInfo(
                name="ibon票券",
                status=message,
                available=available
            )]
        
        except Exception as e:
            print(f"檢查 ibon 票務時出現錯誤: {e}")
            return [TicketInfo(
                name="錯誤",
                status=f"檢查票務時出現錯誤: {e}",
                available=False
            )]
        
        finally:
            try:
                if driver:
                    driver.quit()
            except:
                pass
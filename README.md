# Discord Bot 票券爬蟲

這是一個自動監控多個票務平台（Tixcraft、KKTIX、ibon）票券狀態的 Discord Bot，當檢測到有票時會自動發送通知到指定的 Discord 頻道。

## 支援平台

- **Tixcraft** - 使用 HTTP 請求和 BeautifulSoup 解析
- **KKTIX** - 解析 JavaScript 中的 inventory 數據
- **ibon** - 使用 Selenium 處理 shadow DOM

## 功能特色

- 🤖 **自動監控** - 持續檢查多個票務平台的票券狀態
- 💬 **Discord 通知** - 有票時立即發送通知到 Discord 頻道
- 🔧 **模組化設計** - 易於添加新的票務平台支援
- ⚙️ **靈活配置** - 可單獨啟用/停用各平台監控
- 🕒 **隨機間隔** - 避免被網站封鎖的隨機檢查間隔

## 專案結構

```
Discord-Bot-Ticket_Crawling/
├── bot/                    # Discord Bot 相關程式碼
│   ├── __init__.py
│   └── discord_bot.py     # 主要 Bot 邏輯
├── config/                # 配置管理
│   ├── __init__.py
│   └── settings.py        # 設定檔案
├── crawlers/              # 爬蟲模組
│   ├── __init__.py
│   ├── base.py           # 爬蟲基礎類別
│   ├── tixcraft.py       # Tixcraft 爬蟲
│   ├── kktix.py          # KKTIX 爬蟲
│   └── ibon.py           # ibon 爬蟲
├── const/                 # URL 常數定義
│   ├── ticket.py         # Tixcraft URLs
│   ├── kktix.py          # KKTIX URLs
│   └── ibon.py           # ibon URLs
├── tests/                 # 測試檔案
│   ├── test_tixcraft.py
│   ├── test_kktix.py
│   ├── test_ibon_legacy.py
│   └── test_shadow_dom_legacy.py
├── main.py               # 主程式入口點
├── requirements.txt      # Python 依賴套件
├── .env.example         # 環境變數範例
└── README.md
```

## 安裝指南

### 1. 環境需求

- Python 3.8 或更高版本
- Chrome 瀏覽器（用於 ibon 爬蟲）

### 2. 下載專案

```bash
git clone <repository-url>
cd Discord-Bot-Ticket_Crawling
```

### 3. 安裝依賴套件

建議使用虛擬環境：

```bash
# 創建虛擬環境
python -m venv venv

# 啟用虛擬環境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安裝依賴套件
pip install -r requirements.txt
```

或使用 conda：

```bash
source ~/Desktop/miniconda3/bin/activate
conda activate py311
pip install -r requirements.txt
```

### 4. 配置設定

1. 複製環境變數範例檔案：
   ```bash
   cp .env.example .env
   ```

2. 編輯 `.env` 檔案，設定您的配置：
   ```env
   # Discord Bot Settings
   DISCORD_TOKEN=your_discord_bot_token_here
   DISCORD_CHANNEL_NAME=測試

   # Bot Settings
   CHECK_INTERVAL_MIN=5
   CHECK_INTERVAL_MAX=10

   # Platform Settings
   ENABLE_TIXCRAFT=true
   ENABLE_KKTIX=true
   ENABLE_IBON=true
   ```

### 5. 創建 Discord Bot

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 創建新的應用程式
3. 在 "Bot" 頁面創建 Bot 並複製 Token
4. 在 "OAuth2" > "URL Generator" 頁面選擇：
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Message History`
5. 使用生成的 URL 邀請 Bot 到您的伺服器

## 使用方法

### 執行主程式

```bash
python main.py
```

### 更新監控 URL

編輯 `const/` 目錄下的檔案來新增或修改要監控的票券 URL：

- `const/ticket.py` - Tixcraft URLs
- `const/kktix.py` - KKTIX URLs  
- `const/ibon.py` - ibon URLs

例如：
```python
# const/ticket.py
TICKET_URL1 = {
    "演唱會A": "https://tixcraft.com/activity/game/25_example1",
    "演唱會B": "https://tixcraft.com/activity/game/25_example2",
}
```

### 測試單一平台

您可以單獨測試各平台的爬蟲：

```bash
# 測試 Tixcraft
python tests/test_tixcraft.py

# 測試 KKTIX
python tests/test_kktix.py
```

## 配置選項

### 環境變數說明

| 變數名稱 | 預設值 | 說明 |
|---------|--------|------|
| `DISCORD_TOKEN` | - | Discord Bot Token（必填） |
| `DISCORD_CHANNEL_NAME` | 測試 | 發送通知的頻道名稱 |
| `CHECK_INTERVAL_MIN` | 5 | 最小檢查間隔（秒） |
| `CHECK_INTERVAL_MAX` | 10 | 最大檢查間隔（秒） |
| `ENABLE_TIXCRAFT` | true | 是否啟用 Tixcraft 監控 |
| `ENABLE_KKTIX` | true | 是否啟用 KKTIX 監控 |
| `ENABLE_IBON` | true | 是否啟用 ibon 監控 |

## 開發指南

### 添加新的票務平台

1. 在 `crawlers/` 目錄創建新的爬蟲類別
2. 繼承 `BaseCrawler` 並實現 `check_availability` 方法
3. 在 `bot/discord_bot.py` 中註冊新的爬蟲
4. 添加 URL 配置檔案到 `const/` 目錄

### 爬蟲基礎類別

```python
from crawlers.base import BaseCrawler, TicketInfo

class YourCrawler(BaseCrawler):
    def check_availability(self, url: str) -> List[TicketInfo]:
        # 實現您的爬蟲邏輯
        pass
```

## 注意事項

1. **遵守網站使用條款** - 請確保您的使用方式符合各票務網站的服務條款
2. **合理的檢查頻率** - 避免過於頻繁的請求導致 IP 被封鎖
3. **網站結構變更** - 票務網站可能會更新結構，需要相應調整爬蟲邏輯
4. **隱私保護** - 不要將您的 Discord Token 提交到版本控制系統

## 疑難排解

### 常見問題

1. **Bot 無法連線**
   - 檢查 `DISCORD_TOKEN` 是否正確
   - 確認 Bot 已被邀請到伺服器

2. **找不到頻道**
   - 檢查 `DISCORD_CHANNEL_NAME` 設定
   - 確認 Bot 有權限查看該頻道

3. **Chrome 驅動程式問題**
   - 確認已安裝 Chrome 瀏覽器
   - `webdriver-manager` 會自動下載驅動程式

4. **爬蟲無法正常工作**
   - 檢查網路連線
   - 目標網站可能已更新結構

## 授權

本專案僅供學習和研究目的使用。使用者需自行確保符合相關法律法規和網站使用條款。

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善本專案！

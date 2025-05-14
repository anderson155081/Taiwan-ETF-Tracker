這是為你的「ETF 自動追蹤與分析系統」專案設計的 README.md 初稿，清楚說明功能、架構與使用方式：

⸻



# ETF Tracker & Analyzer 📈

一個可部署在雲端的自動化系統，用來每日追蹤台股市值型 ETF（如 0050、006208），根據技術指標產出視覺化分析與投資建議，並可透過 Email 或 LINE 推播每日分析報告。

## 🚀 功能特色

- 每日自動抓取 ETF 價格資料（支援 0050、006208 等）
- 計算並繪製技術指標圖表（KD, MACD, 均線等）
- 根據自定策略給出「建議進場/持有/觀望」
- 產出每日分析報告（HTML / 圖表）
- 可整合 LINE Notify / Email 做每日推播
- 可部署於 Cloud Run、Railway、GitHub Actions 等平台

## 🛠 技術架構

- 語言：Python 3.10+
- 套件：`yfinance`, `pandas`, `ta`, `matplotlib`, `jinja2`
- 推播：LINE Notify / SMTP Email
- 部署：支援 Railway、Google Cloud Run、GitHub Actions 排程

## 📁 專案結構

etf_tracker/
├── main.py                  # 主程式入口
├── strategy.py              # 技術指標與買進邏輯
├── data_fetcher.py          # 擷取 ETF 價格資料
├── plotter.py               # 繪製技術分析圖表
├── notifier.py              # LINE / Email 通知
├── templates/               # HTML 分析報告模板
├── reports/                 # 每日產出的圖表與報告
└── requirements.txt         # Python 套件需求

## 🔄 自動執行排程建議

你可以透過下列平台實作每日執行：
- **GitHub Actions**（免費、易設定）
- **Google Cloud Scheduler + Cloud Run**
- **Railway / Render** 透過 Webhook 或 CRON 執行

## 🔔 通知設定

### LINE Notify 範例
1. 前往 [LINE Notify 官網](https://notify-bot.line.me/) 建立權杖
2. 將 token 加入 `.env` 或直接放入 `notifier.py`

```python
LINE_TOKEN = "your_token"

📊 技術指標支援

指標	說明
KD	隨機震盪指標（過熱/超賣區）
MACD	移動平均收斂背離
MA	簡單移動平均線

✅ TODO
	•	支援更多 ETF（如 00878, 00929 等）
	•	加入回測機制
	•	網頁 Dashboard 視覺化前端
	•	支援 Telegram Bot

🧑‍💻 作者

Chen Qi’an（陳麒安）
📸 IG: @ande.rsonphoto

⸻

歡迎 Fork / Star / 改進 🎯

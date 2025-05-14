# ETF Tracker & Analyzer 📈

A cloud-deployable automation tool that tracks Taiwan's market cap ETFs (e.g., 0050, 006208) daily, generates beautiful visual analyses with technical indicators, and suggests potential entry signals. Results can be pushed via LINE Messaging API for real-time updates.

## 🚀 Features

- Automatically fetches ETF price data daily (supports 0050, 006208, etc.)
- Calculates and plots technical indicators (KD, MACD, moving averages)
- Applies custom strategy rules to suggest Buy / Hold / Watch decisions
- Generates clear visual reports (PNG/HTML)
- Sends reports via LINE Messaging API
- Deployable on platforms like Railway, Google Cloud Run, or GitHub Actions

## 🛠 Tech Stack

- **Language**: Python 3.10+
- **Libraries**: `yfinance`, `pandas`, `ta`, `matplotlib`, `jinja2`, `flask` (for LINE bot webhook)
- **Notification**: LINE Messaging API (via webhook & reply API)
- **Deployment**: GitHub Actions / Railway / Google Cloud Run / Render

## 📁 Project Structure

```
etf_tracker/
├── main.py                  # Main pipeline
├── strategy.py              # Buy/sell signal logic
├── data_fetcher.py          # Fetches ETF historical/real-time data
├── plotter.py               # Chart generation using technical indicators
├── line_bot.py              # LINE Messaging API integration (webhook receiver)
├── templates/               # HTML templates for rendering reports
├── reports/                 # Output report images or HTML
└── requirements.txt         # Python dependencies
```

## 🔁 Daily Execution

Use any of the following to automate daily runs:
- **GitHub Actions** (free & easy for scheduled jobs)
- **Google Cloud Scheduler + Cloud Run**
- **Railway** or **Render** (supports CRON)

## 💬 LINE Messaging API Setup

1. Create a [LINE Developer Account](https://developers.line.biz/)
2. Create a Messaging API channel
3. Deploy a webhook receiver using Flask (e.g., `line_bot.py`)
4. Push messages using the LINE Reply/Push API

```python
from linebot import LineBotApi
from linebot.models import TextSendMessage

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
user_id = 'USER_ID'
line_bot_api.push_message(user_id, TextSendMessage(text='0050 strategy report is ready!'))
```

## 📊 Supported Indicators

| Indicator | Description |
|-----------|-------------|
| KD | Stochastic Oscillator |
| MACD | Moving Average Convergence |
| MA | Simple Moving Averages |

## ✅ TODO

- Add more ETFs (e.g., 00878, 00929)
- Implement backtesting
- Build web dashboard for historical insights
- Support Telegram Bot alternative

## 👤 Author

Chen Qi'an
- GitHub: [anderson155081](https://github.com/anderson155081)
- Instagram: [@ande.rsonphoto](https://instagram.com/ande.rsonphoto)

---

Feel free to fork, star, or contribute! 🌟

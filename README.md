# 📈 ShadowBeta Financial Dashboard

**A professional-grade financial dashboard for active traders with AI-powered stock analysis, advanced technical indicators, and real-time market data.**

![ShadowBeta Dashboard](https://img.shields.io/badge/Status-Production%20Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11+-blue) ![React](https://img.shields.io/badge/React-19.0+-61DAFB) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-00A86B)

---

## 🎯 What Does ShadowBeta Do?

ShadowBeta is an advanced financial dashboard that helps active traders make informed decisions by:

- **📊 Analyzing stocks** using 6 professional criteria (Trend, Momentum, Volume, Price Action, Oversold, Breakout)
- **🤖 Providing AI insights** from both Google Gemini and OpenAI
- **📈 Displaying real-time data** with advanced technical indicators (RSI, MACD, Bollinger Bands, Stochastic)
- **📱 Working on all devices** with mobile-optimized responsive design
- **⚡ Auto-refreshing data** with configurable intervals
- **📁 Managing custom watchlists** for personalized stock tracking
- **📤 Exporting analysis** in JSON/CSV formats

---

## 🚀 Quick Start Guide

### Step 1: Prerequisites

Before starting, make sure you have:
- **Python 3.11+** installed
- **Node.js 18+** and **Yarn** package manager
- **MongoDB** running (or access to MongoDB Atlas)
- **Internet connection** for API calls

### Step 2: Get Your API Keys

You'll need these FREE API keys:

1. **Finnhub API Key** (for stock data)
   - Go to [finnhub.io](https://finnhub.io)
   - Sign up for free account
   - Copy your API key

2. **Google Gemini API Key** (for AI analysis)
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key

3. **OpenAI API Key** (optional, for alternative AI)
   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create an API key
   - Copy the key

### Step 3: Setup

**Option A: Automatic Setup (Recommended)**

**For Linux/macOS:**
```bash
chmod +x setup_local.sh
./setup_local.sh
```

**For Windows:**
```bash
setup_local.bat
```

**Option B: Manual Setup**

1. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   yarn install
   ```

3. **Create Environment Files:**

   **Backend (.env):**
   ```env
   # Database Configuration
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=shadowbeta

   # Required API Keys
   FINNHUB_API_KEY=your_finnhub_key_here
   GEMINI_API_KEY=your_gemini_key_here
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here

   # Optional Features
   DISCORD_TOKEN=your_discord_token_here
   CHANNEL_ID=your_channel_id_here
   NEWS_API_KEY=your_news_api_key_here
   ```

   **Frontend (.env):**
   ```env
   REACT_APP_BACKEND_URL=http://localhost:8000
   WDS_SOCKET_PORT=443
   ```

### Step 4: Start the Application

**🚀 ONE-CLICK LAUNCHERS (Easiest Method):**

Choose the method that works best for you:

**Option A: Easy Launcher (RECOMMENDED - Always Works)**
```bash
# Run from anywhere - just copy and paste this:
python3 easy_launcher.py
```
- ✅ Works from any directory
- ✅ No GUI dependencies needed
- ✅ Automatic browser opening
- ✅ Simple and reliable

**Option B: GUI Launcher (For GUI lovers)**
```bash
# First install GUI library:
sudo apt-get install python3-tk
# Then run:
python3 shadowbeta_launcher.py
```
- ✅ Beautiful graphical interface
- ✅ One-click start/stop
- ✅ Real-time log monitoring

**Option C: Universal Launcher (Auto-finds directory)**
```bash
# Works from anywhere:
python3 universal_launcher.py
```
- ✅ Automatically finds ShadowBeta directory
- ✅ No GUI needed
- ✅ Detailed status messages

**Option D: Script Launchers**

For **Linux/Ubuntu:**
```bash
./start_shadowbeta.sh
```

For **Windows:**
```bash
start_shadowbeta.bat
```

For **macOS:**
```bash
./start_shadowbeta_macos.sh
```

**Option E: Manual Start (For developers)**
```bash
# Terminal 1: Start Backend
cd backend
python server.py

# Terminal 2: Start Frontend
cd frontend
yarn start
```

### Step 5: Access the Dashboard

Open your web browser and go to:
- **Frontend:** `http://localhost:3000` (or your configured URL)
- **Backend API:** `http://localhost:8000` (for API testing)

## 🔧 Stopping the Application

**Easy Stop Methods:**

**GUI Launcher:**
- Click the "🛑 Stop Application" button in the launcher

**Script Method:**
```bash
# Linux/Ubuntu:
./stop_shadowbeta.sh

# macOS:
./stop_shadowbeta_macos.sh

# Windows: Close the command prompt window or press Ctrl+C
```

**Manual Method:**
```bash
# Stop all services
sudo supervisorctl stop all
```

---

## 🎮 How to Use ShadowBeta

### Basic Usage

1. **📊 View Stock Analysis**
   - The dashboard automatically loads and analyzes stocks
   - Each stock card shows:
     - Current price and % change
     - Score out of 4 based on trading criteria
     - Pass/Fail status for each criterion
     - Technical indicators (RSI, Volume, Moving Averages)

2. **🧠 Get AI Insights**
   - Click "AI Insight" on any stock card
   - Choose between Gemini or OpenAI analysis
   - Get 2-3 sentence trading recommendations

3. **📱 Customize Your Experience**
   - Click the Settings ⚙️ button to:
     - Toggle dark/light mode
     - Enable/disable auto-refresh
     - Set refresh intervals
     - Choose AI provider

### Advanced Features

4. **📝 Create Custom Watchlists**
   - Click "New List" button
   - Enter watchlist name
   - Add comma-separated ticker symbols (e.g., AAPL, MSFT, GOOGL)
   - Click "Create Watchlist"

5. **🔍 Filter and Sort**
   - **Sort by:** Score, Ticker, Volume, Change, RSI
   - **Filter by:** All Stocks, 4/4 Only, 3+ Score, Oversold, Breakout

6. **📤 Export Data**
   - Click "Export" button for JSON format
   - Click "CSV" button (bottom right) for spreadsheet format

---

## 🛠️ Technical Configuration

### Environment Variables Reference

**Backend (.env file):**
```env
# Required API Keys
FINNHUB_API_KEY=your_finnhub_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional Features
DISCORD_TOKEN=your_discord_bot_token
CHANNEL_ID=your_discord_channel_id
POLYGON_API_KEY=your_polygon_api_key

# Database Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="shadowbeta"
```

**Frontend (.env file):**
```env
REACT_APP_BACKEND_URL=http://localhost:8000
WDS_SOCKET_PORT=443
```

### Stock Analysis Criteria

The dashboard evaluates stocks using 6 criteria:

1. **🔍 Trend Analysis**
   - 50-day MA > 200-day MA
   - Current price > both moving averages

2. **⚡ Momentum**
   - RSI > 50
   - MACD line > signal line
   - Stochastic > 20

3. **📊 Volume**
   - Average volume > 1 million
   - Relative volume > 1.5x

4. **🎯 Price Action**
   - Price within Bollinger Bands
   - Price above 50-day MA

5. **📉 Oversold Detection** (Bonus)
   - RSI < 30 and Stochastic < 20

6. **🚀 Breakout Detection** (Bonus)
   - Price above upper Bollinger Band
   - Relative volume > 2.0x

---

## 🐛 Troubleshooting

### Common Issues

**❌ "Loading forever" or no stock data**
```bash
# Check backend status
sudo supervisorctl status backend

# Check backend logs
tail -f /var/log/supervisor/backend.err.log

# Restart backend
sudo supervisorctl restart backend
```

**❌ "AI Insight not working"**
- Verify your API keys in `/app/backend/.env`
- Check you have sufficient API credits
- Try switching AI provider in Settings

**❌ "Can't create watchlists"**
- Ensure MongoDB is running
- Check database connection in backend logs

**❌ "Export not working"**
- Ensure popup blockers are disabled
- Try right-clicking and "Save as..."

### Performance Optimization

**If the app is slow:**
1. Reduce auto-refresh frequency in Settings
2. Use fewer stocks in custom watchlists
3. Clear browser cache and cookies

**For better API performance:**
- Use API keys with higher rate limits
- Consider upgrading to paid API tiers for production use

---

## 📋 Dependencies

### Backend Requirements
- **FastAPI** - Web framework
- **yfinance** - Yahoo Finance data
- **finnhub-python** - Finnhub API client
- **google-generativeai** - Google Gemini AI
- **openai** - OpenAI GPT integration
- **pymongo** - MongoDB client
- **pandas/numpy** - Data analysis

### Frontend Requirements
- **React 19** - UI framework
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Lucide React** - Icons
- **Recharts** - Charts (if needed)

---

## 🔐 Security Notes

- **Keep API keys secure** - Never commit them to version control
- **Use environment variables** - Store sensitive data in .env files
- **Regular updates** - Keep dependencies updated for security
- **Rate limiting** - Be mindful of API rate limits to avoid blocks

---

## 📈 Usage Tips for Traders

### Best Practices

1. **🎯 Focus on 4/4 Scores**
   - Stocks with perfect scores meet all trading criteria
   - Higher probability of successful trades

2. **📊 Use Multiple Timeframes**
   - Check Finviz charts for different timeframes
   - Confirm signals across multiple periods

3. **🤖 Combine AI with Analysis**
   - Use AI insights to supplement technical analysis
   - Compare Gemini vs OpenAI perspectives

4. **⚡ Monitor Breakouts**
   - Filter for "Breakout" stocks for momentum plays
   - Watch for high relative volume

5. **📉 Find Oversold Opportunities**
   - Use "Oversold" filter for potential reversals
   - Combine with strong fundamentals

---

## 🆘 Support

If you need help:

1. **Check the logs** first:
   ```bash
   # Backend logs
   tail -f /var/log/supervisor/backend.err.log

   # Frontend logs
   sudo supervisorctl status frontend
   ```

2. **Verify configuration**:
   - API keys are correctly set
   - Database is running
   - Network connectivity is working

3. **Restart services**:
   ```bash
   sudo supervisorctl restart all
   ```

---

## 🎉 You're Ready to Trade!

Your ShadowBeta Financial Dashboard is now ready to help you make informed trading decisions. The combination of technical analysis, AI insights, and real-time data gives you a professional edge in the markets.

**Happy Trading! 📈🚀**

---

*Built with ❤️ for active traders who demand the best tools for market analysis.*

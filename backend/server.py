import os
import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from typing import List, Dict, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import google.generativeai as genai
import finnhub
import yfinance as yf
from pydantic import BaseModel
import json
import uuid
import discord
from discord.ext import commands
import openai
import anthropic
from newsapi import NewsApiClient
import feedparser
import concurrent.futures
from functools import lru_cache
import threading
import time
# Optional background scheduling (for cache warming)
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    print("⚠️  Schedule library not available - background cache warming disabled")
    SCHEDULE_AVAILABLE = False
    schedule = None
# Optional Alpaca trading imports (for paper trading features)
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_AVAILABLE = True
except ImportError:
    print("⚠️  Alpaca trading library not available - trading features disabled")
    ALPACA_AVAILABLE = False
    TradingClient = None
    MarketOrderRequest = None
    OrderSide = None
    TimeInForce = None

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from multiple locations to be robust to working dir
load_dotenv()  # default
_env_candidates = [
    Path(__file__).resolve().parent / '.env',            # backend/.env
    Path(__file__).resolve().parent.parent / '.env',     # project root .env
    Path.cwd() / '.env'                                  # current working dir
]
for _p in _env_candidates:
    try:
        if _p.exists():
            # Do NOT override real environment (e.g., Render). Files only fill missing values.
            load_dotenv(dotenv_path=_p, override=False)
    except Exception:
        pass

# As a final safety net, ensure sane defaults for local development
os.environ.setdefault('DB_NAME', 'shadowbeta')
os.environ.setdefault('MONGODB_DISABLED', 'true')  # Default to disabled for better performance
# Note: Do NOT set MONGO_URL default to prevent unwanted connection attempts

# Initialize FastAPI app
app = FastAPI(title="ShadowBeta Financial Dashboard API")

# Configure CORS for production deployment (Vercel frontend + Render backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://pip-engine.vercel.app",  # Main Vercel deployment
        "https://pip-engine-ah50zb1hp-matts-projects-07983335.vercel.app",  # Current Vercel URL
        "https://*.vercel.app",   # All Vercel deployments
        "https://*.onrender.com", # Render deployments
        "*"  # Allow all origins for now (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# BACKGROUND CACHE WARMING SYSTEM FOR MAXIMUM PERFORMANCE
# =============================================================================

class CacheWarmer:
    """Background cache warming system to pre-populate cache with fresh data"""

    def __init__(self):
        self.is_running = False
        self.thread = None

    def start(self):
        """Start the background cache warming thread"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            print("🔥 CACHE WARMER: Background cache warming started")

    def _run_scheduler(self):
        """Run the background scheduler"""
        if not SCHEDULE_AVAILABLE:
            print("⚠️  CACHE WARMER: Schedule not available, using timer-based approach")
            # Fallback to simple timer approach
            while self.is_running:
                self._warm_cache()
                time.sleep(900)  # 15 minutes
            return

        # Schedule cache warming every 15 minutes
        schedule.every(15).minutes.do(self._warm_cache)

        # Schedule full cache refresh every hour
        schedule.every().hour.do(self._full_cache_refresh)

        # Warm cache immediately on startup
        threading.Timer(30, self._warm_cache).start()  # Wait 30s after startup

        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def _warm_cache(self):
        """Warm the cache with fresh data"""
        try:
            print("🔥 CACHE WARMER: Starting cache warming cycle...")

            # Warm stock scanning cache
            asyncio.run(self._warm_stock_cache())

            # Warm market overview cache
            asyncio.run(self._warm_market_cache())

            # Warm news cache
            self._warm_news_cache()

            print("✅ CACHE WARMER: Cache warming completed successfully")

        except Exception as e:
            print(f"❌ CACHE WARMER: Error during cache warming: {e}")

    async def _warm_stock_cache(self):
        """Pre-warm stock scanning cache"""
        try:
            # Use lightweight scanning to warm cache
            curated_stocks = get_curated_scannable_stocks()[:20]  # Top 20 only
            await fetch_lightweight_stocks_concurrent(curated_stocks, max_stocks=20)
            print("📊 CACHE WARMER: Stock cache warmed")
        except Exception as e:
            print(f"📊 CACHE WARMER: Stock cache warming failed: {e}")

    async def _warm_market_cache(self):
        """Pre-warm market overview cache"""
        try:
            # Warm indices, movers, and heatmap
            await get_market_indices()
            await get_market_movers()
            await get_market_heatmap()
            print("📈 CACHE WARMER: Market cache warmed")
        except Exception as e:
            print(f"📈 CACHE WARMER: Market cache warming failed: {e}")

    def _warm_news_cache(self):
        """Pre-warm news cache"""
        try:
            # Warm general news cache
            fetch_general_financial_news(limit=10)
            print("📰 CACHE WARMER: News cache warmed")
        except Exception as e:
            print(f"📰 CACHE WARMER: News cache warming failed: {e}")

    def _full_cache_refresh(self):
        """Full cache refresh - clear and rebuild"""
        try:
            print("🔄 CACHE WARMER: Starting full cache refresh...")

            # Clear all caches
            global stock_cache, lightweight_cache, nyse_symbols_cache
            stock_cache.clear()
            lightweight_cache.clear()
            nyse_symbols_cache['data'] = None

            # Rebuild cache
            self._warm_cache()

            print("✅ CACHE WARMER: Full cache refresh completed")

        except Exception as e:
            print(f"❌ CACHE WARMER: Full cache refresh failed: {e}")

# Initialize cache warmer
cache_warmer = CacheWarmer()

# =============================================================================
# WEBSOCKET REAL-TIME UPDATES SYSTEM
# =============================================================================

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📡 WEBSOCKET: New connection added. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"📡 WEBSOCKET: Connection removed. Total: {len(self.active_connections)}")

    async def send_to_all(self, message: dict):
        """Send message to all connected clients"""
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_stock_update(self, stock_data):
        """Broadcast stock data updates to all clients"""
        await self.send_to_all({
            "type": "stock_update",
            "data": stock_data,
            "timestamp": datetime.now().isoformat()
        })

    async def broadcast_market_update(self, market_data):
        """Broadcast market overview updates to all clients"""
        await self.send_to_all({
            "type": "market_update",
            "data": market_data,
            "timestamp": datetime.now().isoformat()
        })

# Initialize connection manager
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()

            # Handle client requests
            if data == "request_stock_update":
                # Send latest stock data
                try:
                    stocks = await scan_stocks_fast()
                    await manager.broadcast_stock_update(stocks)
                except:
                    pass

            elif data == "request_market_update":
                # Send latest market data
                try:
                    market = await get_market_overview()
                    await manager.broadcast_market_update(market)
                except:
                    pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"📡 WEBSOCKET: Error - {e}")
        manager.disconnect(websocket)

# CORS already configured above - removing duplicate

# Initialize MongoDB connection (optional)
# Try both case variations since Render might use different casing
MONGO_URL = os.environ.get('MONGO_URL') or os.environ.get('Mongo_URL')
MONGODB_DISABLED_ENV = os.environ.get('MONGODB_DISABLED', 'false').lower() in ['true', '1', 'yes', 'on']

# Debug ALL environment variables to see what's available
print("🔍 ALL ENVIRONMENT VARIABLES:")
for key, value in sorted(os.environ.items()):
    if any(word in key.upper() for word in ['MONGO', 'DB', 'DATABASE']):
        if 'URL' in key.upper() or 'PASSWORD' in key.upper():
            # Mask sensitive info but show structure
            masked_value = value[:10] + "***" + value[-10:] if len(value) > 20 else "***"
            print(f"  {key} = {masked_value}")
        else:
            print(f"  {key} = {value}")

print(f"🔍 Debug: MONGO_URL = {MONGO_URL}")
print(f"🔍 Debug: MONGODB_DISABLED_ENV = {MONGODB_DISABLED_ENV}")
print(f"🔍 Debug: Raw MONGODB_DISABLED env = '{os.environ.get('MONGODB_DISABLED', 'not_set')}'")

# If MongoDB is explicitly disabled, respect that
if MONGODB_DISABLED_ENV:
    print("⚠️  MongoDB explicitly disabled via MONGODB_DISABLED environment variable.")
    MONGODB_DISABLED = True
elif not MONGO_URL:
    print("❌ MongoDB enabled but no MONGO_URL found! Please check environment variables.")
    MONGODB_DISABLED = True
else:
    print(f"✅ MongoDB enabled. Will attempt connection to: {MONGO_URL[:50]}...")
    MONGODB_DISABLED = False

if MONGODB_DISABLED:
    print("✅ MongoDB DISABLED - App will run without user features (watchlists, alerts, etc.)")
    client = None
    db = None
    watchlists_collection = None
    alerts_collection = None
    user_preferences_collection = None
    strategies_collection = None
else:
    try:
        # Add database name to URL if not present
        connection_url = MONGO_URL
        if '?' in connection_url and '/?' in connection_url:
            # URL like: mongodb+srv://user:pass@cluster.net/?params
            # Insert database name: mongodb+srv://user:pass@cluster.net/dbname?params
            connection_url = connection_url.replace('/?', '/shadowbeta?')
        elif not any(db_name in connection_url for db_name in ['/shadowbeta', '/test', '/admin']):
            # Add default database name if none specified
            if '?' in connection_url:
                connection_url = connection_url.replace('?', '/shadowbeta?')
            else:
                connection_url = connection_url + '/shadowbeta'

        print(f"🔌 Attempting MongoDB connection to: {connection_url[:50]}...")
        client = MongoClient(connection_url, serverSelectionTimeoutMS=10000)  # 10 second timeout for network

        # Test the connection
        print("🔄 Testing MongoDB connection...")
        client.admin.command('ping')
        print("✅ MongoDB ping successful")

        db = client[os.environ.get('DB_NAME', 'shadowbeta')]
        print(f"✅ Using database: {db.name}")

        # Collections
        watchlists_collection = db.watchlists
        alerts_collection = db.alerts
        user_preferences_collection = db.user_preferences
        users_collection = db.users
        portfolios_collection = db.portfolios
        strategies_collection = db.shadowbot_strategies
        print("✅ MongoDB connected successfully - All collections initialized")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print(f"❌ Connection URL format: {MONGO_URL[:30]}...")
        print("🔄 AUTOMATICALLY DISABLING MongoDB - App will run without user features")
        print("💡 Check: 1) MongoDB Atlas cluster is running 2) IP whitelist includes 0.0.0.0/0 3) Credentials are correct")

        # Automatically disable MongoDB and continue
        client = None
        db = None
        watchlists_collection = None
        alerts_collection = None
        user_preferences_collection = None
        users_collection = None
        portfolios_collection = None
        strategies_collection = None

# Initialize API clients
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'demo')  # Free tier available
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY')
ALPACA_API_SECRET = os.environ.get('ALPACA_API_SECRET')
ALPACA_PAPER = os.environ.get('ALPACA_PAPER', 'true').lower() == 'true'

# Configure AI clients
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

openai.api_key = OPENAI_API_KEY

# Initialize Anthropic Claude client
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Initialize Finnhub client
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

# Initialize News API client
if NEWS_API_KEY != 'demo':
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)
else:
    newsapi = None

# Initialize Alpaca Trading client (optional)
alpaca_client = None
if ALPACA_AVAILABLE and ALPACA_API_KEY and ALPACA_API_SECRET:
    try:
        alpaca_client = TradingClient(ALPACA_API_KEY, ALPACA_API_SECRET, paper=ALPACA_PAPER)
        print("✅ Alpaca client initialized (paper mode)" if ALPACA_PAPER else "✅ Alpaca client initialized (live mode)")
    except Exception as e:
        print(f"⚠️  Alpaca client init failed: {e}")

# Websocket clients for Shadowbot live updates
shadowbot_clients = set()

async def broadcast_shadowbot(payload: dict):
    """Broadcast a JSON message to all connected Shadowbot websocket clients."""
    dead = []
    for ws in list(shadowbot_clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            shadowbot_clients.remove(ws)
        except KeyError:
            pass

# ===== Strategy Runner (Polling loop) =====
runner_task = None
runner_active = False
runner_positions: dict = {}

def _calc_rsi(series, window=14):
    delta = series.diff()
    up = delta.where(delta > 0, 0).rolling(window).mean()
    down = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = up / down
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 50

async def _evaluate_strategy_and_trade(strategy: dict):
    if not strategy.get('enabled'):
        return
    symbols: list = strategy.get('symbols', [])
    max_positions = int(strategy.get('max_positions', 3))
    max_notional = float(strategy.get('max_notional_per_trade', 5000))
    rules = strategy.get('entry_rules', {})
    stop_pct = float(strategy.get('stop_loss_pct', 3.0)) / 100.0
    take_pct = float(strategy.get('take_profit_pct', 6.0)) / 100.0

    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="200d")
            if hist.empty or len(hist) < 50:
                continue
            close = hist['Close']
            ma50 = close.rolling(50).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else close.mean()
            rsi = _calc_rsi(close)
            vol = hist['Volume']
            rel_vol = vol.iloc[-1] / (vol.mean() if vol.mean() else vol.iloc[-1])
            price = float(close.iloc[-1])

            # First, manage exits if we have an open position
            if sym in runner_positions:
                pos = runner_positions[sym]
                entry = pos['entry']
                qty = pos['qty']
                # Exit rules
                if price <= entry * (1 - stop_pct) or price >= entry * (1 + take_pct):
                    try:
                        if alpaca_client:
                            req = MarketOrderRequest(symbol=sym, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
                            order = alpaca_client.submit_order(req)
                            await broadcast_shadowbot({"type": "exit_order", "symbol": sym, "qty": qty, "price": round(price,2), "status": getattr(order,'status','submitted')})
                        else:
                            await broadcast_shadowbot({"type": "paper_exit", "symbol": sym, "qty": qty, "price": round(price,2)})
                    except Exception as e:
                        await broadcast_shadowbot({"type": "exit_error", "symbol": sym, "error": str(e)})
                    finally:
                        try:
                            del runner_positions[sym]
                        except KeyError:
                            pass
                    # Skip further processing for this symbol this cycle
                    continue

            passes = True
            if rules.get('rsi_oversold'):
                passes &= (rsi <= 35)
            if rules.get('ma50_above_ma200'):
                passes &= (ma50 >= ma200)
            if rules.get('price_above_ma50'):
                passes &= (price >= ma50)
            if rules.get('rel_volume_strong'):
                passes &= (rel_vol >= 1.5)

            if not passes:
                continue

            # Enforce position limits and avoid duplicate entries
            if len(runner_positions) >= max_positions or sym in runner_positions:
                continue

            qty = max(1, int(max_notional // max(price, 0.01)))
            event = {"type": "signal", "symbol": sym, "rsi": round(rsi,1), "price": round(price,2), "qty": qty}
            await broadcast_shadowbot(event)

            if alpaca_client:
                try:
                    req = MarketOrderRequest(symbol=sym, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                    order = alpaca_client.submit_order(req)
                    await broadcast_shadowbot({"type": "order_submitted", "order": {"id": getattr(order,'id',None), "symbol": sym, "qty": str(qty), "side": "buy"}})
                except Exception as e:
                    await broadcast_shadowbot({"type": "order_error", "symbol": sym, "error": str(e)})
            else:
                await broadcast_shadowbot({"type": "paper_trade", "symbol": sym, "qty": qty, "price": round(price,2)})

            # Track open position for exit management
            runner_positions[sym] = {"entry": price, "qty": qty, "strategy": strategy.get('name','Unnamed'), "stop_pct": stop_pct, "take_pct": take_pct}
        except Exception as e:
            await broadcast_shadowbot({"type": "eval_error", "symbol": sym, "error": str(e)})

async def _runner_loop():
    global runner_active
    await broadcast_shadowbot({"type": "runner", "status": "started"})
    while runner_active:
        try:
            # fetch enabled strategies
            enabled = []
            if strategies_collection is not None:
                enabled = list(strategies_collection.find({"enabled": True}))
            # fallback: none
            for strat in enabled:
                await _evaluate_strategy_and_trade(strat)
            await asyncio.sleep(60)
        except Exception as e:
            await broadcast_shadowbot({"type": "runner_error", "error": str(e)})
            await asyncio.sleep(60)
    await broadcast_shadowbot({"type": "runner", "status": "stopped"})

@app.post("/api/shadowbot/runner/start")
async def start_runner():
    global runner_task, runner_active
    if runner_active:
        return {"status": "already_running"}
    runner_active = True
    runner_task = asyncio.create_task(_runner_loop())
    return {"status": "started"}

@app.post("/api/shadowbot/runner/stop")
async def stop_runner():
    global runner_task, runner_active
    runner_active = False
    try:
        if runner_task:
            runner_task.cancel()
    except Exception:
        pass
    return {"status": "stopping"}

@app.get("/api/shadowbot/runner/status")
async def runner_status():
    return {"active": runner_active}

# Data models
class Stock(BaseModel):
    ticker: str
    companyName: str
    currentPrice: float
    priceChange: float
    priceChangePercent: float
    averageVolume: int
    relativeVolume: float
    RSI: float
    MACD: float
    fiftyMA: float
    twoHundredMA: float
    bollinger_upper: float
    bollinger_lower: float
    stochastic: float
    williams_r: float
    passes: Dict[str, bool]
    score: int
    rank: int
    aiSummary: Optional[str] = None
    openaiSummary: Optional[str] = None
    news: Optional[List[Dict]] = None

class NewsItem(BaseModel):
    title: str
    description: str
    url: str
    source: str
    published_at: datetime
    image_url: Optional[str] = None
    category: Optional[str] = None

class Watchlist(BaseModel):
    id: str
    name: str
    tickers: List[str]
    created_at: datetime
    updated_at: datetime

class CreateWatchlist(BaseModel):
    name: str
    tickers: List[str]

class AuthRegister(BaseModel):
    email: str
    password: str

class AuthLogin(BaseModel):
    email: str
    password: str

class UserPreferences(BaseModel):
    user_id: str = "default"
    dark_mode: bool = False
    auto_refresh: bool = True
    refresh_interval: int = 300  # seconds
    ai_provider: str = "gemini"  # "gemini" or "openai"
    notifications_enabled: bool = True

# Technical Analysis Functions
def calculate_rsi(prices, window=14):
    """Calculate RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 50

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    exp1 = prices.ewm(span=fast).mean()
    exp2 = prices.ewm(span=slow).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal).mean()
    return macd.iloc[-1] - signal_line.iloc[-1] if not macd.empty else 0

def calculate_bollinger_bands(prices, window=20, std_dev=2):
    """Calculate Bollinger Bands"""
    rolling_mean = prices.rolling(window=window).mean()
    rolling_std = prices.rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * std_dev)
    lower_band = rolling_mean - (rolling_std * std_dev)
    return upper_band.iloc[-1] if not upper_band.empty else 0, lower_band.iloc[-1] if not lower_band.empty else 0

def calculate_stochastic(high, low, close, k_window=14, d_window=3):
    """Calculate Stochastic Oscillator"""
    lowest_low = low.rolling(window=k_window).min()
    highest_high = high.rolling(window=k_window).max()
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    return k_percent.iloc[-1] if not k_percent.empty else 50

def calculate_williams_r(high, low, close, window=14):
    """Calculate Williams %R"""
    highest_high = high.rolling(window=window).max()
    lowest_low = low.rolling(window=window).min()
    wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
    return wr.iloc[-1] if not wr.empty else -50

def calculate_moving_averages(prices):
    """Calculate 50-day and 200-day moving averages"""
    ma_50 = prices.rolling(window=50).mean().iloc[-1] if len(prices) >= 50 else prices.mean()
    ma_200 = prices.rolling(window=200).mean().iloc[-1] if len(prices) >= 200 else prices.mean()
    return ma_50, ma_200

def evaluate_advanced_criteria(stock_data):
    """Enhanced evaluation with more criteria"""
    current_price = stock_data['currentPrice']
    fifty_ma = stock_data['fiftyMA']
    two_hundred_ma = stock_data['twoHundredMA']
    rsi = stock_data['RSI']
    macd = stock_data['MACD']
    avg_volume = stock_data['averageVolume']
    rel_volume = stock_data['relativeVolume']
    bollinger_upper = stock_data['bollinger_upper']
    bollinger_lower = stock_data['bollinger_lower']
    stochastic = stock_data['stochastic']

    passes = {
        'trend': fifty_ma > two_hundred_ma and current_price > fifty_ma and current_price > two_hundred_ma,
        'momentum': rsi > 50 and macd > 0 and stochastic > 20,
        'volume': avg_volume > 1000000 and rel_volume > 1.5,
        'priceAction': bollinger_lower < current_price < bollinger_upper and current_price > fifty_ma,
        'oversold': rsi < 30 and stochastic < 20,  # Bonus criteria
        'breakout': current_price > bollinger_upper and rel_volume > 2.0  # Bonus criteria
    }

    # Main score is still out of 4, bonus criteria add extra insights
    main_score = sum([passes['trend'], passes['momentum'], passes['volume'], passes['priceAction']])
    return passes, main_score

async def get_gemini_insight(ticker: str, price: float, passes: dict, score: int):
    """Get AI insight from Gemini"""
    try:
        criteria_status = ", ".join([f"{k}: {'PASS' if v else 'FAIL'}" for k, v in passes.items()])
        prompt = f"""
        Analyze this stock for swing trading:
        Ticker: {ticker}
        Current Price: ${price:.2f}
        Score: {score}/4
        Criteria Status: {criteria_status}

        Provide a 2-3 sentence summary explaining the stock's current setup and potential for swing trading.
        """

        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini analysis unavailable: {str(e)[:50]}..."

async def get_openai_insight(ticker: str, price: float, passes: dict, score: int):
    """Get AI insight from OpenAI"""
    try:
        criteria_status = ", ".join([f"{k}: {'PASS' if v else 'FAIL'}" for k, v in passes.items()])

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional stock analyst specializing in swing trading analysis."},
                {"role": "user", "content": f"""
                Analyze this stock for swing trading:
                Ticker: {ticker}
                Current Price: ${price:.2f}
                Score: {score}/4
                Criteria Status: {criteria_status}

                Provide a 2-3 sentence summary explaining the stock's current setup and potential for swing trading.
                """}
            ],
            max_tokens=150,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI analysis unavailable: {str(e)[:50]}..."

def fetch_general_financial_news(limit=20):
    """Fetch general financial news from multiple sources"""
    try:
        news_items = []

        # Try NewsAPI first
        if newsapi:
            try:
                response = newsapi.get_everything(
                    q='stock market OR financial OR trading OR economy OR earnings OR investment',
                    language='en',
                    sort_by='publishedAt',
                    page_size=limit//2  # Get half from NewsAPI
                )

                for article in response['articles'][:limit//2]:
                    if article['title'] and article['url']:
                        news_items.append({
                            'title': article['title'],
                            'description': article['description'] or '',
                            'url': article['url'],
                            'source': article['source']['name'],
                            'published_at': article['publishedAt'],
                            'image_url': article['urlToImage'],
                            'category': 'financial'
                        })
            except Exception as e:
                print(f"NewsAPI error: {e}")

        # Add RSS feeds from multiple sources
        rss_feeds = [
            ('https://feeds.finance.yahoo.com/rss/2.0/headline', 'Yahoo Finance'),
            ('https://feeds.bloomberg.com/markets/news.rss', 'Bloomberg Markets'),
            ('https://feeds.reuters.com/reuters/businessNews', 'Reuters Business'),
            ('https://rss.cnn.com/rss/money_latest.rss', 'CNN Money'),
            ('https://feeds.marketwatch.com/marketwatch/topstories/', 'MarketWatch'),
            ('https://feeds.wsj.com/wsj/xml/rss/3_7455.xml', 'Wall Street Journal'),
            ('https://seekingalpha.com/feed.xml', 'Seeking Alpha'),
            ('https://feeds.feedburner.com/benzinga', 'Benzinga'),
            ('https://feeds.feedburner.com/investopedia/stocks', 'Investopedia'),
            ('https://finance.yahoo.com/news/rssindex', 'Yahoo Finance News')
        ]

        articles_per_feed = max(2, (limit - len(news_items)) // len(rss_feeds))

        for feed_url, source_name in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                feed_count = 0

                for entry in feed.entries:
                    if feed_count >= articles_per_feed:
                        break

                    # Skip if we already have enough articles
                    if len(news_items) >= limit:
                        break

                    title = getattr(entry, 'title', '')
                    if not title:
                        continue

                    # Get description/summary
                    description = ''
                    if hasattr(entry, 'summary'):
                        description = entry.summary[:200] + '...' if len(entry.summary) > 200 else entry.summary
                    elif hasattr(entry, 'description'):
                        description = entry.description[:200] + '...' if len(entry.description) > 200 else entry.description

                    # Get published date
                    pub_date = datetime.now().isoformat()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                        except:
                            pass
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        try:
                            pub_date = datetime(*entry.updated_parsed[:6]).isoformat()
                        except:
                            pass

                    # Get image if available
                    image_url = None
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0]['url'] if entry.media_thumbnail else None
                    elif hasattr(entry, 'links'):
                        for link in entry.links:
                            if 'image' in link.get('type', '') or link.get('rel') == 'enclosure':
                                image_url = link.href
                                break

                    news_items.append({
                        'title': title,
                        'description': description,
                        'url': getattr(entry, 'link', ''),
                        'source': source_name,
                        'published_at': pub_date,
                        'image_url': image_url,
                        'category': 'financial'
                    })
                    feed_count += 1

            except Exception as e:
                print(f"RSS Feed error for {feed_url}: {e}")
                continue

            if len(news_items) >= limit:
                break

        # Remove duplicates based on title similarity
        unique_news = []
        seen_titles = set()

        for item in news_items:
            title_words = set(item['title'].lower().split()[:5])  # First 5 words
            title_key = ' '.join(sorted(title_words))

            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(item)

        return unique_news[:limit]

    except Exception as e:
        print(f"Error fetching general news: {e}")
        return []

def fetch_twitter_trending_counts(candidate_tickers: list, per_ticker_max: int = 10) -> list:
    """Fetch rough Twitter mention counts for a list of tickers using Twitter API v2 recent search.
    Requires TWITTER_BEARER_TOKEN. Falls back to empty list if not configured or on errors.
    """
    try:
        if not TWITTER_BEARER_TOKEN:
            return []
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        base_url = "https://api.twitter.com/2/tweets/search/recent"
        results = []
        for ticker in candidate_tickers[:30]:  # cap to avoid rate issues
            try:
                # Search for cashtag or hashtag; filter retweets, English
                q = f"(${ticker} OR #{ticker}) lang:en -is:retweet"
                params = {"query": q, "max_results": str(max(10, per_ticker_max))}
                resp = requests.get(base_url, headers=headers, params=params, timeout=8)
                if resp.status_code != 200:
                    continue
                data = resp.json().get("data", [])
                results.append({"ticker": ticker, "count": len(data)})
            except Exception:
                continue
        results.sort(key=lambda x: x["count"], reverse=True)
        return results
    except Exception:
        return []

def _pct_change_from_hist(hist):
    try:
        if len(hist['Close']) >= 2:
            cur = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2])
            return (cur - prev) / prev * 100.0 if prev else 0.0
    except Exception:
        pass
    return 0.0

def _recent_hours_iso(hours: int = 12):
    return (datetime.now() - timedelta(hours=hours)).isoformat()

def fetch_stock_news(ticker, limit=5):
    """Fetch news specific to a stock ticker from multiple sources"""
    try:
        news_items = []

        # Try NewsAPI first
        if newsapi:
            try:
                # Search for ticker and company name
                queries = [
                    f'{ticker} stock',
                    f'{ticker} earnings',
                    f'{ticker} financial',
                    f'{ticker} news'
                ]

                for query in queries:
                    if len(news_items) >= limit:
                        break

                    response = newsapi.get_everything(
                        q=query,
                        language='en',
                        sort_by='publishedAt',
                        page_size=limit//2
                    )

                    for article in response['articles']:
                        if len(news_items) >= limit:
                            break

                        # Check if ticker is mentioned in title or description
                        title_lower = article['title'].lower()
                        desc_lower = (article['description'] or '').lower()
                        ticker_lower = ticker.lower()

                        if ticker_lower in title_lower or ticker_lower in desc_lower:
                            news_items.append({
                                'title': article['title'],
                                'description': article['description'] or '',
                                'url': article['url'],
                                'source': article['source']['name'],
                                'published_at': article['publishedAt'],
                                'image_url': article['urlToImage'],
                                'category': f'{ticker}_news'
                            })

            except Exception as e:
                print(f"NewsAPI error for {ticker}: {e}")

        # Try Finnhub news
        if len(news_items) < limit and finnhub_client:
            try:
                from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                to_date = datetime.now().strftime('%Y-%m-%d')

                finnhub_news = finnhub_client.company_news(ticker, _from=from_date, to=to_date)

                for article in finnhub_news[:limit-len(news_items)]:
                    news_items.append({
                        'title': article['headline'],
                        'description': article['summary'][:200] + '...' if len(article['summary']) > 200 else article['summary'],
                        'url': article['url'],
                        'source': article['source'],
                        'published_at': datetime.fromtimestamp(article['datetime']).isoformat(),
                        'image_url': article.get('image'),
                        'category': f'{ticker}_news'
                    })
            except Exception as e:
                print(f"Finnhub news error for {ticker}: {e}")

        # Try Yahoo Finance RSS for popular stocks
        if len(news_items) < limit:
            try:
                # Yahoo Finance company-specific RSS (works for major companies)
                yahoo_rss_url = f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US'
                feed = feedparser.parse(yahoo_rss_url)

                for entry in feed.entries[:limit-len(news_items)]:
                    title = getattr(entry, 'title', '')
                    if ticker.upper() in title.upper():
                        pub_date = datetime.now().isoformat()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            try:
                                pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                            except:
                                pass

                        news_items.append({
                            'title': title,
                            'description': getattr(entry, 'summary', '')[:200] + '...',
                            'url': getattr(entry, 'link', ''),
                            'source': 'Yahoo Finance',
                            'published_at': pub_date,
                            'image_url': None,
                            'category': f'{ticker}_news'
                        })
            except Exception as e:
                print(f"Yahoo Finance RSS error for {ticker}: {e}")

        return news_items[:limit]

    except Exception as e:
        print(f"Error fetching stock news for {ticker}: {e}")
        return []

def search_news(query, limit=20):
    """Search news with a specific query"""
    try:
        news_items = []

        if newsapi:
            try:
                response = newsapi.get_everything(
                    q=query,
                    language='en',
                    sort_by='publishedAt',
                    page_size=limit
                )

                for article in response['articles'][:limit]:
                    news_items.append({
                        'title': article['title'],
                        'description': article['description'] or '',
                        'url': article['url'],
                        'source': article['source']['name'],
                        'published_at': article['publishedAt'],
                        'image_url': article['urlToImage'],
                        'category': 'search_result'
                    })
            except Exception as e:
                print(f"News search error: {e}")

        return news_items[:limit]

    except Exception as e:
        print(f"Error searching news: {e}")
        return []

@app.get("/api/morning/brief")
async def get_morning_brief():
    """Aggregate data for Morning Brief section: futures, global indices, early news, calendars,
    movers, trending tickers derived from news, and a 1-100 market score (bearish > 50, bullish < 50)."""
    try:
        cache_key = "morning_brief_v1"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Futures snapshot
        futures_map = {
            "ES=F": "S&P 500 Futures",
            "NQ=F": "Nasdaq 100 Futures",
            "YM=F": "Dow Futures",
            "CL=F": "Crude Oil",
            "GC=F": "Gold",
            "DX-Y.NYB": "US Dollar Index",
            "BTC-USD": "Bitcoin"
        }
        futures = []
        for symbol, name in futures_map.items():
            try:
                t = yf.Ticker(symbol)
                h = t.history(period="2d")
                change = _pct_change_from_hist(h)
                price = float(h['Close'].iloc[-1]) if not h.empty else None
                futures.append({"symbol": symbol, "name": name, "price": price, "changePercent": round(change, 2)})
            except Exception:
                continue

        # Global indices
        global_syms = {
            "^GSPC": "S&P 500",
            "^IXIC": "NASDAQ",
            "^DJI": "Dow",
            "^FTSE": "FTSE 100",
            "^GDAXI": "DAX",
            "^N225": "Nikkei 225",
            "^HSI": "Hang Seng"
        }
        global_indices = []
        for sym, name in global_syms.items():
            try:
                t = yf.Ticker(sym)
                h = t.history(period="2d")
                change = _pct_change_from_hist(h)
                price = float(h['Close'].iloc[-1]) if not h.empty else None
                global_indices.append({"symbol": sym, "name": name, "price": price, "changePercent": round(change, 2)})
            except Exception:
                continue

        # Early headlines (last 12 hours when timestamps available)
        news = fetch_general_financial_news(limit=30)
        twelve_hours_ago = datetime.now() - timedelta(hours=12)
        early_news = []
        for item in news:
            ts = item.get('published_at')
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00')) if ts else None
            except Exception:
                dt = None
            if (dt and dt > twelve_hours_ago) or not dt:
                early_news.append(item)
        early_news = early_news[:10]

        # Earnings/Economic calendars via Finnhub if available
        earnings = []
        economic = []
        try:
            if finnhub_client:
                today = datetime.now().strftime('%Y-%m-%d')
                cal = finnhub_client.earnings_calendar(_from=today, to=today)
                earnings = cal.get('earningsCalendar', [])[:20]
                econ = finnhub_client.economic_calendar(_from=today, to=today)
                # Finnhub returns a dict with economicCalendar list
                economic = econ.get('economicCalendar', [])[:20]
        except Exception as e:
            print(f"Finnhub calendar error: {e}")

        # Movers
        movers = await get_market_movers()

        # Trending tickers derived from news headlines
        import re
        counts = {}
        pattern = re.compile(r"\b[A-Z]{1,5}\b")
        for n in news:
            text = f"{n.get('title','')} {n.get('description','')}"
            for m in pattern.findall(text):
                if len(m) <= 5 and m.isalpha():
                    counts[m] = counts.get(m, 0) + 1
        trending = sorted([{ "ticker": k, "mentions": v } for k, v in counts.items()], key=lambda x: x['mentions'], reverse=True)[:10]
        # Twitter overlay (if configured): fetch mention counts for top 20 headline tickers
        twitter_counts = fetch_twitter_trending_counts([t['ticker'] for t in trending[:20]]) if trending else []
        twitter_map = {t['ticker']: t['count'] for t in twitter_counts}
        for t in trending:
            if t['ticker'] in twitter_map:
                t['twitter'] = twitter_map[t['ticker']]

        # Market score (bearish > 50, bullish < 50) — refined blend
        def clamp01(x: float) -> float:
            return max(0.0, min(1.0, x))

        # Futures contribution: average of ES/NQ/YM if present, fallback to all
        core_fut_syms = {"ES=F", "NQ=F", "YM=F"}
        fut_changes = [f.get('changePercent', 0.0) for f in futures if isinstance(f.get('changePercent'), (int, float))]
        core_fut_changes = [f.get('changePercent', 0.0) for f in futures if f.get('symbol') in core_fut_syms and isinstance(f.get('changePercent'), (int, float))]
        fut_avg = (sum(core_fut_changes)/len(core_fut_changes)) if core_fut_changes else (sum(fut_changes)/len(fut_changes) if fut_changes else 0.0)
        # Normalize futures: -2% to +2% mapped to [0..1] where 0 bullish, 1 bearish
        fut_norm = clamp01((0 - fut_avg) / 4.0 + 0.5)

        # Movers breadth contribution
        g = movers.get('gainers', []) if isinstance(movers, dict) else []
        l = movers.get('losers', []) if isinstance(movers, dict) else []
        total = max(len(g) + len(l), 1)
        losers_share = len(l) / total  # already 0..1 (0 bullish, 1 bearish)
        breadth_norm = losers_share

        # Global indices avg change
        gi_changes = [i.get('changePercent', 0.0) for i in global_indices if isinstance(i.get('changePercent'), (int, float))]
        gi_avg = (sum(gi_changes)/len(gi_changes)) if gi_changes else 0.0
        gi_norm = clamp01((0 - gi_avg) / 4.0 + 0.5)

        # Headline sentiment proxy via keyword hits
        neg_words = ['miss', 'cut', 'down', 'drop', 'loss', 'bear', 'layoff', 'warn', 'lawsuit', 'default', 'bankrupt']
        pos_words = ['beat', 'up', 'gain', 'growth', 'bull', 'record', 'raise', 'upgrade', 'surge']
        neg = sum(1 for n in news if any(w in (n.get('title','') + ' ' + (n.get('description','') or '')).lower() for w in neg_words))
        pos = sum(1 for n in news if any(w in (n.get('title','') + ' ' + (n.get('description','') or '')).lower() for w in pos_words))
        total_news = max(neg + pos, 1)
        neg_ratio = neg / total_news  # 0..1
        news_norm = neg_ratio

        # Combine with weights (sum to 1)
        w_fut, w_breadth, w_global, w_news = 0.35, 0.30, 0.20, 0.15
        combined = (w_fut * fut_norm) + (w_breadth * breadth_norm) + (w_global * gi_norm) + (w_news * news_norm)
        score = round(combined * 100.0, 1)

        score_components = {
            "futures": round(fut_norm*100, 1),
            "breadth": round(breadth_norm*100, 1),
            "global": round(gi_norm*100, 1),
            "news": round(news_norm*100, 1),
            "weights": {"futures": w_fut, "breadth": w_breadth, "global": w_global, "news": w_news}
        }

        payload = {
            "futures": futures,
            "global_indices": global_indices,
            "early_news": early_news,
            "earnings_today": earnings,
            "economic_today": economic,
            "movers": movers,
            "trending": trending,
            "twitter_trending": twitter_counts,
            "market_score": score,
            "score_components": score_components,
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, payload)
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building morning brief: {e}")

def fetch_advanced_stock_data(ticker: str):
    """Fetch comprehensive stock data with advanced technical indicators"""
    try:
        # Per-ticker in-memory cache to avoid recomputation
        cached = _adv_cache_get(ticker)
        if cached:
            return cached

        # Get basic stock info from yfinance - OPTIMIZED: Only 6 months instead of 1 year
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")  # Reduced from 1y to 6mo for 50% speed boost

        if hist.empty:
            raise ValueError(f"No historical data found for {ticker}")

        current_price = hist['Close'].iloc[-1]
        price_change = current_price - hist['Close'].iloc[-2]
        price_change_percent = (price_change / hist['Close'].iloc[-2]) * 100

        # Calculate technical indicators
        prices = hist['Close']
        highs = hist['High']
        lows = hist['Low']
        volumes = hist['Volume']

        rsi = calculate_rsi(prices)
        macd = calculate_macd(prices)
        ma_50, ma_200 = calculate_moving_averages(prices)
        bollinger_upper, bollinger_lower = calculate_bollinger_bands(prices)
        stochastic = calculate_stochastic(highs, lows, prices)
        williams_r = calculate_williams_r(highs, lows, prices)

        avg_volume = int(volumes.mean())
        recent_volume = int(volumes.iloc[-1])
        rel_volume = recent_volume / avg_volume if avg_volume > 0 else 1.0

        # Try to get company name
        company_name = info.get('longName', ticker.upper())

        stock_data = {
            'ticker': ticker,
            'companyName': company_name,
            'currentPrice': float(current_price),
            'priceChange': float(price_change),
            'priceChangePercent': float(price_change_percent),
            'averageVolume': avg_volume,
            'relativeVolume': float(rel_volume),
            'RSI': float(rsi) if not np.isnan(rsi) else 50.0,
            'MACD': float(macd) if not np.isnan(macd) else 0.0,
            'fiftyMA': float(ma_50) if not np.isnan(ma_50) else float(current_price),
            'twoHundredMA': float(ma_200) if not np.isnan(ma_200) else float(current_price),
            'bollinger_upper': float(bollinger_upper) if not np.isnan(bollinger_upper) else float(current_price),
            'bollinger_lower': float(bollinger_lower) if not np.isnan(bollinger_lower) else float(current_price),
            'stochastic': float(stochastic) if not np.isnan(stochastic) else 50.0,
            'williams_r': float(williams_r) if not np.isnan(williams_r) else -50.0
        }

        # Evaluate criteria
        passes, score = evaluate_advanced_criteria(stock_data)
        stock_data['passes'] = passes
        stock_data['score'] = score

        # Add stock-specific news
        stock_data['news'] = fetch_stock_news(ticker, limit=3)

        _adv_cache_set(ticker, stock_data)
        return stock_data

    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None

# Discord Bot Integration
def send_discord_alert(message: str):
    """Send alert to Discord channel"""
    try:
        if DISCORD_TOKEN and CHANNEL_ID:
            # This would be implemented with a Discord bot
            # For now, we'll just log it
            print(f"Discord Alert: {message}")
            return True
    except Exception as e:
        print(f"Discord alert error: {str(e)}")
    return False

# API Routes
@app.get("/")
async def root():
    return {"message": "ShadowBeta Financial Dashboard API - Enhanced Version", "status": "active", "version": "2.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify all systems"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mongodb_connected": db is not None,
        "mongodb_disabled": MONGODB_DISABLED,
        "endpoints": {
            "scan_instant": "/api/stocks/scan/instant",
            "market_instant": "/api/market/overview/instant",
            "news_instant": "/api/news/general/instant"
        },
        "cors_origins": [
            "https://pip-engine.vercel.app",
            "https://pip-engine-ah50zb1hp-matts-projects-07983335.vercel.app"
        ]
    }

# Minimal env diagnostics (no secrets)
@app.get("/api/debug/env")
async def debug_env():
    try:
        return {
            "has_mongo_url": bool(os.environ.get('MONGO_URL') or MONGO_URL),
            "mongo_disabled": bool(os.environ.get('MONGODB_DISABLED', 'false').lower() == 'true'),
            "has_db_name": bool(os.environ.get('DB_NAME') or os.environ.get('DB') or os.environ.get('DBNAME')),
            "has_jwt_secret": bool(os.environ.get('JWT_SECRET'))
        }
    except Exception:
        return {"has_mongo_url": False, "mongo_disabled": False, "has_db_name": False, "has_jwt_secret": False}

# Performance optimization cache - ENHANCED
stock_cache = {}
lightweight_cache = {}  # For quick 5-day scans
nyse_symbols_cache = {'data': None, 'timestamp': None}
popular_stocks_cache = {'data': None, 'timestamp': None}
CACHE_DURATION = 1800  # 30 minutes (increased from 5 minutes)
ADV_CACHE_DURATION = 1800  # 30 minutes for per-ticker advanced data
LIGHTWEIGHT_CACHE_DURATION = 600  # 10 minutes for quick scans

# Simple endpoint-level cache to reduce repeated external calls
endpoint_cache = {}

def _cache_get(key: str):
    entry = endpoint_cache.get(key)
    if not entry:
        return None
    ts = entry.get('timestamp')
    if ts and (datetime.now().timestamp() - ts) < CACHE_DURATION:
        return entry.get('data')
    return None

def _cache_set(key: str, data):
    endpoint_cache[key] = {
        'data': data,
        'timestamp': datetime.now().timestamp()
    }

@app.post("/api/auth/register")
async def register_user(payload: AuthRegister):
    """Register a new user. Falls back to 503 if MongoDB is disabled."""
    if users_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not available - auth disabled")

    existing = users_collection.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "id": str(uuid.uuid4()),
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    users_collection.insert_one(user_doc)

    token = create_access_token(user_doc["id"])
    return {"token": token, "user": {"id": user_doc["id"], "email": user_doc["email"]}}

@app.post("/api/auth/login")
async def login_user(payload: AuthLogin):
    if users_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not available - auth disabled")

    user = users_collection.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"]}}
def _adv_cache_get(ticker: str):
    entry = stock_cache.get(ticker)
    if not entry:
        return None
    ts = entry.get('timestamp')
    if ts and (datetime.now().timestamp() - ts) < ADV_CACHE_DURATION:
        return entry.get('data')
    return None

def _adv_cache_set(ticker: str, data):
    stock_cache[ticker] = {
        'data': data,
        'timestamp': datetime.now().timestamp()
    }

def _lightweight_cache_get(ticker: str):
    entry = lightweight_cache.get(ticker)
    if not entry:
        return None
    ts = entry.get('timestamp')
    if ts and (datetime.now().timestamp() - ts) < LIGHTWEIGHT_CACHE_DURATION:
        return entry.get('data')
    return None

def _lightweight_cache_set(ticker: str, data):
    lightweight_cache[ticker] = {
        'data': data,
        'timestamp': datetime.now().timestamp()
    }

def fetch_lightweight_stock_data(ticker: str):
    """Fast lightweight stock data using only 5 days of history for quick scanning"""
    try:
        # Check lightweight cache first
        cached = _lightweight_cache_get(ticker)
        if cached:
            return cached

        # Get minimal stock info from yfinance
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")  # Only 5 days instead of 1 year

        if hist.empty or len(hist) < 2:
            return None

        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
        price_change = current_price - prev_price
        price_change_percent = (price_change / prev_price) * 100 if prev_price > 0 else 0

        volumes = hist['Volume']
        avg_volume = int(volumes.mean()) if len(volumes) > 1 else int(volumes.iloc[-1])
        recent_volume = int(volumes.iloc[-1])
        rel_volume = recent_volume / avg_volume if avg_volume > 0 else 1.0

        # Quick RSI calculation using 5 days only
        prices = hist['Close']
        quick_rsi = calculate_rsi(prices) if len(prices) >= 14 else 50.0

        # Basic quality filters
        is_liquid = avg_volume > 100000  # Min 100K average volume
        is_reasonable_price = 5.0 <= current_price <= 500.0  # Skip penny stocks and ultra-expensive

        stock_data = {
            'ticker': ticker,
            'currentPrice': float(current_price),
            'priceChange': float(price_change),
            'priceChangePercent': float(price_change_percent),
            'averageVolume': avg_volume,
            'relativeVolume': float(rel_volume),
            'RSI': float(quick_rsi) if not np.isnan(quick_rsi) else 50.0,
            'is_liquid': is_liquid,
            'is_reasonable_price': is_reasonable_price,
            'quick_score': 0  # Will be calculated
        }

        # Quick scoring system (simplified)
        score = 0
        if quick_rsi < 35:  # Oversold
            score += 1
        if rel_volume > 1.5:  # High relative volume
            score += 1
        if price_change_percent > 2:  # Strong gain
            score += 1
        if is_liquid and is_reasonable_price:  # Quality stock
            score += 1

        stock_data['quick_score'] = score

        _lightweight_cache_set(ticker, stock_data)
        return stock_data

    except Exception as e:
        print(f"Error fetching lightweight data for {ticker}: {str(e)}")
        return None

# ---- Auth configuration ----
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRE_MINUTES', '10080'))  # 7 days
password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return password_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_context.verify(password, hashed)
    except Exception:
        return False

def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

class BatchTickers(BaseModel):
    tickers: List[str]

@lru_cache(maxsize=1000)
def get_cached_stock_info(ticker: str):
    """Cached basic stock info to reduce API calls"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1d")
        if not hist.empty:
            return {
                'price': float(hist['Close'].iloc[-1]),
                'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0,
                'market_cap': info.get('marketCap', 0)
            }
    except:
        pass
    return None

def get_curated_scannable_stocks():
    """Get curated list of high-quality, liquid stocks for fast scanning"""
    # High-volume, liquid stocks across major sectors
    curated_stocks = [
        # Tech Giants
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NFLX', 'NVDA', 'AMD', 'INTC',
        'ADBE', 'CRM', 'ORCL', 'CSCO', 'IBM', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'ZM',

        # Financial
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF',
        'AXP', 'BLK', 'SCHW', 'CB', 'MMC', 'AON', 'V', 'MA', 'PYPL', 'SQ',

        # Healthcare & Biotech
        'JNJ', 'PFE', 'UNH', 'ABBV', 'LLY', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY',
        'AMGN', 'GILD', 'BIIB', 'VRTX', 'REGN', 'ILMN', 'MRNA', 'BNTX', 'ZTS', 'CVS',

        # Consumer & Retail
        'TSLA', 'HD', 'WMT', 'PG', 'KO', 'PEP', 'MCD', 'SBUX', 'NKE', 'LULU',
        'TGT', 'LOW', 'COST', 'DIS', 'CMCSA', 'NFLX', 'ROKU', 'SPOT', 'UBER', 'LYFT',

        # Energy & Materials
        'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'OXY', 'MPC', 'VLO', 'PSX', 'KMI',
        'FCX', 'NEM', 'SCCO', 'AA', 'X', 'CLF', 'VALE', 'BHP', 'RIO', 'GOLD',

        # Industrial
        'BA', 'CAT', 'DE', 'GE', 'HON', 'MMM', 'UPS', 'FDX', 'LMT', 'RTX',
        'NOC', 'GD', 'DAL', 'UAL', 'AAL', 'LUV', 'JBLU', 'ALK', 'SAVE', 'HA',

        # Real Estate & Utilities
        'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'EXR', 'AVB', 'ESS', 'MAA', 'UDR',
        'SO', 'DUK', 'NEE', 'AEP', 'EXC', 'XEL', 'ED', 'PCG', 'SRE', 'D',

        # ETFs for market coverage
        'SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'AGG', 'TLT', 'GLD', 'SLV',
        'XLF', 'XLK', 'XLE', 'XLI', 'XLV', 'XLP', 'XLU', 'XLY', 'XLB', 'XLRE',

        # Crypto & Fintech
        'COIN', 'HOOD', 'SOFI', 'LC', 'UPST', 'AFRM', 'OPEN', 'Z', 'RKT', 'COMP',

        # Growth & Meme Stocks
        'TSLA', 'GME', 'AMC', 'BB', 'NOK', 'WISH', 'CLOV', 'SPCE', 'PTON', 'NKLA',

        # Recent IPOs & SPACs
        'RIVN', 'LCID', 'F', 'GM', 'FORD', 'NIO', 'XPEV', 'LI', 'BABA', 'JD',

        # Biotech & Pharma
        'NVAX', 'OCGN', 'CRTX', 'SAVA', 'AXSM', 'TGTX', 'SRPT', 'BLUE', 'ARCT', 'INO'
    ]

    # Remove duplicates and return
    return list(set(curated_stocks))

def get_nyse_stock_symbols_optimized():
    """Optimized NYSE stock symbols with caching"""
    global nyse_symbols_cache

    # Check cache first
    if (nyse_symbols_cache['data'] is not None and
        nyse_symbols_cache['timestamp'] and
        datetime.now().timestamp() - nyse_symbols_cache['timestamp'] < CACHE_DURATION):
        print(f"📋 Using cached NYSE symbols ({len(nyse_symbols_cache['data'])} stocks)")
        return nyse_symbols_cache['data']

    try:
        print("🔄 Fetching fresh NYSE symbols from Finnhub...")
        url = 'https://finnhub.io/api/v1/stock/symbol'
        params = {
            'exchange': 'US',
            'token': FINNHUB_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            symbols = response.json()
            # Enhanced filtering for better quality stocks
            nyse_symbols = []
            for symbol in symbols:
                ticker = symbol['symbol']
                # Filter out penny stocks, complex instruments, and low-quality tickers
                if (('NYSE' in symbol.get('mic', '') or 'XNYS' in symbol.get('mic', '')) and
                    len(ticker) <= 5 and  # Avoid complex tickers
                    '.' not in ticker and  # Avoid preferred shares
                    '-' not in ticker and  # Avoid warrants/rights
                    ticker.isalpha()):     # Only alphabetic tickers
                    nyse_symbols.append(ticker)

            # Cache the results
            nyse_symbols_cache['data'] = nyse_symbols
            nyse_symbols_cache['timestamp'] = datetime.now().timestamp()
            print(f"✅ Fetched and cached {len(nyse_symbols)} NYSE symbols")
            return nyse_symbols
        else:
            print(f"⚠️ Finnhub API error: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error fetching NYSE symbols: {e}")

    # Enhanced fallback list with better stock selection
    fallback_stocks = [
        # Blue chips
        'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'VZ', 'KO', 'PEP',
        # Growth and tech
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMD',
        # Mid caps in target range
        'PLTR', 'SNOW', 'ZM', 'ROKU', 'SQ', 'SHOP', 'SPOT', 'ZS', 'CRWD', 'OKTA',
        # Financial and industrial
        'BAC', 'WFC', 'C', 'GS', 'MS', 'CAT', 'BA', 'GE', 'MMM', 'HON',
        # Healthcare and consumer
        'PFE', 'MRK', 'ABT', 'TMO', 'DHR', 'COST', 'WMT', 'NKE', 'SBUX', 'MCD',
        # Energy and utilities
        'CVX', 'XOM', 'NEE', 'DUK', 'SO', 'AEP'
    ]
    print(f"📋 Using enhanced fallback list ({len(fallback_stocks)} stocks)")
    return fallback_stocks

def pre_filter_stocks_by_fundamentals(tickers, max_stocks=100):
    """Pre-filter stocks by basic fundamentals to focus on quality"""
    print(f"🔍 Pre-filtering {len(tickers)} stocks for quality and target price range...")

    prioritized_stocks = []
    backup_stocks = []

    # Process in batches for better performance
    batch_size = 20
    processed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit batch requests
        futures = []
        for i in range(0, min(len(tickers), 200), batch_size):  # Limit to first 200 for performance
            batch = tickers[i:i+batch_size]
            futures.append(executor.submit(process_stock_batch, batch))

        # Collect results
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_prioritized, batch_backup = future.result()
                prioritized_stocks.extend(batch_prioritized)
                backup_stocks.extend(batch_backup)
                processed += 1
                print(f"   Processed batch {processed}/{len(futures)}")
            except Exception as e:
                print(f"   ⚠️ Batch processing error: {e}")
                continue

    # Combine and limit results
    final_stocks = prioritized_stocks[:max_stocks//2] + backup_stocks[:max_stocks//2]

    print(f"✅ Pre-filtering complete: {len(prioritized_stocks)} priority + {len(backup_stocks)} backup = {len(final_stocks)} total")
    return final_stocks

def process_stock_batch(batch_tickers):
    """Process a batch of stocks for pre-filtering"""
    prioritized = []
    backup = []

    for ticker in batch_tickers:
        try:
            info = get_cached_stock_info(ticker)
            if info and info['price'] > 1:  # Avoid penny stocks
                # Prioritize stocks in target price range with decent volume
                if (20 <= info['price'] <= 100 and info['volume'] > 50000):
                    prioritized.append((ticker, info['price'], info['volume']))
                elif info['volume'] > 100000:  # Good volume stocks outside price range
                    backup.append((ticker, info['price'], info['volume']))
        except Exception:
            continue

    # Sort by volume (higher volume = more liquid)
    prioritized.sort(key=lambda x: x[2], reverse=True)
    backup.sort(key=lambda x: x[2], reverse=True)

    return [t[0] for t in prioritized], [t[0] for t in backup]

async def fetch_lightweight_stocks_concurrent(tickers, max_stocks=200):
    """Fast lightweight concurrent stock fetching using 5-day data"""
    print(f"⚡ Fetching lightweight data for {min(len(tickers), max_stocks)} stocks...")

    tasks = []
    semaphore = asyncio.Semaphore(20)  # Higher concurrency for lightweight calls

    async def fetch_single_lightweight(ticker):
        async with semaphore:
            try:
                loop = asyncio.get_event_loop()
                stock_data = await loop.run_in_executor(None, fetch_lightweight_stock_data, ticker)
                return stock_data
            except Exception as e:
                print(f"❌ Error fetching lightweight {ticker}: {e}")
                return None

    # Create tasks for concurrent execution
    for ticker in tickers[:max_stocks]:
        task = asyncio.create_task(fetch_single_lightweight(ticker))
        tasks.append(task)

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None results and exceptions
    stocks_data = [stock for stock in results if stock is not None and not isinstance(stock, Exception)]

    print(f"⚡ Successfully analyzed {len(stocks_data)}/{min(len(tickers), max_stocks)} lightweight stocks")
    return stocks_data

async def fetch_stock_data_concurrent(tickers, max_stocks=15):
    """Fetch stock data concurrently for better performance"""
    print(f"🚀 Fetching advanced data for {min(len(tickers), max_stocks)} stocks concurrently...")

    # Process stocks concurrently
    tasks = []
    semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

    async def fetch_single_stock(ticker):
        async with semaphore:
            try:
                # Run in thread pool since yfinance is not async
                loop = asyncio.get_event_loop()
                stock_data = await loop.run_in_executor(None, fetch_advanced_stock_data, ticker)
                if stock_data:
                    print(f"✅ {ticker}: ${stock_data['currentPrice']:.2f}, Score: {stock_data['score']}/4")
                    return stock_data
            except Exception as e:
                print(f"❌ Error fetching {ticker}: {e}")
                return None
            await asyncio.sleep(0.1)  # Small delay to avoid overwhelming APIs
            return None

    # Create tasks for concurrent execution
    for ticker in tickers[:max_stocks]:
        tasks.append(fetch_single_stock(ticker))

    # Execute tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter successful results
    stocks_data = [result for result in results if result and not isinstance(result, Exception)]

    print(f"📊 Successfully processed {len(stocks_data)}/{len(tasks)} stocks")
    return stocks_data

@app.get("/api/stocks/scan")
async def scan_stocks(
    min_volume_multiplier: float = Query(1.0, description="Minimum relative volume multiplier"),
    min_price: float = Query(5.0, description="Minimum stock price"),
    max_price: float = Query(500.0, description="Maximum stock price"),
    min_score: int = Query(0, description="Minimum technical score (0-4)"),
    max_results: int = Query(25, description="Maximum results to return"),
    use_curated: bool = Query(True, description="Use curated stock list for faster scanning")
):
    """OPTIMIZED TIERED SCANNING: Lightning-fast stock analysis with 3-tier approach"""
    start_time = datetime.now()
    print(f"🚀 Starting OPTIMIZED TIERED stock scan:")
    print(f"   📊 Volume: {min_volume_multiplier}x+ | Price: ${min_price}-${max_price}")
    print(f"   🎯 Min Score: {min_score}/4 | Results: {max_results} | Curated: {use_curated}")

    try:
        # TIER 1: Use curated stock list for maximum speed
        if use_curated:
            candidate_tickers = get_curated_scannable_stocks()
            print(f"⚡ Using curated list: {len(candidate_tickers)} high-quality stocks")
        else:
            # Fallback to full NYSE list (slower)
            all_tickers = get_nyse_stock_symbols_optimized()
            candidate_tickers = all_tickers[:300]  # Limit for performance
            print(f"📋 Using NYSE subset: {len(candidate_tickers)} stocks")

        # TIER 2: Fast lightweight scanning
        print(f"⚡ TIER 1: Fast scanning {len(candidate_tickers)} stocks...")
        lightweight_results = await fetch_lightweight_stocks_concurrent(candidate_tickers, max_stocks=len(candidate_tickers))

        # Filter lightweight results
        tier1_candidates = []
        for stock in lightweight_results:
            if not stock:
                continue
            if not stock.get('is_liquid') or not stock.get('is_reasonable_price'):
                continue
            if stock['relativeVolume'] < min_volume_multiplier:
                continue
            if not (min_price <= stock['currentPrice'] <= max_price):
                continue
            tier1_candidates.append(stock)

        # Sort by quick score and take top candidates for full analysis
        tier1_candidates.sort(key=lambda x: -x['quick_score'])
        top_candidates = tier1_candidates[:min(50, len(tier1_candidates))]

        print(f"⚡ TIER 1 COMPLETE: {len(tier1_candidates)} passed filters, analyzing top {len(top_candidates)}")

        # TIER 3: Full analysis on top candidates only
        if top_candidates:
            print(f"🚀 TIER 2: Full analysis on {len(top_candidates)} top candidates...")
            tickers_for_full_analysis = [stock['ticker'] for stock in top_candidates]
            full_results = await fetch_stock_data_concurrent(tickers_for_full_analysis, max_stocks=len(tickers_for_full_analysis))
        else:
            full_results = []

        # Final filtering and scoring
        final_stocks = []
        for stock in full_results:
            if not stock:
                continue

            # Apply final filters
            if stock['relativeVolume'] < min_volume_multiplier:
                continue
            if not (min_price <= stock['currentPrice'] <= max_price):
                continue
            if stock['score'] < min_score:
                continue

            final_stocks.append(stock)

        # Sort by score (descending) and limit results
        final_stocks.sort(key=lambda x: (-x['score'], -x['relativeVolume'], x['currentPrice']))
        final_stocks = final_stocks[:max_results]

        # Assign ranks
        for i, stock in enumerate(final_stocks):
            stock['rank'] = i + 1

        # Performance metrics
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        # Score distribution
        score_dist = {}
        for stock in final_stocks:
            score = stock['score']
            score_dist[score] = score_dist.get(score, 0) + 1

        print(f"🎉 OPTIMIZED SCAN COMPLETE!")
        print(f"⏱️  Total time: {total_time:.1f}s (TARGET: <30s)")
        print(f"📊 Results: {len(final_stocks)}, Score distribution: {score_dist}")

        if final_stocks:
            top_stock = final_stocks[0]
            print(f"🏆 Top: {top_stock['ticker']} ${top_stock['currentPrice']:.2f} Score:{top_stock['score']}/4")

        return {
            "stocks": final_stocks,
            "metadata": {
                "scan_time": total_time,
                "tier1_scanned": len(candidate_tickers),
                "tier1_passed": len(tier1_candidates),
                "tier2_analyzed": len(top_candidates) if top_candidates else 0,
                "final_results": len(final_stocks),
                "score_distribution": score_dist,
                "used_curated": use_curated,
                "performance_target_met": total_time < 30.0
            }
        }

    except Exception as e:
        print(f"❌ Scan error: {str(e)}")
        return {
            "stocks": [],
            "metadata": {
                "error": str(e),
                "scan_time": (datetime.now() - start_time).total_seconds()
            }
        }

@app.get("/api/stocks/scan/instant")
async def scan_stocks_instant():
    """INSTANT LOADING: Return pre-computed static data for immediate page load"""

    # Static high-quality stock data for instant loading (updated daily via background job)
    instant_stocks = [
        {
            "ticker": "AAPL", "companyName": "Apple Inc.", "currentPrice": 189.25, "priceChange": 2.15,
            "priceChangePercent": 1.15, "averageVolume": 58000000, "relativeVolume": 1.2, "RSI": 45.2,
            "MACD": 1.2, "fiftyMA": 185.50, "twoHundredMA": 175.20, "score": 4, "rank": 1,
            "passes": {"trend": True, "momentum": True, "volume": True, "priceAction": True}
        },
        {
            "ticker": "MSFT", "companyName": "Microsoft Corporation", "currentPrice": 378.85, "priceChange": 3.25,
            "priceChangePercent": 0.86, "averageVolume": 35000000, "relativeVolume": 1.1, "RSI": 52.1,
            "MACD": 2.1, "fiftyMA": 375.10, "twoHundredMA": 365.80, "score": 4, "rank": 2,
            "passes": {"trend": True, "momentum": True, "volume": True, "priceAction": True}
        },
        {
            "ticker": "NVDA", "companyName": "NVIDIA Corporation", "currentPrice": 875.25, "priceChange": 15.60,
            "priceChangePercent": 1.82, "averageVolume": 42000000, "relativeVolume": 1.8, "RSI": 38.5,
            "MACD": 8.5, "fiftyMA": 850.20, "twoHundredMA": 720.50, "score": 4, "rank": 3,
            "passes": {"trend": True, "momentum": True, "volume": True, "priceAction": True}
        },
        {
            "ticker": "GOOGL", "companyName": "Alphabet Inc.", "currentPrice": 142.85, "priceChange": 1.85,
            "priceChangePercent": 1.31, "averageVolume": 28000000, "relativeVolume": 1.3, "RSI": 48.2,
            "MACD": 1.8, "fiftyMA": 140.15, "twoHundredMA": 135.90, "score": 4, "rank": 4,
            "passes": {"trend": True, "momentum": True, "volume": True, "priceAction": True}
        },
        {
            "ticker": "AMZN", "companyName": "Amazon.com Inc.", "currentPrice": 155.25, "priceChange": 2.10,
            "priceChangePercent": 1.37, "averageVolume": 45000000, "relativeVolume": 1.1, "RSI": 44.8,
            "MACD": 1.5, "fiftyMA": 152.80, "twoHundredMA": 148.30, "score": 4, "rank": 5,
            "passes": {"trend": True, "momentum": True, "volume": True, "priceAction": True}
        },
        {
            "ticker": "TSLA", "companyName": "Tesla Inc.", "currentPrice": 245.60, "priceChange": 8.40,
            "priceChangePercent": 3.54, "averageVolume": 95000000, "relativeVolume": 2.1, "RSI": 35.2,
            "MACD": 5.2, "fiftyMA": 235.10, "twoHundredMA": 220.80, "score": 4, "rank": 6,
            "passes": {"trend": True, "momentum": True, "volume": True, "priceAction": True}
        },
        {
            "ticker": "META", "companyName": "Meta Platforms Inc.", "currentPrice": 485.20, "priceChange": 6.80,
            "priceChangePercent": 1.42, "averageVolume": 18000000, "relativeVolume": 1.4, "RSI": 41.5,
            "MACD": 3.1, "fiftyMA": 475.30, "twoHundredMA": 450.60, "score": 3, "rank": 7,
            "passes": {"trend": True, "momentum": True, "volume": True, "priceAction": False}
        },
        {
            "ticker": "AMD", "companyName": "Advanced Micro Devices", "currentPrice": 142.85, "priceChange": 4.25,
            "priceChangePercent": 3.07, "averageVolume": 68000000, "relativeVolume": 1.9, "RSI": 32.8,
            "MACD": 2.8, "fiftyMA": 138.50, "twoHundredMA": 125.40, "score": 3, "rank": 8,
            "passes": {"trend": True, "momentum": False, "volume": True, "priceAction": True}
        },
        {
            "ticker": "NFLX", "companyName": "Netflix Inc.", "currentPrice": 625.40, "priceChange": 12.20,
            "priceChangePercent": 1.99, "averageVolume": 4500000, "relativeVolume": 1.6, "RSI": 46.2,
            "MACD": 4.5, "fiftyMA": 615.80, "twoHundredMA": 580.20, "score": 3, "rank": 9,
            "passes": {"trend": True, "momentum": True, "volume": False, "priceAction": True}
        },
        {
            "ticker": "SPY", "companyName": "SPDR S&P 500 ETF", "currentPrice": 512.85, "priceChange": 1.45,
            "priceChangePercent": 0.28, "averageVolume": 85000000, "relativeVolume": 1.0, "RSI": 50.5,
            "MACD": 0.8, "fiftyMA": 510.20, "twoHundredMA": 495.60, "score": 3, "rank": 10,
            "passes": {"trend": True, "momentum": False, "volume": True, "priceAction": False}
        },
        {
            "ticker": "QQQ", "companyName": "Invesco QQQ Trust", "currentPrice": 425.60, "priceChange": 2.80,
            "priceChangePercent": 0.66, "averageVolume": 45000000, "relativeVolume": 1.1, "RSI": 48.8,
            "MACD": 1.2, "fiftyMA": 420.50, "twoHundredMA": 405.80, "score": 2, "rank": 11,
            "passes": {"trend": True, "momentum": False, "volume": False, "priceAction": True}
        },
        {
            "ticker": "IWM", "companyName": "iShares Russell 2000 ETF", "currentPrice": 198.45, "priceChange": 0.85,
            "priceChangePercent": 0.43, "averageVolume": 28000000, "relativeVolume": 0.9, "RSI": 52.2,
            "MACD": 0.5, "fiftyMA": 196.80, "twoHundredMA": 190.20, "score": 2, "rank": 12,
            "passes": {"trend": False, "momentum": True, "volume": False, "priceAction": False}
        }
    ]

    return {
        "stocks": instant_stocks,
        "metadata": {
            "scan_time": 0.001,  # Instant
            "scan_type": "instant",
            "scanned": len(instant_stocks),
            "results": len(instant_stocks),
            "is_static_data": True,
            "last_updated": "2024-01-15T10:00:00Z",
            "note": "Static data for instant loading. Real-time data loads in background."
        }
    }

@app.get("/api/stocks/scan/fast")
async def scan_stocks_fast():
    """Ultra-fast scanning endpoint for initial page load - uses only curated stocks"""
    start_time = datetime.now()

    try:
        # Use only curated stocks with minimal analysis
        candidate_tickers = get_curated_scannable_stocks()[:100]  # Top 100 only
        print(f"⚡ FAST SCAN: Analyzing {len(candidate_tickers)} curated stocks...")

        # Lightweight scan only
        lightweight_results = await fetch_lightweight_stocks_concurrent(candidate_tickers, max_stocks=len(candidate_tickers))

        # Minimal filtering - only basic quality
        fast_results = []
        for stock in lightweight_results:
            if stock and stock.get('is_liquid') and stock.get('is_reasonable_price'):
                fast_results.append(stock)

        # Sort by quick score and limit to 15 results
        fast_results.sort(key=lambda x: -x['quick_score'])
        fast_results = fast_results[:15]

        # Convert to expected format with minimal data
        formatted_stocks = []
        for i, stock in enumerate(fast_results):
            formatted_stocks.append({
                'ticker': stock['ticker'],
                'companyName': stock['ticker'] + ' Corp',  # Simple fallback
                'currentPrice': stock['currentPrice'],
                'priceChange': stock['priceChange'],
                'priceChangePercent': stock['priceChangePercent'],
                'averageVolume': stock['averageVolume'],
                'relativeVolume': stock['relativeVolume'],
                'RSI': stock['RSI'],
                'score': min(stock['quick_score'], 4),  # Cap at 4
                'rank': i + 1,
                'passes': {
                    'trend': stock['priceChangePercent'] > 0,
                    'volume': stock['relativeVolume'] > 1.5,
                    'oversold': stock['RSI'] < 35,
                    'breakout': stock['priceChangePercent'] > 2
                }
            })

        total_time = (datetime.now() - start_time).total_seconds()

        print(f"⚡ FAST SCAN COMPLETE: {len(formatted_stocks)} results in {total_time:.1f}s")

        return {
            "stocks": formatted_stocks,
            "metadata": {
                "scan_time": total_time,
                "scan_type": "fast",
                "scanned": len(candidate_tickers),
                "results": len(formatted_stocks),
                "is_fast_scan": True
            }
        }

    except Exception as e:
        return {
            "stocks": [],
            "metadata": {
                "error": str(e),
                "scan_time": (datetime.now() - start_time).total_seconds(),
                "scan_type": "fast"
            }
        }

@app.get("/api/news/general/instant")
async def get_general_news_instant():
    """INSTANT news with static data for immediate loading"""
    instant_news = [
        {
            "title": "Stock Market Reaches New Highs as Tech Shares Rally",
            "description": "Major indices close higher as technology stocks lead gains amid positive earnings reports.",
            "url": "https://example.com/news1",
            "source": "Financial News",
            "published_at": "2024-01-15T14:30:00Z",
            "image_url": None,
            "category": "market"
        },
        {
            "title": "Federal Reserve Signals Continued Economic Support",
            "description": "Central bank maintains accommodative monetary policy stance in latest announcement.",
            "url": "https://example.com/news2",
            "source": "Economic Times",
            "published_at": "2024-01-15T13:15:00Z",
            "image_url": None,
            "category": "economy"
        },
        {
            "title": "Major Earnings Reports Drive Market Activity",
            "description": "Several S&P 500 companies report stronger than expected quarterly results.",
            "url": "https://example.com/news3",
            "source": "MarketWatch",
            "published_at": "2024-01-15T12:00:00Z",
            "image_url": None,
            "category": "earnings"
        },
        {
            "title": "Oil Prices Stabilize After Recent Volatility",
            "description": "Energy markets show signs of stability following recent geopolitical tensions.",
            "url": "https://example.com/news4",
            "source": "Energy Daily",
            "published_at": "2024-01-15T11:30:00Z",
            "image_url": None,
            "category": "commodities"
        },
        {
            "title": "Bitcoin and Cryptocurrency Markets Show Mixed Signals",
            "description": "Digital assets trade in tight ranges as investors await regulatory clarity.",
            "url": "https://example.com/news5",
            "source": "Crypto News",
            "published_at": "2024-01-15T10:45:00Z",
            "image_url": None,
            "category": "crypto"
        }
    ]

    return {
        "news": instant_news,
        "metadata": {
            "count": len(instant_news),
            "is_static": True,
            "last_updated": "2024-01-15T15:00:00Z"
        }
    }

def basic_quality_filter(tickers, max_stocks=100):
    """Basic filter to remove obvious junk but preserve high-scoring potential"""
    print(f"🔍 Basic quality filtering {len(tickers)} stocks...")

    filtered_stocks = []

    # Simple filtering - just remove obviously bad tickers and extreme penny stocks
    for ticker in tickers[:200]:  # Limit for performance but cast a wide net
        try:
            # Only exclude obvious junk - let scoring determine quality
            if (len(ticker) <= 5 and  # Reasonable ticker length
                ticker.isalpha() and  # Only letters
                '.' not in ticker and  # No preferred shares
                '-' not in ticker):   # No warrants/rights

                # Quick price check - only eliminate extreme penny stocks (under $1)
                info = get_cached_stock_info(ticker)
                if info and info['price'] >= 1.0:  # Very permissive - just avoid sub-$1 stocks
                    filtered_stocks.append(ticker)
        except Exception:
            continue

        if len(filtered_stocks) >= max_stocks:
            break

    print(f"✅ Basic filtering complete: {len(filtered_stocks)} stocks remain")
    return filtered_stocks

@app.get("/api/stocks/{ticker}")
async def get_stock_detail(ticker: str, ai_provider: str = "gemini"):
    """Get detailed information for a specific stock with AI analysis"""
    # Quick path: try cache first for snappy UX on header search
    cached = _adv_cache_get(ticker.upper())
    if cached:
        stock_data = cached
    else:
        stock_data = fetch_advanced_stock_data(ticker.upper())
    if not stock_data:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Get AI insights based on provider preference
    if ai_provider.lower() == "openai":
        ai_summary = await get_openai_insight(
            ticker.upper(),
            stock_data['currentPrice'],
            stock_data['passes'],
            stock_data['score']
        )
        stock_data['openaiSummary'] = ai_summary
    else:
        ai_summary = await get_gemini_insight(
            ticker.upper(),
            stock_data['currentPrice'],
            stock_data['passes'],
            stock_data['score']
        )
        stock_data['aiSummary'] = ai_summary

    return stock_data

def _fetch_stock_with_cache(symbol: str):
    """Internal helper to fetch stock using per-ticker cache."""
    symbol = symbol.upper()
    cached = _adv_cache_get(symbol)
    if cached:
        return cached
    data = fetch_advanced_stock_data(symbol)
    if data:
        _adv_cache_set(symbol, data)
    return data

@app.post("/api/stocks/batch")
async def get_stocks_batch(payload: BatchTickers):
    """Return advanced stock data for many tickers quickly (no AI)."""
    if not payload or not payload.tickers:
        return {"stocks": []}

    # Clean and dedupe tickers
    cleaned = []
    seen = set()
    for t in payload.tickers:
        if not isinstance(t, str):
            continue
        s = t.split(":")[-1].strip().upper()
        if not s:
            continue
        if s not in seen:
            seen.add(s)
            cleaned.append(s)

    # Use a small thread pool for I/O-bound yfinance calls
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_fetch_stock_with_cache, s) for s in cleaned[:200]]
        for fut in concurrent.futures.as_completed(futures):
            try:
                data = fut.result()
                if data:
                    results.append(data)
            except Exception:
                continue

    # Sort by score and assign ranks
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    for i, stock in enumerate(results):
        stock['rank'] = i + 1
    return {"stocks": results}

@app.get("/api/stocks/{ticker}/finviz")
async def get_finviz_urls(ticker: str):
    """Get Finviz chart and page URLs for a stock"""
    ticker = ticker.upper()
    return {
        "finviz_chart": f"https://finviz.com/chart.ashx?t={ticker}",
        "finviz_page": f"https://finviz.com/quote.ashx?t={ticker}"
    }

# =============================================================================
# SERVER STARTUP: INITIALIZE CACHE WARMING
# =============================================================================

# Initialize and start the cache warmer for background data updates
cache_warmer = CacheWarmer()
cache_warmer.start()

print("🚀 ShadowBeta Financial Dashboard API started successfully!")
print("📊 Cache warming system initialized for optimal performance")

# Watchlist Management
@app.get("/api/watchlists")
async def get_watchlists(authorization: Optional[str] = None):
    """Get all user watchlists for current user (JWT)"""
    if watchlists_collection is None:
        return {"watchlists": [], "message": "MongoDB not available - watchlists disabled"}

    user_id = None
    if authorization and authorization.lower().startswith('bearer '):
        token = authorization.split(' ',1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('sub')
        except JWTError:
            pass

    query = {"user_id": user_id} if user_id else {}

    watchlists = []
    for doc in watchlists_collection.find(query):
        doc['_id'] = str(doc['_id'])
        watchlists.append(doc)
    return {"watchlists": watchlists}

@app.post("/api/watchlists")
async def create_watchlist(watchlist: CreateWatchlist, authorization: Optional[str] = None):
    """Create a new watchlist"""
    if watchlists_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not available - watchlists disabled")

    user_id = None
    if authorization and authorization.lower().startswith('bearer '):
        try:
            payload = jwt.decode(authorization.split(' ',1)[1], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('sub')
        except JWTError:
            pass

    watchlist_doc = {
        "id": str(uuid.uuid4()),
        "name": watchlist.name,
        "tickers": watchlist.tickers,
        "user_id": user_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = watchlists_collection.insert_one(watchlist_doc)
    watchlist_doc['_id'] = str(result.inserted_id)
    return watchlist_doc

@app.put("/api/watchlists/{watchlist_id}")
async def update_watchlist(watchlist_id: str, watchlist: CreateWatchlist, authorization: Optional[str] = None):
    """Update an existing watchlist"""
    update_doc = {
        "name": watchlist.name,
        "tickers": watchlist.tickers,
        "updated_at": datetime.now()
    }

    query = {"id": watchlist_id}
    if authorization and authorization.lower().startswith('bearer '):
        try:
            payload = jwt.decode(authorization.split(' ',1)[1], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            query["user_id"] = payload.get('sub')
        except JWTError:
            pass

    result = watchlists_collection.update_one(
        query,
        {"$set": update_doc}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {"message": "Watchlist updated successfully"}

@app.delete("/api/watchlists/{watchlist_id}")
async def delete_watchlist(watchlist_id: str, authorization: Optional[str] = None):
    """Delete a watchlist"""
    query = {"id": watchlist_id}
    if authorization and authorization.lower().startswith('bearer '):
        try:
            payload = jwt.decode(authorization.split(' ',1)[1], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            query["user_id"] = payload.get('sub')
        except JWTError:
            pass
    result = watchlists_collection.delete_one(query)

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {"message": "Watchlist deleted successfully"}

@app.post("/api/watchlists/{watchlist_id}/scan")
async def scan_watchlist(watchlist_id: str, authorization: Optional[str] = None):
    """Scan stocks in a specific watchlist (fast, cached)."""
    query = {"id": watchlist_id}
    if authorization and authorization.lower().startswith('bearer '):
        try:
            payload = jwt.decode(authorization.split(' ',1)[1], JWT_SECRET, algorithms=[JWT_ALGORITHM])
            query["user_id"] = payload.get('sub')
        except JWTError:
            pass
    watchlist = watchlists_collection.find_one(query)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    batch = await get_stocks_batch(BatchTickers(tickers=watchlist.get('tickers', [])))
    return {"stocks": batch["stocks"], "watchlist_name": watchlist.get('name', '')}

# User Preferences
@app.get("/api/preferences")
async def get_user_preferences():
    """Get user preferences"""
    if user_preferences_collection is None:
        # Return default preferences when MongoDB is not available
        return {
            "user_id": "default",
            "dark_mode": False,
            "auto_refresh": True,
            "refresh_interval": 300,
            "ai_provider": "gemini",
            "notifications_enabled": True,
            "message": "Using default preferences (MongoDB not available)"
        }

    prefs = user_preferences_collection.find_one({"user_id": "default"})
    if not prefs:
        # Create default preferences
        default_prefs = {
            "user_id": "default",
            "dark_mode": False,
            "auto_refresh": True,
            "refresh_interval": 300,
            "ai_provider": "gemini",
            "notifications_enabled": True
        }
        user_preferences_collection.insert_one(default_prefs)
        return default_prefs

    prefs['_id'] = str(prefs['_id'])
    return prefs

@app.put("/api/preferences")
async def update_user_preferences(preferences: UserPreferences):
    """Update user preferences"""
    prefs_dict = preferences.dict()

    result = user_preferences_collection.update_one(
        {"user_id": "default"},
        {"$set": prefs_dict},
        upsert=True
    )

    return {"message": "Preferences updated successfully"}

# Export functionality
@app.get("/api/export/stocks")
async def export_stocks(format: str = "json"):
    """Export current stock analysis"""
    # Get current stock scan
    scan_result = await scan_stocks()
    stocks = scan_result["stocks"]

    if format.lower() == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Ticker', 'Company', 'Price', 'Change%', 'Score', 'Rank',
            'RSI', 'MACD', '50MA', '200MA', 'Volume', 'Trend', 'Momentum', 'Volume_Pass', 'PriceAction'
        ])

        # Write data
        for stock in stocks:
            writer.writerow([
                stock['ticker'],
                stock['companyName'],
                stock['currentPrice'],
                stock['priceChangePercent'],
                stock['score'],
                stock['rank'],
                stock['RSI'],
                stock['MACD'],
                stock['fiftyMA'],
                stock['twoHundredMA'],
                stock['relativeVolume'],
                stock['passes']['trend'],
                stock['passes']['momentum'],
                stock['passes']['volume'],
                stock['passes']['priceAction']
            ])

        return {
            "format": "csv",
            "data": output.getvalue(),
            "filename": f"shadowbeta_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }

    # Default JSON format
    return {
        "format": "json",
        "data": stocks,
        "exported_at": datetime.now().isoformat(),
        "total_stocks": len(stocks)
    }

# ===== ALPACA TRADING ENDPOINTS (INITIAL STUBS) =====

@app.get("/api/alpaca/account")
async def alpaca_account():
    """Get Alpaca account information (paper or live depending on env)."""
    if not alpaca_client:
        raise HTTPException(status_code=503, detail="Alpaca not configured on server")
    try:
        account = alpaca_client.get_account()
        return {"status": account.status, "buying_power": str(account.buying_power), "equity": str(account.equity), "paper": ALPACA_PAPER}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alpaca account error: {e}")

class PlaceOrder(BaseModel):
    symbol: str
    qty: float
    side: str  # 'buy' or 'sell'
    tif: str = "day"  # time in force

@app.post("/api/alpaca/order")
async def alpaca_place_order(order: PlaceOrder):
    """Place a simple market order via Alpaca (paper by default)."""
    if not alpaca_client:
        raise HTTPException(status_code=503, detail="Alpaca not configured on server")
    try:
        req = MarketOrderRequest(
            symbol=order.symbol.upper(),
            qty=order.qty,
            side=OrderSide.BUY if order.side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.DAY if order.tif.lower() == 'day' else TimeInForce.GTC
        )
        result = alpaca_client.submit_order(req)
        # Broadcast minimal order event
        try:
            await broadcast_shadowbot({
                "type": "order_submitted",
                "order": {"id": getattr(result, 'id', None), "symbol": getattr(result, 'symbol', None), "qty": str(getattr(result,'qty','')), "side": getattr(result,'side',None).value if getattr(result,'side',None) else None, "status": getattr(result,'status',None)}
            })
        except Exception:
            pass
        return {"id": result.id, "symbol": result.symbol, "qty": str(result.qty), "side": result.side.value, "status": result.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alpaca order error: {e}")

@app.get("/api/alpaca/orders")
async def alpaca_list_orders(limit: int = 20):
    """List recent Alpaca orders (best effort)."""
    if not alpaca_client:
        raise HTTPException(status_code=503, detail="Alpaca not configured on server")
    try:
        orders = alpaca_client.get_orders()  # default recent/open
        result = []
        for o in list(orders)[:limit]:
            try:
                side_val = o.side.value if hasattr(o.side, 'value') else str(o.side)
                status_val = o.status.value if hasattr(o.status, 'value') else getattr(o, 'status', 'unknown')
                qty_val = str(getattr(o, 'qty', getattr(o, 'quantity', '1')))
                result.append({
                    "id": getattr(o, 'id', None),
                    "symbol": getattr(o, 'symbol', None),
                    "qty": qty_val,
                    "side": side_val,
                    "status": status_val,
                    "submitted_at": str(getattr(o, 'submitted_at', ''))
                })
            except Exception:
                continue
        return {"orders": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alpaca orders error: {e}")

@app.websocket("/ws/shadowbot")
async def shadowbot_ws(ws: WebSocket):
    await ws.accept()
    shadowbot_clients.add(ws)
    try:
        await ws.send_json({"type": "hello", "message": "connected"})
        while True:
            # We don't expect incoming messages yet; keep connection open
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        try:
            shadowbot_clients.remove(ws)
        except KeyError:
            pass

# ===== SHADOWBOT STRATEGIES (CRUD) =====

class Strategy(BaseModel):
    id: Optional[str] = None
    name: str
    enabled: bool = False
    max_positions: int = 3
    max_notional_per_trade: float = 5000
    stop_loss_pct: float = 3.0
    take_profit_pct: float = 6.0
    entry_rules: Dict[str, bool] = {}
    symbols: List[str] = []

@app.get("/api/shadowbot/strategies")
async def list_strategies():
    if strategies_collection is None:
        return {"strategies": []}
    items = []
    for doc in strategies_collection.find():
        doc['_id'] = str(doc['_id'])
        items.append(doc)
    return {"strategies": items}

@app.post("/api/shadowbot/strategies")
async def upsert_strategy(strategy: Strategy):
    if strategies_collection is None:
        raise HTTPException(status_code=503, detail="DB not available for strategies")
    data = strategy.dict()
    _id = data.pop('id', None)
    if _id:
        strategies_collection.update_one({"id": _id}, {"$set": data}, upsert=True)
        data['id'] = _id
        return {"strategy": data}
    else:
        data['id'] = str(uuid.uuid4())
        strategies_collection.insert_one(data)
        return {"strategy": data}

@app.delete("/api/shadowbot/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    if strategies_collection is None:
        raise HTTPException(status_code=503, detail="DB not available for strategies")
    strategies_collection.delete_one({"id": strategy_id})
    return {"deleted": True}


# Alert system
@app.post("/api/alerts")
async def create_alert(ticker: str, condition: str, threshold: float):
    """Create a price/score alert"""
    alert_doc = {
        "id": str(uuid.uuid4()),
        "ticker": ticker.upper(),
        "condition": condition,  # "price_above", "price_below", "score_above"
        "threshold": threshold,
        "created_at": datetime.now(),
        "triggered": False
    }

    result = alerts_collection.insert_one(alert_doc)
    alert_doc['_id'] = str(result.inserted_id)
    return alert_doc

@app.get("/api/alerts")
async def get_alerts():
    """Get all active alerts"""
    alerts = []
    for doc in alerts_collection.find({"triggered": False}):
        doc['_id'] = str(doc['_id'])
        alerts.append(doc)
    return {"alerts": alerts}

# Background task for checking alerts
async def check_alerts():
    """Background task to check for triggered alerts"""
    alerts = list(alerts_collection.find({"triggered": False}))

    for alert in alerts:
        try:
            stock_data = fetch_advanced_stock_data(alert['ticker'])
            if stock_data:
                triggered = False
                message = ""

                if alert['condition'] == 'price_above' and stock_data['currentPrice'] > alert['threshold']:
                    triggered = True
                    message = f"🚀 {alert['ticker']} hit price target! Current: ${stock_data['currentPrice']:.2f} (Target: ${alert['threshold']:.2f})"
                elif alert['condition'] == 'price_below' and stock_data['currentPrice'] < alert['threshold']:
                    triggered = True
                    message = f"📉 {alert['ticker']} dropped below threshold! Current: ${stock_data['currentPrice']:.2f} (Threshold: ${alert['threshold']:.2f})"
                elif alert['condition'] == 'score_above' and stock_data['score'] >= alert['threshold']:
                    triggered = True
                    message = f"⭐ {alert['ticker']} reached score target! Current: {stock_data['score']}/4 (Target: {alert['threshold']})"

                if triggered:
                    # Send Discord notification
                    send_discord_alert(message)

                    # Mark alert as triggered
                    alerts_collection.update_one(
                        {"id": alert['id']},
                        {"$set": {"triggered": True, "triggered_at": datetime.now()}}
                    )
        except Exception as e:
            print(f"Error checking alert for {alert['ticker']}: {str(e)}")

# News API endpoints
@app.get("/api/news/general")
async def get_general_news(limit: int = 20):
    """Get general financial news"""
    try:
        news = fetch_general_financial_news(limit)
        return {"news": news, "total": len(news)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

@app.get("/api/news/stock/{ticker}")
async def get_stock_news(ticker: str, limit: int = 8):
    """Get news for a specific stock"""
    try:
        news = fetch_stock_news(ticker.upper(), limit)
        return {"ticker": ticker.upper(), "news": news, "total": len(news)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock news: {str(e)}")

@app.get("/api/news/search")
async def search_news_endpoint(q: str = Query(..., description="Search query"), limit: int = 30):
    """Search news with a query"""
    try:
        news = search_news(q, limit)
        return {"query": q, "news": news, "total": len(news)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")

# ===== NEW HOME SCREEN MARKET DATA ENDPOINTS =====

@app.get("/api/screener/snapshot")
async def get_screener_snapshot():
    """Return a cached lightweight snapshot for client-side screening to avoid extra API calls.
    Fields: ticker, companyName, currentPrice, averageVolume, sector, RSI, fiftyMA, twoHundredMA
    """
    try:
        cache_key = "screener_snapshot_v1"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Build from a curated list to keep it fast and within limits
        tickers = get_nyse_stock_symbols_optimized()[:120]
        results = []

        for t in tickers:
            try:
                data = fetch_advanced_stock_data(t)
                if not data:
                    continue
                # sector may not be reliably available; set None
                results.append({
                    "ticker": data['ticker'],
                    "companyName": data['companyName'],
                    "currentPrice": data['currentPrice'],
                    "averageVolume": data['averageVolume'],
                    "RSI": data['RSI'],
                    "MACD": data['MACD'],
                    "stochastic": data.get('stochastic'),
                    "relativeVolume": data['relativeVolume'],
                    "priceChangePercent": data.get('priceChangePercent', 0.0),
                    "fiftyMA": data['fiftyMA'],
                    "twoHundredMA": data['twoHundredMA'],
                    "passes": data.get('passes', {}),
                    "score": data.get('score', 0),
                    "sector": None
                })
            except Exception:
                continue

        payload = {"snapshot": results, "count": len(results), "timestamp": datetime.now().isoformat()}
        _cache_set(cache_key, payload)
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building screener snapshot: {str(e)}")

@app.get("/api/market/indices")
async def get_market_indices():
    """Get major market indices data"""
    try:
        indices = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ",
            "^RUT": "Russell 2000",
            "^VIX": "VIX"
        }

        indices_data = []
        cache_key = "indices_v1"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")

                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    # Estimate previous close from history when possible to avoid slow info calls
                    prev_close = hist['Close'].iloc[-2] if len(hist['Close']) >= 2 else current_price
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close else 0

                    indices_data.append({
                        "symbol": symbol,
                        "name": name,
                        "price": round(current_price, 2),
                        "change": round(change, 2),
                        "changePercent": round(change_percent, 2),
                        "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                    })
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue

        result = {"indices": indices_data, "timestamp": datetime.now().isoformat()}
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market indices: {str(e)}")

@app.get("/api/market/movers")
async def get_market_movers():
    """Get top gainers and losers"""
    try:
        cache_key = "movers_v1"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Use a broader list of popular stocks for movers
        popular_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'NFLX', 'CRM',
            'UBER', 'LYFT', 'SNAP', 'TWTR', 'SHOP', 'SQ', 'PYPL', 'ZOOM', 'ROKU', 'PELOTON',
            'COIN', 'RBLX', 'HOOD', 'SOFI', 'PLTR', 'SNOW', 'DDOG', 'NET', 'CRWD', 'ZS'
        ]

        movers_data = []
        for ticker in popular_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="2d")
                info = stock.info

                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100 if prev_close else 0

                    movers_data.append({
                        "ticker": ticker,
                        "name": info.get('shortName', ticker),
                        "price": round(current_price, 2),
                        "change": round(change, 2),
                        "changePercent": round(change_percent, 2),
                        "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                    })
            except Exception as e:
                print(f"Error fetching mover {ticker}: {e}")
                continue

        # Sort by percentage change
        movers_data.sort(key=lambda x: x['changePercent'], reverse=True)

        gainers = movers_data[:10]  # Top 10 gainers
        losers = sorted(movers_data, key=lambda x: x['changePercent'])[:10]  # Top 10 losers

        result = {
            "gainers": gainers,
            "losers": losers,
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market movers: {str(e)}")

@app.get("/api/market/heatmap")
async def get_market_heatmap():
    """Get sector/market heatmap data"""
    try:
        # Major sector ETFs for heatmap visualization
        sector_etfs = {
            "XLK": "Technology",
            "XLF": "Financial Services",
            "XLV": "Healthcare",
            "XLE": "Energy",
            "XLI": "Industrials",
            "XLY": "Consumer Discretionary",
            "XLP": "Consumer Staples",
            "XLU": "Utilities",
            "XLB": "Materials",
            "XLRE": "Real Estate",
            "XLC": "Communication Services"
        }

        cache_key = "heatmap_v1"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        heatmap_data = []
        for symbol, sector in sector_etfs.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")

                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    change_percent = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0

                    # Fixed size metric to avoid slow info calls
                    market_cap = 1_000_000_000

                    heatmap_data.append({
                        "symbol": symbol,
                        "sector": sector,
                        "changePercent": round(change_percent, 2),
                        "size": market_cap,
                        "price": round(current_price, 2)
                    })
            except Exception as e:
                print(f"Error fetching heatmap data for {symbol}: {e}")
                continue

        result = {"heatmap": heatmap_data, "timestamp": datetime.now().isoformat()}
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching heatmap data: {str(e)}")

@app.get("/api/market/high-volume")
async def get_high_volume_stocks():
    """Get highest volume stocks with full analysis"""
    try:
        # List of popular high-volume stocks
        high_volume_tickers = [
            'SPY', 'QQQ', 'TSLA', 'AAPL', 'MSFT', 'NVDA', 'AMD', 'SOXL',
            'TQQQ', 'SQQQ', 'AMZN', 'META', 'GOOGL', 'NFLX', 'CRM',
        ]

        stocks_data = []
        for ticker in high_volume_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                info = stock.info

                if len(hist) < 2:
                    continue

                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                volume = hist['Volume'].iloc[-1]
                avg_volume = hist['Volume'].mean()

                # Calculate technical indicators (same as Shadow's Picks)
                close_prices = hist['Close'].values
                volumes = hist['Volume'].values

                # RSI calculation
                delta = np.diff(close_prices)
                gain = np.where(delta > 0, delta, 0)
                loss = np.where(delta < 0, -delta, 0)
                avg_gain = np.mean(gain[-14:]) if len(gain) >= 14 else np.mean(gain)
                avg_loss = np.mean(loss[-14:]) if len(loss) >= 14 else np.mean(loss)
                rs = avg_gain / avg_loss if avg_loss != 0 else 0
                rsi = 100 - (100 / (1 + rs))

                # MACD calculation (simplified)
                ema12 = pd.Series(close_prices).ewm(span=12).mean().iloc[-1]
                ema26 = pd.Series(close_prices).ewm(span=26).mean().iloc[-1]
                macd = ema12 - ema26

                # Moving averages
                ma50 = np.mean(close_prices[-min(50, len(close_prices)):])
                ma200 = np.mean(close_prices[-min(200, len(close_prices)):])

                # Price change
                price_change = current_price - prev_close
                price_change_percent = (price_change / prev_close) * 100 if prev_close != 0 else 0

                # Volume analysis
                relative_volume = volume / avg_volume if avg_volume > 0 else 1

                # Criteria evaluation (same logic as Shadow's Picks)
                passes = {
                    'trend': current_price > ma50 > ma200,
                    'momentum': rsi > 50,
                    'volume': relative_volume > 1.5,
                    'priceAction': price_change_percent > 0
                }

                score = sum(passes.values())

                stock_data = {
                    'ticker': ticker,
                    'companyName': info.get('shortName', f'{ticker} Corp'),
                    'currentPrice': round(current_price, 2),
                    'priceChange': round(price_change, 2),
                    'priceChangePercent': round(price_change_percent, 2),
                    'volume': int(volume),
                    'avgVolume': int(avg_volume),
                    'relativeVolume': round(relative_volume, 2),
                    'RSI': round(rsi, 2),
                    'MACD': round(macd, 4),
                    'fiftyMA': round(ma50, 2),
                    'twoHundredMA': round(ma200, 2),
                    'passes': passes,
                    'score': score,
                    'rank': 0  # Will be set after sorting
                }

                stocks_data.append(stock_data)

            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue

        # Sort by volume and assign ranks
        stocks_data.sort(key=lambda x: x['volume'], reverse=True)
        for i, stock in enumerate(stocks_data):
            stock['rank'] = i + 1

        return {
            'stocks': stocks_data[:10],  # Top 10 by volume
            'timestamp': datetime.now().isoformat(),
            'total': len(stocks_data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching high volume stocks: {str(e)}")

@app.get("/api/market/full-movers")
async def get_market_full_movers():
    """Get top gainers and losers with full technical analysis like Shadow's Picks"""
    try:
        # Get basic movers first
        movers_data = await get_market_movers()

        # Get full analysis for top gainers and losers
        full_gainers = []
        full_losers = []

        # Process top 3 gainers
        for gainer in movers_data["gainers"][:3]:
            try:
                full_stock = fetch_advanced_stock_data(gainer["ticker"])
                if full_stock:
                    full_gainers.append(full_stock)
                await asyncio.sleep(0.3)  # Rate limiting
            except Exception as e:
                print(f"Error analyzing gainer {gainer['ticker']}: {e}")
                continue

        # Process top 3 losers
        for loser in movers_data["losers"][:3]:
            try:
                full_stock = fetch_advanced_stock_data(loser["ticker"])
                if full_stock:
                    full_losers.append(full_stock)
                await asyncio.sleep(0.3)  # Rate limiting
            except Exception as e:
                print(f"Error analyzing loser {loser['ticker']}: {e}")
                continue

        return {
            "gainers": full_gainers,
            "losers": full_losers,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching full market movers: {str(e)}")

@app.get("/api/market/highest-volume")
async def get_highest_volume_stocks():
    """Get highest volume stocks with full technical analysis"""
    try:
        cache_key = "highvol_v1"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Popular high-volume stocks to check
        high_volume_tickers = [
            'AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META', 'GOOGL', 'AMD', 'NFLX', 'UBER',
            'COIN', 'ROKU', 'RBLX', 'SNOW', 'CRWD', 'PLTR', 'SOFI', 'HOOD', 'NET', 'DDOG'
        ]

        volume_data = []
        for ticker in high_volume_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")

                if not hist.empty and 'Volume' in hist.columns:
                    volume = int(hist['Volume'].iloc[-1])
                    if volume > 0:  # Only include stocks with volume data
                        volume_data.append({
                            "ticker": ticker,
                            "volume": volume
                        })
            except Exception as e:
                print(f"Error fetching volume for {ticker}: {e}")
                continue

        # Sort by volume and get top 3
        volume_data.sort(key=lambda x: x['volume'], reverse=True)
        top_volume_tickers = [item["ticker"] for item in volume_data[:3]]

        # Get full analysis for highest volume stocks
        highest_volume_stocks = []
        for ticker in top_volume_tickers:
            try:
                full_stock = fetch_advanced_stock_data(ticker)
                if full_stock:
                    highest_volume_stocks.append(full_stock)
                await asyncio.sleep(0.3)  # Rate limiting
            except Exception as e:
                print(f"Error analyzing high-volume stock {ticker}: {e}")
                continue

        result = {
            "stocks": highest_volume_stocks,
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching highest volume stocks: {str(e)}")

@app.get("/api/market/overview/instant")
async def get_market_overview_instant():
    """INSTANT market overview with static data for immediate loading"""
    return {
        "indices": [
            {"symbol": "^GSPC", "name": "S&P 500", "price": 4783.45, "change": 12.25, "changePercent": 0.26, "volume": 0},
            {"symbol": "^DJI", "name": "Dow Jones", "price": 37123.28, "change": 56.89, "changePercent": 0.15, "volume": 0},
            {"symbol": "^IXIC", "name": "NASDAQ", "price": 14867.69, "change": 45.12, "changePercent": 0.31, "volume": 0},
            {"symbol": "^RUT", "name": "Russell 2000", "price": 1987.45, "change": 8.23, "changePercent": 0.42, "volume": 0},
            {"symbol": "^VIX", "name": "VIX", "price": 18.45, "change": -0.85, "changePercent": -4.40, "volume": 0}
        ],
        "gainers": [
            {"ticker": "NVDA", "priceChangePercent": 3.82, "currentPrice": 875.25},
            {"ticker": "TSLA", "priceChangePercent": 3.54, "currentPrice": 245.60},
            {"ticker": "AMD", "priceChangePercent": 3.07, "currentPrice": 142.85},
            {"ticker": "NFLX", "priceChangePercent": 1.99, "currentPrice": 625.40},
            {"ticker": "META", "priceChangePercent": 1.42, "currentPrice": 485.20}
        ],
        "losers": [
            {"ticker": "VIX", "priceChangePercent": -4.40, "currentPrice": 18.45},
            {"ticker": "SQQQ", "priceChangePercent": -2.15, "currentPrice": 8.95},
            {"ticker": "UVXY", "priceChangePercent": -1.85, "currentPrice": 12.45},
            {"ticker": "SPXS", "priceChangePercent": -1.42, "currentPrice": 18.75},
            {"ticker": "TZA", "priceChangePercent": -1.25, "currentPrice": 15.60}
        ],
        "sectors": [
            {"sector": "Technology", "change": 1.2, "stocks": 45},
            {"sector": "Financial", "change": 0.8, "stocks": 38},
            {"sector": "Healthcare", "change": 0.3, "stocks": 29},
            {"sector": "Consumer", "change": 0.6, "stocks": 33},
            {"sector": "Energy", "change": -0.4, "stocks": 22}
        ],
        "stats": {
            "trading_session": "Market Open",
            "timestamp": "2024-01-15T15:30:00Z",
            "last_updated": "2024-01-15 15:30:00",
            "is_static": True
        }
    }

@app.get("/api/market/overview")
async def get_market_overview():
    """Get comprehensive market overview combining all data"""
    try:
        # Cache wrapper for overview
        cache_key = "overview_v1"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Get all market data (each call internally cached for 5 minutes)
        indices_data = await get_market_indices()
        movers_data = await get_market_movers()
        heatmap_data = await get_market_heatmap()

        # Add some market stats
        market_stats = {
            "trading_session": "Regular Hours" if 9 <= datetime.now().hour <= 16 else "After Hours",
            "timestamp": datetime.now().isoformat(),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        result = {
            "indices": indices_data["indices"],
            "gainers": movers_data["gainers"][:5],  # Top 5 gainers for overview
            "losers": movers_data["losers"][:5],    # Top 5 losers for overview
            "sectors": heatmap_data["heatmap"],
            "stats": market_stats
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market overview: {str(e)}")

@app.get("/api/stocks/{ticker}/gemini-insight")
async def get_stock_gemini_insight(ticker: str):
    """Get Gemini AI insight for a specific stock"""
    try:
        # Fetch comprehensive stock data using the advanced function
        stock_data = fetch_advanced_stock_data(ticker.upper())

        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

        # Get rich technical data
        current_price = stock_data['currentPrice']
        price_change = stock_data['priceChange']
        price_change_percent = stock_data['priceChangePercent']
        rsi = stock_data['RSI']
        macd = stock_data['MACD']
        ma50 = stock_data['fiftyMA']
        ma200 = stock_data['twoHundredMA']
        volume = stock_data['averageVolume']
        relative_volume = stock_data['relativeVolume']
        score = stock_data['score']
        passes = stock_data['passes']

        # Create comprehensive context for AI analysis
        technical_context = f"""
        Technical Analysis for {ticker.upper()}:
        - Current Price: ${current_price:.2f}
        - Price Change: ${price_change:.2f} ({price_change_percent:.2f}%)
        - RSI: {rsi:.1f} {'(Oversold)' if rsi < 30 else '(Overbought)' if rsi > 70 else '(Neutral)'}
        - MACD: {macd:.3f}
        - 50-day MA: ${ma50:.2f}
        - 200-day MA: ${ma200:.2f}
        - Volume: {volume:,} (Relative: {relative_volume:.1f}x)
        - Technical Score: {score}/4
        - Trend Analysis: {'BULLISH' if current_price > ma50 > ma200 else 'BEARISH' if current_price < ma50 < ma200 else 'MIXED'}
        """

        # Create detailed prompt for better analysis
        prompt = f"""As a professional stock analyst, provide a concise but insightful analysis of {ticker.upper()} stock.

{technical_context}

Based on this technical data, provide:
1. A brief technical analysis (2-3 sentences)
2. Current market sentiment (bullish/bearish/neutral)
3. Key support/resistance levels or patterns
4. One actionable insight for traders

Focus on specific technical indicators and actionable insights. Be concise but informative."""

        try:
            # Use the configured Gemini model
            response = gemini_model.generate_content(prompt)

            if response and response.text:
                insight = response.text.strip()
                return {"insight": insight, "ticker": ticker.upper()}
            else:
                raise Exception("Empty response from Gemini")

        except Exception as api_error:
            print(f"Gemini API error for {ticker}: {api_error}")
            # Provide a more detailed fallback analysis based on technical data
            fallback_analysis = generate_technical_fallback_analysis(ticker, stock_data)
            return {"insight": fallback_analysis, "ticker": ticker.upper()}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in Gemini insight for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting insight for {ticker}: {str(e)}")

def generate_technical_fallback_analysis(ticker: str, stock_data: dict) -> str:
    """Generate a meaningful fallback analysis when AI APIs fail"""
    current_price = stock_data['currentPrice']
    price_change_percent = stock_data['priceChangePercent']
    rsi = stock_data['RSI']
    ma50 = stock_data['fiftyMA']
    ma200 = stock_data['twoHundredMA']
    score = stock_data['score']

    # Determine trend
    if current_price > ma50 > ma200:
        trend = "bullish trend"
        sentiment = "positive"
    elif current_price < ma50 < ma200:
        trend = "bearish trend"
        sentiment = "negative"
    else:
        trend = "mixed signals"
        sentiment = "neutral"

    # RSI analysis
    if rsi < 30:
        rsi_analysis = "oversold conditions"
    elif rsi > 70:
        rsi_analysis = "overbought conditions"
    else:
        rsi_analysis = "neutral momentum"

    # Score interpretation
    if score >= 3:
        score_analysis = "strong technical setup"
    elif score >= 2:
        score_analysis = "moderate technical setup"
    else:
        score_analysis = "weak technical setup"

    return f"{ticker.upper()} is currently in a {trend} with {rsi_analysis} (RSI: {rsi:.1f}). The stock shows a {score_analysis} (score: {score}/4) and is trading at ${current_price:.2f} with a {price_change_percent:.2f}% change. Key levels to watch: 50-day MA at ${ma50:.2f} and 200-day MA at ${ma200:.2f}."

@app.get("/api/stocks/{ticker}/claude-insight")
async def get_stock_claude_insight(ticker: str):
    """Claude AI insight endpoint"""
    try:
        # Fetch comprehensive stock data using the advanced function
        stock_data = fetch_advanced_stock_data(ticker.upper())

        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

        # Get rich technical data
        current_price = stock_data['currentPrice']
        price_change = stock_data['priceChange']
        price_change_percent = stock_data['priceChangePercent']
        rsi = stock_data['RSI']
        macd = stock_data['MACD']
        ma50 = stock_data['fiftyMA']
        ma200 = stock_data['twoHundredMA']
        volume = stock_data['averageVolume']
        relative_volume = stock_data['relativeVolume']
        score = stock_data['score']
        passes = stock_data['passes']
        bollinger_upper = stock_data['bollinger_upper']
        bollinger_lower = stock_data['bollinger_lower']
        stochastic = stock_data['stochastic']
        williams_r = stock_data['williams_r']

        # Create comprehensive technical context
        technical_context = f"""
        Comprehensive Technical Analysis for {ticker.upper()}:

        Price Action:
        - Current Price: ${current_price:.2f}
        - Price Change: ${price_change:.2f} ({price_change_percent:.2f}%)

        Technical Indicators:
        - RSI: {rsi:.1f} {'(Oversold)' if rsi < 30 else '(Overbought)' if rsi > 70 else '(Neutral)'}
        - MACD: {macd:.3f}
        - Stochastic: {stochastic:.1f}
        - Williams %R: {williams_r:.1f}

        Moving Averages:
        - 50-day MA: ${ma50:.2f}
        - 200-day MA: ${ma200:.2f}
        - Trend: {'BULLISH' if current_price > ma50 > ma200 else 'BEARISH' if current_price < ma50 < ma200 else 'MIXED'}

        Volume & Support/Resistance:
        - Volume: {volume:,} (Relative: {relative_volume:.1f}x)
        - Bollinger Upper: ${bollinger_upper:.2f}
        - Bollinger Lower: ${bollinger_lower:.2f}

        Technical Score: {score}/4
        """

        # Create detailed Claude analysis prompt
        prompt = f"""As a professional financial analyst specializing in technical analysis, provide a comprehensive but concise analysis of {ticker.upper()} stock.

{technical_context}

Based on this technical data, provide:
1. Technical analysis summary (2-3 sentences)
2. Current market sentiment and trend direction
3. Key support/resistance levels and potential breakout points
4. Volume analysis and momentum assessment
5. One actionable trading insight or risk consideration

Focus on specific technical indicators, patterns, and actionable insights. Keep it informative but concise (under 150 words)."""

        try:
            # Call Claude API
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            if response and response.content:
                claude_insight = response.content[0].text.strip()
                return {
                    "insight": claude_insight,
                    "ticker": ticker.upper(),
                    "price": current_price,
                    "change_percent": price_change_percent,
                    "rsi": rsi
                }
            else:
                raise Exception("Empty response from Claude")

        except Exception as api_error:
            print(f"Claude API error for {ticker}: {api_error}")
            # Provide detailed fallback analysis
            fallback_analysis = generate_technical_fallback_analysis(ticker, stock_data)
            return {
                "insight": fallback_analysis,
                "ticker": ticker.upper(),
                "price": current_price,
                "change_percent": price_change_percent,
                "rsi": rsi
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting Claude insight for {ticker}: {e}")
        # Fallback response with basic info
        return {
            "insight": f"Claude analysis temporarily unavailable for {ticker.upper()}. Please try again later.",
            "ticker": ticker.upper(),
            "error": str(e)
        }

# ===== AI CHAT ENDPOINT =====

@app.post("/api/ai-chat")
async def ai_chat(request: dict):
    """AI Chat endpoint for user questions"""
    try:
        user_message = request.get('message', '')
        context = request.get('context', 'general')

        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Try to use Anthropic Claude for AI chat responses
        try:
            # Enhanced prompt for financial assistant
            financial_prompt = f"""You are a helpful AI financial assistant integrated into ShadowBeta, a professional trading platform.
            You help users with stock analysis, market insights, trading strategies, and portfolio management questions.

            User's question: {user_message}

            Please provide a helpful, informative response related to finance, trading, or investing.
            Keep responses concise but informative (2-3 sentences maximum).
            If the question is not finance-related, politely redirect to financial topics."""

            # Use Claude-3-haiku model for chat responses
            message = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[
                    {"role": "user", "content": financial_prompt}
                ]
            )

            if message and message.content:
                ai_response = message.content[0].text
                return {"response": ai_response, "provider": "claude"}
        except Exception as e:
            print(f"Claude API error: {e}")
            pass

        # Fallback to predefined responses for common questions
        fallback_responses = {
            "hello": "Hello! I'm here to help you with stock analysis, market insights, and trading strategies. What would you like to know?",
            "help": "I can assist you with stock analysis, market trends, portfolio management, and trading strategies. Try asking about specific stocks, market conditions, or investment concepts!",
            "market": "The market is dynamic and influenced by many factors including economic indicators, earnings reports, and global events. Check the Home screen for current market overview and indices performance.",
            "portfolio": "For portfolio management, visit the Portfolio tab where you can track your positions, add stocks manually, and analyze your performance. What specific portfolio question do you have?",
            "stocks": "I can help analyze stocks! Try asking about specific tickers, technical indicators, or market sectors. You can also check Shadow's Picks for AI-analyzed stock recommendations.",
            "trading": "Trading involves buying and selling securities. Key concepts include technical analysis, risk management, and market timing. What aspect of trading interests you most?"
        }

        # Simple keyword matching for fallback
        user_lower = user_message.lower()
        for keyword, response in fallback_responses.items():
            if keyword in user_lower:
                return {"response": response, "provider": "fallback"}

        # Generic financial assistant response
        return {
            "response": f"That's an interesting question about '{user_message}'. While I'm enhancing my capabilities, I recommend checking our market analysis tools: use Shadow's Picks for stock analysis, the Home screen for market overview, or the Portfolio section for position tracking. Is there a specific financial topic I can help you explore?",
            "provider": "fallback"
        }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "response": "I'm experiencing some technical difficulties right now. Please try asking your question again, or explore our analysis tools in the Shadow's Picks and Portfolio sections.",
            "provider": "error"
        }

# ===== END AI CHAT ENDPOINT =====

# ===== SIMPLE BACKTEST ENDPOINT =====

@app.post("/api/shadowbot/backtest")
async def backtest(strategy: dict):
    """Simple daily bar backtest for a strategy's symbol list using RSI/MA rules.
    Returns equity curve and summary metrics. This is a basic scaffold to iterate later."""
    try:
        symbols = strategy.get('symbols', [])[:10]
        rules = strategy.get('entry_rules', {})
        stop_pct = float(strategy.get('stop_loss_pct', 3.0)) / 100.0
        take_pct = float(strategy.get('take_profit_pct', 6.0)) / 100.0
        start_equity = 10000.0
        equity = start_equity
        trades = 0
        wins = 0
        equity_curve = []

        for sym in symbols:
            try:
                hist = yf.Ticker(sym).history(period="1y")
                if hist.empty:
                    continue
                close = hist['Close']
                ma50 = close.rolling(50).mean()
                ma200 = close.rolling(200).mean().fillna(ma50)
                rsi_series = close.rolling(14).apply(lambda _: _calc_rsi(close.loc[_].index and close.loc[_])) if False else close
                # Simple traversal
                position = 0
                entry = 0
                for i in range(len(close)):
                    price = float(close.iloc[i])
                    ma50v = float(ma50.iloc[i]) if not pd.isna(ma50.iloc[i]) else price
                    ma200v = float(ma200.iloc[i]) if not pd.isna(ma200.iloc[i]) else price
                    # Entry
                    passes = True
                    if rules.get('ma50_above_ma200'):
                        passes &= (ma50v >= ma200v)
                    if rules.get('price_above_ma50'):
                        passes &= (price >= ma50v)
                    # very rough RSI gate using last 14 price momentum
                    if rules.get('rsi_oversold') and i >= 14:
                        rsi = _calc_rsi(close.iloc[:i])
                        passes &= (rsi <= 35)
                    if position == 0 and passes:
                        position = 1
                        entry = price
                        trades += 1
                    # Exit via stops/takes
                    if position == 1:
                        if price <= entry * (1 - stop_pct):
                            equity *= (price / entry)
                            position = 0
                        elif price >= entry * (1 + take_pct):
                            equity *= (price / entry)
                            wins += 1
                            position = 0
                # Close open position at end
                if position == 1 and entry > 0:
                    equity *= (float(close.iloc[-1]) / entry)
            except Exception:
                continue
            equity_curve.append(equity)

        roi = (equity - start_equity) / start_equity * 100.0
        winrate = (wins / trades * 100.0) if trades > 0 else 0.0
        return {"start": start_equity, "end": equity, "roi": round(roi,2), "trades": trades, "wins": wins, "winrate": round(winrate,2), "equity_curve": equity_curve}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest error: {e}")

# ===== PORTFOLIO MANAGEMENT ENDPOINTS =====

@app.get("/api/portfolio/list")
async def get_portfolios():
    """Get list of all portfolios"""
    try:
        # For now, return mock data. This will be replaced with database integration
        portfolios = [
            {
                "id": "demo_portfolio",
                "name": "Demo Portfolio",
                "totalValue": 125000,
                "dayChange": 2500,
                "dayChangePercent": 2.04,
                "positions": []
            }
        ]
        return {"portfolios": portfolios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching portfolios: {str(e)}")

@app.post("/api/portfolio/manual-add")
async def add_manual_position(position_data: dict):
    """Add a manual stock position to portfolio"""
    try:
        # Validate required fields
        required_fields = ['symbol', 'quantity', 'avgCost', 'purchaseDate']
        for field in required_fields:
            if field not in position_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Fetch current stock price using existing logic
        symbol = position_data['symbol'].upper()
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"Stock symbol {symbol} not found")

        current_price = hist['Close'].iloc[-1]

        # Get basic company info (avoid slow calls)
        try:
            info = ticker.info
            company_name = info.get('shortName', f"{symbol} Company")
        except:
            company_name = f"{symbol} Company"

        # Calculate position metrics
        quantity = float(position_data['quantity'])
        avg_cost = float(position_data['avgCost'])
        # Avoid slow info calls; compute from inputs and history only
        market_value = quantity * current_price
        unrealized_pnl = (current_price - avg_cost) * quantity
        unrealized_pnl_percent = (unrealized_pnl / (avg_cost * quantity)) * 100 if avg_cost > 0 else 0

        position = {
            "symbol": symbol,
            "companyName": company_name,
            "quantity": quantity,
            "avgCost": avg_cost,
            "currentPrice": round(current_price, 2),
            "marketValue": round(market_value, 2),
            "unrealizedPnL": round(unrealized_pnl, 2),
            "unrealizedPnLPercent": round(unrealized_pnl_percent, 2),
            "purchaseDate": position_data['purchaseDate']
        }

        return {"position": position, "message": f"Successfully added {symbol} position"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding manual position: {str(e)}")

@app.post("/api/portfolio/webull-import")
async def import_webull_portfolio(credentials: dict):
    """Import portfolio from Webull (requires API credentials)"""
    try:
        # Check if Webull API credentials are configured
        webull_app_key = os.environ.get('WEBULL_APP_KEY')
        webull_app_secret = os.environ.get('WEBULL_APP_SECRET')

        if not webull_app_key or not webull_app_secret:
            raise HTTPException(
                status_code=503,
                detail="Webull API credentials not configured on server. Please contact administrator to set up WEBULL_APP_KEY and WEBULL_APP_SECRET environment variables."
            )

        # For now, return a mock response until actual API credentials are provided
        # This framework is ready for when you provide the actual Webull API keys

        account_id = credentials.get('accountId')
        if not account_id:
            raise HTTPException(status_code=400, detail="Account ID is required")

        # Mock portfolio data for demonstration
        mock_portfolio = {
            "id": f"webull_{account_id}",
            "name": f"Webull Portfolio ({account_id})",
            "totalValue": 250000,
            "dayChange": 5000,
            "dayChangePercent": 2.04,
            "positions": [
                {
                    "symbol": "TSLA",
                    "companyName": "Tesla, Inc.",
                    "quantity": 200,
                    "avgCost": 180.00,
                    "currentPrice": 195.50,
                    "marketValue": 39100.00,
                    "unrealizedPnL": 3100.00,
                    "unrealizedPnLPercent": 8.61,
                    "purchaseDate": "2024-01-10"
                },
                {
                    "symbol": "NVDA",
                    "companyName": "NVIDIA Corporation",
                    "quantity": 100,
                    "avgCost": 400.00,
                    "currentPrice": 450.75,
                    "marketValue": 45075.00,
                    "unrealizedPnL": 5075.00,
                    "unrealizedPnLPercent": 12.69,
                    "purchaseDate": "2024-02-15"
                }
            ],
            "importedAt": datetime.now().isoformat(),
            "source": "webull"
        }

        return {
            "portfolio": mock_portfolio,
            "message": "Portfolio imported successfully (demo data - configure Webull API for live data)"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing Webull portfolio: {str(e)}")

# ===== END PORTFOLIO ENDPOINTS =====

@app.get("/api/market/volatile-stocks")
async def get_volatile_stocks(limit: int = Query(10, ge=1, le=50)):
    """Get the most volatile stocks based on price volatility and volume"""
    try:
        cache_key = f"volatile_v1_{limit}"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Get NYSE symbols for scanning
        symbols = get_nyse_stock_symbols_optimized()
        if not symbols:
            return {"volatile_stocks": [], "message": "No symbols available"}

        # Limit to a reasonable number for performance
        sample_symbols = symbols[:200]  # Sample first 200 symbols
        volatile_stocks = []

        # Process stocks in batches for better performance
        batch_size = 20
        for i in range(0, min(len(sample_symbols), 100), batch_size):  # Process max 100 stocks
            batch = sample_symbols[i:i + batch_size]

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_symbol = {executor.submit(fetch_volatile_stock_data, symbol): symbol for symbol in batch}

                for future in concurrent.futures.as_completed(future_to_symbol):
                    try:
                        stock_data = future.result(timeout=10)
                        if stock_data:
                            volatile_stocks.append(stock_data)
                    except Exception as e:
                        continue

        # Sort by volatility score (combination of price change % and volume)
        volatile_stocks.sort(key=lambda x: x['volatility_score'], reverse=True)

        # Return top volatile stocks
        top_volatile = volatile_stocks[:limit]

        result = {
            "volatile_stocks": top_volatile,
            "total_analyzed": len(volatile_stocks),
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching volatile stocks: {str(e)}")

def fetch_volatile_stock_data(symbol):
    """Fetch volatility data for a single stock with full technical analysis"""
    try:
        # Use the same advanced analysis as other stock endpoints
        full_stock_data = fetch_advanced_stock_data(symbol)
        if not full_stock_data:
            return None

        # Add volatility-specific metrics
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")

        if len(hist) < 2:
            return None

        # Calculate volatility metrics
        price_std = hist['Close'].pct_change().std() * 100  # Standard deviation of returns
        volume_avg = hist['Volume'].mean()
        current_volume = hist['Volume'].iloc[-1]
        relative_volume = current_volume / volume_avg if volume_avg > 0 else 1

        # Calculate volatility score (higher = more volatile)
        volatility_score = abs(full_stock_data['priceChangePercent']) * 0.6 + price_std * 0.3 + min(relative_volume, 5) * 0.1

        # Filter out low-volume or low-price stocks
        if current_volume < 100000 or full_stock_data['currentPrice'] < 1.0:
            return None

        # Enhance the full stock data with volatility metrics
        enhanced_data = {
            **full_stock_data,
            "volatility_score": round(volatility_score, 2),
            "price_std": round(price_std, 2),
            "relativeVolume": round(relative_volume, 2),  # Override with calculated value
        }

        return enhanced_data

    except Exception as e:
        return None

if __name__ == "__main__":
    import uvicorn
    import os

    # Start background cache warming system
    print("🚀 STARTING PERFORMANCE-OPTIMIZED SHADOWBETA SERVER...")
    cache_warmer.start()

    port = int(os.getenv("PORT", 8000))
    print(f"🌐 Server starting on port {port} with background cache warming")
    uvicorn.run(app, host="0.0.0.0", port=port)

import os
import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from typing import List, Dict, Optional
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
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="ShadowBeta Financial Dashboard API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MongoDB connection (optional)
MONGO_URL = os.environ.get('MONGO_URL')
MONGODB_DISABLED = os.environ.get('MONGODB_DISABLED', 'false').lower() == 'true'

print(f"🔍 Debug: MONGO_URL = {MONGO_URL}")
print(f"🔍 Debug: MONGODB_DISABLED = {MONGODB_DISABLED}")

if MONGODB_DISABLED or not MONGO_URL:
    print("⚠️  MongoDB disabled or URL not set - using in-memory storage")
    client = None
    db = None
    watchlists_collection = None
    alerts_collection = None
    user_preferences_collection = None
    strategies_collection = None
else:
    try:
        client = MongoClient(MONGO_URL)
        db = client[os.environ.get('DB_NAME', 'shadowbeta')]
        # Collections
        watchlists_collection = db.watchlists
        alerts_collection = db.alerts
        user_preferences_collection = db.user_preferences
        strategies_collection = db.shadowbot_strategies
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {e}")
        print("⚠️  Continuing without MongoDB - some features may be limited")
        client = None
        db = None
        watchlists_collection = None
        alerts_collection = None
        user_preferences_collection = None
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
if ALPACA_API_KEY and ALPACA_API_SECRET:
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

        # Market score (bearish > 50, bullish < 50)
        fut_avg = 0.0
        if futures:
            fut_avg = sum(f.get('changePercent', 0.0) for f in futures if isinstance(f.get('changePercent'), (int, float))) / max(len(futures), 1)
        # Movers polarity
        g = movers.get('gainers', []) if isinstance(movers, dict) else []
        l = movers.get('losers', []) if isinstance(movers, dict) else []
        total = max(len(g) + len(l), 1)
        losers_share = len(l) / total
        # Headline sentiment proxy via keyword hits
        neg_words = ['miss', 'cut', 'down', 'drop', 'loss', 'bear', 'layoff', 'warn']
        pos_words = ['beat', 'up', 'gain', 'growth', 'bull', 'record', 'raise']
        neg = sum(1 for n in news if any(w in (n.get('title','') + ' ' + (n.get('description','') or '')).lower() for w in neg_words))
        pos = sum(1 for n in news if any(w in (n.get('title','') + ' ' + (n.get('description','') or '')).lower() for w in pos_words))
        total_news = max(neg + pos, 1)
        neg_ratio = neg / total_news

        score = 50.0
        score += (-fut_avg) * 6.0  # red futures increase score (bearish)
        score += (losers_share - 0.5) * 50.0
        score += (neg_ratio - 0.5) * 30.0
        score = max(0, min(100, round(score, 1)))

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

        # Get basic stock info from yfinance
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")

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
    return {"message": "ShadowBeta Financial Dashboard API - Enhanced Version"}

# Performance optimization cache
stock_cache = {}
nyse_symbols_cache = {'data': None, 'timestamp': None}
CACHE_DURATION = 300  # 5 minutes
ADV_CACHE_DURATION = 300  # 5 minutes for per-ticker advanced data

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
    min_volume_multiplier: float = Query(1.0, description="Minimum relative volume multiplier (e.g., 2.0 for 2x+ volume)"),
    min_price: float = Query(1.0, description="Minimum stock price"),
    max_price: float = Query(1000.0, description="Maximum stock price"),
    min_score: int = Query(0, description="Minimum technical score (0-4)"),
    max_stocks: int = Query(100, description="Maximum number of stocks to analyze"),
    include_priority: bool = Query(True, description="Include priority stocks (AMD, NVDA, etc.)")
):
    """SCORE-PRIORITIZED: Scan NYSE stocks with customizable filters"""
    start_time = datetime.now()
    print(f"🚀 Starting SCORE-PRIORITIZED NYSE stock scan with filters:")
    print(f"   📊 Min Volume: {min_volume_multiplier}x")
    print(f"   💰 Price Range: ${min_price:.2f} - ${max_price:.2f}")
    print(f"   🎯 Min Score: {min_score}/4")
    print(f"   📈 Max Stocks: {max_stocks}")
    print(f"   ⭐ Priority Stocks: {'Yes' if include_priority else 'No'}")

    # Step 1: Get NYSE symbols (cached)
    nyse_tickers = get_nyse_stock_symbols_optimized()
    print(f"📋 Working with {len(nyse_tickers)} NYSE symbols")

    # Step 2: Define priority stocks that should always be checked first
    priority_stocks = [
        'AMD', 'NVDA', 'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX',
        'SPY', 'QQQ', 'IWM', 'VTI', 'BTCUSD', 'ETHUSD', 'PLTR', 'COIN', 'SQ',
        'SNOW', 'CRWD', 'ZM', 'DOCU', 'ROKU', 'SPOT', 'UBER', 'LYFT', 'DASH'
    ]

    # Ensure priority stocks are in the ticker list (only if include_priority is True)
    if include_priority:
        for ticker in priority_stocks:
            if ticker not in nyse_tickers:
                nyse_tickers.insert(0, ticker)

    # Step 3: Basic filtering to remove obvious junk (but keep scoring potential)
    basic_filtered = basic_quality_filter(nyse_tickers, max_stocks=200)  # Increased for better filtering
    print(f"🔍 Basic filtered to {len(basic_filtered)} stocks")

    # Step 4: Prioritize known high-scoring stocks at the beginning
    prioritized_tickers = []

    # Add priority stocks first (if enabled)
    if include_priority:
        for ticker in priority_stocks:
            if ticker in basic_filtered:
                prioritized_tickers.append(ticker)
                basic_filtered.remove(ticker)

    # Add remaining stocks
    prioritized_tickers.extend(basic_filtered)

    if include_priority:
        print(f"🎯 Priority stocks included: {len([t for t in priority_stocks if t in prioritized_tickers])}")

    # Step 5: Fetch detailed analysis concurrently - SCORE ALL STOCKS
    stocks_data = await fetch_stock_data_concurrent(prioritized_tickers, max_stocks=max_stocks)

    # Step 6: Apply filters to the results
    filtered_stocks = []
    for stock in stocks_data:
        # Volume filter
        if stock['relativeVolume'] < min_volume_multiplier:
            continue

        # Price filter
        if stock['currentPrice'] < min_price or stock['currentPrice'] > max_price:
            continue

        # Score filter
        if stock['score'] < min_score:
            continue

        filtered_stocks.append(stock)

    print(f"🔍 After filtering: {len(filtered_stocks)}/{len(stocks_data)} stocks meet criteria")

    # Step 7: CRITICAL - Sort by SCORE first (4/4 stocks have highest priority)
    filtered_stocks.sort(key=lambda x: (-x['score'], x['currentPrice']))  # Score descending, then price ascending

    # Step 8: Separate by score tiers for analysis
    score_4_stocks = [s for s in filtered_stocks if s['score'] == 4]
    score_3_stocks = [s for s in filtered_stocks if s['score'] == 3]
    score_2_stocks = [s for s in filtered_stocks if s['score'] == 2]
    score_1_stocks = [s for s in filtered_stocks if s['score'] == 1]
    score_0_stocks = [s for s in filtered_stocks if s['score'] == 0]

    print(f"📊 SCORE DISTRIBUTION (After Filtering):")
    print(f"   4/4 stocks: {len(score_4_stocks)}")
    print(f"   3/4 stocks: {len(score_3_stocks)}")
    print(f"   2/4 stocks: {len(score_2_stocks)}")
    print(f"   1/4 stocks: {len(score_1_stocks)}")
    print(f"   0/4 stocks: {len(score_0_stocks)}")

    # Step 9: Build final list prioritizing high scores
    final_stocks = []

    # Add 4/4 stocks first (up to 10)
    final_stocks.extend(score_4_stocks[:10])
    remaining_slots = 10 - len(final_stocks)

    # Add 3/4 stocks if we need more
    if remaining_slots > 0:
        final_stocks.extend(score_3_stocks[:remaining_slots])
        remaining_slots = 10 - len(final_stocks)

    # Add 2/4 stocks only if we still need more
    if remaining_slots > 0:
        # Within 2/4 stocks, prioritize those in $20-$100 range
        score_2_prioritized = sorted(score_2_stocks,
                                   key=lambda x: (0 if 20 <= x['currentPrice'] <= 100 else 1, x['currentPrice']))
        final_stocks.extend(score_2_prioritized[:remaining_slots])
        remaining_slots = 10 - len(final_stocks)

    # Add lower scores only if absolutely necessary
    if remaining_slots > 0:
        score_1_prioritized = sorted(score_1_stocks,
                                   key=lambda x: (0 if 20 <= x['currentPrice'] <= 100 else 1, x['currentPrice']))
        final_stocks.extend(score_1_prioritized[:remaining_slots])

    # Assign final ranks
    for i, stock in enumerate(final_stocks):
        stock['rank'] = i + 1

    # Performance metrics
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()

    # Enhanced reporting
    final_score_dist = {}
    for stock in final_stocks:
        score = stock['score']
        final_score_dist[score] = final_score_dist.get(score, 0) + 1

    price_range_count = sum(1 for s in final_stocks if 20 <= s['currentPrice'] <= 100)
    high_volume_count = sum(1 for s in final_stocks if s['relativeVolume'] >= 2.0)

    print(f"🎉 SCORE-PRIORITIZED SCAN COMPLETE!")
    print(f"⏱️  Total time: {total_time:.1f}s")
    print(f"📊 Final selection: {final_score_dist}")
    print(f"💰 Price range ($20-$100): {price_range_count}/{len(final_stocks)}")
    print(f"📈 High volume (2x+): {high_volume_count}/{len(final_stocks)}")

    if final_stocks:
        print(f"🏆 Top scorer: {final_stocks[0]['ticker']} (${final_stocks[0]['currentPrice']:.2f}, {final_stocks[0]['score']}/4)")

        # Check if AMD is in the results
        amd_in_results = any(stock['ticker'] == 'AMD' for stock in final_stocks)
        if amd_in_results:
            amd_stock = next(stock for stock in final_stocks if stock['ticker'] == 'AMD')
            print(f"✅ AMD found in results: Rank #{amd_stock['rank']}, Score: {amd_stock['score']}/4")
        else:
            print(f"⚠️  AMD not in final results (may be filtered out or not top 10)")

    return {
        "stocks": final_stocks,
        "scan_time": f"{total_time:.1f}s",
        "score_distribution": final_score_dist,
        "filters_applied": {
            "min_volume_multiplier": min_volume_multiplier,
            "min_price": min_price,
            "max_price": max_price,
            "min_score": min_score,
            "max_stocks_analyzed": max_stocks,
            "include_priority": include_priority
        },
        "filter_stats": {
            "total_analyzed": len(stocks_data),
            "passed_filters": len(filtered_stocks),
            "final_results": len(final_stocks)
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

@app.get("/api/stocks/{ticker}/finviz")
async def get_finviz_urls(ticker: str):
    """Get Finviz chart and page URLs for a stock"""
    ticker = ticker.upper()
    return {
        "chartUrl": f"https://finviz.com/chart.ashx?t={ticker}&ty=c&ta=1&p=d&s=l",
        "pageUrl": f"https://finviz.com/quote.ashx?t={ticker}"
    }

# Watchlist Management
@app.get("/api/watchlists")
async def get_watchlists():
    """Get all user watchlists"""
    if watchlists_collection is None:
        return {"watchlists": [], "message": "MongoDB not available - watchlists disabled"}

    watchlists = []
    for doc in watchlists_collection.find():
        doc['_id'] = str(doc['_id'])
        watchlists.append(doc)
    return {"watchlists": watchlists}

@app.post("/api/watchlists")
async def create_watchlist(watchlist: CreateWatchlist):
    """Create a new watchlist"""
    if watchlists_collection is None:
        raise HTTPException(status_code=503, detail="MongoDB not available - watchlists disabled")

    watchlist_doc = {
        "id": str(uuid.uuid4()),
        "name": watchlist.name,
        "tickers": watchlist.tickers,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    result = watchlists_collection.insert_one(watchlist_doc)
    watchlist_doc['_id'] = str(result.inserted_id)
    return watchlist_doc

@app.put("/api/watchlists/{watchlist_id}")
async def update_watchlist(watchlist_id: str, watchlist: CreateWatchlist):
    """Update an existing watchlist"""
    update_doc = {
        "name": watchlist.name,
        "tickers": watchlist.tickers,
        "updated_at": datetime.now()
    }

    result = watchlists_collection.update_one(
        {"id": watchlist_id},
        {"$set": update_doc}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {"message": "Watchlist updated successfully"}

@app.delete("/api/watchlists/{watchlist_id}")
async def delete_watchlist(watchlist_id: str):
    """Delete a watchlist"""
    result = watchlists_collection.delete_one({"id": watchlist_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return {"message": "Watchlist deleted successfully"}

@app.post("/api/watchlists/{watchlist_id}/scan")
async def scan_watchlist(watchlist_id: str):
    """Scan stocks in a specific watchlist"""
    watchlist = watchlists_collection.find_one({"id": watchlist_id})
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    stocks_data = []

    for ticker in watchlist['tickers']:
        try:
            # Parse ticker to handle exchange prefixes like "NASDAQ:XCUR" -> "XCUR"
            clean_ticker = ticker.split(':')[-1].upper() if ':' in ticker else ticker.upper()
            print(f"Processing ticker: {ticker} -> {clean_ticker}")

            stock_data = fetch_advanced_stock_data(clean_ticker)
            if stock_data:
                stocks_data.append(stock_data)
                await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Skipping {ticker}: {str(e)}")
            continue

    # Sort by score and assign ranks
    stocks_data.sort(key=lambda x: x['score'], reverse=True)
    for i, stock in enumerate(stocks_data):
        stock['rank'] = i + 1

    return {"stocks": stocks_data, "watchlist_name": watchlist['name']}

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

        # Calculate position metrics
        quantity = float(position_data['quantity'])
        avg_cost = float(position_data['avgCost'])
        # Avoid slow info calls; compute from inputs and history only
        market_value = quantity * current_price
        unrealized_pnl = (current_price - avg_cost) * quantity
        unrealized_pnl_percent = (unrealized_pnl / (avg_cost * quantity)) * 100 if avg_cost > 0 else 0

        position = {
            "symbol": symbol,
            "companyName": info.get('shortName', f"{symbol} Company"),
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
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

import os
import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Simple cache for basic functionality
stock_cache = {}
nyse_symbols_cache = {'data': None, 'timestamp': None}
CACHE_DURATION = 300  # 5 minutes

def _cache_get(key: str):
    if key in stock_cache:
        data, timestamp = stock_cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_DURATION):
            return data
        else:
            del stock_cache[key]
    return None

def _cache_set(key: str, data):
    stock_cache[key] = (data, datetime.now())

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'pipengine')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')
ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.environ.get('ALPACA_SECRET_KEY')
FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

# Initialize FastAPI app
app = FastAPI(title="ShadowBeta Financial Dashboard API", version="2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# MongoDB connection
try:
    client = MongoClient(MONGO_URL, maxPoolSize=10, minPoolSize=1)
    db = client[DB_NAME]
    print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    db = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "ShadowBeta Financial Dashboard API - Simple Version"}

# Test endpoint
@app.get("/api/test")
async def test():
    return {"status": "working", "timestamp": str(datetime.now())}

# Featured stocks endpoint
@app.get("/api/featured-stocks")
async def get_featured_stocks():
    """Get featured stocks for the homepage"""
    try:
        cache_key = "featured_stocks"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Featured stocks - a curated list of interesting stocks
        featured_tickers = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'META', 'GOOGL', 'AMZN', 'NFLX', 'AMD', 'PLTR']

        featured_stocks = []

        for ticker in featured_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1mo")
                info = stock.info

                if hist.empty or len(hist) < 2:
                    continue

                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                price_change = current_price - prev_close
                price_change_percent = (price_change / prev_close) * 100 if prev_close else 0

                # Calculate basic indicators
                prices = hist['Close']
                volumes = hist['Volume']

                ma_20 = prices.rolling(window=20).mean().iloc[-1] if len(prices) >= 20 else current_price
                avg_volume = int(volumes.mean()) if not volumes.empty else 0
                recent_volume = int(volumes.iloc[-1]) if not volumes.empty else 0
                rel_volume = recent_volume / avg_volume if avg_volume > 0 else 1.0

                # Get company name
                company_name = info.get('longName', ticker.upper())

                featured_stocks.append({
                    'ticker': ticker,
                    'companyName': company_name,
                    'currentPrice': float(current_price),
                    'priceChange': float(price_change),
                    'priceChangePercent': float(price_change_percent),
                    'averageVolume': avg_volume,
                    'relativeVolume': float(rel_volume),
                    'twentyMA': float(ma_20) if not np.isnan(ma_20) else float(current_price),
                    'volume': recent_volume,
                    'spark': prices.tolist()[-40:] if len(prices) >= 40 else prices.tolist(),
                    'passes': [],
                    'score': 50
                })
            except Exception as e:
                print(f"Error fetching stock {ticker}: {e}")
                continue

        result = {
            "featured_stocks": featured_stocks,
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching featured stocks: {str(e)}")

# Market movers endpoint
@app.get("/api/market/movers")
async def get_market_movers():
    """Get top gainers and losers"""
    try:
        cache_key = "market_movers"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Get top gainers and losers
        gainers = []
        losers = []

        # Use a simple list of major stocks for movers
        major_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'PLTR',
                        'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'ARKK', 'TQQQ', 'SQQQ', 'UVXY']

        for ticker in major_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")

                if hist.empty or len(hist) < 2:
                    continue

                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Open'].iloc[0]
                price_change = current_price - prev_close
                price_change_percent = (price_change / prev_close) * 100 if prev_close else 0

                stock_data = {
                    'ticker': ticker,
                    'currentPrice': float(current_price),
                    'priceChange': float(price_change),
                    'priceChangePercent': float(price_change_percent),
                    'volume': int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0
                }

                if price_change_percent > 0:
                    gainers.append(stock_data)
                else:
                    losers.append(stock_data)

            except Exception as e:
                print(f"Error fetching mover {ticker}: {e}")
                continue

        # Sort and take top 10
        gainers = sorted(gainers, key=lambda x: x['priceChangePercent'], reverse=True)[:10]
        losers = sorted(losers, key=lambda x: x['priceChangePercent'])[:10]

        result = {
            "gainers": gainers,
            "losers": losers,
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market movers: {str(e)}")

# Highest volume stocks endpoint
@app.get("/api/market/highest-volume")
async def get_highest_volume_stocks():
    """Get stocks with highest volume"""
    try:
        cache_key = "highest_volume"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        # Use a simple list of major stocks
        volume_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'PLTR',
                         'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'ARKK', 'TQQQ', 'SQQQ', 'UVXY']

        volume_stocks = []

        for ticker in volume_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")

                if hist.empty:
                    continue

                current_price = hist['Close'].iloc[-1]
                volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0

                volume_stocks.append({
                    'ticker': ticker,
                    'currentPrice': float(current_price),
                    'volume': volume
                })

            except Exception as e:
                print(f"Error fetching volume stock {ticker}: {e}")
                continue

        # Sort by volume and take top 10
        volume_stocks = sorted(volume_stocks, key=lambda x: x['volume'], reverse=True)[:10]

        result = {
            "highest_volume_stocks": volume_stocks,
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching highest volume stocks: {str(e)}")

# Market indices endpoint
@app.get("/api/market/indices")
async def get_market_indices():
    """Get major market indices"""
    try:
        cache_key = "market_indices"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT', '^VIX']
        indices_data = []

        for index in indices:
            try:
                ticker = yf.Ticker(index)
                hist = ticker.history(period="1d")

                if hist.empty or len(hist) < 2:
                    continue

                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Open'].iloc[0]
                price_change = current_price - prev_close
                price_change_percent = (price_change / prev_close) * 100 if prev_close else 0

                index_name = {
                    '^GSPC': 'S&P 500',
                    '^DJI': 'Dow Jones',
                    '^IXIC': 'NASDAQ',
                    '^RUT': 'Russell 2000',
                    '^VIX': 'VIX'
                }.get(index, index)

                indices_data.append({
                    'symbol': index,
                    'name': index_name,
                    'price': float(current_price),
                    'change': float(price_change),
                    'changePercent': float(price_change_percent)
                })

            except Exception as e:
                print(f"Error fetching index {index}: {e}")
                continue

        result = {
            "indices": indices_data,
            "timestamp": datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market indices: {str(e)}")

# Stock detail endpoint
@app.get("/api/stocks/{ticker}")
async def get_stock_detail(ticker: str):
    """Get detailed stock information"""
    try:
        cache_key = f"stock_detail_{ticker.upper()}"
        cached = _cache_get(cache_key)
        if cached:
            return cached

        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period="1mo")
        info = stock.info

        if hist.empty:
            raise HTTPException(status_code=404, detail="Stock not found")

        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else hist['Open'].iloc[0]
        price_change = current_price - prev_close
        price_change_percent = (price_change / prev_close) * 100 if prev_close else 0

        # Basic indicators
        prices = hist['Close']
        volumes = hist['Volume']

        ma_20 = prices.rolling(window=20).mean().iloc[-1] if len(prices) >= 20 else current_price
        avg_volume = int(volumes.mean()) if not volumes.empty else 0
        recent_volume = int(volumes.iloc[-1]) if not volumes.empty else 0

        result = {
            'ticker': ticker.upper(),
            'companyName': info.get('longName', ticker.upper()),
            'currentPrice': float(current_price),
            'priceChange': float(price_change),
            'priceChangePercent': float(price_change_percent),
            'averageVolume': avg_volume,
            'volume': recent_volume,
            'twentyMA': float(ma_20) if not np.isnan(ma_20) else float(current_price),
            'spark': prices.tolist()[-40:] if len(prices) >= 40 else prices.tolist(),
            'timestamp': datetime.now().isoformat()
        }
        _cache_set(cache_key, result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

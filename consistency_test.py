#!/usr/bin/env python3
import requests
import time
import json

# Test the optimized endpoint multiple times to verify consistency
base_url = 'http://localhost:8000'

print('🔄 Running 3 consecutive scans to verify consistency...')
times = []
stock_counts = []

for i in range(3):
    print(f'📊 Scan {i+1}/3:')
    start = time.time()
    response = requests.get(f'{base_url}/api/stocks/scan')
    end = time.time()

    duration = end - start
    times.append(duration)

    if response.status_code == 200:
        data = response.json()
        stocks = data.get('stocks', [])
        stock_counts.append(len(stocks))

        # Show sample stock details
        if stocks:
            sample = stocks[0]
            print(f'   ⏱️  Time: {duration:.2f}s')
            print(f'   📈 Stocks: {len(stocks)}')
            print(f'   🎯 Sample: {sample["ticker"]} (${sample["currentPrice"]:.2f}, Score: {sample["score"]}/4)')
            print(f'   🔍 Price Range Check: {20 <= sample["currentPrice"] <= 100}')
    else:
        print(f'   ❌ HTTP {response.status_code}')

print(f'📊 CONSISTENCY ANALYSIS:')
print(f'   Average Time: {sum(times)/len(times):.2f}s')
print(f'   Time Range: {min(times):.2f}s - {max(times):.2f}s')
print(f'   Stock Counts: {stock_counts}')
print(f'   Consistency: {"✅ GOOD" if max(times) - min(times) < 5 else "⚠️  VARIABLE"}')

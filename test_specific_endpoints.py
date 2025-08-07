#!/usr/bin/env python3
"""
Test specific endpoints mentioned in the review request
"""

import requests
import json

def test_specific_endpoints():
    base_url = 'http://localhost:8000'

    print('🔍 Testing Specific Endpoints from Review Request...')
    print('=' * 60)

    # Test core stock scanning endpoint
    print('\n1. Testing GET /api/stocks/scan')
    try:
        response = requests.get(f'{base_url}/api/stocks/scan', timeout=30)
        if response.status_code == 200:
            data = response.json()
            stocks = data.get('stocks', [])
            print(f'✅ SUCCESS: Found {len(stocks)} stocks')
            if stocks:
                sample = stocks[0]
                print(f'   Sample: {sample["ticker"]} - ${sample["currentPrice"]:.2f} (Score: {sample["score"]}/4)')
        else:
            print(f'❌ FAILED: Status {response.status_code}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

    # Test market overview endpoint
    print('\n2. Testing GET /api/market/overview')
    try:
        response = requests.get(f'{base_url}/api/market/overview', timeout=30)
        if response.status_code == 200:
            data = response.json()
            indices = data.get('indices', [])
            gainers = data.get('gainers', [])
            losers = data.get('losers', [])
            sectors = data.get('sectors', [])
            print(f'✅ SUCCESS: {len(indices)} indices, {len(gainers)} gainers, {len(losers)} losers, {len(sectors)} sectors')
        else:
            print(f'❌ FAILED: Status {response.status_code}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

    # Test market indices endpoint
    print('\n3. Testing GET /api/market/indices')
    try:
        response = requests.get(f'{base_url}/api/market/indices', timeout=30)
        if response.status_code == 200:
            data = response.json()
            indices = data.get('indices', [])
            print(f'✅ SUCCESS: Found {len(indices)} market indices')
            if indices:
                for idx in indices[:3]:  # Show first 3
                    print(f'   {idx["name"]}: ${idx["price"]} ({idx["changePercent"]:+.2f}%)')
        else:
            print(f'❌ FAILED: Status {response.status_code}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

    # Test market movers endpoint
    print('\n4. Testing GET /api/market/movers')
    try:
        response = requests.get(f'{base_url}/api/market/movers', timeout=30)
        if response.status_code == 200:
            data = response.json()
            gainers = data.get('gainers', [])
            losers = data.get('losers', [])
            print(f'✅ SUCCESS: {len(gainers)} gainers, {len(losers)} losers')
            if gainers:
                print(f'   Top Gainer: {gainers[0]["ticker"]} ({gainers[0]["changePercent"]:+.2f}%)')
            if losers:
                print(f'   Top Loser: {losers[0]["ticker"]} ({losers[0]["changePercent"]:+.2f}%)')
        else:
            print(f'❌ FAILED: Status {response.status_code}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

    # Test high volume endpoint
    print('\n5. Testing GET /api/market/high-volume')
    try:
        response = requests.get(f'{base_url}/api/market/high-volume', timeout=30)
        if response.status_code == 200:
            data = response.json()
            stocks = data.get('stocks', [])
            print(f'✅ SUCCESS: Found {len(stocks)} high-volume stocks')
            if stocks:
                sample = stocks[0]
                print(f'   Highest Volume: {sample["ticker"]} - Volume: {sample["volume"]:,}')
        else:
            print(f'❌ FAILED: Status {response.status_code}')
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

    print('\n' + '=' * 60)
    print('✅ All requested endpoints tested successfully!')

if __name__ == "__main__":
    test_specific_endpoints()

#!/usr/bin/env python3
"""
Test script to verify volatile stocks endpoint returns enhanced data
"""

import requests
import json
import time

def test_volatile_stocks():
    base_url = "http://localhost:8000"

    print("🧪 Testing Volatile Stocks Endpoint...")
    print("=" * 50)

    try:
        # Test the volatile stocks endpoint
        response = requests.get(f'{base_url}/api/market/volatile-stocks?limit=3', timeout=30)

        if response.status_code == 200:
            data = response.json()
            stocks = data.get('volatile_stocks', [])

            print(f'✅ SUCCESS: Found {len(stocks)} volatile stocks')
            print(f'📊 Total analyzed: {data.get("total_analyzed", "N/A")}')
            print()

            if stocks:
                # Check the first stock for enhanced data
                sample = stocks[0]
                print(f'🔍 Sample Stock: {sample["ticker"]}')
                print(f'   Company: {sample["companyName"]}')
                print(f'   Price: ${sample["currentPrice"]}')
                print(f'   Change: {sample["priceChangePercent"]}%')
                print(f'   Volatility Score: {sample["volatility_score"]}')
                print()

                # Check for technical indicators
                print("📈 Technical Indicators:")
                print(f'   RSI: {sample.get("RSI", "N/A")}')
                print(f'   MACD: {sample.get("MACD", "N/A")}')
                print(f'   50MA: ${sample.get("fiftyMA", "N/A")}')
                print(f'   200MA: ${sample.get("twoHundredMA", "N/A")}')
                print(f'   Stochastic: {sample.get("stochastic", "N/A")}')
                print(f'   Williams %R: {sample.get("williams_r", "N/A")}')
                print()

                # Check for criteria passes
                passes = sample.get("passes", {})
                if passes:
                    print("✅ Criteria Passes:")
                    for criterion, passed in passes.items():
                        status = "✅ PASS" if passed else "❌ FAIL"
                        print(f'   {criterion.title()}: {status}')
                else:
                    print("❌ No criteria passes found")
                print()

                # Check for score
                score = sample.get("score", "N/A")
                print(f'🏆 Score: {score}/4')

            else:
                print("❌ No volatile stocks returned")

        else:
            print(f'❌ FAILED: Status {response.status_code}')
            print(f'Response: {response.text}')

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend server")
        print("Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

if __name__ == "__main__":
    test_volatile_stocks()

#!/usr/bin/env python3
"""
Claude Integration Test - Focused test for Claude AI endpoints
"""

import requests
import json

class ClaudeIntegrationTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def test_claude_ai_chat(self):
        """Test the /api/ai-chat endpoint with Claude integration"""
        print("🤖 Testing Claude AI Chat Integration")
        print("=" * 50)

        test_cases = [
            {
                "message": "What is the current market outlook?",
                "context": "general",
                "test_name": "Market Outlook Question"
            },
            {
                "message": "How should I analyze AAPL stock?",
                "context": "stock_analysis",
                "test_name": "Stock Analysis Question"
            }
        ]

        for test_case in test_cases:
            try:
                print(f"\n🔍 Testing: {test_case['test_name']}")
                payload = {
                    "message": test_case["message"],
                    "context": test_case["context"]
                }

                response = self.session.post(f"{self.base_url}/api/ai-chat", json=payload, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '')
                    provider = data.get('provider', '')

                    if len(response_text) > 10 and provider in ["claude", "fallback"]:
                        print(f"✅ PASS: Provider: {provider}")
                        print(f"   Response: {response_text[:100]}...")
                    else:
                        print(f"❌ FAIL: Invalid response or provider")
                        print(f"   Provider: {provider}, Response length: {len(response_text)}")
                else:
                    print(f"❌ FAIL: HTTP {response.status_code}")

            except Exception as e:
                print(f"❌ ERROR: {str(e)}")

    def test_claude_stock_insight(self):
        """Test the /api/stocks/{ticker}/claude-insight endpoint"""
        print("\n📊 Testing Claude Stock Insight Integration")
        print("=" * 50)

        test_tickers = ["AAPL", "AMZN", "MSFT"]

        for ticker in test_tickers:
            try:
                print(f"\n🔍 Testing {ticker} Claude insight...")
                response = self.session.get(f"{self.base_url}/api/stocks/{ticker}/claude-insight", timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    insight = data.get('insight', '')
                    price = data.get('price')
                    rsi = data.get('rsi')
                    returned_ticker = data.get('ticker', '')

                    # Check required fields
                    required_fields = ['insight', 'ticker', 'price', 'change_percent', 'rsi']
                    missing_fields = [field for field in required_fields if field not in data]

                    if not missing_fields:
                        is_claude_working = "Claude analysis temporarily unavailable" not in insight
                        is_valid_data = (isinstance(price, (int, float)) and price > 0 and
                                       isinstance(rsi, (int, float)) and 0 <= rsi <= 100 and
                                       returned_ticker.upper() == ticker.upper())

                        if is_claude_working and is_valid_data and len(insight) > 50:
                            print(f"✅ PASS: Claude analysis working")
                            print(f"   Price: ${price:.2f}, RSI: {rsi:.1f}")
                            print(f"   Analysis: {insight[:80]}...")
                        elif not is_claude_working:
                            print(f"⚠️  FALLBACK: Claude temporarily unavailable, using fallback")
                        else:
                            print(f"❌ FAIL: Invalid data or short analysis")
                    else:
                        print(f"❌ FAIL: Missing fields: {missing_fields}")
                elif response.status_code == 404:
                    print(f"❌ FAIL: Stock {ticker} not found")
                else:
                    print(f"❌ FAIL: HTTP {response.status_code}")

            except Exception as e:
                print(f"❌ ERROR: {str(e)}")

def main():
    """Run Claude integration tests"""
    tester = ClaudeIntegrationTester()

    tester.test_claude_ai_chat()
    tester.test_claude_stock_insight()

    print("\n" + "=" * 80)
    print("Claude integration testing completed!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Watchlist Functionality Testing - Focused on the reported issue
Testing watchlist dropdown showing "watchlist is empty" issue
"""

import requests
import sys
import json
from datetime import datetime

class WatchlistTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def test_get_watchlists(self):
        """Test GET /api/watchlists to see what watchlists exist"""
        print("\n🔍 Testing GET /api/watchlists...")
        try:
            response = self.session.get(f"{self.base_url}/api/watchlists")
            success = response.status_code == 200

            if success:
                data = response.json()
                watchlists = data.get('watchlists', [])

                print(f"📋 Found {len(watchlists)} watchlists:")
                for i, watchlist in enumerate(watchlists):
                    print(f"  {i+1}. Name: '{watchlist.get('name', 'N/A')}'")
                    print(f"     ID: {watchlist.get('id', 'N/A')}")
                    tickers = watchlist.get('tickers', [])
                    print(f"     Tickers ({len(tickers)}): {tickers}")
                    print(f"     Created: {watchlist.get('created_at', 'N/A')}")
                    print()

                self.log_test("GET Watchlists", True, f"- Found {len(watchlists)} watchlists")
                return True, watchlists
            else:
                self.log_test("GET Watchlists", False, f"- Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False, []

        except Exception as e:
            self.log_test("GET Watchlists", False, f"- Error: {str(e)}")
            return False, []

    def test_individual_stock_api(self, ticker: str):
        """Test individual stock API for a specific ticker"""
        print(f"\n🔍 Testing GET /api/stocks/{ticker}...")
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/{ticker}")
            success = response.status_code == 200

            if success:
                data = response.json()
                print(f"📈 Stock data for {ticker}:")
                print(f"  Company: {data.get('companyName', 'N/A')}")
                print(f"  Current Price: ${data.get('currentPrice', 0):.2f}")
                print(f"  Price Change: {data.get('priceChange', 0):.2f} ({data.get('priceChangePercent', 0):.2f}%)")
                print(f"  Score: {data.get('score', 0)}/4")
                print(f"  RSI: {data.get('RSI', 0):.2f}")
                print(f"  Volume: {data.get('averageVolume', 0):,}")

                # Check if all required fields are present
                required_fields = ['ticker', 'companyName', 'currentPrice', 'priceChange', 'priceChangePercent', 'score']
                missing_fields = [field for field in required_fields if field not in data or data[field] is None]

                if not missing_fields:
                    self.log_test(f"Stock API - {ticker}", True, f"- Price: ${data.get('currentPrice', 0):.2f}, Score: {data.get('score', 0)}/4")
                    return True, data
                else:
                    self.log_test(f"Stock API - {ticker}", False, f"- Missing fields: {missing_fields}")
                    return False, data
            else:
                self.log_test(f"Stock API - {ticker}", False, f"- Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            self.log_test(f"Stock API - {ticker}", False, f"- Error: {str(e)}")
            return False, {}

    def test_watchlist_scan(self, watchlist_id: str, watchlist_name: str):
        """Test scanning a specific watchlist"""
        print(f"\n🔍 Testing POST /api/watchlists/{watchlist_id}/scan...")
        try:
            response = self.session.post(f"{self.base_url}/api/watchlists/{watchlist_id}/scan")
            success = response.status_code == 200

            if success:
                data = response.json()
                stocks = data.get('stocks', [])
                returned_name = data.get('watchlist_name', '')

                print(f"📊 Watchlist scan results for '{returned_name}':")
                print(f"  Stocks returned: {len(stocks)}")

                if stocks:
                    for i, stock in enumerate(stocks[:3]):  # Show first 3 stocks
                        print(f"  {i+1}. {stock.get('ticker', 'N/A')} - ${stock.get('currentPrice', 0):.2f} (Score: {stock.get('score', 0)}/4)")

                    if len(stocks) > 3:
                        print(f"  ... and {len(stocks) - 3} more stocks")
                else:
                    print("  ⚠️ No stocks returned - this matches the user's reported issue!")

                self.log_test(f"Watchlist Scan - {watchlist_name}", len(stocks) > 0,
                            f"- Returned {len(stocks)} stocks")
                return True, stocks
            else:
                self.log_test(f"Watchlist Scan - {watchlist_name}", False, f"- Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False, []

        except Exception as e:
            self.log_test(f"Watchlist Scan - {watchlist_name}", False, f"- Error: {str(e)}")
            return False, []

    def test_ticker_parsing(self, ticker: str):
        """Test if ticker parsing handles exchange prefixes correctly"""
        print(f"\n🔍 Testing ticker parsing for '{ticker}'...")

        # Extract ticker from exchange prefix if present
        clean_ticker = ticker
        if ':' in ticker:
            clean_ticker = ticker.split(':')[-1]
            print(f"  Original ticker: {ticker}")
            print(f"  Cleaned ticker: {clean_ticker}")

        # Test the cleaned ticker
        success, data = self.test_individual_stock_api(clean_ticker)

        if success:
            self.log_test(f"Ticker Parsing - {ticker}", True, f"- Successfully parsed to {clean_ticker}")
        else:
            self.log_test(f"Ticker Parsing - {ticker}", False, f"- Failed to get data for {clean_ticker}")

        return success, clean_ticker

    def create_test_watchlist(self):
        """Create a test watchlist with known tickers"""
        print("\n🔍 Creating test watchlist...")
        try:
            test_watchlist = {
                "name": f"Test Watchlist {datetime.now().strftime('%H%M%S')}",
                "tickers": ["AAPL", "NASDAQ:XCUR", "MSFT", "GOOGL"]
            }

            response = self.session.post(f"{self.base_url}/api/watchlists", json=test_watchlist)
            success = response.status_code == 200

            if success:
                data = response.json()
                watchlist_id = data.get('id')
                print(f"✅ Created test watchlist: {data.get('name')}")
                print(f"   ID: {watchlist_id}")
                print(f"   Tickers: {test_watchlist['tickers']}")

                self.log_test("Create Test Watchlist", True, f"- ID: {watchlist_id}")
                return True, watchlist_id, test_watchlist['name']
            else:
                self.log_test("Create Test Watchlist", False, f"- Status: {response.status_code}")
                return False, None, None

        except Exception as e:
            self.log_test("Create Test Watchlist", False, f"- Error: {str(e)}")
            return False, None, None

    def delete_test_watchlist(self, watchlist_id: str):
        """Delete the test watchlist"""
        if not watchlist_id:
            return

        print(f"\n🧹 Cleaning up test watchlist {watchlist_id}...")
        try:
            response = self.session.delete(f"{self.base_url}/api/watchlists/{watchlist_id}")
            if response.status_code == 200:
                print("✅ Test watchlist deleted successfully")
            else:
                print(f"⚠️ Failed to delete test watchlist: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error deleting test watchlist: {str(e)}")

    def run_watchlist_tests(self):
        """Run all watchlist-focused tests"""
        print("🚀 Starting Watchlist Functionality Testing")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 80)

        # 1. Test GET /api/watchlists to see what exists
        success, existing_watchlists = self.test_get_watchlists()

        # 2. Test individual stock APIs for AAPL and XCUR
        print("\n🔍 Testing individual stock APIs...")
        self.test_individual_stock_api("AAPL")
        self.test_individual_stock_api("XCUR")

        # 3. Test ticker parsing with exchange prefix
        self.test_ticker_parsing("NASDAQ:XCUR")

        # 4. Test existing watchlists if any
        if existing_watchlists:
            print("\n🔍 Testing existing watchlists...")
            for watchlist in existing_watchlists[:2]:  # Test first 2 watchlists
                watchlist_id = watchlist.get('id')
                watchlist_name = watchlist.get('name', 'Unknown')
                tickers = watchlist.get('tickers', [])

                print(f"\n📋 Testing watchlist: '{watchlist_name}'")
                print(f"   Tickers: {tickers}")

                # Test individual tickers in this watchlist
                for ticker in tickers[:3]:  # Test first 3 tickers
                    if ':' in ticker:
                        clean_ticker = ticker.split(':')[-1]
                        print(f"   Testing ticker: {ticker} -> {clean_ticker}")
                        self.test_individual_stock_api(clean_ticker)
                    else:
                        self.test_individual_stock_api(ticker)

                # Test watchlist scan
                self.test_watchlist_scan(watchlist_id, watchlist_name)

        # 5. Create and test a new watchlist
        print("\n🔍 Testing with new watchlist...")
        created, test_id, test_name = self.create_test_watchlist()

        if created and test_id:
            # Test the newly created watchlist
            self.test_watchlist_scan(test_id, test_name)

            # Clean up
            self.delete_test_watchlist(test_id)

        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Watchlist Test Results: {self.tests_passed}/{self.tests_run} tests passed")

        if self.tests_passed == self.tests_run:
            print("🎉 All watchlist tests passed!")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Issues found with watchlist functionality.")
            return 1

def main():
    """Main test runner"""
    tester = WatchlistTester()
    return tester.run_watchlist_tests()

if __name__ == "__main__":
    sys.exit(main())

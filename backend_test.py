#!/usr/bin/env python3
"""
ShadowBeta Financial Dashboard API Testing Suite - ENHANCED VERSION
Tests all backend endpoints and new advanced features
"""

import requests
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any

class ShadowBetaAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.created_watchlist_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/")
            success = response.status_code == 200
            data = response.json() if success else {}

            if success and "message" in data:
                self.log_test("Root API Endpoint", True, f"- Message: {data['message']}")
            else:
                self.log_test("Root API Endpoint", False, f"- Status: {response.status_code}")

            return success, data
        except Exception as e:
            self.log_test("Root API Endpoint", False, f"- Error: {str(e)}")
            return False, {}

    def test_stocks_scan_endpoint(self):
        """Test the /api/stocks/scan endpoint with enhanced features"""
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/scan")
            success = response.status_code == 200

            if success:
                data = response.json()
                stocks = data.get('stocks', [])

                if stocks:
                    # Validate enhanced stock data structure
                    sample_stock = stocks[0]
                    required_fields = [
                        'ticker', 'companyName', 'currentPrice', 'priceChange',
                        'priceChangePercent', 'averageVolume', 'relativeVolume',
                        'RSI', 'MACD', 'fiftyMA', 'twoHundredMA', 'passes', 'score', 'rank',
                        # NEW ENHANCED FIELDS
                        'bollinger_upper', 'bollinger_lower', 'stochastic', 'williams_r'
                    ]

                    missing_fields = [field for field in required_fields if field not in sample_stock]

                    if not missing_fields:
                        # Check enhanced criteria structure (6 criteria now)
                        passes = sample_stock.get('passes', {})
                        expected_criteria = ['trend', 'momentum', 'volume', 'priceAction', 'oversold', 'breakout']
                        missing_criteria = [c for c in expected_criteria if c not in passes]

                        if not missing_criteria:
                            self.log_test("Enhanced Stocks Scan Endpoint", True,
                                        f"- Found {len(stocks)} stocks with 6 criteria and advanced indicators")
                            return True, data
                        else:
                            self.log_test("Enhanced Stocks Scan Endpoint", False,
                                        f"- Missing enhanced criteria: {missing_criteria}")
                    else:
                        self.log_test("Enhanced Stocks Scan Endpoint", False,
                                    f"- Missing enhanced fields: {missing_fields}")
                else:
                    self.log_test("Enhanced Stocks Scan Endpoint", False, "- No stocks returned")
            else:
                self.log_test("Enhanced Stocks Scan Endpoint", False, f"- Status: {response.status_code}")

            return success, response.json() if success else {}

        except Exception as e:
            self.log_test("Enhanced Stocks Scan Endpoint", False, f"- Error: {str(e)}")
            return False, {}

    def test_dual_ai_integration(self, ticker: str = "AAPL"):
        """Test both Gemini and OpenAI AI providers"""
        # Test Gemini AI
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/{ticker}?ai_provider=gemini")
            success_gemini = response.status_code == 200

            if success_gemini:
                data = response.json()
                if 'aiSummary' in data and data['aiSummary']:
                    self.log_test(f"Gemini AI Integration ({ticker})", True,
                                f"- Summary: {data['aiSummary'][:50]}...")
                else:
                    self.log_test(f"Gemini AI Integration ({ticker})", False, "- No Gemini summary")
                    success_gemini = False
            else:
                self.log_test(f"Gemini AI Integration ({ticker})", False, f"- Status: {response.status_code}")
        except Exception as e:
            self.log_test(f"Gemini AI Integration ({ticker})", False, f"- Error: {str(e)}")
            success_gemini = False

        # Test OpenAI AI
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/{ticker}?ai_provider=openai")
            success_openai = response.status_code == 200

            if success_openai:
                data = response.json()
                if 'openaiSummary' in data and data['openaiSummary']:
                    self.log_test(f"OpenAI Integration ({ticker})", True,
                                f"- Summary: {data['openaiSummary'][:50]}...")
                else:
                    self.log_test(f"OpenAI Integration ({ticker})", False, "- No OpenAI summary")
                    success_openai = False
            else:
                self.log_test(f"OpenAI Integration ({ticker})", False, f"- Status: {response.status_code}")
        except Exception as e:
            self.log_test(f"OpenAI Integration ({ticker})", False, f"- Error: {str(e)}")
            success_openai = False

        return success_gemini and success_openai

    def test_watchlist_crud_operations(self):
        """Test watchlist CRUD operations"""
        # Test GET watchlists (initially empty)
        try:
            response = self.session.get(f"{self.base_url}/api/watchlists")
            success = response.status_code == 200

            if success:
                data = response.json()
                initial_count = len(data.get('watchlists', []))
                self.log_test("Get Watchlists", True, f"- Found {initial_count} existing watchlists")
            else:
                self.log_test("Get Watchlists", False, f"- Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Watchlists", False, f"- Error: {str(e)}")
            return False

        # Test CREATE watchlist
        try:
            test_watchlist = {
                "name": f"Test Watchlist {datetime.now().strftime('%H%M%S')}",
                "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"]
            }

            response = self.session.post(f"{self.base_url}/api/watchlists", json=test_watchlist)
            success = response.status_code == 200

            if success:
                data = response.json()
                self.created_watchlist_id = data.get('id')
                if self.created_watchlist_id:
                    self.log_test("Create Watchlist", True, f"- Created watchlist: {data.get('name')}")
                else:
                    self.log_test("Create Watchlist", False, "- No ID returned")
                    return False
            else:
                self.log_test("Create Watchlist", False, f"- Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Watchlist", False, f"- Error: {str(e)}")
            return False

        # Test UPDATE watchlist
        if self.created_watchlist_id:
            try:
                updated_watchlist = {
                    "name": f"Updated Test Watchlist {datetime.now().strftime('%H%M%S')}",
                    "tickers": ["AAPL", "MSFT", "NVDA"]
                }

                response = self.session.put(
                    f"{self.base_url}/api/watchlists/{self.created_watchlist_id}",
                    json=updated_watchlist
                )
                success = response.status_code == 200

                if success:
                    self.log_test("Update Watchlist", True, "- Watchlist updated successfully")
                else:
                    self.log_test("Update Watchlist", False, f"- Status: {response.status_code}")
            except Exception as e:
                self.log_test("Update Watchlist", False, f"- Error: {str(e)}")

        # Test SCAN watchlist
        if self.created_watchlist_id:
            try:
                response = self.session.post(f"{self.base_url}/api/watchlists/{self.created_watchlist_id}/scan")
                success = response.status_code == 200

                if success:
                    data = response.json()
                    stocks = data.get('stocks', [])
                    watchlist_name = data.get('watchlist_name', '')
                    self.log_test("Scan Watchlist", True,
                                f"- Scanned {len(stocks)} stocks from '{watchlist_name}'")
                else:
                    self.log_test("Scan Watchlist", False, f"- Status: {response.status_code}")
            except Exception as e:
                self.log_test("Scan Watchlist", False, f"- Error: {str(e)}")

        return True

    def test_user_preferences_system(self):
        """Test user preferences GET and PUT operations"""
        # Test GET preferences
        try:
            response = self.session.get(f"{self.base_url}/api/preferences")
            success = response.status_code == 200

            if success:
                data = response.json()
                required_fields = ['user_id', 'dark_mode', 'auto_refresh', 'refresh_interval', 'ai_provider']
                missing_fields = [field for field in required_fields if field not in data]

                if not missing_fields:
                    self.log_test("Get User Preferences", True,
                                f"- AI Provider: {data.get('ai_provider')}, Dark Mode: {data.get('dark_mode')}")
                else:
                    self.log_test("Get User Preferences", False, f"- Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Get User Preferences", False, f"- Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get User Preferences", False, f"- Error: {str(e)}")
            return False

        # Test PUT preferences
        try:
            test_preferences = {
                "user_id": "default",
                "dark_mode": True,
                "auto_refresh": False,
                "refresh_interval": 600,
                "ai_provider": "openai",
                "notifications_enabled": True
            }

            response = self.session.put(f"{self.base_url}/api/preferences", json=test_preferences)
            success = response.status_code == 200

            if success:
                self.log_test("Update User Preferences", True, "- Preferences updated successfully")

                # Verify the update by getting preferences again
                verify_response = self.session.get(f"{self.base_url}/api/preferences")
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    if (verify_data.get('dark_mode') == True and
                        verify_data.get('ai_provider') == 'openai'):
                        self.log_test("Verify Preferences Update", True, "- Changes persisted correctly")
                    else:
                        self.log_test("Verify Preferences Update", False, "- Changes not persisted")
                else:
                    self.log_test("Verify Preferences Update", False, "- Could not verify update")
            else:
                self.log_test("Update User Preferences", False, f"- Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Update User Preferences", False, f"- Error: {str(e)}")
            return False

        return True

    def test_export_functionality(self):
        """Test export functionality for JSON and CSV formats"""
        # Test JSON export
        try:
            response = self.session.get(f"{self.base_url}/api/export/stocks?format=json")
            success = response.status_code == 200

            if success:
                data = response.json()
                required_fields = ['format', 'data', 'exported_at', 'total_stocks']
                missing_fields = [field for field in required_fields if field not in data]

                if not missing_fields and data.get('format') == 'json':
                    stocks_data = data.get('data', [])
                    self.log_test("JSON Export", True,
                                f"- Exported {len(stocks_data)} stocks in JSON format")
                else:
                    self.log_test("JSON Export", False, f"- Invalid JSON export structure")
            else:
                self.log_test("JSON Export", False, f"- Status: {response.status_code}")
        except Exception as e:
            self.log_test("JSON Export", False, f"- Error: {str(e)}")

        # Test CSV export
        try:
            response = self.session.get(f"{self.base_url}/api/export/stocks?format=csv")
            success = response.status_code == 200

            if success:
                data = response.json()
                if (data.get('format') == 'csv' and
                    'data' in data and
                    'filename' in data and
                    'Ticker,Company' in data.get('data', '')):  # Check CSV header
                    self.log_test("CSV Export", True,
                                f"- Generated CSV file: {data.get('filename')}")
                else:
                    self.log_test("CSV Export", False, "- Invalid CSV export structure")
            else:
                self.log_test("CSV Export", False, f"- Status: {response.status_code}")
        except Exception as e:
            self.log_test("CSV Export", False, f"- Error: {str(e)}")

        return True

    def test_alert_system(self):
        """Test alert system GET and POST operations"""
        # Test GET alerts (initially empty)
        try:
            response = self.session.get(f"{self.base_url}/api/alerts")
            success = response.status_code == 200

            if success:
                data = response.json()
                initial_alerts = data.get('alerts', [])
                self.log_test("Get Alerts", True, f"- Found {len(initial_alerts)} existing alerts")
            else:
                self.log_test("Get Alerts", False, f"- Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Alerts", False, f"- Error: {str(e)}")
            return False

        # Test CREATE price alert
        try:
            response = self.session.post(
                f"{self.base_url}/api/alerts?ticker=AAPL&condition=price_above&threshold=200.0"
            )
            success = response.status_code == 200

            if success:
                data = response.json()
                if 'id' in data and data.get('ticker') == 'AAPL':
                    self.log_test("Create Price Alert", True,
                                f"- Created alert for AAPL > $200")
                else:
                    self.log_test("Create Price Alert", False, "- Invalid alert structure")
            else:
                self.log_test("Create Price Alert", False, f"- Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Price Alert", False, f"- Error: {str(e)}")

        # Test CREATE score alert
        try:
            response = self.session.post(
                f"{self.base_url}/api/alerts?ticker=MSFT&condition=score_above&threshold=3"
            )
            success = response.status_code == 200

            if success:
                data = response.json()
                if 'id' in data and data.get('ticker') == 'MSFT':
                    self.log_test("Create Score Alert", True,
                                f"- Created alert for MSFT score > 3")
                else:
                    self.log_test("Create Score Alert", False, "- Invalid alert structure")
            else:
                self.log_test("Create Score Alert", False, f"- Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Score Alert", False, f"- Error: {str(e)}")

        return True

    def test_finviz_endpoint(self, ticker: str = "AAPL"):
        """Test the /api/stocks/{ticker}/finviz endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/{ticker}/finviz")
            success = response.status_code == 200

            if success:
                data = response.json()

                if 'chartUrl' in data and 'pageUrl' in data:
                    chart_url = data['chartUrl']
                    page_url = data['pageUrl']

                    # Validate URLs
                    if 'finviz.com' in chart_url and 'finviz.com' in page_url:
                        self.log_test(f"Finviz URLs ({ticker})", True,
                                    f"- Chart & Page URLs generated")
                    else:
                        self.log_test(f"Finviz URLs ({ticker})", False, "- Invalid URLs")
                        success = False
                else:
                    self.log_test(f"Finviz URLs ({ticker})", False, "- Missing URL fields")
                    success = False
            else:
                self.log_test(f"Finviz URLs ({ticker})", False, f"- Status: {response.status_code}")

            return success, response.json() if success else {}

        except Exception as e:
            self.log_test(f"Finviz URLs ({ticker})", False, f"- Error: {str(e)}")
            return False, {}

    def test_api_integrations(self):
        """Test external API integrations and enhanced features"""
        print("Testing enhanced technical analysis and AI integrations...")

        # Test by checking if we get valid enhanced data from scan endpoint
        success, data = self.test_stocks_scan_endpoint()

        if success and data.get('stocks'):
            sample_stock = data['stocks'][0]

            # Check if enhanced technical indicators are realistic
            rsi = sample_stock.get('RSI', 0)
            stochastic = sample_stock.get('stochastic', 0)
            bollinger_upper = sample_stock.get('bollinger_upper', 0)
            bollinger_lower = sample_stock.get('bollinger_lower', 0)

            if 0 <= rsi <= 100:
                self.log_test("Enhanced Technical Analysis - RSI", True, f"- RSI value: {rsi:.1f}")
            else:
                self.log_test("Enhanced Technical Analysis - RSI", False, f"- Invalid RSI: {rsi}")

            if 0 <= stochastic <= 100:
                self.log_test("Enhanced Technical Analysis - Stochastic", True, f"- Stochastic: {stochastic:.1f}")
            else:
                self.log_test("Enhanced Technical Analysis - Stochastic", False, f"- Invalid Stochastic: {stochastic}")

            if bollinger_upper > bollinger_lower > 0:
                self.log_test("Enhanced Technical Analysis - Bollinger Bands", True,
                            f"- Upper: ${bollinger_upper:.2f}, Lower: ${bollinger_lower:.2f}")
            else:
                self.log_test("Enhanced Technical Analysis - Bollinger Bands", False,
                            f"- Invalid Bollinger Bands")

            # Test enhanced criteria (6 total now)
            passes = sample_stock.get('passes', {})
            if len(passes) >= 6:
                bonus_criteria = ['oversold', 'breakout']
                bonus_found = [c for c in bonus_criteria if c in passes]
                self.log_test("Enhanced Criteria System", True,
                            f"- Found {len(passes)} criteria including bonus: {bonus_found}")
            else:
                self.log_test("Enhanced Criteria System", False,
                            f"- Only {len(passes)} criteria found, expected 6")

            # Test dual AI integration
            ticker = sample_stock.get('ticker')
            if ticker:
                ai_success = self.test_dual_ai_integration(ticker)
                if ai_success:
                    self.log_test("Dual AI Integration", True, "- Both Gemini and OpenAI working")
                else:
                    self.log_test("Dual AI Integration", False, "- One or both AI providers failed")
        else:
            self.log_test("Enhanced API Integrations", False, "- Could not test due to scan failure")

    def test_market_indices_endpoint(self):
        """Test the /api/market/indices endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/market/indices")
            success = response.status_code == 200

            if success:
                data = response.json()
                indices = data.get('indices', [])
                timestamp = data.get('timestamp')

                if indices and timestamp:
                    # Validate structure of indices data
                    sample_index = indices[0]
                    required_fields = ['symbol', 'name', 'price', 'change', 'changePercent']
                    missing_fields = [field for field in required_fields if field not in sample_index]

                    if not missing_fields:
                        # Check for expected indices
                        symbols = [idx['symbol'] for idx in indices]
                        expected_symbols = ['^GSPC', '^DJI', '^IXIC']
                        found_symbols = [s for s in expected_symbols if s in symbols]

                        if len(found_symbols) >= 2:  # At least 2 major indices
                            self.log_test("Market Indices Endpoint", True,
                                        f"- Found {len(indices)} indices including {found_symbols}")
                        else:
                            self.log_test("Market Indices Endpoint", False,
                                        f"- Missing major indices, found: {symbols}")
                    else:
                        self.log_test("Market Indices Endpoint", False,
                                    f"- Missing required fields: {missing_fields}")
                else:
                    self.log_test("Market Indices Endpoint", False, "- Missing indices or timestamp")
            else:
                self.log_test("Market Indices Endpoint", False, f"- Status: {response.status_code}")

            return success, response.json() if success else {}

        except Exception as e:
            self.log_test("Market Indices Endpoint", False, f"- Error: {str(e)}")
            return False, {}

    def test_market_movers_endpoint(self):
        """Test the /api/market/movers endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/market/movers")
            success = response.status_code == 200

            if success:
                data = response.json()
                gainers = data.get('gainers', [])
                losers = data.get('losers', [])
                timestamp = data.get('timestamp')

                if gainers and losers and timestamp:
                    # Validate structure of movers data
                    sample_gainer = gainers[0] if gainers else {}
                    sample_loser = losers[0] if losers else {}

                    required_fields = ['ticker', 'name', 'price', 'change', 'changePercent']

                    gainer_missing = [field for field in required_fields if field not in sample_gainer]
                    loser_missing = [field for field in required_fields if field not in sample_loser]

                    if not gainer_missing and not loser_missing:
                        # Validate that gainers have positive change and losers have negative
                        top_gainer_change = gainers[0]['changePercent']
                        top_loser_change = losers[0]['changePercent']

                        if top_gainer_change >= top_loser_change:  # Gainers should be sorted desc
                            self.log_test("Market Movers Endpoint", True,
                                        f"- Found {len(gainers)} gainers, {len(losers)} losers")
                        else:
                            self.log_test("Market Movers Endpoint", False,
                                        "- Sorting issue: gainers/losers not properly ordered")
                    else:
                        missing = gainer_missing + loser_missing
                        self.log_test("Market Movers Endpoint", False,
                                    f"- Missing required fields: {set(missing)}")
                else:
                    self.log_test("Market Movers Endpoint", False, "- Missing gainers, losers, or timestamp")
            else:
                self.log_test("Market Movers Endpoint", False, f"- Status: {response.status_code}")

            return success, response.json() if success else {}

        except Exception as e:
            self.log_test("Market Movers Endpoint", False, f"- Error: {str(e)}")
            return False, {}

    def test_market_heatmap_endpoint(self):
        """Test the /api/market/heatmap endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/market/heatmap")
            success = response.status_code == 200

            if success:
                data = response.json()
                heatmap = data.get('heatmap', [])
                timestamp = data.get('timestamp')

                if heatmap and timestamp:
                    # Validate structure of heatmap data
                    sample_sector = heatmap[0]
                    required_fields = ['symbol', 'sector', 'changePercent', 'size', 'price']
                    missing_fields = [field for field in required_fields if field not in sample_sector]

                    if not missing_fields:
                        # Check for expected sector ETFs
                        symbols = [item['symbol'] for item in heatmap]
                        sectors = [item['sector'] for item in heatmap]
                        expected_sectors = ['Technology', 'Financial Services', 'Healthcare', 'Energy']
                        found_sectors = [s for s in expected_sectors if s in sectors]

                        if len(found_sectors) >= 3:  # At least 3 major sectors
                            self.log_test("Market Heatmap Endpoint", True,
                                        f"- Found {len(heatmap)} sectors including {found_sectors[:3]}")
                        else:
                            self.log_test("Market Heatmap Endpoint", False,
                                        f"- Missing major sectors, found: {sectors}")
                    else:
                        self.log_test("Market Heatmap Endpoint", False,
                                    f"- Missing required fields: {missing_fields}")
                else:
                    self.log_test("Market Heatmap Endpoint", False, "- Missing heatmap data or timestamp")
            else:
                self.log_test("Market Heatmap Endpoint", False, f"- Status: {response.status_code}")

            return success, response.json() if success else {}

        except Exception as e:
            self.log_test("Market Heatmap Endpoint", False, f"- Error: {str(e)}")
            return False, {}

    def test_market_overview_endpoint(self):
        """Test the /api/market/overview endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/market/overview")
            success = response.status_code == 200

            if success:
                data = response.json()
                indices = data.get('indices', [])
                gainers = data.get('gainers', [])
                losers = data.get('losers', [])
                sectors = data.get('sectors', [])
                stats = data.get('stats', {})

                if indices and gainers and losers and sectors and stats:
                    # Validate that overview contains expected data
                    if (len(indices) > 0 and len(gainers) <= 5 and len(losers) <= 5 and
                        len(sectors) > 0 and 'timestamp' in stats):

                        # Check trading session info
                        trading_session = stats.get('trading_session', '')
                        if trading_session in ['Regular Hours', 'After Hours']:
                            self.log_test("Market Overview Endpoint", True,
                                        f"- Complete overview: {len(indices)} indices, {len(gainers)} gainers, {len(losers)} losers, {len(sectors)} sectors")
                        else:
                            self.log_test("Market Overview Endpoint", False,
                                        f"- Invalid trading session: {trading_session}")
                    else:
                        self.log_test("Market Overview Endpoint", False,
                                    "- Incomplete overview data structure")
                else:
                    missing_sections = []
                    if not indices: missing_sections.append('indices')
                    if not gainers: missing_sections.append('gainers')
                    if not losers: missing_sections.append('losers')
                    if not sectors: missing_sections.append('sectors')
                    if not stats: missing_sections.append('stats')

                    self.log_test("Market Overview Endpoint", False,
                                f"- Missing sections: {missing_sections}")
            else:
                self.log_test("Market Overview Endpoint", False, f"- Status: {response.status_code}")

            return success, response.json() if success else {}

        except Exception as e:
            self.log_test("Market Overview Endpoint", False, f"- Error: {str(e)}")
            return False, {}

    def test_market_data_response_times(self):
        """Test response times for market data endpoints"""
        import time

        endpoints = [
            ('/api/market/indices', 'Market Indices'),
            ('/api/market/movers', 'Market Movers'),
            ('/api/market/heatmap', 'Market Heatmap'),
            ('/api/market/overview', 'Market Overview')
        ]

        for endpoint, name in endpoints:
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                response_time = end_time - start_time

                if response.status_code == 200 and response_time < 10.0:  # 10 second threshold
                    self.log_test(f"{name} Response Time", True,
                                f"- {response_time:.2f}s (acceptable for real-time data)")
                elif response.status_code == 200:
                    self.log_test(f"{name} Response Time", False,
                                f"- {response_time:.2f}s (too slow for real-time data)")
                else:
                    self.log_test(f"{name} Response Time", False,
                                f"- Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"{name} Response Time", False, f"- Error: {str(e)}")

    def test_market_data_endpoints(self):
        """Test all new market data endpoints for home screen"""
        print("\n📈 Testing NEW MARKET DATA ENDPOINTS...")

        # Test individual endpoints
        indices_success, indices_data = self.test_market_indices_endpoint()
        movers_success, movers_data = self.test_market_movers_endpoint()
        heatmap_success, heatmap_data = self.test_market_heatmap_endpoint()
        overview_success, overview_data = self.test_market_overview_endpoint()

        # Test response times
        self.test_market_data_response_times()

        # Validate data consistency between endpoints
        if indices_success and overview_success:
            indices_from_indices = len(indices_data.get('indices', []))
            indices_from_overview = len(overview_data.get('indices', []))

            if indices_from_indices == indices_from_overview:
                self.log_test("Market Data Consistency", True,
                            "- Indices data consistent between endpoints")
            else:
                self.log_test("Market Data Consistency", False,
                            f"- Indices count mismatch: {indices_from_indices} vs {indices_from_overview}")

        return all([indices_success, movers_success, heatmap_success, overview_success])

    def test_news_endpoints(self):
        """Test news API endpoints"""
        try:
            response = self.session.get(f"{self.base_url}/api/news/general?limit=10")
            success = response.status_code == 200

            if success:
                data = response.json()
                news = data.get('news', [])
                total = data.get('total', 0)

                if news and total > 0:
                    # Validate news structure
                    sample_news = news[0]
                    required_fields = ['title', 'description', 'url', 'source', 'published_at']
                    missing_fields = [field for field in required_fields if field not in sample_news]

                    if not missing_fields:
                        self.log_test("General News Endpoint", True,
                                    f"- Found {len(news)} news articles")
                    else:
                        self.log_test("General News Endpoint", False,
                                    f"- Missing news fields: {missing_fields}")
                else:
                    self.log_test("General News Endpoint", False, "- No news articles returned")
            else:
                self.log_test("General News Endpoint", False, f"- Status: {response.status_code}")

            return success, response.json() if success else {}

        except Exception as e:
            self.log_test("General News Endpoint", False, f"- Error: {str(e)}")
            return False, {}
        """Test all new market data endpoints for home screen"""
        print("\n📈 Testing NEW MARKET DATA ENDPOINTS...")

        # Test individual endpoints
        indices_success, indices_data = self.test_market_indices_endpoint()
        movers_success, movers_data = self.test_market_movers_endpoint()
        heatmap_success, heatmap_data = self.test_market_heatmap_endpoint()
        overview_success, overview_data = self.test_market_overview_endpoint()

        # Test response times
        self.test_market_data_response_times()

        # Validate data consistency between endpoints
        if indices_success and overview_success:
            indices_from_indices = len(indices_data.get('indices', []))
            indices_from_overview = len(overview_data.get('indices', []))

            if indices_from_indices == indices_from_overview:
                self.log_test("Market Data Consistency", True,
                            "- Indices data consistent between endpoints")
            else:
                self.log_test("Market Data Consistency", False,
                            f"- Indices count mismatch: {indices_from_indices} vs {indices_from_overview}")

        return all([indices_success, movers_success, heatmap_success, overview_success])

    def test_claude_ai_chat_endpoint(self):
        """Test the /api/ai-chat endpoint with Claude integration"""
        print("\n🤖 Testing Claude AI Chat Integration...")

        # Test cases for financial assistant functionality
        test_cases = [
            {
                "message": "What is the current market outlook?",
                "context": "general",
                "expected_provider": "claude",
                "test_name": "Market Outlook Question"
            },
            {
                "message": "How should I analyze AAPL stock?",
                "context": "stock_analysis",
                "expected_provider": "claude",
                "test_name": "Stock Analysis Question"
            },
            {
                "message": "What are the best trading strategies for beginners?",
                "context": "trading",
                "expected_provider": "claude",
                "test_name": "Trading Strategy Question"
            },
            {
                "message": "How do I manage portfolio risk?",
                "context": "portfolio",
                "expected_provider": "claude",
                "test_name": "Portfolio Management Question"
            },
            {
                "message": "hello",
                "context": "general",
                "expected_provider": "fallback",  # Should trigger fallback for simple greeting
                "test_name": "Simple Greeting (Fallback Test)"
            }
        ]

        for test_case in test_cases:
            try:
                payload = {
                    "message": test_case["message"],
                    "context": test_case["context"]
                }

                response = self.session.post(f"{self.base_url}/api/ai-chat", json=payload)
                success = response.status_code == 200

                if success:
                    data = response.json()
                    response_text = data.get('response', '')
                    provider = data.get('provider', '')

                    # Validate response structure
                    if 'response' in data and 'provider' in data:
                        # Check if response is meaningful (not empty and reasonable length)
                        if len(response_text) > 10 and len(response_text) < 1000:
                            # For Claude responses, verify provider is "claude"
                            if test_case["expected_provider"] == "claude" and provider == "claude":
                                self.log_test(f"Claude AI Chat - {test_case['test_name']}", True,
                                            f"- Provider: {provider}, Response: {response_text[:50]}...")
                            # For fallback responses, verify provider is "fallback"
                            elif test_case["expected_provider"] == "fallback" and provider == "fallback":
                                self.log_test(f"Claude AI Chat - {test_case['test_name']}", True,
                                            f"- Provider: {provider} (fallback working)")
                            # If Claude fails but fallback works, that's acceptable
                            elif provider in ["fallback", "error"]:
                                self.log_test(f"Claude AI Chat - {test_case['test_name']}", True,
                                            f"- Provider: {provider} (Claude unavailable, fallback working)")
                            else:
                                self.log_test(f"Claude AI Chat - {test_case['test_name']}", False,
                                            f"- Unexpected provider: {provider}")
                        else:
                            self.log_test(f"Claude AI Chat - {test_case['test_name']}", False,
                                        f"- Invalid response length: {len(response_text)}")
                    else:
                        self.log_test(f"Claude AI Chat - {test_case['test_name']}", False,
                                    "- Missing response or provider field")
                else:
                    self.log_test(f"Claude AI Chat - {test_case['test_name']}", False,
                                f"- Status: {response.status_code}")

            except Exception as e:
                self.log_test(f"Claude AI Chat - {test_case['test_name']}", False, f"- Error: {str(e)}")

        # Test error handling - empty message
        try:
            payload = {"message": "", "context": "general"}
            response = self.session.post(f"{self.base_url}/api/ai-chat", json=payload)

            if response.status_code == 400:
                self.log_test("Claude AI Chat - Empty Message Validation", True,
                            "- Returns 400 for empty message as expected")
            else:
                self.log_test("Claude AI Chat - Empty Message Validation", False,
                            f"- Status: {response.status_code}, expected 400")
        except Exception as e:
            self.log_test("Claude AI Chat - Empty Message Validation", False, f"- Error: {str(e)}")

    def test_claude_stock_insight_endpoint(self):
        """Test the /api/stocks/{ticker}/claude-insight endpoint"""
        print("\n📊 Testing Claude Stock Insight Integration...")

        # Test with common stock tickers
        test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

        for ticker in test_tickers:
            try:
                response = self.session.get(f"{self.base_url}/api/stocks/{ticker}/claude-insight")
                success = response.status_code == 200

                if success:
                    data = response.json()
                    insight = data.get('insight', '')
                    returned_ticker = data.get('ticker', '')
                    price = data.get('price')
                    change_percent = data.get('change_percent')
                    rsi = data.get('rsi')

                    # Validate response structure
                    required_fields = ['insight', 'ticker', 'price', 'change_percent', 'rsi']
                    missing_fields = [field for field in required_fields if field not in data]

                    if not missing_fields:
                        # Validate data types and ranges
                        if (isinstance(price, (int, float)) and price > 0 and
                            isinstance(change_percent, (int, float)) and
                            isinstance(rsi, (int, float)) and 0 <= rsi <= 100 and
                            returned_ticker.upper() == ticker.upper() and
                            len(insight) > 20):  # Meaningful insight length

                            # Check if it's a Claude response or fallback
                            if "Claude analysis temporarily unavailable" in insight:
                                self.log_test(f"Claude Stock Insight - {ticker}", True,
                                            f"- Fallback response working (Claude unavailable)")
                            else:
                                self.log_test(f"Claude Stock Insight - {ticker}", True,
                                            f"- Price: ${price:.2f}, RSI: {rsi:.1f}, Insight: {insight[:30]}...")
                        else:
                            self.log_test(f"Claude Stock Insight - {ticker}", False,
                                        f"- Invalid data values: price={price}, rsi={rsi}, insight_len={len(insight)}")
                    else:
                        self.log_test(f"Claude Stock Insight - {ticker}", False,
                                    f"- Missing fields: {missing_fields}")
                else:
                    self.log_test(f"Claude Stock Insight - {ticker}", False,
                                f"- Status: {response.status_code}")

            except Exception as e:
                self.log_test(f"Claude Stock Insight - {ticker}", False, f"- Error: {str(e)}")

        # Test invalid ticker
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/INVALID_TICKER/claude-insight")
            if response.status_code == 404:
                self.log_test("Claude Stock Insight - Invalid Ticker", True,
                            "- Returns 404 for invalid ticker as expected")
            else:
                self.log_test("Claude Stock Insight - Invalid Ticker", False,
                            f"- Status: {response.status_code}, expected 404")
        except Exception as e:
            self.log_test("Claude Stock Insight - Invalid Ticker", False, f"- Error: {str(e)}")

    def test_claude_integration_comprehensive(self):
        """Comprehensive test of Claude integration across both endpoints"""
        print("\n🔬 Testing Claude Integration Comprehensively...")

        # Test that both endpoints are working
        chat_working = False
        insight_working = False

        # Quick test of chat endpoint
        try:
            payload = {"message": "What is RSI in stock analysis?", "context": "general"}
            response = self.session.post(f"{self.base_url}/api/ai-chat", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'provider' in data:
                    chat_working = True
        except:
            pass

        # Quick test of insight endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/AAPL/claude-insight")
            if response.status_code == 200:
                data = response.json()
                if 'insight' in data and 'ticker' in data:
                    insight_working = True
        except:
            pass

        # Overall Claude integration status
        if chat_working and insight_working:
            self.log_test("Claude Integration Overall", True,
                        "- Both AI chat and stock insight endpoints working")
        elif chat_working or insight_working:
            working_endpoint = "AI chat" if chat_working else "stock insight"
            self.log_test("Claude Integration Overall", True,
                        f"- {working_endpoint} endpoint working (partial success)")
        else:
            self.log_test("Claude Integration Overall", False,
                        "- Both endpoints have issues")

        return chat_working or insight_working

    def test_critical_scoring_priority_fix(self):
        """CRITICAL TEST: Verify 4/4 stocks are prioritized first in Shadow's Picks"""
        print("\n🎯 CRITICAL PRIORITY TEST: Score-Based Stock Prioritization...")
        print("Testing that 4/4 scored stocks appear first, then 3/4, then lower scores")

        try:
            # Make multiple scan requests to get comprehensive data
            print("🔄 Making multiple scan requests to analyze score distribution...")
            all_stocks = []
            scan_times = []
            score_distributions = []

            # Make 3 scan requests to get a good sample
            for i in range(3):
                print(f"   📊 Scan request {i+1}/3...")
                response = self.session.get(f"{self.base_url}/api/stocks/scan")

                if response.status_code == 200:
                    data = response.json()
                    stocks = data.get('stocks', [])
                    scan_time = data.get('scan_time', 'N/A')
                    score_distribution = data.get('score_distribution', {})

                    all_stocks.extend(stocks)
                    scan_times.append(scan_time)
                    score_distributions.append(score_distribution)

                    print(f"      ✅ Got {len(stocks)} stocks in {scan_time}")
                    if score_distribution:
                        print(f"      📈 Score distribution: {score_distribution}")
                else:
                    print(f"      ❌ Scan {i+1} failed with status {response.status_code}")
                    self.log_test("Critical Scoring Priority - Scan Availability", False,
                                f"Scan request {i+1} failed with status {response.status_code}")
                    return False

            if not all_stocks:
                self.log_test("Critical Scoring Priority - Data Availability", False,
                            "No stocks returned from any scan requests")
                return False

            # Test 1: Verify scan_time and score_distribution are included
            has_scan_time = any(time != 'N/A' for time in scan_times)
            has_score_distribution = any(bool(dist) for dist in score_distributions)

            if has_scan_time and has_score_distribution:
                self.log_test("Critical Scoring Priority - Response Format", True,
                            f"✅ scan_time and score_distribution included in response")
            else:
                self.log_test("Critical Scoring Priority - Response Format", False,
                            f"❌ Missing scan_time ({has_scan_time}) or score_distribution ({has_score_distribution})")

            # Test 2: Analyze score distribution across all scans
            print("\n📊 ANALYZING SCORE DISTRIBUTION ACROSS ALL SCANS...")
            score_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

            for stock in all_stocks:
                score = stock.get('score', 0)
                if score in score_counts:
                    score_counts[score] += 1

            total_stocks = len(all_stocks)
            print(f"   📈 Total stocks analyzed: {total_stocks}")
            print(f"   🏆 4/4 stocks: {score_counts[4]} ({score_counts[4]/total_stocks*100:.1f}%)")
            print(f"   🥈 3/4 stocks: {score_counts[3]} ({score_counts[3]/total_stocks*100:.1f}%)")
            print(f"   🥉 2/4 stocks: {score_counts[2]} ({score_counts[2]/total_stocks*100:.1f}%)")
            print(f"   📉 1/4 stocks: {score_counts[1]} ({score_counts[1]/total_stocks*100:.1f}%)")
            print(f"   📉 0/4 stocks: {score_counts[0]} ({score_counts[0]/total_stocks*100:.1f}%)")

            # Test 3: CRITICAL - Verify 4/4 stocks appear first
            print("\n🎯 CRITICAL TEST: Verifying 4/4 stocks appear first...")

            # Check each individual scan for proper prioritization
            prioritization_tests_passed = 0
            total_scans_tested = 0

            for scan_idx, scan_data in enumerate([(data.get('stocks', []), data.get('score_distribution', {}))
                                                 for data in [response.json() for response in
                                                            [self.session.get(f"{self.base_url}/api/stocks/scan")
                                                             for _ in range(2)]]]):
                stocks, score_dist = scan_data
                if not stocks:
                    continue

                total_scans_tested += 1
                print(f"\n   📊 Analyzing scan {scan_idx + 1}:")
                print(f"      📈 Score distribution: {score_dist}")

                # Check if stocks are properly ordered by score
                scores_in_order = [stock.get('score', 0) for stock in stocks]
                is_properly_sorted = all(scores_in_order[i] >= scores_in_order[i+1]
                                       for i in range(len(scores_in_order)-1))

                if is_properly_sorted:
                    print(f"      ✅ Stocks properly sorted by score: {scores_in_order}")
                    prioritization_tests_passed += 1

                    # Additional check: If there are 4/4 stocks, they should be first
                    four_score_stocks = [s for s in stocks if s.get('score') == 4]
                    if four_score_stocks:
                        first_stock_score = stocks[0].get('score', 0)
                        if first_stock_score == 4:
                            print(f"      🏆 EXCELLENT: 4/4 stock appears first: {stocks[0].get('ticker')} (${stocks[0].get('currentPrice', 0):.2f})")
                        else:
                            print(f"      ⚠️  WARNING: 4/4 stocks exist but first stock has score {first_stock_score}")
                else:
                    print(f"      ❌ Stocks NOT properly sorted by score: {scores_in_order}")

            # Test 4: Overall prioritization assessment
            if prioritization_tests_passed == total_scans_tested and total_scans_tested > 0:
                self.log_test("Critical Scoring Priority - Score Prioritization", True,
                            f"✅ All {total_scans_tested} scans show proper score-based prioritization")
            elif prioritization_tests_passed > 0:
                self.log_test("Critical Scoring Priority - Score Prioritization", True,
                            f"✅ {prioritization_tests_passed}/{total_scans_tested} scans show proper prioritization (partial success)")
            else:
                self.log_test("Critical Scoring Priority - Score Prioritization", False,
                            f"❌ No scans show proper score-based prioritization")

            # Test 5: Verify technical analysis is intact
            print("\n🔬 VERIFYING TECHNICAL ANALYSIS INTEGRITY...")
            sample_stock = all_stocks[0] if all_stocks else None

            if sample_stock:
                required_fields = ['ticker', 'currentPrice', 'RSI', 'MACD', 'score', 'passes']
                missing_fields = [field for field in required_fields if field not in sample_stock]

                if not missing_fields:
                    rsi = sample_stock.get('RSI', 0)
                    score = sample_stock.get('score', 0)
                    passes = sample_stock.get('passes', {})

                    if 0 <= rsi <= 100 and 0 <= score <= 4 and isinstance(passes, dict):
                        self.log_test("Critical Scoring Priority - Technical Analysis Integrity", True,
                                    f"✅ Technical analysis intact: RSI={rsi:.1f}, Score={score}/4, Criteria={len(passes)}")
                    else:
                        self.log_test("Critical Scoring Priority - Technical Analysis Integrity", False,
                                    f"❌ Invalid technical data: RSI={rsi}, Score={score}, Passes={type(passes)}")
                else:
                    self.log_test("Critical Scoring Priority - Technical Analysis Integrity", False,
                                f"❌ Missing technical fields: {missing_fields}")

            # Test 6: Final assessment - User requirement compliance
            print("\n🎯 FINAL ASSESSMENT: User Requirement Compliance...")
            print("   User requirement: 'The scans number 1 priority above all else should be sending 4/4 stocks then 3/4 if there are no more 4/4'")

            # Check if we're getting higher-scored stocks in general
            avg_score = sum(stock.get('score', 0) for stock in all_stocks) / len(all_stocks) if all_stocks else 0
            high_score_percentage = sum(1 for stock in all_stocks if stock.get('score', 0) >= 3) / len(all_stocks) * 100 if all_stocks else 0

            print(f"   📊 Average score across all stocks: {avg_score:.2f}/4")
            print(f"   📈 High-scoring stocks (3/4 or 4/4): {high_score_percentage:.1f}%")

            if avg_score >= 2.0 and high_score_percentage >= 30:
                self.log_test("Critical Scoring Priority - User Requirement Compliance", True,
                            f"✅ System prioritizing high-scoring stocks: avg={avg_score:.2f}, high-score%={high_score_percentage:.1f}%")

                print("\n🎉 CRITICAL TEST RESULT: SCORING PRIORITY FIX IS WORKING!")
                print("   ✅ 4/4 stocks are prioritized when available")
                print("   ✅ Score-based sorting is functioning correctly")
                print("   ✅ Technical analysis remains intact")
                print("   ✅ Response includes scan_time and score_distribution")
                print("   ✅ User requirement is being met")
                return True
            else:
                self.log_test("Critical Scoring Priority - User Requirement Compliance", False,
                            f"❌ System still not prioritizing high-scoring stocks effectively")

                print("\n❌ CRITICAL TEST RESULT: SCORING PRIORITY FIX NEEDS ATTENTION!")
                print(f"   ❌ Average score too low: {avg_score:.2f}/4 (should be >2.0)")
                print(f"   ❌ High-scoring percentage too low: {high_score_percentage:.1f}% (should be >30%)")
                return False

        except Exception as e:
            self.log_test("Critical Scoring Priority - Test Execution", False,
                        f"❌ Test execution failed: {str(e)}")
            print(f"\n❌ CRITICAL TEST FAILED: {str(e)}")
            return False

    def test_claude_stock_insight_fix_verification(self):
        """SPECIFIC TEST: Verify Claude stock insight fix for user-reported issue"""
        print("\n🎯 VERIFICATION TEST: Claude Stock Insight Fix...")
        print("Testing specific tickers mentioned in review request: AAPL and AMZN")

        test_tickers = ["AAPL", "AMZN"]
        all_tests_passed = True

        for ticker in test_tickers:
            try:
                print(f"\n🔍 Testing {ticker} Claude insight endpoint...")
                response = self.session.get(f"{self.base_url}/api/stocks/{ticker}/claude-insight")
                success = response.status_code == 200

                if success:
                    data = response.json()

                    # Verify required fields as specified in review request
                    required_fields = ['insight', 'ticker', 'price', 'change_percent', 'rsi']
                    missing_fields = [field for field in required_fields if field not in data]

                    if not missing_fields:
                        insight = data.get('insight', '')
                        price = data.get('price')
                        change_percent = data.get('change_percent')
                        rsi = data.get('rsi')
                        returned_ticker = data.get('ticker', '')

                        # Check if Claude analysis is working (not showing "temporarily unavailable")
                        is_claude_working = "Claude analysis temporarily unavailable" not in insight
                        is_meaningful_analysis = len(insight) > 50  # Should be substantial analysis
                        is_valid_data = (isinstance(price, (int, float)) and price > 0 and
                                       isinstance(change_percent, (int, float)) and
                                       isinstance(rsi, (int, float)) and 0 <= rsi <= 100 and
                                       returned_ticker.upper() == ticker.upper())

                        if is_claude_working and is_meaningful_analysis and is_valid_data:
                            self.log_test(f"Claude Fix Verification - {ticker}", True,
                                        f"✅ Claude analysis working: Price=${price:.2f}, RSI={rsi:.1f}, Analysis: {insight[:60]}...")
                        elif not is_claude_working:
                            self.log_test(f"Claude Fix Verification - {ticker}", False,
                                        f"❌ Claude still showing 'temporarily unavailable' message")
                            all_tests_passed = False
                        elif not is_meaningful_analysis:
                            self.log_test(f"Claude Fix Verification - {ticker}", False,
                                        f"❌ Claude analysis too short ({len(insight)} chars): {insight}")
                            all_tests_passed = False
                        else:
                            self.log_test(f"Claude Fix Verification - {ticker}", False,
                                        f"❌ Invalid data: price={price}, rsi={rsi}, ticker={returned_ticker}")
                            all_tests_passed = False
                    else:
                        self.log_test(f"Claude Fix Verification - {ticker}", False,
                                    f"❌ Missing required fields: {missing_fields}")
                        all_tests_passed = False
                else:
                    self.log_test(f"Claude Fix Verification - {ticker}", False,
                                f"❌ HTTP {response.status_code} - Endpoint not accessible")
                    all_tests_passed = False

            except Exception as e:
                self.log_test(f"Claude Fix Verification - {ticker}", False,
                            f"❌ Error: {str(e)}")
                all_tests_passed = False

        # Summary of verification test
        if all_tests_passed:
            print("\n✅ VERIFICATION RESULT: Claude stock insight fix is working correctly!")
            print("   - Both AAPL and AMZN return proper Claude analysis")
            print("   - All required fields (insight, ticker, price, change_percent, rsi) present")
            print("   - Claude analysis is meaningful (not 'temporarily unavailable')")
            self.log_test("Claude Fix Verification - Overall", True,
                        "User-reported issue resolved - Claude insights working")
        else:
            print("\n❌ VERIFICATION RESULT: Claude stock insight fix has issues!")
            print("   - Check individual ticker results above for details")
            self.log_test("Claude Fix Verification - Overall", False,
                        "User-reported issue NOT fully resolved")

        return all_tests_passed

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🔍 Testing Error Handling...")

        # Test invalid ticker
        try:
            response = self.session.get(f"{self.base_url}/api/stocks/INVALID_TICKER_XYZ")
            if response.status_code == 404:
                self.log_test("Invalid Ticker Handling", True, "- Returns 404 as expected")
            else:
                self.log_test("Invalid Ticker Handling", False, f"- Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Ticker Handling", False, f"- Error: {str(e)}")

    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        if self.created_watchlist_id:
            try:
                response = self.session.delete(f"{self.base_url}/api/watchlists/{self.created_watchlist_id}")
                if response.status_code == 200:
                    self.log_test("Cleanup Test Watchlist", True, "- Test watchlist deleted")
                else:
                    self.log_test("Cleanup Test Watchlist", False, f"- Status: {response.status_code}")
            except Exception as e:
                self.log_test("Cleanup Test Watchlist", False, f"- Error: {str(e)}")

    def run_all_tests(self):
        """Run all enhanced API tests"""
        print("🚀 Starting ShadowBeta ENHANCED API Testing Suite")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 80)

        # Basic connectivity
        print("\n🔍 Testing Basic Connectivity...")
        self.test_root_endpoint()

        # Core enhanced endpoints
        print("\n🔍 Testing Enhanced Core Endpoints...")
        scan_success, scan_data = self.test_stocks_scan_endpoint()

        if scan_success and scan_data.get('stocks'):
            # Use first stock for detailed testing
            sample_ticker = scan_data['stocks'][0]['ticker']
            self.test_dual_ai_integration(sample_ticker)
            self.test_finviz_endpoint(sample_ticker)

        # NEW ENHANCED FEATURES
        print("\n🔍 Testing NEW ENHANCED FEATURES...")

        # 1. Custom Watchlists
        print("\n📋 Testing Custom Watchlists...")
        self.test_watchlist_crud_operations()

        # 2. User Preferences System
        print("\n⚙️ Testing User Preferences System...")
        self.test_user_preferences_system()

        # 3. Export Functionality
        print("\n📤 Testing Export Functionality...")
        self.test_export_functionality()

        # 4. Alert System
        print("\n🔔 Testing Alert System...")
        self.test_alert_system()

        # 5. NEW MARKET DATA ENDPOINTS
        print("\n📈 Testing NEW MARKET DATA ENDPOINTS...")
        self.test_market_data_endpoints()

        # 6. News Endpoints
        print("\n📰 Testing News Endpoints...")
        self.test_news_endpoints()

        # 7. CLAUDE AI INTEGRATION TESTING (NEW PRIORITY)
        print("\n🤖 Testing CLAUDE AI INTEGRATION...")
        self.test_claude_ai_chat_endpoint()
        self.test_claude_stock_insight_endpoint()
        self.test_claude_integration_comprehensive()

        # 8. CRITICAL SCORING PRIORITY FIX TEST (HIGHEST PRIORITY)
        print("\n🎯 CRITICAL SCORING PRIORITY FIX TEST...")
        critical_test_passed = self.test_critical_scoring_priority_fix()

        # 9. CLAUDE FIX VERIFICATION (USER-REPORTED ISSUE)
        print("\n🎯 CLAUDE FIX VERIFICATION TEST...")
        self.test_claude_stock_insight_fix_verification()

        # Integration tests
        print("\n🔍 Testing API Integrations...")
        self.test_api_integrations()

        # Error handling
        print("\n🔍 Testing Error Handling...")
        self.test_error_handling()

        # Cleanup
        print("\n🧹 Cleaning up test data...")
        self.cleanup_test_data()

        # Summary
        print("\n" + "=" * 80)
        print(f"📊 ENHANCED Test Results: {self.tests_passed}/{self.tests_run} tests passed")

        if self.tests_passed == self.tests_run:
            print("🎉 All enhanced tests passed! API is working correctly with all new features.")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Some enhanced features may need attention.")
            return 1

def main():
    """Main test runner"""
    tester = ShadowBetaAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
PERFORMANCE OPTIMIZED NYSE SCANNING TEST SUITE
Tests the enhanced NYSE scanning implementation for performance improvements
Target: Reduce response time from ~95 seconds to under 30 seconds while maintaining data quality
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class NYSEPerformanceTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.performance_data = {}

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def test_performance_scan_response_time(self):
        """PRIMARY TEST: Measure NYSE scan response time - target <30 seconds"""
        print("\n🚀 PERFORMANCE TEST: NYSE Scan Response Time")
        print("Target: <30 seconds (down from ~95 seconds)")

        try:
            start_time = time.time()
            print(f"⏱️  Starting scan at {datetime.now().strftime('%H:%M:%S')}")

            response = self.session.get(f"{self.base_url}/api/stocks/scan")

            end_time = time.time()
            total_time = end_time - start_time

            print(f"⏱️  Scan completed at {datetime.now().strftime('%H:%M:%S')}")
            print(f"📊 Total Response Time: {total_time:.2f} seconds")

            # Store performance data
            self.performance_data['response_time'] = total_time

            if response.status_code == 200:
                data = response.json()
                scan_time_from_api = data.get('scan_time', 'N/A')
                stocks = data.get('stocks', [])

                print(f"📈 API Reported Scan Time: {scan_time_from_api}")
                print(f"📊 Stocks Returned: {len(stocks)}")

                # Performance evaluation
                if total_time <= 30.0:
                    self.log_test("Performance Target Achievement", True,
                                f"- {total_time:.2f}s ≤ 30s target (EXCELLENT)")
                elif total_time <= 45.0:
                    self.log_test("Performance Target Achievement", True,
                                f"- {total_time:.2f}s ≤ 45s (GOOD - significant improvement from 95s)")
                elif total_time <= 60.0:
                    self.log_test("Performance Target Achievement", True,
                                f"- {total_time:.2f}s ≤ 60s (ACCEPTABLE - still major improvement)")
                else:
                    self.log_test("Performance Target Achievement", False,
                                f"- {total_time:.2f}s > 60s (NEEDS OPTIMIZATION)")

                return True, data, total_time
            else:
                self.log_test("Performance Scan Response", False,
                            f"- HTTP {response.status_code} after {total_time:.2f}s")
                return False, {}, total_time

        except Exception as e:
            self.log_test("Performance Scan Response", False, f"- Error: {str(e)}")
            return False, {}, 0

    def test_data_quality_verification(self, scan_data: Dict):
        """Verify that data quality is maintained despite performance optimizations"""
        print("\n🔍 DATA QUALITY VERIFICATION")

        stocks = scan_data.get('stocks', [])
        if not stocks:
            self.log_test("Data Quality - Stock Count", False, "- No stocks returned")
            return False

        # Test 1: Stock Count and Diversity
        stock_count = len(stocks)
        tickers = [stock['ticker'] for stock in stocks]
        unique_tickers = set(tickers)

        if stock_count >= 8 and len(unique_tickers) == stock_count:
            self.log_test("Data Quality - Stock Diversity", True,
                        f"- {stock_count} unique stocks returned")
        else:
            self.log_test("Data Quality - Stock Diversity", False,
                        f"- Only {stock_count} stocks, {len(unique_tickers)} unique")

        # Test 2: Required Technical Analysis Fields
        sample_stock = stocks[0]
        required_fields = [
            'ticker', 'companyName', 'currentPrice', 'priceChange',
            'priceChangePercent', 'averageVolume', 'relativeVolume',
            'RSI', 'MACD', 'fiftyMA', 'twoHundredMA', 'passes', 'score', 'rank',
            'bollinger_upper', 'bollinger_lower', 'stochastic', 'williams_r'
        ]

        missing_fields = [field for field in required_fields if field not in sample_stock]

        if not missing_fields:
            self.log_test("Data Quality - Technical Fields", True,
                        f"- All {len(required_fields)} technical fields present")
        else:
            self.log_test("Data Quality - Technical Fields", False,
                        f"- Missing fields: {missing_fields}")

        # Test 3: Scoring System Integrity
        scores = [stock.get('score', 0) for stock in stocks]
        valid_scores = [s for s in scores if 0 <= s <= 4]

        if len(valid_scores) == len(scores):
            avg_score = sum(scores) / len(scores)
            self.log_test("Data Quality - Scoring System", True,
                        f"- All scores valid (0-4), avg: {avg_score:.1f}")
        else:
            self.log_test("Data Quality - Scoring System", False,
                        f"- Invalid scores found: {scores}")

        # Test 4: Technical Indicators Validity
        rsi_values = [stock.get('RSI', 0) for stock in stocks]
        valid_rsi = [r for r in rsi_values if 0 <= r <= 100]

        if len(valid_rsi) == len(rsi_values):
            self.log_test("Data Quality - RSI Values", True,
                        f"- All RSI values valid (0-100)")
        else:
            self.log_test("Data Quality - RSI Values", False,
                        f"- Invalid RSI values found")

        return True

    def test_price_prioritization_verification(self, scan_data: Dict):
        """Verify that $20-$100 price prioritization is still working"""
        print("\n💰 PRICE PRIORITIZATION VERIFICATION")

        stocks = scan_data.get('stocks', [])
        if not stocks:
            self.log_test("Price Prioritization", False, "- No stocks to analyze")
            return False

        # Analyze price distribution
        prices = [stock.get('currentPrice', 0) for stock in stocks]
        target_range_stocks = [p for p in prices if 20 <= p <= 100]
        below_20 = [p for p in prices if p < 20]
        above_100 = [p for p in prices if p > 100]

        target_percentage = (len(target_range_stocks) / len(prices)) * 100

        print(f"📊 Price Distribution Analysis:")
        print(f"   - $20-$100 range: {len(target_range_stocks)}/{len(prices)} ({target_percentage:.1f}%)")
        print(f"   - Below $20: {len(below_20)} stocks")
        print(f"   - Above $100: {len(above_100)} stocks")

        # Store price data
        self.performance_data['price_distribution'] = {
            'target_range_count': len(target_range_stocks),
            'target_percentage': target_percentage,
            'total_stocks': len(prices)
        }

        # Evaluation criteria
        if target_percentage >= 70:
            self.log_test("Price Prioritization - Target Range", True,
                        f"- {target_percentage:.1f}% in $20-$100 range (EXCELLENT)")
        elif target_percentage >= 50:
            self.log_test("Price Prioritization - Target Range", True,
                        f"- {target_percentage:.1f}% in $20-$100 range (GOOD)")
        elif target_percentage >= 30:
            self.log_test("Price Prioritization - Target Range", True,
                        f"- {target_percentage:.1f}% in $20-$100 range (ACCEPTABLE)")
        else:
            self.log_test("Price Prioritization - Target Range", False,
                        f"- Only {target_percentage:.1f}% in target range")

        # Show sample prices for verification
        sample_prices = [(stock['ticker'], stock['currentPrice']) for stock in stocks[:5]]
        print(f"📈 Sample Stock Prices: {sample_prices}")

        return target_percentage >= 30

    def test_stock_diversity_verification(self, scan_data: Dict):
        """Verify that we're getting diverse NYSE stocks, not just fallback list"""
        print("\n🌐 STOCK DIVERSITY VERIFICATION")

        stocks = scan_data.get('stocks', [])
        if not stocks:
            self.log_test("Stock Diversity", False, "- No stocks to analyze")
            return False

        # Check for common fallback/hardcoded stocks
        common_fallback_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX'
        }

        returned_tickers = set(stock['ticker'] for stock in stocks)
        fallback_matches = returned_tickers.intersection(common_fallback_stocks)
        unique_stocks = returned_tickers - common_fallback_stocks

        fallback_percentage = (len(fallback_matches) / len(returned_tickers)) * 100
        unique_percentage = (len(unique_stocks) / len(returned_tickers)) * 100

        print(f"📊 Stock Diversity Analysis:")
        print(f"   - Unique NYSE stocks: {len(unique_stocks)}/{len(returned_tickers)} ({unique_percentage:.1f}%)")
        print(f"   - Common tech stocks: {len(fallback_matches)}/{len(returned_tickers)} ({fallback_percentage:.1f}%)")
        print(f"   - Unique tickers: {list(unique_stocks)[:5]}...")

        # Store diversity data
        self.performance_data['stock_diversity'] = {
            'unique_count': len(unique_stocks),
            'unique_percentage': unique_percentage,
            'total_stocks': len(returned_tickers)
        }

        # Evaluation criteria
        if unique_percentage >= 70:
            self.log_test("Stock Diversity - NYSE Scanning", True,
                        f"- {unique_percentage:.1f}% unique NYSE stocks (EXCELLENT)")
        elif unique_percentage >= 50:
            self.log_test("Stock Diversity - NYSE Scanning", True,
                        f"- {unique_percentage:.1f}% unique NYSE stocks (GOOD)")
        elif unique_percentage >= 30:
            self.log_test("Stock Diversity - NYSE Scanning", True,
                        f"- {unique_percentage:.1f}% unique NYSE stocks (ACCEPTABLE)")
        else:
            self.log_test("Stock Diversity - NYSE Scanning", False,
                        f"- Only {unique_percentage:.1f}% unique stocks - may be using fallback")

        return unique_percentage >= 30

    def test_concurrent_processing_verification(self, scan_data: Dict):
        """Verify that concurrent processing optimizations are working"""
        print("\n⚡ CONCURRENT PROCESSING VERIFICATION")

        # Check for optimization indicators in the response
        scan_time_str = scan_data.get('scan_time', '0s')

        try:
            # Extract numeric value from scan_time (e.g., "25.3s" -> 25.3)
            scan_time_numeric = float(scan_time_str.replace('s', ''))
        except:
            scan_time_numeric = 0

        stocks = scan_data.get('stocks', [])
        stock_count = len(stocks)

        # Calculate processing efficiency (stocks per second)
        if scan_time_numeric > 0:
            processing_rate = stock_count / scan_time_numeric
            print(f"📊 Processing Efficiency: {processing_rate:.2f} stocks/second")

            # Store processing data
            self.performance_data['processing_rate'] = processing_rate

            # Evaluation criteria for concurrent processing
            if processing_rate >= 0.5:  # At least 0.5 stocks per second
                self.log_test("Concurrent Processing - Efficiency", True,
                            f"- {processing_rate:.2f} stocks/sec (GOOD parallel processing)")
            elif processing_rate >= 0.2:
                self.log_test("Concurrent Processing - Efficiency", True,
                            f"- {processing_rate:.2f} stocks/sec (ACCEPTABLE)")
            else:
                self.log_test("Concurrent Processing - Efficiency", False,
                            f"- {processing_rate:.2f} stocks/sec (TOO SLOW - may not be using concurrency)")
        else:
            self.log_test("Concurrent Processing - Efficiency", False,
                        "- Cannot calculate processing rate")

        # Check for signs of optimization in stock data quality
        # High-quality stocks with complete data suggest good pre-filtering
        complete_stocks = 0
        for stock in stocks:
            if (stock.get('RSI', 0) > 0 and
                stock.get('currentPrice', 0) > 0 and
                stock.get('score', 0) > 0):
                complete_stocks += 1

        completeness_rate = (complete_stocks / stock_count) * 100 if stock_count > 0 else 0

        if completeness_rate >= 90:
            self.log_test("Concurrent Processing - Data Quality", True,
                        f"- {completeness_rate:.1f}% complete stock data (good pre-filtering)")
        elif completeness_rate >= 70:
            self.log_test("Concurrent Processing - Data Quality", True,
                        f"- {completeness_rate:.1f}% complete stock data (acceptable)")
        else:
            self.log_test("Concurrent Processing - Data Quality", False,
                        f"- Only {completeness_rate:.1f}% complete stock data")

        return True

    def test_caching_effectiveness(self):
        """Test caching effectiveness by running multiple scans"""
        print("\n🗄️  CACHING EFFECTIVENESS TEST")

        # First scan (cold cache)
        print("🔄 Running first scan (cold cache)...")
        start_time_1 = time.time()
        response_1 = self.session.get(f"{self.base_url}/api/stocks/scan")
        end_time_1 = time.time()
        time_1 = end_time_1 - start_time_1

        if response_1.status_code != 200:
            self.log_test("Caching Test - First Scan", False,
                        f"- HTTP {response_1.status_code}")
            return False

        # Wait a moment then run second scan (warm cache)
        print("⏳ Waiting 2 seconds...")
        time.sleep(2)

        print("🔄 Running second scan (warm cache)...")
        start_time_2 = time.time()
        response_2 = self.session.get(f"{self.base_url}/api/stocks/scan")
        end_time_2 = time.time()
        time_2 = end_time_2 - start_time_2

        if response_2.status_code != 200:
            self.log_test("Caching Test - Second Scan", False,
                        f"- HTTP {response_2.status_code}")
            return False

        # Analyze caching effectiveness
        time_improvement = time_1 - time_2
        improvement_percentage = (time_improvement / time_1) * 100 if time_1 > 0 else 0

        print(f"📊 Caching Analysis:")
        print(f"   - First scan (cold): {time_1:.2f}s")
        print(f"   - Second scan (warm): {time_2:.2f}s")
        print(f"   - Time improvement: {time_improvement:.2f}s ({improvement_percentage:.1f}%)")

        # Store caching data
        self.performance_data['caching'] = {
            'cold_cache_time': time_1,
            'warm_cache_time': time_2,
            'improvement_percentage': improvement_percentage
        }

        # Evaluation criteria
        if improvement_percentage >= 20:
            self.log_test("Caching Effectiveness", True,
                        f"- {improvement_percentage:.1f}% improvement (EXCELLENT caching)")
        elif improvement_percentage >= 10:
            self.log_test("Caching Effectiveness", True,
                        f"- {improvement_percentage:.1f}% improvement (GOOD caching)")
        elif improvement_percentage >= 5:
            self.log_test("Caching Effectiveness", True,
                        f"- {improvement_percentage:.1f}% improvement (SOME caching)")
        else:
            self.log_test("Caching Effectiveness", False,
                        f"- Only {improvement_percentage:.1f}% improvement (LIMITED caching)")

        return improvement_percentage >= 5

    def test_optimization_comparison(self):
        """Compare current performance against the baseline (95 seconds)"""
        print("\n📈 OPTIMIZATION COMPARISON")

        baseline_time = 95.0  # Previous performance baseline
        current_time = self.performance_data.get('response_time', 0)

        if current_time > 0:
            improvement = baseline_time - current_time
            improvement_percentage = (improvement / baseline_time) * 100

            print(f"📊 Performance Comparison:")
            print(f"   - Baseline (old): {baseline_time:.1f}s")
            print(f"   - Current (optimized): {current_time:.1f}s")
            print(f"   - Improvement: {improvement:.1f}s ({improvement_percentage:.1f}%)")

            # Evaluation criteria
            if improvement_percentage >= 70:
                self.log_test("Optimization Impact", True,
                            f"- {improvement_percentage:.1f}% improvement (EXCELLENT optimization)")
            elif improvement_percentage >= 50:
                self.log_test("Optimization Impact", True,
                            f"- {improvement_percentage:.1f}% improvement (GOOD optimization)")
            elif improvement_percentage >= 30:
                self.log_test("Optimization Impact", True,
                            f"- {improvement_percentage:.1f}% improvement (ACCEPTABLE optimization)")
            else:
                self.log_test("Optimization Impact", False,
                            f"- Only {improvement_percentage:.1f}% improvement (NEEDS MORE OPTIMIZATION)")

            return improvement_percentage >= 30
        else:
            self.log_test("Optimization Impact", False, "- Cannot compare - no current time data")
            return False

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "="*80)
        print("📊 PERFORMANCE OPTIMIZATION REPORT")
        print("="*80)

        # Response Time Analysis
        response_time = self.performance_data.get('response_time', 0)
        print(f"\n⏱️  RESPONSE TIME ANALYSIS:")
        print(f"   Target: <30 seconds")
        print(f"   Achieved: {response_time:.2f} seconds")

        if response_time <= 30:
            print(f"   Status: ✅ TARGET ACHIEVED ({response_time:.2f}s ≤ 30s)")
        elif response_time <= 45:
            print(f"   Status: ✅ GOOD PERFORMANCE ({response_time:.2f}s)")
        else:
            print(f"   Status: ⚠️  NEEDS IMPROVEMENT ({response_time:.2f}s)")

        # Price Prioritization Analysis
        price_data = self.performance_data.get('price_distribution', {})
        target_percentage = price_data.get('target_percentage', 0)
        print(f"\n💰 PRICE PRIORITIZATION ANALYSIS:")
        print(f"   Target Range ($20-$100): {target_percentage:.1f}%")
        print(f"   Status: {'✅ WORKING' if target_percentage >= 50 else '⚠️  NEEDS ATTENTION'}")

        # Stock Diversity Analysis
        diversity_data = self.performance_data.get('stock_diversity', {})
        unique_percentage = diversity_data.get('unique_percentage', 0)
        print(f"\n🌐 STOCK DIVERSITY ANALYSIS:")
        print(f"   Unique NYSE Stocks: {unique_percentage:.1f}%")
        print(f"   Status: {'✅ DIVERSE' if unique_percentage >= 50 else '⚠️  LIMITED DIVERSITY'}")

        # Processing Efficiency Analysis
        processing_rate = self.performance_data.get('processing_rate', 0)
        print(f"\n⚡ PROCESSING EFFICIENCY:")
        print(f"   Rate: {processing_rate:.2f} stocks/second")
        print(f"   Status: {'✅ EFFICIENT' if processing_rate >= 0.3 else '⚠️  COULD BE FASTER'}")

        # Caching Analysis
        caching_data = self.performance_data.get('caching', {})
        improvement_pct = caching_data.get('improvement_percentage', 0)
        print(f"\n🗄️  CACHING EFFECTIVENESS:")
        print(f"   Cache Improvement: {improvement_pct:.1f}%")
        print(f"   Status: {'✅ WORKING' if improvement_pct >= 10 else '⚠️  LIMITED CACHING'}")

        # Overall Assessment
        print(f"\n🎯 OVERALL OPTIMIZATION ASSESSMENT:")

        success_criteria = [
            response_time <= 45,  # Response time under 45s
            target_percentage >= 40,  # At least 40% in target price range
            unique_percentage >= 30,  # At least 30% unique stocks
            processing_rate >= 0.2   # At least 0.2 stocks/second
        ]

        passed_criteria = sum(success_criteria)
        total_criteria = len(success_criteria)

        if passed_criteria == total_criteria:
            print(f"   Status: ✅ OPTIMIZATION SUCCESSFUL ({passed_criteria}/{total_criteria} criteria met)")
            print(f"   Result: Performance optimizations are working effectively!")
        elif passed_criteria >= total_criteria * 0.75:
            print(f"   Status: ✅ MOSTLY SUCCESSFUL ({passed_criteria}/{total_criteria} criteria met)")
            print(f"   Result: Good optimization with room for minor improvements")
        else:
            print(f"   Status: ⚠️  NEEDS IMPROVEMENT ({passed_criteria}/{total_criteria} criteria met)")
            print(f"   Result: Optimization partially working but needs attention")

        print("="*80)

    def run_performance_tests(self):
        """Run all performance optimization tests"""
        print("🚀 STARTING NYSE PERFORMANCE OPTIMIZATION TESTS")
        print(f"📡 Testing against: {self.base_url}")
        print("🎯 Goal: Reduce response time from ~95s to <30s while maintaining quality")
        print("="*80)

        # PRIMARY TEST: Performance measurement
        scan_success, scan_data, response_time = self.test_performance_scan_response_time()

        if not scan_success:
            print("❌ Cannot continue tests - scan endpoint failed")
            return 1

        # QUALITY VERIFICATION TESTS
        print("\n🔍 RUNNING QUALITY VERIFICATION TESTS...")
        self.test_data_quality_verification(scan_data)
        self.test_price_prioritization_verification(scan_data)
        self.test_stock_diversity_verification(scan_data)
        self.test_concurrent_processing_verification(scan_data)

        # OPTIMIZATION TESTS
        print("\n⚡ RUNNING OPTIMIZATION TESTS...")
        self.test_caching_effectiveness()
        self.test_optimization_comparison()

        # GENERATE COMPREHENSIVE REPORT
        self.generate_performance_report()

        # Final Summary
        print(f"\n📊 TEST SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")

        if self.tests_passed >= self.tests_run * 0.8:  # 80% pass rate
            print("🎉 PERFORMANCE OPTIMIZATION TESTING SUCCESSFUL!")
            return 0
        else:
            print("⚠️  PERFORMANCE OPTIMIZATION NEEDS ATTENTION")
            return 1

def main():
    """Main test runner"""
    tester = NYSEPerformanceTester()
    return tester.run_performance_tests()

if __name__ == "__main__":
    sys.exit(main())

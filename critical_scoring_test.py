#!/usr/bin/env python3
"""
CRITICAL SCORING PRIORITY TEST - Focused test for the 4/4 stocks priority issue
"""

import requests
import json
from datetime import datetime

class CriticalScoringTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def test_critical_scoring_priority_fix(self):
        """CRITICAL TEST: Verify 4/4 stocks are prioritized first in Shadow's Picks"""
        print("🎯 CRITICAL PRIORITY TEST: Score-Based Stock Prioritization")
        print("Testing that 4/4 scored stocks appear first, then 3/4, then lower scores")
        print("=" * 80)

        try:
            # Make scan request
            print("🔄 Making scan request to /api/stocks/scan...")
            response = self.session.get(f"{self.base_url}/api/stocks/scan", timeout=120)

            if response.status_code != 200:
                print(f"❌ CRITICAL FAILURE: Scan endpoint returned {response.status_code}")
                return False

            data = response.json()
            stocks = data.get('stocks', [])
            scan_time = data.get('scan_time', 'N/A')
            score_distribution = data.get('score_distribution', {})

            print(f"✅ Scan completed successfully in {scan_time}")
            print(f"📊 Returned {len(stocks)} stocks")
            print(f"📈 Score distribution: {score_distribution}")

            if not stocks:
                print("❌ CRITICAL FAILURE: No stocks returned")
                return False

            # Test 1: Verify response format includes required fields
            print("\n📋 TEST 1: Response Format Verification")
            if scan_time != 'N/A' and score_distribution:
                print("✅ PASS: scan_time and score_distribution included in response")
            else:
                print("❌ FAIL: Missing scan_time or score_distribution in response")
                return False

            # Test 2: Analyze score distribution
            print("\n📊 TEST 2: Score Distribution Analysis")
            score_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

            for stock in stocks:
                score = stock.get('score', 0)
                if score in score_counts:
                    score_counts[score] += 1

            total_stocks = len(stocks)
            print(f"   📈 Total stocks analyzed: {total_stocks}")
            print(f"   🏆 4/4 stocks: {score_counts[4]} ({score_counts[4]/total_stocks*100:.1f}%)")
            print(f"   🥈 3/4 stocks: {score_counts[3]} ({score_counts[3]/total_stocks*100:.1f}%)")
            print(f"   🥉 2/4 stocks: {score_counts[2]} ({score_counts[2]/total_stocks*100:.1f}%)")
            print(f"   📉 1/4 stocks: {score_counts[1]} ({score_counts[1]/total_stocks*100:.1f}%)")
            print(f"   📉 0/4 stocks: {score_counts[0]} ({score_counts[0]/total_stocks*100:.1f}%)")

            # Test 3: CRITICAL - Verify score-based prioritization
            print("\n🎯 TEST 3: CRITICAL Score-Based Prioritization")
            scores_in_order = [stock.get('score', 0) for stock in stocks]
            is_properly_sorted = all(scores_in_order[i] >= scores_in_order[i+1]
                                   for i in range(len(scores_in_order)-1))

            print(f"   📊 Stock scores in order: {scores_in_order}")

            if is_properly_sorted:
                print("✅ PASS: Stocks are properly sorted by score (highest first)")

                # Check if 4/4 stocks appear first when available
                if score_counts[4] > 0:
                    first_stock_score = stocks[0].get('score', 0)
                    if first_stock_score == 4:
                        first_stock = stocks[0]
                        print(f"🏆 EXCELLENT: 4/4 stock appears first!")
                        print(f"   Ticker: {first_stock.get('ticker')}")
                        print(f"   Price: ${first_stock.get('currentPrice', 0):.2f}")
                        print(f"   Score: {first_stock.get('score')}/4")
                    else:
                        print(f"⚠️  WARNING: 4/4 stocks exist but first stock has score {first_stock_score}")
                        return False
                else:
                    print("ℹ️  INFO: No 4/4 stocks in this scan, checking 3/4 prioritization...")
                    if score_counts[3] > 0 and stocks[0].get('score', 0) == 3:
                        print("✅ GOOD: 3/4 stock appears first (no 4/4 available)")
                    elif score_counts[3] > 0:
                        print("⚠️  WARNING: 3/4 stocks exist but not prioritized first")
                        return False
            else:
                print("❌ FAIL: Stocks are NOT properly sorted by score")
                return False

            # Test 4: Verify technical analysis integrity
            print("\n🔬 TEST 4: Technical Analysis Integrity")
            sample_stock = stocks[0]
            required_fields = ['ticker', 'currentPrice', 'RSI', 'MACD', 'score', 'passes']
            missing_fields = [field for field in required_fields if field not in sample_stock]

            if not missing_fields:
                rsi = sample_stock.get('RSI', 0)
                score = sample_stock.get('score', 0)
                passes = sample_stock.get('passes', {})

                if 0 <= rsi <= 100 and 0 <= score <= 4 and isinstance(passes, dict):
                    print(f"✅ PASS: Technical analysis intact")
                    print(f"   RSI: {rsi:.1f}")
                    print(f"   Score: {score}/4")
                    print(f"   Criteria: {len(passes)} evaluated")
                else:
                    print(f"❌ FAIL: Invalid technical data")
                    return False
            else:
                print(f"❌ FAIL: Missing technical fields: {missing_fields}")
                return False

            # Test 5: User requirement compliance assessment
            print("\n🎯 TEST 5: User Requirement Compliance")
            print("User requirement: 'The scans number 1 priority above all else should be sending 4/4 stocks then 3/4 if there are no more 4/4'")

            avg_score = sum(stock.get('score', 0) for stock in stocks) / len(stocks)
            high_score_count = sum(1 for stock in stocks if stock.get('score', 0) >= 3)
            high_score_percentage = high_score_count / len(stocks) * 100

            print(f"   📊 Average score: {avg_score:.2f}/4")
            print(f"   📈 High-scoring stocks (3/4 or 4/4): {high_score_count}/{len(stocks)} ({high_score_percentage:.1f}%)")

            # Success criteria: proper sorting + reasonable score quality
            if is_properly_sorted and avg_score >= 1.5:
                print("\n🎉 CRITICAL TEST RESULT: SCORING PRIORITY FIX IS WORKING!")
                print("   ✅ Stocks are properly sorted by score (4/4 first, then 3/4, etc.)")
                print("   ✅ Technical analysis remains intact")
                print("   ✅ Response includes scan_time and score_distribution")
                print("   ✅ User requirement is being met")

                # Show top 3 stocks as examples
                print("\n🏆 TOP 3 STOCKS (showing prioritization):")
                for i, stock in enumerate(stocks[:3]):
                    print(f"   {i+1}. {stock.get('ticker')} - ${stock.get('currentPrice', 0):.2f} - Score: {stock.get('score')}/4")

                return True
            else:
                print("\n❌ CRITICAL TEST RESULT: SCORING PRIORITY FIX NEEDS ATTENTION!")
                print(f"   Properly sorted: {is_properly_sorted}")
                print(f"   Average score: {avg_score:.2f}/4 (should be reasonable)")
                return False

        except Exception as e:
            print(f"\n❌ CRITICAL TEST FAILED: {str(e)}")
            return False

def main():
    """Run the critical scoring priority test"""
    tester = CriticalScoringTester()
    success = tester.test_critical_scoring_priority_fix()

    if success:
        print("\n" + "=" * 80)
        print("🎉 CRITICAL TEST PASSED: Scoring priority fix is working correctly!")
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ CRITICAL TEST FAILED: Scoring priority fix needs attention!")
        return 1

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
SHADOWBETA PERFORMANCE TEST SUITE
Tests all optimized endpoints for load times and validates improvements
"""

import asyncio
import aiohttp
import time
import json
import statistics
from datetime import datetime
import sys

class PerformanceTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {}

    async def test_endpoint(self, session, endpoint, name, iterations=5):
        """Test a single endpoint multiple times and collect metrics"""
        print(f"🧪 Testing {name}...")
        times = []

        for i in range(iterations):
            start = time.time()
            try:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        end = time.time()
                        response_time = (end - start) * 1000  # Convert to ms
                        times.append(response_time)

                        # Validate response structure
                        if i == 0:  # Only validate first response
                            await self.validate_response(endpoint, data)

                        print(f"  ✅ Attempt {i+1}: {response_time:.1f}ms")
                    else:
                        print(f"  ❌ Attempt {i+1}: HTTP {response.status}")
                        return None
            except Exception as e:
                print(f"  ❌ Attempt {i+1}: Error - {e}")
                return None

        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)

            result = {
                "average": avg_time,
                "min": min_time,
                "max": max_time,
                "samples": len(times),
                "all_times": times
            }

            print(f"  📊 {name}: Avg={avg_time:.1f}ms, Min={min_time:.1f}ms, Max={max_time:.1f}ms")
            return result

        return None

    async def validate_response(self, endpoint, data):
        """Validate response structure for different endpoints"""
        if "/instant" in endpoint:
            if "stocks" in endpoint:
                assert "stocks" in data, f"Missing 'stocks' in {endpoint}"
                assert "metadata" in data, f"Missing 'metadata' in {endpoint}"
                assert isinstance(data["stocks"], list), f"'stocks' not a list in {endpoint}"
                if data["stocks"]:
                    stock = data["stocks"][0]
                    required_fields = ["ticker", "companyName", "currentPrice", "score"]
                    for field in required_fields:
                        assert field in stock, f"Missing '{field}' in stock data from {endpoint}"

            elif "market" in endpoint:
                assert "indices" in data, f"Missing 'indices' in {endpoint}"
                assert "gainers" in data, f"Missing 'gainers' in {endpoint}"
                assert "losers" in data, f"Missing 'losers' in {endpoint}"

            elif "news" in endpoint:
                assert "news" in data, f"Missing 'news' in {endpoint}"
                assert isinstance(data["news"], list), f"'news' not a list in {endpoint}"

        print(f"  ✅ Response validation passed for {endpoint}")

    async def run_comprehensive_test(self):
        """Run comprehensive performance tests on all optimized endpoints"""
        print("🚀 SHADOWBETA PERFORMANCE TEST SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test endpoints in order of importance
        test_endpoints = [
            ("/api/stocks/scan/instant", "Stock Scanner (Instant)", 10),
            ("/api/market/overview/instant", "Market Overview (Instant)", 10),
            ("/api/news/general/instant", "News Feed (Instant)", 5),
            ("/api/stocks/scan/fast", "Stock Scanner (Fast)", 5),
            ("/api/stocks/scan", "Stock Scanner (Full)", 3),
            ("/api/market/overview", "Market Overview (Full)", 3),
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint, name, iterations in test_endpoints:
                result = await self.test_endpoint(session, endpoint, name, iterations)
                if result:
                    self.results[name] = result
                print()

        await self.generate_report()

    async def generate_report(self):
        """Generate comprehensive performance report"""
        print("📊 PERFORMANCE REPORT")
        print("=" * 60)

        # Performance targets
        targets = {
            "Stock Scanner (Instant)": 100,  # 100ms target
            "Market Overview (Instant)": 100,
            "News Feed (Instant)": 100,
            "Stock Scanner (Fast)": 2000,   # 2s target
            "Stock Scanner (Full)": 30000,  # 30s target
            "Market Overview (Full)": 5000, # 5s target
        }

        all_passed = True

        for name, result in self.results.items():
            target = targets.get(name, 1000)
            avg_time = result["average"]
            status = "✅ PASS" if avg_time <= target else "❌ FAIL"

            if avg_time > target:
                all_passed = False

            print(f"{name}:")
            print(f"  Average: {avg_time:.1f}ms (Target: {target}ms) {status}")
            print(f"  Range: {result['min']:.1f}ms - {result['max']:.1f}ms")
            print(f"  Samples: {result['samples']}")
            print()

        # Overall assessment
        print("🎯 OVERALL PERFORMANCE ASSESSMENT")
        print("=" * 60)

        instant_endpoints = [k for k in self.results.keys() if "Instant" in k]
        if instant_endpoints:
            instant_avg = statistics.mean([self.results[k]["average"] for k in instant_endpoints])
            print(f"Instant Endpoints Average: {instant_avg:.1f}ms")

            if instant_avg <= 150:
                print("🟢 EXCELLENT: Lightning-fast instant loading achieved!")
            elif instant_avg <= 500:
                print("🟡 GOOD: Fast loading, room for improvement")
            else:
                print("🔴 NEEDS WORK: Instant endpoints too slow")

        if all_passed:
            print("🎉 ALL PERFORMANCE TARGETS MET!")
        else:
            print("⚠️  Some endpoints need optimization")

        # Save detailed results
        with open(f"performance_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "results": self.results,
                "targets": targets,
                "all_passed": all_passed
            }, f, indent=2)

        print(f"\n📁 Detailed results saved to performance_results_*.json")

async def main():
    """Main test runner"""
    base_url = "http://localhost:8000"

    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    tester = PerformanceTester(base_url)

    try:
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

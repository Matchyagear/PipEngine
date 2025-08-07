#!/usr/bin/env python3
"""
Simple test script to check if ShadowBeta backend is working
"""

import requests
import time
import json

def test_backend():
    print("🔍 Testing ShadowBeta Backend...")
    print("=" * 50)

    # Test basic connectivity
    try:
        print("1. Testing basic connectivity...")
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"   ✅ Backend is responding: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Backend is not running on port 8000")
        print("   💡 Make sure to start the backend first: cd backend && python server.py")
        return False
    except Exception as e:
        print(f"   ❌ Error connecting to backend: {e}")
        return False

    # Test stock scan endpoint
    try:
        print("\n2. Testing stock scan endpoint...")
        print("   ⏳ This may take 10-15 seconds for initial data...")
        response = requests.get("http://localhost:8000/api/stocks/scan", timeout=30)

        if response.status_code == 200:
            data = response.json()
            stocks = data.get('stocks', [])
            print(f"   ✅ Stock scan successful: {len(stocks)} stocks found")

            if stocks:
                print("   📊 Sample stocks:")
                for i, stock in enumerate(stocks[:3]):
                    print(f"      {i+1}. {stock.get('ticker', 'N/A')} - ${stock.get('currentPrice', 0):.2f} (Score: {stock.get('score', 0)}/4)")
            else:
                print("   ⚠️  No stocks returned - this might be normal for first run")
        else:
            print(f"   ❌ Stock scan failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")

    except requests.exceptions.Timeout:
        print("   ⏰ Request timed out - backend might be processing")
        print("   💡 Try again in a few seconds")
    except Exception as e:
        print(f"   ❌ Error testing stock scan: {e}")

    # Test market overview
    try:
        print("\n3. Testing market overview...")
        response = requests.get("http://localhost:8000/api/market/overview", timeout=10)

        if response.status_code == 200:
            data = response.json()
            indices = data.get('indices', [])
            print(f"   ✅ Market overview successful: {len(indices)} indices found")
        else:
            print(f"   ❌ Market overview failed: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Error testing market overview: {e}")

    print("\n" + "=" * 50)
    print("🎯 Backend Test Complete!")
    print("\n💡 If you see errors above:")
    print("   1. Make sure MongoDB is running (if using local MongoDB)")
    print("   2. Check that all API keys are set in backend/.env")
    print("   3. Try running: cd backend && python server.py")
    print("\n🌐 Frontend should be available at: http://localhost:3000")

    return True

if __name__ == "__main__":
    test_backend()

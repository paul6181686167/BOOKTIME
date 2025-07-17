#!/usr/bin/env python3
"""
Test suite for BOOKTIME Series functionality after Ultra Harvest 100k
Testing the addition of 160 new series and the expanded database of 10,603 series
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://db3c8666-cd4a-47d7-a8e7-dde05cbd05aa.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class SeriesHarvestTest:
    def __init__(self):
        self.test_user_data = {
            "first_name": "SeriesTest",
            "last_name": "User",
            "password": "testpass123"
        }
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.cleanup_ids = []

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("🔐 Setting up authentication...")
        
        # Register test user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        if response.status_code == 200:
            user_data = response.json()
            self.token = user_data["access_token"]  # Fixed: use access_token instead of token
            self.headers['Authorization'] = f'Bearer {self.token}'
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False

    def test_health_check(self):
        """Test basic connectivity"""
        print("\n🔍 Testing basic connectivity...")
        
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("database") == "connected":
                    print("✅ Health check passed - Database connected")
                    return True
            print(f"❌ Health check failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def test_series_database_capacity(self):
        """Test 1: Verify system can handle 10,603 series"""
        print("\n📊 Test 1: Testing series database capacity (10,603 series)...")
        
        try:
            # Test series stats endpoint
            start_time = time.time()
            response = requests.get(f"{API_URL}/series/stats", headers=self.headers, timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                stats = response.json()
                total_series = stats.get("total_series", 0)
                print(f"✅ Series stats loaded in {response_time:.0f}ms")
                print(f"   Total series in database: {total_series}")
                
                # Verify we have the expected number of series (around 10,603)
                if total_series >= 10000:
                    print(f"✅ Database contains {total_series} series (expected ~10,603)")
                    return True
                else:
                    print(f"⚠️  Database contains only {total_series} series (expected ~10,603)")
                    return False
            else:
                print(f"❌ Series stats failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Series database test error: {e}")
            return False

    def test_new_series_presence(self):
        """Test 2: Verify new series from Ultra Harvest are present"""
        print("\n🔍 Test 2: Testing presence of new series (CHERUB, Henderson's Boys, Red Rising)...")
        
        test_series = [
            {"name": "CHERUB", "author": "Robert Muchamore"},
            {"name": "Henderson's Boys", "author": "Robert Muchamore"},
            {"name": "Red Rising", "author": "Pierce Brown"}
        ]
        
        results = []
        for series_info in test_series:
            try:
                # Search for the series
                response = requests.get(
                    f"{API_URL}/series/search", 
                    params={"query": series_info["name"]},
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    search_results = response.json()
                    series_list = search_results.get("series", [])
                    
                    # Look for exact match
                    found = False
                    for series in series_list:
                        if (series_info["name"].lower() in series.get("name", "").lower() and
                            series_info["author"].lower() in [author.lower() for author in series.get("authors", [])]):
                            found = True
                            print(f"✅ Found '{series_info['name']}' by {series_info['author']}")
                            print(f"   Series details: {series.get('name')} - {series.get('category')} - {series.get('volumes')} volumes")
                            break
                    
                    if not found:
                        print(f"❌ '{series_info['name']}' by {series_info['author']} not found")
                    
                    results.append(found)
                else:
                    print(f"❌ Search failed for '{series_info['name']}': {response.status_code}")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ Error searching for '{series_info['name']}': {e}")
                results.append(False)
        
        success_rate = sum(results) / len(results)
        print(f"\n📈 New series detection rate: {success_rate*100:.0f}% ({sum(results)}/{len(results)})")
        return success_rate >= 0.67  # At least 2/3 should be found

    def test_series_search_api(self):
        """Test 3: Test series search API with new series"""
        print("\n🔎 Test 3: Testing series search API...")
        
        search_queries = ["CHERUB", "Red Rising", "Henderson", "Harry Potter"]
        
        all_passed = True
        for query in search_queries:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{API_URL}/series/search",
                    params={"query": query},
                    headers=self.headers,
                    timeout=15
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    series_count = len(data.get("series", []))
                    total_found = data.get("total", 0)
                    
                    print(f"✅ Search '{query}': {series_count} series returned in {response_time:.0f}ms (total: {total_found})")
                    
                    # Verify response structure
                    if "series" in data and "total" in data and "search_term" in data:
                        print(f"   Response structure valid")
                    else:
                        print(f"   ⚠️  Response structure incomplete")
                        all_passed = False
                        
                else:
                    print(f"❌ Search '{query}' failed: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ Search '{query}' error: {e}")
                all_passed = False
        
        return all_passed

    def test_series_detection_api(self):
        """Test 4: Test series detection API"""
        print("\n🎯 Test 4: Testing series detection API...")
        
        detection_tests = [
            {"title": "CHERUB Class A", "expected_series": "CHERUB"},
            {"title": "Red Rising Book 1", "expected_series": "Red Rising"},
            {"title": "Harry Potter à l'école des sorciers", "expected_series": "Harry Potter"}
        ]
        
        all_passed = True
        for test in detection_tests:
            try:
                start_time = time.time()
                response = requests.get(
                    f"{API_URL}/series/detection",
                    params={"title": test["title"]},
                    headers=self.headers,
                    timeout=15
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    detected = data.get("detected", False)
                    series_name = data.get("series_name", "")
                    confidence = data.get("confidence", 0)
                    
                    print(f"✅ Detection '{test['title']}': {response_time:.0f}ms")
                    print(f"   Detected: {detected}, Series: {series_name}, Confidence: {confidence}")
                    
                    if detected and confidence > 100:
                        print(f"   ✅ High confidence detection")
                    else:
                        print(f"   ⚠️  Low confidence or not detected")
                        
                else:
                    print(f"❌ Detection '{test['title']}' failed: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ Detection '{test['title']}' error: {e}")
                all_passed = False
        
        return all_passed

    def test_series_endpoints(self):
        """Test 5: Test all main series endpoints"""
        print("\n🔗 Test 5: Testing main series endpoints...")
        
        endpoints = [
            {"url": f"{API_URL}/series/", "name": "Series list"},
            {"url": f"{API_URL}/series/popular", "name": "Popular series"},
            {"url": f"{API_URL}/series/stats", "name": "Series statistics"}
        ]
        
        all_passed = True
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint["url"], headers=self.headers, timeout=15)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint['name']}: {response_time:.0f}ms - Response received")
                    
                    # Basic structure validation
                    if isinstance(data, (list, dict)):
                        print(f"   Valid JSON structure")
                    else:
                        print(f"   ⚠️  Invalid JSON structure")
                        all_passed = False
                        
                else:
                    print(f"❌ {endpoint['name']} failed: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ {endpoint['name']} error: {e}")
                all_passed = False
        
        return all_passed

    def test_batch_detection(self):
        """Test 6: Test batch series detection"""
        print("\n📦 Test 6: Testing batch series detection...")
        
        batch_titles = [
            "CHERUB Class A",
            "Red Rising Book 1", 
            "Harry Potter à l'école des sorciers",
            "One Piece Tome 1",
            "Astérix le Gaulois"
        ]
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_URL}/series/batch-detect",
                json={"titles": batch_titles},
                headers=self.headers,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                print(f"✅ Batch detection completed in {response_time:.0f}ms")
                print(f"   Processed {len(results)} titles")
                
                detected_count = sum(1 for r in results if r.get("detected", False))
                print(f"   Detection rate: {detected_count}/{len(results)} ({detected_count/len(results)*100:.0f}%)")
                
                # Show individual results
                for i, result in enumerate(results):
                    title = batch_titles[i] if i < len(batch_titles) else f"Title {i+1}"
                    detected = result.get("detected", False)
                    series_name = result.get("series_name", "N/A")
                    confidence = result.get("confidence", 0)
                    print(f"   {title}: {'✅' if detected else '❌'} {series_name} (confidence: {confidence})")
                
                return detected_count >= len(batch_titles) * 0.6  # At least 60% detection rate
                
            else:
                print(f"❌ Batch detection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Batch detection error: {e}")
            return False

    def test_performance(self):
        """Test 7: Test performance with large database"""
        print("\n⚡ Test 7: Testing performance with 10,603 series...")
        
        performance_tests = [
            {"name": "Series search", "url": f"{API_URL}/series/search", "params": {"query": "Harry"}},
            {"name": "Popular series", "url": f"{API_URL}/series/popular", "params": {}},
            {"name": "Series stats", "url": f"{API_URL}/series/stats", "params": {}}
        ]
        
        all_passed = True
        total_time = 0
        
        for test in performance_tests:
            try:
                # Run test 3 times and take average
                times = []
                for i in range(3):
                    start_time = time.time()
                    response = requests.get(
                        test["url"], 
                        params=test["params"],
                        headers=self.headers,
                        timeout=20
                    )
                    response_time = (time.time() - start_time) * 1000
                    times.append(response_time)
                    
                    if response.status_code != 200:
                        print(f"❌ {test['name']} failed: {response.status_code}")
                        all_passed = False
                        break
                
                if response.status_code == 200:
                    avg_time = sum(times) / len(times)
                    total_time += avg_time
                    
                    print(f"✅ {test['name']}: {avg_time:.0f}ms average")
                    
                    # Performance threshold: should be under 5 seconds
                    if avg_time > 5000:
                        print(f"   ⚠️  Performance warning: {avg_time:.0f}ms > 5000ms")
                        all_passed = False
                    else:
                        print(f"   ✅ Performance acceptable")
                        
            except Exception as e:
                print(f"❌ {test['name']} error: {e}")
                all_passed = False
        
        print(f"\n📊 Total performance time: {total_time:.0f}ms")
        return all_passed and total_time < 15000  # Total should be under 15 seconds

    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting BOOKTIME Series Ultra Harvest 100k Tests")
        print("=" * 60)
        
        # Setup
        if not self.test_health_check():
            print("❌ Health check failed - aborting tests")
            return False
            
        if not self.setup_authentication():
            print("❌ Authentication failed - aborting tests")
            return False
        
        # Run tests
        test_results = []
        
        tests = [
            ("Database Capacity (10,603 series)", self.test_series_database_capacity),
            ("New Series Presence", self.test_new_series_presence),
            ("Series Search API", self.test_series_search_api),
            ("Series Detection API", self.test_series_detection_api),
            ("Main Series Endpoints", self.test_series_endpoints),
            ("Batch Detection", self.test_batch_detection),
            ("Performance Testing", self.test_performance)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            try:
                result = test_func()
                test_results.append((test_name, result))
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"\n{status}: {test_name}")
            except Exception as e:
                print(f"\n❌ ERROR in {test_name}: {e}")
                test_results.append((test_name, False))
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        
        print(f"\n📈 Overall Result: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Ultra Harvest 100k integration successful!")
            return True
        elif passed >= total * 0.8:
            print("⚠️  MOSTLY SUCCESSFUL - Minor issues detected")
            return True
        else:
            print("❌ SIGNIFICANT ISSUES - Ultra Harvest 100k integration needs attention")
            return False

if __name__ == "__main__":
    tester = SeriesHarvestTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
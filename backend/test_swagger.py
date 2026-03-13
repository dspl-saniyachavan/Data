#!/usr/bin/env python3
"""
Test script to verify Swagger documentation is accessible
"""
import requests
import sys

def test_swagger_ui():
    """Test if Swagger UI is accessible"""
    print("Testing Swagger UI accessibility...")
    
    try:
        response = requests.get('http://localhost:5000/api/docs', timeout=5)
        
        if response.status_code == 200:
            print("✅ Swagger UI is accessible at http://localhost:5000/api/docs")
            return True
        else:
            print(f"❌ Swagger UI returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Is it running?")
        print("   Start it with: python run.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_swagger_spec():
    """Test if Swagger spec JSON is accessible"""
    print("\nTesting Swagger API spec...")
    
    try:
        response = requests.get('http://localhost:5000/apispec.json', timeout=5)
        
        if response.status_code == 200:
            spec = response.json()
            print("✅ Swagger API spec is accessible")
            print(f"   API Title: {spec.get('info', {}).get('title', 'N/A')}")
            print(f"   API Version: {spec.get('info', {}).get('version', 'N/A')}")
            
            # Count documented endpoints
            paths = spec.get('paths', {})
            print(f"   Documented endpoints: {len(paths)}")
            
            return True
        else:
            print(f"❌ API spec returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_documented_endpoints():
    """List all documented endpoints"""
    print("\nListing documented endpoints...")
    
    try:
        response = requests.get('http://localhost:5000/apispec.json', timeout=5)
        
        if response.status_code == 200:
            spec = response.json()
            paths = spec.get('paths', {})
            
            if not paths:
                print("⚠️  No endpoints documented yet")
                return False
            
            print(f"\n📋 Found {len(paths)} documented endpoints:\n")
            
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        tags = details.get('tags', ['Untagged'])
                        summary = details.get('summary', 'No description')
                        print(f"   {method.upper():6} {path:40} [{', '.join(tags)}]")
            
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Swagger Documentation Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(test_swagger_ui())
    results.append(test_swagger_spec())
    results.append(test_documented_endpoints())
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("✅ All tests passed! Swagger is working correctly.")
        print("\n🚀 Access Swagger UI at: http://localhost:5000/api/docs")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == '__main__':
    main()

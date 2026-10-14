"""
CLI Verification Tool for External Price APIs (SerpApi & RapidAPI).
Run: python backend/test_price_api.py [query]
"""
import os
import sys

# Ensure backend path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Configure stdout encoding for Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from services.price_api import PriceAPIService

def test_api():
    query = sys.argv[1] if len(sys.argv) > 1 else "Sony WH-1000XM5"
    config = PriceAPIService.get_config()

    print("=" * 60)
    print("  External Price API Integration Diagnostic Tool")
    print("=" * 60)
    print(f"Configured Provider : {config['provider']}")
    print(f"SerpApi Key         : {'[Configured]' if config['serpapi_key'] else '[MISSING]'}")
    print(f"RapidAPI Key        : {'[Configured]' if config['rapidapi_key'] else '[MISSING]'}")
    print(f"RapidAPI Host       : {config['rapidapi_host']}")
    print(f"Target Country      : {config['country']}")
    print(f"Target Currency     : {config['currency']}")
    print(f"Test Query          : '{query}'")
    print("-" * 60)

    print("\nExecuting live API search...")
    result = PriceAPIService.fetch_product_prices(query)

    print("\nResult:")
    print(f"Success    : {result.get('success')}")
    print(f"Source     : {result.get('source')}")

    if not result.get("success"):
        print(f"Error Code : {result.get('error_code')}")
        print(f"Error      : {result.get('error')}")
    else:
        prices = result.get("prices", [])
        print(f"Stores Found: {len(prices)}")
        for idx, p in enumerate(prices[:8], 1):
            print(f"  {idx}. [{p['retailer_name']}] ₹{p['price']:,.0f} | {p['availability']} | {p['delivery']}")
            print(f"     Title : {p['product_name'][:55]}")
            print(f"     Link  : {p['product_url'][:75]}...")

    print("=" * 60)

if __name__ == "__main__":
    test_api()

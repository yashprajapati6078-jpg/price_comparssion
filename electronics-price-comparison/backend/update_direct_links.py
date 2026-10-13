import os
import sys
import re

# Configure stdout encoding for Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app, db
from models import Product, Price

def update_all_direct_links():
    """
    Updates store prices in the database to use clean direct single-product URLs (Amazon /dp/ASIN, Flipkart /p/itm, etc.).
    Extracts canonical product IDs and classifies URL types into DIRECT_PRODUCT vs SEARCH_FALLBACK.
    """
    with app.app_context():
        prices = Price.query.all()
        updated_single_count = 0
        total_count = len(prices)
        
        for pr in prices:
            resolved = pr.resolve_single_product_url()
            r_slug = (pr.retailer.slug if pr.retailer else "amazon").lower().strip()
            
            if pr.is_single_product_url(resolved):
                pr.product_url = resolved
                pr.direct_url = resolved
                pr.buy_url = resolved
                pr.url_type = "DIRECT_PRODUCT"
                
                # Extract canonical product ID
                if not pr.retailer_product_id:
                    if "amazon." in resolved:
                        m = re.search(r"/dp/([A-Z0-9]{10})", resolved)
                        if m:
                            pr.retailer_product_id = m.group(1)
                    elif "flipkart." in resolved:
                        m = re.search(r"pid=([A-Z0-9]+)", resolved) or re.search(r"/p/(itm[a-zA-Z0-9]+)", resolved)
                        if m:
                            pr.retailer_product_id = m.group(1)
                    elif "croma." in resolved:
                        m = re.search(r"/p/(\d+)", resolved)
                        if m:
                            pr.retailer_product_id = m.group(1)
                    elif "reliancedigital." in resolved:
                        m = re.search(r"/p/(\d+)", resolved)
                        if m:
                            pr.retailer_product_id = m.group(1)
                    elif "vijaysales." in resolved:
                        m = re.search(r"/(\d{4,8})(?:[/?#]|$)", resolved)
                        if m:
                            pr.retailer_product_id = m.group(1)
                
                updated_single_count += 1
            else:
                pr.url_type = "SEARCH_FALLBACK"
                if not pr.product_url:
                    pr.product_url = resolved
                if not pr.buy_url:
                    pr.buy_url = resolved
            
        db.session.commit()
        print(f"Successfully resolved {updated_single_count} / {total_count} price entries to exact single-product links!")

if __name__ == "__main__":
    update_all_direct_links()

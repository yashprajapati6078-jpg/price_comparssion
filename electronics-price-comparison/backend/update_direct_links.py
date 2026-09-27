import os
import sys

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
    """
    with app.app_context():
        prices = Price.query.all()
        updated_single_count = 0
        total_count = 0
        for pr in prices:
            total_count += 1
            resolved = pr.resolve_single_product_url()
            if pr.is_single_product_url(resolved):
                pr.buy_url = resolved
                updated_single_count += 1
            
        db.session.commit()
        print(f"Successfully resolved {updated_single_count} / {total_count} price entries to exact single-product links!")

if __name__ == "__main__":
    update_all_direct_links()

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

def populate_direct_urls():
    """
    Populates direct retailer purchase URLs for all products in the database.
    """
    with app.app_context():
        products = Product.query.all()
        print(f"Updating direct store purchase URLs for {len(products)} products...")
        
        updated_count = 0
        for prod in products:
            for pr in prod.prices:
                r_slug = pr.retailer.slug if pr.retailer else "amazon"
                direct_url = Price.generate_direct_store_url(prod.name, prod.brand, r_slug)
                pr.buy_url = direct_url
                updated_count += 1
                
        db.session.commit()
        print(f"Done! Successfully updated {updated_count} store links across {len(products)} products.")

if __name__ == "__main__":
    populate_direct_urls()

import sqlite3
import os
import sys
import urllib.parse
import re

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.asin_resolver import resolve_canonical_single_url
from models import Price

db_path = os.path.join(backend_dir, 'electronics.db')
con = sqlite3.connect(db_path, timeout=30)
cur = con.cursor()

cur.execute("PRAGMA journal_mode=WAL;")
cur.execute("PRAGMA busy_timeout=30000;")

cur.execute("""
    SELECT p.id, pr.name, pr.brand, r.slug
    FROM prices p
    JOIN products pr ON p.product_id = pr.id
    JOIN retailers r ON p.retailer_id = r.id
""")
rows = cur.fetchall()

dummy_price = Price()

updated_count = 0
croma_updated = 0
vijay_updated = 0

for p_id, p_name, p_brand, r_slug in rows:
    # 1. Check Canonical Resolver
    resolved = resolve_canonical_single_url(p_name, p_brand, r_slug)
    
    if resolved:
        final_url = resolved
    else:
        final_url = Price.generate_direct_store_url(p_name, p_brand, r_slug)
        
    url_type = "DIRECT_PRODUCT" if dummy_price.is_single_product_url(final_url) else "SEARCH_FALLBACK"
    
    cur.execute("""
        UPDATE prices
        SET product_url = ?, direct_url = ?, buy_url = ?, url_type = ?
        WHERE id = ?
    """, (final_url, final_url, final_url, url_type, p_id))
    
    updated_count += 1
    if r_slug == "croma":
        croma_updated += 1
    elif r_slug == "vijaysales":
        vijay_updated += 1

con.commit()
con.close()

print(f"Migration successful!")
print(f"Total prices updated: {updated_count}")
print(f"Croma prices updated: {croma_updated}")
print(f"Vijay Sales prices updated: {vijay_updated}")

"""
Cleanup script to purge refurbished and mismatched product prices,
restore genuine catalog prices for affected products,
and upgrade retailer badge color styles.
"""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

backend_dir = os.path.abspath(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app
from models import db, Product, Price, PriceHistory, Retailer
from services.price_api import PriceAPIService
import catalog_data

def run_cleanup():
    with app.app_context():
        print("--- Starting Retailer Badge & Price Cleanup ---")
        
        ALLOWED_RETAILER_SLUGS = {"amazon", "flipkart", "croma", "reliance", "vijaysales"}

        # 1. Purge non-famous retailers from DB
        stale_retailers = Retailer.query.filter(~Retailer.slug.in_(ALLOWED_RETAILER_SLUGS)).all()
        for sr in stale_retailers:
            print(f"Purging unsupported retailer: {sr.name} ({sr.slug})")
            PriceHistory.query.filter_by(retailer_id=sr.id).delete()
            Price.query.filter_by(retailer_id=sr.id).delete()
            db.session.delete(sr)
        db.session.commit()

        # 2. Update remaining 5 Retailer badges to modern styles
        retailers = Retailer.query.filter(Retailer.slug.in_(ALLOWED_RETAILER_SLUGS)).all()
        for r in retailers:
            new_badge = PriceAPIService.get_retailer_badge_style(r.slug, r.name)
            if r.badge_bg != new_badge:
                print(f"Updating retailer '{r.name}' badge: {r.badge_bg} -> {new_badge}")
                r.badge_bg = new_badge
        db.session.commit()
        print(f"Updated badges for {len(retailers)} retailers.")

        # 3. Check and purge refurbished, mismatched, or non-allowed prices
        catalog_products_by_name = {p["name"]: p for p in catalog_data.CURATED_PRODUCTS}
        purged_count = 0

        for product in Product.query.all():
            ref_price = product.original_price or 0
            cat_entry = catalog_products_by_name.get(product.name)

            prices = Price.query.filter_by(product_id=product.id).all()
            for pr in prices:
                retailer_slug = pr.retailer.slug if pr.retailer else ""
                retailer_name = pr.retailer.name if pr.retailer else ""
                buy_url = (pr.buy_url or "").lower()

                should_delete = False
                reason = ""

                # Condition 0: Not one of the 5 famous retailers
                if retailer_slug not in ALLOWED_RETAILER_SLUGS:
                    should_delete = True
                    reason = f"Not a famous retailer ({retailer_name} / {retailer_slug})"

                # Condition A: Refurbished retailer
                elif PriceAPIService.is_refurbished_store(retailer_slug, retailer_name):
                    should_delete = True
                    reason = f"Refurbished store ({retailer_name})"

                # Condition B: Refurbished keyword in buy_url
                elif any(r_kw in buy_url for r_kw in ["refurbished", "pre-owned", "preowned", "second-hand", "fair+condition", "like-new", "used"]):
                    should_delete = True
                    reason = "Refurbished URL keyword"

                # Condition C: Extreme price anomaly for premium items
                elif ref_price > 5000 and pr.price < (ref_price * (0.55 if ref_price >= 15000 else 0.40)):
                    should_delete = True
                    reason = f"Price anomaly (Rs.{pr.price:,.0f} vs MSRP Rs.{ref_price:,.0f})"

                if should_delete:
                    print(f"  [PURGE] Product #{product.id} '{product.name[:35]}' | Store: {retailer_name} | Price: Rs.{pr.price:,.0f} | Reason: {reason}")
                    PriceHistory.query.filter_by(product_id=product.id, retailer_id=pr.retailer_id).delete()
                    db.session.delete(pr)
                    purged_count += 1

            db.session.flush()

            # Ensure legitimate primary catalog retailer prices exist
            if cat_entry and "prices" in cat_entry:
                retailers_by_slug = {r.slug: r for r in Retailer.query.all()}
                for item in cat_entry["prices"]:
                    r_slug = item["retailer"]
                    r_obj = retailers_by_slug.get(r_slug)
                    if not r_obj:
                        continue
                    existing_pr = Price.query.filter_by(product_id=product.id, retailer_id=r_obj.id).first()
                    if not existing_pr:
                        print(f"  [RESTORE] Restoring {r_obj.name} (Rs.{item['price']:,.0f}) for Product #{product.id}")
                        new_pr = Price(
                            product_id=product.id,
                            retailer_id=r_obj.id,
                            price=float(item["price"]),
                            delivery=item.get("delivery", "Standard Delivery"),
                            availability="In Stock",
                            rating=4.7,
                            buy_url=f"https://www.{r_slug}.in" if r_slug != "croma" else "https://www.croma.com"
                        )
                        db.session.add(new_pr)
                        db.session.add(PriceHistory(
                            product_id=product.id,
                            retailer_id=r_obj.id,
                            price=float(item["price"])
                        ))

            # Recalculate lowest price
            product.recalculate_lowest_price()

        db.session.commit()
        print(f"\n--- Cleanup Complete! Purged {purged_count} invalid price entries. ---")

if __name__ == "__main__":
    run_cleanup()

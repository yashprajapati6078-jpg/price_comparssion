import random
import logging
from datetime import datetime, timedelta
from rapidfuzz import fuzz, process
import requests
from bs4 import BeautifulSoup
from models import db, Product, Price, PriceHistory, PriceAlert, Retailer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PriceScraper")

class PriceScraperEngine:
    @staticmethod
    def fuzzy_search_products(query, products, score_cutoff=50):
        """
        Uses RapidFuzz to match user query against product names and brands.
        Returns a list of matching products sorted by match score.
        """
        if not query or not products:
            return products

        product_names = [f"{p.brand} {p.name}" for p in products]
        results = process.extract(query, product_names, scorer=fuzz.token_set_ratio, limit=len(products))
        
        matched_products = []
        for match in results:
            text, score, index = match[0], match[1], match[2]
            if score >= score_cutoff:
                matched_products.append(products[index])
        
        return matched_products if matched_products else products

    @staticmethod
    def scrape_and_update_product(product, db_session):
        """
        Fetches live retailer prices for a specific product from external Price API.
        Extracts multi-retailer prices, updates database models, and checks alert thresholds.
        """
        from services.price_api import PriceAPIService
        
        query = Price.clean_product_query(product.name, product.brand)
        logger.info(f"Querying external Price API for product: {product.name} (ID: {product.id}) with query: '{query}'")
        
        api_result = PriceAPIService.fetch_product_prices(query)
        if not api_result.get("success"):
            logger.warning(f"Price API update aborted for '{product.name}': {api_result.get('error')}")
            return {
                "success": False,
                "error": api_result.get("error"),
                "error_code": api_result.get("error_code"),
                "source": api_result.get("source"),
                "prices_updated": 0
            }

        extracted_prices = api_result.get("prices", [])
        if not extracted_prices:
            return {
                "success": False,
                "error": "No valid prices returned by the external API.",
                "error_code": "MISSING_PRICE",
                "source": api_result.get("source"),
                "prices_updated": 0
            }

        now = datetime.utcnow()
        prices_updated = 0
        ALLOWED_RETAILERS = {"amazon", "flipkart", "croma", "reliance", "vijaysales"}
        all_retailers = {r.slug: r for r in Retailer.query.filter(Retailer.slug.in_(ALLOWED_RETAILERS)).all()}
        all_retailers_by_name = {r.name.lower(): r for r in all_retailers.values()}

        for item in extracted_prices:
            r_slug = item.get("retailer_slug", "store")
            r_name = item.get("retailer_name", "Online Store")
            if r_slug not in ALLOWED_RETAILERS:
                continue

            new_price = item.get("price")
            if not new_price or new_price <= 0:
                continue

            # Anomaly check: Reject accessory prices disguised as main product or mismatched cheaper variants
            ref_price = product.original_price or product.lowest_price or 0
            min_ratio = 0.55 if ref_price >= 15000 else 0.40
            if ref_price > 3000 and new_price < (ref_price * min_ratio):
                logger.info(f"Skipping price anomaly ₹{new_price} for product '{product.name}' (MSRP: ₹{ref_price}, min valid: ₹{ref_price * min_ratio:.0f})")
                continue

            # Find matching retailer among the 5 famous retailers
            retailer_obj = all_retailers.get(r_slug) or all_retailers_by_name.get(r_name.lower())
            if not retailer_obj:
                continue

            # Find or create Price record for this product + retailer
            price_obj = Price.query.filter_by(product_id=product.id, retailer_id=retailer_obj.id).first()
            if not price_obj:
                price_obj = Price(
                    product_id=product.id,
                    retailer_id=retailer_obj.id,
                    price=float(new_price),
                    delivery=item.get("delivery", "Standard Delivery"),
                    availability=item.get("availability", "In Stock"),
                    rating=item.get("rating") or 4.5,
                    buy_url=item.get("product_url") or "#",
                    last_updated=now
                )
                db_session.add(price_obj)
            else:
                price_obj.price = float(new_price)
                if item.get("product_url"):
                    price_obj.buy_url = item.get("product_url")
                if item.get("delivery"):
                    price_obj.delivery = item.get("delivery")
                if item.get("availability"):
                    price_obj.availability = item.get("availability")
                if item.get("rating"):
                    price_obj.rating = float(item["rating"])
                price_obj.last_updated = now

            # Record in PriceHistory
            history_entry = PriceHistory(
                product_id=product.id,
                retailer_id=retailer_obj.id,
                price=float(new_price),
                recorded_at=now
            )
            db_session.add(history_entry)
            prices_updated += 1

        # Recalculate lowest price for product
        product.recalculate_lowest_price()
        db_session.commit()

        # Check Price Alerts for this product
        PriceScraperEngine.check_price_alerts(product, db_session)

        return {
            "success": True,
            "prices_updated": prices_updated,
            "source": api_result.get("source"),
            "product_id": product.id,
            "lowest_price": product.lowest_price,
            "prices": extracted_prices
        }

    @staticmethod
    def check_price_alerts(product, db_session):
        """
        Evaluates active price alerts for the product.
        If product.lowest_price <= target_price, marks alert as triggered.
        """
        active_alerts = PriceAlert.query.filter_by(product_id=product.id, is_triggered=False).all()
        triggered_count = 0
        for alert in active_alerts:
            if product.lowest_price <= alert.target_price:
                alert.is_triggered = True
                triggered_count += 1
                logger.info(f"ALERT TRIGGERED! User ID {alert.user_id} alert for product '{product.name}' target ₹{alert.target_price} reached current price ₹{product.lowest_price}")
        if triggered_count > 0:
            db_session.commit()
        return triggered_count

    @staticmethod
    def seed_initial_price_history(product, db_session):
        """
        Generates 30-day realistic historical price data points for Chart.js graphing.
        """
        if not product.prices:
            return
        
        today = datetime.utcnow()
        base_price = product.lowest_price or product.original_price or 50000.0

        for price_obj in product.prices:
            # Check if history already exists
            existing_count = PriceHistory.query.filter_by(product_id=product.id, retailer_id=price_obj.retailer_id).count()
            if existing_count > 5:
                continue

            current_p = price_obj.price
            for days_ago in range(30, 0, -5):
                date_point = today - timedelta(days=days_ago)
                # Historical price had slight variation (+-5%)
                hist_p = round(current_p * (1 + random.uniform(-0.05, 0.05)))
                h = PriceHistory(
                    product_id=product.id,
                    retailer_id=price_obj.retailer_id,
                    price=float(hist_p),
                    recorded_at=date_point
                )
                db_session.add(h)
            
            # Add current point
            h_current = PriceHistory(
                product_id=product.id,
                retailer_id=price_obj.retailer_id,
                price=current_p,
                recorded_at=today
            )
            db_session.add(h_current)
        
        db_session.commit()

    @staticmethod
    def insert_products_batch(products_data, db_session):
        """
        Batch creates and saves products, store prices, and 30-day price history graphs.
        """
        from models import Category, Retailer, Product, Price
        import json

        categories = {c.name: c for c in Category.query.all()}
        retailers = {r.slug: r for r in Retailer.query.all()}

        inserted_count = 0
        for pdata in products_data:
            cat_obj = categories.get(pdata["category"])
            if not cat_obj:
                continue

            # Check if product with identical name already exists
            if Product.query.filter_by(name=pdata["name"]).first():
                continue

            specs_dict = pdata.get("specs", {})
            if cat_obj.name == "PC Components" and "Subcomponent" not in specs_dict:
                from catalog_data import detect_subcomponent_from_query
                subcomp = pdata.get("subcomponent") or detect_subcomponent_from_query(pdata.get("name", ""), pdata.get("name", ""))
                specs_dict["Subcomponent"] = subcomp

            p = Product(
                name=pdata["name"],
                brand=pdata["brand"],
                category_id=cat_obj.id,
                image=pdata["image"],
                gallery_json=json.dumps(pdata.get("gallery", [pdata["image"]])),
                rating=pdata.get("rating", 4.5),
                review_count=pdata.get("review_count", 150),
                original_price=pdata.get("original_price", 50000),
                is_featured=pdata.get("is_featured", False),
                is_deal=pdata.get("is_deal", False),
                colors_json=json.dumps(pdata.get("colors", ["Standard"])),
                storage_options_json=json.dumps(pdata.get("storage_options", ["Standard"])),
                description=pdata.get("description", ""),
                features_json=json.dumps(pdata.get("features", [])),
                specs_json=json.dumps(specs_dict)
            )
            db_session.add(p)
            db_session.flush()

            # Add retailer prices
            for pr in pdata.get("prices", []):
                ret_obj = retailers.get(pr["retailer"])
                if ret_obj:
                    price_entry = Price(
                        product_id=p.id,
                        retailer_id=ret_obj.id,
                        price=pr["price"],
                        delivery=pr.get("delivery", "Standard Delivery"),
                        availability="In Stock",
                        rating=4.7,
                        buy_url=ret_obj.website_url
                    )
                    db_session.add(price_entry)

            p.recalculate_lowest_price()
            db_session.commit()

            # Seed 30-day Price History
            PriceScraperEngine.seed_initial_price_history(p, db_session)
            inserted_count += 1

        return inserted_count

    @staticmethod
    def generate_and_insert_infinite_products(count=15, category_name=None, db_session=None):
        """
        Generates and persists synthetic products on demand for infinite catalog exploration.
        """
        from catalog_data import generate_synthetic_catalog_batch
        new_items = generate_synthetic_catalog_batch(category_name=category_name, count=count)
        return PriceScraperEngine.insert_products_batch(new_items, db_session)

    @staticmethod
    def sync_live_prices(product, db_session):
        """
        Updates product prices across retailers, records PriceHistory, and checks alerts.
        """
        return PriceScraperEngine.scrape_and_update_product(product, db_session)

    @staticmethod
    def run_full_scraping_job(app, db_session):
        """
        Full background job triggered by APScheduler.
        """
        with app.app_context():
            logger.info("Starting automated price refresh job...")
            products = Product.query.all()
            total_updated = 0
            for product in products:
                res = PriceScraperEngine.scrape_and_update_product(product, db_session)
                if isinstance(res, dict):
                    total_updated += res.get("prices_updated", 0)
                elif isinstance(res, int):
                    total_updated += res
            logger.info(f"Price refresh completed. Updated {total_updated} price points.")
            return total_updated

    @staticmethod
    def get_live_fluctuations(limit=30, drops_only=False, category_slug=None):
        """
        Retrieves real-time price fluctuation stream across the catalog.
        """
        products = Product.query.all()
        if category_slug:
            products = [p for p in products if p.category and (p.category.slug == category_slug or p.category.name.lower() == category_slug.lower())]

        events = []
        for p in products:
            fluc = p.get_fluctuation_metrics()
            if fluc["direction"] == "stable" and not drops_only:
                continue
            if drops_only and fluc["direction"] != "down":
                continue

            # Best store price
            best_price_obj = None
            for pr in p.prices:
                if pr.is_lowest or pr.price == p.lowest_price:
                    best_price_obj = pr
                    break

            ret_name = best_price_obj.retailer.name if (best_price_obj and best_price_obj.retailer) else "Amazon"
            ret_slug = best_price_obj.retailer.slug if (best_price_obj and best_price_obj.retailer) else "amazon"
            buy_url = best_price_obj.direct_buy_url if best_price_obj else f"https://www.amazon.in/s?k={p.name}"

            old_p = round(p.lowest_price - fluc["change_amt"], 2) if fluc["change_amt"] != 0 else p.original_price or p.lowest_price

            events.append({
                "product_id": p.id,
                "name": p.name,
                "brand": p.brand,
                "category": p.category.name if p.category else "Electronics",
                "image": p.image,
                "current_price": p.lowest_price,
                "previous_price": old_p,
                "change_amt": fluc["change_amt"],
                "change_pct": fluc["change_pct"],
                "direction": fluc["direction"],
                "retailer_name": ret_name,
                "retailer_slug": ret_slug,
                "buy_url": buy_url,
                "all_time_low": fluc["all_time_low"],
                "volatility": fluc["volatility"],
                "deal_score": fluc["deal_score"],
                "recommendation": fluc["recommendation"],
                "last_changed": fluc["last_changed"]
            })

        # Sort: biggest percentage drops first
        events.sort(key=lambda x: (x["direction"] != "down", x["change_pct"] if x["direction"] == "down" else -x["change_pct"]))
        return events[:limit]

    @staticmethod
    def simulate_live_fluctuations(count=6, product_ids=None, db_session=None):
        """
        Triggers live market price fluctuations for testing live price drops, ticker, and alert engines.
        """
        if db_session is None:
            db_session = db.session

        if product_ids:
            target_products = [Product.query.get(pid) for pid in product_ids if Product.query.get(pid)]
        else:
            all_prods = Product.query.all()
            if not all_prods:
                return []
            target_products = random.sample(all_prods, min(count, len(all_prods)))

        now = datetime.utcnow()
        results = []

        for prod in target_products:
            if not prod.prices:
                continue

            # Pick a random retailer price to fluctuate
            chosen_price_obj = random.choice(prod.prices)
            old_p = chosen_price_obj.price

            # Bias towards price drops for exciting real-time deals (-12% to +3%)
            fluct_rate = random.choice([-0.08, -0.06, -0.05, -0.04, -0.03, -0.02, 0.01, 0.02])
            new_p = max(500.0, round(old_p * (1 + fluct_rate)))

            chosen_price_obj.price = float(new_p)
            chosen_price_obj.last_updated = now

            # Insert history record
            h_entry = PriceHistory(
                product_id=prod.id,
                retailer_id=chosen_price_obj.retailer_id,
                price=float(new_p),
                recorded_at=now
            )
            db_session.add(h_entry)

            prod.recalculate_lowest_price()
            db_session.commit()

            # Check price alerts
            alerts_hit = PriceScraperEngine.check_price_alerts(prod, db_session)

            fluc = prod.get_fluctuation_metrics()
            results.append({
                "product_id": prod.id,
                "name": prod.name,
                "brand": prod.brand,
                "retailer": chosen_price_obj.retailer.name if chosen_price_obj.retailer else "Store",
                "old_price": old_p,
                "new_price": new_p,
                "change_amt": fluc["change_amt"],
                "change_pct": fluc["change_pct"],
                "direction": fluc["direction"],
                "lowest_price": prod.lowest_price,
                "alerts_triggered": alerts_hit,
                "timestamp": now.strftime("%H:%M:%S")
            })

        return results


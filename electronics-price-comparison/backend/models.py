import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    wishlists = db.relationship('Wishlist', backref='user', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('PriceAlert', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(50), default="bi-box")
    description = db.Column(db.Text, nullable=True)

    products = db.relationship('Product', backref='category', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "icon": self.icon,
            "description": self.description,
            "product_count": len(self.products)
        }


class Retailer(db.Model):
    __tablename__ = 'retailers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    badge_bg = db.Column(db.String(50), default="bg-secondary text-white")
    icon = db.Column(db.String(50), default="bi-shop")
    website_url = db.Column(db.String(255), default="#")

    prices = db.relationship('Price', backref='retailer', lazy=True, cascade="all, delete-orphan")
    price_histories = db.relationship('PriceHistory', backref='retailer', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "badge_bg": self.badge_bg,
            "icon": self.icon,
            "website_url": self.website_url
        }


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image = db.Column(db.String(500))
    gallery_json = db.Column(db.Text, default='[]')
    rating = db.Column(db.Float, default=4.5)
    review_count = db.Column(db.Integer, default=0)
    lowest_price = db.Column(db.Float, default=0.0)
    original_price = db.Column(db.Float, default=0.0)
    discount_percentage = db.Column(db.Integer, default=0)
    savings_amount = db.Column(db.Float, default=0.0)
    is_featured = db.Column(db.Boolean, default=False)
    is_deal = db.Column(db.Boolean, default=False)
    colors_json = db.Column(db.Text, default='[]')
    storage_options_json = db.Column(db.Text, default='[]')
    description = db.Column(db.Text, nullable=True)
    features_json = db.Column(db.Text, default='[]')
    specs_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prices = db.relationship('Price', backref='product', lazy=True, cascade="all, delete-orphan")
    price_histories = db.relationship('PriceHistory', backref='product', lazy=True, cascade="all, delete-orphan")
    wishlist_entries = db.relationship('Wishlist', backref='product', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('PriceAlert', backref='product', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def gallery(self):
        try:
            return json.loads(self.gallery_json) if self.gallery_json else []
        except Exception:
            return []

    @property
    def colors(self):
        try:
            return json.loads(self.colors_json) if self.colors_json else []
        except Exception:
            return []

    @property
    def storage_options(self):
        try:
            return json.loads(self.storage_options_json) if self.storage_options_json else []
        except Exception:
            return []

    @property
    def features(self):
        try:
            return json.loads(self.features_json) if self.features_json else []
        except Exception:
            return []

    @property
    def specs(self):
        try:
            return json.loads(self.specs_json) if self.specs_json else {}
        except Exception:
            return {}

    def recalculate_lowest_price(self):
        if self.prices:
            valid_prices = [p.price for p in self.prices if p.price > 0]
            if valid_prices:
                min_p = min(valid_prices)
                self.lowest_price = min_p
                if self.original_price and self.original_price > min_p:
                    self.savings_amount = self.original_price - min_p
                    self.discount_percentage = int(((self.original_price - min_p) / self.original_price) * 100)
                else:
                    self.savings_amount = 0.0
                    self.discount_percentage = 0
                for p in self.prices:
                    p.is_lowest = (p.price == min_p)

    def get_fluctuation_metrics(self):
        """
        Calculates recent price fluctuation deltas, all-time lows, volatility, and smart deal score.
        """
        try:
            histories = PriceHistory.query.filter_by(product_id=self.id).order_by(PriceHistory.recorded_at.desc()).all()
            if not histories:
                return {
                    "change_amt": 0.0,
                    "change_pct": 0.0,
                    "direction": "stable",
                    "all_time_low": self.lowest_price or self.original_price or 0.0,
                    "all_time_high": self.original_price or self.lowest_price or 0.0,
                    "volatility": "Low Fluctuation",
                    "deal_score": 85,
                    "recommendation": "Fair Market Price",
                    "last_changed": "Recently"
                }

            all_prices = [h.price for h in histories if h.price > 0]
            if not all_prices:
                all_prices = [self.lowest_price]

            all_time_low = min(all_prices)
            all_time_high = max(all_prices)
            if self.original_price and self.original_price > all_time_high:
                all_time_high = self.original_price

            curr_price = self.lowest_price or (all_prices[0] if all_prices else 0.0)

            # Find previous distinct price point
            prev_price = curr_price
            last_changed_dt = histories[0].recorded_at if histories else datetime.utcnow()
            for h in histories[1:]:
                if abs(h.price - curr_price) >= 1.0:
                    prev_price = h.price
                    last_changed_dt = h.recorded_at
                    break

            change_amt = curr_price - prev_price
            change_pct = round(((curr_price - prev_price) / prev_price * 100), 1) if prev_price > 0 else 0.0

            if change_amt < -1.0:
                direction = "down"
            elif change_amt > 1.0:
                direction = "up"
            else:
                direction = "stable"

            # Volatility calculation
            spread_pct = ((all_time_high - all_time_low) / all_time_low * 100) if all_time_low > 0 else 0.0
            if spread_pct >= 15.0:
                volatility = "High Fluctuation"
            elif spread_pct >= 6.0:
                volatility = "Moderate Fluctuation"
            else:
                volatility = "Low Fluctuation"

            # Deal Score (1 - 100)
            if curr_price <= all_time_low * 1.02:
                deal_score = 96
                recommendation = "🔥 Strong Buy - Price at Historic Low!"
            elif curr_price <= all_time_low * 1.06:
                deal_score = 88
                recommendation = "🟢 Great Deal - Well Below Average"
            elif curr_price <= all_time_low * 1.12:
                deal_score = 75
                recommendation = "⚖️ Fair Market Price"
            else:
                deal_score = 60
                recommendation = "⏳ Wait for Upcoming Deal"

            # Format relative time
            delta = datetime.utcnow() - (last_changed_dt or datetime.utcnow())
            if delta.days > 1:
                last_changed = f"{delta.days} days ago"
            elif delta.seconds > 3600:
                last_changed = f"{delta.seconds // 3600}h ago"
            elif delta.seconds > 60:
                last_changed = f"{delta.seconds // 60}m ago"
            else:
                last_changed = "Just now"

            return {
                "change_amt": round(change_amt, 2),
                "change_pct": change_pct,
                "direction": direction,
                "all_time_low": round(all_time_low, 2),
                "all_time_high": round(all_time_high, 2),
                "volatility": volatility,
                "deal_score": deal_score,
                "recommendation": recommendation,
                "last_changed": last_changed
            }
        except Exception:
            return {
                "change_amt": 0.0,
                "change_pct": 0.0,
                "direction": "stable",
                "all_time_low": self.lowest_price,
                "all_time_high": self.original_price or self.lowest_price,
                "volatility": "Moderate",
                "deal_score": 80,
                "recommendation": "Great Deal",
                "last_changed": "Recently"
            }

    @property
    def fluctuation(self):
        return self.get_fluctuation_metrics()

    @property
    def google_shopping_url(self):
        """
        Direct search redirect to the Google Shopping engine (SerpApi engine).
        """
        import urllib.parse
        clean_name = Price.clean_product_query(self.name, self.brand)
        encoded = urllib.parse.quote_plus(clean_name)
        return f"https://www.google.com/search?tbm=shop&q={encoded}&gl=in&hl=en"

    @property
    def amazon_url(self):
        return Price.generate_direct_store_url(self.name, self.brand, "amazon")

    @property
    def flipkart_url(self):
        return Price.generate_direct_store_url(self.name, self.brand, "flipkart")

    @property
    def croma_url(self):
        return Price.generate_direct_store_url(self.name, self.brand, "croma")

    @property
    def reliance_url(self):
        return Price.generate_direct_store_url(self.name, self.brand, "reliance")

    @property
    def vijaysales_url(self):
        return Price.generate_direct_store_url(self.name, self.brand, "vijaysales")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category.name if self.category else "Electronics",
            "category_id": self.category_id,
            "image": self.image,
            "gallery": self.gallery,
            "rating": self.rating,
            "review_count": self.review_count,
            "lowest_price": self.lowest_price,
            "original_price": self.original_price,
            "discount_percentage": self.discount_percentage,
            "savings_amount": self.savings_amount,
            "is_featured": self.is_featured,
            "is_deal": self.is_deal,
            "colors": self.colors,
            "storage_options": self.storage_options,
            "description": self.description,
            "features": self.features,
            "specs": self.specs,
            "fluctuation": self.fluctuation,
            "stores": [p.to_dict() for p in self.prices]
        }


class Price(db.Model):
    __tablename__ = 'prices'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailers.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    delivery = db.Column(db.String(100), default="Standard Delivery")
    availability = db.Column(db.String(50), default="In Stock")
    rating = db.Column(db.Float, default=4.5)
    is_lowest = db.Column(db.Boolean, default=False)
    buy_url = db.Column(db.String(500), default="#")
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def clean_product_query(product_name: str, brand: str = "") -> str:
        """
        Cleans and normalizes product titles to pure brand + model without clutter.
        Preserves storage spec and removes accessory/color noise so retailer searches hit exact device.
        """
        import re
        clean = product_name

        # Extract storage or spec (e.g. 128 GB, 256 GB, 512 GB, 1 TB)
        storage_match = re.search(r"(\d+\s*(?:GB|TB))\b", clean, re.IGNORECASE)
        storage = storage_match.group(1).replace(" ", "") if storage_match else ""

        # Remove parenthetical noise like '(5G Series)', '(256 GB)', '(Standard)'
        clean = re.sub(r"\s*\([^)]*\)", "", clean)

        # Remove trailing color options after dash or slash
        clean = re.sub(r"\s*[-–—]\s*(?:Pink|Blue|Black|White|Silver|Gold|Green|Yellow|Red|Titanium|Natural Titanium|Space Black|Midnight|Starlight|Grey|Gray|Purple|Teal|Desert Titanium)(?:\s*/\s*[\w\s]+)*", "", clean, flags=re.IGNORECASE)

        # Remove any remaining trailing slash segments
        if "/" in clean:
            clean = clean.split("/")[0]

        # Remove dash separators
        clean = re.sub(r"\s*[-–—]\s*", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()

        # Re-attach storage specification if not already in title
        if storage and storage.lower() not in clean.lower():
            clean = f"{clean} {storage}"

        # Normalize any synthetic model names
        clean = re.sub(r"Neo\s+2\d", "Neo 9 Pro", clean, flags=re.IGNORECASE)

        if brand and brand.lower() not in clean.lower():
            clean = f"{brand} {clean}".strip()

        return clean or product_name.strip()

    @staticmethod
    def generate_direct_store_url(product_name: str, brand: str = "", retailer_slug: str = "amazon") -> str:
        """
        Generates genuine direct retailer store URLs (Amazon, Flipkart, Croma, Reliance Digital, etc.)
        ensuring users land directly on the merchant product search instead of Google Shopping.
        """
        import urllib.parse

        clean_name = Price.clean_product_query(product_name, brand)
        encoded = urllib.parse.quote_plus(clean_name)
        r_slug = (retailer_slug or "").lower().strip()

        retailer_urls = {
            "amazon": f"https://www.amazon.in/s?k={encoded}",
            "flipkart": f"https://www.flipkart.com/search?q={encoded}",
            "croma": f"https://www.croma.com/searchB?q={encoded}%3Arelevance",
            "reliance": f"https://www.reliancedigital.in/search?q={encoded}",
            "vijaysales": f"https://www.vijaysales.com/search/{encoded}",
            "tatacliq": f"https://www.tatacliq.com/search/?searchCategory=all&text={encoded}",
            "ajio": f"https://www.ajio.com/search/?text={encoded}",
            "poorvika": f"https://www.poorvika.com/search?q={encoded}",
            "mdcomputers": f"https://mdcomputers.in/index.php?category_id=0&search={encoded}&submit_search=&route=product%2Fsearch",
            "vedantcomputers": f"https://www.vedantcomputers.com/index.php?route=product/search&search={encoded}",
            "vedant": f"https://www.vedantcomputers.com/index.php?route=product/search&search={encoded}",
            "primeabgb": f"https://www.primeabgb.com/?post_type=product&s={encoded}",
            "ovantica": f"https://ovantica.com/search?q={encoded}"
        }
        return retailer_urls.get(r_slug, f"https://www.amazon.in/s?k={encoded}")

    def is_single_product_url(self, url: str) -> bool:
        """Determines if the given URL points to a specific single product page rather than a search query."""
        if not url or url == "#":
            return False
        u = url.lower()
        if "/s?k=" in u or "/search" in u or "query=" in u:
            return False
        if "/dp/" in u or "/gp/product/" in u or "/p/" in u or "/item/" in u:
            return True
        return False

    def resolve_single_product_url(self) -> str:
        """
        Resolves the exact direct single product page (Amazon /dp/ASIN, Flipkart /p/itm, etc.)
        saving users from landing on a 100+ item search results page.
        """
        # 1. If self.buy_url already has a direct single product page link, return it
        if self.buy_url and self.is_single_product_url(self.buy_url):
            return self.buy_url

        prod_name = (self.product.name if self.product else "").strip()
        prod_brand = (self.product.brand if self.product else "").strip()
        r_slug = (self.retailer.slug if self.retailer else "amazon").lower().strip()

        # 2. Check canonical ASIN resolver
        try:
            from services.asin_resolver import resolve_canonical_single_url
            resolved = resolve_canonical_single_url(prod_name, prod_brand, r_slug)
            if resolved and self.is_single_product_url(resolved):
                self.buy_url = resolved
                try:
                    db.session.commit()
                except Exception:
                    pass
                return resolved
        except Exception:
            pass

        # 3. Fallback to direct store URL
        return self.direct_buy_url

    @property
    def direct_buy_url(self):
        """
        Returns the genuine direct retailer link (Amazon, Flipkart, Croma, etc.)
        for the 'Buy Now' button, unwrapping any Google redirects and ensuring
        users are never redirected to Google Shopping.
        """
        import urllib.parse

        if self.buy_url and self.buy_url != "#":
            if "google." in self.buy_url:
                parsed = urllib.parse.urlparse(self.buy_url)
                qs = urllib.parse.parse_qs(parsed.query)
                for param in ['q', 'url', 'adurl', 'direct_url']:
                    if param in qs and qs[param][0].startswith('http') and 'google.' not in qs[param][0]:
                        return qs[param][0]
            else:
                return self.buy_url

        prod_name = self.product.name if self.product else "product"
        prod_brand = self.product.brand if self.product else ""
        r_slug = self.retailer.slug if self.retailer else "amazon"

        return Price.generate_direct_store_url(prod_name, prod_brand, r_slug)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "retailer_id": self.retailer_id,
            "name": self.retailer.name if self.retailer else "Retailer",
            "logo_text": self.retailer.name if self.retailer else "Retailer",
            "price": self.price,
            "delivery": self.delivery,
            "rating": self.rating,
            "availability": self.availability,
            "is_lowest": self.is_lowest,
            "buy_url": self.direct_buy_url,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M") if self.last_updated else ""
        }


class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailers.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "retailer_id": self.retailer_id,
            "retailer_name": self.retailer.name if self.retailer else "Retailer",
            "price": self.price,
            "recorded_at": self.recorded_at.strftime("%Y-%m-%d")
        }


class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PriceAlert(db.Model):
    __tablename__ = 'price_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    is_triggered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "",
            "product_image": self.product.image if self.product else "",
            "current_price": self.product.lowest_price if self.product else 0.0,
            "target_price": self.target_price,
            "is_triggered": self.is_triggered,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

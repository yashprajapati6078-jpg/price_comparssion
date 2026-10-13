import json
import re
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
    direct_url = db.Column(db.String(1000), nullable=True)
    product_url = db.Column(db.String(1000), nullable=True)
    url_type = db.Column(db.String(50), default="SEARCH_FALLBACK")
    retailer_product_id = db.Column(db.String(100), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def clean_product_query(product_name: str, brand: str = "") -> str:
        """
        Cleans and normalizes product titles to pure brand + model without clutter.
        Preserves storage spec and removes accessory/color/tech noise so retailer searches hit exact device.
        """
        import re
        clean = product_name or ""

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

        # Remove technical clutter phrases that break retailer search engines
        clutter_patterns = [
            r"\bgddr6x\b", r"\bgddr6\b", r"\bfounders edition\b", r"\boc edition\b", r"\bedition\b",
            r"\bgraphics card\b", r"\bdesktop processor\b", r"\bunlocked processor\b", r"\bflagship processor\b",
            r"\bprocessor\b", r"\binternal gaming ssd\b", r"\binternal ssd\b", r"\bwith heatsink\b",
            r"\bwireless active noise canceling headphones\b", r"\bwireless noise canceling headphones\b",
            r"\bnoise canceling wireless headphones\b", r"\bbluetooth headset\b", r"\bbluetooth headphone with mic\b",
            r"\bfull-frame mirrorless camera\b", r"\bconsole\b", r"\bslim disc\b", r"\bsmart oled evo tv\b",
            r"\bsmart tv\b", r"\bgoogle tv\b", r"\bcrystal uhd tv\b", r"\bneo qled 144hz tv\b", r"\bmini-led\b",
            r"\bcinema oled master series\b", r"\bspecial creator\b", r"\bwireless v2\b", r"\b5g dual sim\b",
            r"\bpcie\s*4\.0\b", r"\bpcie gen4\b", r"\bnvme\s*m\.2\b", r"\b3d nand\b",
            r"\b24gb\b", r"\b16gb\b", r"\b12gb\b", r"\b8gb\b", r"\b32gb\b", r"\b64gb\b"
        ]
        for pat in clutter_patterns:
            clean = re.sub(pat, "", clean, flags=re.IGNORECASE)

        # Remove dash separators
        clean = re.sub(r"\s*[-–—]\s*", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()

        # Re-attach storage specification if it was a phone/tablet/drive and not already present
        if storage and storage.lower() not in clean.lower() and any(k in clean.lower() for k in ["iphone", "galaxy", "ipad", "pixel", "ssd", "pro", "ultra"]):
            clean = f"{clean} {storage}"

        # Normalize any synthetic model names
        clean = re.sub(r"Neo\s+2\d", "Neo 9 Pro", clean, flags=re.IGNORECASE)

        if brand and brand.lower() not in clean.lower():
            clean = f"{brand} {clean}".strip()

        return clean or (product_name or "").strip()

    @staticmethod
    def generate_direct_store_url(product_name: str, brand: str = "", retailer_slug: str = "amazon") -> str:
        """
        Generates genuine direct retailer store URLs (Amazon, Flipkart, Croma, Reliance Digital, etc.)
        ensuring users land directly on the merchant product search instead of Google Shopping.
        """
        import urllib.parse
        import re

        clean_name = Price.clean_product_query(product_name, brand)
        r_slug = (retailer_slug or "").lower().strip()

        if r_slug == "croma":
            try:
                from services.asin_resolver import resolve_canonical_single_url
                canon = resolve_canonical_single_url(clean_name, brand, "croma")
                if canon:
                    return canon
            except Exception:
                pass
            encoded = urllib.parse.quote_plus(clean_name)
            return f"https://www.croma.com/searchB?q={encoded}%3Arelevance"
        elif r_slug == "vijaysales":
            try:
                from services.asin_resolver import resolve_canonical_single_url
                canon = resolve_canonical_single_url(clean_name, brand, "vijaysales")
                if canon:
                    return canon
            except Exception:
                pass
            encoded = urllib.parse.quote_plus(clean_name)
            return f"https://www.vijaysales.com/search-listing?q={encoded}"
        elif r_slug == "reliance":
            encoded = urllib.parse.quote_plus(clean_name)
            return f"https://www.reliancedigital.in/products?q={encoded}"
        elif r_slug == "flipkart":
            encoded = urllib.parse.quote_plus(clean_name)
            return f"https://www.flipkart.com/search?q={encoded}"

        encoded = urllib.parse.quote_plus(clean_name)
        return f"https://www.amazon.in/s?k={encoded}"

    def is_single_product_url(self, url: str) -> bool:
        """
        Determines whether the given URL points to a specific exact single product page
        rather than a search query or category listing page.
        """
        if not url or url == "#":
            return False
        u = url.lower().strip()

        # Definite search / query patterns -> NOT an exact product page
        if "/search" in u or "/s?k=" in u or "searchb" in u or "/s?" in u or "query=" in u or "route=product/search" in u:
            return False

        # Reject synthetic hashes and broken placeholders
        if "itm00" in u or "4900000" in u or "b0bg953f9f" in u:
            return False

        # Amazon single product: /dp/<ASIN> or /gp/product/<ASIN>
        if "amazon." in u and ("/dp/" in u or "/gp/product/" in u):
            return True

        # Flipkart single product: /p/itm or /p/<id> with product page pattern
        if "flipkart." in u and "/p/" in u:
            return True

        # Croma single product: /p/<sku>
        if "croma." in u and "/p/" in u:
            return True

        # Reliance Digital single product: /p/<id>
        if "reliancedigital." in u and "/p/" in u:
            return True

        # Vijay Sales single product: /<slug>/<id> where id is numeric (e.g. /23812) or /p/
        if "vijaysales." in u and (re.search(r"/\d{4,8}(?:[/?#]|$)", u) or "/p/" in u):
            return True

        # Pre-generated direct affiliate links (EarnKaro, CueLinks, etc.)
        if any(dom in u for dom in ["fktr.in", "ekaro.in", "linkredirect.in", "linksredirect.com"]):
            return True

        # Generic e-commerce single product (/product/<id>, /item/<id>, /p/<id>)
        if "/product/" in u or "/item/" in u or "/p/" in u:
            return True

        return False

    @property
    def effective_url_type(self) -> str:
        """Returns DIRECT_PRODUCT if URL is an exact single product link, else SEARCH_FALLBACK."""
        url = self.effective_product_url
        return "DIRECT_PRODUCT" if self.is_single_product_url(url) else "SEARCH_FALLBACK"

    @property
    def effective_product_url(self) -> str:
        """
        Returns the most specific retailer product URL available.
        Checks:
        1. Canonical Product Registry (verified exact URLs take top priority)
        2. Stored product_url (if single product page and not synthetic hash)
        3. Stored direct_url (if single product page)
        4. Existing buy_url (if single product page)
        5. Targeted store query URL (guarantees exact product without dead links)
        """
        prod_name = (self.product.name if self.product else "").strip()
        prod_brand = (self.product.brand if self.product else "").strip()
        r_slug = (self.retailer.slug if self.retailer else "amazon").lower().strip()

        # 1. Resolve via Canonical Product Registry first
        try:
            from services.asin_resolver import resolve_canonical_single_url
            resolved = resolve_canonical_single_url(prod_name, prod_brand, r_slug)
            if resolved:
                if "b0bg953f9f" in resolved.lower():
                    resolved = resolved.replace("B0BG953F9F", "B0BSVMLVTD").replace("b0bg953f9f", "B0BSVMLVTD")
                return resolved
        except Exception:
            pass

        # 2. Stored exact product_url
        if self.product_url and self.is_single_product_url(self.product_url):
            p_url = self.product_url
            if "b0bg953f9f" in p_url.lower():
                p_url = p_url.replace("B0BG953F9F", "B0BSVMLVTD").replace("b0bg953f9f", "B0BSVMLVTD")
            return p_url

        # 3. Stored direct_url
        if self.direct_url and self.is_single_product_url(self.direct_url):
            d_url = self.direct_url
            if "b0bg953f9f" in d_url.lower():
                d_url = d_url.replace("B0BG953F9F", "B0BSVMLVTD").replace("b0bg953f9f", "B0BSVMLVTD")
            return d_url

        # 4. Existing buy_url
        if self.buy_url and self.is_single_product_url(self.buy_url):
            return self.buy_url

        # 5. Targeted merchant store URL
        fallback_url = Price.generate_direct_store_url(prod_name, prod_brand, r_slug)
        return fallback_url

    def resolve_single_product_url(self) -> str:
        """
        Resolves the exact direct single product page (Amazon /dp/ASIN, Flipkart /p/itm, etc.)
        with active merchant affiliate parameters attached.
        """
        base_url = self.effective_product_url
        try:
            from services.affiliate import build_affiliate_url
            prod_name = (self.product.name if self.product else "").strip()
            prod_brand = (self.product.brand if self.product else "").strip()
            r_slug = (self.retailer.slug if self.retailer else "amazon").lower().strip()
            return build_affiliate_url(base_url, r_slug, prod_name, prod_brand, self.retailer_product_id)
        except Exception:
            return base_url

    @property
    def direct_buy_url(self):
        """Maintains backward compatibility returning the affiliate product URL."""
        return self.resolve_single_product_url()

    def to_dict(self):
        url = self.effective_product_url
        u_type = self.effective_url_type
        r_id = self.retailer_product_id or ""
        if not r_id and "amazon." in url and "/dp/" in url:
            m = re.search(r"/dp/([A-Z0-9]{10})", url)
            if m:
                r_id = m.group(1)
        elif not r_id and "flipkart." in url:
            m = re.search(r"pid=([A-Z0-9]+)", url) or re.search(r"/p/(itm[a-zA-Z0-9]+)", url)
            if m:
                r_id = m.group(1)

        return {
            "id": self.id,
            "product_id": self.product_id,
            "retailer_id": self.retailer_id,
            "retailer": self.retailer.name if self.retailer else "Retailer",
            "name": self.retailer.name if self.retailer else "Retailer",
            "product_name": self.product.name if self.product else "",
            "logo_text": self.retailer.name if self.retailer else "Retailer",
            "price": self.price,
            "delivery": self.delivery,
            "rating": self.rating,
            "availability": self.availability,
            "is_lowest": self.is_lowest,
            "product_url": url,
            "buy_url": url,
            "url_type": u_type,
            "retailer_product_id": r_id,
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

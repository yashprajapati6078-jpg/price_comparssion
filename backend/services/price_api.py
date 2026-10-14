import os
import re
import logging
import requests
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger("PriceAPIService")

class PriceAPIService:
    """
    Legitimate External Product & Price API Integration Service.
    Supports SerpApi (Google Shopping) and RapidAPI Real-Time Product Search.
    Extracts live retailer prices, direct URLs, stock status, and metadata.
    """

    DEFAULT_TIMEOUT = 25  # seconds

    ACCESSORY_KEYWORDS = [
        "case", "cover", "back cover", "tempered glass", "screen protector",
        "protector", "skin", "pouch", "sleeve", "bumper", "strap", "cable",
        "charger", "adapter", "housing", "lens protector", "guard", "decal",
        "stand", "holder", "holster"
    ]

    REFURBISHED_KEYWORDS = [
        "refurbished", "renewed", "pre-owned", "preowned", "second hand", "secondhand",
        "used", "unlocked fair", "unlocked mix", "fair condition", "good grade",
        "grade a", "grade b", "grade c", "like-new", "like new", "open box", "open-box",
        "pre owned", "tested & verified", "superb (like-new)"
    ]

    REFURBISHED_RETAILER_SLUGS = {
        "grest", "ovantica", "controlz", "easyphones", "phoneswapstore",
        "phoneswap", "budli", "fonezone", "sahivalue", "cashify", "quickmobile"
    }

    @classmethod
    def _is_accessory_listing(cls, query: str, item_title: str) -> bool:
        """
        Determines whether a returned shopping result is an accessory (case, cover, glass)
        rather than the main queried device.
        """
        if not item_title:
            return False
        q_lower = query.lower()
        t_lower = item_title.lower()

        # If user explicitly queried for an accessory, do not filter out
        for kw in cls.ACCESSORY_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                return False

        # If item title contains accessory terms not present in query
        for kw in cls.ACCESSORY_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", t_lower):
                return True

        return False

    @classmethod
    def _query_requests_refurbished(cls, query: str) -> bool:
        """Check if user query explicitly asked for refurbished/used products."""
        q_lower = query.lower()
        return any(kw in q_lower for kw in ["refurbished", "renewed", "pre-owned", "preowned", "second hand", "used"])

    @classmethod
    def _is_refurbished_or_used(cls, query: str, item_title: str) -> bool:
        """
        Filters out refurbished, renewed, open-box, or second-hand listings
        unless the search query explicitly requested them.
        """
        if not item_title or cls._query_requests_refurbished(query):
            return False
        t_lower = item_title.lower()
        for kw in cls.REFURBISHED_KEYWORDS:
            if kw in t_lower:
                return True
        return False

    @classmethod
    def is_refurbished_store(cls, retailer_slug: str, raw_source: str = "") -> bool:
        """Determines if the retailer is primarily a refurbished/used device seller."""
        s = (retailer_slug or "").lower()
        r = (raw_source or "").lower()
        for ref_slug in cls.REFURBISHED_RETAILER_SLUGS:
            if ref_slug in s or ref_slug in r:
                return True
        return False

    @classmethod
    def _is_model_mismatch(cls, query: str, item_title: str) -> bool:
        """
        Guarantees exact model variant integrity:
        e.g., iPhone 15 Pro Max query rejects base iPhone 15, iPhone 15 Plus, or iPhone 17.
        """
        if not item_title:
            return False
        q = query.lower()
        t = item_title.lower()

        # 1. Pro Max check: if query has 'pro max', title must have 'pro max'
        if "pro max" in q and "pro max" not in t:
            return True

        # 2. Pro check: if query has 'pro' (and not 'pro max'), title cannot be 'pro max' or omit 'pro'
        if "pro" in q and "pro max" not in q:
            if "pro max" in t or "pro" not in t:
                return True

        # 3. Plus check: query has plus -> title must have plus; query lacks plus -> title must not have plus
        if "plus" in q and "plus" not in t:
            return True
        if "plus" not in q and "plus" in t:
            return True

        # 4. Ultra check: query has ultra -> title must have ultra; query lacks ultra -> title must not have ultra
        if "ultra" in q and "ultra" not in t:
            return True
        if "ultra" not in q and "ultra" in t:
            return True

        # 5. Mini check
        if "mini" in q and "mini" not in t:
            return True
        if "mini" not in q and "mini" in t:
            return True

        # 6. iPhone model generation mismatch (e.g. iPhone 15 vs iPhone 14/16/17)
        m_q = re.search(r"\biphone\s+(\d{1,2})\b", q)
        if m_q:
            q_num = m_q.group(1)
            m_t = re.search(r"\biphone\s+(\d{1,2})\b", t)
            if m_t and m_t.group(1) != q_num:
                return True

        # 7. Samsung Galaxy S-series number mismatch (e.g. S24 vs S23)
        m_sg_q = re.search(r"\b(s\d{2})\b", q)
        if m_sg_q:
            q_sg = m_sg_q.group(1)
            m_sg_t = re.search(r"\b(s\d{2})\b", t)
            if m_sg_t and m_sg_t.group(1) != q_sg:
                return True

        return False

    @staticmethod
    def get_retailer_badge_style(retailer_slug: str, retailer_name: str = "") -> str:
        """
        Returns modern curated CSS badge classes for retailers.
        Avoids dull default grey badges.
        """
        s = (retailer_slug or "").lower().strip()
        n = (retailer_name or "").lower().strip()

        mapping = {
            "amazon": "badge-retailer-amazon",
            "flipkart": "badge-retailer-flipkart",
            "croma": "badge-retailer-croma",
            "reliance": "badge-retailer-reliance",
            "vijaysales": "badge-retailer-vijaysales",
            "tatacliq": "badge-retailer-tatacliq",
            "poorvika": "badge-retailer-poorvika",
            "jiomart": "badge-retailer-jiomart",
            "bajaj": "badge-retailer-bajaj",
            "mdcomputers": "badge-retailer-indigo",
            "vedant": "badge-retailer-teal",
            "primeabgb": "badge-retailer-purple",
            "apple": "bg-dark text-white",
            "samsung": "badge-retailer-indigo",
        }
        for k, v in mapping.items():
            if k in s or k in n:
                return v

        # Dynamic modern palette
        dynamic_palettes = [
            "badge-retailer-indigo",
            "badge-retailer-teal",
            "badge-retailer-purple",
            "badge-retailer-rose",
            "badge-retailer-cyan",
            "badge-retailer-emerald",
            "badge-retailer-amber",
            "badge-retailer-slate"
        ]
        val = sum(ord(c) for c in (s or n or "store"))
        return dynamic_palettes[val % len(dynamic_palettes)]


    @staticmethod
    def get_config() -> Dict[str, str]:
        """
        Loads API credentials and provider configuration from environment variables.
        """
        try:
            from dotenv import load_dotenv
            # Check current dir and parent directories for .env
            current = os.path.abspath(os.path.dirname(__file__))
            for _ in range(4):
                env_file = os.path.join(current, '.env')
                if os.path.exists(env_file):
                    load_dotenv(env_file, override=True)
                    break
                current = os.path.dirname(current)
        except Exception:
            pass

        return {
            "provider": os.getenv("PRICE_API_PROVIDER", "serpapi").lower().strip(),
            "serpapi_key": os.getenv("SERPAPI_API_KEY", "").strip(),
            "rapidapi_key": os.getenv("RAPIDAPI_KEY", "").strip(),
            "rapidapi_host": os.getenv("RAPIDAPI_HOST", "real-time-product-search.p.rapidapi.com").strip(),
            "country": os.getenv("PRICE_API_COUNTRY", "in").lower().strip(),
            "currency": os.getenv("PRICE_API_CURRENCY", "INR").upper().strip(),
        }

    @classmethod
    def fetch_product_prices(cls, query: str, country: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entrypoint: Accepts a product query, queries the external price API,
        and returns normalized multi-retailer price data.
        """
        clean_query = query.strip()
        if not clean_query:
            return {
                "success": False,
                "error_code": "EMPTY_QUERY",
                "error": "Product search query cannot be empty.",
                "prices": [],
                "source": None
            }

        config = cls.get_config()
        provider = config["provider"]

        if provider == "rapidapi":
            return cls._fetch_rapidapi_product_search(clean_query, config, country)
        elif provider == "serpapi":
            return cls._fetch_serpapi_google_shopping(clean_query, config, country)
        elif provider in ("hybrid", "multi", "auto"):
            # Multi-source Strategy: Try SerpApi first, fallback to RapidAPI on quota/rate-limit/error
            if config["serpapi_key"]:
                logger.info("Hybrid Mode: Querying Primary Provider (SerpApi)...")
                res = cls._fetch_serpapi_google_shopping(clean_query, config, country)
                if res.get("success") and res.get("prices"):
                    return res
                logger.warning(f"SerpApi did not return active prices ({res.get('error_code')}). Falling back to RapidAPI...")

            if config["rapidapi_key"]:
                logger.info("Hybrid Mode: Querying Secondary Provider (RapidAPI)...")
                return cls._fetch_rapidapi_product_search(clean_query, config, country)

            return {
                "success": False,
                "error_code": "NO_KEYS_CONFIGURED",
                "error": "Neither SERPAPI_API_KEY nor RAPIDAPI_KEY is configured in .env.",
                "prices": [],
                "source": "Hybrid Multi-Source"
            }
        else:
            return {
                "success": False,
                "error_code": "UNSUPPORTED_PROVIDER",
                "error": f"Unsupported API provider '{provider}'. Valid options are 'serpapi', 'rapidapi', or 'hybrid'.",
                "prices": [],
                "source": provider
            }

    @classmethod
    def _fetch_serpapi_google_shopping(cls, query: str, config: Dict[str, str], country: Optional[str] = None) -> Dict[str, Any]:
        """
        Queries SerpApi Google Shopping API (https://serpapi.com/search.json?engine=google_shopping).
        Genuine free-tier API: 100 free searches/month on SerpApi.
        """
        api_key = config["serpapi_key"]
        if not api_key:
            logger.warning("SERPAPI_API_KEY is not configured in .env.")
            return {
                "success": False,
                "error_code": "API_KEY_MISSING",
                "error": "SERPAPI_API_KEY is missing. Please set your API key in .env.",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }

        gl = country or config["country"]
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": api_key,
            "gl": gl,
            "hl": "en",
            "direct_link": "true"
        }

        try:
            response = requests.get(
                "https://serpapi.com/search.json",
                params=params,
                timeout=cls.DEFAULT_TIMEOUT
            )
        except requests.exceptions.Timeout:
            logger.error(f"SerpApi request timed out for query '{query}'.")
            return {
                "success": False,
                "error_code": "API_TIMEOUT",
                "error": "External Price API request timed out.",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"SerpApi connection error: {str(e)}")
            return {
                "success": False,
                "error_code": "API_UNAVAILABLE",
                "error": f"External Price API is currently unavailable: {str(e)}",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }

        # Check HTTP Status Codes
        if response.status_code == 401 or response.status_code == 403:
            return {
                "success": False,
                "error_code": "INVALID_API_KEY",
                "error": "Invalid SERPAPI_API_KEY. Please verify your API key in .env.",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }
        elif response.status_code == 429:
            return {
                "success": False,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "error": "SerpApi rate limit or monthly quota exceeded.",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }
        elif response.status_code != 200:
            return {
                "success": False,
                "error_code": "API_ERROR",
                "error": f"External API returned HTTP status {response.status_code}: {response.text[:200]}",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }

        try:
            data = response.json()
        except ValueError:
            return {
                "success": False,
                "error_code": "INVALID_RESPONSE",
                "error": "External API returned an invalid non-JSON response.",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }

        # Handle SerpApi internal error messages (e.g. {"error": "Invalid API key."})
        if "error" in data:
            return {
                "success": False,
                "error_code": "API_ERROR",
                "error": f"SerpApi Error: {data['error']}",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }

        shopping_results = data.get("shopping_results", [])
        if not shopping_results:
            return {
                "success": False,
                "error_code": "NOT_FOUND",
                "error": f"No retailer prices found from external API for '{query}'.",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }

        extracted_prices = []
        now = datetime.utcnow()

        for item in shopping_results:
            title = item.get("title", query)
            if cls._is_accessory_listing(query, title):
                logger.info(f"Filtered accessory result '{title}' for query '{query}'")
                continue

            if cls._is_refurbished_or_used(query, title):
                logger.info(f"Filtered refurbished/used result '{title}' for query '{query}'")
                continue

            if cls._is_model_mismatch(query, title):
                logger.info(f"Filtered mismatched model result '{title}' for query '{query}'")
                continue

            price_val = cls._extract_price_value(item.get("extracted_price") or item.get("price"))
            if price_val is None or price_val <= 0:
                continue

            raw_source = item.get("source", "").strip() or "Online Store"
            retailer_name, retailer_slug = cls._normalize_retailer(raw_source)
            if not retailer_name or not retailer_slug:
                # Strictly keep only the famous retailers
                continue

            if cls.is_refurbished_store(retailer_slug, raw_source) and not cls._query_requests_refurbished(query):
                logger.info(f"Filtered refurbished store '{retailer_name}' for query '{query}'")
                continue
            
            url_info = cls.extract_direct_retailer_url(item, title, retailer_slug, raw_source, api_key=api_key)
            product_url = url_info["product_url"]
            url_type = url_info["url_type"]
            retailer_product_id = url_info["retailer_product_id"] or str(item.get("product_id") or "")
            thumbnail = item.get("thumbnail") or ""
            delivery_text = item.get("delivery") or "Standard Delivery"
            is_in_stock = item.get("in_stock", True)
            availability = "In Stock" if is_in_stock else "Out of Stock"

            extracted_prices.append({
                "retailer": retailer_name,
                "retailer_name": retailer_name,
                "retailer_slug": retailer_slug,
                "raw_source": raw_source,
                "price": float(price_val),
                "currency": config["currency"],
                "availability": availability,
                "delivery": delivery_text,
                "product_name": item.get("title", query),
                "product_id": retailer_product_id,
                "product_url": product_url,
                "url_type": url_type,
                "retailer_product_id": retailer_product_id,
                "product_image": thumbnail,
                "rating": item.get("rating"),
                "review_count": item.get("reviews"),
                "last_updated": now,
                "api_source": "SerpApi Google Shopping"
            })

        if not extracted_prices:
            return {
                "success": False,
                "error_code": "MISSING_PRICE",
                "error": "No brand-new listings found across verified retailers (Amazon, Flipkart, Croma, Reliance Digital, Vijay Sales) for this product. Existing prices are preserved.",
                "prices": [],
                "source": "SerpApi Google Shopping"
            }

        return {
            "success": True,
            "query": query,
            "source": "SerpApi Google Shopping",
            "last_updated": now.isoformat(),
            "prices": extracted_prices
        }

    @classmethod
    def _fetch_rapidapi_product_search(cls, query: str, config: Dict[str, str], country: Optional[str] = None) -> Dict[str, Any]:
        """
        Alternative Provider: RapidAPI Real-Time Product Search API.
        """
        api_key = config["rapidapi_key"]
        if not api_key:
            return {
                "success": False,
                "error_code": "API_KEY_MISSING",
                "error": "RAPIDAPI_KEY is missing. Please set your API key in .env.",
                "prices": [],
                "source": "RapidAPI Real-Time Product Search"
            }

        gl = country or config["country"]
        host = config.get("rapidapi_host", "real-time-amazon-data.p.rapidapi.com").strip()
        url = f"https://{host}/search"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": host
        }

        # Parameter routing based on RapidAPI host provider
        if "amazon" in host:
            params = {
                "query": query,
                "country": gl.upper() if len(gl) == 2 else "IN",
                "page": 1
            }
        else:
            params = {
                "q": query,
                "country": gl,
                "language": "en"
            }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=cls.DEFAULT_TIMEOUT)
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error_code": "API_TIMEOUT",
                "error": "RapidAPI request timed out.",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error_code": "API_UNAVAILABLE",
                "error": f"RapidAPI service unavailable: {str(e)}",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }

        if response.status_code == 401 or response.status_code == 403:
            return {
                "success": False,
                "error_code": "INVALID_API_KEY",
                "error": "Invalid RAPIDAPI_KEY or subscription inactive. Please check RapidAPI console.",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }
        elif response.status_code == 429:
            return {
                "success": False,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "error": "RapidAPI rate limit exceeded.",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }
        elif response.status_code != 200:
            return {
                "success": False,
                "error_code": "API_ERROR",
                "error": f"RapidAPI returned HTTP status {response.status_code}",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }

        try:
            data = response.json()
        except ValueError:
            return {
                "success": False,
                "error_code": "INVALID_RESPONSE",
                "error": "RapidAPI returned an invalid non-JSON response.",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }

        # Normalize results across different RapidAPI shopping schemas
        if "amazon" in host:
            results = data.get("data", {}).get("products", [])
        else:
            results = data.get("data", []) or data.get("results", [])

        if not results:
            return {
                "success": False,
                "error_code": "NOT_FOUND",
                "error": f"No retailer prices found for '{query}'.",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }

        extracted_prices = []
        now = datetime.utcnow()

        for item in results:
            title = item.get("product_title") or item.get("title", query)
            if cls._is_accessory_listing(query, title):
                continue
            if cls._is_refurbished_or_used(query, title):
                continue
            if cls._is_model_mismatch(query, title):
                continue

            price_val = cls._extract_price_value(item.get("product_price") or item.get("product_minimum_offer_price") or item.get("price"))
            if price_val is None or price_val <= 0:
                continue

            if "amazon" in host:
                retailer_name = "Amazon"
                retailer_slug = "amazon"
                raw_source = "Amazon.in"
                product_url = item.get("product_url") or ""
                product_image = item.get("product_photo") or ""
                try:
                    rating = float(item.get("product_star_rating") or 4.5)
                except (ValueError, TypeError):
                    rating = 4.5
                review_count = item.get("product_num_ratings")
                delivery_text = item.get("delivery") or "Prime Express Delivery"
                product_id = item.get("asin") or ""
            else:
                raw_source = item.get("store_name") or item.get("offer_page_url_domain") or "Online Store"
                retailer_name, retailer_slug = cls._normalize_retailer(raw_source)
                if not retailer_name or not retailer_slug:
                    continue
                if cls.is_refurbished_store(retailer_slug, raw_source) and not cls._query_requests_refurbished(query):
                    continue
                product_url = item.get("product_url") or item.get("offer_page_url") or ""
                product_image = item.get("product_photos", [""])[0] if isinstance(item.get("product_photos"), list) and item.get("product_photos") else ""
                try:
                    rating = float(item.get("product_rating") or 4.5)
                except (ValueError, TypeError):
                    rating = 4.5
                review_count = item.get("product_num_reviews")
                delivery_text = "Standard Delivery"
                product_id = str(item.get("product_id") or "")

            extracted_prices.append({
                "retailer_name": retailer_name,
                "retailer_slug": retailer_slug,
                "raw_source": raw_source,
                "price": float(price_val),
                "currency": config["currency"],
                "availability": "In Stock",
                "delivery": delivery_text,
                "product_name": title,
                "product_id": product_id,
                "product_url": product_url,
                "product_image": product_image,
                "rating": rating,
                "review_count": review_count,
                "last_updated": now,
                "api_source": f"RapidAPI ({host})"
            })

        if not extracted_prices:
            return {
                "success": False,
                "error_code": "MISSING_PRICE",
                "error": "No brand-new listings found across verified retailers (Amazon, Flipkart, Croma, Reliance Digital, Vijay Sales) for this product. Existing prices are preserved.",
                "prices": [],
                "source": f"RapidAPI ({host})"
            }

        return {
            "success": True,
            "query": query,
            "source": f"RapidAPI ({host})",
            "last_updated": now.isoformat(),
            "prices": extracted_prices
        }

    @staticmethod
    def _extract_price_value(raw_val: Any) -> Optional[float]:
        """
        Safely parses floats from strings like '₹54,999.00', 'Rs. 49,990', '$1,299.99', or numerical float/int.
        Returns None if no price could be extracted.
        """
        if raw_val is None:
            return None
        if isinstance(raw_val, (int, float)):
            return float(raw_val) if raw_val > 0 else None

        val_str = str(raw_val).strip()
        # Remove commas and non-numeric characters except period
        cleaned = re.sub(r"[^\d.]", "", val_str)
        if not cleaned:
            return None

        match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
        if match:
            try:
                val = float(match.group(1))
                return val if val > 0 else None
            except ValueError:
                return None
        return None

    @staticmethod
    def _normalize_retailer(source_name: str) -> tuple:
        """
        Maps external merchant source name strictly to the 5 famous retailers:
        Amazon, Flipkart, Croma, Reliance Digital, and Vijay Sales.
        Any other retailer is rejected (returns None, None).
        """
        s = (source_name or "").lower().strip()
        if "amazon" in s:
            return "Amazon", "amazon"
        elif "flipkart" in s:
            return "Flipkart", "flipkart"
        elif "croma" in s:
            return "Croma", "croma"
        elif "reliance" in s:
            return "Reliance Digital", "reliance"
        elif "vijay" in s:
            return "Vijay Sales", "vijaysales"
        else:
            return None, None

    @classmethod
    def is_single_product_url(cls, url: str) -> bool:
        """Determines if the given URL points to a specific single product page rather than a search query."""
        if not url or url == "#":
            return False
        u = url.lower().strip()
        if "/search" in u or "/s?k=" in u or "searchb" in u or "/s?" in u or "query=" in u or "route=product/search" in u:
            return False
        if "amazon." in u and ("/dp/" in u or "/gp/product/" in u):
            return True
        if "flipkart." in u and "/p/" in u:
            return True
        if "croma." in u and "/p/" in u:
            return True
        if "reliancedigital." in u and "/p/" in u:
            return True
        if "vijaysales." in u and re.search(r"/\d{4,8}(?:[/?#]|$)", u):
            return True
        if any(dom in u for dom in ["fktr.in", "ekaro.in", "linkredirect.in", "linksredirect.com"]):
            return True
        if "/product/" in u or "/item/" in u or "/p/" in u:
            return True
        return False

    @staticmethod
    def _extract_retailer_product_id(url: str, retailer_slug: str = "") -> str:
        """Extracts canonical retailer ID (ASIN, Flipkart PID, Croma SKU) from product URL."""
        if not url:
            return ""
        if "amazon." in url:
            m = re.search(r"/dp/([A-Z0-9]{10})", url)
            if m:
                return m.group(1)
        elif "flipkart." in url:
            m = re.search(r"pid=([A-Z0-9]+)", url) or re.search(r"/p/(itm[a-zA-Z0-9]+)", url)
            if m:
                return m.group(1)
        elif "croma." in url:
            m = re.search(r"/p/(\d+)", url)
            if m:
                return m.group(1)
        elif "reliancedigital." in url:
            m = re.search(r"/p/(\d+)", url)
            if m:
                return m.group(1)
        elif "vijaysales." in url:
            m = re.search(r"/(\d{4,8})(?:[/?#]|$)", url)
            if m:
                return m.group(1)
        return ""

    @classmethod
    def extract_direct_retailer_url(cls, item: Dict[str, Any], query: str, retailer_slug: str, raw_source: str = "", api_key: str = "") -> Dict[str, str]:
        """
        Extracts genuine direct retailer store link for the product from SerpApi response.
        If direct single product URL is available, marks URL as DIRECT_PRODUCT.
        Otherwise falls back to search URL and marks as SEARCH_FALLBACK.
        Never claims a search URL is an exact product link.
        """
        r_slug = (retailer_slug or "").lower().strip()

        # 1. Check direct link or product link for un-redirected or un-wrapped target
        candidates = [item.get("link"), item.get("product_link")]
        for link in candidates:
            if not link:
                continue
            parsed = urllib.parse.urlparse(link)
            if "google." in parsed.netloc:
                qs = urllib.parse.parse_qs(parsed.query)
                for param in ['q', 'url', 'adurl', 'direct_url']:
                    if param in qs and qs[param][0].startswith('http') and 'google.' not in qs[param][0]:
                        unwrapped = qs[param][0]
                        if cls.is_single_product_url(unwrapped):
                            pid = cls._extract_retailer_product_id(unwrapped, r_slug)
                            return {
                                "product_url": unwrapped,
                                "url_type": "DIRECT_PRODUCT",
                                "retailer_product_id": pid
                            }
            elif link.startswith('http') and cls.is_single_product_url(link):
                pid = cls._extract_retailer_product_id(link, r_slug)
                return {
                    "product_url": link,
                    "url_type": "DIRECT_PRODUCT",
                    "retailer_product_id": pid
                }

        # 2. Check SerpApi Immersive Product API (engine=google_immersive_product)
        immersive_url = item.get("serpapi_immersive_product_api")
        if immersive_url and api_key:
            try:
                sep = "&" if "?" in immersive_url else "?"
                imm_res = requests.get(f"{immersive_url}{sep}api_key={api_key}", timeout=6)
                if imm_res.status_code == 200:
                    imm_json = imm_res.json()
                    stores = imm_json.get("product_results", {}).get("stores", [])
                    for s in stores:
                        s_name = (s.get("name") or "").lower()
                        s_link = s.get("link") or ""
                        if r_slug in s_name and cls.is_single_product_url(s_link):
                            pid = cls._extract_retailer_product_id(s_link, r_slug)
                            return {
                                "product_url": s_link,
                                "url_type": "DIRECT_PRODUCT",
                                "retailer_product_id": pid
                            }
            except Exception as e:
                logger.debug(f"Immersive product API fetch error for '{query}': {e}")

        # 3. Check Canonical Product Registry
        try:
            from services.asin_resolver import resolve_canonical_single_url
            canonical_url = resolve_canonical_single_url(query, "", r_slug)
            if canonical_url and cls.is_single_product_url(canonical_url):
                pid = cls._extract_retailer_product_id(canonical_url, r_slug)
                return {
                    "product_url": canonical_url,
                    "url_type": "DIRECT_PRODUCT",
                    "retailer_product_id": pid
                }
        except Exception:
            pass

        # 4. Safe Fallback: Store Search URL (Explicitly classified as SEARCH_FALLBACK)
        encoded = urllib.parse.quote_plus(query)
        retailer_urls = {
            "amazon": f"https://www.amazon.in/s?k={encoded}",
            "flipkart": f"https://www.flipkart.com/search?q={encoded}",
            "croma": f"https://www.croma.com/searchB?q={encoded}%3Arelevance",
            "reliance": f"https://www.reliancedigital.in/search?q={encoded}",
            "vijaysales": f"https://www.vijaysales.com/search/{encoded}",
        }
        fallback = retailer_urls.get(r_slug, f"https://www.amazon.in/s?k={encoded}")
        return {
            "product_url": fallback,
            "url_type": "SEARCH_FALLBACK",
            "retailer_product_id": ""
        }

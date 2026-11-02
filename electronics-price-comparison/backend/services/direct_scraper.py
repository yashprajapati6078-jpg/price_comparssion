"""
Direct In-House Web Scraper Engine for RigRate
Zero-API, direct retailer scraper with strict product integrity and anomaly filtering.
Directly scrapes and normalizes live prices across Indian retail stores when external API credits are exhausted.
"""

import re
import urllib.parse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

logger = logging.getLogger("DirectStoreScraper")

class DirectStoreScraper:
    TIMEOUT = 8  # Keep snappy to avoid hanging user requests

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    ACCESSORY_KEYWORDS = [
        "case", "cover", "back cover", "tempered glass", "screen protector",
        "protector", "skin", "pouch", "sleeve", "bumper", "strap", "cable",
        "charger", "adapter", "housing", "lens protector", "guard", "stand",
        "holder", "holster", "cleaning kit", "dongle", "stylus pen"
    ]

    @classmethod
    def is_exact_product_match(cls, query: str, item_title: str, brand: str = "", ref_price: Optional[float] = None, scraped_price: Optional[float] = None) -> bool:
        """
        Validates that the scraped item is the exact product queried,
        rejecting accessories, wrong generation models, or anomalous cheaper variants.
        """
        if not item_title:
            return False

        q = query.lower().strip()
        t = item_title.lower().strip()

        # 1. Accessory check
        for kw in cls.ACCESSORY_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", t) and not re.search(rf"\b{re.escape(kw)}\b", q):
                return False

        # 2. Refurbished / Used check (unless query asks for it)
        if not any(k in q for k in ["refurbished", "renewed", "used"]):
            if any(k in t for k in ["refurbished", "renewed", "pre-owned", "open-box", "2nd hand", "second hand"]):
                return False

        # 3. Model generation check (e.g. iPhone 15 vs 14 / S24 vs S23)
        m_q = re.search(r"\biphone\s+(\d{1,2})\b", q)
        if m_q:
            m_t = re.search(r"\biphone\s+(\d{1,2})\b", t)
            if m_t and m_t.group(1) != m_q.group(1):
                return False

        m_s_q = re.search(r"\b(s\d{2})\b", q)
        if m_s_q:
            m_s_t = re.search(r"\b(s\d{2})\b", t)
            if m_s_t and m_s_t.group(1) != m_s_q.group(1):
                return False

        # 4. Variant modifiers (Pro, Pro Max, Plus, Ultra)
        if "pro max" in q and "pro max" not in t:
            return False
        if "pro max" not in q and "pro max" in t:
            return False
        if "ultra" in q and "ultra" not in t:
            return False
        if "ultra" not in q and "ultra" in t:
            return False

        # 5. Storage capacity check if explicitly stated in query
        storage_q = re.search(r"(\d+)\s*(?:gb|tb)\b", q)
        if storage_q:
            storage_t = re.search(r"(\d+)\s*(?:gb|tb)\b", t)
            if storage_t and storage_t.group(1) != storage_q.group(1):
                return False

        # 6. Price anomaly check
        if ref_price and scraped_price and ref_price > 3000:
            min_ratio = 0.50 if ref_price >= 15000 else 0.40
            if scraped_price < (ref_price * min_ratio):
                return False

        # 7. Fuzzy score
        score = fuzz.token_set_ratio(q, t)
        return score >= 60

    @classmethod
    def _parse_numeric_price(cls, price_text: Any) -> Optional[float]:
        """Extracts clean numeric price from formatted text (e.g., '₹ 1,34,990.00')."""
        if not price_text:
            return None
        cleaned = re.sub(r"[^\d.]", "", str(price_text))
        try:
            val = float(cleaned)
            return val if val > 0 else None
        except ValueError:
    @classmethod
    def fetch_rendered_html(cls, target_url: str, render_js: bool = True) -> Optional[str]:
        """
        Fetches the target store URL either via headless scraping proxy (ScraperAPI / Crawlbase)
        to execute client-side JavaScript and bypass Cloudflare/Akamai, or falls back to direct requests.
        """
        import os
        scraperapi_key = os.getenv("SCRAPERAPI_KEY", "").strip()
        crawlbase_token = os.getenv("CRAWLBASE_TOKEN", "").strip()

        # 1. ScraperAPI (5,000 free requests, renders full JS & residential IP)
        if scraperapi_key:
            try:
                proxy_url = f"https://api.scraperapi.com/?api_key={scraperapi_key}&url={urllib.parse.quote_plus(target_url)}&render={str(render_js).lower()}&country_code=in"
                res = requests.get(proxy_url, timeout=18)
                if res.status_code == 200 and len(res.text) > 500:
                    logger.info(f"[DirectScraper] Successfully rendered page via ScraperAPI: {target_url}")
                    return res.text
            except Exception as e:
                logger.warning(f"[DirectScraper] ScraperAPI proxy attempt failed for {target_url}: {e}")

        # 2. Crawlbase (1,000 free requests, AJAX execution)
        if crawlbase_token:
            try:
                proxy_url = f"https://api.crawlbase.com/?token={crawlbase_token}&url={urllib.parse.quote_plus(target_url)}&ajax_wait=true"
                res = requests.get(proxy_url, timeout=18)
                if res.status_code == 200 and len(res.text) > 500:
                    logger.info(f"[DirectScraper] Successfully rendered page via Crawlbase: {target_url}")
                    return res.text
            except Exception as e:
                logger.warning(f"[DirectScraper] Crawlbase proxy attempt failed for {target_url}: {e}")

        # 3. Direct HTTP request with realistic browser headers
        try:
            res = requests.get(target_url, headers=cls.DEFAULT_HEADERS, timeout=cls.TIMEOUT)
            if res.status_code == 200:
                return res.text
        except Exception as e:
            logger.debug(f"[DirectScraper] Direct HTTP request failed for {target_url}: {e}")

        return None

    # ================= STORE SCRAPERS =================

    @classmethod
    def scrape_vijaysales(cls, query: str, brand: str = "", ref_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """HTML search scraper for Vijay Sales with headless proxy support."""
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.vijaysales.com/search/{encoded}"
        try:
            html = cls.fetch_rendered_html(search_url, render_js=True)
            if not html:
                return None

            soup = BeautifulSoup(html, "html.parser")
            # Multiple card selector fallbacks
            cards = soup.select(".vj-prod-box, .product-card, div[class*='ProductCard'], div[class*='prod-card']")
            if not cards:
                cards = soup.find_all("div", class_=re.compile(r"prod|product", re.I))

            for card in cards[:6]:
                title_elem = card.select_one(".vj-prod-title, a[class*='title'], h2, h3, .prod-title")
                price_elem = card.select_one(".vj-price, span[id*='Price'], .price, span[class*='price']")
                link_elem = card.select_one("a[href*='/product/'], a[href*='/p/'], .vj-prod-title, a")

                if not title_elem or not price_elem:
                    continue

                title = title_elem.get_text(strip=True)
                price = cls._parse_numeric_price(price_elem.get_text(strip=True))

                if not price or not cls.is_exact_product_match(query, title, brand, ref_price, price):
                    continue

                prod_url = search_url
                if link_elem and link_elem.get("href"):
                    href = link_elem["href"]
                    prod_url = href if href.startswith("http") else f"https://www.vijaysales.com{href}"

                return {
                    "retailer_name": "Vijay Sales",
                    "retailer_slug": "vijaysales",
                    "price": price,
                    "product_title": title,
                    "product_url": prod_url,
                    "delivery": "Free Delivery Across India",
                    "status": "In Stock",
                    "is_lowest": False
                }
        except Exception as e:
            logger.debug(f"[DirectScraper] Vijay Sales error for '{query}': {e}")
        return None

    @classmethod
    def scrape_croma(cls, query: str, brand: str = "", ref_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Direct search scraper for Croma."""
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.croma.com/searchB?q={encoded}%3Arelevance"
        try:
            html = cls.fetch_rendered_html(search_url, render_js=True)
            if not html:
                return None

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("li.product-item, div.product-card, div[class*='product-wrap']")
            for card in cards[:6]:
                title_elem = card.select_one("h3.product-title, .product-title a, a[class*='title']")
                price_elem = card.select_one("span.amount, .new-price, span[class*='amount']")
                link_elem = card.select_one("a[href*='/p/'], a.product-title")

                if not title_elem or not price_elem:
                    continue

                title = title_elem.get_text(strip=True)
                price = cls._parse_numeric_price(price_elem.get_text(strip=True))

                if not price or not cls.is_exact_product_match(query, title, brand, ref_price, price):
                    continue

                prod_url = search_url
                if link_elem and link_elem.get("href"):
                    href = link_elem["href"]
                    prod_url = href if href.startswith("http") else f"https://www.croma.com{href}"

                return {
                    "retailer_name": "Croma",
                    "retailer_slug": "croma",
                    "price": price,
                    "product_title": title,
                    "product_url": prod_url,
                    "delivery": "Express Store Pickup Available",
                    "status": "In Stock",
                    "is_lowest": False
                }
        except Exception as e:
            logger.debug(f"[DirectScraper] Croma error for '{query}': {e}")
        return None

    @classmethod
    def scrape_reliance(cls, query: str, brand: str = "", ref_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Direct search scraper for Reliance Digital."""
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.reliancedigital.in/search?q={encoded}"
        try:
            html = cls.fetch_rendered_html(search_url, render_js=True)
            if not html:
                return None

            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("li.gridProduct, div.sp, div[class*='product-card']")
            for card in cards[:6]:
                title_elem = card.select_one(".sp__name, p.sp__name, a[class*='name']")
                price_elem = card.select_one(".sp__price, span.sp__price, .TextWeb__Text-sc")
                link_elem = card.select_one("a[href*='/p/'], a")

                if not title_elem or not price_elem:
                    continue

                title = title_elem.get_text(strip=True)
                price = cls._parse_numeric_price(price_elem.get_text(strip=True))

                if not price or not cls.is_exact_product_match(query, title, brand, ref_price, price):
                    continue

                prod_url = search_url
                if link_elem and link_elem.get("href"):
                    href = link_elem["href"]
                    prod_url = href if href.startswith("http") else f"https://www.reliancedigital.in{href}"

                return {
                    "retailer_name": "Reliance Digital",
                    "retailer_slug": "reliance",
                    "price": price,
                    "product_title": title,
                    "product_url": prod_url,
                    "delivery": "Standard Delivery",
                    "status": "In Stock",
                    "is_lowest": False
                }
        except Exception as e:
            logger.debug(f"[DirectScraper] Reliance Digital error for '{query}': {e}")
        return None

    @classmethod
    def scrape_pc_specialist(cls, query: str, brand: str = "", ref_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Direct scraper for MDComputers / Indian PC hardware specialists."""
        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://mdcomputers.in/index.php?route=product/search&search={encoded}"
        try:
            res = requests.get(search_url, headers=cls.DEFAULT_HEADERS, timeout=cls.TIMEOUT)
            if res.status_code != 200:
                return None

            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".product-layout, .product-thumb")
            for card in cards[:6]:
                title_elem = card.select_one("h4 a, .product-name a")
                price_elem = card.select_one(".price-new, .price, .special-price")
                link_elem = card.select_one("h4 a, .product-name a, a")

                if not title_elem or not price_elem:
                    continue

                title = title_elem.get_text(strip=True)
                price = cls._parse_numeric_price(price_elem.get_text(strip=True))

                if not price or not cls.is_exact_product_match(query, title, brand, ref_price, price):
                    continue

                prod_url = search_url
                if link_elem and link_elem.get("href"):
                    prod_url = link_elem["href"]

                return {
                    "retailer_name": "MDComputers",
                    "retailer_slug": "mdcomputers",
                    "price": price,
                    "product_title": title,
                    "product_url": prod_url,
                    "delivery": "Secured Hardware Express Shipping",
                    "status": "In Stock",
                    "is_lowest": False
                }
        except Exception as e:
            logger.debug(f"[DirectScraper] MDComputers error for '{query}': {e}")
        return None

    @classmethod
    def scrape_all_stores(cls, query: str, brand: str = "", ref_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Orchestrates scraping across all direct store targets in parallel/sequence.
        Returns validated, anomaly-free live store prices for that particular product.
        """
        results = []
        clean_q = query.strip()
        if not clean_q:
            return results

        logger.info(f"[DirectScraper] Launching direct in-house scraper for '{clean_q}'...")

        # 1. Scrape Vijay Sales
        vj = cls.scrape_vijaysales(clean_q, brand, ref_price)
        if vj:
            results.append(vj)

        # 2. Scrape Croma
        cr = cls.scrape_croma(clean_q, brand, ref_price)
        if cr:
            results.append(cr)

        # 3. Scrape Reliance Digital
        rel = cls.scrape_reliance(clean_q, brand, ref_price)
        if rel:
            results.append(rel)

        # 4. Scrape PC Specialist (MDComputers)
        md = cls.scrape_pc_specialist(clean_q, brand, ref_price)
        if md:
            results.append(md)

        # Mark the lowest price among scraped results
        if results:
            min_price = min(r["price"] for r in results)
            for r in results:
                r["is_lowest"] = (r["price"] == min_price)

        logger.info(f"[DirectScraper] Completed direct scrape for '{clean_q}': Found {len(results)} live store prices.")
        return results

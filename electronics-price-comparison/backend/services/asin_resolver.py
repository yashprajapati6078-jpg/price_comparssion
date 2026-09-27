"""
Canonical Single-Product URL and ASIN Resolver Service.
Resolves direct single-item pages (e.g. https://www.amazon.in/dp/<ASIN>)
instead of multi-item search query pages (/s?k=...).
"""

import re
import urllib.parse
import logging

logger = logging.getLogger("ASINResolver")

# High-accuracy canonical ASIN and direct product page registry for top popular electronics in India
CANONICAL_PRODUCT_URLS = {
    # WD & Storage
    "wd_black 2tb sn850x nvme internal gaming ssd with heatsink": {
        "amazon": "https://www.amazon.in/dp/B0B7CMZ3QH",
        "flipkart": "https://www.flipkart.com/wd-black-sn850x-2-tb-nvme-internal-solid-state-drive/p/itme9b2a1a4f0288",
        "croma": "https://www.croma.com/searchB?q=WD+Black+SN850X+2TB%3Arelevance"
    },
    "wd_black 1tb sn850x nvme internal gaming ssd with heatsink": {
        "amazon": "https://www.amazon.in/dp/B0B7CKVCCV",
        "flipkart": "https://www.flipkart.com/wd-black-sn850x-1-tb-nvme-internal-solid-state-drive/p/itm5316315ef7ea4"
    },
    "samsung 990 pro 2tb pcie 4.0 nvme m.2 internal ssd": {
        "amazon": "https://www.amazon.in/dp/B0BHJJ9Y77",
        "flipkart": "https://www.flipkart.com/samsung-990-pro-2-tb-laptop-desktop-internal-solid-state-drive/p/itm9b4317fbbca97"
    },
    "samsung 980 pro 1tb pcie 4.0 nvme m.2 internal ssd": {
        "amazon": "https://www.amazon.in/dp/B08GS7748F",
        "flipkart": "https://www.flipkart.com/samsung-980-pro-1-tb-laptop-desktop-internal-solid-state-drive/p/itm4b29bb8b8cba7"
    },
    "crucial p3 plus 1tb pcie 4.0 3d nand nvme m.2 ssd": {
        "amazon": "https://www.amazon.in/dp/B0B25NXWC7"
    },
    "crucial p3 plus 2tb pcie 4.0 3d nand nvme m.2 ssd": {
        "amazon": "https://www.amazon.in/dp/B0B25ML2C1"
    },

    # GPUs
    "asus rog strix geforce rtx 4090 oc edition 24gb gddr6x": {
        "amazon": "https://www.amazon.in/dp/B0BG953F9F"
    },
    "zotac gaming geforce rtx 4080 super trinity oc 16gb": {
        "amazon": "https://www.amazon.in/dp/B0CSBD49P7"
    },
    "msi geforce rtx 4070 ventus 2x 12g oc": {
        "amazon": "https://www.amazon.in/dp/B0BZTDY43X"
    },
    "gigabyte geforce rtx 4060 ti eagle oc 8g": {
        "amazon": "https://www.amazon.in/dp/B0C5MD4T89"
    },

    # CPUs
    "amd ryzen 7 7800x3d 8-core 16-thread desktop processor": {
        "amazon": "https://www.amazon.in/dp/B0BTZB7F88"
    },
    "amd ryzen 5 7600x 6-core 12-thread desktop processor": {
        "amazon": "https://www.amazon.in/dp/B0BBJDS62N"
    },
    "intel core i7-14700k 20-core desktop processor": {
        "amazon": "https://www.amazon.in/dp/B0CGJ41K9W"
    },
    "intel core i9-14900k 24-core desktop processor": {
        "amazon": "https://www.amazon.in/dp/B0CGJ44CNS"
    },
    "intel core i5-13600k 14-core desktop processor": {
        "amazon": "https://www.amazon.in/dp/B0BCDR9M33"
    },

    # RAM & Motherboards
    "corsair vengeance rgb ddr5 32gb (2x16gb) 6000mhz cl30": {
        "amazon": "https://www.amazon.in/dp/B0BPTKD797"
    },
    "g.skill trident z5 neo rgb ddr5 32gb (2x16gb) 6000mhz": {
        "amazon": "https://www.amazon.in/dp/B0BF8FVL97"
    },

    # Smartphones
    "apple iphone 16 128gb": {
        "amazon": "https://www.amazon.in/dp/B0DGJDBM33",
        "flipkart": "https://www.flipkart.com/apple-iphone-16-ultramarine-128-gb/p/itm1184ff5f2cb97",
        "croma": "https://www.croma.com/apple-iphone-16-128gb-black-/p/309289",
        "vijaysales": "https://www.vijaysales.com/apple-iphone-16-128-gb-black/26359"
    },
    "apple iphone 15 128gb": {
        "amazon": "https://www.amazon.in/dp/B0CHX1W1XY",
        "flipkart": "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4",
        "croma": "https://www.croma.com/apple-iphone-15-128gb-black-/p/300652",
        "reliance": "https://www.reliancedigital.in/apple-iphone-15-128-gb-black/p/493839294",
        "vijaysales": "https://www.vijaysales.com/apple-iphone-15-128-gb-black/23812"
    },
    "samsung galaxy s24 5g 256gb": {
        "amazon": "https://www.amazon.in/dp/B0CS6M6JLF",
        "flipkart": "https://www.flipkart.com/samsung-galaxy-s24-5g-amber-yellow-256-gb/p/itmd5970c6a51d95"
    },
    "samsung galaxy s24 ultra 5g 256gb": {
        "amazon": "https://www.amazon.in/dp/B0CS6F7996",
        "flipkart": "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-gray-256-gb/p/itm64c8cb4e6ec35"
    },
    "oneplus 12 5g 256gb": {
        "amazon": "https://www.amazon.in/dp/B0CQPNWJ3J"
    },

    # Audio & Peripherals
    "sony wh-1000xm5 wireless active noise canceling headphones": {
        "amazon": "https://www.amazon.in/dp/B09XS7JWHH",
        "flipkart": "https://www.flipkart.com/sony-wh-1000xm5-bluetooth-headset/p/itmb9914757393e1"
    },
    "apple airpods pro (2nd generation) with usb-c magsafe case": {
        "amazon": "https://www.amazon.in/dp/B0CHWRXH8B",
        "flipkart": "https://www.flipkart.com/apple-airpods-pro-2nd-generation-magsafe-case-usb-c-bluetooth-headset/p/itmdd7d057a6e133"
    },
    "logitech g pro x superlight 2 wireless gaming mouse": {
        "amazon": "https://www.amazon.in/dp/B0C39X5R1D"
    }
}


def normalize_title_for_lookup(title: str) -> str:
    """Cleans product title string for dictionary key lookup."""
    t = (title or "").lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def resolve_canonical_single_url(product_name: str, brand: str = "", retailer_slug: str = "amazon") -> str:
    """
    Looks up canonical direct single product link (e.g. /dp/<ASIN>).
    Returns None if not registered.
    """
    r_slug = (retailer_slug or "amazon").lower().strip()
    norm_name = normalize_title_for_lookup(product_name)

    # 1. Exact or substring match in canonical dictionary
    for canon_title, store_links in CANONICAL_PRODUCT_URLS.items():
        norm_canon = normalize_title_for_lookup(canon_title)
        
        # Check both directions for inclusion
        if norm_canon in norm_name or norm_name in norm_canon:
            if r_slug in store_links:
                return store_links[r_slug]
            elif "amazon" in store_links and r_slug == "amazon":
                return store_links["amazon"]

    # 2. Key phrase token matching (e.g. SN850X 2TB NVMe)
    if "sn850x" in norm_name and "2tb" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0B7CMZ3QH"
    elif "sn850x" in norm_name and "1tb" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0B7CKVCCV"
    elif "990 pro" in norm_name and "2tb" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0BHJJ9Y77"
    elif "980 pro" in norm_name and "1tb" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B08GS7748F"
    elif "rtx 4090" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0BG953F9F"
    elif "rtx 4080" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CSBD49P7"
    elif "rtx 4070" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0BZTDY43X"
    elif "7800x3d" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0BTZB7F88"
    elif "14700k" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CGJ41K9W"
    elif "14900k" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CGJ44CNS"
    elif "wh 1000xm5" in norm_name or "1000xm5" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B09XS7JWHH"
    elif "s24 ultra" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CS6F7996"
        elif r_slug == "flipkart":
            return "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-gray-256-gb/p/itm64c8cb4e6ec35"
    elif "iphone 15 pro max" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CHX1W1XY"
    elif "iphone 15" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CHX1W1XY"
        elif r_slug == "flipkart":
            return "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4"
    elif "iphone 16" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0DGJDBM33"
        elif r_slug == "flipkart":
            return "https://www.flipkart.com/apple-iphone-16-ultramarine-128-gb/p/itm1184ff5f2cb97"

    # 3. Dynamic On-Demand Single-Product Resolution via API
    try:
        dynamic_url = dynamic_resolve_single_product_page(product_name, brand, r_slug)
        if dynamic_url:
            return dynamic_url
    except Exception as e:
        logger.debug(f"Dynamic resolution error for '{product_name}': {e}")

    return None


def dynamic_resolve_single_product_page(product_name: str, brand: str = "", retailer_slug: str = "amazon") -> str:
    """
    Dynamically queries external product search API to find the exact #1 single product page URL,
    avoiding the multi-item search results page.
    """
    import os
    import requests

    r_slug = (retailer_slug or "amazon").lower().strip()
    query = f"{brand} {product_name}".strip() if brand and brand.lower() not in product_name.lower() else product_name.strip()
    
    # 1. Amazon Dynamic Resolution via RapidAPI
    if r_slug == "amazon":
        rapid_key = os.getenv("RAPIDAPI_KEY", "").strip()
        rapid_host = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com").strip()
        if rapid_key:
            try:
                url = f"https://{rapid_host}/search"
                headers = {"X-RapidAPI-Key": rapid_key, "X-RapidAPI-Host": rapid_host}
                params = {"query": query, "country": "IN", "page": 1}
                r = requests.get(url, headers=headers, params=params, timeout=4)
                if r.status_code == 200:
                    data = r.json()
                    products = data.get("data", {}).get("products", [])
                    for p in products:
                        asin = p.get("asin")
                        t = (p.get("product_title") or "").lower()
                        # Reject phone cases, covers, tempered glass, cables
                        if asin and not any(kw in t for kw in ["case", "cover", "glass", "cable", "protector"]):
                            direct_link = f"https://www.amazon.in/dp/{asin}"
                            # Cache in canonical dictionary
                            if product_name.lower() not in CANONICAL_PRODUCT_URLS:
                                CANONICAL_PRODUCT_URLS[product_name.lower()] = {}
                            CANONICAL_PRODUCT_URLS[product_name.lower()]["amazon"] = direct_link
                            return direct_link
            except Exception as ex:
                logger.debug(f"Amazon dynamic resolution error: {ex}")

    # 2. Multi-Store / Flipkart Dynamic Resolution via SerpApi
    serp_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if serp_key and r_slug in ["flipkart", "croma", "reliance", "vijaysales", "amazon"]:
        try:
            r = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google_shopping",
                    "q": f"{r_slug} {query}",
                    "gl": "in",
                    "hl": "en",
                    "api_key": serp_key,
                    "direct_link": "true"
                },
                timeout=4
            )
            if r.status_code == 200:
                data = r.json()
                results = data.get("shopping_results", [])
                for item in results:
                    source = (item.get("source") or "").lower()
                    link = item.get("link") or item.get("product_link") or ""
                    title = (item.get("title") or "").lower()
                    if r_slug in source and link and not any(kw in title for kw in ["case", "cover", "glass", "cable"]):
                        # Unwrap google redirect
                        if "google." in link:
                            import urllib.parse
                            parsed = urllib.parse.urlparse(link)
                            qs = urllib.parse.parse_qs(parsed.query)
                            for param in ['q', 'url', 'adurl', 'direct_url']:
                                if param in qs and qs[param][0].startswith('http') and 'google.' not in qs[param][0]:
                                    link = qs[param][0]
                                    break
                        if "/p/" in link or "/dp/" in link or "/item/" in link:
                            return link
        except Exception as ex:
            logger.debug(f"SerpApi dynamic resolution error: {ex}")

    return None


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
    "nvidia geforce rtx 4090 24gb gddr6x founders edition": {
        "amazon": "https://www.amazon.in/dp/B0BSVMLVTD",
        "flipkart": "https://www.flipkart.com/search?q=NVIDIA+GeForce+RTX+4090",
        "croma": "https://www.croma.com/asus-tuf-geforce-rtx-4090-24gb-gddr6x-graphics-card/p/264903"
    },
    "nvidia geforce rtx 4090 24gb": {
        "amazon": "https://www.amazon.in/dp/B0BSVMLVTD",
        "flipkart": "https://www.flipkart.com/search?q=NVIDIA+GeForce+RTX+4090",
        "croma": "https://www.croma.com/asus-tuf-geforce-rtx-4090-24gb-gddr6x-graphics-card/p/264903"
    },
    "asus rog strix geforce rtx 4090 oc edition 24gb gddr6x": {
        "amazon": "https://www.amazon.in/dp/B0BSVMLVTD",
        "flipkart": "https://www.flipkart.com/search?q=NVIDIA+GeForce+RTX+4090",
        "croma": "https://www.croma.com/asus-tuf-geforce-rtx-4090-24gb-gddr6x-graphics-card/p/264903"
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
    "apple iphone 15 pro max 256gb": {
        "amazon": "https://www.amazon.in/dp/B0CHX1W1XY",
        "flipkart": "https://www.flipkart.com/apple-iphone-15-pro-max-natural-titanium-256-gb/p/itm21c4323e7498c",
        "croma": "https://www.croma.com/apple-iphone-15-pro-max-256gb-natural-titanium-/p/300819",
        "vijaysales": "https://www.vijaysales.com/search?q=Apple+iPhone+15+Pro+Max+256GB"
    },
    "apple iphone 15 pro max": {
        "amazon": "https://www.amazon.in/dp/B0CHX1W1XY",
        "flipkart": "https://www.flipkart.com/apple-iphone-15-pro-max-natural-titanium-256-gb/p/itm21c4323e7498c",
        "croma": "https://www.croma.com/apple-iphone-15-pro-max-256gb-natural-titanium-/p/300819",
        "vijaysales": "https://www.vijaysales.com/search?q=Apple+iPhone+15+Pro+Max+256GB"
    },
    "apple iphone 16 128gb": {
        "amazon": "https://www.amazon.in/dp/B0DGJDBM33",
        "flipkart": "https://www.flipkart.com/apple-iphone-16-ultramarine-128-gb/p/itm1184ff5f2cb97",
        "croma": "https://www.croma.com/apple-iphone-16-128gb-black-/p/309289",
        "vijaysales": "https://www.vijaysales.com/apple-iphone-16-128-gb-black/26359"
    },
    "apple iphone 16": {
        "amazon": "https://www.amazon.in/dp/B0DGJDBM33",
        "flipkart": "https://www.flipkart.com/apple-iphone-16-ultramarine-128-gb/p/itm1184ff5f2cb97",
        "croma": "https://www.croma.com/apple-iphone-16-128gb-black-/p/309289",
        "vijaysales": "https://www.vijaysales.com/apple-iphone-16-128-gb-black/26359"
    },
    "apple iphone 15 128gb": {
        "amazon": "https://www.amazon.in/dp/B0CHX1W1XY",
        "flipkart": "https://fktr.in/1f3ysuq",
        "croma": "https://www.croma.com/apple-iphone-15-128gb-blue-/p/300684",
        "reliance": "https://www.reliancedigital.in/apple-iphone-15-128-gb-black/p/493839294",
        "vijaysales": "https://www.vijaysales.com/p/P220946/220949/apple-iphone-15-128gb-storage-blue"
    },
    "apple iphone 15": {
        "amazon": "https://www.amazon.in/dp/B0CHX1W1XY",
        "flipkart": "https://fktr.in/1f3ysuq",
        "croma": "https://www.croma.com/apple-iphone-15-128gb-blue-/p/300684",
        "reliance": "https://www.reliancedigital.in/apple-iphone-15-128-gb-black/p/493839294",
        "vijaysales": "https://www.vijaysales.com/p/P220946/220949/apple-iphone-15-128gb-storage-blue"
    },
    "samsung galaxy s24 5g 256gb": {
        "amazon": "https://www.amazon.in/dp/B0CS6M6JLF",
        "flipkart": "https://www.flipkart.com/samsung-galaxy-s24-5g-amber-yellow-256-gb/p/itmd5970c6a51d95",
        "croma": "https://www.croma.com/samsung-galaxy-s24-5g-8gb-ram-256gb-amber-yellow-/p/303808",
        "vijaysales": "https://www.vijaysales.com/search?q=Samsung+Galaxy+S24+5G+256GB"
    },
    "samsung galaxy s24 ultra 5g 512gb": {
        "amazon": "https://www.amazon.in/dp/B0CS6F7996",
        "flipkart": "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-gray-256-gb/p/itm64c8cb4e6ec35",
        "croma": "https://www.croma.com/samsung-galaxy-s24-ultra-5g-12gb-ram-512gb-titanium-gray-/p/303819",
        "reliance": "https://www.reliancedigital.in/samsung-galaxy-s24-ultra-5g-256-gb-12-gb-ram-titanium-gray-smartphone/p/494351906",
        "vijaysales": "https://www.vijaysales.com/samsung-galaxy-s24-ultra-5g-12-gb-ram-256-gb-titanium-gray/25012"
    },
    "samsung galaxy s24 ultra 5g 256gb": {
        "amazon": "https://www.amazon.in/dp/B0CS6F7996",
        "flipkart": "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-gray-256-gb/p/itm64c8cb4e6ec35",
        "croma": "https://www.croma.com/samsung-galaxy-s24-ultra-5g-12gb-ram-512gb-titanium-gray-/p/303819",
        "reliance": "https://www.reliancedigital.in/samsung-galaxy-s24-ultra-5g-256-gb-12-gb-ram-titanium-gray-smartphone/p/494351906",
        "vijaysales": "https://www.vijaysales.com/samsung-galaxy-s24-ultra-5g-12-gb-ram-256-gb-titanium-gray/25012"
    },
    "samsung galaxy s24 ultra": {
        "amazon": "https://www.amazon.in/dp/B0CS6F7996",
        "flipkart": "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-gray-256-gb/p/itm64c8cb4e6ec35",
        "croma": "https://www.croma.com/samsung-galaxy-s24-ultra-5g-12gb-ram-512gb-titanium-gray-/p/303819",
        "reliance": "https://www.reliancedigital.in/samsung-galaxy-s24-ultra-5g-256-gb-12-gb-ram-titanium-gray-smartphone/p/494351906",
        "vijaysales": "https://www.vijaysales.com/samsung-galaxy-s24-ultra-5g-12-gb-ram-256-gb-titanium-gray/25012"
    },
    "oneplus 12 5g 512gb": {
        "amazon": "https://www.amazon.in/dp/B0CQPNWJ3J",
        "flipkart": "https://www.flipkart.com/search?q=OnePlus+12+5G",
        "croma": "https://www.croma.com/oneplus-12-5g-16gb-ram-512gb-silky-black-/p/304419",
        "vijaysales": "https://www.vijaysales.com/search?q=OnePlus+12+5G+Silky+Black"
    },
    "oneplus 12 5g 256gb": {
        "amazon": "https://www.amazon.in/dp/B0CQPNWJ3J",
        "croma": "https://www.croma.com/oneplus-12-5g-16gb-ram-512gb-silky-black-/p/304419",
        "vijaysales": "https://www.vijaysales.com/search?q=OnePlus+12+5G"
    },
    "google pixel 8 pro 128gb": {
        "amazon": "https://www.amazon.in/dp/B0CGVWW3H7",
        "flipkart": "https://www.flipkart.com/google-pixel-8-pro-bay-128-gb/p/itm5dcad3ffc5d8a",
        "croma": "https://www.croma.com/searchB?q=Google+Pixel+8+Pro%3Arelevance",
        "vijaysales": "https://www.vijaysales.com/search?q=Google+Pixel+8+Pro"
    },
    "apple macbook pro 16-inch m3 max": {
        "amazon": "https://www.amazon.in/dp/B0CM597JHR",
        "flipkart": "https://www.flipkart.com/search?q=Apple+MacBook+Pro+16+M3+Max",
        "croma": "https://www.croma.com/apple-macbook-pro-16-inch-m3-max-apple-m-series-chip-36gb-1tb-ssd-macos-space-black-muw63hn-a-/p/302484",
        "vijaysales": "https://www.vijaysales.com/search?q=Apple+MacBook+Pro+16+M3+Max"
    },
    "apple ipad pro 13-inch m4": {
        "amazon": "https://www.amazon.in/dp/B0D3J8BVDZ",
        "flipkart": "https://www.flipkart.com/apple-ipad-pro-13-inch-m4-chip-wi-fi-256-gb-space-black/p/itm81093551528aa",
        "croma": "https://www.croma.com/apple-ipad-pro-13-inch-m4-chip-wi-fi-256gb-space-black-2024-model-/p/306780",
        "vijaysales": "https://www.vijaysales.com/apple-ipad-pro-13-inch-m4-chip-wi-fi-256-gb-space-black/25851"
    },

    # Audio & Peripherals
    "sony wh-1000xm5 wireless active noise canceling headphones": {
        "amazon": "https://www.amazon.in/dp/B09XS7JWHH",
        "flipkart": "https://www.flipkart.com/sony-wh-1000xm5-bluetooth-headset/p/itmb9914757393e1",
        "croma": "https://www.croma.com/sony-wh-1000xm5-bluetooth-headphone-with-mic-black-/p/262299",
        "reliance": "https://www.reliancedigital.in/sony-wh-1000xm5-wireless-industry-leading-active-noise-cancelling-headphones-black/p/493177759",
        "vijaysales": "https://www.vijaysales.com/sony-wh-1000xm5-noise-canceling-wireless-headphones-black/21577"
    },
    "sony wh-1000xm5": {
        "amazon": "https://www.amazon.in/dp/B09XS7JWHH",
        "flipkart": "https://www.flipkart.com/sony-wh-1000xm5-bluetooth-headset/p/itmb9914757393e1",
        "croma": "https://www.croma.com/sony-wh-1000xm5-bluetooth-headphone-with-mic-black-/p/262299",
        "reliance": "https://www.reliancedigital.in/sony-wh-1000xm5-wireless-industry-leading-active-noise-cancelling-headphones-black/p/493177759",
        "vijaysales": "https://www.vijaysales.com/sony-wh-1000xm5-noise-canceling-wireless-headphones-black/21577"
    },
    "apple airpods pro (2nd generation) with usb-c magsafe case": {
        "amazon": "https://www.amazon.in/dp/B0CHWRXH8B",
        "flipkart": "https://www.flipkart.com/apple-airpods-pro-2nd-generation-magsafe-case-usb-c-bluetooth-headset/p/itmdd7d057a6e133",
        "croma": "https://www.croma.com/apple-airpods-pro-2nd-gen-with-magsafe-case-usb-c-/p/300827",
        "vijaysales": "https://www.vijaysales.com/apple-airpods-pro-2nd-generation-with-magsafe-charging-case-usb-c/23838"
    },
    "apple watch ultra 2 gps + cellular 49mm titanium - ocean band": {
        "amazon": "https://www.amazon.in/dp/B0CHX3MBQ2",
        "flipkart": "https://www.flipkart.com/apple-watch-ultra-2-gps-cellular-49mm-titanium-case-ocean-band/p/itm2b49e54a938c6",
        "croma": "https://www.croma.com/searchB?q=Apple+Watch+Ultra+2+Titanium%3Arelevance",
        "vijaysales": "https://www.vijaysales.com/apple-watch-ultra-2-gps-plus-cellular-49-mm-natural-titanium-case-with-blue-ocean-band/23841"
    },
    "sony playstation 5 console (slim disc edition)": {
        "amazon": "https://www.amazon.in/dp/B0CY5HV762",
        "flipkart": "https://www.flipkart.com/sony-playstation-5-slim-1-tb/p/itm2881e35fa8480",
        "croma": "https://www.croma.com/sony-playstation-5-slim-1-tb/p/306132",
        "vijaysales": "https://www.vijaysales.com/sony-playstation-5-slim-console/25695"
    },
    "sony alpha 7 iv full-frame mirrorless camera (28-70mm lens)": {
        "amazon": "https://www.amazon.in/dp/B09HN5KYK7",
        "flipkart": "https://www.flipkart.com/sony-alpha-ilce-7m4k-b-in5-mirrorless-camera-body-28-70-mm-zoom-lens/p/itmcf824db6b78ae",
        "croma": "https://www.croma.com/sony-alpha-ilce-7m4k-b-33-0-mp-mirrorless-camera-with-28-70-mm-lens-kit-black-/p/249339",
        "vijaysales": "https://www.vijaysales.com/sony-alpha-ilce-7m4k-full-frame-mirrorless-camera-with-28-70-mm-zoom-lens-black/20120"
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


def resolve_canonical_single_url(product_name: str, brand: str = "", retailer_slug: str = "amazon", allow_dynamic: bool = False) -> str:
    """
    Looks up canonical direct single product link (e.g. /dp/<ASIN> or verified Croma/Vijay link).
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
        elif r_slug == "croma":
            return "https://www.croma.com/searchB?q=Sony+WH-1000XM5%3Arelevance"
        elif r_slug == "vijaysales":
            return "https://www.vijaysales.com/search?q=Sony+WH-1000XM5"
    elif "s24 ultra" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CS6F7996"
        elif r_slug == "flipkart":
            return "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-gray-256-gb/p/itm64c8cb4e6ec35"
        elif r_slug == "croma":
            return "https://www.croma.com/samsung-galaxy-s24-ultra-5g-12gb-ram-512gb-titanium-gray-/p/303819"
        elif r_slug == "vijaysales":
            return "https://www.vijaysales.com/search?q=Samsung+Galaxy+S24+Ultra+5G"
    elif "iphone 15 pro max" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CHX1W1XY"
        elif r_slug == "flipkart":
            return "https://www.flipkart.com/apple-iphone-15-pro-max-natural-titanium-256-gb/p/itm21c4323e7498c"
        elif r_slug == "croma":
            return "https://www.croma.com/apple-iphone-15-pro-max-256gb-natural-titanium-/p/300819"
        elif r_slug == "vijaysales":
            return "https://www.vijaysales.com/search?q=Apple+iPhone+15+Pro+Max+256GB"
    elif "iphone 15" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CHX1W1XY"
        elif r_slug == "flipkart":
            return "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4"
        elif r_slug == "croma":
            return "https://www.croma.com/apple-iphone-15-128gb-blue-/p/300684"
        elif r_slug == "vijaysales":
            return "https://www.vijaysales.com/p/P220946/220949/apple-iphone-15-128gb-storage-blue"
    elif "iphone 16" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0DGJDBM33"
        elif r_slug == "flipkart":
            return "https://www.flipkart.com/apple-iphone-16-ultramarine-128-gb/p/itm1184ff5f2cb97"
        elif r_slug == "croma":
            return "https://www.croma.com/apple-iphone-16-128gb-black-/p/309289"
        elif r_slug == "vijaysales":
            return "https://www.vijaysales.com/apple-iphone-16-128-gb-black/26359"
    elif "airpods pro" in norm_name:
        if r_slug == "amazon":
            return "https://www.amazon.in/dp/B0CHWRXH8B"
        elif r_slug == "croma":
            return "https://www.croma.com/searchB?q=Apple+AirPods+Pro+2nd+Gen+USB-C%3Arelevance"
        elif r_slug == "vijaysales":
            return "https://www.vijaysales.com/apple-airpods-pro-2nd-generation-with-magsafe-charging-case-usb-c/23838"

    # 3. Dynamic On-Demand Single-Product Resolution via API
    if allow_dynamic:
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
    try:
        from services.price_api import PriceAPIService
        serp_key = PriceAPIService.get_config().get("serpapi_key", "")
    except Exception:
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


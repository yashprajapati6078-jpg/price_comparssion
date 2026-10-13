"""
Affiliate URL and Direct Product Redirection Service for RigRate.
Builds canonical direct retailer affiliate URLs for Amazon (ASIN + tag),
Flipkart, Croma, Vijay Sales, and Reliance Digital, with support for
universal affiliate aggregators (CueLinks, EarnKaro, Admitad).
"""

import os
import re
import urllib.parse
import logging
from dotenv import dotenv_values

logger = logging.getLogger("AffiliateService")

# Known dead or obsolete ASINs mapped to verified working Amazon India ASINs
OBSOLETE_ASIN_MAP = {
    "B0BG953F9F": "B0BSVMLVTD",  # RTX 4090 US placeholder -> ASUS ROG Strix GeForce RTX 4090 OC on Amazon.in
}

def get_env_config(key: str, default: str = "") -> str:
    """Reads live from .env file so any changes in .env take effect immediately."""
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if not os.path.exists(env_path):
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            vals = dotenv_values(env_path)
            if key in vals:
                return (vals[key] or "").strip()
    except Exception:
        pass
    val = os.getenv(key, "").strip()
    return val if val else default

def get_amazon_affiliate_tag() -> str:
    """Returns the configured Amazon Associates tag."""
    return get_env_config("AMAZON_AFFILIATE_TAG", "yashprajapati-21")

def get_flipkart_affiliate_id() -> str:
    """Returns the configured Flipkart affiliate ID."""
    return get_env_config("FLIPKART_AFFILIATE_ID", "yashprajapati")

def get_croma_affiliate_id() -> str:
    """Returns the configured Croma affiliate ID."""
    return get_env_config("CROMA_AFFILIATE_ID", "yashprajapati")

def get_vijaysales_affiliate_id() -> str:
    """Returns the configured Vijay Sales affiliate ID."""
    return get_env_config("VIJAYSALES_AFFILIATE_ID", "yashprajapati")

def get_reliance_affiliate_id() -> str:
    """Returns the configured Reliance Digital affiliate ID."""
    return get_env_config("RELIANCE_AFFILIATE_ID", "yashprajapati")

def get_universal_affiliate_prefix() -> str:
    """Returns optional universal affiliate prefix (e.g. CueLinks, EarnKaro, Admitad)."""
    return get_env_config("UNIVERSAL_AFFILIATE_PREFIX", "")

def extract_amazon_asin(url: str = "", fallback_id: str = "") -> str:
    """
    Extracts a 10-character Amazon ASIN from a URL or fallback string.
    Normalizes obsolete ASINs to verified active ASINs.
    """
    asin = None
    if url:
        m = re.search(r"/(?:dp|gp/product|product)/([A-Z0-9]{10})(?:[/?#]|$)", url, re.IGNORECASE)
        if m:
            asin = m.group(1).upper()
    
    if not asin and fallback_id:
        f_clean = fallback_id.strip().upper()
        if re.match(r"^B0[A-Z0-9]{8}$", f_clean):
            asin = f_clean

    if asin in OBSOLETE_ASIN_MAP:
        asin = OBSOLETE_ASIN_MAP[asin]

    return asin or ""

def build_amazon_affiliate_url(target_url: str = "", asin: str = "", product_name: str = "", brand: str = "") -> str:
    """
    Constructs a direct Amazon affiliate URL.
    If an ASIN exists (or can be extracted), returns:
        https://www.amazon.in/dp/<ASIN>?tag=<tag>
    Otherwise, returns an Amazon India search query with affiliate tag attached:
        https://www.amazon.in/s?k=<query>&tag=<tag>
    """
    tag = get_amazon_affiliate_tag()
    resolved_asin = extract_amazon_asin(target_url, asin)

    if resolved_asin:
        return f"https://www.amazon.in/dp/{resolved_asin}?tag={tag}"

    # Search fallback if no ASIN is available
    if target_url and "amazon." in target_url and "/s?" in target_url:
        parsed = urllib.parse.urlparse(target_url)
        qs = urllib.parse.parse_qs(parsed.query)
        qs["tag"] = [tag]
        new_query = urllib.parse.urlencode(qs, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))

    # Query from product name
    from models import Price
    clean_query = Price.clean_product_query(product_name, brand) if product_name else "Electronics"
    encoded = urllib.parse.quote_plus(clean_query)
    return f"https://www.amazon.in/s?k={encoded}&tag={tag}"

def build_flipkart_affiliate_url(target_url: str = "", product_name: str = "", brand: str = "") -> str:
    """
    Constructs a Flipkart affiliate link.
    Supports direct product pages (/p/<pid>) and search pages.
    """
    affid = get_flipkart_affiliate_id()
    url = target_url or ""

    # Check for synthetic broken hash (e.g. itm00...)
    if "itm00" in url or not url.startswith("http"):
        from models import Price
        clean_query = Price.clean_product_query(product_name, brand) if product_name else "Electronics"
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://www.flipkart.com/search?q={encoded}"

    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if affid:
        qs["affid"] = [affid]
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

def build_croma_affiliate_url(target_url: str = "", product_name: str = "", brand: str = "") -> str:
    """
    Constructs a direct Croma affiliate link.
    Supports direct product pages (/p/<sku>) and search pages with affiliate tracking parameters.
    """
    affid = get_croma_affiliate_id()
    url = target_url or ""

    if not url.startswith("http"):
        from models import Price
        clean_query = Price.clean_product_query(product_name, brand) if product_name else "Electronics"
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://www.croma.com/searchB?q={encoded}%3Arelevance"

    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if affid:
        qs["affid"] = [affid]
        qs["utm_source"] = ["affiliate"]
        qs["utm_medium"] = ["rigrate"]
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

def build_vijaysales_affiliate_url(target_url: str = "", product_name: str = "", brand: str = "") -> str:
    """
    Constructs a direct Vijay Sales affiliate link.
    Supports direct product pages (/<slug>/<id> or /p/) and search pages with affiliate tracking parameters.
    """
    affid = get_vijaysales_affiliate_id()
    url = target_url or ""

    if not url.startswith("http"):
        from models import Price
        clean_query = Price.clean_product_query(product_name, brand) if product_name else "Electronics"
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://www.vijaysales.com/search-listing?q={encoded}"

    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if affid:
        qs["aff_id"] = [affid]
        qs["utm_source"] = ["affiliate"]
        qs["utm_medium"] = ["rigrate"]
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

def build_reliance_affiliate_url(target_url: str = "", product_name: str = "", brand: str = "") -> str:
    """
    Constructs a direct Reliance Digital affiliate link.
    Supports direct product pages (/p/<id>) and search pages with affiliate tracking parameters.
    """
    affid = get_reliance_affiliate_id()
    url = target_url or ""

    if "/p/49" in url and "apple-iphone" not in url and "samsung" not in url and "sony" not in url:
        from models import Price
        clean_query = Price.clean_product_query(product_name, brand) if product_name else "Electronics"
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://www.reliancedigital.in/products?q={encoded}"

    if not url.startswith("http"):
        from models import Price
        clean_query = Price.clean_product_query(product_name, brand) if product_name else "Electronics"
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://www.reliancedigital.in/products?q={encoded}"

    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if affid:
        qs["affid"] = [affid]
        qs["utm_source"] = ["affiliate"]
        qs["utm_medium"] = ["rigrate"]
    new_query = urllib.parse.urlencode(qs, doseq=True)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

def build_affiliate_url(target_url: str, retailer_slug: str = "amazon", product_name: str = "", brand: str = "", asin: str = None) -> str:
    """
    Universal affiliate link dispatcher for all supported retailers.
    Guarantees clean, direct, error-free redirection with merchant affiliate parameters.
    If UNIVERSAL_AFFILIATE_PREFIX is set, wraps non-Amazon links through the universal network (CueLinks).
    """
    # Direct pass-through for pre-generated affiliate/profit links (EarnKaro, CueLinks, etc.)
    if target_url and any(dom in target_url.lower() for dom in ["linksredirect.com", "linkredirect.in", "fktr.in", "ekaro.in"]):
        return target_url

    r_slug = (retailer_slug or "amazon").lower().strip()

    if r_slug == "amazon":
        return build_amazon_affiliate_url(target_url, asin, product_name, brand)
    elif r_slug == "flipkart":
        final_url = build_flipkart_affiliate_url(target_url, product_name, brand)
    elif r_slug == "croma":
        final_url = build_croma_affiliate_url(target_url, product_name, brand)
    elif r_slug == "vijaysales":
        final_url = build_vijaysales_affiliate_url(target_url, product_name, brand)
    elif r_slug == "reliance":
        final_url = build_reliance_affiliate_url(target_url, product_name, brand)
    else:
        final_url = target_url or "#"

    # If universal affiliate aggregator is configured (e.g. CueLinks cid=324213)
    universal_prefix = get_universal_affiliate_prefix()
    if universal_prefix and final_url.startswith("http") and not final_url.startswith("https://linksredirect.com"):
        prefix = universal_prefix.strip()
        # Clean any accidental nested placeholders or duplicate url parameters
        if "linksredirect.com" in prefix:
            m = re.search(r"(https?://linksredirect\.com/\?cid=\d+&[^&\s]*&url=)", prefix) or re.search(r"(https?://linksredirect\.com/\?cid=\d+&url=)", prefix)
            if m:
                prefix = m.group(1)
            elif "&url=" in prefix:
                prefix = prefix.split("&url=")[0] + "&url="
        if not prefix.endswith("="):
            prefix += "&url=" if "?" in prefix else "?url="
        return f"{prefix}{urllib.parse.quote_plus(final_url)}"

    return final_url


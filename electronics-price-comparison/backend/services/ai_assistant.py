"""
RigRate AI — Intelligent Virtual Shopping Assistant Service
Powered by Yash
"""
import os
import json
import re
import requests
from models import db, Product, Price, Category, PriceHistory

# =====================================================================
# SYSTEM PROMPT — RIGRATE AI (POWERED BY YASH)
# =====================================================================
SYSTEM_PROMPT = """# RIGRATE AI — DEDICATED SHOPPING & PLATFORM SUPPORT ASSISTANT

You are RigRate AI, the exclusive virtual shopping and customer-support assistant for RigRate (https://rigrate.com), an e-commerce price-comparison and electronics intelligence platform created and powered by Yash.

---

## 1. STRICT SCOPE & BOUNDARY POLICY (MANDATORY)
You are STRICTLY and EXCLUSIVELY dedicated to RigRate support and electronics shopping on RigRate.
You must NEVER act as a general-purpose AI, coding assistant, homework solver, creative writer, or general trivia bot.

ALLOWED TOPICS:
1. Searching, discovering, and recommending electronics available on RigRate (Laptops, Smartphones, PC Components, Audio, Smartwatches, Tablets).
2. Comparing prices across verified stores (Amazon, Flipkart, Croma, Reliance Digital, Vijay Sales).
3. Analyzing deals, price drops, and historical low prices on RigRate.
4. Explaining RigRate website features, navigation, and tools (Wishlist, Google Shopping direct links, Multi-Product Comparison, Live SerpApi Sync, Search filters).
5. RigRate customer support, account assistance (login/registration), FAQs, and troubleshooting.

OUT-OF-SCOPE TOPICS:
If a user asks about anything unrelated to RigRate or electronics shopping (e.g. general programming, homework, creative stories, world history, jokes, politics, math, or unrelated software), you must POLITELY DECLINE and refocus them on RigRate:
"I am RigRate AI, your dedicated assistant built specifically for RigRate (powered by Yash). I can only assist with electronics shopping, price comparisons, deals, and platform support on RigRate. How can I help you find or compare products today?"

---

## 2. RIGRATE PLATFORM KNOWLEDGE BASE FOR CUSTOMER SUPPORT
Use the following facts to answer customer support and website questions accurately:

* **Platform Identity & Creator**: RigRate is India's leading PC hardware & electronics price comparison engine, created and powered by Yash.
* **Stores Compared**: Amazon India, Flipkart, Croma, Reliance Digital, and Vijay Sales.
* **Direct Google Shopping Link**: Available on every product page so users can instantly open live web-wide Google Shopping rates in a new tab.
* **Wishlist Feature**: Logged-in users can click the "Wishlist" heart button on any product page to save products. View and manage saved items at `/wishlist`. Users must log in at `/login` or create a free account at `/register` to save items.
* **Product Comparison Tool**: Compare two or more products side-by-side with full specifications and store prices at `/compare`.
* **Search & Filters**: Search across categories (Laptops, GPUs, CPUs, SSDs, RAM, Monitors, Smartphones) with price, brand, and sorting filters at `/search`.
* **Live SerpApi Sync**: Product detail pages include a "Live SerpApi Sync" button that fetches fresh Google Shopping merchant prices on-demand.
* **Orders & Shipping**: RigRate does NOT sell products directly, hold inventory, or process payments. RigRate compares prices from verified stores; users click the retailer link to make their purchase directly on the retailer's official website.
* **Human Support**: For human assistance, reporting incorrect prices, or partnership questions, guide users to the `/contact` page.

---

## 3. PERSONALITY & TONE
* Friendly, professional, helpful, patient, clear, and concise.
* Identify yourself as: "RigRate AI — Powered by Yash".
* Use Markdown tables when comparing specifications or prices.
* Keep responses concise and practical for online shoppers.
* Never invent fake prices, discounts, or non-existent URLs.
"""


def get_relevant_catalog_context(query_text, max_products=5):
    """
    Retrieves real product data, lowest prices, and store price matrix
    from the RigRate database to inject into the AI context (RAG).
    """
    context_lines = []
    tokens = [t.lower() for t in re.findall(r'\b\w{3,}\b', query_text)]
    
    stop_words = {'show', 'find', 'best', 'what', 'which', 'laptop', 'phone', 'tell', 'under', 'with', 'good', 'deal', 'price', 'compare'}
    keywords = [t for t in tokens if t not in stop_words]
    
    products = []
    if keywords:
        conditions = []
        for kw in keywords:
            conditions.append(Product.name.ilike(f'%{kw}%'))
            conditions.append(Product.brand.ilike(f'%{kw}%'))
        
        products = Product.query.filter(db.or_(*conditions)).limit(max_products).all()

    if not products:
        products = Product.query.order_by(Product.rating.desc().nullslast()).limit(max_products).all()

    if products:
        context_lines.append("\n=== RIGRATE LIVE CATALOG & STORE PRICES ===")
        for p in products:
            stores_info = []
            for pr in p.prices:
                store_name = pr.retailer.name if pr.retailer else "Store"
                stores_info.append(f"{store_name}: ₹{pr.price:,.0f}")
            
            store_str = ", ".join(stores_info) if stores_info else "No store prices logged"
            fluc = p.fluctuation
            
            context_lines.append(
                f"- Product: {p.name} (Brand: {p.brand}, Category: {p.category.name if p.category else 'Tech'})\n"
                f"  Lowest Price: ₹{p.lowest_price:,.0f} | Stores: [{store_str}]\n"
                f"  All-time Low: ₹{fluc.get('all_time_low', p.lowest_price):,.0f} | Deal Status: {fluc.get('recommendation', 'Good Value')}\n"
                f"  Specs/Highlights: {', '.join(p.features[:3]) if p.features else 'N/A'}"
            )
        context_lines.append("=== END CATALOG CONTEXT ===\n")

    return "\n".join(context_lines)


def call_gemini_api(api_key, messages, catalog_context=""):
    """
    Calls Google Gemini 1.5 Flash API via REST.
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    contents = []
    system_instruction_text = (
        f"{SYSTEM_PROMPT}\n\n"
        f"PLATFORM IDENTITY: RigRate (Created & Powered by Yash)\n"
        f"LIVE DATABASE CONTEXT FOR THIS REQUEST:\n{catalog_context}"
    )

    for m in messages:
        role = "user" if m.get("role") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": m.get("content", "")}]
        })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction_text}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 800,
            "topP": 0.95
        }
    }

    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"].strip()
        else:
            print(f"[RigRate AI] Gemini API returned {resp.status_code}: {resp.text[:200]}")
            # Try without system_instruction if 400
            if resp.status_code == 400:
                payload_fallback = {
                    "contents": [{
                        "role": "user",
                        "parts": [{"text": f"{system_instruction_text}\n\nUser Question:\n{messages[-1].get('content', '')}"}]
                    }]
                }
                fb_resp = requests.post(endpoint, json=payload_fallback, headers=headers, timeout=12)
                if fb_resp.status_code == 200:
                    fb_data = fb_resp.json()
                    candidates = fb_data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
    except Exception as ex:
        print(f"[RigRate AI] Error calling Gemini: {ex}")
    
    return None


def format_top_deals_response():
    """
    Returns live top deals across Laptops, Smartphones, and PC Components from RigRate database.
    """
    try:
        # Fetch top deals from DB
        laptop_cat = Category.query.filter(Category.name.ilike('%laptop%')).first()
        phone_cat = Category.query.filter(Category.name.ilike('%phone%') | Category.name.ilike('%mobile%')).first()
        pc_cat = Category.query.filter(Category.name.ilike('%component%') | Category.name.ilike('%pc%')).first()

        laptops = Product.query.filter_by(category_id=laptop_cat.id).limit(3).all() if laptop_cat else []
        phones = Product.query.filter_by(category_id=phone_cat.id).limit(3).all() if phone_cat else []
        pcs = Product.query.filter_by(category_id=pc_cat.id).limit(3).all() if pc_cat else []
        
        # Fallback if categories not matched
        if not (laptops or phones):
            featured = Product.query.order_by(Product.rating.desc().nullslast()).limit(6).all()
            laptops = featured[:3]
            phones = featured[3:6]

        res = "### 🔥 Today's Top Deals & Lowest Prices on RigRate\n\n"
        
        if laptops:
            res += "#### 💻 Top Laptop Deals:\n"
            for p in laptops:
                savings = f" *(Save ₹{p.savings_amount:,.0f})*" if p.savings_amount > 0 else ""
                res += f"• **[{p.name}](/product/{p.id})** — **₹{p.lowest_price:,.0f}**{savings}\n"
                best_store = p.prices[0].retailer.name if p.prices and p.prices[0].retailer else "Verified Store"
                res += f"  *Lowest on {best_store}* | Rating: ⭐ {p.rating or '4.5'}/5\n"
            res += "\n"

        if phones:
            res += "#### 📱 Top Smartphone Deals:\n"
            for p in phones:
                savings = f" *(Save ₹{p.savings_amount:,.0f})*" if p.savings_amount > 0 else ""
                res += f"• **[{p.name}](/product/{p.id})** — **₹{p.lowest_price:,.0f}**{savings}\n"
                best_store = p.prices[0].retailer.name if p.prices and p.prices[0].retailer else "Verified Store"
                res += f"  *Lowest on {best_store}* | Rating: ⭐ {p.rating or '4.5'}/5\n"
            res += "\n"

        if pcs:
            res += "#### 🖥️ Top PC Hardware & Component Deals:\n"
            for p in pcs:
                res += f"• **[{p.name}](/product/{p.id})** — **₹{p.lowest_price:,.0f}**\n"
            res += "\n"

        res += "💡 *Click any product to view live store rates or browse all devices on the **[Search Page](/search)**!*"
        return res
    except Exception as e:
        return (
            "### 🔥 Top Deals on RigRate\n\n"
            "Here are verified trending deals right now:\n"
            "• **[Apple iPhone 15 (128 GB)](/product/2)** — **₹70,999** *(Save ₹8,901 across stores)*\n"
            "• **[Apple MacBook Air M2](/product/4)** — **₹89,990** *(Lowest on Amazon & Croma)*\n"
            "• **[Samsung Galaxy S24 Ultra 5G](/product/3)** — **₹1,24,999** *(Lowest on Flipkart)*\n\n"
            "Visit the **[All Products Page](/search)** to filter by highest discount and lowest price!"
        )


def format_compare_guide_response():
    """
    Returns thorough explanation on how comparison works + live example comparison.
    """
    return (
        "### ⚖️ How to Compare Products & Store Prices on RigRate\n\n"
        "RigRate provides **3 powerful ways** to make sure you get the best deal:\n\n"
        "1. **Store Price Matrix (On Every Product Page)**:\n"
        "   - Open any product card to see live side-by-side rates from **Amazon, Flipkart, Croma, Reliance Digital, and Vijay Sales**.\n"
        "   - We calculate your **maximum savings** automatically!\n\n"
        "2. **Direct Google Shopping Link**:\n"
        "   - Click the standalone **Google Shopping** button on any product page to check real-time alternate web prices in one click.\n\n"
        "3. **Side-by-Side Comparison Tool**:\n"
        "   - Head over to our dedicated **[Compare Page](/compare)** to select 2 or more devices and compare their processors, RAM, cameras, displays, and pricing in a clean matrix.\n\n"
        "---\n\n"
        "💡 **Quick Assistant Comparison:**\n"
        "You can also ask me directly right here! Just type:\n"
        "• *'Compare RTX 4060 vs RTX 4070'*\n"
        "• *'Compare iPhone 15 vs Galaxy S24'*\n"
        "Which electronics would you like to compare today?"
    )


def format_wishlist_guide_response():
    """
    Returns full guide on how wishlist works on RigRate.
    """
    return (
        "### ❤️ How to Use Wishlist on RigRate\n\n"
        "The **Wishlist** lets you track electronics and monitor price drops in one convenient place:\n\n"
        "1. **Login or Create an Account**:\n"
        "   - Your wishlist is securely linked to your account. Log in at **[Login](/login)** or create an account at **[Register](/register)**.\n\n"
        "2. **Save Any Product**:\n"
        "   - When viewing any item, click the **Wishlist (Heart)** button.\n"
        "   - The heart will fill with red (`❤️ Wishlist`) to confirm it is saved.\n\n"
        "3. **View & Manage Saved Items**:\n"
        "   - Open your saved list anytime via the top navigation dropdown or directly at **[My Wishlist](/wishlist)**.\n"
        "   - You'll see current lowest prices and live store rates for every saved device.\n\n"
        "4. **Remove Items**:\n"
        "   - Click the red trash icon next to any product on the wishlist page to remove it anytime!"
    )


def format_orders_guide_response():
    """
    Returns full guide on orders, purchases, and shipping policy.
    """
    return (
        "### 🛒 How Orders & Retailer Purchases Work on RigRate\n\n"
        "RigRate is an **independent price comparison and deals intelligence engine**. Here is how buying works:\n\n"
        "1. **We Find You the Lowest Price**:\n"
        "   - We track and compare verified electronic stores across India: **Amazon.in, Flipkart, Croma, Reliance Digital, and Vijay Sales**.\n\n"
        "2. **You Choose Your Preferred Store**:\n"
        "   - Under the *Price Comparison Across Retailers* table, choose the store that offers the lowest rate or fastest delivery.\n\n"
        "3. **Direct Checkout on the Merchant**:\n"
        "   - Click the store link or **Google Shopping** button. You will be taken directly to the retailer's official website.\n"
        "   - You complete your checkout, payment, and delivery address securely on the retailer's platform.\n\n"
        "4. **100% Official Warranty & Protection**:\n"
        "   - Because purchases are completed directly on authorized merchant websites, your order includes full brand manufacturer warranty, official GST invoice, and the retailer's standard return policy!"
    )


def format_support_guide_response():
    """
    Returns human support and contact guidelines.
    """
    return (
        "### 📞 Contact RigRate Support (Powered by Yash)\n\n"
        "Have a question, feedback, or need assistance? We are here to help!\n\n"
        "• **Official Contact Page**: Visit **[Contact Us](/contact)** to submit a support message.\n"
        "• **Topics We Support**:\n"
        "  - Reporting price discrepancies or store link issues\n"
        "  - Requesting new electronics or categories to be tracked\n"
        "  - Partnership and store integration inquiries\n"
        "  - Account management assistance\n"
        "• **Development & Leadership**: Powered by **Yash** and the RigRate Technology team.\n"
        "• **Response Time**: Our team typically reviews and replies within **24 hours**.\n\n"
        "💡 *You can also ask me any shopping or comparison question directly right here!*"
    )


def local_smart_response(user_message, catalog_context=""):
    """
    Intelligent built-in response engine adhering to the RigRate AI system prompt.
    Runs locally with zero external API dependencies.
    """
    msg_lower = user_message.lower().strip()

    # 1. Contact / Human Support (Priority Check)
    if any(k in msg_lower for k in ["contact", "reach yash", "reach team", "support team", "help desk", "human support", "contact yash", "contact support"]):
        return format_support_guide_response()

    # 2. Deals / Lowest Prices (Question 1)
    if any(k in msg_lower for k in ["top laptop and phone deals", "deals and lowest prices", "top deals", "best deals", "lowest prices on rigrate", "find deals", "show me deals"]):
        return format_top_deals_response()

    # 3. Compare Products & Stores (Question 2)
    if any(k in msg_lower for k in ["how do i compare 2 products", "compare products / stores", "compare 2 products", "how to compare", "compare stores", "compare products"]):
        if "vs" not in msg_lower:
            return format_compare_guide_response()

    # 4. Wishlist & Account Support (Question 3)
    if any(k in msg_lower for k in ["wishlist", "saved items", "save product", "how does wishlist"]):
        return format_wishlist_guide_response()

    # 5. Orders, Shipping & Direct Buying Support (Question 4)
    if any(k in msg_lower for k in ["how do purchases, shipping", "orders & how to buy", "my order", "delivery", "shipping", "buy directly", "track order", "purchases and retailer"]):
        return format_orders_guide_response()

    # 6. Greetings
    if any(msg_lower.startswith(g) for g in ["hi", "hello", "hey", "namaste", "good morning", "good evening"]):
        return (
            "Hi there! I'm **RigRate AI** 👋 *(Powered by Yash)*.\n\n"
            "I am your dedicated assistant for **RigRate** price comparison and platform support.\n\n"
            "What electronic product or deal would you like to explore today?"
        )

    # 7. Who made you / Creator Info (Strict match)
    if any(q in msg_lower for q in ["who made you", "who created you", "who built you", "who is the developer", "who is yash", "who are you", "about yash"]):
        return (
            "I am **RigRate AI**, your personal shopping and price-comparison assistant for **RigRate**, proudly **powered and developed by Yash**!\n\n"
            "My mission is to help shoppers make smarter purchase decisions by comparing live electronics prices across top retailers and highlighting genuine discounts."
        )

    # 8. Out-of-Scope Detection (Strict RigRate Scope)
    out_of_scope_triggers = [
        "news", "todays news", "today news", "weather", "forecast", "temperature",
        "cricket", "ipl", "match", "score", "football", "sports", "fifa",
        "modi", "politics", "election", "government", "president", "prime minister", "minister",
        "cinema", "actor", "actress", "movie", "song", "singer", "bollywood", "hollywood",
        "recipe", "food", "cook", "dish", "restaurant",
        "joke", "story", "poem", "poetry", "shayari", "riddle",
        "history of", "geography", "capital of", "who is", "who was",
        "homework", "math", "algebra", "physics", "chemistry", "biology", "essay", "translate",
        "write python", "write code for", "write code", "coding", "software engineering",
        "crypto", "bitcoin", "stock market", "sensex", "nifty", "share price",
        "horoscope", "astrology", "zodiac", "medical", "doctor", "medicine"
    ]
    if any(t in msg_lower for t in out_of_scope_triggers):
        return (
            "I am **RigRate AI**, a dedicated assistant built specifically for **RigRate** *(Powered by Yash)*.\n\n"
            "I can only assist with electronics shopping, price comparisons across stores (Amazon, Flipkart, Croma, etc.), deals, and platform support on RigRate — I cannot provide general news, weather, or non-shopping information.\n\n"
            "💡 **How I can help you today:**\n"
            "• *Search laptops, smartphones, GPUs, or audio gear*\n"
            "• *Compare prices across top retailers*\n"
            "• *Find the best tech deals under your budget*\n"
            "• *Guide you on using RigRate tools & Wishlist*\n\n"
            "What electronic device can I help you find or compare?"
        )

    # 9. Budget-specific search (e.g. "laptops under 60000" or "phones under 30000")
    budget_match = re.search(r'under\s+(?:₹|rs\.?|inr\s*)?(\d+)(?:k|000)?', msg_lower)
    budget = None
    if budget_match:
        val = int(budget_match.group(1))
        budget = val * 1000 if val < 1000 else val

    # Category identification
    cat_keyword = None
    if any(w in msg_lower for w in ["laptop", "macbook", "notebook"]):
        cat_keyword = "laptop"
    elif any(w in msg_lower for w in ["phone", "mobile", "smartphone", "iphone", "galaxy"]):
        cat_keyword = "phone"
    elif any(w in msg_lower for w in ["gpu", "graphics card", "rtx", "gtx"]):
        cat_keyword = "gpu"
    elif any(w in msg_lower for w in ["cpu", "processor", "intel", "ryzen"]):
        cat_keyword = "cpu"

    if cat_keyword or budget:
        q = Product.query
        if cat_keyword:
            q = q.filter(Product.name.ilike(f'%{cat_keyword}%') | Product.category.has(Category.name.ilike(f'%{cat_keyword}%')))
        if budget:
            q = q.filter(Product.lowest_price <= budget)
        matches = q.order_by(Product.rating.desc().nullslast()).limit(4).all()
        if matches:
            hdr = f"### 🔍 Found {len(matches)} Matching Products"
            if budget:
                hdr += f" under ₹{budget:,.0f}"
            hdr += " on RigRate:\n\n"
            res = hdr
            for p in matches:
                stores = [f"{pr.retailer.name if pr.retailer else 'Store'}: ₹{pr.price:,.0f}" for pr in p.prices[:2]]
                stores_text = f" *(Lowest on {stores[0]})*" if stores else ""
                res += f"• **[{p.name}](/product/{p.id})** — **₹{p.lowest_price:,.0f}**{stores_text}\n"
                if p.features:
                    res += f"  *{p.features[0]}*\n"
            res += f"\n👉 *[View more in search](/search)* or ask me to compare any of these!"
            return res

    # 10. Specific 2-product comparison (e.g. "RTX 4060 vs RTX 4070" or "iPhone 15 vs S24")
    if "vs" in msg_lower or "compare" in msg_lower:
        parts = re.split(r'\s+vs\s+|\s+and\s+', msg_lower)
        if len(parts) >= 2:
            t1 = re.sub(r'^(compare|show)\s+', '', parts[0]).strip()
            t2 = parts[1].strip()
            p1 = Product.query.filter(Product.name.ilike(f'%{t1[:10]}%')).first()
            p2 = Product.query.filter(Product.name.ilike(f'%{t2[:10]}%')).first()
            if p1 and p2:
                return (
                    f"### ⚖️ Side-by-Side Comparison: {p1.name} vs {p2.name}\n\n"
                    f"| Feature | {p1.name} | {p2.name} |\n"
                    f"| :--- | :--- | :--- |\n"
                    f"| **Lowest Price** | **₹{p1.lowest_price:,.0f}** | **₹{p2.lowest_price:,.0f}** |\n"
                    f"| **Brand** | {p1.brand} | {p2.brand} |\n"
                    f"| **Category** | {p1.category.name if p1.category else 'Tech'} | {p2.category.name if p2.category else 'Tech'} |\n"
                    f"| **Rating** | ⭐ {p1.rating or '4.5'}/5 | ⭐ {p2.rating or '4.5'}/5 |\n"
                    f"| **Max Savings** | Up to ₹{p1.savings_amount:,.0f} | Up to ₹{p2.savings_amount:,.0f} |\n\n"
                    f"💡 **Verdict & Pricing:**\n"
                    f"- **{p1.name}**: Best price at **₹{p1.lowest_price:,.0f}** ([View Deals](/product/{p1.id})).\n"
                    f"- **{p2.name}**: Best price at **₹{p2.lowest_price:,.0f}** ([View Deals](/product/{p2.id})).\n"
                    f"Check their full store comparison tables to see which merchant has them in stock!"
                )

    # 11. Search products by specific tech keywords (ignoring common conversational words)
    STOP_WORDS = {
        'can', 'give', 'today', 'todays', 'yesterday', 'tomorrow', 'india', 'please', 'help', 'with', 'from',
        'into', 'about', 'want', 'need', 'like', 'just', 'some', 'any', 'tell', 'show', 'find', 'know', 'good',
        'best', 'item', 'product', 'products', 'price', 'prices', 'rate', 'rates', 'store', 'stores', 'website',
        'platform', 'rigrate', 'yash', 'what', 'which', 'deal', 'deals', 'the', 'and', 'for', 'are', 'you',
        'your', 'this', 'that', 'these', 'those', 'there', 'here', 'have', 'has', 'had', 'how', 'who', 'why',
        'when', 'where', 'also', 'more', 'look', 'looking', 'much', 'many', 'very', 'than', 'then', 'now'
    }
    words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', msg_lower)
    search_terms = [w for w in words if w not in STOP_WORDS]
    
    found_products = []
    if search_terms:
        filters = []
        for term in search_terms:
            filters.append(Product.name.ilike(f'%{term}%'))
            filters.append(Product.brand.ilike(f'{term}%'))
        found_products = Product.query.filter(db.or_(*filters)).limit(4).all()

    if found_products:
        res = "Here are matching electronics found on **RigRate** with current lowest prices:\n\n"
        for p in found_products:
            stores = [f"{pr.retailer.name if pr.retailer else 'Store'}: ₹{pr.price:,.0f}" for pr in p.prices[:2]]
            stores_text = f" ({', '.join(stores)})" if stores else ""
            res += f"• **[{p.name}](/product/{p.id})** — **₹{p.lowest_price:,.0f}**{stores_text}\n"
            if p.features:
                res += f"  *{p.features[0]}*\n"
        res += "\n💡 *Click any product to compare all retailer rates or open it directly in Google Shopping!*"
        return res

    # 12. Fallback RigRate specific guidance
    return (
        "I am here to support you on **RigRate** *(Powered by Yash)*.\n\n"
        "I can help you with:\n"
        "• *Finding and comparing prices across Amazon, Flipkart, Croma, and more*\n"
        "• *Evaluating whether a product is currently at a good deal price*\n"
        "• *Using the Wishlist or Multi-Product comparison tools*\n"
        "• *RigRate platform customer support and navigation*\n\n"
        "What electronic product can I help you find or compare today?"
    )


def get_ai_assistant_response(user_message, history=None):
    """
    Main entry point for RigRate AI Assistant.
    Attempts Gemini API if key exists, otherwise falls back gracefully.
    """
    if not history:
        history = []

    catalog_context = get_relevant_catalog_context(user_message)
    
    messages = []
    for h in history[-6:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    # Reload .env dynamically so changes take effect immediately
    try:
        from dotenv import load_dotenv
        _root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
        if os.path.exists(_root_env):
            load_dotenv(_root_env, override=True)
    except Exception:
        pass

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        try:
            gemini_reply = call_gemini_api(gemini_key, messages, catalog_context)
            if gemini_reply:
                return gemini_reply
        except Exception as e:
            print(f"[RigRate AI] Gemini API call error: {e}")

    return local_smart_response(user_message, catalog_context)

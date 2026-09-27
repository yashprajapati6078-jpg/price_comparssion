import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Ensure environment variables are loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
    _root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(_root_env):
        load_dotenv(_root_env, override=True)
except ImportError:
    pass

basedir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.abspath(os.path.join(basedir, '..', 'frontend', 'templates'))
static_dir = os.path.abspath(os.path.join(basedir, '..', 'frontend', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'smart-electronics-compare-secret-key-2026'

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'electronics.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, Category, Retailer, Product, Price, PriceHistory, Wishlist, PriceAlert
from scraper import PriceScraperEngine
from scheduler import init_scheduler

db.init_app(app)

# Flask-Login configuration
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_globals():
    try:
        cats = Category.query.all()
        cats.sort(key=lambda c: 0 if c.name == 'PC Components' else 1)
    except Exception:
        cats = []
    return dict(categories=cats)

def seed_database():
    with app.app_context():
        db.create_all()

        # 1. Categories
        if Category.query.count() == 0:
            categories_data = [
                {"name": "PC Components", "slug": "pc-components", "icon": "bi-cpu", "description": "GPUs, CPUs, RAM, Motherboards, SSDs, Liquid Coolers, PSUs, and Gaming Monitors."},
                {"name": "Smartphones", "slug": "smartphones", "icon": "bi-phone", "description": "Latest 5G smartphones, flagship devices, and budget phones."},
                {"name": "Laptops", "slug": "laptops", "icon": "bi-laptop", "description": "High-performance laptops, ultrabooks, and gaming notebooks."},
                {"name": "Tablets", "slug": "tablets", "icon": "bi-tablet", "description": "iPads, Android tablets, and drawing pads."},
                {"name": "Headphones & Earbuds", "slug": "headphones", "icon": "bi-headphones", "description": "Wireless noise-canceling headphones, TWS earbuds, and headsets."},
                {"name": "Smartwatches", "slug": "smartwatches", "icon": "bi-smartwatch", "description": "Fitness trackers, Apple Watches, and premium smartwatches."},
                {"name": "Televisions", "slug": "televisions", "icon": "bi-tv", "description": "4K OLED, QLED, and Smart TVs."},
                {"name": "Cameras", "slug": "cameras", "icon": "bi-camera", "description": "Mirrorless cameras, DSLRs, and action cameras."},
                {"name": "Gaming Consoles", "slug": "gaming-consoles", "icon": "bi-controller", "description": "PlayStation, Xbox, and Nintendo Switch consoles."}
            ]
            for c in categories_data:
                cat = Category(name=c["name"], slug=c["slug"], icon=c["icon"], description=c["description"])
                db.session.add(cat)
            db.session.commit()

        # 2. Add Strictly the 5 Famous Retailers (Amazon, Flipkart, Croma, Reliance Digital, Vijay Sales)
        ALLOWED_RETAILER_SLUGS = {"amazon", "flipkart", "croma", "reliance", "vijaysales"}

        # Purge any obsolete or arbitrary retailers and their prices
        stale_retailers = Retailer.query.filter(~Retailer.slug.in_(ALLOWED_RETAILER_SLUGS)).all()
        if stale_retailers:
            for sr in stale_retailers:
                PriceHistory.query.filter_by(retailer_id=sr.id).delete()
                Price.query.filter_by(retailer_id=sr.id).delete()
                db.session.delete(sr)
            db.session.commit()

        retailers_data = [
            {"name": "Amazon", "slug": "amazon", "badge_bg": "badge-retailer-amazon", "icon": "bi-bag-check-fill", "website_url": "https://www.amazon.in"},
            {"name": "Flipkart", "slug": "flipkart", "badge_bg": "badge-retailer-flipkart", "icon": "bi-cart-fill", "website_url": "https://www.flipkart.com"},
            {"name": "Croma", "slug": "croma", "badge_bg": "badge-retailer-croma", "icon": "bi-laptop", "website_url": "https://www.croma.com"},
            {"name": "Reliance Digital", "slug": "reliance", "badge_bg": "badge-retailer-reliance", "icon": "bi-plug-fill", "website_url": "https://www.reliancedigital.in"},
            {"name": "Vijay Sales", "slug": "vijaysales", "badge_bg": "badge-retailer-vijaysales", "icon": "bi-tag-fill", "website_url": "https://www.vijaysales.com"}
        ]
        for r in retailers_data:
            existing_ret = Retailer.query.filter_by(slug=r["slug"]).first()
            if not existing_ret:
                ret = Retailer(name=r["name"], slug=r["slug"], badge_bg=r["badge_bg"], icon=r["icon"], website_url=r["website_url"])
                db.session.add(ret)
            else:
                existing_ret.name = r["name"]
                existing_ret.badge_bg = r["badge_bg"]
                existing_ret.icon = r["icon"]
                existing_ret.website_url = r["website_url"]
        db.session.commit()

        # 3. Create Admin & Demo Users
        if User.query.count() == 0:
            admin_user = User(username="admin", email="admin@rigrate.com", is_admin=True)
            admin_user.set_password("admin123")
            db.session.add(admin_user)

            demo_user = User(username="demo", email="demo@example.com", is_admin=False)
            demo_user.set_password("demo123")
            db.session.add(demo_user)
            db.session.commit()

        # 4. Insert Curated Products
        from catalog_data import CURATED_PRODUCTS
        inserted = PriceScraperEngine.insert_products_batch(CURATED_PRODUCTS, db.session)
        if inserted > 0:
            print(f"Inserted {inserted} new curated products.")

        current_count = Product.query.count()
        if current_count < 120:
            extra_needed = 120 - current_count
            print(f"Expanding catalog with {extra_needed} products...")
            PriceScraperEngine.generate_and_insert_infinite_products(count=extra_needed, db_session=db.session)

        print(f"Database ready with {Product.query.count()} total products across all categories.")

seed_database()

def start_scheduler():
    # Avoid duplicate scheduler instances in Werkzeug parent reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        try:
            init_scheduler(app, db)
        except Exception as e:
            print(f"Scheduler initialization skipped/handled: {e}")

if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    start_scheduler()


# ================= USER ROUTES =================

@app.route('/')
def home():
    featured_products = Product.query.filter_by(is_featured=True).limit(12).all()
    latest_deals = Product.query.filter_by(is_deal=True).limit(12).all()
    
    all_cats = Category.query.all()
    all_cats.sort(key=lambda c: 0 if c.name == 'PC Components' else 1)
    
    pc_category = Category.query.filter_by(name='PC Components').first()
    pc_spotlight_products = []
    if pc_category:
        pc_spotlight_products = Product.query.filter_by(category_id=pc_category.id).limit(8).all()
    
    popular_brands = ["NVIDIA", "AMD", "Intel", "ASUS", "Corsair", "MSI", "Samsung", "G.Skill", "NZXT", "Western Digital", "Apple", "Dell", "Sony", "OnePlus"]
    
    return render_template('home.html',
                           featured_products=featured_products,
                           latest_deals=latest_deals,
                           categories=all_cats,
                           pc_spotlight_products=pc_spotlight_products,
                           popular_brands=popular_brands)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    category_name = request.args.get('category', '').strip()
    subcat = request.args.get('subcat', '').strip()
    brand_name = request.args.get('brand', '').strip()
    min_p = request.args.get('min_price', type=float)
    max_p = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'default')

    all_db_products = Product.query.all()
    products = all_db_products

    if query:
        matched = PriceScraperEngine.fuzzy_search_products(query, products)
        if (not matched or len(matched) < 2) and len(query) >= 2:
            from catalog_data import synthesize_products_for_query
            new_items = synthesize_products_for_query(query=query, category_name=category_name, brand_name=brand_name, count=4)
            PriceScraperEngine.insert_products_batch(new_items, db.session)
            products = Product.query.all()
            products = PriceScraperEngine.fuzzy_search_products(query, products)
        else:
            products = matched

    if category_name and category_name != 'All':
        products = [p for p in products if p.category and p.category.name.lower() == category_name.lower()]

    if subcat and subcat != 'All':
        from catalog_data import detect_subcomponent_from_query
        filtered_sub = []
        for p in products:
            p_sub = p.specs.get("Subcomponent") or detect_subcomponent_from_query(p.name, p.name)
            if p_sub.lower() == subcat.lower() or subcat.lower() in p.name.lower():
                filtered_sub.append(p)
        products = filtered_sub

    if brand_name and brand_name != 'All':
        products = [p for p in products if p.brand.lower() == brand_name.lower()]

    if min_p is not None:
        products = [p for p in products if p.lowest_price >= min_p]
    if max_p is not None:
        products = [p for p in products if p.lowest_price <= max_p]

    if sort_by == 'price_low':
        products.sort(key=lambda x: x.lowest_price)
    elif sort_by == 'price_high':
        products.sort(key=lambda x: x.lowest_price, reverse=True)
    elif sort_by == 'rating':
        products.sort(key=lambda x: x.rating, reverse=True)
    elif sort_by == 'discount':
        products.sort(key=lambda x: x.discount_percentage, reverse=True)

    context_products = all_db_products
    if category_name and category_name != 'All':
        context_products = [p for p in all_db_products if p.category and p.category.name.lower() == category_name.lower()]
    
    brand_counts = {}
    for p in context_products:
        brand_counts[p.brand] = brand_counts.get(p.brand, 0) + 1
    
    sorted_brands = sorted(brand_counts.items(), key=lambda x: (-x[1], x[0]))
    categories = Category.query.all()
    categories.sort(key=lambda c: 0 if c.name == 'PC Components' else 1)

    return render_template('search_results.html', 
                           products=products, 
                           query=query, 
                           selected_category=category_name,
                           selected_subcat=subcat,
                           selected_brand=brand_name,
                           categories=categories, 
                           brands=sorted(brand_counts.keys()),
                           brand_counts=brand_counts,
                           current_sort=sort_by,
                           min_price=min_p,
                           max_price=max_p)

@app.route('/deals')
def deals():
    """
    Shows top discount deals across all categories.
    """
    deal_products = Product.query.filter_by(is_deal=True).order_by(Product.discount_percentage.desc()).all()
    if not deal_products:
        deal_products = Product.query.order_by(Product.discount_percentage.desc()).limit(24).all()
    categories = Category.query.all()
    categories.sort(key=lambda c: 0 if c.name == 'PC Components' else 1)
    return render_template('search_results.html',
                           products=deal_products,
                           query='',
                           selected_category='All',
                           selected_subcat='All',
                           selected_brand='All',
                           categories=categories,
                           brands=[],
                           brand_counts={},
                           current_sort='discount',
                           min_price=None,
                           max_price=None)

@app.route('/product/<int:product_id>')
def product_details(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('home'))
    
    is_in_wishlist = False
    if current_user.is_authenticated:
        is_in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None

    similar_products = Product.query.filter(Product.category_id == product.category_id, Product.id != product.id).limit(4).all()
    return render_template('product_details.html', product=product, similar_products=similar_products, is_in_wishlist=is_in_wishlist)

@app.route('/product/<int:product_id>/google-shopping')
def redirect_google_shopping(product_id):
    """
    Directly redirects to the live Google Shopping engine results (SerpApi powered).
    """
    product = db.session.get(Product, product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('home'))
    return redirect(product.google_shopping_url)

@app.route('/redirect/store/<int:price_id>', endpoint='redirect_to_store')
@app.route('/redirect/buy/<int:price_id>', endpoint='redirect_buy')
def redirect_to_store(price_id):
    """
    Buyhatke-style intermediate transition controller.
    Displays a branded 'Redirecting you securely...' screen while resolving
    and forwarding the user directly to the single product page (Amazon /dp/ASIN, Flipkart /p/itm, etc.).
    """
    price_obj = db.session.get(Price, price_id)
    if not price_obj:
        flash("Deal link not found.", "warning")
        return redirect(url_for('home'))

    product = price_obj.product
    retailer = price_obj.retailer
    target_url = price_obj.resolve_single_product_url()

    return render_template(
        'redirect_outbound.html',
        product=product,
        retailer=retailer,
        price=price_obj,
        target_url=target_url
    )

@app.route('/compare')
@app.route('/comparison')
def compare():
    product_ids_raw = request.args.get('ids', '') or request.args.get('product_id', '')
    product_ids = [int(i) for i in product_ids_raw.split(',') if i.isdigit()]
    
    if not product_ids:
        first_prod = Product.query.first()
        if first_prod:
            product_ids = [first_prod.id]
        else:
            flash("Select products to compare.", "info")
            return redirect(url_for('search'))
        
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    primary_product = products[0] if products else None
    stores = primary_product.prices if primary_product else []
    max_savings = primary_product.savings_amount if primary_product else 0
    return render_template('comparison.html', product=primary_product, products=products, stores=stores, max_savings=max_savings)

@app.route('/wishlist', methods=['GET', 'POST'], endpoint='wishlist')
@app.route('/wishlist/toggle', methods=['POST'], endpoint='toggle_wishlist')
@app.route('/wishlist/toggle/<int:product_id>', methods=['POST'], endpoint='toggle_wishlist_id')
def wishlist(product_id=None):
    if not current_user.is_authenticated:
        flash("Please log in to manage your wishlist.", "warning")
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        p_id = product_id or request.form.get('product_id', type=int) or request.args.get('product_id', type=int)
        if p_id:
            existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=p_id).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
                flash("Removed from Wishlist.", "info")
            else:
                item = Wishlist(user_id=current_user.id, product_id=p_id)
                db.session.add(item)
                db.session.commit()
                flash("Added to Wishlist!", "success")
        return redirect(request.referrer or url_for('wishlist'))
        
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist.html', wishlist_items=items, items=items)

@app.route('/alerts', methods=['GET', 'POST'], endpoint='alerts')
@app.route('/price-alerts', methods=['GET', 'POST'], endpoint='price_alerts')
@app.route('/price-alerts/set', methods=['POST'], endpoint='set_price_alert')
@app.route('/price-alerts/set/<int:product_id>', methods=['POST'], endpoint='set_price_alert_id')
def price_alerts(product_id=None):
    if not current_user.is_authenticated:
        flash("Please log in to create price alerts.", "warning")
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        p_id = product_id or request.form.get('product_id', type=int) or request.args.get('product_id', type=int)
        target_price = request.form.get('target_price', type=float)
        if p_id and target_price:
            alert = PriceAlert(user_id=current_user.id, product_id=p_id, target_price=target_price)
            db.session.add(alert)
            db.session.commit()
            flash(f"Price alert created for target ₹{target_price:,.0f}!", "success")
        return redirect(request.referrer or url_for('price_alerts'))
        
    alerts = PriceAlert.query.filter_by(user_id=current_user.id).all()
    return render_template('alerts.html', alerts=alerts, items=alerts)

@app.route('/price-alerts/delete/<int:alert_id>', methods=['POST'], endpoint='delete_price_alert')
def delete_price_alert(alert_id):
    if not current_user.is_authenticated:
        flash("Please log in to manage your alerts.", "warning")
        return redirect(url_for('login'))
    alert = PriceAlert.query.filter_by(id=alert_id, user_id=current_user.id).first()
    if alert:
        db.session.delete(alert)
        db.session.commit()
        flash("Price alert removed.", "info")
    return redirect(request.referrer or url_for('price_alerts'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash("Thank you for contacting RigRate! We will get back to you shortly.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ================= AUTHENTICATION =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Successfully logged in!", "success")
            return redirect(url_for('home'))
        flash("Invalid username or password.", "danger")
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Registration successful!", "success")
            return redirect(url_for('home'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for('home'))

# ================= API ENDPOINTS =================

@app.route('/api/products/search')
def api_search():
    q = request.args.get('q', '').strip()
    products = Product.query.all()
    if q:
        products = PriceScraperEngine.fuzzy_search_products(q, products)
    return jsonify([p.to_dict() for p in products[:20]])

@app.route('/api/categories')
def api_categories():
    categories = Category.query.all()
    categories.sort(key=lambda c: 0 if c.name == 'PC Components' else 1)
    return jsonify([{"id": c.id, "name": c.name, "slug": c.slug, "icon": c.icon} for c in categories])

@app.route('/api/products/<int:product_id>/history')
def api_product_history(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
        
    history_records = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.recorded_at.asc()).all()
    
    dates = sorted(list(set([h.recorded_at.strftime("%b %d") for h in history_records])))
    retailer_map = {}
    for h in history_records:
        r_name = h.retailer.name if h.retailer else "Retailer"
        if r_name not in retailer_map:
            retailer_map[r_name] = []
        retailer_map[r_name].append(h.price)
        
    datasets = []
    colors = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#9333ea"]
    for idx, (r_name, prices_list) in enumerate(retailer_map.items()):
        datasets.append({
            "label": r_name,
            "data": prices_list[-len(dates):],
            "borderColor": colors[idx % len(colors)],
            "fill": False,
            "tension": 0.3
        })
        
    return jsonify({"labels": dates, "datasets": datasets})

# ================= ADMIN DASHBOARD =================

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
        
    total_products = Product.query.count()
    total_categories = Category.query.count()
    total_retailers = Retailer.query.count()
    total_users = User.query.count()
    products = Product.query.order_by(Product.id.desc()).limit(15).all()
    
    return render_template('admin/dashboard.html',
                           total_products=total_products,
                           total_categories=total_categories,
                           total_retailers=total_retailers,
                           total_users=total_users,
                           products=products)

@app.route('/admin/scrape-now', methods=['POST'], endpoint='admin_scrape_now')
@app.route('/admin/trigger-scrape', methods=['POST'], endpoint='admin_trigger_scrape')
@login_required
def admin_scrape_now():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    updated = PriceScraperEngine.run_full_scraping_job(app, db.session)
    flash(f"Scrape completed! Updated {updated} price points across all products.", "success")
    return redirect(url_for('admin_dashboard'))

# Admin Product Management
@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    products = Product.query.order_by(Product.id.desc()).all()
    categories = Category.query.all()
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/products/add', methods=['POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    name = request.form.get('name')
    brand = request.form.get('brand')
    category_id = request.form.get('category_id', type=int)
    original_price = request.form.get('original_price', type=float) or 0.0
    image_url = request.form.get('image') or request.form.get('image_url') or 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=500&auto=format&fit=crop&q=60'
    description = request.form.get('description', '')

    if name and category_id:
        prod = Product(
            name=name,
            brand=brand or 'Generic',
            category_id=category_id,
            original_price=original_price,
            image_url=image_url,
            description=description
        )
        db.session.add(prod)
        db.session.commit()

        # Add initial retailer prices if provided
        retailer_map = {
            "amazon": request.form.get('amazon_price', type=float),
            "flipkart": request.form.get('flipkart_price', type=float),
            "mdcomputers": request.form.get('croma_price', type=float),
            "vedantcomputers": request.form.get('reliance_price', type=float)
        }
        for r_slug, p_val in retailer_map.items():
            if p_val and p_val > 0:
                ret = Retailer.query.filter_by(slug=r_slug).first() or Retailer.query.first()
                if ret:
                    price_obj = Price(product_id=prod.id, retailer_id=ret.id, price=p_val, in_stock=True, product_url=ret.website_url)
                    db.session.add(price_obj)
        db.session.commit()
        flash("Product added successfully!", "success")
    return redirect(url_for('admin_products'))

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    prod = db.session.get(Product, product_id)
    if prod:
        db.session.delete(prod)
        db.session.commit()
        flash("Product deleted successfully.", "info")
    return redirect(url_for('admin_products'))

# Admin Category Management
@app.route('/admin/categories')
@login_required
def admin_categories():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['POST'])
@login_required
def admin_add_category():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    name = request.form.get('name')
    slug = request.form.get('slug') or (name.lower().replace(' ', '-') if name else '')
    icon = request.form.get('icon') or 'bi-tag'
    description = request.form.get('description', '')
    if name:
        cat = Category(name=name, slug=slug, icon=icon, description=description)
        db.session.add(cat)
        db.session.commit()
        flash("Category added successfully!", "success")
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def admin_delete_category(category_id):
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    cat = db.session.get(Category, category_id)
    if cat:
        db.session.delete(cat)
        db.session.commit()
        flash("Category deleted successfully.", "info")
    return redirect(url_for('admin_categories'))

# Admin Retailer Management
@app.route('/admin/retailers')
@login_required
def admin_retailers():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    retailers = Retailer.query.all()
    return render_template('admin/retailers.html', retailers=retailers)

@app.route('/admin/retailers/add', methods=['POST'])
@login_required
def admin_add_retailer():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    name = request.form.get('name')
    slug = request.form.get('slug') or (name.lower().replace(' ', '-') if name else '')
    badge_bg = request.form.get('badge_bg') or 'bg-primary text-white'
    icon = request.form.get('icon') or 'bi-shop'
    website_url = request.form.get('website_url', '')
    if name:
        ret = Retailer(name=name, slug=slug, badge_bg=badge_bg, icon=icon, website_url=website_url)
        db.session.add(ret)
        db.session.commit()
        flash("Retailer added successfully!", "success")
    return redirect(url_for('admin_retailers'))

@app.route('/admin/retailers/delete/<int:retailer_id>', methods=['POST'])
@login_required
def admin_delete_retailer(retailer_id):
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for('home'))
    ret = db.session.get(Retailer, retailer_id)
    if ret:
        db.session.delete(ret)
        db.session.commit()
        flash("Retailer deleted successfully.", "info")
    return redirect(url_for('admin_retailers'))

# ================= LIVE SCRAPING & FLUCTUATION ROUTES =================

@app.route('/live-tracker')
@app.route('/live-fluctuations')
def live_tracker():
    """
    Redirect to Deals Radar page.
    """
    return redirect(url_for('deals'))


@app.route('/api/live/fluctuations')
def api_live_fluctuations():
    """
    REST API returning real-time price fluctuation stream, top drops, and volatility summary.
    """
    drops_only = request.args.get('drops_only', 'false').lower() == 'true'
    category_slug = request.args.get('category', '').strip() or None
    limit = request.args.get('limit', 40, type=int)

    fluctuations = PriceScraperEngine.get_live_fluctuations(limit=limit, drops_only=drops_only, category_slug=category_slug)
    drop_events = [f for f in fluctuations if f["direction"] == "down"]
    
    return jsonify({
        "success": True,
        "count": len(fluctuations),
        "total_drops": len(drop_events),
        "fluctuations": fluctuations,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    })

@app.route('/api/live/market-pulse')
def api_live_market_pulse():
    """
    Lightweight streaming ticker endpoint for the global navigation ticker bar.
    """
    fluctuations = PriceScraperEngine.get_live_fluctuations(limit=15)
    pulse_items = []
    
    for item in fluctuations:
        sign = "-" if item["direction"] == "down" else ("+" if item["direction"] == "up" else "")
        pulse_items.append({
            "product_id": item["product_id"],
            "name": item["name"],
            "brand": item["brand"],
            "retailer": item["retailer_name"],
            "current_price": item["current_price"],
            "change_pct": item["change_pct"],
            "direction": item["direction"],
            "badge_text": f"{sign}{abs(item['change_pct'])}%" if item["change_pct"] != 0 else "Best Price",
            "time_ago": item["last_changed"]
        })

    return jsonify({"pulse": pulse_items})

@app.route('/api/live/simulate-fluctuations', methods=['POST'])
def api_live_simulate_fluctuations():
    """
    Interactive test trigger to apply live market fluctuations and demonstrate real-time price changes.
    """
    data = request.get_json() or {}
    count = data.get('count', 6)
    product_ids = data.get('product_ids', None)

    updated = PriceScraperEngine.simulate_live_fluctuations(count=count, product_ids=product_ids, db_session=db.session)
    return jsonify({
        "success": True,
        "message": f"Successfully simulated real-time market fluctuations on {len(updated)} products.",
        "updated": updated
    })

@app.route('/api/products/<int:product_id>/live-status')
def api_product_live_status(product_id):
    """
    Fetches real-time status, live fluctuation metrics, and updated history for in-place frontend sync.
    """
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    fluc = product.get_fluctuation_metrics()
    prices = [p.to_dict() for p in product.prices]
    prices.sort(key=lambda x: x["price"])

    # Chart datasets
    history_records = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.recorded_at.asc()).all()
    dates = sorted(list(set([h.recorded_at.strftime("%b %d") for h in history_records])))
    retailer_map = {}
    for h in history_records:
        r_name = h.retailer.name if h.retailer else "Retailer"
        if r_name not in retailer_map:
            retailer_map[r_name] = []
        retailer_map[r_name].append(h.price)

    datasets = []
    colors = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#9333ea"]
    for idx, (r_name, prices_list) in enumerate(retailer_map.items()):
        datasets.append({
            "label": r_name,
            "data": prices_list[-len(dates):],
            "borderColor": colors[idx % len(colors)],
            "fill": False,
            "tension": 0.3
        })

    return jsonify({
        "success": True,
        "product_id": product.id,
        "name": product.name,
        "lowest_price": product.lowest_price,
        "original_price": product.original_price,
        "savings_amount": product.savings_amount,
        "discount_percentage": product.discount_percentage,
        "fluctuation": fluc,
        "prices": prices,
        "chart": {
            "labels": dates,
            "datasets": datasets
        }
    })

@app.route('/api/products/<int:product_id>/sync-live', methods=['POST'])
def api_sync_product_live(product_id):
    """
    Triggers on-demand real-time price synchronization from live APIs (Amazon, Flipkart, etc.).
    """
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    try:
        result = PriceScraperEngine.sync_live_prices(product, db.session)
        if isinstance(result, dict) and not result.get("success", True):
            return jsonify({
                "success": False,
                "error": result.get("error", "Failed to fetch live prices from external API."),
                "error_code": result.get("error_code", "API_ERROR"),
                "source": result.get("source")
            }), 400

        fluc = product.get_fluctuation_metrics()
        
        # Fetch updated price list
        prices = [p.to_dict() for p in product.prices]
        prices.sort(key=lambda x: x["price"])

        # Updated chart datasets
        history_records = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.recorded_at.asc()).all()
        dates = sorted(list(set([h.recorded_at.strftime("%b %d") for h in history_records])))
        retailer_map = {}
        for h in history_records:
            r_name = h.retailer.name if h.retailer else "Retailer"
            if r_name not in retailer_map:
                retailer_map[r_name] = []
            retailer_map[r_name].append(h.price)

        datasets = []
        colors = ["#2563eb", "#16a34a", "#dc2626", "#d97706", "#9333ea"]
        for idx, (r_name, prices_list) in enumerate(retailer_map.items()):
            datasets.append({
                "label": r_name,
                "data": prices_list[-len(dates):],
                "borderColor": colors[idx % len(colors)],
                "fill": False,
                "tension": 0.3
            })

        return jsonify({
            "success": True,
            "message": f"Successfully updated live prices for {product.name}!",
            "lowest_price": product.lowest_price,
            "original_price": product.original_price,
            "savings_amount": product.savings_amount,
            "discount_percentage": product.discount_percentage,
            "fluctuation": fluc,
            "prices": prices,
            "chart": {
                "labels": dates,
                "datasets": datasets
            },
            "sync_details": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/prices/lookup', methods=['GET'])
def api_external_price_lookup():
    """
    Direct endpoint to query external Price/Product API for any search query.
    Extracts multi-retailer prices, direct links, and stock availability.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"success": False, "error": "Query parameter 'q' is required."}), 400

    from services.price_api import PriceAPIService
    result = PriceAPIService.fetch_product_prices(query)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code

@app.route('/api/products')
def api_products():
    """
    Returns JSON list of all products in catalog.
    """
    products = Product.query.all()
    return jsonify({
        "success": True,
        "count": len(products),
        "products": [p.to_dict() for p in products]
    })

@app.route('/api/search/suggestions')
def api_search_suggestions():
    """
    Returns search query suggestions based on product titles and brands.
    """
    q = request.args.get('q', '').strip().lower()
    if not q or len(q) < 2:
        return jsonify({"suggestions": []})

    products = Product.query.all()
    suggestions = set()
    for p in products:
        if q in p.name.lower() or q in p.brand.lower():
            suggestions.add(f"{p.brand} {p.name}")
            if len(suggestions) >= 8:
                break

@app.route('/api/assistant/chat', methods=['POST'])
def api_assistant_chat():
    """
    RigRate AI — Virtual Shopping Assistant Chat API (Powered by Yash)
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])
    
    if not message:
        return jsonify({"success": False, "error": "Message is required."}), 400

    from services.ai_assistant import get_ai_assistant_response
    try:
        reply = get_ai_assistant_response(message, history)
        return jsonify({
            "success": True,
            "reply": reply,
            "assistant": "RigRate AI",
            "powered_by": "Yash"
        })
    except Exception as e:
        print(f"[RigRate AI Chat Error]: {e}")
        return jsonify({
            "success": True,
            "reply": "I apologize, but I encountered a momentary hiccup while processing your request. Please try asking again!",
            "assistant": "RigRate AI",
            "powered_by": "Yash"
        })

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True, port=5000)




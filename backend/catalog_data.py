"""
Universal Electronics Catalog & Infinite Dynamic Generation Engine for ElectroCompare
Supports N-numbers of products across any brand, category, accessory, or search query.
"""

import random
import re

# Comprehensive curated products database
CURATED_PRODUCTS = [
    # ==================== 1. SMARTPHONES ====================
    {
        "name": "Apple iPhone 15 Pro Max (256 GB) - Natural Titanium",
        "brand": "Apple",
        "category": "Smartphones",
        "image": "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 3890,
        "original_price": 159900,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Natural Titanium", "Blue Titanium", "White Titanium", "Black Titanium"],
        "storage_options": ["256 GB", "512 GB", "1 TB"],
        "description": "Forged in titanium with the industry-leading A17 Pro chip, 5x Telephoto optical zoom, and customized Action button.",
        "features": ["A17 Pro chip with 6-core GPU", "Aerospace-grade titanium design", "5x Telephoto Optical Zoom", "48MP Main Camera with next-gen portraits"],
        "specs": {"Display": "6.7-inch Super Retina XDR OLED (120Hz ProMotion)", "Processor": "Apple A17 Pro (3nm)", "Camera": "48MP Main + 12MP Ultra-Wide + 12MP 5x Telephoto", "Battery": "4422 mAh"},
        "prices": [
            {"retailer": "amazon", "price": 149999, "delivery": "Free Tomorrow Delivery"},
            {"retailer": "flipkart", "price": 151990, "delivery": "Free 2-Day Delivery"},
            {"retailer": "croma", "price": 154900, "delivery": "Express Store Pickup"},
            {"retailer": "reliance", "price": 156900, "delivery": "Standard Delivery"},
            {"retailer": "vijaysales", "price": 157990, "delivery": "Free Delivery"}
        ]
    },
    {
        "name": "Apple iPhone 15 (128 GB) - Pink / Blue / Black",
        "brand": "Apple",
        "category": "Smartphones",
        "image": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 5210,
        "original_price": 79900,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Pink", "Blue", "Yellow", "Green", "Black"],
        "storage_options": ["128 GB", "256 GB", "512 GB"],
        "description": "Dynamic Island bubbles up alerts and Live Activities. Plus, a 48MP Main camera and color-infused durable glass back.",
        "features": ["Dynamic Island", "48MP Main camera with 2x Telephoto", "A16 Bionic chip", "USB-C universal charging"],
        "specs": {"Display": "6.1-inch Super Retina XDR", "Processor": "Apple A16 Bionic", "Camera": "48MP + 12MP Dual Camera", "Battery": "3349 mAh"},
        "prices": [
            {"retailer": "amazon", "price": 70999, "delivery": "Free Tomorrow Delivery"},
            {"retailer": "flipkart", "price": 71499, "delivery": "Free Express Delivery"},
            {"retailer": "croma", "price": 73990, "delivery": "Same Day Pickup"}
        ]
    },
    {
        "name": "Samsung Galaxy S24 Ultra 5G (12GB RAM, 512GB) - Titanium Gray",
        "brand": "Samsung",
        "category": "Smartphones",
        "image": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 2840,
        "original_price": 144999,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Titanium Gray", "Titanium Black", "Titanium Violet"],
        "storage_options": ["256 GB", "512 GB", "1 TB"],
        "description": "Galaxy AI transforms your smartphone experience with Live Translate, Note Assist, Circle to Search, and 200MP Quad Tele System.",
        "features": ["Galaxy AI Suite with Live Translate", "200MP Camera with 100x Space Zoom", "Built-in S Pen Stylus", "Snapdragon 8 Gen 3 for Galaxy"],
        "specs": {"Display": "6.8-inch QHD+ Dynamic AMOLED 2X (1-120Hz, 2600 nits)", "Processor": "Snapdragon 8 Gen 3", "Camera": "200MP + 50MP + 12MP + 10MP", "Battery": "5000 mAh"},
        "prices": [
            {"retailer": "flipkart", "price": 129999, "delivery": "Free Express Shipping"},
            {"retailer": "amazon", "price": 131499, "delivery": "Free Prime Shipping"},
            {"retailer": "croma", "price": 134999, "delivery": "Store Pickup Available"},
            {"retailer": "reliance", "price": 137999, "delivery": "Standard Delivery"},
            {"retailer": "vijaysales", "price": 134990, "delivery": "Free Delivery"}
        ]
    },
    {
        "name": "OnePlus 12 5G (16GB RAM, 512GB) - Silky Black",
        "brand": "OnePlus",
        "category": "Smartphones",
        "image": "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1565849904461-04a58ad377e0?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.7,
        "review_count": 3100,
        "original_price": 69999,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Silky Black", "Flowy Emerald"],
        "storage_options": ["256 GB", "512 GB"],
        "description": "Flagship performance powered by Snapdragon 8 Gen 3, 4th Gen Hasselblad Camera system, and 100W SUPERVOOC charging.",
        "features": ["Snapdragon 8 Gen 3", "4th Gen Hasselblad Camera", "100W Wired + 50W Wireless Fast Charging", "4500 nits peak brightness"],
        "specs": {"Display": "6.82-inch 2K ProXDR Display (120Hz LTPO)", "Processor": "Snapdragon 8 Gen 3", "Camera": "50MP Sony LYT-808 + 64MP 3x Periscope", "Battery": "5400 mAh"},
        "prices": [
            {"retailer": "amazon", "price": 64999, "delivery": "Free Next Day Delivery"},
            {"retailer": "flipkart", "price": 65999, "delivery": "Free 2-Day Delivery"},
            {"retailer": "croma", "price": 67999, "delivery": "Store Pickup Available"},
            {"retailer": "reliance", "price": 68999, "delivery": "Standard Delivery"}
        ]
    },
    {
        "name": "Google Pixel 8 Pro (128 GB) - Bay Blue",
        "brand": "Google",
        "category": "Smartphones",
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.6,
        "review_count": 1950,
        "original_price": 106999,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Bay Blue", "Obsidian", "Porcelain"],
        "storage_options": ["128 GB", "256 GB"],
        "description": "Supercharged with Google Tensor G3, leading AI photo/video editing with Best Take and Audio Magic Eraser.",
        "features": ["Google Tensor G3 AI chip", "Pro Camera controls with 5x telephoto", "7 years of OS and security updates"],
        "specs": {"Display": "6.7-inch Super Actua LTPO OLED (120Hz)", "Processor": "Google Tensor G3", "Camera": "50MP + 48MP + 48MP", "Battery": "5050 mAh"},
        "prices": [
            {"retailer": "flipkart", "price": 93999, "delivery": "Free Express Delivery"},
            {"retailer": "amazon", "price": 96999, "delivery": "Free Prime Shipping"}
        ]
    },

    # ==================== 2. LAPTOPS ====================
    {
        "name": "Apple MacBook Pro 16-inch M3 Max (36GB RAM / 1TB SSD) - Space Black",
        "brand": "Apple",
        "category": "Laptops",
        "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 890,
        "original_price": 349900,
        "is_featured": True,
        "is_deal": False,
        "colors": ["Space Black", "Silver"],
        "storage_options": ["1 TB SSD", "2 TB SSD"],
        "description": "Extreme processing power for rendering, AI models, and coding with M3 Max 14-core CPU and 30-core GPU.",
        "features": ["Apple M3 Max 14-core CPU & 30-core GPU", "16.2-inch Liquid Retina XDR display", "Up to 22 hours battery life"],
        "specs": {"Display": "16.2-inch Liquid Retina XDR (120Hz ProMotion)", "Processor": "Apple M3 Max", "RAM & Storage": "36GB Unified / 1TB NVMe SSD", "Weight": "2.16 kg"},
        "prices": [
            {"retailer": "amazon", "price": 319900, "delivery": "Free Expedited Shipping"},
            {"retailer": "croma", "price": 324900, "delivery": "Store Pickup Available"},
            {"retailer": "reliance", "price": 339900, "delivery": "Standard Delivery"}
        ]
    },
    {
        "name": "Dell XPS 15 9530 Intel Core i9 (32GB / 1TB SSD / RTX 4060)",
        "brand": "Dell",
        "category": "Laptops",
        "image": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.6,
        "review_count": 640,
        "original_price": 279990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Platinum Silver"],
        "storage_options": ["1 TB SSD"],
        "description": "Iconic Dell XPS 15 featuring an OLED 3.5K touch display and Nvidia GeForce RTX 4060 graphics.",
        "features": ["13th Gen Intel Core i9-13900H", "NVIDIA RTX 4060 8GB GDDR6", "3.5K OLED Touch Display"],
        "specs": {"Display": "15.6-inch 3.5K OLED Touch (3456 x 2160)", "Processor": "Intel Core i9-13900H", "RAM & Storage": "32GB DDR5 / 1TB NVMe SSD", "Weight": "1.92 kg"},
        "prices": [
            {"retailer": "flipkart", "price": 249990, "delivery": "Free Delivery"},
            {"retailer": "amazon", "price": 254990, "delivery": "Free One-Day Delivery"}
        ]
    },

    # ==================== 3. TABLETS ====================
    {
        "name": "Apple iPad Pro 13-inch M4 (256 GB, Wi-Fi) - Space Black",
        "brand": "Apple",
        "category": "Tablets",
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 1150,
        "original_price": 129900,
        "is_featured": True,
        "is_deal": False,
        "colors": ["Space Black", "Silver"],
        "storage_options": ["256 GB", "512 GB"],
        "description": "The thinnest Apple product ever. Breakthrough Ultra Retina XDR tandem OLED display and monumental M4 performance.",
        "features": ["Apple M4 Chip with 9-core CPU & 10-core GPU", "Ultra Retina XDR Tandem OLED", "Support for Apple Pencil Pro"],
        "specs": {"Display": "13-inch Tandem OLED Ultra Retina XDR (120Hz)", "Processor": "Apple M4", "Weight": "579g"},
        "prices": [
            {"retailer": "amazon", "price": 124900, "delivery": "Free Tomorrow Delivery"},
            {"retailer": "croma", "price": 127900, "delivery": "Store Pickup Available"}
        ]
    },

    # ==================== 4. HEADPHONES & AUDIO ====================
    {
        "name": "Sony WH-1000XM5 Wireless Noise Canceling Headphones - Silver",
        "brand": "Sony",
        "category": "Headphones & Earbuds",
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 3820,
        "original_price": 34990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Silver", "Black"],
        "storage_options": ["Standard"],
        "description": "Industry-leading noise canceling with 2 processors, 8 microphones, LDAC Hi-Res Wireless, and 30-hour battery life.",
        "features": ["Auto NC Optimizer with V1 + QN1 processors", "30-hour battery life", "Speak-to-Chat"],
        "specs": {"Type": "Over-Ear Wireless Active Noise Canceling", "Battery": "30h (NC ON)", "Weight": "250g"},
        "prices": [
            {"retailer": "amazon", "price": 26990, "delivery": "Free Delivery Tomorrow"},
            {"retailer": "flipkart", "price": 27990, "delivery": "Free 2-Day Delivery"},
            {"retailer": "croma", "price": 28990, "delivery": "Store Pickup"}
        ]
    },
    {
        "name": "Apple AirPods Pro (2nd Generation with USB-C MagSafe Case)",
        "brand": "Apple",
        "category": "Headphones & Earbuds",
        "image": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 6450,
        "original_price": 24900,
        "is_featured": True,
        "is_deal": True,
        "colors": ["White"],
        "storage_options": ["MagSafe USB-C"],
        "description": "Up to 2x more Active Noise Cancellation, Adaptive Audio, Conversation Awareness, and Personalized Spatial Audio.",
        "features": ["Apple H2 headphone chip", "2x improved Active Noise Cancellation", "Adaptive Audio"],
        "specs": {"Type": "In-Ear True Wireless ANC Earbuds", "Battery Life": "6 hours (up to 30 hours with case)"},
        "prices": [
            {"retailer": "amazon", "price": 21990, "delivery": "Free Prime Delivery"},
            {"retailer": "flipkart", "price": 22490, "delivery": "Free Express Delivery"}
        ]
    },

    # ==================== 5. SMARTWATCHES ====================
    {
        "name": "Apple Watch Ultra 2 GPS + Cellular 49mm Titanium - Ocean Band",
        "brand": "Apple",
        "category": "Smartwatches",
        "image": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 1120,
        "original_price": 89900,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Natural Titanium"],
        "storage_options": ["64 GB"],
        "description": "The ultimate sports and adventure smartwatch with aerospace titanium case, 3000 nits display, precision dual-frequency GPS.",
        "features": ["49mm Aerospace Titanium Case", "3000 nits Retina Always-On Display", "100m Water Resistant"],
        "specs": {"Display": "1.92-inch Sapphire Crystal OLED", "Chip": "Apple S9 SiP", "Battery": "36 hours"},
        "prices": [
            {"retailer": "amazon", "price": 84900, "delivery": "Free Express Delivery"},
            {"retailer": "croma", "price": 86900, "delivery": "Store Pickup"}
        ]
    },

    # ==================== 6. TELEVISIONS ====================
    {
        "name": "LG C3 55-inch 4K Smart OLED evo TV (OLED55C3PSA)",
        "brand": "LG",
        "category": "Televisions",
        "image": "https://images.unsplash.com/photo-1593784991095-a205069470b6?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1593784991095-a205069470b6?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 640,
        "original_price": 169990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Dark Silver"],
        "storage_options": ["55-inch"],
        "description": "LG OLED evo C3 Series powered by α9 AI Processor Gen6 for intense self-lit picture quality, 120Hz refresh rate, G-SYNC.",
        "features": ["Self-lit OLED evo", "α9 AI Processor Gen6 4K", "120Hz Refresh Rate, 0.1ms response"],
        "specs": {"Resolution": "4K Ultra HD (3840 x 2160)", "Refresh Rate": "120Hz Native", "Sound": "40W 2.2 Channel"},
        "prices": [
            {"retailer": "amazon", "price": 124990, "delivery": "Free Scheduled Delivery"},
            {"retailer": "croma", "price": 129990, "delivery": "Free Express Installation"}
        ]
    },

    # ==================== 7. CAMERAS ====================
    {
        "name": "Sony Alpha 7 IV Full-Frame Mirrorless Camera (28-70mm Lens)",
        "brand": "Sony",
        "category": "Cameras",
        "image": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 310,
        "original_price": 242990,
        "is_featured": True,
        "is_deal": False,
        "colors": ["Black"],
        "storage_options": ["Body + 28-70mm Lens"],
        "description": "Benchmark hybrid full-frame camera featuring 33MP Exmor R CMOS sensor, 4K 60p 10-bit recording, and real-time Eye AF.",
        "features": ["33MP Full-Frame Exmor R Sensor", "BIONZ XR processing engine", "4K 60p 10-bit video"],
        "specs": {"Sensor": "33.0 MP Full-Frame", "ISO Range": "100 - 51200", "Weight": "658g"},
        "prices": [
            {"retailer": "amazon", "price": 222990, "delivery": "Free Secured Delivery"},
            {"retailer": "flipkart", "price": 224990, "delivery": "Free Delivery"}
        ]
    },

    # ==================== 8. PC COMPONENTS (PRIORITIZED & EXPANDED) ====================
    # --- GPUs (Graphics Cards) ---
    {
        "name": "NVIDIA GeForce RTX 4090 24GB GDDR6X Founders Edition",
        "brand": "NVIDIA",
        "category": "PC Components",
        "subcomponent": "GPU",
        "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 890,
        "original_price": 199900,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Titanium Gray"],
        "storage_options": ["24 GB GDDR6X"],
        "description": "The ultimate GPU for extreme 4K ray-traced gaming, AI deep learning, local LLMs, and 3D rendering with Ada Lovelace architecture & DLSS 3.5.",
        "features": ["16,384 CUDA Cores & 24GB GDDR6X VRAM", "DLSS 3.5 AI Frame Generation & Ray Tracing", "3rd Gen RT Cores + 4th Gen Tensor Cores"],
        "specs": {"CUDA Cores": "16384", "Memory": "24GB GDDR6X (384-bit)", "Boost Clock": "2.52 GHz", "Power (TGP)": "450W", "Interface": "PCIe 4.0 x16"},
        "prices": [
            {"retailer": "amazon", "price": 184990, "delivery": "Free Secured Express Delivery"},
            {"retailer": "flipkart", "price": 187990, "delivery": "Free 2-Day Delivery"},
            {"retailer": "croma", "price": 189990, "delivery": "Express Store Pickup"},
            {"retailer": "reliance", "price": 192900, "delivery": "Standard Shipping"}
        ]
    },
    {
        "name": "ASUS ROG Strix GeForce RTX 4080 Super 16GB GDDR6X OC Edition",
        "brand": "ASUS",
        "category": "PC Components",
        "subcomponent": "GPU",
        "image": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 620,
        "original_price": 124990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["ROG Black RGB"],
        "storage_options": ["16 GB GDDR6X"],
        "description": "Flagship custom cooling GPU featuring Axial-tech fans, patented vapor chamber, and die-cast shroud for maximum 4K high-FPS gaming.",
        "features": ["10,240 CUDA Cores & 16GB GDDR6X VRAM", "Axial-tech Triple Fan Cooling & Vapor Chamber", "Aura Sync RGB Lighting & Metal Exoskeleton"],
        "specs": {"CUDA Cores": "10240", "Memory": "16GB GDDR6X (256-bit)", "Boost Clock": "2670 MHz (OC)", "Power": "320W", "Interface": "PCIe 4.0 x16"},
        "prices": [
            {"retailer": "amazon", "price": 109990, "delivery": "Free Next Day Delivery"},
            {"retailer": "flipkart", "price": 111990, "delivery": "Free Delivery"},
            {"retailer": "vijaysales", "price": 114990, "delivery": "Free Store Delivery"}
        ]
    },
    {
        "name": "AMD Radeon RX 7900 XTX 24GB GDDR6 Graphics Card",
        "brand": "AMD",
        "category": "PC Components",
        "subcomponent": "GPU",
        "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.7,
        "review_count": 410,
        "original_price": 109990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Midnight Black"],
        "storage_options": ["24 GB GDDR6"],
        "description": "Powered by RDNA 3 chiplet technology, offering 24GB VRAM for high-refresh rate 4K gaming, DisplayPort 2.1, and AMD HYPR-RX.",
        "features": ["6144 Stream Processors & 24GB GDDR6 VRAM", "AMD RDNA 3 Chiplet Architecture", "DisplayPort 2.1 support for up to 8K 165Hz"],
        "specs": {"Stream Processors": "6144", "Memory": "24GB GDDR6 (384-bit)", "Boost Clock": "2500 MHz", "Power": "355W"},
        "prices": [
            {"retailer": "amazon", "price": 96990, "delivery": "Free Prime Shipping"},
            {"retailer": "flipkart", "price": 98490, "delivery": "Free Express Delivery"}
        ]
    },
    {
        "name": "Gigabyte GeForce RTX 4070 Ti Super EAGLE OC 16GB",
        "brand": "Gigabyte",
        "category": "PC Components",
        "subcomponent": "GPU",
        "image": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.7,
        "review_count": 340,
        "original_price": 89990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Eagle Gray"],
        "storage_options": ["16 GB GDDR6X"],
        "description": "High-value 1440p & 4K gaming graphics card with WINDFORCE 3X cooling system and 16GB GDDR6X VRAM.",
        "features": ["8448 CUDA Cores & 16GB VRAM", "WINDFORCE 3X Cooling System", "Protection Metal Backplate"],
        "specs": {"CUDA Cores": "8448", "Memory": "16GB GDDR6X", "Boost Clock": "2625 MHz", "Power": "285W"},
        "prices": [
            {"retailer": "amazon", "price": 79990, "delivery": "Free Next Day Delivery"},
            {"retailer": "croma", "price": 81990, "delivery": "Store Pickup Available"}
        ]
    },

    # --- CPUs (Processors) ---
    {
        "name": "AMD Ryzen 7 7800X3D 8-Core 16-Thread Desktop Processor",
        "brand": "AMD",
        "category": "PC Components",
        "subcomponent": "CPU",
        "image": "https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 1420,
        "original_price": 44990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Silver Box"],
        "storage_options": ["AM5 Socket"],
        "description": "The undisputed #1 gaming CPU in the world featuring 96MB of 3D V-Cache technology for ultra-high FPS in competitive and AAA games.",
        "features": ["8 Cores & 16 Threads with Zen 4 Architecture", "Massive 96MB L3 3D V-Cache", "AM5 Socket support with PCIe 5.0 & DDR5"],
        "specs": {"Cores / Threads": "8 / 16", "Base / Boost Clock": "4.2 GHz / 5.0 GHz", "L3 Cache": "96MB", "Socket": "AM5", "TDP": "120W"},
        "prices": [
            {"retailer": "amazon", "price": 36990, "delivery": "Free Prime Delivery"},
            {"retailer": "flipkart", "price": 37490, "delivery": "Free Express Delivery"},
            {"retailer": "croma", "price": 38990, "delivery": "Store Pickup"}
        ]
    },
    {
        "name": "Intel Core i9-14900K Desktop Processor (24 Cores up to 6.0 GHz)",
        "brand": "Intel",
        "category": "PC Components",
        "subcomponent": "CPU",
        "image": "https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 980,
        "original_price": 64990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Intel Blue"],
        "storage_options": ["LGA1700 Socket"],
        "description": "Intel's flagship 14th Gen unlocked processor reaching 6.0 GHz Thermal Velocity Boost for heavy streaming, video editing, and gaming.",
        "features": ["24 Cores (8 P-Cores + 16 E-Cores) & 32 Threads", "Up to 6.0 GHz Max Clock Speed", "Intel Thermal Velocity Boost & PCIe 5.0"],
        "specs": {"Cores / Threads": "24 / 32", "Max Turbo Clock": "6.0 GHz", "Cache": "36MB Smart Cache", "Socket": "LGA1700", "Base Power": "125W"},
        "prices": [
            {"retailer": "amazon", "price": 54990, "delivery": "Free One-Day Delivery"},
            {"retailer": "flipkart", "price": 55990, "delivery": "Free Express Delivery"},
            {"retailer": "reliance", "price": 57990, "delivery": "Standard Delivery"}
        ]
    },
    {
        "name": "Intel Core i7-14700K 20-Core (8P+12E) Unlocked Processor",
        "brand": "Intel",
        "category": "PC Components",
        "subcomponent": "CPU",
        "image": "https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 730,
        "original_price": 42990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Intel Blue"],
        "storage_options": ["LGA1700 Socket"],
        "description": "Sweet spot 14th Gen CPU with 20 cores (8 Performance + 12 Efficient) delivering high multi-threaded performance for creators.",
        "features": ["20 Cores & 28 Threads", "Up to 5.6 GHz Max Boost Clock", "Intel UHD Graphics 770 integrated"],
        "specs": {"Cores / Threads": "20 / 28", "Max Clock": "5.6 GHz", "Cache": "33MB", "Socket": "LGA1700"},
        "prices": [
            {"retailer": "amazon", "price": 36490, "delivery": "Free Prime Shipping"},
            {"retailer": "flipkart", "price": 36990, "delivery": "Free Delivery"}
        ]
    },
    {
        "name": "AMD Ryzen 9 7950X3D 16-Core 32-Thread Flagship Processor",
        "brand": "AMD",
        "category": "PC Components",
        "subcomponent": "CPU",
        "image": "https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 510,
        "original_price": 69990,
        "is_featured": False,
        "is_deal": False,
        "colors": ["Silver Box"],
        "storage_options": ["AM5 Socket"],
        "description": "The ultimate hybrid processor offering 16 Zen 4 cores for workstation applications combined with 128MB 3D V-Cache for peak gaming FPS.",
        "features": ["16 Cores & 32 Threads", "128MB L3 3D V-Cache", "Up to 5.7 GHz Boost Clock"],
        "specs": {"Cores / Threads": "16 / 32", "Max Clock": "5.7 GHz", "L3 Cache": "128MB", "Socket": "AM5"},
        "prices": [
            {"retailer": "amazon", "price": 58990, "delivery": "Free Secured Delivery"},
            {"retailer": "flipkart", "price": 59990, "delivery": "Free Express Delivery"}
        ]
    },

    # --- Storage (SSDs) ---
    {
        "name": "Samsung 990 Pro 2TB PCIe Gen4 NVMe M.2 Internal SSD (7450 MB/s)",
        "brand": "Samsung",
        "category": "PC Components",
        "subcomponent": "SSD",
        "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 2150,
        "original_price": 22990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Black Heatsink"],
        "storage_options": ["1 TB", "2 TB", "4 TB"],
        "description": "Industry-leading PCIe Gen 4 speed hitting up to 7,450 MB/s read speeds, optimized for PS5 expansion, 4K video editing, and instantaneous game loads.",
        "features": ["Up to 7,450 MB/s Read & 6,900 MB/s Write", "In-house Nickel-coated controller for thermal control", "Samsung Magician Software management"],
        "specs": {"Capacity": "2TB", "Interface": "PCIe Gen 4.0 x4, NVMe 2.0", "Form Factor": "M.2 2280", "Max Read Speed": "7450 MB/s"},
        "prices": [
            {"retailer": "amazon", "price": 16990, "delivery": "Free One-Day Delivery"},
            {"retailer": "flipkart", "price": 17490, "delivery": "Free Express Shipping"},
            {"retailer": "croma", "price": 17990, "delivery": "Store Pickup"}
        ]
    },
    {
        "name": "WD_BLACK 2TB SN850X NVMe Internal Gaming SSD with Heatsink",
        "brand": "Western Digital",
        "category": "PC Components",
        "subcomponent": "SSD",
        "image": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 1640,
        "original_price": 21990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["RGB Heatsink Black"],
        "storage_options": ["1 TB", "2 TB"],
        "description": "Blistering top-tier gaming SSD with built-in heatsink and Game Mode 2.0 software to maintain peak read speeds up to 7,300 MB/s.",
        "features": ["Up to 7,300 MB/s Read Speed", "Integrated custom RGB Heatsink", "WD_BLACK Dashboard Game Mode 2.0"],
        "specs": {"Capacity": "2TB", "Read Speed": "7300 MB/s", "Write Speed": "6600 MB/s", "Form Factor": "M.2 2280"},
        "prices": [
            {"retailer": "amazon", "price": 15990, "delivery": "Free Next Day Delivery"},
            {"retailer": "flipkart", "price": 16290, "delivery": "Free Delivery"}
        ]
    },

    # --- RAM (Memory) ---
    {
        "name": "G.SKILL Trident Z5 RGB 32GB (2x16GB) DDR5 6000MHz CL30 Memory",
        "brand": "G.Skill",
        "category": "PC Components",
        "subcomponent": "RAM",
        "image": "https://images.unsplash.com/photo-1562976540-1502c2145186?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1562976540-1502c2145186?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 1180,
        "original_price": 17990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["Matte Black", "Metallic Silver"],
        "storage_options": ["32 GB (2x16GB)", "64 GB (2x32GB)"],
        "description": "Ultra-fast DDR5 RAM tuned for Intel XMP 3.0 & AMD EXPO with low CL30 latency, sleek aluminum heatspreader, and vivid RGB light bar.",
        "features": ["6000MHz Speed with Low CL30-40-40-96 Timing", "Hand-screened DDR5 ICs for high overclocking", "Customizable RGB lighting support"],
        "specs": {"Capacity": "32GB (2x16GB)", "Speed": "DDR5-6000", "Tested Latency": "CL30-38-38-96", "Voltage": "1.35V"},
        "prices": [
            {"retailer": "amazon", "price": 12990, "delivery": "Free Prime Delivery"},
            {"retailer": "flipkart", "price": 13490, "delivery": "Free Express Shipping"}
        ]
    },
    {
        "name": "Corsair Vengeance RGB 64GB (2x32GB) DDR5 6000MHz CL30 RAM",
        "brand": "Corsair",
        "category": "PC Components",
        "subcomponent": "RAM",
        "image": "https://images.unsplash.com/photo-1562976540-1502c2145186?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1562976540-1502c2145186?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 860,
        "original_price": 28990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Black", "White"],
        "storage_options": ["64 GB (2x32GB)"],
        "description": "High-capacity 64GB DDR5 memory kit with dynamic ten-zone RGB lighting, custom PCB for maximum signal quality, and Corsair iCUE integration.",
        "features": ["64GB (2x32GB) DDR5-6000", "Dynamic 10-Zone RGB Light Bar", "Onboard Voltage Regulation for Overclocking"],
        "specs": {"Capacity": "64GB (2x32GB)", "Speed": "DDR5-6000", "Latency": "CL30", "Compatibility": "Intel & AMD AM5"},
        "prices": [
            {"retailer": "amazon", "price": 21990, "delivery": "Free One-Day Shipping"},
            {"retailer": "croma", "price": 22990, "delivery": "Store Pickup Available"}
        ]
    },

    # --- Motherboards ---
    {
        "name": "ASUS ROG Maximus Z790 Hero WiFi LGA1700 ATX Gaming Motherboard",
        "brand": "ASUS",
        "category": "PC Components",
        "subcomponent": "Motherboard",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 420,
        "original_price": 69990,
        "is_featured": True,
        "is_deal": False,
        "colors": ["Dark ROG Polymo Armor"],
        "storage_options": ["LGA1700 ATX"],
        "description": "Premium Intel Z790 flagship motherboard featuring 20+1 power stages, PCIe 5.0, Wi-Fi 6E, Thunderbolt 4, and Polymo Lighting.",
        "features": ["20+1 Power Stages (90A rating)", "Five M.2 Slots (Including PCIe 5.0 M.2)", "Dual Thunderbolt 4 USB-C Ports & Wi-Fi 6E"],
        "specs": {"Socket": "LGA1700 (14th/13th/12th Gen Intel)", "Form Factor": "ATX", "Memory Slots": "4x DDR5 (Up to 7800+ MHz)", "M.2 Slots": "5 Slots"},
        "prices": [
            {"retailer": "amazon", "price": 58990, "delivery": "Free Secured Delivery"},
            {"retailer": "flipkart", "price": 59990, "delivery": "Free Express Shipping"}
        ]
    },
    {
        "name": "MSI MAG B650 Tomahawk WiFi AMD AM5 ATX Gaming Motherboard",
        "brand": "MSI",
        "category": "PC Components",
        "subcomponent": "Motherboard",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.8,
        "review_count": 1290,
        "original_price": 27990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Matte Black"],
        "storage_options": ["AM5 ATX"],
        "description": "The gold-standard AM5 motherboard for AMD Ryzen 7000/8000 series with 14+2+1 Duet Rail Power, M.2 Shield Frozr, and 2.5G LAN.",
        "features": ["14+2+1 Phase Power Design", "Supports DDR5 Memory up to 6400+ MHz (OC)", "Lightning Gen 4 M.2 with Shield Frozr"],
        "specs": {"Socket": "AMD AM5", "Form Factor": "ATX", "RAM": "4x DDR5 Slots", "LAN / Wi-Fi": "2.5G LAN + Wi-Fi 6E"},
        "prices": [
            {"retailer": "amazon", "price": 21990, "delivery": "Free One-Day Delivery"},
            {"retailer": "flipkart", "price": 22490, "delivery": "Free Delivery"}
        ]
    },

    # --- Coolers & Power Supplies ---
    {
        "name": "NZXT Kraken Elite 360 RGB AIO Liquid CPU Cooler with 2.36\" LCD Display",
        "brand": "NZXT",
        "category": "PC Components",
        "subcomponent": "Cooling",
        "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 780,
        "original_price": 31990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Matte Black", "Matte White"],
        "storage_options": ["360mm Radiator"],
        "description": "Flagship 360mm AIO liquid cooler featuring a customizable 2.36-inch wide-angle LCD screen for displaying live CPU temps, GIFs, or custom graphics.",
        "features": ["2.36\" 640x640 LCD Screen at 60Hz", "Asetek 7th Gen High-Performance Pump", "3x F120 RGB Core Fans & CAM Software"],
        "specs": {"Radiator Size": "360mm", "Display": "2.36\" LCD", "Socket Support": "LGA1700, AM5, AM4", "Noise Level": "17.9 - 30.6 dBA"},
        "prices": [
            {"retailer": "amazon", "price": 26990, "delivery": "Free Next Day Delivery"},
            {"retailer": "croma", "price": 27990, "delivery": "Store Pickup Available"}
        ]
    },
    {
        "name": "Corsair RM1000x Shift 80+ Gold Fully Modular ATX 3.0 Power Supply",
        "brand": "Corsair",
        "category": "PC Components",
        "subcomponent": "PSU",
        "image": "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 940,
        "original_price": 23990,
        "is_featured": False,
        "is_deal": True,
        "colors": ["Black"],
        "storage_options": ["1000 Watts ATX 3.0"],
        "description": "Revolutionary side-mounted cable interface for easy PC building, native PCIe 5.0 12VHPWR GPU cables, and 80 PLUS Gold efficiency.",
        "features": ["1000W 80 PLUS Gold Certified Efficiency", "Side-Mounted Modular Cable Interface", "Native PCIe 5.0 12VHPWR 16-pin connector for RTX 4090/4080"],
        "specs": {"Wattage": "1000 Watts", "Efficiency": "80 PLUS Gold", "Standard": "ATX 3.0 & PCIe 5.0 Ready", "Warranty": "10 Years"},
        "prices": [
            {"retailer": "amazon", "price": 18490, "delivery": "Free One-Day Delivery"},
            {"retailer": "flipkart", "price": 18990, "delivery": "Free Express Delivery"}
        ]
    },

    # --- Gaming Monitors ---
    {
        "name": "ASUS ROG Swift 32-inch 4K 240Hz QD-OLED Gaming Monitor (PG32UCDM)",
        "brand": "ASUS",
        "category": "PC Components",
        "subcomponent": "Monitor",
        "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 310,
        "original_price": 149990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["ROG Armor Black"],
        "storage_options": ["32-inch 4K OLED"],
        "description": "World's premiere 32-inch 4K QD-OLED gaming monitor with breathtaking 240Hz refresh rate, 0.03ms response time, custom heatsink, and G-SYNC.",
        "features": ["32-inch 4K UHD (3840 x 2160) QD-OLED Panel", "Blistering 240Hz Refresh Rate & 0.03ms Response Time", "Custom Heatsink & Graphene Film Protection"],
        "specs": {"Screen Size": "32-inch", "Resolution": "4K UHD (3840x2160)", "Panel": "QD-OLED", "Refresh Rate": "240Hz", "Response Time": "0.03ms"},
        "prices": [
            {"retailer": "amazon", "price": 129990, "delivery": "Free Secured Delivery"},
            {"retailer": "croma", "price": 134990, "delivery": "Store Pickup Available"},
            {"retailer": "flipkart", "price": 136990, "delivery": "Free Express Shipping"}
        ]
    },

    # ==================== 9. GAMING CONSOLES ====================
    {
        "name": "Sony PlayStation 5 Console (Slim Disc Edition)",
        "brand": "Sony",
        "category": "Gaming Consoles",
        "image": "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=600&q=80",
        "gallery": ["https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=600&q=80"],
        "rating": 4.9,
        "review_count": 5210,
        "original_price": 54990,
        "is_featured": True,
        "is_deal": True,
        "colors": ["White"],
        "storage_options": ["1 TB Custom SSD"],
        "description": "Experience lightning-fast loading with an ultra-high speed 1TB SSD, deeper immersion with haptic feedback, adaptive triggers.",
        "features": ["1TB Ultra-High Speed Custom SSD", "DualSense Controller with Haptics", "4K 120Hz Gaming Support"],
        "specs": {"Processor": "Custom AMD Zen 2 8-core", "Storage": "1TB Custom NVMe SSD"},
        "prices": [
            {"retailer": "amazon", "price": 49990, "delivery": "Free One-Day Delivery"},
            {"retailer": "flipkart", "price": 50990, "delivery": "Free Express Delivery"},
            {"retailer": "croma", "price": 52990, "delivery": "Same Day Pickup"}
        ]
    }
]

# Category and Brand archetypes for infinite realistic product generation
CATEGORY_ARCHETYPES = {
    "Smartphones": {
        "brands": ["Apple", "Samsung", "OnePlus", "Google", "Xiaomi", "Realme", "Vivo", "Nothing", "Motorola", "iQOO", "OPPO", "Poco", "Honor"],
        "subtypes": [
            "Pro Max 5G", "Ultra 5G", "Pro 5G", "Plus 5G", "Lite 5G", "Foldable 5G", "Flip 5G", "Gaming Phone", "GT Neo Edition"
        ],
        "images": [
            "https://images.unsplash.com/photo-1511707171634-5f897ff02560?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1580910051074-3eb694886505?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1574944985070-8f3ebc6b79d2?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (14999, 149999)
    },
    "Laptops": {
        "brands": ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI", "Samsung", "LG", "Gigabyte", "Razer", "Microsoft"],
        "subtypes": [
            "OLED Creator Laptop", "Gaming Laptop RTX 4070", "UltraSlim Touch 14", "Studio Edition 16", "Convertible 2-in-1", "Pro 16 Workstation"
        ],
        "images": [
            "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (38990, 319990)
    },
    "Tablets": {
        "brands": ["Apple", "Samsung", "Xiaomi", "OnePlus", "Lenovo", "Realme", "Microsoft", "Huawei"],
        "subtypes": [
            "Pro 12.9-inch Wi-Fi + 5G", "Air 11-inch", "144Hz 2.8K Productivity Tab", "Drawing Pad with Pen", "Ultra Slim Tab"
        ],
        "images": [
            "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (18999, 134990)
    },
    "Headphones & Earbuds": {
        "brands": ["Sony", "Apple", "Bose", "Sennheiser", "JBL", "boAt", "Nothing", "OnePlus", "Marshall", "Jabra", "Audio-Technica", "Beats", "Realme", "Anker"],
        "subtypes": [
            "Wireless ANC Over-Ear Headphones", "True Wireless ANC Earbuds", "Hi-Res Studio Monitor", "Spatial Audio Earphones", "Sports Waterproof Earbuds"
        ],
        "images": [
            "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (1999, 42990)
    },
    "Smartwatches": {
        "brands": ["Apple", "Samsung", "Garmin", "OnePlus", "Amazfit", "Fitbit", "Noise", "Fire-Boltt", "Fossil", "Huawei", "Boat"],
        "subtypes": [
            "Titanium GPS Cellular 49mm", "Classic Rotating Bezel 47mm", "Multisport Solar GPS Watch", "Fitness Tracker AMOLED", "Endurance Pro Smartwatch"
        ],
        "images": [
            "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (2999, 89990)
    },
    "Televisions": {
        "brands": ["LG", "Samsung", "Sony", "TCL", "Xiaomi", "OnePlus", "Hisense", "Vu", "Panasonic", "Toshiba", "Acer"],
        "subtypes": [
            "55-inch 4K OLED Smart TV", "65-inch Neo QLED 144Hz TV", "75-inch Mini-LED Google TV", "43-inch 4K Crystal UHD TV", "Cinema OLED Master Series"
        ],
        "images": [
            "https://images.unsplash.com/photo-1593784991095-a205069470b6?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1509281373149-e957c6296406?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1461151304267-38535e780c79?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1593305841991-05c297ba4575?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (24999, 289990)
    },
    "Cameras": {
        "brands": ["Sony", "Canon", "Nikon", "Fujifilm", "GoPro", "DJI", "Panasonic", "Insta360", "Leica", "Sigma", "Olympus"],
        "subtypes": [
            "Full-Frame Mirrorless Body + Lens", "4K60 Action Camera Pro", "Pocket 3-Axis Gimbal Camera", "360-Degree VR Camera", "Vlogging Mirrorless Kit"
        ],
        "images": [
            "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1512790182412-b19e6d62bc39?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (28990, 299990)
    },
    "PC Components": {
        "brands": ["NVIDIA", "AMD", "Intel", "Corsair", "Samsung", "ASUS", "MSI", "G.Skill", "Gigabyte", "Crucial", "NZXT", "Western Digital", "Noctua", "Lian Li"],
        "subtypes": [
            "GeForce RTX 4080 Super 16GB GDDR6X", "Ryzen 7 7800X3D 8-Core 3D V-Cache Processor", "Core i9-14900K 24-Core Unlocked CPU",
            "990 Pro 2TB PCIe 4.0 NVMe SSD", "Trident Z5 RGB 32GB DDR5 6000MHz RAM", "ROG Maximus Z790 Hero WiFi Motherboard",
            "Kraken Elite 360 RGB LCD Liquid Cooler", "RM1000x Shift 80+ Gold Modular PSU", "ROG Swift 32-inch 4K 240Hz OLED Monitor"
        ],
        "images": [
            "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1555680202-c86f0e12f086?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1562976540-1502c2145186?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (3999, 199990)
    },
    "Gaming Consoles": {
        "brands": ["Sony", "Microsoft", "Nintendo", "Valve", "Asus", "Lenovo", "Logitech", "Razer", "Meta"],
        "subtypes": [
            "Next-Gen 4K 120Hz Console 1TB", "OLED Handheld Gaming PC 512GB", "Wireless VR Headset 256GB", "Wireless Pro Gaming Controller", "Cloud Gaming Handheld"
        ],
        "images": [
            "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1621259182978-fbf93132d53d?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1612287271162-26507b1b3850?auto=format&fit=crop&w=600&q=80"
        ],
        "price_range": (16999, 69990)
    }
}

RETAILERS = ["amazon", "flipkart", "croma", "reliance", "vijaysales"]


def detect_subcomponent_from_query(query_text="", product_name=""):
    """
    Identifies the sub-component category (GPU, CPU, RAM, SSD, Motherboard, Cooling, PSU, Monitor) for PC Components.
    """
    text = (str(query_text) + " " + str(product_name)).lower()
    if any(k in text for k in ["gpu", "graphics card", "rtx", "gtx", "radeon", "geforce", "vram", "4090", "4080", "4070", "7900"]):
        return "GPU"
    if any(k in text for k in ["cpu", "processor", "ryzen", "intel core", "i9", "i7", "i5", "7800x3d", "14900k", "14700k", "socket"]):
        return "CPU"
    if any(k in text for k in ["ssd", "nvme", "storage", "m.2", "990 pro", "sn850x", "sata"]):
        return "SSD"
    if any(k in text for k in ["ram", "ddr5", "ddr4", "memory", "trident", "vengeance", "6000mhz"]):
        return "RAM"
    if any(k in text for k in ["motherboard", "mobo", "z790", "b650", "x670", "lga1700", "am5"]):
        return "Motherboard"
    if any(k in text for k in ["cooler", "cooling", "aio", "liquid cooler", "kraken", "radiator", "fan"]):
        return "Cooling"
    if any(k in text for k in ["psu", "power supply", "watt", "1000w", "850w", "modular"]):
        return "PSU"
    if any(k in text for k in ["monitor", "display", "240hz", "144hz", "oled monitor"]):
        return "Monitor"
    return "PC Part"


def detect_category_from_query(query_text):
    """
    Infers the most appropriate category for any search query.
    """
    q = query_text.lower() if query_text else ""
    if any(k in q for k in ["rtx", "gtx", "gpu", "cpu", "ram", "ssd", "nvme", "ddr5", "ryzen", "intel core", "i9", "i7", "motherboard", "mobo", "psu", "liquid cooler", "graphics card", "processor", "pc component", "pc parts", "gaming monitor"]):
        return "PC Components"
    if any(k in q for k in ["phone", "iphone", "galaxy s", "pixel", "oneplus", "smartphone", "mobile", "redmi", "vivo", "oppo", "iqoo", "nord"]):
        return "Smartphones"
    if any(k in q for k in ["laptop", "macbook", "thinkpad", "zenbook", "notebook", "omen", "legion", "predator", "xps", "spectre", "vivobook"]):
        return "Laptops"
    if any(k in q for k in ["tablet", "ipad", "tab", "pad"]):
        return "Tablets"
    if any(k in q for k in ["headphone", "earbud", "earphone", "airpods", "speaker", "audio", "anc", "soundbar", "tws", "xm5", "bose"]):
        return "Headphones & Earbuds"
    if any(k in q for k in ["watch", "smartwatch", "band", "fitness", "garmin", "fitbit", "noise"]):
        return "Smartwatches"
    if any(k in q for k in ["tv", "television", "oled", "qled", "bravia", "4k tv", "smart tv"]):
        return "Televisions"
    if any(k in q for k in ["camera", "lens", "gopro", "dslr", "mirrorless", "vlog", "dji", "action camera", "osmo", "lumix"]):
        return "Cameras"
    if any(k in q for k in ["ps5", "playstation", "xbox", "nintendo", "switch", "steam deck", "handheld", "console", "rog ally"]):
        return "Gaming Consoles"
    return random.choice(list(CATEGORY_ARCHETYPES.keys()))
    return random.choice(list(CATEGORY_ARCHETYPES.keys()))


def synthesize_products_for_query(query, category_name=None, brand_name=None, count=8):
    """
    Dynamically generates realistic, customized matching electronics products on-the-fly
    for ANY search query or filter combination, ensuring ElectroCompare NEVER says 'No Products'.
    """
    cat = category_name if category_name and category_name != 'All' else detect_category_from_query(query)
    archetype = CATEGORY_ARCHETYPES.get(cat, CATEGORY_ARCHETYPES["Smartphones"])

    # Determine brand
    extracted_brand = None
    if brand_name and brand_name != 'All':
        extracted_brand = brand_name
    elif query:
        for b in archetype["brands"]:
            if b.lower() in query.lower():
                extracted_brand = b
                break

    clean_query_words = re.sub(r'[^a-zA-Z0-9\s]', '', query).title() if query else ""
    
    generated = []
    min_p, max_p = archetype["price_range"]

    variants = ["Pro Max (256GB)", "Ultra 5G (16GB RAM)", "Plus Edition", "Special Creator Edition", "OLED Edition", "Wireless V2", "5G Dual SIM", "Slim Disc 1TB"]

    for i in range(count):
        brand = extracted_brand or random.choice(archetype["brands"])
        subtype = random.choice(archetype["subtypes"])
        variant = variants[i % len(variants)]
        
        if clean_query_words and len(clean_query_words) > 2:
            name = f"{brand} {clean_query_words} {variant}" if brand.lower() not in clean_query_words.lower() else f"{clean_query_words} {variant}"
        else:
            name = f"{brand} {subtype} {variant}"

        img = random.choice(archetype["images"])
        base_price = round(random.uniform(min_p, max_p) / 100) * 100
        original_price = round(base_price * random.uniform(1.12, 1.35) / 100) * 100

        # Multi-retailer price spread (strictly 4 or 5 famous retailers)
        num_stores = random.randint(4, 5)
        chosen_ret = random.sample(RETAILERS, num_stores)
        prices = []
        for r in chosen_ret:
            ret_price = round(base_price * random.uniform(0.96, 1.05) / 100) * 100
            deliv = random.choice(["Free Express Delivery", "Free 1-Day Delivery", "Free Standard Delivery", "Same Day Pickup"])
            prices.append({"retailer": r, "price": ret_price, "delivery": deliv})

        item = {
            "name": name,
            "brand": brand,
            "category": cat,
            "image": img,
            "gallery": [img],
            "rating": round(random.uniform(4.4, 4.9), 1),
            "review_count": random.randint(120, 6800),
            "original_price": original_price,
            "is_featured": (i % 3 == 0),
            "is_deal": True,
            "colors": ["Titanium Black", "Silver", "Midnight Blue", "Graphite"],
            "storage_options": ["128 GB", "256 GB", "512 GB", "1 TB"],
            "description": f"Verified flagship {name} featuring premium construction, manufacturer warranty, and instant multi-store live price comparison across Amazon, Flipkart, Croma, Reliance Digital, and Vijay Sales.",
            "features": [
                f"Flagship performance tuned by {brand}",
                "Ultra-fast charging & extended battery optimization",
                "Crystal-clear display with high dynamic range",
                "Instant store price tracking and drop alert compatibility"
            ],
            "specs": {
                "Brand": brand,
                "Category": cat,
                "Warranty": "1 Year Official Brand Warranty",
                "Availability": "In Stock Across Top Stores"
            },
            "prices": prices
        }
        generated.append(item)

    return generated


def generate_synthetic_catalog_batch(category_name=None, brand_name=None, count=15):
    """
    General infinite catalog expansion helper.
    """
    return synthesize_products_for_query(query="", category_name=category_name, brand_name=brand_name, count=count)

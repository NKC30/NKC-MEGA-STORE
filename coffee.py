import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import random
import os

# ==========================================
# 0. PAGE CONFIG & ADVANCED COLORFUL CSS
# ==========================================
st.set_page_config(
    page_title="NKC Megastore & EatInMinutes | Online Shopping & 30-Min Delivery", 
    page_icon="⚡", 
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #f8fafc;
        }
        
        .main-header {
            background: linear-gradient(90deg, #ec4899 0%, #8b5cf6 50%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            padding: 10px 0;
        }
        
        div[data-testid="stBlock"] {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }
        div[data-testid="stBlock"]:hover {
            transform: translateY(-5px);
            border-color: #8b5cf6;
        }

        .badge-fast {
            background-color: #ef4444;
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        .badge-store {
            background-color: #3b82f6;
            color: white;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .stButton > button {
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
            color: white !important;
            border: none;
            border-radius: 10px;
            font-weight: bold;
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.6);
            transform: scale(1.02);
        }

        div[data-testid="stMetricValue"] {
            color: #38bdf8 !important;
            font-size: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATABASE COMPONENT LAYER
# ==========================================
if not os.path.exists("db_initialized.flag"):
    if os.path.exists("nkc_superstore.db"):
        try: os.remove("nkc_superstore.db")
        except Exception: pass
    with open("db_initialized.flag", "w") as f: f.write("initialized")

class DBManager:
    def __init__(self):
        self.db = "nkc_superstore.db"
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    item_name TEXT UNIQUE, 
                    price REAL, 
                    category TEXT,
                    store_type TEXT,
                    image_url TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    phone TEXT, 
                    address TEXT,
                    store_type TEXT,
                    order_type TEXT,
                    items TEXT, 
                    bill REAL, 
                    status TEXT DEFAULT 'Pending',
                    time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("CREATE TABLE IF NOT EXISTS promos (code TEXT PRIMARY KEY, discount REAL)")
            c.execute("CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, rating INTEGER, review TEXT, time DATETIME DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, val TEXT)")
            
            c.execute("INSERT OR IGNORE INTO promos VALUES ('NKC50', 50.0), ('EAT100', 100.0), ('SUPER30', 30.0)")
            
            c.execute("SELECT COUNT(*) FROM inventory")
            if c.fetchone()[0] == 0:
                items = [
                    # --- EAT IN MINUTES ---
                    ("Hot Cappuccino Coffee", 160.0, "Beverages", "EatInMinutes", "https://images.unsplash.com/photo-1534778101976-62847782c213?w=600"),
                    ("Hazelnut Cold Brew", 190.0, "Beverages", "EatInMinutes", "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=600"),
                    ("Grilled Cheese Panini", 180.0, "Quick Snacks", "EatInMinutes", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=600"),
                    ("Loaded Veggie Burger", 150.0, "Quick Snacks", "EatInMinutes", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600"),
                    ("Crispy Pepperoni Pizza Slice", 220.0, "Main Course", "EatInMinutes", "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600"),
                    ("Crispy Golden Fries", 125.0, "Quick Snacks", "EatInMinutes", "https://images.unsplash.com/photo-1576107232684-1279f390859f?w=600"),
                    ("Choco Chip Fudge Cookie", 80.0, "Desserts", "EatInMinutes", "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=600"),
                    ("Red Velvet Cream Slice", 165.0, "Desserts", "EatInMinutes", "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?w=600"),

                    # --- NKC STORE ---
                    ("Wireless ANC Headphones", 2499.0, "Electronics", "NKC Store", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600"),
                    ("Smart Fitness Watch Pro", 3199.0, "Electronics", "NKC Store", "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600"),
                    ("RGB Mechanical Keyboard", 1899.0, "Electronics", "NKC Store", "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600"),
                    ("True Wireless Earbuds", 1499.0, "Electronics", "NKC Store", "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600"),
                    ("Urban Streetwear Hoodie", 1299.0, "Fashion", "NKC Store", "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600"),
                    ("Classic Denim Jacket", 2199.0, "Fashion", "NKC Store", "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600"),
                    ("Stainless Hydro Bottle 1L", 799.0, "Lifestyle", "NKC Store", "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600"),
                    ("Minimalist Leather Wallet", 499.0, "Lifestyle", "NKC Store", "https://images.unsplash.com/photo-1627123424574-724758594e93?w=600")
                ]
                c.executemany("INSERT INTO inventory (item_name, price, category, store_type, image_url) VALUES (?, ?, ?, ?, ?)", items)
            
            default_pin = hashlib.sha256("nkc2026".encode()).hexdigest()
            c.execute("INSERT OR IGNORE INTO config (key, val) VALUES ('pin', ?)", (default_pin,))

    def run_q(self, q, params=(), commit=False, select=False):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            c.execute(q, params)
            if commit: conn.commit()
            if select: return c.fetchall()

db = DBManager()

# ==========================================
# 2. SESSION STATE
# ==========================================
for key, default in [("cart", {}), ("otp", None), ("pending", None), ("last_order_id", None), ("discount", 0)]:
    if key not in st.session_state: st.session_state[key] = default

# ==========================================
# 3. HEADER & NAVIGATION
# ==========================================
st.markdown("<div class='main-header'>🏪 NKC MEGASTORE & ⚡ EatInMinutes</div>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a855f7; font-weight: 600;'>Your One-Stop Platform for 30-Min Food & E-Commerce Shopping</p>", unsafe_allow_html=True)
st.write("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⚡ EatInMinutes", 
    "🛍️ NKC Store", 
    "🛒 Cart & Checkout", 
    "🚚 Order Tracker", 
    "⭐ Reviews",
    "🔒 Admin Panel"
])

def render_catalog(store_filter, search_key, badge_html):
    col_s1, col_s2 = st.columns([3, 1])
    search_query = col_s1.text_input("🔎 Search products by name...", key=search_key)
    
    if search_query:
        res = db.run_q("SELECT * FROM inventory WHERE store_type = ? AND item_name LIKE ?", (store_filter, f"%{search_query}%"), select=True)
    else:
        res = db.run_q("SELECT * FROM inventory WHERE store_type = ?", (store_filter,), select=True)
        
    df = pd.DataFrame(res, columns=["id", "item_name", "price", "category", "store_type", "image_url"]) if res else pd.DataFrame()
    
    if df.empty: 
        st.info("No items match your search.")
    else:
        for cat in df['category'].unique():
            st.markdown(f"### 🏷️ {cat}")
            cols = st.columns(4)
            cat_df = df[df['category'] == cat].reset_index(drop=True)
            
            for idx, row in cat_df.iterrows():
                with cols[idx % 4]:
                    with st.container():
                        st.markdown(f"{badge_html}", unsafe_allow_html=True)
                        st.image(row['image_url'], use_container_width=True)
                        st.markdown(f"#### {row['item_name']}")
                        st.markdown(f"<h3 style='color:#38bdf8; margin:0;'>₹{row['price']}</h3>", unsafe_allow_html=True)
                        st.write("")
                        
                        if st.button("➕ Add to Cart", key=f"add_{row['id']}"):
                            item_data = st.session_state.cart.get(row['item_name'], {'price': row['price'], 'qty': 0, 'store': row['store_type']})
                            item_data['qty'] += 1
                            st.session_state.cart[row['item_name']] = item_data
                            st.toast(f"Added {row['item_name']} to Cart!", icon="🛒")

# ------------------------------------------
# TAB 1: EAT IN MINUTES
# ------------------------------------------
with tab1:
    st.subheader("⚡ Quick Commerce: Food & Drinks Delivered in 30 Minutes")
    render_catalog("EatInMinutes", "search_eat", "<span class='badge-fast'>⚡ 30 MIN EXPRESS</span>")

# ------------------------------------------
# TAB 2: NKC STORE
# ------------------------------------------
with tab2:
    st.subheader("📦 NKC Store: Premium Shopping Collection")
    render_catalog("NKC Store", "search_store", "<span class='badge-store'>🛍️ STORE ITEM</span>")

# ------------------------------------------
# TAB 3: CART & CHECKOUT
# ------------------------------------------
with tab3:
    st.subheader("🛒 Interactive Cart Management")
    if not st.session_state.cart: 
        st.info("Your shopping cart is empty. Explore items from the tabs above!")
    else:
        subtotal = 0.0
        items_list = []
        to_delete = None

        for item, details in list(st.session_state.cart.items()):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"**{item}**<br><small style='color:#a855f7;'>[{details.get('store', 'Store')}]</small>", unsafe_allow_html=True)
            c2.markdown(f"<h4 style='color:#38bdf8;'>₹{details['price']}</h4>", unsafe_allow_html=True)
            new_qty = c3.number_input("Qty", min_value=1, max_value=20, value=details['qty'], key=f"q_{item}")
            st.session_state.cart[item]['qty'] = new_qty
            
            if c4.button("🗑️", key=f"r_{item}"):
                to_delete = item

            subtotal += details['price'] * new_qty
            items_list.append(f"{item}(x{new_qty})")
        
        if to_delete:
            del st.session_state.cart[to_delete]
            st.rerun()
        
        st.write("---")
        
        col_type, col_promo = st.columns(2)
        with col_type:
            st.subheader("🚚 Select Order Mode")
            order_type = st.radio("Fulfillment Options:", ["30-Min Home Delivery 🛵", "Store Pickup / Dine-In 🍽️"])
        
        with col_promo:
            st.subheader("🎁 Promo Coupons")
            coupon = st.text_input("Enter Code (e.g. NKC50, EAT100):")
            if st.button("Apply Discount"):
                code = coupon.strip().upper()
                promo_res = db.run_q("SELECT discount FROM promos WHERE code = ?", (code,), select=True)
                if promo_res:
                    st.session_state.discount = promo_res[0][0]
                    st.toast(f"Applied ₹{st.session_state.discount} Discount!", icon="🎉")
                else:
                    st.session_state.discount = 0
                    st.error("Invalid Code")

        discount_amount = st.session_state.discount
        final_total = max(0.0, subtotal - discount_amount)

        st.markdown(f"#### Subtotal: **₹{subtotal:.2f}**")
        if discount_amount > 0:
            st.markdown(f"#### Promo Discount: <span style='color:#ef4444;'>-₹{discount_amount:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"## Total Payable: <span style='color:#22c55e;'>₹{final_total:.2f}</span>", unsafe_allow_html=True)

        st.write("---")
        st.subheader("🔒 Verification & Secure Checkout")
        
        with st.form("checkout"):
            name = st.text_input("Customer Full Name:")
            phone = st.text_input("10-Digit Mobile Number:", max_chars=10)
            address = st.text_area("Complete Address (Optional for Dine-In):")
            submit_otp = st.form_submit_button("Generate Verification OTP")
            
            if submit_otp:
                if len(phone) == 10 and phone.isdigit() and name.strip():
                    st.session_state.otp = str(random.randint(100000, 999999))
                    st.session_state.pending = {
                        'name': name.strip(), 
                        'phone': phone, 
                        'address': address.strip() if address.strip() else "Pickup/Dine-In",
                        'order_type': order_type,
                        'items': ", ".join(items_list), 
                        'total': final_total
                    }
                    st.success("📲 OTP Generated Below!")
                else: 
                    st.error("Please enter a valid Name and 10-Digit Mobile Number.")

        if st.session_state.otp:
            st.warning(f"🔑 **Simulated Security OTP:** `{st.session_state.otp}`")
            user_otp = st.text_input("Enter the 6-Digit Code displayed above:", max_chars=6)
            
            if st.button("Verify & Place Order"):
                if user_otp == st.session_state.otp:
                    p = st.session_state.pending
                    db.run_q(
                        "INSERT INTO orders (name, phone, address, store_type, order_type, items, bill, status) VALUES (?, ?, ?, 'Combined', ?, ?, ?, 'Pending')", 
                        (p['name'], p['phone'], p['address'], p['order_type'], p['items'], p['total']), 
                        commit=True
                    )
                    
                    last_id = db.run_q("SELECT max(id) FROM orders", select=True)[0][0]
                    st.session_state.last_order_id = last_id
                    
                    st.success(f"🎉 Order #{last_id} Successfully Confirmed!")
                    st.balloons()
                    
                    st.session_state.cart = {}
                    st.session_state.otp = None
                    st.session_state.pending = None
                    st.session_state.discount = 0
                    st.rerun()
                else: 
                    st.error("Incorrect Verification Code.")

# ------------------------------------------
# TAB 4: ORDER TRACKING
# ------------------------------------------
with tab4:
    st.subheader("🚚 Live Visual Order Status Tracker")
    
    search_id = st.number_input("Enter Order ID Number:", min_value=1, step=1, value=st.session_state.last_order_id if st.session_state.last_order_id else 1)
    
    if st.button("Track Progress"):
        res = db.run_q("SELECT id, name, items, bill, status, address, order_type, time FROM orders WHERE id = ?", (search_id,), select=True)
        if res:
            order = res[0]
            st.success(f"Order #{order[0]} Records Found!")
            
            col_a, col_b = st.columns(2)
            col_a.metric("Customer Name", order[1])
            col_a.metric("Total Bill Amount", f"₹{order[3]}")
            col_b.metric("Current Live Status", order[4])
            col_b.write(f"**Fulfillment Mode:** {order[6]}")
            col_b.write(f"**Ordered Items:** {order[2]}")
            col_b.write(f"**Delivery Location:** {order[5]}")
            
            status_map = {"Pending": 20, "Packed/Preparing": 50, "Out for Delivery": 80, "Delivered": 100}
            st.progress(status_map.get(order[4], 10))
        else:
            st.error("Order ID not found.")

# ------------------------------------------
# TAB 5: REVIEWS & FEEDBACK
# ------------------------------------------
with tab5:
    st.subheader("⭐ Customer Reviews & Product Ratings")
    
    all_items = [r[0] for r in db.run_q("SELECT item_name FROM inventory", select=True)]
    selected_item = st.selectbox("Select Product to Rate:", all_items)
    
    rating = st.slider("Rating Score (1 to 5 Stars):", 1, 5, 5)
    review_text = st.text_area("Write Your Feedback:")
    
    if st.button("Publish Review"):
        if review_text.strip():
            db.run_q("INSERT INTO reviews (item_name, rating, review) VALUES (?, ?, ?)", (selected_item, rating, review_text.strip()), commit=True)
            st.success("Review Published Successfully!")
            st.rerun()
            
    st.write("---")
    st.markdown(f"### Recent Customer Feedback for **{selected_item}**")
    revs = db.run_q("SELECT rating, review, time FROM reviews WHERE item_name = ? ORDER BY id DESC", (selected_item,), select=True)
    if revs:
        for r in revs:
            st.markdown(f"⭐ **{r[0]}/5 Stars** — *\"{r[1]}\"* `<small style='color:#a855f7;'>({r[2]})</small>`", unsafe_allow_html=True)
    else:
        st.info("No reviews submitted for this product yet.")

# ------------------------------------------
# TAB 6: ADMIN DASHBOARD
# ------------------------------------------
with tab6:
    st.subheader("🔒 Administrative Control Center")
    pin = st.text_input("Enter Security PIN (Default: nkc2026):", type="password")
    
    if pin:
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        stored_pin = db.run_q("SELECT val FROM config WHERE key='pin'", select=True)
        
        if stored_pin and pin_hash == stored_pin[0][0]:
            st.success("Access Authorized.")
            
            st.markdown("### 📊 Business Analytics Chart")
            orders_raw = db.run_q("SELECT * FROM orders ORDER BY id DESC", select=True)
            
            if orders_raw:
                df_orders = pd.DataFrame(orders_raw, columns=["ID", "Name", "Phone", "Address", "Store", "OrderType", "Items", "Bill", "Status", "Time"])
                
                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("Total Completed Orders", len(df_orders))
                c_m2.metric("Gross Revenue Earned", f"₹{df_orders['Bill'].sum():.2f}")
                c_m3.metric("Average Order Ticket", f"₹{df_orders['Bill'].mean():.2f}")
                
                st.line_chart(df_orders.groupby('Time')['Bill'].sum())
                
                st.write("---")
                st.markdown("### 📋 Manage Customer Orders & Status")
                for idx, row in df_orders.iterrows():
                    with st.expander(f"Order #{row['ID']} - {row['Name']} (₹{row['Bill']}) - Current Status: {row['Status']}"):
                        c_info, c_status = st.columns([2, 1])
                        c_info.write(f"**Phone:** {row['Phone']}")
                        c_info.write(f"**Type:** {row['OrderType']}")
                        c_info.write(f"**Address:** {row['Address']}")
                        c_info.write(f"**Items:** {row['Items']}")
                        
                        status_options = ["Pending", "Packed/Preparing", "Out for Delivery", "Delivered"]
                        new_status = c_status.selectbox(
                            "Update Status", status_options, 
                            index=status_options.index(row['Status']) if row['Status'] in status_options else 0,
                            key=f"status_{row['ID']}"
                        )
                        if c_status.button("Save Status Change", key=f"btn_status_{row['ID']}"):
                            db.run_q("UPDATE orders SET status = ? WHERE id = ?", (new_status, row['ID']), commit=True)
                            st.toast(f"Order #{row['ID']} Updated to {new_status}")
                            st.rerun()

            st.write("---")
            st.markdown("### ⚙️ Add New Products & Custom Promo Coupons")
            col_add, col_promo = st.columns(2)
            
            with col_add.form("add_item"):
                st.markdown("#### Add New Product to Store")
                n = st.text_input("Item Name:")
                p = st.number_input("Price (₹):", min_value=1.0, value=100.0)
                st_type = st.selectbox("Assign to Section:", ["EatInMinutes", "NKC Store"])
                c = st.text_input("Category Name:", value="General")
                img = st.text_input("Product Image Web URL:", value="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600")
                if st.form_submit_button("Add Product"):
                    if n.strip():
                        db.run_q("INSERT INTO inventory (item_name, price, category, store_type, image_url) VALUES (?, ?, ?, ?, ?)", (n.strip(), p, c.strip(), st_type, img.strip()), commit=True)
                        st.success("Product Added Successfully!")
                        st.rerun()

            with col_promo.form("add_promo"):
                st.markdown("#### Create Custom Promo Coupon")
                pr_code = st.text_input("Coupon Name:")
                pr_disc = st.number_input("Discount Value (₹):", min_value=1.0, value=50.0)
                if st.form_submit_button("Generate Code"):
                    if pr_code.strip():
                        db.run_q("INSERT OR REPLACE INTO promos VALUES (?, ?)", (pr_code.strip().upper(), pr_disc), commit=True)
                        st.success(f"Coupon '{pr_code.strip().upper()}' Created!")
                        st.rerun()
        else:
            st.error("Access Denied.")
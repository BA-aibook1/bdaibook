import os
import sqlite3
import random
import uuid
import base64
import urllib.parse
import hashlib
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Global Verified Network",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

components.html(
    """
    <meta name="msvalidate.01" content="e776b8ce73ea3dcc07551e8a021a0907">
    <meta name="monetag" content="5cc1b7ba5cb29eff802ce49009f87e2b">
    """,
    height=0,
)

SMART_LINK = "https://omg10.com/4/10954816"

# ==========================================
# 2. LOCAL STORAGE & DATABASE SETUP
# ==========================================
DB_FILE = "local_storage.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
PROFILE_DIR = "stored_profiles"

for folder in [VIDEO_DIR, IMAGE_DIR, PROFILE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            clean_phone TEXT UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            profile_pic TEXT,
            bio TEXT,
            is_verified INTEGER DEFAULT 1,
            payment_method TEXT,
            account_details TEXT,
            nid_number TEXT,
            address TEXT,
            followers_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'none',
            earnings REAL DEFAULT 0.0,
            role TEXT DEFAULT 'user',
            created_at TEXT
        )
    """)

    # 2. Daily Upload Logs (Limit Checking)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_upload_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content_type TEXT NOT NULL,
            upload_date TEXT NOT NULL
        )
    """)

    # 3. Advertisements Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertisements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            advertiser_email TEXT,
            ad_type TEXT,
            content_link TEXT,
            duration_months INTEGER,
            region TEXT,
            payment_method TEXT,
            amount REAL,
            trx_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    # 4. Bank Details Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            payment_type TEXT DEFAULT 'Bank Transfer',
            bank_name TEXT,
            branch_name TEXT,
            account_name TEXT,
            account_number TEXT,
            routing_number TEXT,
            swift_code TEXT,
            card_number TEXT,
            card_holder TEXT,
            card_expiry TEXT,
            global_wallet TEXT,
            mobile_banking TEXT,
            country TEXT,
            updated_at TEXT,
            FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE ON UPDATE CASCADE
        )
    """)

    # 5. Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            video_url TEXT,
            uploader_name TEXT,
            uploader_pic TEXT,
            video_type TEXT DEFAULT 'long',
            duration_mins REAL DEFAULT 0.0,
            title TEXT,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # 6. Posts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            uploader_pic TEXT,
            content TEXT,
            image_url TEXT,
            likes INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # 7. Comments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            post_id TEXT,
            uploader_name TEXT,
            comment_text TEXT,
            gift_type TEXT,
            created_at TEXT
        )
    """)

    # Owner Account Setup
    owner_email = "rasohel1234@gmail.com"
    hashed_pw = hashlib.sha256("S$s123456789112233".encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username = ?", (owner_email,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, phone_number, clean_phone, password, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (owner_email, "01722003172", "01722003172", hashed_pw, "MD. SOHEL RANA", "owner", datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. HELPER & LIMIT CHECKING FUNCTIONS
# ==========================================
def normalize_phone(phone_str):
    if not phone_str:
        return ""
    return "".join(filter(str.isdigit, str(phone_str)))

def mask_phone_number(phone):
    if not phone:
        return ""
    clean_p = normalize_phone(phone)
    if len(clean_p) >= 10:
        return "+" + clean_p[:3] + "*****" + clean_p[-3:]
    elif len(clean_p) > 4:
        return clean_p[:2] + "****" + clean_p[-2:]
    return clean_p

def format_value(value):
    if value is None:
        return "0"
    if value >= 1000000:
        return f"{value/1000000:.1f}M"
    if value >= 1000:
        return f"{value/1000:.1f}K"
    return str(value)

def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception:
            return None
    return None

def check_daily_limit(username, content_type, limit):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) as count FROM daily_upload_limits 
        WHERE username = ? AND content_type = ? AND upload_date = ?
    """, (username, content_type, today_str))
    res = cursor.fetchone()
    conn.close()
    count = res['count'] if res else 0
    return count < limit, count

def record_upload(username, content_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO daily_upload_limits (username, content_type, upload_date)
        VALUES (?, ?, ?)
    """, (username, content_type, today_str))
    conn.commit()
    conn.close()

def show_verified_profile(display_name, profile_pic_path=None, subtitle="Official Creator", is_verified=True):
    b64_img = get_image_base64(profile_pic_path)
    if b64_img:
        img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; border:2px solid #1877F2;">'
    else:
        img_html = '<div style="width:50px; height:50px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:24px;">👤</div>'

    blue_tick_svg = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="margin-left: 6px; vertical-align: middle;">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#1877F2"/>
    </svg>""" if is_verified else ""

    html_code = f"""<div style="display: flex; align-items: center; gap: 12px; background: #18191a; padding: 12px; border-radius: 12px; border: 1px solid #2d2f31; margin-bottom: 12px;">
        <div>{img_html}</div>
        <div>
            <div style="display: flex; align-items: center; font-weight: 700; font-size: 17px; color: #e4e6eb; font-family: sans-serif;">
                <span>{display_name}</span>
                {blue_tick_svg}
            </div>
            <div style="color: #b0b3b8; font-size: 12px; margin-top: 1px;">{subtitle}</div>
        </div>
    </div>"""
    st.markdown(html_code, unsafe_allow_html=True)

def show_auto_moving_banner():
    ad_html = f"""
    <div style="text-align:center; margin: 15px 0;">
        <a href="{SMART_LINK}" target="_blank" style="text-decoration:none;">
            <div style="background: linear-gradient(90deg, #1877F2, #00c853); color: #fff; padding: 14px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 1px solid #3a3b3c; font-family: sans-serif;">
                <span style="font-size: 15px; font-weight: bold;">⚡ GLOBAL AUTOMATIC MONETIZATION ACTIVE ⚡</span><br>
                <span style="font-size: 12px;">Click to Boost Earnings & Claim Reward Bonus!</span>
            </div>
        </a>
    </div>
    """
    components.html(ad_html, height=95)

def render_comments_section(post_id):
    with st.expander("💬 Comments & Gifts"):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY created_at DESC", (post_id,))
        all_comments = [dict(r) for r in cursor.fetchall()]
        
        if all_comments:
            for c in all_comments:
                gift_badge = f" <span style='background:#3a3b3c; padding:2px 6px; border-radius:6px;'>{c['gift_type']}</span>" if c.get('gift_type') and c.get('gift_type') != "None" else ""
                st.markdown(f"**{c['uploader_name']}**{gift_badge} <small style=\"color:#888;\">({c['created_at']})</small>:<br>{c['comment_text']}", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.caption("No comments yet.")
            
        if st.session_state.user:
            with st.form(key=f"c_form_{post_id}"):
                c_input = st.text_input("Write a comment...", key=f"inp_{post_id}")
                gift_selected = st.selectbox("🎁 Select Gift", ["None", "🎁 Gift Box (+10 pts)", "💎 Diamond (+50 pts)", "🌟 Star (+20 pts)"], key=f"gft_{post_id}")
                submit_btn = st.form_submit_button("Post Comment")
                
                if submit_btn:
                    if c_input.strip():
                        now_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                        cursor.execute("""
                            INSERT INTO comments (id, post_id, uploader_name, comment_text, gift_type, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (str(uuid.uuid4()), post_id, st.session_state.user, c_input.strip(), gift_selected, now_time))
                        conn.commit()
                        conn.close()
                        st.toast("✅ Comment published successfully!")
                        st.rerun()
                    else:
                        st.warning("Comment cannot be empty!")
                        conn.close()
        else:
            st.info("Log in to leave a comment.")
            conn.close()

# ==========================================
# 4. CUSTOM STYLING
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background-color: #242526 !important; color: #ffffff !important; border: 1px solid #3a3b3c !important;
    }
    textarea, input { color: #ffffff !important; background-color: #242526 !important; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    .monetization-box { background: linear-gradient(135deg, #00b09b, #96c93d); color: white; padding: 18px; border-radius: 12px; margin-top: 15px; margin-bottom: 15px; }
    .btn-direct { display: block; width: 100%; padding: 10px; margin: 6px 0; color: white !important; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SESSION INITIALIZATION
# ==========================================
if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.user_phone = None
    st.session_state.pic = None
    st.session_state.is_verified = 0
    st.session_state.role = 'user'

if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None
if 'otp_sent_to' not in st.session_state:
    st.session_state.otp_sent_to = None
if 'show_reset_mode' not in st.session_state:
    st.session_state.show_reset_mode = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# Main Header
st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #00c853; font-weight: 900; margin: 0;">🔥 BD AI Book — Global Platform 🔥</h1>
        <p style="color: #b0b3b8; margin: 0;">Artificial Intelligence & Learning Platform for Everyone Worldwide</p>
    </div>
""", unsafe_allow_html=True)
st.divider()

# ==========================================
# 6. SIDEBAR AUTHENTICATION
# ==========================================
st.sidebar.header("📱 User Authentication")

if not st.session_state.user:
    phone_input = st.sidebar.text_input("Phone / Email", placeholder="rasohel1234@gmail.com or +880...", key="auth_phone")
    
    if phone_input.strip():
        clean_input = normalize_phone(phone_input)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR clean_phone = ? OR phone_number = ?", 
                       (phone_input.strip(), clean_input, phone_input.strip()))
        user_record = cursor.fetchone()
        conn.close()
        
        if user_record:
            st.sidebar.success(f"✅ User Found: **{user_record['username']}**")
            login_pass = st.sidebar.text_input("Password", type="password", key="login_pass")
            
            if st.sidebar.button("🔓 Login Now"):
                hashed_input = hashlib.sha256(login_pass.encode()).hexdigest()
                if user_record['password'] == login_pass or user_record['password'] == hashed_input:
                    st.session_state.user = user_record['username']
                    st.session_state.user_phone = user_record['phone_number']
                    st.session_state.pic = user_record['profile_pic']
                    st.session_state.is_verified = 1
                    st.session_state.role = user_record['role']
                    st.sidebar.success("🎉 Logged in Successfully.")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Incorrect Password!")
        else:
            st.sidebar.info("🆕 New User Registration")
            if st.sidebar.button("📲 Send WhatsApp OTP"):
                otp_code = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp_code
                st.session_state.otp_sent_to = clean_input
                msg = f"Your BD AI Book Verification OTP is: {otp_code}"
                wa_url = f"https://wa.me/{clean_input}?text={urllib.parse.quote(msg)}"
                st.sidebar.success(f"OTP: **{otp_code}**")
                st.sidebar.markdown(f"[👉 Send OTP via WhatsApp]({wa_url})", unsafe_allow_html=True)
            
            if st.session_state.generated_otp and st.session_state.otp_sent_to == clean_input:
                entered_otp = st.sidebar.text_input("Enter 6-Digit OTP", max_chars=6)
                desired_username = st.sidebar.text_input("Create Username")
                new_password = st.sidebar.text_input("Create Password", type="password")
                
                if st.sidebar.button("🔒 Save Account"):
                    if entered_otp != st.session_state.generated_otp or not desired_username.strip() or not new_password:
                        st.sidebar.error("❌ Invalid details or OTP!")
                    else:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        try:
                            cursor.execute("""
                                INSERT INTO users (username, phone_number, clean_phone, password, full_name, is_verified, created_at)
                                VALUES (?, ?, ?, ?, ?, 1, ?)
                            """, (desired_username.strip(), phone_input.strip(), clean_input, new_password, desired_username.strip(), today_str))
                            conn.commit()
                            conn.close()
                            st.session_state.user = desired_username.strip()
                            st.session_state.role = 'user'
                            st.sidebar.success("🎉 Account Created Successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            conn.close()
                            st.sidebar.error("❌ Username or Phone already exists!")
else:
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** ✔️")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.role = 'user'
        st.rerun()

nav_tabs = ["🌍 World Feed", "📱 Shorts Feed", "📢 Advertiser Hub", "💬 Support", "💳 Payout & Monetization", "👤 Profile & Status", "📤 Upload Content"]
if st.session_state.role == 'owner':
    nav_tabs.append("🔐 Owner Control Panel")

tab = st.sidebar.radio("Navigation", nav_tabs, index=nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0)
st.session_state.active_tab = tab

# ==========================================
# 7. TAB IMPLEMENTATIONS
# ==========================================

if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts")
    posts = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM videos WHERE video_type != 'short'")
    videos = [dict(r) for r in cursor.fetchall()]
    
    feed = posts + videos
    random.shuffle(feed)
    
    if not feed:
        st.info("No content available yet.")
    else:
        for item in feed:
            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(item.get('uploader_name', 'User'), profile_pic_path=item.get('uploader_pic'))
            if item.get('content'):
                st.write(item['content'])
            if item.get('image_url') and os.path.exists(item['image_url']):
                st.image(item['image_url'], use_container_width=True)
            if item.get('video_url') and os.path.exists(item['video_url']):
                st.video(item['video_url'])
            show_auto_moving_banner()
            render_comments_section(item['id'])
            st.markdown('</div>', unsafe_allow_html=True)
    conn.close()

elif tab == "📱 Shorts Feed":
    st.subheader("📱 Vertical Shorts")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    shorts = [dict(r) for r in cursor.fetchall()]
    
    for s in shorts:
        show_verified_profile(s.get('uploader_name', 'User'), profile_pic_path=s.get('uploader_pic'))
        st.caption(s.get('title'))
        if os.path.exists(s['video_url']):
            st.video(s['video_url'])
        render_comments_section(s['id'])
        st.divider()
    conn.close()

elif tab == "📢 Advertiser Hub":
    st.title("📢 Advertiser Portal")
    region = st.selectbox("Region", ["Bangladesh (BD)", "International (Global)"])
    price = 1000 if "Bangladesh" in region else 30
    duration = st.number_input("Months", min_value=1, value=1)
    st.metric("Total Payable", f"{price * duration} {'BDT' if 'Bangladesh' in region else 'USD'}")
    
    pay_method = st.radio("Payment Method", ["bKash", "Nagad", "Bank Transfer (Islami Bank)", "Crypto Wallet (USDT)"])
    if pay_method == "bKash": st.info("bKash Personal: 01302134435")
    elif pay_method == "Nagad": st.warning("Nagad Personal: 01722003172")
    elif pay_method == "Bank Transfer (Islami Bank)": st.code("Acc: 20502530202612312 | Islami Bank Lalmonirhat Branch")
    elif pay_method == "Crypto Wallet (USDT)": st.code("USDT TRC20: TM6DAbNuF2kaMaRoC8HKi2G8Gi5hVWnbCP")
    
    email = st.text_input("Your Email Address")
    link = st.text_input("Ad Content Link (Video / Image URL)")
    trx = st.text_input("Transaction ID / Reference Number (TrxID)")
    
    if st.button("Submit Advertisement for Review"):
        if email and link and trx:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO advertisements (advertiser_email, ad_type, content_link, duration_months, region, payment_method, amount, trx_id) VALUES (?, 'Banner', ?, ?, ?, ?, ?, ?)",
                           (email, link, duration, region, pay_method, price*duration, trx))
            conn.commit()
            conn.close()
            st.success("Ad submitted successfully for approval!")

elif tab == "💬 Support":
    st.subheader("💬 Official Support Desk")
    wa_link = f"https://wa.me/8801722003172?text={urllib.parse.quote('Hello Support!')}"
    st.markdown(f"[📲 Open Official WhatsApp Support Desk]({wa_link})")

elif tab == "💳 Payout & Monetization":
    st.subheader("💳 Payout Account Details")
    if st.session_state.user:
        acc_num = st.text_input("Bank Account / Mobile Wallet Number")
        if st.button("Save Payout Information"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET account_details = ? WHERE username = ?", (acc_num, st.session_state.user))
            conn.commit()
            conn.close()
            st.success("Payout details saved successfully!")

elif tab == "👤 Profile & Status":
    if not st.session_state.user:
        st.warning("Please log in to view your profile.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
        u = cursor.fetchone()
        
        followers = u['followers_count'] or 0
        watch_hours = (u['watch_time_mins'] or 0.0) / 60.0
        m_status = u['monetization_status'] or 'none'
        
        st.subheader(f"👤 {st.session_state.user}")
        st.write(f"👥 Followers: **{followers}/300** | ⏱️ Watch Time: **{watch_hours:.1f}/3000 Hours**")
        
        st.progress(min(followers / 300.0, 1.0))
        st.progress(min(watch_hours / 3000.0, 1.0))
        
        if m_status == 'none':
            if followers >= 300 and watch_hours >= 3000.0:
                if st.button("📩 Apply for Monetization"):
                    cursor.execute("UPDATE users SET monetization_status = 'pending' WHERE username = ?", (st.session_state.user,))
                    conn.commit()
                    st.success("Monetization application submitted to Owner for review!")
                    st.rerun()
            else:
                st.info("🔒 Monetization Requirements Not Met (300 Followers & 3000 Hours needed).")
        elif m_status == 'pending':
            st.warning("⏳ Monetization application is pending Owner Approval.")
        elif m_status == 'approved':
            st.success("✅ Monetization Approved & Active!")
            st.metric("Total Earnings", f"${u['earnings']:.2f} USD")
            
        conn.close()

elif tab == "📤 Upload Content":
    if not st.session_state.user:
        st.warning("Please login to upload content.")
    else:
        st.subheader("📤 Content Upload Hub")
        
        # Strict Global Guidelines Warning (English)
        st.error("""
            🚨 **STRICT COMMUNITY GUIDELINES & POLICY (Google & Global Compliance):**
            1. **Original Content Only:** Third-party copyrighted content, watermarked media, or stolen videos are strictly prohibited.
            2. **Safety First:** Sexual, adult, violent, or misleading content will result in an immediate account ban and forfeiture of earnings.
            3. **Daily Limits:** Maximum 10 Text/Image Posts, 1 Short Video, and 1 Long Video allowed per day.
        """)
        
        upload_type = st.radio("Select Content Type:", [
            "📝 Text/Image Post (Limit: 10/day)", 
            "📱 Short Video (Limit: 1/day)", 
            "🎥 Long Video (10-20 Mins, Limit: 1/day)"
        ])
        
        if upload_type == "📝 Text/Image Post (Limit: 10/day)":
            allowed, count = check_daily_limit(st.session_state.user, "post", 10)
            st.caption(f"Today's Limit Used: {count}/10")
            
            if not allowed:
                st.error("❌ You have reached your daily limit of 10 posts!")
            else:
                post_text = st.text_area("Write your post content...")
                img_file = st.file_uploader("Attach Image (Optional)", type=["jpg", "png", "jpeg"])
                
                if st.button("🚀 Publish Post"):
                    if not post_text.strip() and not img_file:
                        st.warning("Please enter text or select an image!")
                    else:
                        img_path = None
                        if img_file:
                            img_path = os.path.join(IMAGE_DIR, f"img_{uuid.uuid4()}.jpg")
                            with open(img_path, "wb") as f:
                                f.write(img_file.getvalue())
                        
                        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO posts (id, uploader_name, uploader_pic, content, image_url, likes, created_at)
                            VALUES (?, ?, ?, ?, ?, 0, ?)
                        """, (str(uuid.uuid4()), st.session_state.user, st.session_state.pic, post_text, img_path, today_str))
                        conn.commit()
                        conn.close()
                        
                        record_upload(st.session_state.user, "post")
                        st.toast("✅ Post published successfully!")
                        st.rerun()

        elif upload_type == "📱 Short Video (Limit: 1/day)":
            allowed, count = check_daily_limit(st.session_state.user, "short", 1)
            st.caption(f"Today's Limit Used: {count}/1")
            
            if not allowed:
                st.error("❌ Daily limit reached! You can only upload 1 Short video per day.")
            else:
                v_title = st.text_input("Short Video Title")
                vid_file = st.file_uploader("Select Short Video (MP4)", type=["mp4"])
                
                if st.button("🚀 Upload Short"):
                    if not vid_file or not v_title.strip():
                        st.warning("Please provide both video title and file!")
                    else:
                        vid_path = os.path.join(VIDEO_DIR, f"short_{uuid.uuid4()}.mp4")
                        with open(vid_path, "wb") as f:
                            f.write(vid_file.getvalue())
                        
                        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO videos (id, video_url, uploader_name, uploader_pic, video_type, title, likes, views, created_at)
                            VALUES (?, ?, ?, ?, 'short', ?, 0, 1, ?)
                        """, (str(uuid.uuid4()), vid_path, st.session_state.user, st.session_state.pic, v_title.strip(), today_str))
                        conn.commit()
                        conn.close()
                        
                        record_upload(st.session_state.user, "short")
                        st.toast("🎉 Short video uploaded successfully!")
                        st.rerun()

        elif upload_type == "🎥 Long Video (10-20 Mins, Limit: 1/day)":
            allowed, count = check_daily_limit(st.session_state.user, "long", 1)
            st.caption(f"Today's Limit Used: {count}/1")
            
            if not allowed:
                st.error("❌ Daily limit reached! You can only upload 1 Long video per day.")
            else:
                v_title = st.text_input("Video Title")
                duration_mins = st.number_input("Video Duration (Enter minutes)", min_value=1.0, max_value=120.0, value=10.0)
                vid_file = st.file_uploader("Upload Video File (MP4)", type=["mp4"])
                
                if st.button("🚀 Upload Long Video"):
                    if not vid_file or not v_title.strip():
                        st.warning("Please complete all required fields!")
                    elif duration_mins < 10.0 or duration_mins > 20.0:
                        st.error("❌ Video duration MUST be between 10 to 20 minutes!")
                    else:
                        vid_path = os.path.join(VIDEO_DIR, f"long_{uuid.uuid4()}.mp4")
                        with open(vid_path, "wb") as f:
                            f.write(vid_file.getvalue())
                        
                        today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO videos (id, video_url, uploader_name, uploader_pic, video_type, duration_mins, title, likes, views, created_at)
                            VALUES (?, ?, ?, ?, 'long', ?, ?, 0, 1, ?)
                        """, (str(uuid.uuid4()), vid_path, st.session_state.user, st.session_state.pic, duration_mins, v_title.strip(), today_str))
                        conn.commit()
                        conn.close()
                        
                        record_upload(st.session_state.user, "long")
                        st.toast("🎉 Long video uploaded successfully!")
                        st.rerun()

elif tab == "🔐 Owner Control Panel":
    if st.session_state.role != 'owner':
        st.error("🚫 Access Denied!")
    else:
        st.title("👑 Owner Master Dashboard & Approvals")
        conn = get_db_connection()
        cursor = conn.cursor()

        st.subheader("📩 Pending Monetization Requests")
        cursor.execute("SELECT id, username, followers_count, watch_time_mins FROM users WHERE monetization_status = 'pending'")
        pending_users = cursor.fetchall()
        
        if pending_users:
            for pu in pending_users:
                st.write(f"👤 **{pu['username']}** | 👥 Followers: {pu['followers_count']} | ⏱️ Watch Mins: {pu['watch_time_mins']}")
                c1, c2 = st.columns(2)
                if c1.button(f"✅ Approve Monetization for {pu['username']}", key=f"app_m_{pu['id']}"):
                    cursor.execute("UPDATE users SET monetization_status = 'approved' WHERE id = ?", (pu['id'],))
                    conn.commit()
                    st.toast("Monetization Approved!")
                    st.rerun()
                if c2.button(f"❌ Reject", key=f"rej_m_{pu['id']}"):
                    cursor.execute("UPDATE users SET monetization_status = 'none' WHERE id = ?", (pu['id'],))
                    conn.commit()
                    st.rerun()
        else:
            st.info("No monetization applications currently pending.")

        st.divider()
        st.subheader("📢 Ad Approvals")
        cursor.execute("SELECT * FROM advertisements WHERE status = 'Pending'")
        ads = cursor.fetchall()
        if ads:
            for ad in ads:
                st.write(f"Email: {ad['advertiser_email']} | Amount: {ad['amount']} | Trx: {ad['trx_id']}")
                if st.button(f"Approve Ad #{ad['id']}"):
                    cursor.execute("UPDATE advertisements SET status = 'Active' WHERE id = ?", (ad['id'],))
                    conn.commit()
                    st.rerun()
        else:
            st.info("No ads pending approval.")
            
        conn.close()

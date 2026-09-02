একটি গুগল গ্রাউট এর জন্য টেস্ট করার জন্য 🇧🇩
import base64
from datetime import datetime, timedelta
import hashlib
import os
import random
import sqlite3
import uuid

import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. GLOBAL APPLICATION CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Enterprise Global Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Meta tags for crawlers, SEO, and ad networks
components.html(
    """
    <meta name="msvalidate.01" content="e776b8ce73ea3dcc07551e8a021a0907">
    <meta name="monetag" content="5cc1b7ba5cb29eff802ce49009f87e2b">
    """,
    height=0,
)

SECRET_OWNER_KEY = "S$s123456789112233"

# Cloud Environment Variables
DATABASE_URL = os.environ.get("DATABASE_URL", None)
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", None)

LOCAL_DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"

for folder in [VIDEO_DIR, IMAGE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==========================================
# 2. HIGH-AVAILABILITY DATABASE ENGINE
# ==========================================
def get_db_connection():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.DictCursor)
        return conn, "postgresql"
    else:
        conn = sqlite3.connect(LOCAL_DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_master_database_system():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgresql":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(30) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                country VARCHAR(60) DEFAULT 'Global / Other',
                profile_pic_base64 TEXT,
                is_verified BOOLEAN DEFAULT TRUE,
                is_suspended BOOLEAN DEFAULT FALSE,
                suspended_until TIMESTAMP,
                watch_time_hours REAL DEFAULT 0.0,
                followers_count INT DEFAULT 0,
                is_monetized BOOLEAN DEFAULT FALSE,
                payout_method VARCHAR(50),
                payout_account_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255),
                content TEXT,
                media_url TEXT,
                category VARCHAR(50) DEFAULT 'general',
                likes_count INT DEFAULT 0,
                views_count INT DEFAULT 0,
                is_published BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id VARCHAR(36) PRIMARY KEY,
                post_id VARCHAR(36) REFERENCES posts(id) ON DELETE CASCADE,
                user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone_number TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                country TEXT DEFAULT 'Global / Other',
                profile_pic_base64 TEXT,
                is_verified INTEGER DEFAULT 1,
                is_suspended INTEGER DEFAULT 0,
                suspended_until TEXT,
                watch_time_hours REAL DEFAULT 0.0,
                followers_count INTEGER DEFAULT 0,
                is_monetized INTEGER DEFAULT 0,
                payout_method TEXT,
                payout_account_details TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                content TEXT,
                media_url TEXT,
                category TEXT DEFAULT 'general',
                likes_count INTEGER DEFAULT 0,
                views_count INTEGER DEFAULT 0,
                is_published INTEGER DEFAULT 1,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

    conn.commit()
    conn.close()

init_master_database_system()

# ==========================================
# 3. AI CONTENT SAFETY & SUSPENSION ENGINE
# ==========================================
BANNED_KEYWORDS = [
    "sex", "porn", "nude", "adult", "xvideo", "badword1", "badword2",
    "গালাগালি", "খারাপ", "অশ্লীল", "১৮+"
]

def check_ai_content_safety(text_to_check: str) -> bool:
    if not text_to_check:
        return True
    lowered = text_to_check.lower()
    for word in BANNED_KEYWORDS:
        if word in lowered:
            return False
    return True

def suspend_user_account(user_id: str, days: int = 30):
    conn, db_type = get_db_connection()
    c = conn.cursor()
    until_date = datetime.now() + timedelta(days=days)
    until_str = until_date.strftime("%Y-%m-%d %H:%M:%S")

    if db_type == "postgresql":
        c.execute("UPDATE users SET is_suspended = TRUE, suspended_until = %s WHERE id = %s", (until_date, user_id))
    else:
        c.execute("UPDATE users SET is_suspended = 1, suspended_until = ? WHERE id = ?", (until_str, user_id))
    
    conn.commit()
    conn.close()

def is_user_suspended(user_id: str) -> tuple[bool, str]:
    if user_id == "owner_admin":
        return False, ""
        
    conn, _ = get_db_connection()
    c = conn.cursor()
    query = "SELECT is_suspended, suspended_until FROM users WHERE id = %s" if DATABASE_URL else "SELECT is_suspended, suspended_until FROM users WHERE id = ?"
    c.execute(query, (user_id,))
    usr = c.fetchone()
    conn.close()

    if not usr or not usr["is_suspended"]:
        return False, ""

    suspended_until = usr["suspended_until"]
    if isinstance(suspended_until, str):
        until_dt = datetime.strptime(suspended_until, "%Y-%m-%d %H:%M:%S")
    else:
        until_dt = suspended_until

    if datetime.now() < until_dt:
        return True, until_dt.strftime("%b %d, %Y")
    else:
        conn, db_type = get_db_connection()
        c = conn.cursor()
        if db_type == "postgresql":
            c.execute("UPDATE users SET is_suspended = FALSE WHERE id = %s", (user_id,))
        else:
            c.execute("UPDATE users SET is_suspended = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return False, ""

def get_daily_upload_count(user_id: str, category: str) -> int:
    conn, _ = get_db_connection()
    c = conn.cursor()
    one_day_ago = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    query = """
        SELECT COUNT(*) as cnt FROM posts 
        WHERE user_id = %s AND category = %s AND created_at >= %s
    """ if DATABASE_URL else """
        SELECT COUNT(*) as cnt FROM posts 
        WHERE user_id = ? AND category = ? AND created_at >= ?
    """
    c.execute(query, (user_id, category, one_day_ago))
    res = c.fetchone()
    conn.close()
    return res["cnt"] if res else 0

# ==========================================
# 4. MONETIZATION & AUTOMATIC APPROVAL ENGINE
# ==========================================
def check_and_update_monetization(user_id: str):
    if user_id == "owner_admin":
        return
    
    conn, db_type = get_db_connection()
    c = conn.cursor()
    query = "SELECT watch_time_hours, followers_count, is_monetized FROM users WHERE id = %s" if DATABASE_URL else "SELECT watch_time_hours, followers_count, is_monetized FROM users WHERE id = ?"
    c.execute(query, (user_id,))
    usr = c.fetchone()

    if usr:
        w_hours = usr["watch_time_hours"] or 0.0
        followers = usr["followers_count"] or 0
        monetized = usr["is_monetized"]

        if not monetized and w_hours >= 3000.0 and followers >= 300:
            if db_type == "postgresql":
                c.execute("UPDATE users SET is_monetized = TRUE WHERE id = %s", (user_id,))
            else:
                c.execute("UPDATE users SET is_monetized = 1 WHERE id = ?", (user_id,))
            conn.commit()
    conn.close()

# ==========================================
# 5. MEDIA STORAGE & ADS
# ==========================================
def save_media_file(uploaded_file, file_prefix, extension):
    filename = f"{file_prefix}{extension}"
    if GCS_BUCKET_NAME:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(filename)
            blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
            return blob.public_url
        except Exception as e:
            st.error(f"Cloud Storage Error: {e}")
            return ""
    else:
        target_dir = IMAGE_DIR if extension in [".jpg", ".png", ".jpeg"] else VIDEO_DIR
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath

DIRECT_AD_LINKS = ["", "", ""] 

def render_ad_button():
    valid_links = [link for link in DIRECT_AD_LINKS if link.strip()]
    ad_url = random.choice(valid_links) if valid_links else "#"
    if ad_url == "#": return ""
    return f"""
        <div style="text-align: center; margin: 12px 0;">
            <a href="{ad_url}" target="_blank" style="background: linear-gradient(45deg, #00c853, #00e676); color: #000; padding: 10px 22px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; display: inline-block;">
                👉 Click Here / Watch Sponsored Content 🌐
            </a>
        </div>
    """

# ==========================================
# 6. USER INTERFACE & PROFILE HELPER
# ==========================================
ALLOWED_COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Australia", "Germany", 
    "France", "Japan", "India", "Bangladesh", "Pakistan", "Saudi Arabia", 
    "United Arab Emirates", "Malaysia", "Global / Other"
]

PAYMENT_METHODS = [
    "bKash (বাংলাদেশ)",
    "Nagad (বাংলাদেশ)",
    "PayPal (International)",
    "Mastercard (Global)",
    "Dual Currency Visa Card",
    "Other Card / Bank Wire"
]

def show_verified_profile(user_id, subtitle="Member"):
    conn, _ = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT full_name, is_verified, country, profile_pic_base64, is_monetized FROM users WHERE id = %s" if DATABASE_URL else "SELECT full_name, is_verified, country, profile_pic_base64, is_monetized FROM users WHERE id = ?", (user_id,))
    u_data = c.fetchone()
    conn.close()
    
    display_name = u_data["full_name"] if u_data else "Global User"
    is_verified = u_data["is_verified"] if u_data else True
    user_country = u_data["country"] if u_data and u_data["country"] else "Global HQ"
    b64_img = u_data["profile_pic_base64"] if (u_data and u_data["profile_pic_base64"]) else None
    is_monetized = u_data["is_monetized"] if u_data else False
    
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">' if b64_img else '<div style="width:45px; height:45px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:20px;">👤</div>'
    verified_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px; display: inline-block;"><path fill="#1877F2" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1.2 14.2l-3.5-3.5 1.41-1.41 2.09 2.08 5.68-5.67 1.41 1.41-7.09 7.09z"/></svg>'
    monetized_badge = '<span style="background:#ffd700; color:#000; font-size:10px; font-weight:bold; padding:2px 6px; border-radius:4px; margin-left:6px;">💰 MONETIZED</span>' if is_monetized else ''
    
    tick = verified_svg if is_verified else ''
    
    card_html = f"""<div style="display:flex; align-items:center; gap:12px; background: #18191a; padding: 10px; border-radius: 10px; border: 1px solid #2d2f31; margin-bottom: 12px;">{img_html}<div><div style="font-weight:bold; color:#e4e6eb; font-size: 16px; display: flex; align-items: center;">{display_name} {tick} {monetized_badge}</div><div style="color:#b0b3b8; font-size:12px;">{subtitle} • 🌐 {user_country}</div></div></div>"""
    st.markdown(card_html, unsafe_allow_html=True)

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #00c853; font-weight: 900; margin: 0;">🛡️ Global AI Book — World Enterprise Platform 🛡️</h1>
    </div>
""", unsafe_allow_html=True)
st.divider()

if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 7. SIDEBAR & AUTHENTICATION
# ==========================================
st.sidebar.markdown("### 🔍 Search Engine")
search_query = st.sidebar.text_input("Search content or Admin Passcode...", key="search_query")

if search_query.strip() == SECRET_OWNER_KEY:
    st.session_state.user_id = "owner_admin"
    st.session_state.user_name = "System Owner"
    st.session_state.active_tab = "👑 Owner Control Center"

st.sidebar.markdown("---")
mode = st.sidebar.radio("Select Access Mode", ["📱 Secure Login", "📝 New Registration"])

if mode == "📱 Secure Login":
    login_phone = st.sidebar.text_input("Mobile Number / User ID")
    login_pass = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        clean_phone = login_phone.strip()
        if clean_phone and login_pass:
            hashed_pass = hash_password(login_pass)
            conn, _ = get_db_connection()
            c = conn.cursor()
            query = "SELECT * FROM users WHERE phone_number = %s AND password_hash = %s" if DATABASE_URL else "SELECT * FROM users WHERE phone_number = ? AND password_hash = ?"
            c.execute(query, (clean_phone, hashed_pass))
            usr = c.fetchone()
            conn.close()
            
            if usr:
                st.session_state.user_id = usr["id"]
                st.session_state.user_name = usr["full_name"]
                st.sidebar.success(f"✅ Welcome back, {usr['full_name']}!")
                check_and_update_monetization(usr["id"])
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid Credentials!")

elif mode == "📝 New Registration":
    reg_name = st.sidebar.text_input("Full Name")
    reg_phone = st.sidebar.text_input("Mobile Number")
    reg_pass = st.sidebar.text_input("Password", type="password")
    reg_country = st.sidebar.selectbox("Country", ALLOWED_COUNTRIES)
    
    if st.sidebar.button("Register Account"):
        if reg_name and reg_phone and reg_pass:
            user_uuid = str(uuid.uuid4())
            hashed_pass = hash_password(reg_pass)
            created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn, db_type = get_db_connection()
            c = conn.cursor()
            try:
                query = """
                    INSERT INTO users (id, full_name, phone_number, password_hash, country, is_verified, is_suspended, created_at)
                    VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, %s)
                """ if db_type == "postgresql" else """
                    INSERT INTO users (id, full_name, phone_number, password_hash, country, is_verified, is_suspended, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, 0, ?)
                """
                c.execute(query, (user_uuid, reg_name, reg_phone, hashed_pass, reg_country, created_time))
                conn.commit()
                
                st.session_state.user_id = user_uuid
                st.session_state.user_name = reg_name
                st.sidebar.success("🎉 Account created successfully!")
                st.rerun()
            except Exception as e:
                st.sidebar.error("❌ Phone number already registered!")
            finally:
                conn.close()

if st.session_state.user_id:
    st.sidebar.markdown(f"Authenticated as: **{st.session_state.user_name}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.active_tab = "🌍 World Feed"
        st.rerun()

nav_tabs = ["🌍 World Feed", "📱 TikTok Shorts Feed", "📺 Direct Long Videos", "📤 Upload Studio", "💵 Monetization Hub"]
if st.session_state.user_id == "owner_admin":
    nav_tabs.append("👑 Owner Control Center")

current_index = nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0
tab = st.sidebar.radio("Navigation", nav_tabs, index=current_index)
st.session_state.active_tab = tab

# ==========================================
# 8. CONTENT FEEDS & UPLOAD CONTROL
# ==========================================

# --- World Feed ---
if tab == "🌍 World Feed":
    st.markdown("### 🌍 World Feed")
    conn, _ = get_db_connection()
    c = conn.cursor()
    query = "SELECT * FROM posts WHERE category = 'general' AND is_published = TRUE ORDER BY created_at DESC" if DATABASE_URL else "SELECT * FROM posts WHERE category = 'general' AND is_published = 1 ORDER BY created_at DESC"
    c.execute(query)
    posts = [dict(r) for r in c.fetchall()]
    conn.close()

    for item in posts:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item["user_id"], subtitle=f"Posted {item.get('created_at')}")
        if item.get("title"): st.markdown(f"#### {item['title']}")
        st.write(item.get("content", ""))
        
        media_path = item.get("media_url")
        if media_path:
            if media_path.startswith("http") or os.path.exists(media_path):
                st.image(media_path, use_container_width=True)
            
        ad_html = render_ad_button()
        if ad_html: st.markdown(ad_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- Video Feeds ---
elif tab in ["📱 TikTok Shorts Feed", "📺 Direct Long Videos"]:
    cat_type = "short" if tab == "📱 TikTok Shorts Feed" else "long"
    st.markdown(f"### {'📱 TikTok Shorts Feed' if cat_type == 'short' else '📺 Direct Long Videos'}")
    
    conn, _ = get_db_connection()
    c = conn.cursor()
    query = "SELECT * FROM posts WHERE category = %s AND is_published = TRUE ORDER BY created_at DESC" if DATABASE_URL else "SELECT * FROM posts WHERE category = ? AND is_published = 1 ORDER BY created_at DESC"
    c.execute(query, (cat_type,))
    vids = [dict(r) for r in c.fetchall()]
    conn.close()

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid["user_id"], subtitle=f"Uploaded {vid.get('created_at')}")
        if vid.get("title"): st.subheader(vid['title'])
        st.write(vid.get('content', ''))
        
        media_path = vid.get("media_url")
        if media_path:
            if media_path.startswith("http") or os.path.exists(media_path):
                st.video(media_path)
            
        ad_html = render_ad_button()
        if ad_html: st.markdown(ad_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- Upload Studio WITH AI SAFETY & LIMITS ---
elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Upload Studio")
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to publish content.")
    else:
        suspended, until_date = is_user_suspended(st.session_state.user_id)
        if suspended:
            st.error(f"🚫 YOUR ACCOUNT IS SUSPENDED UNTIL {until_date} FOR VIOLATING COMMUNITY SAFETY RULES (NSFW / Profanity Content).")
        else:
            cat = st.selectbox("Category", ["General Post (Photo/Text)", "TikTok Short Video", "Direct Long Video"])
            title_in = st.text_input("Title")
            desc_in = st.text_area("Description")
            
            post_uuid = str(uuid.uuid4())
            created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if cat == "General Post (Photo/Text)":
                f_up = st.file_uploader("Select Photo (Max 15 per day)", type=["jpg", "png", "jpeg"])
                if st.button("Publish Post"):
                    if not check_ai_content_safety(title_in) or not check_ai_content_safety(desc_in) or (f_up and not check_ai_content_safety(f_up.name)):
                        suspend_user_account(st.session_state.user_id, days=30)
                        st.error("🚨 Violating Content Detected! Your account has been suspended for 30 days by AI Moderation.")
                        st.rerun()
                    elif get_daily_upload_count(st.session_state.user_id, "general") >= 15:
                        st.warning("⚠️ Daily limit reached! You can only post 15 general posts per day.")
                    else:
                        media_link = save_media_file(f_up, post_uuid, ".jpg") if f_up else ""
                        conn, db_type = get_db_connection()
                        c = conn.cursor()
                        query = """
                            INSERT INTO posts (id, user_id, title, content, media_url, category, views_count, created_at)
                            VALUES (%s, %s, %s, %s, %s, 'general', 15000, %s)
                        """ if db_type == "postgresql" else """
                            INSERT INTO posts (id, user_id, title, content, media_url, category, views_count, created_at)
                            VALUES (?, ?, ?, ?, ?, 'general', 15000, ?)
                        """
                        c.execute(query, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, created_time))
                        conn.commit()
                        conn.close()
                        st.success("✅ General Post published globally!")
                        st.rerun()

            else:
                cat_code = "short" if cat == "TikTok Short Video" else "long"
                limit_num = 1
                v_up = st.file_uploader(f"Select Video (Max {limit_num} per day)", type=["mp4", "mov"])
                
                if st.button("Publish Video"):
                    if not v_up:
                        st.warning("⚠️ Please attach a video file first.")
                    elif not check_ai_content_safety(title_in) or not check_ai_content_safety(desc_in) or not check_ai_content_safety(v_up.name):
                        suspend_user_account(st.session_state.user_id, days=30)
                        st.error("🚨 Unsafe or Bad Content Detected! Your account has been suspended for 30 days by AI Moderation.")
                        st.rerun()
                    elif get_daily_upload_count(st.session_state.user_id, cat_code) >= limit_num:
                        st.warning(f"⚠️ Daily limit reached! You can only upload {limit_num} {cat_code} video per day.")
                    else:
                        media_link = save_media_file(v_up, post_uuid, ".mp4")
                        conn, db_type = get_db_connection()
                        c = conn.cursor()
                        query = """
                            INSERT INTO posts (id, user_id, title, content, media_url, category, views_count, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, 15000, %s)
                        """ if db_type == "postgresql" else """
                            INSERT INTO posts (id, user_id, title, content, media_url, category, views_count, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, 15000, ?)
                        """
                        c.execute(query, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, cat_code, created_time))
                        conn.commit()
                        conn.close()
                        st.success("✅ Video uploaded successfully!")
                        st.rerun()

# --- Monetization Hub ---
elif tab == "💵 Monetization Hub":
    st.markdown("### 💵 Monetization & Revenue Program")
    if not st.session_state.user_id:
        st.warning("⚠️ Please log in to view your Monetization Status.")
    elif st.session_state.user_id == "owner_admin":
        st.info("👑 System Owner Account — Monetization features are automatically unlocked.")
    else:
        conn, _ = get_db_connection()
        c = conn.cursor()
        query = "SELECT watch_time_hours, followers_count, is_monetized, payout_method, payout_account_details FROM users WHERE id = %s" if DATABASE_URL else "SELECT watch_time_hours, followers_count, is_monetized, payout_method, payout_account_details FROM users WHERE id = ?"
        c.execute(query, (st.session_state.user_id,))
        u_info = c.fetchone()
        conn.close()

        w_hours = u_info["watch_time_hours"] if u_info and u_info["watch_time_hours"] else 0.0
        followers = u_info["followers_count"] if u_info and u_info["followers_count"] else 0
        is_monetized = u_info["is_monetized"] if u_info else False
        current_method = u_info["payout_method"] if u_info else ""
        current_acc = u_info["payout_account_details"] if u_info else ""

        check_and_update_monetization(st.session_state.user_id)

        st.markdown("#### 📊 Monetization Requirements Eligibility")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(label="⏱️ Watch Time (Goal: 3,000 Hours)", value=f"{w_hours:.1f} Hours")
            st.progress(min(w_hours / 3000.0, 1.0))
            
        with col2:
            st.metric(label="👥 Followers (Goal: 300 Followers)", value=f"{followers}")
            st.progress(min(followers / 300.0, 1.0))

        st.divider()

        if is_monetized or (w_hours >= 3000.0 and followers >= 300):
            st.success("🎉 **MONETIZATION APPROVED!** Profile review complete. Your account is eligible for payout distribution.")
            st.markdown("### 💳 Payout Setup & Payment Method")
            st.write("নিচে আপনার পছন্দের পেমেন্ট মেথড নির্বাচন করুন এবং অ্যাকাউন্টের বিবরণ দিয়ে সেভ করুন:")

            p_method = st.selectbox("Select Payout Method", PAYMENT_METHODS, index=PAYMENT_METHODS.index(current_method) if current_method in PAYMENT_METHODS else 0)
            p_details = st.text_input("Account Details (e.g. Bkash/Nagad Number, Card Number, PayPal Email)", value=current_acc)

            if st.button("Save Payout Method"):
                if p_details.strip():
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    if db_type == "postgresql":
                        c.execute("UPDATE users SET payout_method = %s, payout_account_details = %s, is_monetized = TRUE WHERE id = %s", (p_method, p_details, st.session_state.user_id))
                    else:
                        c.execute("UPDATE users SET payout_method = ?, payout_account_details = ?, is_monetized = 1 WHERE id = ?", (p_method, p_details, st.session_state.user_id))
                    conn.commit()
                    conn.close()
                    st.success("✅ Payout account settings saved successfully!")
                    st.rerun()
                else:
                    st.error("⚠️ Please enter valid account details.")
        else:
            st.warning("🔒 **Monetization Inactive:** আপনার ৩,০০০ ঘণ্টা ওয়াচটাইম এবং ৩০০ ফলোয়ার পূর্ণ হলে সিস্টেম অটোমেটিক প্রোফাইল যাচাই করে মনিটাইজেশন অন করে দেবে।")

# --- Owner Control Center ---
elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Master Control Center")
    st.success("👑 Authenticated as Global Platform Owner!")

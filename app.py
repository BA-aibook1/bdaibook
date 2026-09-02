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

components.html(
    """
    <meta name="msvalidate.01" content="e776b8ce73ea3dcc07551e8a021a0907">
    <meta name="monetag" content="5cc1b7ba5cb29eff802ce49009f87e2b">
    """,
    height=0,
)

SECRET_OWNER_KEY = "S$s123456789112233"

DATABASE_URL = os.environ.get("DATABASE_URL", None)
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", None)

LOCAL_DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"

for folder in [VIDEO_DIR, IMAGE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==========================================
# 2. DATABASE CONNECTOR & SYSTEM SETTINGS TABLE
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
                user_id VARCHAR(36),
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
            CREATE TABLE IF NOT EXISTS site_settings (
                key_name VARCHAR(50) PRIMARY KEY,
                val_data TEXT
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
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                key_name TEXT PRIMARY KEY,
                val_data TEXT
            )
        """)

    conn.commit()
    conn.close()

init_master_database_system()

def get_site_setting(key, default_val=""):
    conn, _ = get_db_connection()
    c = conn.cursor()
    query = "SELECT val_data FROM site_settings WHERE key_name = %s" if DATABASE_URL else "SELECT val_data FROM site_settings WHERE key_name = ?"
    c.execute(query, (key,))
    row = c.fetchone()
    conn.close()
    return row["val_data"] if row and row["val_data"] else default_val

def set_site_setting(key, value):
    conn, db_type = get_db_connection()
    c = conn.cursor()
    if db_type == "postgresql":
        c.execute("INSERT INTO site_settings (key_name, val_data) VALUES (%s, %s) ON CONFLICT (key_name) DO UPDATE SET val_data = EXCLUDED.val_data", (key, str(value)))
    else:
        c.execute("INSERT OR REPLACE INTO site_settings (key_name, val_data) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# ==========================================
# 3. SAFETY & UTILITY FUNCTIONS
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

ALLOWED_COUNTRIES = ["United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "Japan", "India", "Bangladesh", "Pakistan", "Saudi Arabia", "United Arab Emirates", "Malaysia", "Global / Other"]

def show_verified_profile(user_id, subtitle="Member"):
    if user_id == "owner_admin":
        display_name, is_verified, user_country, b64_img, is_monetized = "System Owner", True, "Global Owner HQ", None, True
    else:
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

# ==========================================
# 4. DYNAMIC HEADER & LOGO DISPLAY
# ==========================================
header_text = get_site_setting("header_text", "🛡️ Global AI Book — World Enterprise Platform 🛡️")
header_pic = get_site_setting("header_pic_url", "")
header_width = int(get_site_setting("header_pic_width", "250"))

if header_pic:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(header_pic, width=header_width)

st.markdown(f"""
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #00c853; font-weight: 900; margin: 0;">{header_text}</h1>
    </div>
""", unsafe_allow_html=True)
st.divider()

if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 5. SIDEBAR & AUTHENTICATION
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
                query = "INSERT INTO users (id, full_name, phone_number, password_hash, country, is_verified, is_suspended, created_at) VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, %s)" if db_type == "postgresql" else "INSERT INTO users (id, full_name, phone_number, password_hash, country, is_verified, is_suspended, created_at) VALUES (?, ?, ?, ?, ?, 1, 0, ?)"
                c.execute(query, (user_uuid, reg_name, reg_phone, hashed_pass, reg_country, created_time))
                conn.commit()
                st.session_state.user_id = user_uuid
                st.session_state.user_name = reg_name
                st.sidebar.success("🎉 Account created successfully!")
                st.rerun()
            except Exception:
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
# 6. FEEDS & UPLOAD STUDIO
# ==========================================
if tab == "🌍 World Feed":
    st.markdown("### 🌍 World Feed")
    conn, db_type = get_db_connection()
    c = conn.cursor()
    try:
        query = "SELECT * FROM posts WHERE (category = 'general' OR category IS NULL) ORDER BY created_at DESC"
        c.execute(query)
        posts = [dict(r) for r in c.fetchall()]
    except Exception: posts = []
    finally: conn.close()

    for item in posts:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item.get("user_id"), subtitle=f"Posted {item.get('created_at', '')}")
        if item.get("title"): st.markdown(f"#### {item['title']}")
        st.write(item.get("content", ""))
        media_path = item.get("media_url")
        if media_path and (media_path.startswith("http") or os.path.exists(media_path)):
            st.image(media_path, use_container_width=True)
        ad_html = render_ad_button()
        if ad_html: st.markdown(ad_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif tab in ["📱 TikTok Shorts Feed", "📺 Direct Long Videos"]:
    cat_type = "short" if tab == "📱 TikTok Shorts Feed" else "long"
    st.markdown(f"### {'📱 TikTok Shorts Feed' if cat_type == 'short' else '📺 Direct Long Videos'}")
    conn, db_type = get_db_connection()
    c = conn.cursor()
    try:
        query = "SELECT * FROM posts WHERE category = %s ORDER BY created_at DESC" if db_type == "postgresql" else "SELECT * FROM posts WHERE category = ? ORDER BY created_at DESC"
        c.execute(query, (cat_type,))
        vids = [dict(r) for r in c.fetchall()]
    except Exception: vids = []
    finally: conn.close()

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid.get("user_id"), subtitle=f"Uploaded {vid.get('created_at', '')}")
        if vid.get("title"): st.subheader(vid['title'])
        st.write(vid.get('content', ''))
        media_path = vid.get("media_url")
        if media_path and (media_path.startswith("http") or os.path.exists(media_path)):
            st.video(media_path)
        ad_html = render_ad_button()
        if ad_html: st.markdown(ad_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Upload Studio")
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to publish content.")
    else:
        is_owner = (st.session_state.user_id == "owner_admin")
        cat = st.selectbox("Category", ["General Post (Photo/Text)", "TikTok Short Video", "Direct Long Video"])
        title_in = st.text_input("Title")
        desc_in = st.text_area("Description")
        post_uuid = str(uuid.uuid4())
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if cat == "General Post (Photo/Text)":
            f_up = st.file_uploader("Select Photo", type=["jpg", "png", "jpeg"])
            if st.button("Publish Post"):
                media_link = save_media_file(f_up, post_uuid, ".jpg") if f_up else ""
                conn, db_type = get_db_connection()
                c = conn.cursor()
                query = "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (%s, %s, %s, %s, %s, 'general', %s)" if db_type == "postgresql" else "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (?, ?, ?, ?, ?, 'general', ?)"
                c.execute(query, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, created_time))
                conn.commit()
                conn.close()
                st.success("✅ Post published successfully!")
                st.rerun()

        else:
            cat_code = "short" if cat == "TikTok Short Video" else "long"
            v_up = st.file_uploader("Select Video", type=["mp4", "mov", "mkv", "avi"])
            if st.button("Publish Video"):
                if not v_up:
                    st.warning("⚠️ Please select a video file.")
                else:
                    ext = os.path.splitext(v_up.name)[1]
                    media_link = save_media_file(v_up, post_uuid, ext)
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    query = "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)" if db_type == "postgresql" else "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                    c.execute(query, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, cat_code, created_time))
                    conn.commit()
                    conn.close()
                    st.success("✅ Video published successfully!")
                    st.rerun()

elif tab == "💵 Monetization Hub":
    st.markdown("### 💵 Monetization Hub")
    st.info("Monetization Status & Payout Settings Available Here.")

# ==========================================
# 7. 👑 OWNER CONTROL CENTER
# ==========================================
elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Master Control Center")
    st.success("👑 Authenticated as Global Platform Owner!")
    
    st.markdown("---")
    st.markdown("### 🖼️ Modify Header Picture & Header Title")
    
    current_h_text = get_site_setting("header_text", "🛡️ Global AI Book — World Enterprise Platform 🛡️")
    new_h_text = st.text_input("Header Title Banner Text", value=current_h_text)
    
    current_width = int(get_site_setting("header_pic_width", "250"))
    new_width = st.slider("Logo / Header Image Size (Width in Pixels)", min_value=100, max_value=800, value=current_width, step=10)
    
    h_file = st.file_uploader("Upload New Header Banner Image", type=["jpg", "png", "jpeg"])
    
    if st.button("Save New Header Settings"):
        if new_h_text.strip():
            set_site_setting("header_text", new_h_text.strip())
        set_site_setting("header_pic_width", new_width)
        if h_file:
            header_img_path = save_media_file(h_file, "header_banner", ".jpg")
            set_site_setting("header_pic_url", header_img_path)
        
        st.success("🎉 Header Text, Size and Banner Picture Updated Successfully!")
        st.rerun()

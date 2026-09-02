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

def init_master_database_system():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgresql":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(150) UNIQUE NOT NULL,
                password_hash TEXT DEFAULT 'OTP_USER',
                country VARCHAR(60) DEFAULT 'Global / Other',
                bio TEXT DEFAULT '',
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
                password_hash TEXT DEFAULT 'OTP_USER',
                country TEXT DEFAULT 'Global / Other',
                bio TEXT DEFAULT '',
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
        # Schema migration check for bio column in SQLite
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if "bio" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")

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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                key_name TEXT PRIMARY KEY,
                val_data TEXT
            )
        """)

    conn.commit()
    conn.close()

init_master_database_system()

# Helper Functions
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

# AI Safety Moderation
BANNED_KEYWORDS = ["sex", "porn", "nude", "adult", "xvideo", "গালাগালি", "খারাপ", "অশ্লীল", "১৮+"]

def check_ai_content_safety(text_to_check: str) -> bool:
    if not text_to_check: return True
    lowered = text_to_check.lower()
    for word in BANNED_KEYWORDS:
        if word in lowered: return False
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
    if user_id == "owner_admin": return False, ""
    conn, _ = get_db_connection()
    c = conn.cursor()
    query = "SELECT is_suspended, suspended_until FROM users WHERE id = %s" if DATABASE_URL else "SELECT is_suspended, suspended_until FROM users WHERE id = ?"
    c.execute(query, (user_id,))
    usr = c.fetchone()
    conn.close()

    if not usr or not usr["is_suspended"]: return False, ""
    suspended_until = usr["suspended_until"]
    until_dt = datetime.strptime(suspended_until, "%Y-%m-%d %H:%M:%S") if isinstance(suspended_until, str) else suspended_until

    if datetime.now() < until_dt:
        return True, until_dt.strftime("%b %d, %Y")
    return False, ""

def get_daily_upload_count(user_id: str, category: str) -> int:
    if user_id == "owner_admin": return 0
    conn, _ = get_db_connection()
    c = conn.cursor()
    one_day_ago = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    query = "SELECT COUNT(*) as cnt FROM posts WHERE user_id = %s AND category = %s AND created_at >= %s" if DATABASE_URL else "SELECT COUNT(*) as cnt FROM posts WHERE user_id = ? AND category = ? AND created_at >= ?"
    c.execute(query, (user_id, category, one_day_ago))
    res = c.fetchone()
    conn.close()
    return res["cnt"] if res else 0

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
        target_dir = IMAGE_DIR if extension.lower() in [".jpg", ".png", ".jpeg"] else VIDEO_DIR
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath

# User Verified Profile Renderer
def show_verified_profile(user_id, subtitle="Member"):
    if user_id == "owner_admin":
        display_name = "System Owner"
        is_verified = True
        user_country = "Global HQ"
        b64_img = None
        is_monetized = True
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

# CSS Custom Theme
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# Header Render
header_text = get_site_setting("header_text", "🛡️ Global AI Book — World Enterprise Platform 🛡️")
header_pic = get_site_setting("header_pic_url", "")
header_width = int(get_site_setting("header_pic_width", "250"))

if header_pic and os.path.exists(header_pic):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.image(header_pic, width=header_width)

st.markdown(f'<div style="text-align: center; padding: 10px 0;"><h1 style="color: #00c853; font-weight: 900; margin: 0;">{header_text}</h1></div>', unsafe_allow_html=True)
st.divider()

# Session States
if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "🌍 World Feed"
if "sent_otp" not in st.session_state: st.session_state.sent_otp = None
if "temp_identifier" not in st.session_state: st.session_state.temp_identifier = None

# ==========================================
# 3. SIDEBAR NAVIGATION & AUTHENTICATION
# ==========================================
st.sidebar.markdown("### 🔍 Search / Owner Access")
search_query = st.sidebar.text_input("Enter Search Keyword or Owner Key", key="search_query")

if search_query.strip() == SECRET_OWNER_KEY:
    st.session_state.user_id = "owner_admin"
    st.session_state.user_name = "System Owner"
    st.session_state.active_tab = "👑 Owner Control Center"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 Global OTP Login / Register")

login_input = st.sidebar.text_input("Enter Gmail or Mobile Number")

if st.sidebar.button("Send 6-Digit OTP Code"):
    if login_input.strip():
        generated_otp = str(random.randint(100000, 999999))
        st.session_state.sent_otp = generated_otp
        st.session_state.temp_identifier = login_input.strip()
        st.sidebar.info(f"🔑 Your Verification Code: **{generated_otp}**")
    else:
        st.sidebar.warning("⚠️ Enter a valid Gmail or Mobile Number.")

if st.session_state.sent_otp:
    user_otp = st.sidebar.text_input("Enter 6-Digit OTP Code", type="password")
    if st.sidebar.button("Verify & Enter Platform"):
        if user_otp.strip() == st.session_state.sent_otp:
            identifier = st.session_state.temp_identifier
            conn, db_type = get_db_connection()
            c = conn.cursor()
            query = "SELECT * FROM users WHERE phone_number = %s" if db_type == "postgresql" else "SELECT * FROM users WHERE phone_number = ?"
            c.execute(query, (identifier,))
            usr = c.fetchone()

            if not usr:
                new_id = str(uuid.uuid4())
                created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_disp_name = identifier.split('@')[0] if '@' in identifier else identifier
                ins_query = """
                    INSERT INTO users (id, full_name, phone_number, password_hash, country, is_verified, is_suspended, created_at)
                    VALUES (%s, %s, %s, 'OTP_USER', 'Global User', TRUE, FALSE, %s)
                """ if db_type == "postgresql" else """
                    INSERT INTO users (id, full_name, phone_number, password_hash, country, is_verified, is_suspended, created_at)
                    VALUES (?, ?, ?, 'OTP_USER', 'Global User', 1, 0, ?)
                """
                c.execute(ins_query, (new_id, user_disp_name, identifier, created_time))
                conn.commit()
                st.session_state.user_id = new_id
                st.session_state.user_name = user_disp_name
            else:
                st.session_state.user_id = usr["id"]
                st.session_state.user_name = usr["full_name"]

            conn.close()
            st.session_state.sent_otp = None
            st.sidebar.success("🎉 Authentication Successful!")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Code!")

if st.session_state.user_id:
    st.sidebar.markdown(f"Authenticated as: **{st.session_state.user_name}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.active_tab = "🌍 World Feed"
        st.rerun()

nav_tabs = ["🌍 World Feed", "📱 TikTok Shorts Feed", "📺 Direct Long Videos", "📤 Upload Studio", "👤 My Profile", "💵 Monetization Hub"]
if st.session_state.user_id == "owner_admin":
    nav_tabs.append("👑 Owner Control Center")

current_index = nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0
tab = st.sidebar.radio("Navigation", nav_tabs, index=current_index)
st.session_state.active_tab = tab

# ==========================================
# 4. CONTENT FEEDS & PAGES
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
        if media_path and (media_path.startswith("http") or os.path.exists(media_path)):
            st.image(media_path, use_container_width=True)
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
        if media_path and (media_path.startswith("http") or os.path.exists(media_path)):
            st.video(media_path)
        st.markdown('</div>', unsafe_allow_html=True)

# --- Upload Studio ---
elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Upload Studio")
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to publish content.")
    else:
        suspended, until_date = is_user_suspended(st.session_state.user_id)
        if suspended:
            st.error(f"🚫 YOUR ACCOUNT IS SUSPENDED UNTIL {until_date} FOR VIOLATING COMMUNITY SAFETY RULES.")
        else:
            cat = st.selectbox("Category", ["General Post (Photo/Text)", "TikTok Short Video", "Direct Long Video"])
            title_in = st.text_input("Title")
            desc_in = st.text_area("Description")
            
            post_uuid = str(uuid.uuid4())
            created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if cat == "General Post (Photo/Text)":
                f_up = st.file_uploader("Select Photo (Max 15 per day)", type=["jpg", "png", "jpeg"])
                if st.button("Publish Post"):
                    if not check_ai_content_safety(title_in) or not check_ai_content_safety(desc_in):
                        suspend_user_account(st.session_state.user_id, days=30)
                        st.error("🚨 Violating Content Detected! Account suspended.")
                        st.rerun()
                    elif st.session_state.user_id != "owner_admin" and get_daily_upload_count(st.session_state.user_id, "general") >= 15:
                        st.warning("⚠️ Limit reached! Max 15 posts per day.")
                    else:
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
                    elif not check_ai_content_safety(title_in) or not check_ai_content_safety(desc_in):
                        suspend_user_account(st.session_state.user_id, days=30)
                        st.error("🚨 Violating Content Detected! Account suspended.")
                        st.rerun()
                    else:
                        ext = os.path.splitext(v_up.name)[1]
                        media_link = save_media_file(v_up, post_uuid, ext)
                        conn, db_type = get_db_connection()
                        c = conn.cursor()
                        query = "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)" if db_type == "postgresql" else "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                        c.execute(query, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, cat_code, created_time))
                        conn.commit()
                        conn.close()
                        st.success("✅ Video uploaded successfully!")
                        st.rerun()

# --- USER PROFILE & PERSONAL POSTS DASHBOARD ---
elif tab == "👤 My Profile":
    st.markdown("### 👤 User Profile Dashboard")
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to view and edit your profile.")
    else:
        conn, db_type = get_db_connection()
        c = conn.cursor()
        query = "SELECT * FROM users WHERE id = %s" if db_type == "postgresql" else "SELECT * FROM users WHERE id = ?"
        c.execute(query, (st.session_state.user_id,))
        usr = c.fetchone()
        
        show_verified_profile(st.session_state.user_id, subtitle="Verified Active Member")

        profile_tab1, profile_tab2 = st.tabs(["📝 Edit My Profile Settings", "🎬 My Uploaded Videos & Posts"])

        # Tab 1: Edit Profile Details
        with profile_tab1:
            st.markdown("#### Update Profile Info")
            curr_name = usr["full_name"] if usr else st.session_state.user_name
            curr_bio = usr["bio"] if usr and "bio" in usr.keys() and usr["bio"] else ""
            curr_country = usr["country"] if usr and usr["country"] else "Global / Other"

            new_name = st.text_input("Full Name / Display Name", value=curr_name)
            new_bio = st.text_area("Profile Bio / Address Info", value=curr_bio)
            new_country = st.selectbox("Select Country", ["Bangladesh", "United States", "India", "Global / Other"], index=0)

            pic_file = st.file_uploader("Upload Profile Picture (PNG/JPG)", type=["jpg", "png", "jpeg"])

            if st.button("Save Profile Changes"):
                b64_str = usr["profile_pic_base64"] if usr else None
                if pic_file:
                    b64_str = base64.b64encode(pic_file.getvalue()).decode('utf-8')
                
                if db_type == "postgresql":
                    c.execute("UPDATE users SET full_name = %s, bio = %s, country = %s, profile_pic_base64 = %s WHERE id = %s",
                              (new_name, new_bio, new_country, b64_str, st.session_state.user_id))
                else:
                    c.execute("UPDATE users SET full_name = ?, bio = ?, country = ?, profile_pic_base64 = ? WHERE id = ?",
                              (new_name, new_bio, new_country, b64_str, st.session_state.user_id))
                
                conn.commit()
                st.session_state.user_name = new_name
                st.success("🎉 Profile updated successfully!")
                st.rerun()

        # Tab 2: User's Own Uploaded Content
        with profile_tab2:
            st.markdown("#### 📁 My Uploaded Contents")
            p_query = "SELECT * FROM posts WHERE user_id = %s ORDER BY created_at DESC" if db_type == "postgresql" else "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC"
            c.execute(p_query, (st.session_state.user_id,))
            my_posts = [dict(r) for r in c.fetchall()]

            if not my_posts:
                st.info("ℹ️ You haven't uploaded any videos or posts yet.")
            else:
                for item in my_posts:
                    st.markdown('<div class="feed-card">', unsafe_allow_html=True)
                    st.caption(f"Category: **{item['category'].upper()}** | Uploaded: {item['created_at']}")
                    if item.get("title"): st.markdown(f"**{item['title']}**")
                    if item.get("content"): st.write(item["content"])
                    
                    m_path = item.get("media_url")
                    if m_path and (m_path.startswith("http") or os.path.exists(m_path)):
                        if item["category"] in ["short", "long"]:
                            st.video(m_path)
                        else:
                            st.image(m_path, use_container_width=True)
                    
                    if st.button(f"🗑️ Delete Post", key=f"del_{item['id']}"):
                        del_q = "DELETE FROM posts WHERE id = %s" if db_type == "postgresql" else "DELETE FROM posts WHERE id = ?"
                        c.execute(del_q, (item['id'],))
                        conn.commit()
                        st.success("Deleted!")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        conn.close()

# --- Monetization Hub ---
elif tab == "💵 Monetization Hub":
    st.markdown("### 💵 Monetization Hub")
    if not st.session_state.user_id:
        st.warning("⚠️ Please log in to view Monetization status.")
    else:
        st.info("📊 Account Monetization Engine active. Complete 3,000 Watch Hours & 300 Followers to unlock payout settings.")

# --- Owner Control Center ---
elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Master Control Center")
    st.success("👑 Authenticated as System Owner!")
    new_h_text = st.text_input("Header Title Banner Text", value=get_site_setting("header_text", "🛡️ Global AI Book 🛡️"))
    if st.button("Update Header"):
        set_site_setting("header_text", new_h_text)
        st.success("Updated Header!")
        st.rerun()

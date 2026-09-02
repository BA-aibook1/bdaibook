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
# 1. GLOBAL CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Enterprise Global Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
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
# 2. FIXED DATABASE SCHEMA ENGINE
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
                full_name VARCHAR(100) DEFAULT 'Global User',
                identifier VARCHAR(150) UNIQUE NOT NULL,
                country VARCHAR(60) DEFAULT 'Global / Other',
                profile_pic_base64 TEXT,
                is_verified BOOLEAN DEFAULT TRUE,
                is_suspended BOOLEAN DEFAULT FALSE,
                suspended_until TIMESTAMP,
                watch_time_hours REAL DEFAULT 0.0,
                followers_count INT DEFAULT 0,
                is_monetized BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                title TEXT,
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
                full_name TEXT DEFAULT 'Global User',
                identifier TEXT UNIQUE NOT NULL,
                country TEXT DEFAULT 'Global / Other',
                profile_pic_base64 TEXT,
                is_verified INTEGER DEFAULT 1,
                is_suspended INTEGER DEFAULT 0,
                suspended_until TEXT,
                watch_time_hours REAL DEFAULT 0.0,
                followers_count INTEGER DEFAULT 0,
                is_monetized INTEGER DEFAULT 0,
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

# DB Utilities
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

def save_media_file(uploaded_file, file_prefix, extension):
    filename = f"{file_prefix}{extension}"
    target_dir = IMAGE_DIR if extension.lower() in [".jpg", ".png", ".jpeg"] else VIDEO_DIR
    filepath = os.path.join(target_dir, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

# ==========================================
# 3. GLOBAL UI HEADER DISPLAY
# ==========================================
header_text = get_site_setting("header_text", "🛡️ Global AI Book — World Enterprise Platform 🛡️")
header_pic = get_site_setting("header_pic_url", "")
header_width = int(get_site_setting("header_pic_width", "250"))

if header_pic and os.path.exists(header_pic):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(header_pic, width=header_width)

st.markdown(f"<h1 style='text-align: center; color: #00c853;'>{header_text}</h1>", unsafe_allow_html=True)
st.divider()

# Session States
if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "🌍 World Feed"
if "sent_otp" not in st.session_state: st.session_state.sent_otp = None
if "temp_identifier" not in st.session_state: st.session_state.temp_identifier = None

# ==========================================
# 4. SIDEBAR & PASSCODE/OTP AUTH SYSTEM
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
            query = "SELECT * FROM users WHERE identifier = %s" if db_type == "postgresql" else "SELECT * FROM users WHERE identifier = ?"
            c.execute(query, (identifier,))
            usr = c.fetchone()

            if not usr:
                new_id = str(uuid.uuid4())
                created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ins_query = "INSERT INTO users (id, full_name, identifier, created_at) VALUES (%s, %s, %s, %s)" if db_type == "postgresql" else "INSERT INTO users (id, full_name, identifier, created_at) VALUES (?, ?, ?, ?)"
                c.execute(ins_query, (new_id, identifier.split('@')[0], identifier, created_time))
                conn.commit()
                st.session_state.user_id = new_id
                st.session_state.user_name = identifier.split('@')[0]
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
    st.sidebar.markdown(f"LoggedIn: **{st.session_state.user_name}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.active_tab = "🌍 World Feed"
        st.rerun()

nav_tabs = ["🌍 World Feed", "📱 TikTok Shorts Feed", "📺 Direct Long Videos", "📤 Upload Studio"]
if st.session_state.user_id == "owner_admin":
    nav_tabs.append("👑 Owner Control Center")

current_index = nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0
tab = st.sidebar.radio("Navigation", nav_tabs, index=current_index)
st.session_state.active_tab = tab

# ==========================================
# 5. FEEDS & UPLOAD STUDIO (FIXED DB QUERIES)
# ==========================================
if tab == "🌍 World Feed":
    st.markdown("### 🌍 World Feed")
    conn, _ = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE category = 'general' ORDER BY created_at DESC")
    posts = [dict(r) for r in c.fetchall()]
    conn.close()

    for item in posts:
        st.markdown(f"#### {item.get('title', '')}")
        st.write(item.get("content", ""))
        if item.get("media_url") and os.path.exists(item["media_url"]):
            st.image(item["media_url"], use_container_width=True)
        st.divider()

elif tab in ["📱 TikTok Shorts Feed", "📺 Direct Long Videos"]:
    cat_type = "short" if tab == "📱 TikTok Shorts Feed" else "long"
    st.markdown(f"### {'📱 TikTok Shorts Feed' if cat_type == 'short' else '📺 Direct Long Videos'}")
    conn, db_type = get_db_connection()
    c = conn.cursor()
    query = "SELECT * FROM posts WHERE category = %s ORDER BY created_at DESC" if db_type == "postgresql" else "SELECT * FROM posts WHERE category = ? ORDER BY created_at DESC"
    c.execute(query, (cat_type,))
    vids = [dict(r) for r in c.fetchall()]
    conn.close()

    for vid in vids:
        if vid.get("title"): st.subheader(vid['title'])
        st.write(vid.get('content', ''))
        if vid.get("media_url") and os.path.exists(vid["media_url"]):
            st.video(vid["media_url"])
        st.divider()

elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Upload Studio")
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to upload content.")
    else:
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
                st.success("✅ Published successfully!")
                st.rerun()

        else:
            cat_code = "short" if cat == "TikTok Short Video" else "long"
            v_up = st.file_uploader("Select Video", type=["mp4", "mov", "mkv", "avi"])
            if st.button("Publish Video"):
                if not v_up:
                    st.warning("⚠️ Select a video file.")
                else:
                    ext = os.path.splitext(v_up.name)[1]
                    media_link = save_media_file(v_up, post_uuid, ext)
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    query = "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)" if db_type == "postgresql" else "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                    c.execute(query, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, cat_code, created_time))
                    conn.commit()
                    conn.close()
                    st.success("✅ Video Published Successfully!")
                    st.rerun()

# ==========================================
# 6. OWNER CONTROL CENTER
# ==========================================
elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Master Control Center")
    st.success("👑 Authenticated as Global Platform Owner!")
    st.markdown("---")
    
    current_h_text = get_site_setting("header_text", "🛡️ Global AI Book — World Enterprise Platform 🛡️")
    new_h_text = st.text_input("Header Title Banner Text", value=current_h_text)
    
    current_width = int(get_site_setting("header_pic_width", "250"))
    new_width = st.slider("Logo Size (Width in Pixels)", min_value=100, max_value=800, value=current_width, step=10)
    
    h_file = st.file_uploader("Upload New Logo Banner Image", type=["jpg", "png", "jpeg"])
    
    if st.button("Save New Settings"):
        if new_h_text.strip():
            set_site_setting("header_text", new_h_text.strip())
        set_site_setting("header_pic_width", new_width)
        if h_file:
            header_img_path = save_media_file(h_file, "header_banner", ".jpg")
            set_site_setting("header_pic_url", header_img_path)
        
        st.success("🎉 Header and Logo Settings Updated!")
        st.rerun()

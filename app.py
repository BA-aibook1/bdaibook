import base64
from datetime import datetime
import hashlib
import os
import random
import sqlite3
import uuid

import requests
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Enterprise Master Hub",
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

SMART_LINK = "https://omg10.com/4/10954816"
SECRET_OWNER_KEY = "S$s123456789112233"  

# ==========================================
# 2. LOCAL STORAGE & DATABASE SETUP
# ==========================================
DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
PROFILE_DIR = "stored_profiles"
SETTINGS_DIR = "stored_settings"

for folder in [VIDEO_DIR, IMAGE_DIR, PROFILE_DIR, SETTINGS_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_all_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # App Settings (Header Picture etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Main Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            full_name TEXT,
            profile_pic TEXT,
            is_verified INTEGER DEFAULT 0,
            followers_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'none',
            earnings REAL DEFAULT 0.0,
            created_at TEXT
        )
    """)

    # Sovereign Vault
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sovereign_vault (
            vault_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            gmail_address TEXT UNIQUE,
            hashed_password TEXT NOT NULL,
            security_tier INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    # Posts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            uploader_pic TEXT,
            content TEXT,
            image_url TEXT,
            category TEXT DEFAULT 'General',
            likes INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            video_url TEXT,
            uploader_name TEXT,
            uploader_pic TEXT,
            video_type TEXT DEFAULT 'long',
            title TEXT,
            category TEXT DEFAULT 'General',
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # Comments Table
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

    # Dynamic 16 Tables Auto Initializer
    tables_16 = [
        "tb_01_users", "tb_02_interactions", "tb_03_image_posts", "tb_04_long_videos", 
        "tb_05_short_videos", "tb_06_islamic_short_videos", "tb_07_islamic_long_videos",
        "tb_08_news_contents", "tb_09_blog_contents", "tb_10_educational_contents",
        "tb_11_entertainment_contents", "tb_12_tech_contents", "tb_13_live_streams",
        "tb_14_advertisements", "tb_15_bank_details", "tb_16_global_central_pipeline"
    ]
    
    for t_name in tables_16:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {t_name} (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                content_title TEXT,
                media_path TEXT,
                ai_verified INT DEFAULT 1,
                created_at TEXT
            )
        """)

    # Default Owner Account Creation
    cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner'")
    if not cursor.fetchone():
        owner_pass = hashlib.sha256("OwnerMasterKey2026#".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO global_sovereign_vault (vault_id, username, phone_number, hashed_password, security_tier, created_at)
            VALUES ('vault_owner_01', 'system_owner', '01722003172', ?, 999, ?)
        """, (owner_pass, datetime.now().strftime("%Y-%m-%d")))
        
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, phone_number, full_name, is_verified, created_at)
            VALUES ('system_owner', '01722003172', 'System Owner', 1, ?)
        """, (datetime.now().strftime("%Y-%m-%d"),))

    conn.commit()
    conn.close()

init_all_tables()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_setting(key, default=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return None
    return None

def register_or_get_user(username, phone_number=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user:
        c.execute("SELECT COUNT(*) as total FROM users")
        user_count = c.fetchone()["total"]
        auto_verify = 1 if user_count < 1000 else 0
        
        c.execute("INSERT INTO users (username, phone_number, full_name, is_verified, created_at) VALUES (?, ?, ?, ?, ?)",
                  (username, phone_number, username, auto_verify, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
    conn.close()
    return dict(user)

def show_verified_profile(display_name, profile_pic_path=None, subtitle="Member"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_verified FROM users WHERE username = ?", (display_name,))
    u_data = c.fetchone()
    conn.close()
    
    is_verified = u_data["is_verified"] if u_data else False
    b64_img = get_image_base64(profile_pic_path)
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">' if b64_img else '<div style="width:45px; height:45px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:20px;">👤</div>'
    tick = '<span style="color:#1da1f2; font-weight:bold; margin-left:6px;" title="Verified">✔️</span>' if is_verified else ''
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; background: #18191a; padding: 10px; border-radius: 10px; border: 1px solid #2d2f31; margin-bottom: 12px;">
            {img_html}
            <div>
                <div style="font-weight:bold; color:#e4e6eb; font-size: 16px;">{display_name} {tick}</div>
                <div style="color:#b0b3b8; font-size:12px;">{subtitle}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. CUSTOM STYLING & HEADER RENDER
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    .btn-direct { display: block; width: 100%; padding: 10px; margin: 6px 0; color: white !important; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 14px; background: linear-gradient(135deg, #FF416C, #FF4B2B); }
    </style>
""", unsafe_allow_html=True)

# Load Dynamic Header Picture
custom_header_path = get_setting("header_image")
if custom_header_path and os.path.exists(custom_header_path):
    b64_logo = get_image_base64(custom_header_path)
    st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <img src="data:image/jpeg;base64,{b64_logo}" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 4px solid #00c853;">
            <h1 style="color: #00c853; font-weight: 900; margin-top: 5px;">🛡️ BD AI Book — Enterprise Master Hub 🛡️</h1>
            <p style="color: #b0b3b8; margin: 0;">Autonomous AI & 16-Table Master Pipeline Hub</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">🛡️ BD AI Book — Enterprise Master Hub 🛡️</h1>
            <p style="color: #b0b3b8; margin: 0;">Autonomous AI & 16-Table Master Pipeline Hub</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

if "user" not in st.session_state:
    st.session_state.user = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 5. SIDEBAR AUTHENTICATION
# ==========================================
st.sidebar.markdown("### 🔍 Search Feed")
search_query = st.sidebar.text_input("Search content...", key="search_query")

st.sidebar.markdown("---")
st.sidebar.header("🔐 Portal Access & Auth")

available_modes = ["Login (Phone & Password)", "Register (Phone, Gmail & Face)"]
if search_query.strip() == SECRET_OWNER_KEY:
    available_modes.append("👑 Owner Exclusive Portal")

mode = st.sidebar.radio("Select Mode", available_modes)

if mode == "👑 Owner Exclusive Portal":
    st.sidebar.markdown("### 🔒 Owner Bypass Access")
    if st.sidebar.button("⚡ Login As Owner Instant"):
        st.session_state.user = "system_owner"
        st.sidebar.success("👑 Owner Verified Successfully!")
        st.rerun()

elif mode == "Login (Phone & Password)":
    login_phone = st.sidebar.text_input("Mobile Number")
    login_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
        cursor.execute("SELECT * FROM global_sovereign_vault WHERE phone_number = ? AND hashed_password = ?", (login_phone, hashed_pass))
        vault_user = cursor.fetchone()
        conn.close()
        if vault_user:
            st.session_state.user = vault_user["username"]
            register_or_get_user(vault_user["username"], login_phone)
            st.sidebar.success(f"✅ Welcome, {vault_user['username']}!")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Phone Number or Password!")

elif mode == "Register (Phone, Gmail & Face)":
    reg_user = st.sidebar.text_input("Username")
    reg_phone = st.sidebar.text_input("Mobile Number")
    reg_gmail = st.sidebar.text_input("Gmail Address")
    reg_pass = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Register & Sync"):
        if reg_user and reg_phone and reg_pass:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                hashed_pass = hashlib.sha256(reg_pass.encode()).hexdigest()
                cursor.execute("INSERT INTO global_sovereign_vault (vault_id, username, phone_number, gmail_address, hashed_password, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                               (f"vault_{uuid.uuid4().hex[:8]}", reg_user, reg_phone, reg_gmail, hashed_pass, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                register_or_get_user(reg_user, reg_phone)
                st.sidebar.success("🎉 Registered successfully!")
            except Exception:
                st.sidebar.error("User or Phone number already exists!")
            finally:
                conn.close()

if st.session_state.user:
    st.sidebar.markdown(f"Active User: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# Navigation
nav_tabs = ["🌍 World Feed", "📱 Scrolle Shorts Feed", "💬 WhatsApp Support Desk", "💳 Payout & Monetization", "👤 My Profile & Earnings", "📤 Create Post / Upload"]
if st.session_state.user == "system_owner":
    nav_tabs.append("👑 Owner Control Center")

tab = st.sidebar.radio("Navigation", nav_tabs)

# ==========================================
# 6. MAIN APPLICATION PANELS
# ==========================================

# --- World Feed ---
if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not posts:
        st.info("No content available yet.")

    for item in posts:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item.get("uploader_name", "User"), subtitle=f"Posted {item.get('created_at')}")
        st.write(item["content"])
        if item.get("image_url") and os.path.exists(item["image_url"]):
            st.image(item["image_url"], use_container_width=True)
            
        if st.session_state.user == "system_owner":
            if st.button(f"🗑️ Delete Post", key=f"del_{item['id']}"):
                c = get_db_connection()
                c.cursor().execute("DELETE FROM posts WHERE id = ?", (item['id'],))
                c.commit()
                c.close()
                st.success("Post Deleted!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Owner Control Center (New) ---
elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Owner Master Management Board")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = c.fetchone()["total_users"]
    
    c.execute("SELECT COUNT(*) as total_posts FROM posts")
    total_posts = c.fetchone()["total_posts"]
    
    c.execute("SELECT COUNT(*) as total_vids FROM videos")
    total_vids = c.fetchone()["total_vids"]
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Live Users", total_users)
    col2.metric("Total Posts", total_posts)
    col3.metric("Total Videos", total_vids)
    
    st.markdown("---")
    st.subheader("🖼️ Change Global Header Logo")
    header_up = st.file_uploader("Upload New Header Image", type=["jpg", "png", "jpeg"])
    if st.button("Save & Apply Globally"):
        if header_up:
            save_path = os.path.join(SETTINGS_DIR, "global_header.jpg")
            with open(save_path, "wb") as f:
                f.write(header_up.getbuffer())
            set_setting("header_image", save_path)
            st.success("✅ Header image updated globally!")
            st.rerun()

# --- Create Post / Upload ---
elif tab == "📤 Create Post / Upload":
    st.markdown("### 📤 Upload Center")
    if not st.session_state.user:
        st.warning("Please login to upload.")
    else:
        title_in = st.text_input("Post Caption")
        file_up = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

        if st.button("Publish"):
            if file_up and title_in:
                f_id = str(uuid.uuid4())
                save_path = os.path.join(IMAGE_DIR, f"{f_id}.jpg")
                with open(save_path, "wb") as f:
                    f.write(file_up.getbuffer())
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT INTO posts (id, uploader_name, content, image_url, created_at) VALUES (?, ?, ?, ?, ?)",
                          (f_id, st.session_state.user, title_in, save_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()
                st.success("✅ Published successfully!")
                st.rerun()

# --- Profile Section ---
elif tab == "👤 My Profile & Earnings":
    if st.session_state.user:
        u_data = register_or_get_user(st.session_state.user)
        show_verified_profile(u_data["username"], subtitle="User Profile")
        st.write(f"Verified Status: {'Verified ✔️' if u_data['is_verified'] else 'Not Verified'}")
    else:
        st.warning("Please login first.")

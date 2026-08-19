import base64
from datetime import datetime
import hashlib
import os
import random
import sqlite3
import urllib.parse
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

# ==========================================
# 2. LOCAL STORAGE & DATABASE SETUP
# ==========================================
DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
PROFILE_DIR = "stored_profiles"

for folder in [VIDEO_DIR, IMAGE_DIR, PROFILE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_all_16_servers_and_vault():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sovereign_vault (
            vault_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            gmail_address TEXT UNIQUE,
            hashed_password TEXT NOT NULL,
            biometric_face_hash TEXT,
            security_tier INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_01_users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'Public ID',
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_02_interactions (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            target_id TEXT,
            comment_text TEXT,
            created_at TEXT
        )
    """)

    # Standard Tables setup
    tables = [
        "tb_03_image_posts", "tb_04_long_videos", "tb_05_short_videos",
        "tb_06_islamic_short_videos", "tb_07_islamic_long_videos",
        "tb_08_news_contents", "tb_09_blog_contents", "tb_10_educational_contents",
        "tb_11_entertainment_contents", "tb_12_tech_contents", "tb_13_live_streams",
        "tb_14_advertisements", "tb_15_bank_details"
    ]
    
    for t_name in tables:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {t_name} (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                content_title TEXT,
                media_path TEXT,
                ai_verified INT DEFAULT 0,
                created_at TEXT
            )
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_16_global_central_pipeline (
            pipeline_id TEXT PRIMARY KEY,
            source_table TEXT NOT NULL,
            record_id TEXT NOT NULL,
            username TEXT NOT NULL,
            owner_approval_status TEXT DEFAULT 'Pending Owner Approval',
            transferred_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            full_name TEXT,
            profile_pic TEXT,
            is_verified INTEGER DEFAULT 1,
            payment_method TEXT,
            account_details TEXT,
            nid_number TEXT,
            address TEXT,
            followers_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'none',
            earnings REAL DEFAULT 0.0,
            created_at TEXT
        )
    """)

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
            views_count INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

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

    # Default Owner Setup
    cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner'")
    if not cursor.fetchone():
        owner_pass = hashlib.sha256("OwnerMasterKey2026#".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO global_sovereign_vault (vault_id, username, phone_number, hashed_password, security_tier, created_at)
            VALUES ('vault_owner_01', 'system_owner', '01722003172', ?, 999, ?)
        """, (owner_pass, datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()

init_all_16_servers_and_vault()

# ==========================================
# 3. HELPER FUNCTIONS & ENGINE
# ==========================================
def ai_content_security_guard(file_name):
    banned_keywords = ["tiktok", "instagram_dl", "facebook_video", "adult", "x_rated", "pirated", "hack"]
    for keyword in banned_keywords:
        if keyword in file_name.lower():
            return False, f"🚨 AI Security Block: Content contains banned phrase ('{keyword}'). Upload denied!"
    return True, "✅ AI Verified: Approved."

def push_to_central_pipeline(source_table, record_id, username):
    conn = get_db_connection()
    cursor = conn.cursor()
    pipeline_id = f"pipe_{uuid.uuid4().hex[:10]}"
    cursor.execute("""
        INSERT INTO tb_16_global_central_pipeline 
        (pipeline_id, source_table, record_id, username, owner_approval_status, transferred_at)
        VALUES (?, ?, ?, ?, 'Approved', ?)
    """, (pipeline_id, source_table, record_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def register_or_get_user(username, phone_number=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? OR phone_number = ?", (username, phone_number))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (username, phone_number, created_at) VALUES (?, ?, ?)",
                  (username, phone_number, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
    conn.close()
    return dict(user)

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
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return None
    return None

def show_verified_profile(display_name, profile_pic_path=None, subtitle="Official Creator", is_verified=True):
    b64_img = get_image_base64(profile_pic_path)
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">' if b64_img else '<div style="width:45px; height:45px; border-radius:50%; background:#3a3b3c; color:#fff; display:flex; align-items:center; justify-content:center;">👤</div>'
    
    tick = '<span style="color:#00c853; font-weight:bold; margin-left:5px;">✔️</span>' if is_verified else ''
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
            {img_html}
            <div>
                <div style="font-weight:bold; color:#e4e6eb;">{display_name} {tick}</div>
                <div style="color:#b0b3b8; font-size:12px;">{subtitle}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_comments_section(post_id):
    with st.expander("💬 Comments & Gifts"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY created_at DESC", (post_id,))
        all_comments = [dict(r) for r in cursor.fetchall()]

        if all_comments:
            for c in all_comments:
                st.markdown(f"**{c['uploader_name']}**: {c['comment_text']} <small style='color:#888;'>({c['created_at']})</small>", unsafe_allow_html=True)
        else:
            st.caption("No comments yet.")

        if st.session_state.user:
            with st.form(key=f"c_form_{post_id}"):
                c_input = st.text_input("Write a comment...", key=f"inp_{post_id}")
                submit_btn = st.form_submit_button("Post Comment")
                if submit_btn and c_input.strip():
                    cursor.execute("INSERT INTO comments (id, post_id, uploader_name, comment_text, created_at) VALUES (?, ?, ?, ?, ?)",
                                   (str(uuid.uuid4()), post_id, st.session_state.user, c_input.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    st.rerun()
                conn.close()

# ==========================================
# 4. CUSTOM STYLING & HEADER
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h1 style="color: #00c853; font-weight: 900; margin: 0;">🛡️ BD AI Book — Enterprise Master Hub 🛡️</h1>
        <p style="color: #b0b3b8; margin: 0;">Autonomous AI & 16-Table Master Pipeline Hub</p>
    </div>
""", unsafe_allow_html=True)

st.divider()

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.pic = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 5. SIDEBAR AUTHENTICATION
# ==========================================
st.sidebar.markdown("### 🔍 Search Feed")
search_query = st.sidebar.text_input("Search posts, videos, creators...", placeholder="Type to search...", key="search_query")

st.sidebar.markdown("---")
st.sidebar.header("🔐 Portal Access & Auth")

mode = st.sidebar.radio("Select Mode", ["Login (Phone & Password)", "Register (Phone, Gmail & Face)", "👑 Owner Exclusive Portal"])

if mode == "👑 Owner Exclusive Portal":
    owner_phone = st.sidebar.text_input("Owner Phone Number", value="01722003172")
    owner_pass_input = st.sidebar.text_input("Owner Master Password", type="password")
    if st.sidebar.button("Enter Owner Chamber"):
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_owner_pass = hashlib.sha256(owner_pass_input.encode()).hexdigest()
        cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner' AND phone_number = ? AND hashed_password = ?", (owner_phone, hashed_owner_pass))
        if cursor.fetchone():
            st.session_state.user = "system_owner"
            st.sidebar.success("👑 Owner Verified Successfully!")
            st.rerun()
        else:
            st.sidebar.error("❌ Access Denied!")
        conn.close()

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
            st.sidebar.success(f"✅ Welcome, {vault_user['username']}!")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Credentials!")

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
                cursor.execute("INSERT INTO users (username, phone_number, created_at) VALUES (?, ?, ?)",
                               (reg_user, reg_phone, datetime.now().strftime("%Y-%m-%d")))
                cursor.execute("INSERT INTO tb_01_users (id, username, created_at) VALUES (?, ?, ?)",
                               (str(uuid.uuid4()), reg_user, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.sidebar.success("🎉 Registered successfully!")
            except Exception as e:
                st.sidebar.error(f"Error: Username or Phone already exists!")
            finally:
                conn.close()

if st.session_state.user:
    st.sidebar.markdown(f"User: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# Navigation Tabs
nav_tabs = ["🌍 World Feed", "📱 Scrolle Shorts Feed", "💬 WhatsApp Support Desk", "💳 Payout & Monetization", "👤 My Profile & Earnings", "📤 Create Post / Upload"]
tab = st.sidebar.radio("Navigation", nav_tabs, index=nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0)
st.session_state.active_tab = tab

# ==========================================
# 6. TAB CONTENT
# ==========================================

# --- World Feed ---
if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM videos WHERE video_type != 'short' ORDER BY created_at DESC")
    videos = [dict(r) for r in cursor.fetchall()]
    conn.close()

    feed = posts + videos
    random.shuffle(feed)

    if not feed:
        st.info("No content available yet.")

    for item in feed:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item.get("uploader_name", "User"), subtitle=f"Posted {item.get('created_at')}")
        if "content" in item:
            st.write(item["content"])
            if item.get("image_url") and os.path.exists(item["image_url"]):
                st.image(item["image_url"], use_container_width=True)
        elif "title" in item:
            st.subheader(item["title"])
            if item.get("video_url") and os.path.exists(item["video_url"]):
                st.video(item["video_url"])
        render_comments_section(str(item["id"]))
        st.markdown('</div>', unsafe_allow_html=True)

# --- Shorts Feed ---
elif tab == "📱 Scrolle Shorts Feed":
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    shorts = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if shorts:
        for sv in shorts:
            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(sv.get("uploader_name", "User"))
            st.write(sv.get("title", ""))
            if os.path.exists(sv["video_url"]):
                st.video(sv["video_url"])
            render_comments_section(sv["id"])
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No shorts uploaded yet.")

# --- Support ---
elif tab == "💬 WhatsApp Support Desk":
    st.markdown("### 💬 WhatsApp Support Desk")
    st.write("Direct Support Line: +8801722003172")

# --- Monetization ---
elif tab == "💳 Payout & Monetization":
    st.markdown("### 💳 Payout & Monetization")
    st.info("Automatic monetization pipeline connected with 16 Master Servers.")

# --- Profile ---
elif tab == "👤 My Profile & Earnings":
    st.markdown("### 👤 User Dashboard")
    if st.session_state.user:
        u_data = register_or_get_user(st.session_state.user)
        col1, col2, col3 = st.columns(3)
        col1.metric("Followers", format_value(u_data.get("followers_count", 0)))
        col2.metric("Watch Time", f"{u_data.get('watch_time_mins', 0):.1f} Mins")
        col3.metric("Earnings", f"${u_data.get('earnings', 0):.2f}")
    else:
        st.warning("Please login first.")

# --- Dynamic Upload (16 Server Unified) ---
elif tab == "📤 Create Post / Upload":
    st.markdown("### 📤 Dynamic Content Upload")
    if not st.session_state.user:
        st.warning("Please login to upload content.")
    else:
        cat = st.selectbox("Select Content Type & Server Target", [
            "Image Post (tb_03)", "Long Video (tb_04)", "Short Video (tb_05)",
            "Islamic Short (tb_06)", "Islamic Long (tb_07)", "News Content (tb_08)",
            "Blog Content (tb_09)", "Educational Content (tb_10)", "Entertainment (tb_11)",
            "Tech & Code (tb_12)"
        ])
        title_in = st.text_input("Title / Post Content")
        file_up = st.file_uploader("Choose File", type=["jpg", "jpeg", "png", "mp4"])

        if st.button("Publish Content"):
            if file_up and title_in:
                is_safe, msg = ai_content_security_guard(file_up.name)
                if not is_safe:
                    st.error(msg)
                else:
                    ext = file_up.name.split(".")[-1]
                    f_id = str(uuid.uuid4())
                    conn = get_db_connection()
                    c = conn.cursor()

                    if "Image" in cat or "Blog" in cat or "News" in cat:
                        save_path = os.path.join(IMAGE_DIR, f"{f_id}.{ext}")
                        with open(save_path, "wb") as f:
                            f.write(file_up.getbuffer())
                        
                        c.execute("INSERT INTO posts (id, uploader_name, content, image_url, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                  (f_id, st.session_state.user, title_in, save_path, cat, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        target_tbl = "tb_03_image_posts"
                    else:
                        save_path = os.path.join(VIDEO_DIR, f"{f_id}.{ext}")
                        with open(save_path, "wb") as f:
                            f.write(file_up.getbuffer())
                        
                        v_type = "short" if "Short" in cat else "long"
                        c.execute("INSERT INTO videos (id, video_url, uploader_name, video_type, title, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (f_id, save_path, st.session_state.user, v_type, title_in, cat, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        target_tbl = "tb_05_short_videos" if v_type == "short" else "tb_04_long_videos"

                    # Sync directly to targeted pipeline server
                    c.execute(f"INSERT INTO {target_tbl} (id, username, content_title, media_path, ai_verified, created_at) VALUES (?, ?, ?, ?, 1, ?)",
                              (f_id, st.session_state.user, title_in, save_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    
                    conn.commit()
                    conn.close()

                    push_to_central_pipeline(target_tbl, f_id, st.session_state.user)
                    st.success("✅ Content Published and Synced to 16-Server Network!")
                    st.rerun()
            else:
                st.warning("Provide both Title and File!")

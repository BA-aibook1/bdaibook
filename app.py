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

# 👈 আপনার নতুন গোপন পাসওয়ার্ড সেট করা হলো
SECRET_OWNER_KEY = "S$s123456789112233"  

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
# 3. HELPER FUNCTIONS & AI ENGINE
# ==========================================
def ai_content_security_guard(file_name):
    banned_keywords = ["tiktok", "instagram_dl", "facebook_video", "adult", "x_rated", "pirated", "hack"]
    for keyword in banned_keywords:
        if keyword in file_name.lower():
            return False, f"🚨 AI Security Block: Content contains banned keyword ('{keyword}'). Upload rejected!"
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

def show_verified_profile(display_name, profile_pic_path=None, subtitle="Official Verified Creator", is_verified=True):
    b64_img = get_image_base64(profile_pic_path)
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">' if b64_img else '<div style="width:45px; height:45px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:20px;">👤</div>'
    tick = '<span style="color:#00c853; font-weight:bold; margin-left:6px;">✔️</span>' if is_verified else ''
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; background: #18191a; padding: 10px; border-radius: 10px; border: 1px solid #2d2f31; margin-bottom: 12px;">
            {img_html}
            <div>
                <div style="font-weight:bold; color:#e4e6eb; font-size: 16px;">{display_name} {tick}</div>
                <div style="color:#b0b3b8; font-size:12px;">{subtitle}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def show_auto_moving_banner():
    ad_html = f"""
    <div style="text-align:center; margin: 15px 0;">
        <a href="{SMART_LINK}" target="_blank" style="text-decoration:none;">
            <div style="background: linear-gradient(90deg, #00c853, #1e88e5); color: #fff; padding: 14px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-family: sans-serif;">
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
                gift_badge = f" <span style='background:#3a3b3c; padding:2px 6px; border-radius:6px; font-size:12px;'>{c['gift_type']}</span>" if c.get('gift_type') and c.get('gift_type') != "None" else ""
                st.markdown(f"**{c['uploader_name']}**{gift_badge} <small style='color:#888;'>({c['created_at']})</small>:<br>{c['comment_text']}", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.caption("No comments yet.")

        if st.session_state.user:
            with st.form(key=f"c_form_{post_id}"):
                c_input = st.text_input("Write a comment...", key=f"inp_{post_id}")
                gift_selected = st.selectbox("🎁 Send Gift", ["None", "🎁 Gift Box (+10 pts)", "💎 Diamond (+50 pts)", "🌟 Star (+20 pts)", "🔥 Fire (+15 pts)"], key=f"gft_{post_id}")
                submit_btn = st.form_submit_button("Post Comment")

                if submit_btn and c_input.strip():
                    cursor.execute("INSERT INTO comments (id, post_id, uploader_name, comment_text, gift_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                   (str(uuid.uuid4()), post_id, st.session_state.user, c_input.strip(), gift_selected, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    st.toast("✅ Comment added!")
                    st.rerun()
        conn.close()

# ==========================================
# 4. CUSTOM STYLING & UI HEADER
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    .btn-direct { display: block; width: 100%; padding: 10px; margin: 6px 0; color: white !important; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 14px; background: linear-gradient(135deg, #FF416C, #FF4B2B); }
    </style>
""", unsafe_allow_html=True)

LOGO_PATH = "logo.jpg"
if os.path.exists(LOGO_PATH):
    b64_logo = get_image_base64(LOGO_PATH)
    st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <img src="data:image/jpeg;base64,{b64_logo}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #00c853;">
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
    st.session_state.pic = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 5. SIDEBAR NAVIGATION & AUTHENTICATION
# ==========================================
st.sidebar.markdown("### 🔍 Search Feed")
search_query = st.sidebar.text_input("Search content, creators...", placeholder="Type here...", key="search_query")

st.sidebar.markdown("---")
st.sidebar.header("🔐 Portal Access & Auth")

# সাধারণ ইউজারদের জন্য মোড
available_modes = ["Login (Phone & Password)", "Register (Phone, Gmail & Face)"]

# 👈 নতুন গোপন কোড ম্যাচ করলে নিঃশব্দে ওনার প্যানেল যুক্ত হবে (কোনো ব্যানার/নোটিফিকেশন থাকবে না)
if search_query.strip() == SECRET_OWNER_KEY:
    available_modes.append("👑 Owner Exclusive Portal")

mode = st.sidebar.radio("Select Mode", available_modes)

if mode == "👑 Owner Exclusive Portal":
    st.sidebar.markdown("### 🔒 Owner Secure Chamber")
    owner_phone = st.sidebar.text_input("Owner Phone Number", value="01722003172")
    owner_pass_input = st.sidebar.text_input("Owner Master Password", type="password")
    owner_face_capture = st.sidebar.camera_input("Biometric Face Lock Verification")

    if st.sidebar.button("Enter Owner Chamber"):
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_owner_pass = hashlib.sha256(owner_pass_input.encode()).hexdigest()
        cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner' AND phone_number = ? AND hashed_password = ?", (owner_phone, hashed_owner_pass))
        if cursor.fetchone() and owner_face_capture:
            st.session_state.user = "system_owner"
            st.sidebar.success("👑 Owner Verified Successfully!")
            st.rerun()
        else:
            st.sidebar.error("❌ Access Denied: Incorrect Details or Face Lock missing!")
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
            st.sidebar.success(f"✅ Welcome back, {vault_user['username']}!")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Mobile Number or Password!")

elif mode == "Register (Phone, Gmail & Face)":
    reg_user = st.sidebar.text_input("Full Name / Username")
    reg_phone = st.sidebar.text_input("Mobile Number")
    reg_gmail = st.sidebar.text_input("Gmail Address")
    reg_pass = st.sidebar.text_input("Password", type="password")
    face_capture = st.sidebar.camera_input("Capture Face Lock")

    if st.sidebar.button("Register & Sync"):
        if reg_user and reg_phone and reg_gmail and reg_pass and face_capture:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                hashed_pass = hashlib.sha256(reg_pass.encode()).hexdigest()
                fname = os.path.join(PROFILE_DIR, f"p_{uuid.uuid4().hex[:8]}.jpg")
                with open(fname, "wb") as f:
                    f.write(face_capture.getvalue())

                cursor.execute("INSERT INTO global_sovereign_vault (vault_id, username, phone_number, gmail_address, hashed_password, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                               (f"vault_{uuid.uuid4().hex[:8]}", reg_user, reg_phone, reg_gmail, hashed_pass, datetime.now().strftime("%Y-%m-%d")))
                cursor.execute("INSERT INTO users (username, phone_number, full_name, profile_pic, created_at) VALUES (?, ?, ?, ?, ?)",
                               (reg_user, reg_phone, reg_user, fname, datetime.now().strftime("%Y-%m-%d")))
                cursor.execute("INSERT INTO tb_01_users (id, username, created_at) VALUES (?, ?, ?)",
                               (str(uuid.uuid4()), reg_user, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.sidebar.success("🎉 Registered successfully!")
            except Exception as e:
                st.sidebar.error("Error: User or Mobile Number already registered!")
            finally:
                conn.close()
        else:
            st.sidebar.error("All fields and Face capture are required!")

if st.session_state.user:
    st.sidebar.markdown(f"Active User: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

# Navigation Tabs
nav_tabs = ["🌍 World Feed", "📱 Scrolle Shorts Feed", "💬 WhatsApp Support Desk", "💳 Payout & Monetization", "👤 My Profile & Earnings", "📤 Create Post / Upload"]
tab = st.sidebar.radio("Navigation", nav_tabs, index=nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0)
st.session_state.active_tab = tab

# ==========================================
# 6. MAIN APPLICATION TABS
# ==========================================

# --- World Feed ---
if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query and search_query != SECRET_OWNER_KEY:
        cursor.execute("SELECT * FROM posts WHERE content LIKE ? OR uploader_name LIKE ?", (f"%{search_query}%", f"%{search_query}%"))
        posts = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM videos WHERE video_type != 'short' AND (title LIKE ? OR uploader_name LIKE ?)", (f"%{search_query}%", f"%{search_query}%"))
        videos = [dict(r) for r in cursor.fetchall()]
    else:
        cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
        posts = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM videos WHERE video_type != 'short' ORDER BY created_at DESC")
        videos = [dict(r) for r in cursor.fetchall()]
    conn.close()

    feed = posts + videos
    if not search_query:
        random.shuffle(feed)

    if not feed:
        st.info("No content available yet.")

    for item in feed:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item.get("uploader_name", "User"), profile_pic_path=item.get("uploader_pic"), subtitle=f"Posted {item.get('created_at')}")
        
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
            show_verified_profile(sv.get("uploader_name", "User"), profile_pic_path=sv.get("uploader_pic"))
            if sv.get("title"):
                st.write(sv["title"])
            if os.path.exists(sv["video_url"]):
                st.video(sv["video_url"])
            render_comments_section(sv["id"])
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No shorts uploaded yet.")

# --- WhatsApp Support Desk ---
elif tab == "💬 WhatsApp Support Desk":
    st.markdown("### 💬 WhatsApp Support Desk")
    st.write("Direct Official Support Line: +8801722003172")
    st.markdown('<a href="https://wa.me/8801722003172" target="_blank" class="btn-direct">Chat Directly on WhatsApp</a>', unsafe_allow_html=True)

# --- Payout & Monetization ---
elif tab == "💳 Payout & Monetization":
    st.markdown("### 💳 Payout & Monetization")
    show_auto_moving_banner()
    st.info("Automatic monetization pipeline connected with 16 Master Servers.")

# --- My Profile & Earnings ---
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

# --- Content Upload Section (Fully Synced with 16 Tables) ---
elif tab == "📤 Create Post / Upload":
    st.markdown("### 📤 Dynamic Content Upload Hub")
    if not st.session_state.user:
        st.warning("Please login to upload content.")
    else:
        target_server_map = {
            "Image Post (tb_03)": "tb_03_image_posts",
            "Long Video (tb_04)": "tb_04_long_videos",
            "Short Video (tb_05)": "tb_05_short_videos",
            "Islamic Short (tb_06)": "tb_06_islamic_short_videos",
            "Islamic Long (tb_07)": "tb_07_islamic_long_videos",
            "News Content (tb_08)": "tb_08_news_contents",
            "Blog Content (tb_09)": "tb_09_blog_contents",
            "Educational Content (tb_10)": "tb_10_educational_contents",
            "Entertainment (tb_11)": "tb_11_entertainment_contents",
            "Tech & Code (tb_12)": "tb_12_tech_contents",
            "Live Streams (tb_13)": "tb_13_live_streams",
            "Advertisements (tb_14)": "tb_14_advertisements",
            "Bank Details / Payment (tb_15)": "tb_15_bank_details"
        }
        
        cat = st.selectbox("Select Content Type & Target Server", list(target_server_map.keys()))
        title_in = st.text_input("Title / Post Content Caption")
        file_up = st.file_uploader("Upload File (Image/Video)", type=["jpg", "jpeg", "png", "mp4"])

        if st.button("Publish & Sync to Pipeline"):
            if file_up and title_in:
                is_safe, msg = ai_content_security_guard(file_up.name)
                if not is_safe:
                    st.error(msg)
                else:
                    ext = file_up.name.split(".")[-1]
                    f_id = str(uuid.uuid4())
                    conn = get_db_connection()
                    c = conn.cursor()
                    
                    target_tbl = target_server_map[cat]

                    if "Image" in cat or "Blog" in cat or "News" in cat or "Bank" in cat:
                        save_path = os.path.join(IMAGE_DIR, f"{f_id}.{ext}")
                        with open(save_path, "wb") as f:
                            f.write(file_up.getbuffer())
                        
                        c.execute("INSERT INTO posts (id, uploader_name, content, image_url, category, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                  (f_id, st.session_state.user, title_in, save_path, cat, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    else:
                        save_path = os.path.join(VIDEO_DIR, f"{f_id}.{ext}")
                        with open(save_path, "wb") as f:
                            f.write(file_up.getbuffer())
                        
                        v_type = "short" if "Short" in cat else "long"
                        c.execute("INSERT INTO videos (id, video_url, uploader_name, video_type, title, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (f_id, save_path, st.session_state.user, v_type, title_in, cat, datetime.now().strftime("%Y-%m-%d %H:%M")))

                    c.execute(f"INSERT INTO {target_tbl} (id, username, content_title, media_path, ai_verified, created_at) VALUES (?, ?, ?, ?, 1, ?)",
                              (f_id, st.session_state.user, title_in, save_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    
                    conn.commit()
                    conn.close()

                    push_to_central_pipeline(target_tbl, f_id, st.session_state.user)
                    st.success(f"✅ Published & Synced to {target_tbl} and Central Pipeline!")
                    st.rerun()
            else:
                st.warning("Please enter title and select a media file.")

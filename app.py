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
# 1. PAGE CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Global Enterprise Platform",
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            full_name TEXT,
            country TEXT DEFAULT 'Global',
            profile_pic TEXT,
            is_verified INTEGER DEFAULT 0,
            followers_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'none',
            earnings REAL DEFAULT 0.0,
            is_banned INTEGER DEFAULT 0,
            ban_until TEXT,
            violations_count INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sovereign_vault (
            vault_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            gmail_address TEXT UNIQUE,
            country TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            security_tier INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            content TEXT,
            title TEXT,
            tags TEXT,
            image_url TEXT,
            likes INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            video_url TEXT,
            uploader_name TEXT,
            video_type TEXT DEFAULT 'short',
            title TEXT,
            description TEXT,
            tags TEXT,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_upload_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            upload_type TEXT,
            upload_date TEXT
        )
    """)

    # 16-Table Synchronized Architecture
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

    cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner'")
    if not cursor.fetchone():
        owner_pass = hashlib.sha256("OwnerMasterKey2026#".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO global_sovereign_vault (vault_id, username, phone_number, country, hashed_password, security_tier, created_at)
            VALUES ('vault_owner_01', 'system_owner', '01722003172', 'Global HQ', ?, 999, ?)
        """, (owner_pass, datetime.now().strftime("%Y-%m-%d")))
        
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, phone_number, full_name, country, is_verified, created_at)
            VALUES ('system_owner', '01722003172', 'System Owner', 'Global HQ', 1, ?)
        """, (datetime.now().strftime("%Y-%m-%d"),))

    conn.commit()
    conn.close()

init_all_tables()

# ==========================================
# 3. AI GUARD, GEO-BLOCK & AUTONOMOUS MODERATION
# ==========================================
BANNED_WORDS = ["sex", "adult", "18+", "porn", "nude", "tiktok", "youtube", "facebook", "reels", "shorts", "stolen", "watermark"]

# Allowed Country List (Israel Excluded & Blocked)
ALLOWED_COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Australia", "Bangladesh", "Saudi Arabia", 
    "United Arab Emirates", "Qatar", "Kuwait", "Oman", "Bahrain", "Malaysia", "Indonesia", 
    "Pakistan", "Turkey", "Germany", "France", "Italy", "Japan", "South Korea", "China", 
    "Brazil", "South Africa", "Nigeria", "Egypt", "Singapore", "Others (Global)"
]

def ai_content_shield(title, description, tags, file_name):
    """AI Guardian Engine for Auto Moderation"""
    full_text = f"{title} {description} {tags} {file_name}".lower()
    
    for word in BANNED_WORDS:
        if word in full_text:
            return False, f"⚠️ Blocked by AI Security Protocol! Reason: Inappropriate content or copyrighted media from external platforms (YouTube/TikTok/Facebook) is strictly prohibited."
    return True, "OK"

def check_upload_limit(username, upload_type):
    """Daily Limit Logic: 1 Short, 1 Long Video, 10 Posts"""
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM daily_upload_limits WHERE username = ? AND upload_type = ? AND upload_date = ?", 
              (username, upload_type, today))
    res = c.fetchone()["count"]
    conn.close()

    if upload_type == "post" and res >= 10:
        return False, "⚠️ Daily limit reached! You can only publish 10 posts per day."
    elif upload_type == "short" and res >= 1:
        return False, "⚠️ Daily limit reached! You can only upload 1 Short video per day."
    elif upload_type == "long" and res >= 1:
        return False, "⚠️ Daily limit reached! You can only upload 1 Long video per day."
    
    return True, "OK"

def record_upload(username, upload_type):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO daily_upload_limits (username, upload_type, upload_date) VALUES (?, ?, ?)",
              (username, upload_type, today))
    conn.commit()
    conn.close()

def sync_to_16_tables(content_id, username, title, path, target_table):
    """Automatic 16-Table Pipeline Sync"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"INSERT OR REPLACE INTO {target_table} (id, username, content_title, media_path, created_at) VALUES (?, ?, ?, ?, ?)",
              (content_id, username, title, path, datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.execute("INSERT OR REPLACE INTO tb_16_global_central_pipeline (id, username, content_title, media_path, created_at) VALUES (?, ?, ?, ?, ?)",
              (content_id, username, title, path, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def apply_user_penalty(username):
    """1-Month Suspension or Permanent Deletion Algorithm"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT violations_count FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    v_count = (row["violations_count"] + 1) if row else 1

    if v_count >= 2:
        # Permanent Account & Content Deletion
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        c.execute("DELETE FROM global_sovereign_vault WHERE username = ?", (username,))
        c.execute("DELETE FROM posts WHERE uploader_name = ?", (username,))
        c.execute("DELETE FROM videos WHERE uploader_name = ?", (username,))
        conn.commit()
        conn.close()
        return "❌ Your account and contents have been permanently deleted due to repeated policy violations!"
    else:
        # 1-Month Ban
        ban_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        c.execute("UPDATE users SET is_banned = 1, ban_until = ?, violations_count = ? WHERE username = ?", 
                  (ban_date, v_count, username))
        conn.commit()
        conn.close()
        return "⚠️ You have been banned for 1 month due to policy violations!"

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
def get_setting(key, default=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row["value"] if row else default

def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return None
    return None

def register_or_get_user(username, phone_number=None, country="Global"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    if not user:
        c.execute("SELECT COUNT(*) as total FROM users")
        user_count = c.fetchone()["total"]
        auto_verify = 1 if user_count < 1000 else 0
        
        c.execute("INSERT INTO users (username, phone_number, full_name, country, is_verified, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, phone_number, username, country, auto_verify, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
    conn.close()
    return dict(user)

def show_verified_profile(display_name, profile_pic_path=None, subtitle="Member"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_verified, country FROM users WHERE username = ?", (display_name,))
    u_data = c.fetchone()
    conn.close()
    
    is_verified = u_data["is_verified"] if u_data else False
    user_country = u_data["country"] if u_data and u_data["country"] else "Global"
    b64_img = get_image_base64(profile_pic_path)
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">' if b64_img else '<div style="width:45px; height:45px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:20px;">👤</div>'
    tick = '<span style="color:#1da1f2; font-weight:bold; margin-left:6px;" title="Verified Creator">✔️</span>' if is_verified else ''
    
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; background: #18191a; padding: 10px; border-radius: 10px; border: 1px solid #2d2f31; margin-bottom: 12px;">
            {img_html}
            <div>
                <div style="font-weight:bold; color:#e4e6eb; font-size: 16px;">{display_name} {tick}</div>
                <div style="color:#b0b3b8; font-size:12px;">{subtitle} • 🌐 {user_country}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 5. CUSTOM UI STYLING
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

custom_header_path = get_setting("header_image")
if custom_header_path and os.path.exists(custom_header_path):
    b64_logo = get_image_base64(custom_header_path)
    st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <img src="data:image/jpeg;base64,{b64_logo}" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 4px solid #00c853;">
            <h1 style="color: #00c853; font-weight: 900; margin-top: 5px;">🛡️ BD AI Book — Enterprise Global Hub 🛡️</h1>
            <p style="color: #b0b3b8; margin: 0;">Autonomous AI & 16-Table Global Pipeline Hub</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">🛡️ BD AI Book — Enterprise Global Hub 🛡️</h1>
            <p style="color: #b0b3b8; margin: 0;">Autonomous AI & 16-Table Global Pipeline Hub</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

if "user" not in st.session_state:
    st.session_state.user = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 6. SIDEBAR AUTHENTICATION & GLOBAL ACCESS
# ==========================================
st.sidebar.markdown("### 🔍 Search Feed")
search_query = st.sidebar.text_input("Search content or Secret Code...", key="search_query")

if search_query.strip() == SECRET_OWNER_KEY:
    st.session_state.user = "system_owner"
    st.session_state.active_tab = "👑 Owner Control Center"

st.sidebar.markdown("---")
st.sidebar.header("🔐 Portal Access & Auth")

available_modes = ["Login (Phone & Password)", "Register (Global Account)"]
if st.session_state.user == "system_owner":
    available_modes.append("👑 Owner Exclusive Portal")

mode = st.sidebar.radio("Select Mode", available_modes)

if mode == "Login (Phone & Password)":
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
            register_or_get_user(vault_user["username"], login_phone, vault_user["country"])
            st.sidebar.success(f"✅ Welcome, {vault_user['username']}!")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Phone Number or Password!")

elif mode == "Register (Global Account)":
    reg_user = st.sidebar.text_input("Username")
    reg_phone = st.sidebar.text_input("Mobile Number (with Country Code)")
    reg_gmail = st.sidebar.text_input("Gmail Address")
    reg_country = st.sidebar.selectbox("Select Country", ALLOWED_COUNTRIES)
    reg_pass = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Register & Sync"):
        if reg_country == "Israel":
            st.sidebar.error("❌ Service Unavailable in this region.")
        elif reg_user and reg_phone and reg_pass and reg_gmail:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Specific validation checks
            cursor.execute("SELECT username FROM global_sovereign_vault WHERE username = ?", (reg_user,))
            if cursor.fetchone():
                st.sidebar.error("❌ Username already taken! Choose a different username.")
                conn.close()
            else:
                cursor.execute("SELECT phone_number FROM global_sovereign_vault WHERE phone_number = ?", (reg_phone,))
                if cursor.fetchone():
                    st.sidebar.error("❌ Phone number already registered! Please Login.")
                    conn.close()
                else:
                    cursor.execute("SELECT gmail_address FROM global_sovereign_vault WHERE gmail_address = ?", (reg_gmail,))
                    if cursor.fetchone():
                        st.sidebar.error("❌ Gmail already registered! Please Login.")
                        conn.close()
                    else:
                        try:
                            hashed_pass = hashlib.sha256(reg_pass.encode()).hexdigest()
                            cursor.execute("""
                                INSERT INTO global_sovereign_vault 
                                (vault_id, username, phone_number, gmail_address, country, hashed_password, created_at) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (f"vault_{uuid.uuid4().hex[:8]}", reg_user, reg_phone, reg_gmail, reg_country, hashed_pass, datetime.now().strftime("%Y-%m-%d")))
                            
                            cursor.execute("""
                                INSERT OR REPLACE INTO users (username, phone_number, full_name, country, is_verified, created_at)
                                VALUES (?, ?, ?, ?, 0, ?)
                            """, (reg_user, reg_phone, reg_user, reg_country, datetime.now().strftime("%Y-%m-%d")))
                            
                            conn.commit()
                            st.sidebar.success("🎉 Registration successful! Switch to Login Mode.")
                        except Exception as e:
                            st.sidebar.error(f"Error: {e}")
                        finally:
                            conn.close()
        else:
            st.sidebar.warning("Please fill in all required fields.")

if st.session_state.user:
    st.sidebar.markdown(f"Active User: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.active_tab = "🌍 World Feed"
        st.rerun()

# Navigation Tabs
nav_tabs = ["🌍 World Feed (FB Style)", "📱 TikTok Shorts Feed", "📺 YouTube Long Feed", "💳 Monetization & Earnings", "👤 My Profile & Channel", "📤 Upload Studio"]
if st.session_state.user == "system_owner":
    nav_tabs.append("👑 Owner Control Center")

current_index = nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0
tab = st.sidebar.radio("Navigation", nav_tabs, index=current_index)
st.session_state.active_tab = tab

# ==========================================
# 7. MAIN APPLICATION FEEDS
# ==========================================

# --- Facebook Style Feed ---
if tab == "🌍 World Feed (FB Style)":
    st.markdown("### 🌍 Global Post Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not posts:
        st.info("No posts available in the global feed.")

    for item in posts:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item.get("uploader_name", "User"), subtitle=f"Posted {item.get('created_at')}")
        if item.get("title"):
            st.markdown(f"#### {item['title']}")
        st.write(item["content"])
        if item.get("tags"):
            st.caption(f"Tags: {item['tags']}")
        if item.get("image_url") and os.path.exists(item["image_url"]):
            st.image(item["image_url"], use_container_width=True)
            
        c1, c2 = st.columns(2)
        if c1.button(f"👍 Like ({item['likes']})", key=f"like_{item['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (item['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if st.session_state.user == "system_owner":
            if c2.button(f"🗑️ Delete", key=f"del_{item['id']}"):
                c = get_db_connection()
                c.cursor().execute("DELETE FROM posts WHERE id = ?", (item['id'],))
                c.commit()
                c.close()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- TikTok Shorts Feed ---
elif tab == "📱 TikTok Shorts Feed":
    st.markdown("### 📱 Global Shorts Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    vids = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid.get("uploader_name", "User"), subtitle=f"Uploaded {vid.get('created_at')}")
        st.markdown(f"**{vid.get('title', '')}**")
        st.caption(vid.get('description', ''))
        
        views_display = vid.get('views', 0) + 125000 
        likes_display = vid.get('likes', 0) + 48000
        
        st.write(f"👁️ **{views_display:,} Views** | ❤️ **{likes_display:,} Likes**")
        if vid.get("video_url") and os.path.exists(vid["video_url"]):
            st.video(vid["video_url"])
        st.markdown('</div>', unsafe_allow_html=True)

# --- YouTube Long Feed ---
elif tab == "📺 YouTube Long Feed":
    st.markdown("### 📺 Long Videos Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'long' ORDER BY created_at DESC")
    vids = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid.get("uploader_name", "User"), subtitle=f"Uploaded {vid.get('created_at')}")
        st.subheader(vid.get('title', ''))
        st.write(vid.get('description', ''))
        
        views_display = vid.get('views', 0) + 250000 
        st.write(f"👁️ **{views_display:,} Views**")
        
        if vid.get("video_url") and os.path.exists(vid["video_url"]):
            st.video(vid["video_url"])
        st.markdown('</div>', unsafe_allow_html=True)

# --- Upload Studio (With AI Shield) ---
elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Creator Upload Studio")
    if not st.session_state.user:
        st.warning("Please log in to upload content.")
    else:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT is_banned, ban_until FROM users WHERE username = ?", (st.session_state.user,))
        u_info = c.fetchone()
        conn.close()

        if u_info and u_info["is_banned"]:
            st.error(f"❌ Your account is suspended until {u_info['ban_until']}. You cannot upload media.")
        else:
            upload_type = st.selectbox("Select Content Category", ["Facebook Post (Image/Text)", "TikTok Short Reel", "YouTube Long Video (20-25 Mins)"])
            title_in = st.text_input("Title")
            desc_in = st.text_area("Description")
            tags_in = st.text_input("Tags")

            if upload_type == "Facebook Post (Image/Text)":
                file_up = st.file_uploader("Select Image", type=["jpg", "jpeg", "png"])
                if st.button("Publish Post"):
                    allowed, msg = check_upload_limit(st.session_state.user, "post")
                    if not allowed:
                        st.error(msg)
                    else:
                        is_safe, ai_msg = ai_content_shield(title_in, desc_in, tags_in, file_up.name if file_up else "")
                        if not is_safe:
                            pen_msg = apply_user_penalty(st.session_state.user)
                            st.error(f"{ai_msg}\n\n{pen_msg}")
                        else:
                            f_id = str(uuid.uuid4())
                            save_path = ""
                            if file_up:
                                save_path = os.path.join(IMAGE_DIR, f"{f_id}.jpg")
                                with open(save_path, "wb") as f:
                                    f.write(file_up.getbuffer())
                            
                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute("INSERT INTO posts (id, uploader_name, content, title, tags, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                      (f_id, st.session_state.user, desc_in, title_in, tags_in, save_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                            conn.commit()
                            conn.close()

                            record_upload(st.session_state.user, "post")
                            sync_to_16_tables(f_id, st.session_state.user, title_in, save_path, "tb_03_image_posts")
                            st.success("✅ Post published successfully!")
                            st.rerun()

            elif upload_type in ["TikTok Short Reel", "YouTube Long Video (20-25 Mins)"]:
                v_type = "short" if upload_type == "TikTok Short Reel" else "long"
                vid_up = st.file_uploader("Select Video File (Original Recorded Video)", type=["mp4", "mov", "avi"])
                
                if st.button("Publish Video"):
                    allowed, msg = check_upload_limit(st.session_state.user, v_type)
                    if not allowed:
                        st.error(msg)
                    else:
                        is_safe, ai_msg = ai_content_shield(title_in, desc_in, tags_in, vid_up.name if vid_up else "")
                        if not is_safe:
                            pen_msg = apply_user_penalty(st.session_state.user)
                            st.error(f"{ai_msg}\n\n{pen_msg}")
                        else:
                            v_id = str(uuid.uuid4())
                            save_path = os.path.join(VIDEO_DIR, f"{v_id}.mp4")
                            with open(save_path, "wb") as f:
                                f.write(vid_up.getbuffer())

                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute("INSERT INTO videos (id, uploader_name, video_type, title, description, tags, video_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                      (v_id, st.session_state.user, v_type, title_in, desc_in, tags_in, save_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                            conn.commit()
                            conn.close()

                            record_upload(st.session_state.user, v_type)
                            target_tb = "tb_05_short_videos" if v_type == "short" else "tb_04_long_videos"
                            sync_to_16_tables(v_id, st.session_state.user, title_in, save_path, target_tb)
                            st.success("✅ Video uploaded and synced across 16 master tables successfully!")
                            st.rerun()

# --- Monetization ---
elif tab == "💳 Monetization & Earnings":
    st.markdown("### 💳 Monetization & Earnings Hub")
    st.markdown("""
        **Creator Monetization Requirements:**
        * 🕒 300 Hours Watch Time
        * 👥 300 Global Followers
        * 👁️ 100,000 Views (For Shorts Media)
    """)
    if st.session_state.user:
        u_data = register_or_get_user(st.session_state.user)
        st.write(f"Monetization Status: **{u_data.get('monetization_status', 'Pending')}**")
        st.metric("Total Revenue", f"${u_data.get('earnings', 0.0):.2f}")

# --- Owner Control Center ---
elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Master Control Center")
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
    col1.metric("Total Registered Users", total_users)
    col2.metric("Total Global Posts", total_posts)
    col3.metric("Total Videos Published", total_vids)

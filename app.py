import base64
from datetime import datetime, timedelta
import os
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

def auto_repair_table_columns():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    u_cols = [col[1] for col in cursor.fetchall()]
    
    fields_to_add = {
        'phone_number': 'TEXT',
        'country': "TEXT DEFAULT 'Bangladesh'",
        'dob_day': 'TEXT',
        'dob_month': 'TEXT',
        'dob_year': 'TEXT',
        'gender': 'TEXT',
        'profile_pic': 'TEXT'
    }
    
    for col_name, col_type in fields_to_add.items():
        if col_name not in u_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()

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
            username TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            full_name TEXT,
            country TEXT DEFAULT 'Bangladesh',
            dob_day TEXT,
            dob_month TEXT,
            dob_year TEXT,
            gender TEXT,
            profile_pic TEXT,
            is_verified INTEGER DEFAULT 1,
            followers_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'approved',
            earnings REAL DEFAULT 0.0,
            is_banned INTEGER DEFAULT 0,
            ban_until TEXT,
            violations_count INTEGER DEFAULT 0,
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

    conn.commit()
    conn.close()

    auto_repair_table_columns()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone_number = '01722003172'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT OR IGNORE INTO users (username, phone_number, full_name, country, is_verified, created_at)
            VALUES ('system_owner', '01722003172', 'System Owner', 'Global HQ', 1, ?)
        """, (datetime.now().strftime("%Y-%m-%d"),))

    conn.commit()
    conn.close()

init_all_tables()

# ==========================================
# 3. AI GUARD & HELPER FUNCTIONS
# ==========================================
BANNED_WORDS = ["sex", "adult", "18+", "porn", "nude", "tiktok", "youtube", "facebook", "reels", "shorts", "stolen", "watermark"]

ALLOWED_COUNTRIES = [
    "Bangladesh", "United States", "United Kingdom", "Canada", "Australia", "Saudi Arabia", 
    "United Arab Emirates", "Qatar", "Kuwait", "Oman", "Bahrain", "Malaysia", "Indonesia", 
    "Pakistan", "Turkey", "Germany", "France", "Italy", "Japan", "South Korea", "China", 
    "Brazil", "South Africa", "Nigeria", "Egypt", "Singapore", "Others (Global)"
]

MONTHS_LIST = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def ai_content_shield(title, description, tags, file_name):
    full_text = f"{title} {description} {tags} {file_name}".lower()
    for word in BANNED_WORDS:
        if word in full_text:
            return False, "⚠️ Blocked by AI Security Protocol! Inappropriate content is prohibited."
    return True, "OK"

def check_upload_limit(username, upload_type):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM daily_upload_limits WHERE username = ? AND upload_type = ? AND upload_date = ?", 
              (username, upload_type, today))
    res = c.fetchone()["count"]
    conn.close()

    if upload_type == "post" and res >= 10:
        return False, "⚠️ Daily limit reached! Maximum 10 posts per day."
    elif upload_type == "short" and res >= 5:
        return False, "⚠️ Daily limit reached! Maximum 5 Short videos per day."
    elif upload_type == "long" and res >= 5:
        return False, "⚠️ Daily limit reached! Maximum 5 Long videos per day."
    
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
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"INSERT OR REPLACE INTO {target_table} (id, username, content_title, media_path, created_at) VALUES (?, ?, ?, ?, ?)",
              (content_id, username, title, path, datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.execute("INSERT OR REPLACE INTO tb_16_global_central_pipeline (id, username, content_title, media_path, created_at) VALUES (?, ?, ?, ?, ?)",
              (content_id, username, title, path, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

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

def show_verified_profile(display_name, subtitle="Member"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_verified, country, profile_pic FROM users WHERE LOWER(username) = LOWER(?)", (display_name.strip(),))
    u_data = c.fetchone()
    conn.close()
    
    is_verified = u_data["is_verified"] if u_data else True
    user_country = u_data["country"] if u_data and u_data["country"] else "Global"
    profile_pic = u_data["profile_pic"] if u_data and u_data["profile_pic"] else None
    
    b64_img = get_image_base64(profile_pic)
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">' if b64_img else '<div style="width:45px; height:45px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:20px;">👤</div>'
    
    # Clean SVG verified badge
    verified_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px; display: inline-block;"><path fill="#1877F2" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1.2 14.2l-3.5-3.5 1.41-1.41 2.09 2.08 5.68-5.67 1.41 1.41-7.09 7.09z"/></svg>'
    
    tick = verified_svg if is_verified else ''
    
    card_html = f"""<div style="display:flex; align-items:center; gap:12px; background: #18191a; padding: 10px; border-radius: 10px; border: 1px solid #2d2f31; margin-bottom: 12px;">{img_html}<div><div style="font-weight:bold; color:#e4e6eb; font-size: 16px; display: flex; align-items: center;">{display_name} {tick}</div><div style="color:#b0b3b8; font-size:12px;">{subtitle} • 🌐 {user_country}</div></div></div>"""
    
    st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# 4. CUSTOM UI STYLING & HEADER
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
            <h1 style="color: #00c853; font-weight: 900; margin-top: 5px;">🛡️ BD AI Book — Global Hub 🛡️</h1>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">🛡️ BD AI Book — Global Hub 🛡️</h1>
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
search_query = st.sidebar.text_input("Search content or Secret Code...", key="search_query")

if search_query.strip() == SECRET_OWNER_KEY:
    st.session_state.user = "system_owner"
    st.session_state.active_tab = "👑 Owner Control Center"

st.sidebar.markdown("---")
st.sidebar.header("📱 Mobile Access")

available_modes = ["📱 Quick Login", "📝 New Registration"]
if st.session_state.user == "system_owner":
    available_modes.append("👑 Owner Exclusive Portal")

mode = st.sidebar.radio("Select Access Mode", available_modes)

# --- LOGIN WITH PHONE NUMBER ONLY ---
if mode == "📱 Quick Login":
    login_phone = st.sidebar.text_input("Mobile Number (মোবাইল নম্বর)")
    if st.sidebar.button("Login"):
        clean_phone = login_phone.strip()
        if clean_phone:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE phone_number = ?", (clean_phone,))
            usr = cursor.fetchone()
            conn.close()
            
            if usr:
                st.session_state.user = usr["username"]
                st.sidebar.success(f"✅ Welcome back, {usr['full_name']}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Phone number not registered. Please Register first!")
        else:
            st.sidebar.warning("⚠️ Please enter your mobile number.")

# --- NEW REGISTRATION FORM ---
elif mode == "📝 New Registration":
    reg_name = st.sidebar.text_input("Full Name / English Name (নাম)")
    reg_phone = st.sidebar.text_input("Mobile Number (মোবাইল নম্বর)")
    reg_country = st.sidebar.selectbox("Current Country (বর্তমান দেশ)", ALLOWED_COUNTRIES)
    
    st.sidebar.markdown("**Date of Birth (জন্ম তারিখ):**")
    col_d, col_m, col_y = st.sidebar.columns(3)
    dob_day = col_d.selectbox("Day", [str(i) for i in range(1, 32)])
    dob_month = col_m.selectbox("Month", MONTHS_LIST)
    dob_year = col_y.selectbox("Year", [str(i) for i in range(1950, 2027)][::-1])
    
    reg_gender = st.sidebar.radio("Gender (লিঙ্গ)", ["Male (ছেলে)", "Female (মেয়ে)", "Other (অন্যান্য)"])

    if st.sidebar.button("Register & Login"):
        clean_phone = reg_phone.strip()
        clean_name = reg_name.strip()
        
        if clean_name and clean_phone:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE phone_number = ?", (clean_phone,))
            if cursor.fetchone():
                st.sidebar.error("❌ Phone number is already registered! Please Login.")
                conn.close()
            else:
                try:
                    cursor.execute("""
                        INSERT INTO users (username, phone_number, full_name, country, dob_day, dob_month, dob_year, gender, is_verified, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """, (clean_name, clean_phone, clean_name, reg_country, dob_day, dob_month, dob_year, reg_gender, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    conn.close()
                    
                    st.session_state.user = clean_name
                    st.sidebar.success("🎉 Account created successfully!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")
                    conn.close()
        else:
            st.sidebar.warning("⚠️ Please provide Name and Mobile Number.")

if st.session_state.user:
    st.sidebar.markdown(f"Logged in as: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.active_tab = "🌍 World Feed"
        st.rerun()

# Navigation Tabs
nav_tabs = ["🌍 World Feed (FB Style)", "📱 TikTok Shorts Feed", "📺 YouTube Long Feed", "👤 My Profile & Channel", "💳 Monetization & Earnings", "📤 Upload Studio"]
if st.session_state.user == "system_owner":
    nav_tabs.append("👑 Owner Control Center")

current_index = nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0
tab = st.sidebar.radio("Navigation", nav_tabs, index=current_index)
st.session_state.active_tab = tab

# ==========================================
# 6. MAIN APPLICATION FEEDS & PROFILE
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

        # Delete Option for Content Owner or System Owner
        if st.session_state.user in [item.get("uploader_name"), "system_owner"]:
            if c2.button("🗑️ Delete Post", key=f"del_{item['id']}"):
                c = get_db_connection()
                c.cursor().execute("DELETE FROM posts WHERE id = ?", (item['id'],))
                c.commit()
                c.close()
                st.success("Post deleted!")
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

    if not vids:
        st.info("No short videos available.")

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid.get("uploader_name", "User"), subtitle=f"Uploaded {vid.get('created_at')}")
        st.markdown(f"**{vid.get('title', '')}**")
        st.caption(vid.get('description', ''))
        
        st.write(f"👁️ **{vid.get('views', 0):,} Views** | ❤️ **{vid.get('likes', 0):,} Likes**")
        if vid.get("video_url") and os.path.exists(vid["video_url"]):
            st.video(vid["video_url"])

        # Delete option
        if st.session_state.user in [vid.get("uploader_name"), "system_owner"]:
            if st.button("🗑️ Delete Video", key=f"del_v_{vid['id']}"):
                c = get_db_connection()
                c.cursor().execute("DELETE FROM videos WHERE id = ?", (vid['id'],))
                c.commit()
                c.close()
                st.success("Video deleted!")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# --- YouTube Long Feed ---
elif tab == "📺 YouTube Long Feed":
    st.markdown("### 📺 Long Videos Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'long' ORDER BY created_at DESC")
    vids = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not vids:
        st.info("No long videos available.")

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid.get("uploader_name", "User"), subtitle=f"Uploaded {vid.get('created_at')}")
        st.subheader(vid.get('title', ''))
        st.write(vid.get('description', ''))
        
        st.write(f"👁️ **{vid.get('views', 0):,} Views**")
        if vid.get("video_url") and os.path.exists(vid["video_url"]):
            st.video(vid["video_url"])

        # Delete option
        if st.session_state.user in [vid.get("uploader_name"), "system_owner"]:
            if st.button("🗑️ Delete Long Video", key=f"del_lv_{vid['id']}"):
                c = get_db_connection()
                c.cursor().execute("DELETE FROM videos WHERE id = ?", (vid['id'],))
                c.commit()
                c.close()
                st.success("Video deleted!")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# --- MY PROFILE & CHANNEL ---
elif tab == "👤 My Profile & Channel":
    st.markdown("### 👤 My Profile & Settings")
    if not st.session_state.user:
        st.warning("Please login to view and edit your profile.")
    else:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
        u_info = c.fetchone()
        conn.close()

        if u_info:
            u_info = dict(u_info)
            show_verified_profile(u_info["username"], subtitle="Personal Account")

            st.markdown("---")
            st.subheader("⚙️ Update Profile Details")

            # 1. Profile Picture Upload
            st.markdown("**Upload Profile Picture (প্রোফাইল পিকচার সেট করুন)**")
            pic_up = st.file_uploader("Choose Profile Image", type=["jpg", "jpeg", "png"])
            if pic_up and st.button("Save Profile Picture"):
                save_pic_path = os.path.join(PROFILE_DIR, f"{st.session_state.user}_profile.jpg")
                with open(save_pic_path, "wb") as f:
                    f.write(pic_up.getbuffer())
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE users SET profile_pic = ? WHERE username = ?", (save_pic_path, st.session_state.user))
                conn.commit()
                conn.close()
                st.success("✅ Profile Picture updated successfully!")
                st.rerun()

            # 2. Update Full Name / Display Name
            st.markdown("---")
            st.markdown("**Edit Name (নাম পরিবর্তন করুন)**")
            new_name = st.text_input("Enter New Name / English Name", value=u_info.get("full_name", u_info["username"]))
            if st.button("Update Name"):
                if new_name.strip():
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE users SET full_name = ?, username = ? WHERE username = ?", (new_name.strip(), new_name.strip(), st.session_state.user))
                    conn.commit()
                    conn.close()
                    st.session_state.user = new_name.strip()
                    st.success("✅ Name updated successfully!")
                    st.rerun()

            # 3. View Verified Badge Status
            st.markdown("---")
            st.markdown(f"**Verification Status:** {'✔️ Verified (ব্লুটিক প্রাপ্ত)' if u_info.get('is_verified') else '❌ Not Verified'}")

# --- Upload Studio ---
elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Creator Upload Studio")
    if not st.session_state.user:
        st.warning("Please enter your Mobile Number on the sidebar to login and upload content.")
    else:
        upload_type = st.selectbox("Select Content Category", ["Facebook Post (Image/Text)", "TikTok Short Reel", "YouTube Long Video"])
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
                        st.error(ai_msg)
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

        elif upload_type in ["TikTok Short Reel", "YouTube Long Video"]:
            v_type = "short" if upload_type == "TikTok Short Reel" else "long"
            vid_up = st.file_uploader("Select Video File", type=["mp4", "mov", "avi"])
            
            if st.button("Publish Video"):
                if not vid_up:
                    st.warning("Please upload a video file.")
                else:
                    allowed, msg = check_upload_limit(st.session_state.user, v_type)
                    if not allowed:
                        st.error(msg)
                    else:
                        is_safe, ai_msg = ai_content_shield(title_in, desc_in, tags_in, vid_up.name)
                        if not is_safe:
                            st.error(ai_msg)
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
                            st.success("✅ Video uploaded successfully!")
                            st.rerun()

# --- Monetization ---
elif tab == "💳 Monetization & Earnings":
    st.markdown("### 💳 Monetization & Earnings Hub")
    if st.session_state.user:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT earnings FROM users WHERE username = ?", (st.session_state.user,))
        row = c.fetchone()
        conn.close()
        earn = row["earnings"] if row else 0.0
        st.metric("Total Revenue", f"${earn:.2f}")

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

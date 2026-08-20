import base64
from datetime import datetime
import os
import random
import sqlite3
import uuid

import pycountry
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Enterprise Master Platform",
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
# ডাইরেক্ট লিঙ্ক বক্স (ফাঁকা রাখা হয়েছে)
# ==========================================
DIRECT_AD_LINKS = [
    "",  # এখানে আপনার ডাইরেক্ট লিঙ্ক-১ বসাবেন
    "",  # এখানে আপনার ডাইরেক্ট লিঙ্ক-২ বসাবেন
    ""   # এখানে আপনার ডাইরেক্ট লিঙ্ক-৩ বসাবেন
]

def get_random_ad_link():
    """উপলব্ধ লিঙ্ক থেকে র্যান্ডমলি একটি এড লিঙ্ক বেছে নেবে"""
    valid_links = [link for link in DIRECT_AD_LINKS if link.strip()]
    if valid_links:
        return random.choice(valid_links)
    return "#"

def render_ad_button():
    """প্রতিটি পোস্ট/ভিডিওর নিচে স্পন্সরড বাটন রেন্ডার করার ফাংশন"""
    ad_url = get_random_ad_link()
    if ad_url == "#":
        return ""
    return f"""
        <div style="text-align: center; margin: 12px 0;">
            <a href="{ad_url}" target="_blank" style="background: linear-gradient(45deg, #00c853, #00e676); color: #000; padding: 10px 22px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; display: inline-block; box-shadow: 0px 4px 10px rgba(0, 200, 83, 0.3);">
                👉 Click Here / Watch Sponsored Content 🌐
            </a>
        </div>
    """

# ==========================================
# 2. LOCAL STORAGE & DATABASE SETUP
# ==========================================
DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
SETTINGS_DIR = "stored_settings"

for folder in [VIDEO_DIR, IMAGE_DIR, SETTINGS_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_clean_database():
    conn = get_db_connection()
    cursor = conn.cursor()

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
            profile_pic_base64 TEXT,
            is_verified INTEGER DEFAULT 1,
            followers_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            shares_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'approved',
            earnings REAL DEFAULT 0.0,
            is_banned INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if "profile_pic_base64" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic_base64 TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            content TEXT,
            title TEXT,
            tags TEXT,
            image_url TEXT,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            video_url TEXT,
            uploader_name TEXT,
            video_type TEXT DEFAULT 'long',
            title TEXT,
            description TEXT,
            tags TEXT,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS owner_updates (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            media_type TEXT,
            media_url TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()

init_clean_database()

# ==========================================
# 3. HELPER & ALGORITHM FUNCTIONS
# ==========================================
BANNED_WORDS = ["sex", "adult", "18+", "porn", "nude", "stolen"]

# সারা বিশ্বের সব দেশের নাম অটোমেটিক জেনারেট করার লজিক
ALLOWED_COUNTRIES = sorted([country.name for country in pycountry.countries])

MONTHS_LIST = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def generate_initial_boost_views():
    return random.randint(10000, 20000)

def ai_content_shield(title, description, tags, file_name):
    full_text = f"{title} {description} {tags} {file_name}".lower()
    for word in BANNED_WORDS:
        if word in full_text:
            return False, "⚠️ Blocked by AI Security Shield!"
    return True, "OK"

def show_verified_profile(display_name, subtitle="Member"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_verified, country, profile_pic_base64 FROM users WHERE LOWER(username) = LOWER(?)", (str(display_name).strip(),))
    u_data = c.fetchone()
    conn.close()
    
    is_verified = u_data["is_verified"] if u_data else True
    user_country = u_data["country"] if u_data and u_data["country"] else "Global HQ"
    b64_img = u_data["profile_pic_base64"] if (u_data and "profile_pic_base64" in u_data.keys() and u_data["profile_pic_base64"]) else None
    
    if b64_img:
        img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">'
    else:
        img_html = '<div style="width:45px; height:45px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:20px;">👤</div>'
    
    verified_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px; display: inline-block;"><path fill="#1877F2" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1.2 14.2l-3.5-3.5 1.41-1.41 2.09 2.08 5.68-5.67 1.41 1.41-7.09 7.09z"/></svg>'
    tick = verified_svg if is_verified else ''
    
    card_html = f"""<div style="display:flex; align-items:center; gap:12px; background: #18191a; padding: 10px; border-radius: 10px; border: 1px solid #2d2f31; margin-bottom: 12px;">{img_html}<div><div style="font-weight:bold; color:#e4e6eb; font-size: 16px; display: flex; align-items: center;">{display_name} {tick}</div><div style="color:#b0b3b8; font-size:12px;">{subtitle} • 🌐 {user_country}</div></div></div>"""
    st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# 4. CUSTOM UI STYLING & HEADER WITH OWNER MEDIA
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT profile_pic_base64 FROM users WHERE LOWER(username) = 'system_owner'")
owner_data = c.fetchone()

c.execute("SELECT value FROM app_settings WHERE key = 'header_bg_music'")
music_data = c.fetchone()
conn.close()

owner_pic_b64 = owner_data["profile_pic_base64"] if (owner_data and owner_data["profile_pic_base64"]) else None

header_img_html = ""
if owner_pic_b64:
    header_img_html = f'<img src="data:image/jpeg;base64,{owner_pic_b64}" style="width:80px; height:80px; border-radius:50%; object-fit:cover; border:3px solid #00c853; margin-bottom:10px;">'
else:
    header_img_html = '<div style="width:80px; height:80px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:35px; margin: 0 auto 10px auto;">🛡️</div>'

st.markdown(f"""
    <div style="text-align: center; padding: 10px 0;">
        {header_img_html}
        <h1 style="color: #00c853; font-weight: 900; margin: 0;">🛡️ BD AI Book — Global Hub 🛡️</h1>
    </div>
""", unsafe_allow_html=True)

if music_data and os.path.exists(music_data["value"]):
    st.audio(music_data["value"], format="audio/mp3", loop=True)

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

if mode == "📱 Quick Login":
    login_phone = st.sidebar.text_input("Mobile Number (with Country Code e.g. +1..., +880...)")
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

elif mode == "📝 New Registration":
    reg_name = st.sidebar.text_input("Full Name / Display Name")
    reg_phone = st.sidebar.text_input("Mobile Number (Include Country Code e.g. +1..., +44...)")
    reg_country = st.sidebar.selectbox("Country", ALLOWED_COUNTRIES)
    
    col_d, col_m, col_y = st.sidebar.columns(3)
    dob_day = col_d.selectbox("Day", [str(i) for i in range(1, 32)])
    dob_month = col_m.selectbox("Month", MONTHS_LIST)
    dob_year = col_y.selectbox("Year", [str(i) for i in range(1950, 2027)][::-1])
    reg_gender = st.sidebar.radio("Gender", ["Male", "Female", "Other"])

    if st.sidebar.button("Register Account"):
        clean_phone = reg_phone.strip()
        clean_name = reg_name.strip()
        if clean_name and clean_phone:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE phone_number = ?", (clean_phone,))
            if cursor.fetchone():
                st.sidebar.error("❌ Phone number is already registered!")
                conn.close()
            else:
                cursor.execute("""
                    INSERT INTO users (username, phone_number, full_name, country, dob_day, dob_month, dob_year, gender, is_verified, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (clean_name, clean_phone, clean_name, reg_country, dob_day, dob_month, dob_year, reg_gender, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.session_state.user = clean_name
                st.sidebar.success("🎉 Account created successfully!")
                st.rerun()

if st.session_state.user:
    st.sidebar.markdown(f"Logged in as: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.active_tab = "🌍 World Feed"
        st.rerun()

# Navigation Tabs
nav_tabs = ["🌍 World Feed", "📱 TikTok Shorts Feed", "📺 Direct Long Videos", "👤 My Profile & Channel", "💳 Monetization", "📤 Upload Studio"]
if st.session_state.user == "system_owner":
    nav_tabs.append("👑 Owner Control Center")

current_index = nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0
tab = st.sidebar.radio("Navigation", nav_tabs, index=current_index)
st.session_state.active_tab = tab

# ==========================================
# 6. FEEDS & CONTROLS
# ==========================================

# --- World Feed ---
if tab == "🌍 World Feed":
    st.markdown("### 🌍 World Feed")
    conn = get_db_connection()
    c = conn.cursor()
    
    if search_query.strip() and search_query.strip() != SECRET_OWNER_KEY:
        c.execute("SELECT * FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC", 
                  (f"%{search_query}%", f"%{search_query}%"))
    else:
        c.execute("SELECT * FROM posts ORDER BY created_at DESC")
        
    posts = [dict(r) for r in c.fetchall()]
    conn.close()

    if not posts:
        st.info("No posts published yet.")

    for item in posts:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item.get("uploader_name", "User"), subtitle=f"Posted {item.get('created_at')}")
        
        if item.get("title"):
            st.markdown(f"#### {item['title']}")
        st.write(item.get("content", ""))
        
        if item.get("image_url") and os.path.exists(item["image_url"]):
            st.image(item["image_url"], use_container_width=True)
            
        ad_html = render_ad_button()
        if ad_html:
            st.markdown(ad_html, unsafe_allow_html=True)
            
        c1, c2, c3, c4 = st.columns(4)
        if c1.button(f"👍 ({item.get('likes', 0)})", key=f"like_p_{item['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (item['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if c2.button(f"💬 ({item.get('comments', 0)})", key=f"comm_p_{item['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE posts SET comments = comments + 1 WHERE id = ?", (item['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if c3.button(f"🔄 ({item.get('shares', 0)})", key=f"share_p_{item['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE posts SET shares = shares + 1 WHERE id = ?", (item['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if st.session_state.user in [item.get("uploader_name"), "system_owner"]:
            if c4.button("🗑️ Delete", key=f"del_p_{item['id']}"):
                c = get_db_connection()
                c.cursor().execute("DELETE FROM posts WHERE id = ?", (item['id'],))
                c.commit()
                c.close()
                st.success("Post deleted!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Video Feeds ---
elif tab in ["📱 TikTok Shorts Feed", "📺 Direct Long Videos"]:
    video_type_filter = "short" if tab == "📱 TikTok Shorts Feed" else "long"
    st.markdown(f"### {'📱 TikTok Shorts Feed' if video_type_filter == 'short' else '📺 Direct Long Videos'}")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM videos WHERE video_type = ? ORDER BY created_at DESC", (video_type_filter,))
    vids = [dict(r) for r in c.fetchall()]
    conn.close()

    if not vids:
        st.info("No videos uploaded in this category yet.")

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid.get("uploader_name", "User"), subtitle=f"Uploaded {vid.get('created_at')}")
        st.subheader(vid.get('title', ''))
        st.write(vid.get('description', ''))
        
        if vid.get("video_url") and os.path.exists(vid["video_url"]):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET views = views + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.video(vid["video_url"])

        ad_html = render_ad_button()
        if ad_html:
            st.markdown(ad_html, unsafe_allow_html=True)

        c_views, c_like, c_comm, c_share, c_del = st.columns(5)
        c_views.markdown(f"👁️ **{vid.get('views', 0):,}** Views")

        if c_like.button(f"❤️ ({vid.get('likes', 0)})", key=f"like_v_{vid['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if c_comm.button(f"💬 ({vid.get('comments', 0)})", key=f"comm_v_{vid['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET comments = comments + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if c_share.button(f"🔄 ({vid.get('shares', 0)})", key=f"share_v_{vid['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET shares = shares + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if st.session_state.user in [vid.get("uploader_name"), "system_owner"]:
            if c_del.button("🗑️", key=f"del_v_{vid['id']}"):
                c = get_db_connection()
                c.cursor().execute("DELETE FROM videos WHERE id = ?", (vid['id'],))
                c.commit()
                c.close()
                st.success("Video deleted!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Account Profile ---
elif tab == "👤 My Profile & Channel":
    st.markdown("### 👤 Account Profile")
    if not st.session_state.user:
        st.warning("Please login to manage your profile.")
    else:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
        u_info = c.fetchone()
        conn.close()

        if u_info:
            u_info = dict(u_info)
            show_verified_profile(u_info["username"], subtitle="Profile")
            st.write(f"📱 Phone: {u_info.get('phone_number')}")
            st.write(f"🌐 Country: {u_info.get('country')}")

            pic_up = st.file_uploader("Upload Profile Picture (Global View)", type=["jpg", "jpeg", "png"])
            if pic_up and st.button("Save Profile Picture Globally"):
                base64_image = base64.b64encode(pic_up.read()).decode("utf-8")
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE users SET profile_pic_base64 = ? WHERE username = ?", (base64_image, st.session_state.user))
                conn.commit()
                conn.close()
                st.success("🎉 Profile picture updated globally!")
                st.rerun()

# --- Monetization ---
elif tab == "💳 Monetization":
    st.markdown("### 💳 Monetization Dashboard")
    if not st.session_state.user:
        st.warning("Please login to view your earnings.")
    else:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT earnings, monetization_status FROM users WHERE username = ?", (st.session_state.user,))
        usr_m = c.fetchone()
        conn.close()

        status = usr_m["monetization_status"] if usr_m else "Approved"
        earnings = usr_m["earnings"] if usr_m else 0.0

        st.success(f"Status: **{status.upper()}**")
        st.metric(label="Total Earnings", value=f"${earnings:.2f}")

# --- Upload Studio ---
elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Upload Studio")
    if not st.session_state.user:
        st.warning("Please login from the sidebar first.")
    else:
        cat = st.selectbox("Category", ["Facebook Post", "TikTok Short Video", "Direct Long Video"])
        title_in = st.text_input("Title")
        desc_in = st.text_area("Description")
        tags_in = st.text_input("Tags")

        if cat == "Facebook Post":
            f_up = st.file_uploader("Select Photo", type=["jpg", "jpeg", "png"])
            if st.button("Publish Post"):
                is_safe, msg = ai_content_shield(title_in, desc_in, tags_in, f_up.name if f_up else "")
                if not is_safe:
                    st.error(msg)
                else:
                    p_id = str(uuid.uuid4())
                    save_p = ""
                    if f_up:
                        save_p = os.path.join(IMAGE_DIR, f"{p_id}.jpg")
                        with open(save_p, "wb") as f:
                            f.write(f_up.getbuffer())

                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO posts (id, uploader_name, content, title, tags, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (p_id, str(st.session_state.user), desc_in, title_in, tags_in, save_p, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    st.success("✅ Post uploaded successfully!")
                    st.rerun()

        else:
            v_type = "short" if cat == "TikTok Short Video" else "long"
            v_up = st.file_uploader("Select Video", type=["mp4", "mov", "avi"])
            if st.button("Publish Video"):
                if not v_up:
                    st.warning("Please upload a video file.")
                else:
                    is_safe, msg = ai_content_shield(title_in, desc_in, tags_in, v_up.name)
                    if not is_safe:
                        st.error(msg)
                    else:
                        v_id = str(uuid.uuid4())
                        save_v = os.path.join(VIDEO_DIR, f"{v_id}.mp4")
                        with open(save_v, "wb") as f:
                            f.write(v_up.getbuffer())

                        initial_views = generate_initial_boost_views()

                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO videos (id, user_id, uploader_name, video_type, title, description, tags, video_url, views, created_at) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (v_id, str(st.session_state.user), str(st.session_state.user), v_type, title_in, desc_in, tags_in, save_v, initial_views, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        conn.close()
                        st.success("✅ Video uploaded successfully with algorithm boost!")
                        st.rerun()

# --- Owner Control Center ---
elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Owner Exclusive Panel")
    
    st.subheader("🎵 Header Background Music Setting")
    audio_file = st.file_uploader("Upload Header Audio/Music (MP3/WAV)", type=["mp3", "wav"])
    if st.button("Save Header Music"):
        if audio_file:
            save_path = os.path.join(SETTINGS_DIR, "header_music.mp3")
            with open(save_path, "wb") as f:
                f.write(audio_file.getbuffer())
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('header_bg_music', ?)", (save_path,))
            conn.commit()
            conn.close()
            st.success("🎶 Header background music updated!")
            st.rerun()

    st.divider()

    st.subheader("📢 Publish Owner Picture/Video Update")
    u_title = st.text_input("Update Title")
    u_desc = st.text_area("Update Details")
    media_file = st.file_uploader("Upload Image or Video", type=["jpg", "png", "mp4"])

    if st.button("Publish Owner Update"):
        if u_title and media_file:
            up_id = str(uuid.uuid4())
            m_type = "video" if media_file.name.endswith(".mp4") else "picture"
            save_path = os.path.join(SETTINGS_DIR, f"{up_id}_{media_file.name}")
            with open(save_path, "wb") as f:
                f.write(media_file.getbuffer())

            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO owner_updates (id, title, description, media_type, media_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (up_id, u_title, u_desc, m_type, save_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("✅ Owner Update Published Successfully!")
            st.rerun()

    st.divider()
    st.subheader("📋 All Owner Updates Feed")
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM owner_updates ORDER BY created_at DESC")
    updates = [dict(r) for r in c.fetchall()]
    conn.close()

    for up in updates:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        st.subheader(up["title"])
        st.write(up["description"])
        if up["media_type"] == "picture" and os.path.exists(up["media_url"]):
            st.image(up["media_url"], use_container_width=True)
        elif up["media_type"] == "video" and os.path.exists(up["media_url"]):
            st.video(up["media_url"])
            
        ad_html = render_ad_button()
        if ad_html:
            st.markdown(ad_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

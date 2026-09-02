import os
import sqlite3
import uuid
import hashlib
import random
from datetime import datetime, timedelta
import streamlit as st

# ==========================================
# 1. PAGE SETUP & STORAGE DIRECTORY
# ==========================================
st.set_page_config(
    page_title="BD AI Book",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

UPLOAD_DIR = "uploaded_media"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

LOCAL_DB_FILE = "bd_ai_book_master.db"
SECRET_CODES = ["S$s123456789112233", "S$s123456789112233BDAIBOOK"]
BANNED_KEYWORDS = ["nude", "sex", "adult", "porn", "xrated", "18+"]

# ==========================================
# 2. MASTER DATABASE ENGINE
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(LOCAL_DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_master_database():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS master_app_table (
            record_id TEXT PRIMARY KEY,
            data_type TEXT NOT NULL,
            user_id TEXT,
            full_name TEXT,
            auth_identifier TEXT,
            password_hash TEXT,
            address TEXT,
            bio TEXT,
            profile_pic_path TEXT,
            cover_pic_path TEXT,
            fb_link TEXT,
            tiktok_link TEXT,
            yt_link TEXT,
            website_link TEXT,
            followers_count INTEGER DEFAULT 0,
            is_verified INTEGER DEFAULT 1,
            violation_count INTEGER DEFAULT 0,
            is_suspended INTEGER DEFAULT 0,
            suspended_until TEXT,
            title TEXT,
            content TEXT,
            tags TEXT,
            media_path TEXT,
            post_category TEXT,
            likes_count INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            is_boosted INTEGER DEFAULT 0,
            monetization_status TEXT DEFAULT 'Not Eligible',
            country TEXT DEFAULT 'Global',
            is_owner_post INTEGER DEFAULT 0,
            created_at TEXT
        );
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS boost_requests (
            boost_id TEXT PRIMARY KEY,
            user_id TEXT,
            post_id TEXT,
            plan TEXT,
            amount TEXT,
            trx_info TEXT,
            payment_method TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        );
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS monetization_requests (
            mon_id TEXT PRIMARY KEY,
            user_id TEXT,
            followers_count INTEGER,
            bank_info TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        );
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            follower_id TEXT,
            following_id TEXT,
            PRIMARY KEY (follower_id, following_id)
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            user_id TEXT,
            post_id TEXT,
            category TEXT DEFAULT 'general',
            PRIMARY KEY (user_id, post_id)
        );
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS payment_gateways (
            gateway_id TEXT PRIMARY KEY,
            method_type TEXT,
            provider_name TEXT,
            account_details TEXT,
            is_active INTEGER DEFAULT 1
        );
    """)
    
    default_settings = {
        "app_name": "BD AI Book",
        "owner_announcement": "Welcome to BD AI Book 100% Monetization Income Guaranteed! Next-Gen Social & Media Platform",
        "lock_upload": "OFF",
        "daily_limit_mode": "OFF",
        "lock_login": "OFF",
        "logo_path": "",
        "show_ads": "OFF"
    }
    
    for k, v in default_settings.items():
        c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, v))

    c.execute("SELECT COUNT(*) as cnt FROM payment_gateways")
    if c.fetchone()["cnt"] == 0:
        c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Mobile Banking", "bKash Personal", "01700000000"))
        c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Mobile Banking", "Nagad Personal", "01700000000"))
        
    conn.commit()
    conn.close()

init_master_database()

def get_setting(key, default=""):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM site_settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def hash_pass(pwd): 
    return hashlib.sha256(pwd.encode()).hexdigest()

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

def increment_views(post_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE master_app_table SET views_count = views_count + 1 WHERE record_id = ?", (post_id,))
    conn.commit()
    conn.close()

st.markdown("""
<style>
    img { border-radius: 12px; }
    .stImage > img {
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid #0064e0 !important;
    }
    .announcement-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False

app_name = get_setting("app_name", "BD AI Book")
announcement = get_setting("owner_announcement", "")

st.markdown(f"<h1 style='text-align: center; color:#0064e0;'>{app_name}</h1>", unsafe_allow_html=True)
if announcement:
    st.markdown(f"<div class='announcement-box'>📢 {announcement}</div>", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR AUTHENTICATION
# ==========================================
real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 User Login")
if not st.session_state.user_id:
    auth_input = st.sidebar.text_input("Gmail or Mobile")
    auth_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Send OTP"):
        if auth_input and auth_pass:
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.sidebar.info(f"📩 OTP Code: **{st.session_state.otp_code}**")
            
    if st.session_state.otp_code:
        user_otp = st.sidebar.text_input("Enter OTP Code")
        if st.sidebar.button("Verify & Login"):
            if user_otp == st.session_state.otp_code:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                usr = c.fetchone()
                if usr:
                    st.session_state.user_id = usr["user_id"]
                    conn.close()
                    st.rerun()
                else:
                    new_uid = str(uuid.uuid4())
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("""
                        INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, created_at)
                        VALUES (?, 'user', ?, ?, ?, ?, 1, ?)
                    """, (new_uid, new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), now))
                    conn.commit()
                    conn.close()
                    st.session_state.user_id = new_uid
                    st.rerun()
else:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
    raw_user = c.fetchone()
    
    c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (st.session_state.user_id,))
    f_res = c.fetchone()
    real_followers = f_res["cnt"] if f_res else 0
    conn.close()
    
    current_user = dict(raw_user) if raw_user else {}

    st.sidebar.markdown(f"User: **{current_user.get('full_name', 'User')}**")
    st.sidebar.markdown(f"👥 Real Followers: **{real_followers:,}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.is_owner_session = False
        st.rerun()

# ==========================================
# 5. MAIN NAVIGATION TABS
# ==========================================
tab_feed, tab_profile, tab_monetization = st.tabs(["📺 Public Live Feed", "👤 Profile & Studio", "🌍 Global Monetization & Boost"])

with tab_feed:
    search_input = st.text_input("🔍 Search Users, Videos, Hashtags or Secret Code...", key="main_search_box")
    
    clean_search = search_input.strip()
    if clean_search in SECRET_CODES:
        st.session_state.is_owner_session = True

    # 👑 OWNER PANEL
    if st.session_state.is_owner_session:
        st.success("👑 OWNER COMMAND CENTER UNLOCKED!")
        if st.button("❌ Exit Owner Mode"):
            st.session_state.is_owner_session = False
            st.rerun()
            
        st.markdown("---")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post'")
        all_posts = c.fetchall()
        
        st.markdown("### 🗑️ Delete Posts")
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
        posts_to_mod = c.fetchall()
        for p in posts_to_mod:
            col_p1, col_p2 = st.columns([4, 1])
            col_p1.write(f"📌 **{p['title']}** ({p['full_name']})")
            if col_p2.button("🗑️ Delete", key=f"del_{p['record_id']}"):
                c.execute("DELETE FROM master_app_table WHERE record_id = ?", (p['record_id'],))
                conn.commit()
                conn.close()
                st.rerun()
        conn.close()

    # 📺 PUBLIC FEED (FAST NATIVE PLAYBACK)
    else:
        conn = get_db_connection()
        c = conn.cursor()
        
        if clean_search and clean_search not in SECRET_CODES:
            q_str = f"%{clean_search}%"
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND (title LIKE ? OR content LIKE ? OR full_name LIKE ?) ORDER BY created_at DESC", (q_str, q_str, q_str))
        else:
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
            
        posts = [dict(r) for r in c.fetchall()]
        conn.close()

        for post in posts:
            increment_views(post["record_id"])
            st.markdown("<div style='background:#18191a; padding:15px; border-radius:12px; margin-bottom:15px;'>", unsafe_allow_html=True)
            
            tick = get_meta_blue_badge() if post.get("is_verified") else ""
            st.markdown(f"**{post.get('full_name')}** {tick}", unsafe_allow_html=True)
            st.caption(f"Category: {post.get('post_category')}")

            if post.get("title"): st.subheader(post["title"])
            if post.get("content"): st.write(post["content"])
            
            media_path = post.get("media_path")
            cat = post.get("post_category", "general")
            
            # FAST NATIVE STREAMLIT MEDIA PLAYBACK
            if media_path and os.path.exists(media_path):
                if cat == "picture":
                    st.image(media_path, use_container_width=True)
                else:
                    st.video(media_path)

            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM likes WHERE post_id = ?", (post["record_id"],))
            real_likes = c.fetchone()["cnt"]
            conn.close()

            st.markdown("---")
            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.write(f"👁️ **{(post.get('views_count', 0) + 1):,}** Views")
            
            if col_b2.button(f"👍 Like ({real_likes})", key=f"lk_{post['record_id']}"):
                if st.session_state.user_id:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("INSERT OR IGNORE INTO likes (user_id, post_id, category) VALUES (?, ?, ?)", (st.session_state.user_id, post["record_id"], cat))
                    conn.commit()
                    conn.close()
                    st.rerun()

            if col_b3.button("🚀 Share", key=f"sh_{post['record_id']}"):
                st.toast("Link Copied!")
                
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: PROFILE & UPLOAD
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.warning("Please login to upload!")
    else:
        st.markdown("### 📤 Upload New Content")
        post_type = st.selectbox("Format", ["short", "long", "picture"])
        title = st.text_input("Title")
        desc = st.text_area("Description")
        uploaded_media = st.file_uploader("Media File", type=["mp4", "jpg", "png"])
        
        if st.button("Publish Post"):
            if uploaded_media and title:
                ext = os.path.splitext(uploaded_media.name)[1]
                m_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
                with open(m_path, "wb") as f: f.write(uploaded_media.getbuffer())
                
                rec_id = str(uuid.uuid4())
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, media_path, post_category, views_count, likes_count, created_at)
                    VALUES (?, 'post', ?, ?, 1, ?, ?, ?, ?, 1, 0, ?)
                """, (rec_id, st.session_state.user_id, current_user.get("full_name", "User"), title, desc, m_path, post_type, now))
                conn.commit()
                conn.close()
                st.success("Published Successfully!")
                st.rerun()

# ------------------------------------------
# TAB 3: MONETIZATION
# ------------------------------------------
with tab_monetization:
    st.markdown("### 💸 Monetization Center")
    st.info("Monetization features will process automatically based on views.")

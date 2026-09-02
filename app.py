import os
import sqlite3
import uuid
import hashlib
import random
from datetime import datetime, timedelta
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & DIRECTORIES
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

DATABASE_URL = os.environ.get("DATABASE_URL", None)
LOCAL_DB_FILE = "bd_ai_book_master.db"
SECRET_OWNER_KEY = "S$s123456789112233"

# ==========================================
# 2. MASTER DATABASE ENGINE
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

def init_master_database():
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Unified Single Table Architecture
    query = """
        CREATE TABLE IF NOT EXISTS master_app_table (
            record_id TEXT PRIMARY KEY,
            data_type TEXT NOT NULL, -- 'user', 'post', 'system'
            user_id TEXT,
            full_name TEXT,
            auth_identifier TEXT,
            password_hash TEXT,
            address TEXT,
            bio TEXT,
            is_verified INTEGER DEFAULT 1,
            violation_count INTEGER DEFAULT 0,
            is_suspended INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            suspended_until TEXT,
            title TEXT,
            content TEXT,
            tags TEXT,
            media_path TEXT,
            post_category TEXT,
            likes_count INTEGER DEFAULT 0,
            header_logo_url TEXT,
            created_at TEXT
        );
    """
    c.execute(query)
    conn.commit()
    conn.close()

init_master_database()

# ==========================================
# 3. UTILITY & AI SAFETY FUNCTIONS
# ==========================================
def hash_pass(pwd): 
    return hashlib.sha256(pwd.encode()).hexdigest()

def check_ai_safety(text, filename=""):
    banned_words = ["sex", "porn", "nude", "adult", "18+", "গালাগালি", "খারাপ", "অশ্লীল"]
    combined = (text + " " + filename).lower()
    for word in banned_words:
        if word in combined:
            return False, "NSFW / Policy Violation"
    return True, "Passed"

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

# ==========================================
# 4. SESSION & AUTH
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None

# Header Section
st.markdown("<h1 style='text-align: center; color:#0064e0;'>📖 BD AI Book</h1>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Next-Gen Social Video Platform</p>", unsafe_allow_html=True)

# Sidebar Login/Register Component
st.sidebar.markdown("### 🔐 User Account")
if not st.session_state.user_id:
    auth_input = st.sidebar.text_input("Gmail or Mobile Number")
    auth_pass = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Send 6-Digit OTP"):
        if auth_input and auth_pass:
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.sidebar.info(f"📩 OTP Code: **{st.session_state.otp_code}**")
        else:
            st.sidebar.error("Fill all fields!")
            
    if st.session_state.otp_code:
        user_otp = st.sidebar.text_input("Enter OTP Code")
        if st.sidebar.button("Verify & Login"):
            if user_otp == st.session_state.otp_code:
                conn, db_type = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                usr = c.fetchone()
                
                if usr:
                    if usr["is_banned"]:
                        st.sidebar.error("🚫 Account Banned!")
                    else:
                        st.session_state.user_id = usr["user_id"]
                        st.sidebar.success("Logged In!")
                        st.rerun()
                else:
                    new_uid = str(uuid.uuid4())
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("""
                        INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, created_at)
                        VALUES (?, 'user', ?, ?, ?, ?, 1, ?)
                    """, (new_uid, new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), now))
                    conn.commit()
                    st.session_state.user_id = new_uid
                    st.sidebar.success("Account Created!")
                    st.rerun()
                conn.close()
else:
    conn, db_type = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
    current_user = c.fetchone()
    conn.close()

    st.sidebar.markdown(f"LoggedIn as: **{current_user['full_name']}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.otp_code = None
        st.rerun()

# ==========================================
# 5. MAIN NAVIGATION TABS
# ==========================================
tab_feed, tab_profile, tab_admin = st.tabs(["📺 Public Live Feed", "👤 My Profile & Upload Studio", "👑 Owner Control Center"])

# ------------------------------------------
# TAB 1: PUBLIC FEED (NO LOGIN REQUIRED TO WATCH)
# ------------------------------------------
with tab_feed:
    search_query = st.text_input("🔍 Search Videos by Title, Hashtag (#) or Keyword...")
    
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    if search_query:
        query_str = f"%{search_query}%"
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND (title LIKE ? OR tags LIKE ? OR content LIKE ?) ORDER BY created_at DESC", (query_str, query_str, query_str))
    else:
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
        
    posts = [dict(r) for r in c.fetchall()]
    conn.close()

    if not posts:
        st.info("No videos or posts found.")

    for post in posts:
        st.markdown("<div style='background:#18191a; padding:15px; border-radius:10px; margin-bottom:20px;'>", unsafe_allow_html=True)
        tick = get_meta_blue_badge() if post.get("is_verified") else ""
        st.markdown(f"### {post.get('full_name')} {tick}", unsafe_allow_html=True)
        st.caption(f"Category: {post.get('post_category')} | Time: {post.get('created_at')}")
        
        if post.get("title"): st.subheader(post["title"])
        if post.get("content"): st.write(post["content"])
        if post.get("tags"): st.markdown(f"<span style='color:#0064e0;'>{post['tags']}</span>", unsafe_allow_html=True)
        
        # MEDIA PLAYER
        media_path = post.get("media_path")
        if media_path and os.path.exists(media_path):
            if post.get("post_category") == "picture":
                st.image(media_path, use_container_width=True)
            else:
                st.video(media_path)
                
        # ACTION BUTTONS & SOCIAL SHARING
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        with col1:
            if st.button(f"👍 Like ({post.get('likes_count', 0)})", key=f"lk_{post['record_id']}"):
                if not st.session_state.user_id:
                    st.warning("Please login from sidebar to like!")
                else:
                    # Update Likes Logic
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE master_app_table SET likes_count = likes_count + 1 WHERE record_id = ?", (post['record_id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
                    
        with col2: st.markdown("[Facebook Share](https://facebook.com)")
        with col3: st.markdown("[YouTube](https://youtube.com)")
        with col4: st.markdown("[TikTok](https://tiktok.com)")
        with col5: st.markdown("[Telegram](https://telegram.org)")
        
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: MY PROFILE & UPLOAD (REQUIRES LOGIN)
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.warning("🔐 You must login/register from the left sidebar to upload videos or manage your profile!")
    else:
        tick = get_meta_blue_badge() if current_user["is_verified"] else ""
        st.markdown(f"## Profile Studio: {current_user['full_name']} {tick}", unsafe_allow_html=True)
        
        # PROFILE UPDATE SECTION
        with st.expander("✏️ Update My Address & Info"):
            u_name = st.text_input("Full Name", value=current_user["full_name"])
            u_addr = st.text_input("Address / Location", value=current_user["address"] or "")
            u_bio = st.text_area("Profile Bio", value=current_user["bio"] or "")
            if st.button("Save Profile"):
                conn, db_type = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE master_app_table SET full_name = ?, address = ?, bio = ? WHERE user_id = ?", (u_name, u_addr, u_bio, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("Profile Updated!")
                st.rerun()

        st.markdown("---")
        
        # UPLOAD SECTION
        if current_user["is_suspended"]:
            st.error(f"🚫 Account Suspended until {current_user['suspended_until']} for Terms Violation!")
        else:
            st.markdown("### 📤 Upload Video / Photo to BD AI Book")
            post_type = st.selectbox("Category", ["short", "long", "picture"])
            title = st.text_input("Video Title")
            desc = st.text_area("Description & Keywords")
            tags = st.text_input("Hashtags (e.g. #trending #viral #bdai)")
            
            uploaded_file = st.file_uploader("Select Media File", type=["mp4", "mov", "jpg", "png", "jpeg"])
            
            if st.button("Publish Video"):
                if uploaded_file is not None:
                    file_ext = os.path.splitext(uploaded_file.name)[1]
                    saved_filename = f"{uuid.uuid4()}{file_ext}"
                    full_save_path = os.path.join(UPLOAD_DIR, saved_filename)
                    
                    with open(full_save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    is_safe, reason = check_ai_safety(title + " " + desc, uploaded_file.name)
                    
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    
                    if not is_safe:
                        v_count = current_user["violation_count"] + 1
                        if v_count == 1:
                            suspend_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE master_app_table SET violation_count = 1, is_suspended = 1, suspended_until = ? WHERE user_id = ?", (suspend_until, st.session_state.user_id))
                            st.error(f"🚨 NSFW Detected ({reason})! 30 Days Suspension Applied.")
                        else:
                            c.execute("UPDATE master_app_table SET violation_count = ?, is_banned = 1 WHERE user_id = ?", (v_count, st.session_state.user_id))
                            st.error("🚨 Account Banned Permanently!")
                        conn.commit()
                    else:
                        rec_id = str(uuid.uuid4())
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("""
                            INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, tags, media_path, post_category, created_at)
                            VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (rec_id, st.session_state.user_id, current_user["full_name"], current_user["is_verified"], title, desc, tags, full_save_path, post_type, now))
                        conn.commit()
                        st.success("✅ Published Successfully!")
                    conn.close()
                    st.rerun()

        # MY UPLOADED VIDEOS & DELETE OPTION
        st.markdown("---")
        st.markdown("### 📹 My Uploaded Videos")
        conn, db_type = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND user_id = ? ORDER BY created_at DESC", (st.session_state.user_id,))
        my_posts = [dict(r) for r in c.fetchall()]
        conn.close()
        
        for my_p in my_posts:
            m_col1, m_col2 = st.columns([4, 1])
            with m_col1:
                st.write(f"**{my_p['title']}** ({my_p['post_category']}) - Likes: {my_p['likes_count']}")
            with m_col2:
                if st.button("🗑️ Delete", key=f"del_{my_p['record_id']}"):
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (my_p['record_id'],))
                    conn.commit()
                    conn.close()
                    if os.path.exists(my_p['media_path']):
                        os.remove(my_p['media_path'])
                    st.success("Deleted!")
                    st.rerun()

# ------------------------------------------
# TAB 3: OWNER PANEL (ADMIN CONTROL CENTER)
# ------------------------------------------
with tab_admin:
    st.markdown("### 👑 BD AI Book - Master Owner Panel")
    pass_key = st.text_input("Owner Passkey", type="password")
    if pass_key == SECRET_OWNER_KEY:
        st.success("Authorized Owner Access Granted")
        
        conn, db_type = get_db_connection()
        c = conn.cursor()
        
        # Stats
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'user'")
        u_cnt = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post'")
        p_cnt = c.fetchone()["cnt"]
        
        st.metric("Total Platform Users", u_cnt)
        st.metric("Total Videos Published", p_cnt)
        
        st.markdown("---")
        st.markdown("### 🛠️ Global Content Management (Delete Any Video)")
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
        all_posts = [dict(r) for r in c.fetchall()]
        
        for ap in all_posts:
            a_col1, a_col2 = st.columns([4, 1])
            with a_col1:
                st.write(f"User: **{ap['full_name']}** | Title: {ap['title']}")
            with a_col2:
                if st.button("Admin Delete", key=f"adel_{ap['record_id']}"):
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (ap['record_id'],))
                    conn.commit()
                    st.success("Post removed by Admin!")
                    st.rerun()
                    
        conn.close()

import base64
from datetime import datetime, timedelta
import hashlib
import os
import random
import sqlite3
import uuid

import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & DIRECTORIES
# ==========================================
st.set_page_config(
    page_title="BD Enterprise Social Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Local Storage Directory Setup for Real Files
UPLOAD_DIR = "uploaded_media"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

DATABASE_URL = os.environ.get("DATABASE_URL", None)
LOCAL_DB_FILE = "enterprise_master_single.db"
SECRET_OWNER_KEY = "S$s123456789112233"

# ==========================================
# 2. SINGLE TABLE DATABASE ENGINE
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
    
    # Unified Single Table for Cloud Engine
    query = """
        CREATE TABLE IF NOT EXISTS master_app_table (
            record_id VARCHAR(36) PRIMARY KEY,
            data_type VARCHAR(20) NOT NULL, -- 'user', 'post', 'system'
            user_id VARCHAR(36),
            full_name VARCHAR(100),
            auth_identifier VARCHAR(100), -- Phone or Email
            password_hash TEXT,
            is_verified BOOLEAN DEFAULT TRUE,
            violation_count INT DEFAULT 0,
            is_suspended BOOLEAN DEFAULT FALSE,
            is_banned BOOLEAN DEFAULT FALSE,
            suspended_until TIMESTAMP,
            followers_count INT DEFAULT 0,
            title TEXT,
            content TEXT,
            media_path TEXT,
            post_category VARCHAR(20), -- 'short', 'long', 'picture'
            likes_count INT DEFAULT 0,
            owner_balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """ if db_type == "postgresql" else """
        CREATE TABLE IF NOT EXISTS master_app_table (
            record_id TEXT PRIMARY KEY,
            data_type TEXT NOT NULL,
            user_id TEXT,
            full_name TEXT,
            auth_identifier TEXT,
            password_hash TEXT,
            is_verified INTEGER DEFAULT 1,
            violation_count INTEGER DEFAULT 0,
            is_suspended INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            suspended_until TEXT,
            followers_count INTEGER DEFAULT 0,
            title TEXT,
            content TEXT,
            media_path TEXT,
            post_category TEXT,
            likes_count INTEGER DEFAULT 0,
            owner_balance REAL DEFAULT 0.0,
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
            return False, "NSFW / Adult Content"
    return True, "Passed"

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425 3.25-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

# ==========================================
# 4. SESSION STATE & AUTHENTICATION
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None

st.markdown("<h2 style='text-align: center; color:#00c853;'>🌐 BD Global Media Platform</h2>", unsafe_allow_html=True)

if not st.session_state.user_id:
    st.sidebar.markdown("### 🔐 User Login / Register")
    auth_input = st.sidebar.text_input("Gmail or Mobile Number")
    auth_pass = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Send 6-Digit OTP Code"):
        if auth_input and auth_pass:
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.sidebar.info(f"📩 Your 6-Digit OTP: **{st.session_state.otp_code}**")
        else:
            st.sidebar.error("Enter Credentials!")
            
    if st.session_state.otp_code:
        user_otp = st.sidebar.text_input("Enter 6-Digit Code")
        if st.sidebar.button("Verify & Login"):
            if user_otp == st.session_state.otp_code:
                conn, db_type = get_db_connection()
                c = conn.cursor()
                
                # Check User Existing
                q = "SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = %s" if db_type == "postgresql" else "SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?"
                c.execute(q, (auth_input,))
                usr = c.fetchone()
                
                if usr:
                    if usr["is_banned"]:
                        st.sidebar.error("🚫 Permanent Banned Account!")
                    else:
                        st.session_state.user_id = usr["user_id"]
                        st.sidebar.success("Logged In Successfully!")
                        st.rerun()
                else:
                    new_uid = str(uuid.uuid4())
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    iq = """
                        INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, created_at)
                        VALUES (%s, 'user', %s, %s, %s, %s, TRUE, %s)
                    """ if db_type == "postgresql" else """
                        INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, created_at)
                        VALUES (?, 'user', ?, ?, ?, ?, 1, ?)
                    """
                    c.execute(iq, (new_uid, new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), now))
                    conn.commit()
                    st.session_state.user_id = new_uid
                    st.sidebar.success("Account Created & Logged In!")
                    st.rerun()
                conn.close()

# ==========================================
# 5. MAIN APPLICATION FEED & UPLOADER
# ==========================================
else:
    conn, db_type = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = %s" if db_type == "postgresql" else "SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
    current_user = c.fetchone()
    conn.close()

    # Top Control Bar
    st.sidebar.markdown(f"LoggedIn: **{current_user['full_name']}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.otp_code = None
        st.rerun()

    tab_feed, tab_profile, tab_admin = st.tabs(["📺 Live Feed", "👤 Profile & Upload Studio", "👑 Owner Control"])

    # ------------------------------------------
    # TAB 1: LIVE FEED (FACEBOOK/TIKTOK STYLE)
    # ------------------------------------------
    with tab_feed:
        st.markdown("### 🍿 Real User Live Feed")
        conn, db_type = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
        posts = [dict(r) for r in c.fetchall()]
        conn.close()

        if not posts:
            st.info("No videos/posts published yet. Go to 'Profile & Upload Studio' to test upload!")
            
        for post in posts:
            st.markdown("<div style='background:#1e1e1e; padding:15px; border-radius:10px; margin-bottom:15px;'>", unsafe_allow_html=True)
            tick = get_meta_blue_badge() if post.get("is_verified") else ""
            st.markdown(f"**{post.get('full_name')}** {tick}", unsafe_allow_html=True)
            st.caption(f"Category: {post.get('post_category')} | Uploaded: {post.get('created_at')}")
            
            if post.get("title"): st.subheader(post["title"])
            if post.get("content"): st.write(post["content"])
            
            # REAL FILE MEDIA PLAYER
            media_path = post.get("media_path")
            if media_path and os.path.exists(media_path):
                if post.get("post_category") == "picture":
                    st.image(media_path, use_container_width=True)
                else:
                    st.video(media_path)
                    
            st.markdown("---")
            l_col, c_col = st.columns([1, 5])
            with l_col: st.button(f"👍 Like ({post.get('likes_count', 0)})", key=f"lk_{post['record_id']}")
            st.markdown("</div>", unsafe_allow_html=True)

    # ------------------------------------------
    # TAB 2: PROFILE & REAL VIDEO UPLOAD
    # ------------------------------------------
    with tab_profile:
        tick = get_meta_blue_badge() if current_user["is_verified"] else ""
        st.markdown(f"## Profile: {current_user['full_name']} {tick}", unsafe_allow_html=True)
        
        # CHECK SUSPENSION STATUS
        if current_user["is_suspended"]:
            st.error(f"🚫 YOUR ACCOUNT IS SUSPENDED UNTIL {current_user['suspended_until']} FOR POLICY VIOLATION!")
        else:
            st.markdown("### ➕ Upload Real Video / Photo Test")
            post_type = st.selectbox("Select Category", ["picture", "short", "long"])
            title = st.text_input("Post Title")
            desc = st.text_area("Description")
            
            uploaded_file = st.file_uploader("Choose Video/Picture File from Device", type=["mp4", "mov", "jpg", "png", "jpeg"])
            
            if st.button("Publish Now"):
                if uploaded_file is not None:
                    # Save File to Disk
                    file_ext = os.path.splitext(uploaded_file.name)[1]
                    saved_filename = f"{uuid.uuid4()}{file_ext}"
                    full_save_path = os.path.join(UPLOAD_DIR, saved_filename)
                    
                    with open(full_save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # AI Moderation Check
                    is_safe, reason = check_ai_safety(title + " " + desc, uploaded_file.name)
                    
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    
                    if not is_safe:
                        v_count = current_user["violation_count"] + 1
                        if v_count == 1:
                            suspend_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            q = "UPDATE master_app_table SET violation_count = 1, is_suspended = TRUE, suspended_until = %s WHERE user_id = %s" if db_type == "postgresql" else "UPDATE master_app_table SET violation_count = 1, is_suspended = 1, suspended_until = ? WHERE user_id = ?"
                            c.execute(q, (suspend_until, st.session_state.user_id))
                            st.error(f"🚨 Unsafe Media Detected ({reason})! Account Suspended for 30 Days.")
                        else:
                            q = "UPDATE master_app_table SET violation_count = %s, is_banned = TRUE WHERE user_id = %s" if db_type == "postgresql" else "UPDATE master_app_table SET violation_count = ?, is_banned = 1 WHERE user_id = ?"
                            c.execute(q, (v_count, st.session_state.user_id))
                            st.error("🚨 Repeated Violation! Permanent Account Ban.")
                        conn.commit()
                    else:
                        rec_id = str(uuid.uuid4())
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        iq = """
                            INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, media_path, post_category, created_at)
                            VALUES (%s, 'post', %s, %s, %s, %s, %s, %s, %s, %s)
                        """ if db_type == "postgresql" else """
                            INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, media_path, post_category, created_at)
                            VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?)
                        """
                        c.execute(iq, (rec_id, st.session_state.user_id, current_user["full_name"], current_user["is_verified"], title, desc, full_save_path, post_type, now))
                        conn.commit()
                        st.success("✅ Video Uploaded Successfully! Check Live Feed.")
                    conn.close()
                    st.rerun()
                else:
                    st.warning("Attach a video file first!")

    # ------------------------------------------
    # TAB 3: OWNER CONTROL CENTER
    # ------------------------------------------
    with tab_admin:
        st.markdown("### 👑 Master Admin Panel")
        pass_key = st.text_input("Admin Passkey", type="password")
        if pass_key == SECRET_OWNER_KEY:
            st.success("Welcome Owner!")
            conn, db_type = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'user'")
            u_cnt = c.fetchone()["cnt"]
            c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post'")
            p_cnt = c.fetchone()["cnt"]
            st.metric("Total Users Registered", u_cnt)
            st.metric("Total Videos/Posts Uploaded", p_cnt)
            conn.close()

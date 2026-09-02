import base64
from datetime import datetime, timedelta
import hashlib
import os
import random
import sqlite3
import uuid

import streamlit as st

# ==========================================
# 1. CONFIGURATION & ENVIRONMENT
# ==========================================
st.set_page_config(
    page_title="Enterprise Global Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATABASE_URL = os.environ.get("DATABASE_URL", None)
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", None)
LOCAL_DB_FILE = "enterprise_single_master.db"
SECRET_OWNER_KEY = "S$s123456789112233"

# ==========================================
# 2. SINGLE TABLE DATABASE SYSTEM
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

def init_single_master_database():
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Unified Single Table Schema
    if db_type == "postgresql":
        c.execute("""
            CREATE TABLE IF NOT EXISTS app_master_data (
                record_id VARCHAR(36) PRIMARY KEY,
                data_type VARCHAR(20) NOT NULL, -- 'user', 'post', 'system'
                user_id VARCHAR(36),
                full_name VARCHAR(100),
                email VARCHAR(100),
                phone_number VARCHAR(30),
                password_hash TEXT,
                country VARCHAR(60) DEFAULT 'Global',
                is_verified BOOLEAN DEFAULT FALSE,
                violation_count INT DEFAULT 0,
                is_suspended BOOLEAN DEFAULT FALSE,
                is_banned BOOLEAN DEFAULT FALSE,
                suspended_until TIMESTAMP,
                followers_count INT DEFAULT 0,
                title VARCHAR(255),
                content TEXT,
                media_url TEXT,
                post_category VARCHAR(20), -- 'short', 'long', 'picture'
                likes_count INT DEFAULT 0,
                owner_balance REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS app_master_data (
                record_id TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                user_id TEXT,
                full_name TEXT,
                email TEXT,
                phone_number TEXT,
                password_hash TEXT,
                country TEXT DEFAULT 'Global',
                is_verified INTEGER DEFAULT 0,
                violation_count INTEGER DEFAULT 0,
                is_suspended INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                suspended_until TEXT,
                followers_count INTEGER DEFAULT 0,
                title TEXT,
                content TEXT,
                media_url TEXT,
                post_category TEXT,
                likes_count INTEGER DEFAULT 0,
                owner_balance REAL DEFAULT 0.0,
                created_at TEXT
            );
        """)
    conn.commit()
    
    # Seed Demo Profiles if database is empty
    c.execute("SELECT COUNT(*) as cnt FROM app_master_data WHERE data_type = 'user'")
    res = c.fetchone()
    if res['cnt'] == 0:
        for i in range(120):
            uid = f"demo_user_{i+1}"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if db_type == "postgresql":
                c.execute("""
                    INSERT INTO app_master_data (record_id, data_type, user_id, full_name, is_verified, followers_count, created_at)
                    VALUES (%s, 'user', %s, %s, TRUE, 1500, %s)
                """, (uid, uid, f"Demo Creator {i+1}", now))
            else:
                c.execute("""
                    INSERT INTO app_master_data (record_id, data_type, user_id, full_name, is_verified, followers_count, created_at)
                    VALUES (?, 'user', ?, ?, 1, 1500, ?)
                """, (uid, uid, f"Demo Creator {i+1}", now))
        conn.commit()
    conn.close()

init_single_master_database()

# ==========================================
# 3. HELPER & MODERATION FUNCTIONS
# ==========================================
def hash_pass(pwd): 
    return hashlib.sha256(pwd.encode()).hexdigest()

def check_ai_safety(text, url=""):
    banned = ["sex", "porn", "nude", "adult", "gaalaagali", "গালাগালি", "খারাপ", "১৮+"]
    external_domains = ["youtube.com", "tiktok.com", "facebook.com", "instagram.com"]
    
    # Sex/NSFW Moderation
    lowered = (text + " " + url).lower()
    if any(word in lowered for word in banned):
        return False, "NSFW/Violating Content"
        
    # External Platform Copyright Moderation
    if any(domain in lowered for domain in external_domains):
        return False, "Copyright Violation (External Platform Video)"
        
    return True, "Clean"

def get_meta_blue_tick_html():
    # Exact Starburst Meta Blue Badge SVG
    return """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;">
        <path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425 3.25-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/>
        <path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/>
    </svg>
    """

# ==========================================
# 4. SESSION STATE MANAGEMENT
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "generated_otp" not in st.session_state: st.session_state.generated_otp = None
if "temp_user_data" not in st.session_state: st.session_state.temp_user_data = {}

# ==========================================
# 5. AUTHENTICATION (EMAIL/PHONE + 6-DIGIT OTP)
# ==========================================
if not st.session_state.user_id:
    st.markdown("<h2 style='text-align: center; color:#00c853;'>🔐 Secure Login Engine</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        login_type = st.radio("Access Mode", ["Gmail", "Phone Number"])
        user_input = st.text_input("Enter Email / Phone")
        user_pwd = st.text_input("Password", type="password")
        
        if not st.session_state.otp_sent:
            if st.button("Send 6-Digit OTP"):
                if user_input and user_pwd:
                    st.session_state.generated_otp = str(random.randint(100000, 999999))
                    st.session_state.otp_sent = True
                    st.session_state.temp_user_data = {
                        "input": user_input,
                        "pwd": hash_pass(user_pwd),
                        "type": login_type
                    }
                    st.rerun()
                else:
                    st.error("Please fill all fields.")
        else:
            st.info(f"📩 Demo Code Sent to {user_input}: **{st.session_state.generated_otp}**")
            input_otp = st.text_input("Enter 6-Digit Code")
            
            if st.button("Verify & Login/Register"):
                if input_otp == st.session_state.generated_otp:
                    conn, db_type = get_db_connection()
                    c = conn.cursor()
                    
                    # Check Existing User
                    q = "SELECT * FROM app_master_data WHERE data_type = 'user' AND (email = %s OR phone_number = %s)" if db_type == "postgresql" else "SELECT * FROM app_master_data WHERE data_type = 'user' AND (email = ? OR phone_number = ?)"
                    c.execute(q, (user_input, user_input))
                    usr = c.fetchone()
                    
                    if usr:
                        if usr["is_banned"]:
                            st.error("🚫 Your account is permanently banned by Admin!")
                        else:
                            st.session_state.user_id = usr["user_id"]
                            st.success("LoggedIn Successfully!")
                            st.rerun()
                    else:
                        # Auto Register New User
                        new_uid = str(uuid.uuid4())
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        email_val = user_input if login_type == "Gmail" else ""
                        phone_val = user_input if login_type == "Phone Number" else ""
                        
                        ins_q = """
                            INSERT INTO app_master_data (record_id, data_type, user_id, full_name, email, phone_number, password_hash, created_at)
                            VALUES (%s, 'user', %s, %s, %s, %s, %s, %s)
                        """ if db_type == "postgresql" else """
                            INSERT INTO app_master_data (record_id, data_type, user_id, full_name, email, phone_number, password_hash, created_at)
                            VALUES (?, 'user', ?, ?, ?, ?, ?, ?)
                        """
                        c.execute(ins_q, (new_uid, new_uid, f"User_{new_uid[:5]}", email_val, phone_val, hash_pass(user_pwd), now))
                        conn.commit()
                        st.session_state.user_id = new_uid
                        st.success("Registered and Logged In Successfully!")
                        st.rerun()
                    conn.close()
                else:
                    st.error("❌ Invalid Code!")

# ==========================================
# 6. MAIN APPLICATION & DASHBOARD
# ==========================================
else:
    conn, db_type = get_db_connection()
    c = conn.cursor()
    
    # Fetch Logged-in User Info
    q = "SELECT * FROM app_master_data WHERE data_type = 'user' AND user_id = %s" if db_type == "postgresql" else "SELECT * FROM app_master_data WHERE data_type = 'user' AND user_id = ?"
    c.execute(q, (st.session_state.user_id,))
    current_user = c.fetchone()
    conn.close()
    
    # Navigation Topbar
    nav_col1, nav_col2, nav_col3 = st.columns([3, 3, 1])
    with nav_col1:
        st.markdown("<h3 style='color:#00c853;'>🌐 BD AI Global Platform</h3>", unsafe_allow_html=True)
    with nav_col3:
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.otp_sent = False
            st.rerun()
            
    tab_feed, tab_profile, tab_admin = st.tabs(["📺 Global Feed", "👤 Profile & Settings", "👑 Admin Control"])
    
    # ------------------------------------------
    # TAB 1: GLOBAL FEED
    # ------------------------------------------
    with tab_feed:
        st.markdown("### 🍿 Community Feed")
        conn, db_type = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM app_master_data WHERE data_type = 'post' ORDER BY created_at DESC")
        posts = [dict(r) for r in c.fetchall()]
        conn.close()
        
        for item in posts:
            st.markdown("---")
            # Profile Header Rendering
            tick = get_meta_blue_tick_html() if item.get("is_verified") else ""
            st.markdown(f"**{item.get('full_name', 'User')}** {tick}", unsafe_allow_html=True)
            st.caption(f"Posted on: {item.get('created_at')}")
            
            if item.get("title"): st.markdown(f"#### {item['title']}")
            if item.get("content"): st.write(item["content"])
            
            if item.get("media_url"):
                if item.get("post_category") == "picture":
                    st.image(item["media_url"], use_container_width=True)
                else:
                    st.video(item["media_url"])
                    
            # Interactions
            l_col, c_col, s_col = st.columns([1, 1, 4])
            with l_col: st.button(f"👍 Like ({item.get('likes_count', 0)})", key=f"like_{item['record_id']}")
            with c_col: st.button("💬 Comment", key=f"cmt_{item['record_id']}")
            with s_col: st.button("🔗 Share", key=f"sh_{item['record_id']}")

    # ------------------------------------------
    # TAB 2: PROFILE & SETTINGS (ALL CONTROLS IN SIDE)
    # ------------------------------------------
    with tab_profile:
        if current_user:
            tick_display = get_meta_blue_tick_html() if current_user["is_verified"] else ""
            st.markdown(f"## 👤 {current_user['full_name']} {tick_display}", unsafe_allow_html=True)
            st.caption(f"Followers: {current_user['followers_count']} | Status: {'Active' if not current_user['is_suspended'] else 'Suspended'}")
            
            st.divider()
            
            # --- PLUS ICON CONTENT UPLOADER ---
            with st.expander("➕ Create & Upload New Content", expanded=False):
                if current_user["is_suspended"]:
                    st.error("🚫 Your account is currently suspended for Policy Violation!")
                else:
                    post_type = st.selectbox("Content Type", ["Picture (Max 10/day)", "Short Video (Max 1/day)", "Long Video (Max 1/day)"])
                    p_title = st.text_input("Title")
                    p_content = st.text_area("Description / Content")
                    p_url = st.text_input("Media Direct Link / Video URL")
                    
                    if st.button("Publish Content"):
                        safe, reason = check_ai_safety(p_title + " " + p_content, p_url)
                        
                        if not safe:
                            # AI Suspension Logic: 1st Violation = 30 Days, 2nd Violation = Permanent Ban
                            conn, db_type = get_db_connection()
                            c = conn.cursor()
                            v_count = current_user["violation_count"] + 1
                            
                            if v_count == 1:
                                until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                                q = "UPDATE app_master_data SET violation_count = 1, is_suspended = TRUE, suspended_until = %s WHERE user_id = %s" if db_type == "postgresql" else "UPDATE app_master_data SET violation_count = 1, is_suspended = 1, suspended_until = ? WHERE user_id = ?"
                                c.execute(q, (until, st.session_state.user_id))
                                st.error(f"🚨 Violation Detected ({reason})! Account Suspended for 30 Days.")
                            else:
                                q = "UPDATE app_master_data SET violation_count = %s, is_banned = TRUE WHERE user_id = %s" if db_type == "postgresql" else "UPDATE app_master_data SET violation_count = ?, is_banned = 1 WHERE user_id = ?"
                                c.execute(q, (v_count, st.session_state.user_id))
                                st.error("🚨 Repeated Violation Detected! Account Banned Permanently.")
                                
                            conn.commit()
                            conn.close()
                        else:
                            # Successful Upload Logic
                            cat_map = {"Picture (Max 10/day)": "picture", "Short Video (Max 1/day)": "short", "Long Video (Max 1/day)": "long"}
                            rec_id = str(uuid.uuid4())
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            conn, db_type = get_db_connection()
                            c = conn.cursor()
                            q = """
                                INSERT INTO app_master_data (record_id, data_type, user_id, full_name, is_verified, title, content, media_url, post_category, created_at)
                                VALUES (%s, 'post', %s, %s, %s, %s, %s, %s, %s, %s)
                            """ if db_type == "postgresql" else """
                                INSERT INTO app_master_data (record_id, data_type, user_id, full_name, is_verified, title, content, media_url, post_category, created_at)
                                VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?)
                            """
                            c.execute(q, (rec_id, st.session_state.user_id, current_user["full_name"], current_user["is_verified"], p_title, p_content, p_url, cat_map[post_type], now))
                            conn.commit()
                            conn.close()
                            st.success("✅ Published Successfully!")
                            st.rerun()

            # --- MANAGE OWN POSTS (DELETE OPTION) ---
            st.markdown("### 🗑️ Manage Your Posts")
            conn, db_type = get_db_connection()
            c = conn.cursor()
            q = "SELECT * FROM app_master_data WHERE data_type = 'post' AND user_id = %s" if db_type == "postgresql" else "SELECT * FROM app_master_data WHERE data_type = 'post' AND user_id = ?"
            c.execute(q, (st.session_state.user_id,))
            my_posts = [dict(r) for r in c.fetchall()]
            conn.close()
            
            for mp in my_posts:
                m_col1, m_col2 = st.columns([4, 1])
                with m_col1: st.write(f"📌 **{mp.get('title', 'Untitled')}** ({mp.get('post_category')})")
                with m_col2:
                    if st.button("Delete", key=f"del_{mp['record_id']}"):
                        conn, db_type = get_db_connection()
                        c = conn.cursor()
                        dq = "DELETE FROM app_master_data WHERE record_id = %s" if db_type == "postgresql" else "DELETE FROM app_master_data WHERE record_id = ?"
                        c.execute(dq, (mp['record_id'],))
                        conn.commit()
                        conn.close()
                        st.success("Deleted!")
                        st.rerun()

    # ------------------------------------------
    # TAB 3: OWNER & ADMIN CONTROL PANEL
    # ------------------------------------------
    with tab_admin:
        st.markdown("### 👑 Master Control Center")
        pass_in = st.text_input("Enter Passcode", type="password")
        
        if pass_in == SECRET_OWNER_KEY:
            st.success("Access Granted!")
            
            conn, db_type = get_db_connection()
            c = conn.cursor()
            
            # Global Master Balance Calculation
            c.execute("SELECT SUM(owner_balance) as total_bal FROM app_master_data")
            tot = c.fetchone()
            st.metric("💰 Owner Platform Total Revenue", f"${tot['total_bal'] or 0.0:.2f}")
            
            # Manage Pending Meta Blue Ticks for > 1000 Followers
            st.markdown("#### 🟦 Pending Blue Tick Verification Requests (>1,000 Followers)")
            c.execute("SELECT * FROM app_master_data WHERE data_type = 'user' AND followers_count >= 1000 AND is_verified = FALSE")
            reqs = [dict(r) for r in c.fetchall()]
            
            for req in reqs:
                r_col1, r_col2 = st.columns([3, 1])
                with r_col1: st.write(f"👤 **{req['full_name']}** ({req['followers_count']} Followers)")
                with r_col2:
                    if st.button("Approve Blue Tick", key=f"bt_{req['record_id']}"):
                        uq = "UPDATE app_master_data SET is_verified = TRUE WHERE record_id = %s" if db_type == "postgresql" else "UPDATE app_master_data SET is_verified = 1 WHERE record_id = ?"
                        c.execute(uq, (req['record_id'],))
                        conn.commit()
                        st.success("Blue Tick Approved!")
                        st.rerun()
            conn.close()

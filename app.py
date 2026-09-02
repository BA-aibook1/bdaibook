import os
import sqlite3
import uuid
import hashlib
import random
from datetime import datetime, timedelta
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & INITIALIZATION
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

# Secret Keys for Owner Access via Search Box
SECRET_CODES = ["S$s123456789112233", "S$s123456789112233BDAIBOOK"]

# ==========================================
# 2. SINGLE MASTER DATABASE ENGINE
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
    query = """
        CREATE TABLE IF NOT EXISTS master_app_table (
            record_id TEXT PRIMARY KEY,
            data_type TEXT NOT NULL,
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
            country TEXT DEFAULT 'Global',
            monetization_status TEXT DEFAULT 'Pending',
            created_at TEXT
        );
    """
    c.execute(query)
    conn.commit()
    conn.close()

init_master_database()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def hash_pass(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

# Session Handling
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False
if "header_logo" not in st.session_state: st.session_state.header_logo = "📖 BD AI Book"

# Header Display
st.markdown(f"<h1 style='text-align: center; color:#0064e0;'>{st.session_state.header_logo}</h1>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Global Multi-Country Video & AI Platform</p>", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR AUTHENTICATION
# ==========================================
st.sidebar.markdown("### 🔐 User Portal")
if not st.session_state.user_id:
    auth_input = st.sidebar.text_input("Gmail or Mobile Number")
    auth_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Send 6-Digit OTP"):
        if auth_input and auth_pass:
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.sidebar.info(f"📩 Code: **{st.session_state.otp_code}**")
        else:
            st.sidebar.error("Fill credentials!")
            
    if st.session_state.otp_code:
        user_otp = st.sidebar.text_input("Enter OTP Code")
        if st.sidebar.button("Verify & Login"):
            if user_otp == st.session_state.otp_code:
                conn, db_type = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                usr = c.fetchone()
                if usr:
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
                    st.sidebar.success("Registered & Logged In!")
                    st.rerun()
                conn.close()
else:
    conn, db_type = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
    current_user = c.fetchone()
    conn.close()
    st.sidebar.markdown(f"User: **{current_user['full_name']}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.is_owner_session = False
        st.rerun()

# ==========================================
# 5. TABS INTERFACE
# ==========================================
tab_feed, tab_profile, tab_monetization = st.tabs(["📺 Public Live Feed", "👤 Profile & Studio", "🌍 Global Monetization"])

# ------------------------------------------
# TAB 1: PUBLIC FEED & OWNER SECRET SEARCH
# ------------------------------------------
with tab_feed:
    search_input = st.text_input("🔍 Search Videos, Music, Hashtags (or Enter Secret Access Code)...")
    
    # OWNER SECRET SEARCH TRIGGER
    if search_input.strip() in SECRET_CODES:
        st.session_state.is_owner_session = True
        st.success("👑 OWNER PRIVILEGED ACCESS GRANTED VIA SECRET CODE!")
        st.markdown("---")
        st.markdown("## 👑 Master Owner Profile & System Command Center")
        
        # Header/Logo Changer
        new_logo = st.text_input("Change Platform Header Name / Logo Text", value=st.session_state.header_logo)
        if st.button("Update Header"):
            st.session_state.header_logo = new_logo
            st.success("Platform Header Updated Globally!")
            st.rerun()
            
        conn, db_type = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'user'")
        tot_u = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post'")
        tot_p = c.fetchone()["cnt"]
        
        st.metric("Total Global Registered Users", tot_u)
        st.metric("Total Uploaded Videos", tot_p)
        st.metric("Estimated Platform Revenue", f"${tot_p * 1.25:.2f}")
        
        st.markdown("### 🛠️ Global Content Management (Delete Any Video)")
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
        all_posts = [dict(r) for r in c.fetchall()]
        for ap in all_posts:
            ac1, ac2 = st.columns([4, 1])
            with ac1: st.write(f"User: **{ap['full_name']}** | Title: {ap['title']}")
            with ac2:
                if st.button("Owner Delete", key=f"odel_{ap['record_id']}"):
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (ap['record_id'],))
                    conn.commit()
                    st.success("Post removed!")
                    st.rerun()
        conn.close()

    # REGULAR PUBLIC FEED
    else:
        conn, db_type = get_db_connection()
        c = conn.cursor()
        if search_input:
            q_str = f"%{search_input}%"
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND (title LIKE ? OR tags LIKE ?) ORDER BY created_at DESC", (q_str, q_str))
        else:
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
            
        posts = [dict(r) for r in c.fetchall()]
        conn.close()

        for post in posts:
            st.markdown("<div style='background:#18191a; padding:15px; border-radius:10px; margin-bottom:20px;'>", unsafe_allow_html=True)
            tick = get_meta_blue_badge() if post.get("is_verified") else ""
            st.markdown(f"### {post.get('full_name')} {tick}", unsafe_allow_html=True)
            st.caption(f"Country: {post.get('country')} | Category: {post.get('post_category')}")
            
            if post.get("title"): st.subheader(post["title"])
            if post.get("content"): st.write(post["content"])
            
            media_path = post.get("media_path")
            if media_path and os.path.exists(media_path):
                if post.get("post_category") == "picture":
                    st.image(media_path, use_container_width=True)
                else:
                    st.video(media_path)
                    
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            with col1:
                st.button(f"👍 Like ({post.get('likes_count', 0)})", key=f"plk_{post['record_id']}")
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: PROFILE & UPLOAD STUDIO
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.warning("Please login from sidebar to upload videos!")
    else:
        tick = get_meta_blue_badge() if current_user["is_verified"] else ""
        st.markdown(f"## Studio: {current_user['full_name']} {tick}", unsafe_allow_html=True)
        
        post_type = st.selectbox("Type", ["short", "long", "picture"])
        title = st.text_input("Title")
        desc = st.text_area("Description")
        tags = st.text_input("Hashtags & Key Search Words")
        country = st.selectbox("Target Country Audience", ["Bangladesh", "United States", "India", "Middle East", "Global"])
        
        uploaded_file = st.file_uploader("Upload Video / Audio / Picture", type=["mp4", "mp3", "jpg", "png"])
        
        if st.button("Publish Now"):
            if uploaded_file:
                file_ext = os.path.splitext(uploaded_file.name)[1]
                saved_filename = f"{uuid.uuid4()}{file_ext}"
                full_save_path = os.path.join(UPLOAD_DIR, saved_filename)
                
                with open(full_save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
                conn, db_type = get_db_connection()
                c = conn.cursor()
                rec_id = str(uuid.uuid4())
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""
                    INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, tags, media_path, post_category, country, created_at)
                    VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (rec_id, st.session_state.user_id, current_user["full_name"], current_user["is_verified"], title, desc, tags, full_save_path, post_type, country, now))
                conn.commit()
                conn.close()
                st.success("Published Successfully!")
                st.rerun()

# ------------------------------------------
# TAB 3: GLOBAL MONETIZATION & PAYMENTS
# ------------------------------------------
with tab_monetization:
    st.markdown("### 💸 Worldwide Monetization & Payout System")
    st.info("Monetization eligibility: 1,000 Views + 100 Followers")
    
    pay_country = st.selectbox("Select Your Country for Payment Withdrawal", ["Bangladesh (bKash/Nagad)", "USA/Europe (PayPal/Stripe)", "Middle East/Global (Pyypl/Crypto)"])
    st.text_input("Enter Account / Wallet Address")
    if st.button("Submit Monetization Request"):
        st.success("Monetization Application Submitted! Processing by Owner.")

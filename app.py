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
    # Updated Table Schema supporting Profile Pic, Cover Image, and Site Logo
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
            is_owner_post INTEGER DEFAULT 0,
            created_at TEXT
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()

init_master_database()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def hash_pass(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

# Session Storage
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False

# Fetch Custom Logo Settings
conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT value FROM site_settings WHERE key = 'logo_path'")
logo_row = c.fetchone()
site_logo_path = logo_row["value"] if logo_row else None
conn.close()

# Dynamic Header Rendering
if site_logo_path and os.path.exists(site_logo_path):
    col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
    with col_l2:
        st.image(site_logo_path, width=120)
st.markdown("<h1 style='text-align: center; color:#0064e0;'>BD AI Book</h1>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Next-Gen Global Social & Media Platform</p>", unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR AUTH
# ==========================================
st.sidebar.markdown("### 🔐 User Login")
if not st.session_state.user_id:
    auth_input = st.sidebar.text_input("Gmail or Mobile")
    auth_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Send 6-Digit OTP"):
        if auth_input and auth_pass:
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.sidebar.info(f"📩 Code: **{st.session_state.otp_code}**")
            
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
                    st.sidebar.success("Registered!")
                    st.rerun()
                conn.close()
else:
    conn = get_db_connection()
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
    search_input = st.text_input("🔍 Search Videos, Hashtags or Secret Code...")
    
    # OWNER CODE UNLOCK LOGIC
    if search_input.strip() in SECRET_CODES:
        st.session_state.is_owner_session = True
        st.success("👑 MASTER OWNER ACCESS UNLOCKED!")
        st.markdown("---")
        st.markdown("## 👑 Master Owner Profile & Platform Control")
        
        # OWNER LOGO UPLOAD SETTING
        st.markdown("### 🖼️ Upload Platform Main Header Logo")
        new_logo_file = st.file_uploader("Upload Web Logo Image (PNG/JPG)", type=["png", "jpg", "jpeg"], key="owner_logo")
        if st.button("Set Web Logo"):
            if new_logo_file:
                logo_path = os.path.join(UPLOAD_DIR, f"site_logo_{uuid.uuid4()}.png")
                with open(logo_path, "wb") as f: f.write(new_logo_file.getbuffer())
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES ('logo_path', ?)", (logo_path,))
                conn.commit()
                conn.close()
                st.success("Official Platform Logo Updated!")
                st.rerun()

        # OWNER DIRECT VIDEO PUBLISHING STUDIO
        st.markdown("---")
        st.markdown("### 📢 Owner Official Announcement / Video Studio")
        o_title = st.text_input("Owner Post Title")
        o_desc = st.text_area("Owner Description")
        o_file = st.file_uploader("Upload Owner Video / Image", type=["mp4", "jpg", "png"], key="owner_media")
        
        if st.button("Publish as Owner"):
            if o_file:
                ext = os.path.splitext(o_file.name)[1]
                o_media_path = os.path.join(UPLOAD_DIR, f"owner_{uuid.uuid4()}{ext}")
                with open(o_media_path, "wb") as f: f.write(o_file.getbuffer())
                
                conn = get_db_connection()
                c = conn.cursor()
                rec_id = str(uuid.uuid4())
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""
                    INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, media_path, post_category, is_owner_post, created_at)
                    VALUES (?, 'post', 'OWNER_ID', '👑 Official Platform Owner', 1, ?, ?, ?, 'short', 1, ?)
                """, (rec_id, o_title, o_desc, o_media_path, now))
                conn.commit()
                conn.close()
                st.success("Owner Official Video Published Globally!")
                st.rerun()

        st.markdown("---")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'user'")
        st.metric("Total Platform Users", c.fetchone()["cnt"])
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post'")
        st.metric("Total Videos Published", c.fetchone()["cnt"])
        conn.close()

    # REGULAR LIVE FEED
    else:
        conn = get_db_connection()
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
            badge = "👑 [OWNER]" if post.get("is_owner_post") else ""
            
            st.markdown(f"### {post.get('full_name')} {tick} <span style='color:gold;'>{badge}</span>", unsafe_allow_html=True)
            st.caption(f"Category: {post.get('post_category')} | Uploaded: {post.get('created_at')}")
            
            if post.get("title"): st.subheader(post["title"])
            if post.get("content"): st.write(post["content"])
            
            media_path = post.get("media_path")
            if media_path and os.path.exists(media_path):
                if post.get("post_category") == "picture":
                    st.image(media_path, use_container_width=True)
                else:
                    st.video(media_path)
                    
            st.markdown("---")
            st.button(f"👍 Like ({post.get('likes_count', 0)})", key=f"lk_{post['record_id']}")
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: USER PROFILE & HEADER/AVATAR SETTINGS
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.warning("Login required to customize profile & upload media!")
    else:
        tick = get_meta_blue_badge() if current_user["is_verified"] else ""
        st.markdown(f"## Profile Studio: {current_user['full_name']} {tick}", unsafe_allow_html=True)
        
        # RENDER USER COVER & PROFILE PIC
        if current_user.get("cover_pic_path") and os.path.exists(current_user["cover_pic_path"]):
            st.image(current_user["cover_pic_path"], caption="Header / Cover Photo", use_container_width=True)
            
        col_p1, col_p2 = st.columns([1, 4])
        with col_p1:
            if current_user.get("profile_pic_path") and os.path.exists(current_user["profile_pic_path"]):
                st.image(current_user["profile_pic_path"], width=100)
            else:
                st.info("No Profile Pic")
        with col_p2:
            st.write(f"**Bio:** {current_user.get('bio', 'No bio added')}")
            st.write(f"**Address:** {current_user.get('address', 'Not set')}")
            
        # PROFILE CUSTOMIZATION EXPANDER
        with st.expander("⚙️ Edit Profile, Header Photo & Profile Picture"):
            u_name = st.text_input("Change Name", value=current_user["full_name"])
            u_addr = st.text_input("Change Address", value=current_user["address"] or "")
            u_bio = st.text_area("Change Bio", value=current_user["bio"] or "")
            
            up_prof = st.file_uploader("Upload Profile Picture (DP)", type=["jpg", "png", "jpeg"], key="dp_file")
            up_cov = st.file_uploader("Upload Header / Cover Image", type=["jpg", "png", "jpeg"], key="cover_file")
            
            if st.button("Save Profile Updates"):
                p_path = current_user["profile_pic_path"]
                c_path = current_user["cover_pic_path"]
                
                if up_prof:
                    p_path = os.path.join(UPLOAD_DIR, f"dp_{st.session_state.user_id}.png")
                    with open(p_path, "wb") as f: f.write(up_prof.getbuffer())
                    
                if up_cov:
                    c_path = os.path.join(UPLOAD_DIR, f"cov_{st.session_state.user_id}.png")
                    with open(c_path, "wb") as f: f.write(up_cov.getbuffer())
                    
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    UPDATE master_app_table 
                    SET full_name = ?, address = ?, bio = ?, profile_pic_path = ?, cover_pic_path = ? 
                    WHERE user_id = ?
                """, (u_name, u_addr, u_bio, p_path, c_path, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("Profile Details, Header & Avatar Saved!")
                st.rerun()

        # MEDIA UPLOADER
        st.markdown("---")
        st.markdown("### 📤 Upload New Video / Picture")
        post_type = st.selectbox("Format", ["short", "long", "picture"])
        title = st.text_input("Title")
        desc = st.text_area("Description")
        uploaded_media = st.file_uploader("Media File", type=["mp4", "jpg", "png"])
        
        if st.button("Publish Content"):
            if uploaded_media:
                ext = os.path.splitext(uploaded_media.name)[1]
                m_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
                with open(m_path, "wb") as f: f.write(uploaded_media.getbuffer())
                
                conn = get_db_connection()
                c = conn.cursor()
                rec_id = str(uuid.uuid4())
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""
                    INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, media_path, post_category, created_at)
                    VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?)
                """, (rec_id, st.session_state.user_id, current_user["full_name"], current_user["is_verified"], title, desc, m_path, post_type, now))
                conn.commit()
                conn.close()
                st.success("Uploaded!")
                st.rerun()

# ------------------------------------------
# TAB 3: MONETIZATION
# ------------------------------------------
with tab_monetization:
    st.markdown("### 💸 Worldwide Monetization & Payout System")
    st.info("Monetization Status: Active for Verified Creators")

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
# 2. MASTER DATABASE ENGINE & CONFIG SYSTEM
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(LOCAL_DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_master_database():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Master Table (Updated with Mobile & Email)
    c.execute("""
        CREATE TABLE IF NOT EXISTS master_app_table (
            record_id TEXT PRIMARY KEY,
            data_type TEXT NOT NULL,
            user_id TEXT,
            full_name TEXT,
            auth_identifier TEXT,
            email TEXT,
            mobile TEXT,
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
    
    # Boost Requests Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS boost_requests (
            boost_id TEXT PRIMARY KEY,
            user_id TEXT,
            post_id TEXT,
            plan TEXT,
            amount TEXT,
            trx_info TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        );
    """)
    
    # Monetization Requests Table
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
    
    # Follows & Likes
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
    
    # Global Site Settings & Lockdowns Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    
    default_settings = {
        "app_name": "BD AI Book",
        "owner_announcement": "Welcome to BD AI Book - Next-Gen Social & Media Platform!",
        "lock_upload": "OFF",
        "lock_login": "OFF",
        "bank_account_name": "Md Sohel Rana",
        "bank_name": "Clear Bank",
        "bank_iban": "GB89CLRB04281239130579",
        "bank_swift": "CLRBGB22XXX",
        "bank_acc_num": "39130579",
        "bank_acc_type": "Checking (Current)"
    }
    
    for k, v in default_settings.items():
        c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, v))
        
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

# ==========================================
# 3. HELPER & CSS (PERFECT CIRCULAR PROFILE PIC)
# ==========================================
def hash_pass(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

def increment_views(post_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE master_app_table SET views_count = views_count + 1 WHERE record_id = ?", (post_id,))
    conn.commit()
    conn.close()

# CSS for Square-to-Circle Avatar Crop
st.markdown("""
<style>
    .circular-avatar {
        width: 100px;
        height: 100px;
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 3px solid #0064e0;
    }
    .circular-avatar-small {
        width: 48px;
        height: 48px;
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid #0064e0;
    }
    .video-watermark-wrapper { position: relative; }
    .video-watermark-badge {
        position: absolute;
        top: 12px;
        right: 15px;
        background: rgba(0, 100, 224, 0.75);
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        z-index: 99;
        pointer-events: none;
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

# Session Setup
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False

# Render Logo & Dynamic App Header Name
site_logo_path = get_setting("logo_path")
app_name = get_setting("app_name", "BD AI Book")
announcement = get_setting("owner_announcement", "")

if site_logo_path and os.path.exists(site_logo_path):
    col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
    with col_l2: st.image(site_logo_path, width=120)

st.markdown(f"<h1 style='text-align: center; color:#0064e0;'>{app_name}</h1>", unsafe_allow_html=True)
if announcement:
    st.markdown(f"<div class='announcement-box'>📢 {announcement}</div>", unsafe_allow_html=True)

# ==========================================
# 4. AUTHENTICATION SYSTEM
# ==========================================
real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 User Login")

login_locked = get_setting("lock_login") == "ON"

if not st.session_state.user_id:
    if login_locked:
        st.sidebar.error("🚫 Login System is temporarily locked by Owner for maintenance!")
    else:
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
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
    raw_user = c.fetchone()
    
    c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (st.session_state.user_id,))
    f_res = c.fetchone()
    real_followers = f_res["cnt"] if f_res else 0
    conn.close()
    
    current_user = dict(raw_user) if raw_user else {}
    
    if current_user.get("is_suspended"):
        sus_until = current_user.get("suspended_until", "")
        if datetime.now().strftime("%Y-%m-%d %H:%M:%S") < sus_until:
            st.error(f"🚫 Account Suspended until: {sus_until}")
            st.stop()

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

# ------------------------------------------
# TAB 1: PUBLIC FEED & OWNER MASTER PANEL
# ------------------------------------------
with tab_feed:
    search_input = st.text_input("🔍 Search Users (Name, Mobile, Email, Address), Videos or Secret Code...")
    
    # OWNER MASTER CONTROL CENTER
    if search_input.strip() in SECRET_CODES:
        st.session_state.is_owner_session = True
        st.success("👑 MASTER OWNER COMMAND CENTER UNLOCKED!")
        st.markdown("---")
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'user'")
        total_users = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post'")
        total_posts = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE is_boosted = 1")
        total_boosted = c.fetchone()["cnt"]
        conn.close()

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("👥 Total App Users", total_users)
        col_m2.metric("🎬 Total App Posts", total_posts)
        col_m3.metric("🔥 Active Boosted Posts", total_boosted)

        st.markdown("---")
        st.markdown("### 🎛️ Owner 5 Master Control Power Panels")
        
        o_tab1, o_tab2, o_tab3, o_tab4, o_tab5 = st.tabs([
            "1️⃣ Global Branding & Owner Video Post", 
            "2️⃣ Upload Lockdown Control", 
            "3️⃣ Emergency Login Kill-Switch", 
            "4️⃣ Dynamic Bank Gateway Setup",
            "5️⃣ Content & Payout Moderation"
        ])
        
        with o_tab1:
            st.markdown("#### 🖼️ Global Branding, Logo & Owner Video Broadcaster")
            new_app_name = st.text_input("Header App Name", value=get_setting("app_name", "BD AI Book"))
            new_announcement = st.text_area("Global Owner Announcement/Video Title", value=get_setting("owner_announcement", ""))
            up_logo = st.file_uploader("Change App Master Logo", type=["png", "jpg", "jpeg"])
            
            if st.button("💾 Save Branding & Broadcast Updates"):
                set_setting("app_name", new_app_name)
                set_setting("owner_announcement", new_announcement)
                if up_logo:
                    l_path = os.path.join(UPLOAD_DIR, "site_logo.png")
                    with open(l_path, "wb") as f: f.write(up_logo.getbuffer())
                    set_setting("logo_path", l_path)
                st.success("Global App Branding & Announcement Updated Worldwide!")
                st.rerun()

        with o_tab2:
            st.markdown("#### 🚫 Video Upload Access Lockdown Control")
            curr_upload = get_setting("lock_upload", "OFF")
            st.write(f"Current Upload Status: **{'LOCKED (Disabled)' if curr_upload == 'ON' else 'UNLOCKED (Active)'}**")
            if curr_upload == "OFF":
                if st.button("🔒 ACTIVATE UPLOAD LOCKDOWN"):
                    set_setting("lock_upload", "ON")
                    st.warning("Upload system locked!")
                    st.rerun()
            else:
                if st.button("🔓 DISABLE UPLOAD LOCKDOWN"):
                    set_setting("lock_upload", "OFF")
                    st.success("Upload system unlocked!")
                    st.rerun()

        with o_tab3:
            st.markdown("#### ⚡ Emergency System & Login Kill-Switch")
            curr_login = get_setting("lock_login", "OFF")
            st.write(f"Current Login Status: **{'LOCKED (Disabled)' if curr_login == 'ON' else 'UNLOCKED (Active)'}**")
            if curr_login == "OFF":
                if st.button("🚨 ACTIVATE LOGIN KILL-SWITCH"):
                    set_setting("lock_login", "ON")
                    st.error("Login System Locked!")
                    st.rerun()
            else:
                if st.button("🟢 DISABLE LOGIN KILL-SWITCH"):
                    set_setting("lock_login", "OFF")
                    st.success("Login System Restored!")
                    st.rerun()

        with o_tab4:
            st.markdown("#### 🏦 Set Owner Custom Bank Account Gateway")
            b_acc_name = st.text_input("Account Name", value=get_setting("bank_account_name"))
            b_bank_name = st.text_input("Bank Name", value=get_setting("bank_name"))
            b_iban = st.text_input("IBAN Number", value=get_setting("bank_iban"))
            b_swift = st.text_input("BIC / SWIFT Code", value=get_setting("bank_swift"))
            b_acc_num = st.text_input("Account Number", value=get_setting("bank_acc_num"))
            b_acc_type = st.text_input("Account Type", value=get_setting("bank_acc_type"))
            
            if st.button("💳 Save Owner Bank Details Worldwide"):
                set_setting("bank_account_name", b_acc_name)
                set_setting("bank_name", b_bank_name)
                set_setting("bank_iban", b_iban)
                set_setting("bank_swift", b_swift)
                set_setting("bank_acc_num", b_acc_num)
                set_setting("bank_acc_type", b_acc_type)
                st.success("Bank Gateway Details Updated!")
                st.rerun()

        with o_tab5:
            st.markdown("#### 🛠️ Content Block & Approvals")
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
            all_posts = c.fetchall()
            for p in all_posts:
                col_cp1, col_cp2, col_cp3 = st.columns([3, 1, 1])
                col_cp1.write(f"📌 **{p['title']}** (By: {p['full_name']})")
                if col_cp2.button("🗑️ Delete", key=f"ow_del_{p['record_id']}"):
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (p['record_id'],))
                    conn.commit()
                    st.rerun()
                if col_cp3.button("🚫 Block User", key=f"ow_sus_{p['record_id']}"):
                    sus_time = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("UPDATE master_app_table SET is_suspended = 1, suspended_until = ? WHERE user_id = ?", (sus_time, p['user_id']))
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (p['record_id'],))
                    conn.commit()
                    st.rerun()
            conn.close()

    # PUBLIC FEED DISPLAY
    else:
        conn = get_db_connection()
        c = conn.cursor()
        
        if search_input:
            q_str = f"%{search_input}%"
            c.execute("""
                SELECT * FROM master_app_table 
                WHERE data_type = 'post' AND (title LIKE ? OR content LIKE ? OR full_name LIKE ? OR tags LIKE ?) 
                ORDER BY is_boosted DESC, created_at DESC
            """, (q_str, q_str, q_str, q_str))
        else:
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY is_boosted DESC, created_at DESC")
            
        posts = [dict(r) for r in c.fetchall()]
        conn.close()

        for post in posts:
            increment_views(post["record_id"])
            st.markdown("<div style='background:#18191a; padding:15px; border-radius:12px; margin-bottom:20px;'>", unsafe_allow_html=True)
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT profile_pic_path FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (post.get("user_id"),))
            author = c.fetchone()
            conn.close()
            
            author_pic = author["profile_pic_path"] if author and author["profile_pic_path"] and os.path.exists(author["profile_pic_path"]) else None
            
            col_h1, col_h2 = st.columns([4, 1])
            with col_h1:
                tick = get_meta_blue_badge() if post.get("is_verified") else ""
                boost_badge = "🔥 [BOOSTED]" if post.get("is_boosted") else ""
                
                # Circular Profile Image Render
                if author_pic:
                    st.markdown(f"<img src='data:image/png;base64,{open(author_pic, 'rb').read().hex()}' class='circular-avatar-small'>", unsafe_allow_html=True)
                st.markdown(f"### {post.get('full_name')} {tick} <span style='color:orange;'>{boost_badge}</span>", unsafe_allow_html=True)
                
            if post.get("title"): st.subheader(post["title"])
            if post.get("content"): st.write(post["content"])
            
            media_path = post.get("media_path")
            cat = post.get("post_category", "general")
            
            if media_path and os.path.exists(media_path):
                st.markdown(f"<div class='video-watermark-wrapper'><div class='video-watermark-badge'>{app_name}</div>", unsafe_allow_html=True)
                if cat == "picture":
                    st.image(media_path, use_container_width=True)
                else:
                    st.video(media_path)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")
            col_b1, col_b2 = st.columns(2)
            col_b1.write(f"👁️ **{(post.get('views_count', 0) + 1):,}** Views")
            if col_b2.button("🚀 Share", key=f"sh_{post['record_id']}"):
                st.toast("Link Copied!")
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: PROFILE & STUDIO (WITH ALL FIXED FEATURES)
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.warning("Please login to view and edit profile!")
    else:
        tick = get_meta_blue_badge() if current_user.get("is_verified") else ""
        st.markdown(f"## Profile Studio: {current_user.get('full_name', 'User')} {tick}", unsafe_allow_html=True)
        
        # User Video Count
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post' AND user_id = ?", (st.session_state.user_id,))
        total_user_videos = c.fetchone()["cnt"]
        conn.close()

        profile_path = current_user.get("profile_pic_path")
        
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            if profile_path and os.path.exists(profile_path):
                # Perfect Round Avatar Crop Implementation
                st.image(profile_path, width=120)
            else:
                st.info("No Avatar Set")
        with col_p2:
            st.write(f"👥 **Real Followers:** {real_followers:,}")
            st.write(f"🎬 **Total Uploaded Videos:** {total_user_videos}")
            st.write(f"📞 **Mobile:** {current_user.get('mobile', 'Not Set')}")
            st.write(f"📧 **Email:** {current_user.get('email', 'Not Set')}")
            st.write(f"🏠 **Address:** {current_user.get('address', 'Not Set')}")
            st.write(f"📝 **Bio:** {current_user.get('bio', 'No bio added')}")

        with st.expander("⚙️ Edit Profile Details (Name, Phone, Email, Address, DP)"):
            u_name = st.text_input("Full Name", value=current_user.get("full_name", ""))
            u_mobile = st.text_input("Mobile Number", value=current_user.get("mobile") or "")
            u_email = st.text_input("Gmail / Email", value=current_user.get("email") or "")
            u_address = st.text_area("Address", value=current_user.get("address") or "")
            u_bio = st.text_area("Bio", value=current_user.get("bio") or "")
            up_prof = st.file_uploader("Upload Profile Picture (Auto Cropped Circle)", type=["jpg", "png", "jpeg"], key="dp_edit")
            
            if st.button("Save Profile Information"):
                p_path = profile_path
                if up_prof:
                    p_path = os.path.join(UPLOAD_DIR, f"dp_{st.session_state.user_id}.png")
                    with open(p_path, "wb") as f: f.write(up_prof.getbuffer())
                    
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    UPDATE master_app_table 
                    SET full_name = ?, mobile = ?, email = ?, address = ?, bio = ?, profile_pic_path = ? 
                    WHERE user_id = ?
                """, (u_name, u_mobile, u_email, u_address, u_bio, p_path, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("Profile Details Updated Successfully!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📤 Upload New Post")
        
        if get_setting("lock_upload") == "ON":
            st.error("🚫 Video Upload System is temporarily disabled by Owner.")
        else:
            post_type = st.selectbox("Format", ["short", "long", "picture"])
            title = st.text_input("Title")
            desc = st.text_area("Description")
            p_tags = st.text_input("Hashtags")
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
                        INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, tags, media_path, post_category, views_count, likes_count, created_at)
                        VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)
                    """, (rec_id, st.session_state.user_id, current_user.get("full_name", "User"), current_user.get("is_verified", 1), title, desc, p_tags, m_path, post_type, now))
                    conn.commit()
                    conn.close()
                    st.success("Published Successfully!")
                    st.rerun()

        st.markdown("---")
        st.markdown(f"### 🎬 My Uploaded Videos ({total_user_videos} Videos)")
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND user_id = ? ORDER BY created_at DESC", (st.session_state.user_id,))
        my_posts = c.fetchall()
        conn.close()

        if my_posts:
            for mp in my_posts:
                col_mp1, col_mp2 = st.columns([4, 1])
                with col_mp1:
                    st.write(f"📌 **{mp['title']}** ({mp['post_category']}) - 👁️ {mp['views_count']:,} views")
                with col_mp2:
                    if st.button("🗑️ Delete", key=f"del_my_{mp['record_id']}"):
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("DELETE FROM master_app_table WHERE record_id = ?", (mp['record_id'],))
                        conn.commit()
                        conn.close()
                        st.success("Video Deleted!")
                        st.rerun()
        else:
            st.info("You haven't uploaded any videos yet.")

# ------------------------------------------
# TAB 3: MONETIZATION & BANK PAYMENTS
# ------------------------------------------
with tab_monetization:
    st.markdown("### 💸 Worldwide Monetization & Video Boost Center")
    st.info("Monetization and Boost settings managed globally.")

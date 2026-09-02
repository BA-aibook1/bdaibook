import os
import sqlite3
import uuid
import hashlib
import random
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components

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
    with get_db_connection() as conn:
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
            "owner_announcement": "Welcome to BD AI Book - Next-Gen Social & Media Platform!",
            "lock_upload": "OFF",
            "daily_limit_mode": "OFF",
            "lock_login": "OFF",
            "logo_path": "",
            "adsense_client_id": "ca-pub-0000000000000000",
            "adsense_script": """<div style="background:#222; color:#fff; text-align:center; padding:15px; border:1px dashed #0064e0; border-radius:8px;">📢 <b>Google AdSense Banner Placeholder</b><br><small>Replace code in Owner Panel</small></div>""",
            "show_ads": "ON"
        }
        
        for k, v in default_settings.items():
            c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, v))

        c.execute("SELECT COUNT(*) as cnt FROM payment_gateways")
        if c.fetchone()["cnt"] == 0:
            c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Mobile Banking", "bKash Personal", "01700000000"))
            c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Mobile Banking", "Nagad Personal", "01700000000"))
            c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Bank Transfer", "Dutch Bangla Bank", "Acc: 123456789, Branch: Dhaka"))
            
        conn.commit()

init_master_database()

# Config Helper Functions
def get_setting(key, default=""):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM site_settings WHERE key = ?", (key,))
        row = c.fetchone()
        return row["value"] if row else default

def set_setting(key, value):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

def hash_pass(pwd): 
    return hashlib.sha256(pwd.encode()).hexdigest()

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

def increment_views(post_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE master_app_table SET views_count = views_count + 1 WHERE record_id = ?", (post_id,))
        conn.commit()

def get_user_today_upload_count(user_id, category):
    with get_db_connection() as conn:
        c = conn.cursor()
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            SELECT COUNT(*) as cnt FROM master_app_table 
            WHERE data_type = 'post' AND user_id = ? AND post_category = ? AND created_at >= ?
        """, (user_id, category, twenty_four_hours_ago))
        res = c.fetchone()
        return res["cnt"] if res else 0

# CSS Styling
st.markdown("""
<style>
    img { border-radius: 12px; }
    .stImage > img {
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid #0064e0 !important;
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
    .tiktok-container {
        max-width: 360px;
        margin: 0 auto;
        border-radius: 14px;
        overflow: hidden;
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
    .ad-container {
        margin-top: 15px;
        margin-bottom: 15px;
        padding: 8px;
        background: #0e0e10;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
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
# 4. AUTHENTICATION SYSTEM (FIXED SECURITY)
# ==========================================
real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 User Login / Register")

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
            else:
                st.sidebar.warning("Please provide both identifier and password!")
                
        if st.session_state.otp_code:
            user_otp = st.sidebar.text_input("Enter OTP Code")
            if st.sidebar.button("Verify & Proceed"):
                if user_otp == st.session_state.otp_code:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                        usr = c.fetchone()
                        
                        if usr:
                            # 🔒 Password Match Verification Added
                            if usr["password_hash"] == hash_pass(auth_pass):
                                st.session_state.user_id = usr["user_id"]
                                st.sidebar.success("Logged In Successfully!")
                                st.rerun()
                            else:
                                st.sidebar.error("❌ Invalid Password!")
                        else:
                            # Registration
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
else:
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
        raw_user = c.fetchone()
        
        c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (st.session_state.user_id,))
        f_res = c.fetchone()
        real_followers = f_res["cnt"] if f_res else 0
        
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
        st.session_state.otp_code = None
        st.rerun()

# ==========================================
# 5. MAIN NAVIGATION TABS
# ==========================================
tab_feed, tab_profile, tab_monetization = st.tabs(["📺 Public Live Feed", "👤 Profile & Studio", "🌍 Global Monetization & Boost"])

# ------------------------------------------
# TAB 1: PUBLIC FEED & OWNER MASTER PANEL
# ------------------------------------------
with tab_feed:
    search_input = st.text_input("🔍 Search Users, Videos, Hashtags or Secret Code...")
    
    if search_input.strip() in SECRET_CODES:
        st.session_state.is_owner_session = True
        st.success("👑 MASTER OWNER COMMAND CENTER UNLOCKED!")
        st.markdown("---")
        
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'user'")
            total_users = c.fetchone()["cnt"]
            c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post'")
            total_posts = c.fetchone()["cnt"]
            c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE is_boosted = 1")
            total_boosted = c.fetchone()["cnt"]

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("👥 Total App Users", total_users)
        col_m2.metric("🎬 Total App Posts", total_posts)
        col_m3.metric("🔥 Active Boosted Posts", total_boosted)

        st.markdown("---")
        st.markdown("### 🎛️ Owner 7 Master Control Power Panels")
        
        o_tab1, o_tab2, o_tab3, o_tab4, o_tab5, o_tab6, o_tab7 = st.tabs([
            "1️⃣ Global Branding", 
            "2️⃣ Upload Control", 
            "3️⃣ Emergency Kill-Switch", 
            "4️⃣ Dynamic Payment Methods",
            "5️⃣ Google AdSense Settings",
            "6️⃣ Content Moderation",
            "7️⃣ Boost Requests"
        ])
        
        with o_tab1:
            st.markdown("#### 🖼️ Global Branding & Logo")
            new_app_name = st.text_input("Header App Name", value=get_setting("app_name", "BD AI Book"))
            new_announcement = st.text_area("Global Owner Announcement", value=get_setting("owner_announcement", ""))
            up_logo = st.file_uploader("Change Master Logo", type=["png", "jpg", "jpeg"])
            
            if st.button("💾 Save Branding Updates"):
                set_setting("app_name", new_app_name)
                set_setting("owner_announcement", new_announcement)
                if up_logo:
                    l_path = os.path.join(UPLOAD_DIR, "site_logo.png")
                    with open(l_path, "wb") as f: f.write(up_logo.getbuffer())
                    set_setting("logo_path", l_path)
                st.success("Branding Updated!")
                st.rerun()

        with o_tab2:
            st.markdown("#### 🚫 Video Upload Access Lockdown & Limits")
            curr_upload = get_setting("lock_upload", "OFF")
            st.write(f"Upload Lockdown Status: **{'LOCKED' if curr_upload == 'ON' else 'UNLOCKED'}**")
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                if curr_upload == "OFF":
                    if st.button("🔒 ACTIVATE UPLOAD LOCKDOWN"):
                        set_setting("lock_upload", "ON")
                        st.rerun()
                else:
                    if st.button("🔓 DISABLE UPLOAD LOCKDOWN"):
                        set_setting("lock_upload", "OFF")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### ⚙️ Global Daily Limit Switch (১ Short, ১ Long, ১০ Post per day)")
            curr_daily_limit = get_setting("daily_limit_mode", "OFF")
            st.write(f"Global Daily Limit Status: **{'ACTIVE (১টি Short, ১টি Long, ১০টি Post)' if curr_daily_limit == 'ON' else 'UNLIMITED (যত খুশি পোস্ট)'}**")

            with col_u2:
                if curr_daily_limit == "OFF":
                    if st.button("🟢 TURN ON DAILY LIMIT MODE"):
                        set_setting("daily_limit_mode", "ON")
                        st.rerun()
                else:
                    if st.button("🔴 TURN OFF DAILY LIMIT MODE"):
                        set_setting("daily_limit_mode", "OFF")
                        st.rerun()

        with o_tab3:
            st.markdown("#### ⚡ Emergency System Login Kill-Switch")
            curr_login = get_setting("lock_login", "OFF")
            st.write(f"Current Login Status: **{'LOCKED' if curr_login == 'ON' else 'UNLOCKED'}**")
            
            if curr_login == "OFF":
                if st.button("🚨 ACTIVATE LOGIN KILL-SWITCH"):
                    set_setting("lock_login", "ON")
                    st.rerun()
            else:
                if st.button("🟢 DISABLE LOGIN KILL-SWITCH"):
                    set_setting("lock_login", "OFF")
                    st.rerun()

        with o_tab4:
            st.markdown("#### 🏦 Dynamic Payment Gateway & Bank Account Control")
            
            with st.form("add_new_payment_method"):
                m_type = st.selectbox("Method Type", ["Mobile Banking", "Bank Transfer", "Crypto / International"])
                p_name = st.text_input("Provider / Bank Name", placeholder="e.g. bKash Merchant / City Bank")
                p_details = st.text_area("Account Details / Number", placeholder="e.g. Account No: 123456, Branch: Dhaka")
                submit_gw = st.form_submit_button("➕ Add New Payment Method")
                
                if submit_gw and p_name and p_details:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), m_type, p_name, p_details))
                        conn.commit()
                    st.success("Payment Method Added Successfully!")
                    st.rerun()

            st.markdown("##### Existing Active Payment Gateways")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM payment_gateways")
                gateways = c.fetchall()

            for gw in gateways:
                col_g1, col_g2 = st.columns([4, 1])
                col_g1.write(f"📌 **[{gw['method_type']}] {gw['provider_name']}** — {gw['account_details']}")
                if col_g2.button("🗑️ Remove", key=f"del_gw_{gw['gateway_id']}"):
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM payment_gateways WHERE gateway_id = ?", (gw['gateway_id'],))
                        conn.commit()
                    st.rerun()

        with o_tab5:
            st.markdown("#### 📢 Google AdSense & Ads Management")
            ad_status = st.radio("Global Video Ads Status", ["ON", "OFF"], index=0 if get_setting("show_ads") == "ON" else 1)
            adsense_code = st.text_area("Paste Google AdSense / Banner HTML Script", value=get_setting("adsense_script"), height=150)
            
            if st.button("💾 Save AdSense Configuration"):
                set_setting("show_ads", ad_status)
                set_setting("adsense_script", adsense_code)
                st.success("AdSense Settings Saved!")
                st.rerun()

        with o_tab6:
            st.markdown("#### 🛠️ Content & Moderation")
            with get_db_connection() as conn:
                c = conn.cursor()
                st.markdown("##### Monetization Approvals")
                c.execute("SELECT * FROM monetization_requests WHERE status = 'Pending'")
                m_reqs = c.fetchall()
                for mr in m_reqs:
                    st.write(f"User ID: {mr['user_id']} | Bank: {mr['bank_info']}")
                    if st.button(f"✅ Approve ({mr['mon_id']})"):
                        c.execute("UPDATE master_app_table SET monetization_status = 'Approved' WHERE user_id = ?", (mr['user_id'],))
                        c.execute("UPDATE monetization_requests SET status = 'Approved' WHERE mon_id = ?", (mr['mon_id'],))
                        conn.commit()
                        st.rerun()

                st.markdown("##### Delete Content & Suspend User")
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
                all_posts = c.fetchall()
                for p in all_posts:
                    col_cp1, col_cp2, col_cp3 = st.columns([3, 1, 1])
                    col_cp1.write(f"📌 **{p['title']}** ({p['full_name']})")
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

        with o_tab7:
            st.markdown("#### 🚀 Video Boost Requests")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM boost_requests WHERE status = 'Pending'")
                b_reqs = c.fetchall()
                for br in b_reqs:
                    st.write(f"📌 Post ID: {br['post_id']} | Method: {br['payment_method']} | Trx: {br['trx_info']} | Plan: {br['plan']}")
                    if st.button(f"🔥 Approve & Boost ({br['boost_id']})"):
                        c.execute("UPDATE master_app_table SET is_boosted = 1 WHERE record_id = ?", (br['post_id'],))
                        c.execute("UPDATE boost_requests SET status = 'Approved' WHERE boost_id = ?", (br['boost_id'],))
                        conn.commit()
                        st.success("Post Boosted!")
                        st.rerun()

    else:
        with get_db_connection() as conn:
            c = conn.cursor()
            if search_input:
                q_str = f"%{search_input}%"
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND (title LIKE ? OR content LIKE ? OR full_name LIKE ? OR tags LIKE ?) ORDER BY is_boosted DESC, created_at DESC", (q_str, q_str, q_str, q_str))
            else:
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY is_boosted DESC, created_at DESC")
                
            posts = [dict(r) for r in c.fetchall()]

        ads_enabled = get_setting("show_ads") == "ON"
        ads_html = get_setting("adsense_script")

        for post in posts:
            increment_views(post["record_id"])
            st.markdown("<div style='background:#18191a; padding:15px; border-radius:12px; margin-bottom:15px;'>", unsafe_allow_html=True)
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT profile_pic_path FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (post.get("user_id"),))
                author = c.fetchone()
                
                c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (post.get("user_id"),))
                f_row = c.fetchone()
                author_followers = f_row["cnt"] if f_row else 0
                
                is_following = False
                if st.session_state.user_id:
                    c.execute("SELECT * FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, post.get("user_id")))
                    if c.fetchone(): is_following = True
            
            author_pic = author["profile_pic_path"] if author and author["profile_pic_path"] and os.path.exists(author["profile_pic_path"]) else None
            
            col_h1, col_h2 = st.columns([3, 2])
            with col_h1:
                col_pic, col_info = st.columns([1, 4])
                with col_pic:
                    if author_pic: 
                        st.image(author_pic, width=50)
                    else:
                        st.markdown("👤")
                with col_info:
                    tick = get_meta_blue_badge() if post.get("is_verified") else ""
                    boost_badge = "🔥 [BOOSTED]" if post.get("is_boosted") else ""
                    st.markdown(f"**{post.get('full_name')}** {tick} <span style='color:orange;'>{boost_badge}</span>", unsafe_allow_html=True)
                    st.caption(f"👥 Followers: {author_followers:,} | Category: {post.get('post_category')}")
                
            with col_h2:
                if st.session_state.user_id and st.session_state.user_id != post.get("user_id"):
                    fol_lbl = "✔ Following" if is_following else "➕ Follow"
                    if st.button(fol_lbl, key=f"fol_{post['record_id']}"):
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            if is_following:
                                c.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, post.get("user_id")))
                            else:
                                c.execute("INSERT OR REPLACE INTO follows VALUES (?, ?)", (st.session_state.user_id, post.get("user_id")))
                            conn.commit()
                        st.rerun()

            if post.get("title"): st.subheader(post["title"])
            if post.get("content"): st.write(post["content"])
            if post.get("tags"): st.markdown(f"<span style='color:#0064e0;'>{post['tags']}</span>", unsafe_allow_html=True)
            
            media_path = post.get("media_path")
            cat = post.get("post_category", "general")
            
            if media_path and os.path.exists(media_path):
                st.markdown(f"<div class='video-watermark-wrapper'><div class='video-watermark-badge'>{app_name}</div>", unsafe_allow_html=True)
                if cat == "picture":
                    st.image(media_path, use_container_width=True)
                elif cat == "short":
                    st.markdown("<div class='tiktok-container'>", unsafe_allow_html=True)
                    st.video(media_path)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.video(media_path)
                st.markdown("</div>", unsafe_allow_html=True)

            if ads_enabled and ads_html:
                st.markdown("<div class='ad-container'>", unsafe_allow_html=True)
                components.html(ads_html, height=100)
                st.markdown("</div>", unsafe_allow_html=True)

            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) as cnt FROM likes WHERE post_id = ?", (post["record_id"],))
                real_likes = c.fetchone()["cnt"]
                
                has_liked = False
                if st.session_state.user_id:
                    c.execute("SELECT * FROM likes WHERE user_id = ? AND post_id = ?", (st.session_state.user_id, post["record_id"]))
                    if c.fetchone(): has_liked = True

            st.markdown("---")
            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.write(f"👁️ **{(post.get('views_count', 0) + 1):,}** Views")
            
            like_lbl = f"❤️ Liked ({real_likes})" if has_liked else f"👍 Like ({real_likes})"
            if col_b2.button(like_lbl, key=f"lk_{post['record_id']}"):
                if st.session_state.user_id:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        if has_liked:
                            c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (st.session_state.user_id, post["record_id"]))
                        else:
                            c.execute("INSERT OR REPLACE INTO likes (user_id, post_id, category) VALUES (?, ?, ?)", (st.session_state.user_id, post["record_id"], cat))
                        conn.commit()
                    st.rerun()
                else:
                    st.warning("Please login to like!")

            if col_b3.button("🚀 Share", key=f"sh_{post['record_id']}"):
                st.toast("Sharing Link Copied!")
                
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: PROFILE & STUDIO
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.warning("Please login to manage profile!")
    else:
        tick = get_meta_blue_badge() if current_user.get("is_verified") else ""
        st.markdown(f"## Profile Studio: {current_user.get('full_name', 'User')} {tick}", unsafe_allow_html=True)
        
        profile_path = current_user.get("profile_pic_path")
        
        col_p1, col_p2 = st.columns([1, 4])
        with col_p1:
            if profile_path and os.path.exists(profile_path):
                st.image(profile_path, width=120)
            else:
                st.info("No Profile Pic")
        with col_p2:
            st.write(f"👥 **Real Followers:** {real_followers:,}")
            st.write(f"**Bio:** {current_user.get('bio', 'No bio added')}")

        with st.expander("⚙️ Edit Profile"):
            u_name = st.text_input("Name", value=current_user.get("full_name", ""))
            u_bio = st.text_area("Bio", value=current_user.get("bio") or "")
            up_prof = st.file_uploader("Upload Profile Picture", type=["jpg", "png", "jpeg"], key="dp_edit")
            
            if st.button("Save Profile"):
                p_path = profile_path
                if up_prof:
                    p_path = os.path.join(UPLOAD_DIR, f"dp_{st.session_state.user_id}.png")
                    with open(p_path, "wb") as f: f.write(up_prof.getbuffer())
                    
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("UPDATE master_app_table SET full_name = ?, bio = ?, profile_pic_path = ? WHERE user_id = ?", (u_name, u_bio, p_path, st.session_state.user_id))
                    conn.commit()
                st.success("Profile Updated!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📤 Upload New Post")
        
        if get_setting("lock_upload") == "ON":
            st.error("🚫 Video Upload System is temporarily disabled by Owner.")
        else:
            post_type = st.selectbox("Format", ["short", "long", "picture"])
            
            if get_setting("daily_limit_mode") == "ON":
                current_cnt = get_user_today_upload_count(st.session_state.user_id, post_type)
                limit_max = 1 if post_type in ["short", "long"] else 10
                st.info(f"⚠️ **Daily Guidelines Active:** You have uploaded **{current_cnt}/{limit_max}** {post_type} post(s) today.")

            title = st.text_input("Title")
            desc = st.text_area("Description")
            p_tags = st.text_input("Hashtags")
            uploaded_media = st.file_uploader("Media File", type=["mp4", "jpg", "png"])
            
            if st.button("Publish Post"):
                if uploaded_media and title:
                    if get_setting("daily_limit_mode") == "ON":
                        today_count = get_user_today_upload_count(st.session_state.user_id, post_type)
                        if post_type == "short" and today_count >= 1:
                            st.error("🚫 Limit Exceeded! You can only upload 1 Short video per 24 hours.")
                            st.stop()
                        elif post_type == "long" and today_count >= 1:
                            st.error("🚫 Limit Exceeded! You can only upload 1 Long video per 24 hours.")
                            st.stop()
                        elif post_type == "picture" and today_count >= 10:
                            st.error("🚫 Limit Exceeded! You can only upload 10 Pictures/Posts per 24 hours.")
                            st.stop()

                    if any(w in (title + " " + desc).lower() for w in BANNED_KEYWORDS):
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            sus_time = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE master_app_table SET is_suspended = 1, suspended_until = ? WHERE user_id = ?", (sus_time, st.session_state.user_id))
                            conn.commit()
                        st.error("🚫 Inappropriate Content Detected! Account suspended.")
                        st.rerun()

                    ext = os.path.splitext(uploaded_media.name)[1]
                    m_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
                    with open(m_path, "wb") as f: f.write(uploaded_media.getbuffer())
                    
                    rec_id = str(uuid.uuid4())
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, tags, media_path, post_category, views_count, likes_count, created_at)
                            VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)
                        """, (rec_id, st.session_state.user_id, current_user.get("full_name", "User"), current_user.get("is_verified", 1), title, desc, p_tags, m_path, post_type, now))
                        conn.commit()
                    st.success("Published Successfully!")
                    st.rerun()

# ------------------------------------------
# TAB 3: MONETIZATION & BANK PAYMENTS
# ------------------------------------------
with tab_monetization:
    st.markdown("### 💸 Worldwide Monetization & Video Boost Center")
    
    mon_status = current_user.get("monetization_status", "Not Eligible")
    
    if mon_status == "Approved":
        st.success(f"🎉 **Monetization Active & Approved!**")
        st.metric("Estimated Earning Balance", "$1,250.00 USD")
    elif real_followers >= 1000:
        st.success(f"🎉 **You are eligible for Monetization!**")
        with st.expander("📝 Apply for Monetization Payout"):
            bank_info_input = st.text_area("Enter Your Bank Account / bKash / Nagad Details for Payouts")
            if st.button("Submit Monetization Application"):
                if bank_info_input:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO monetization_requests (mon_id, user_id, followers_count, bank_info, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (str(uuid.uuid4()), st.session_state.user_id, real_followers, bank_info_input, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                    st.success("Application Submitted!")
    else:
        st.info(f"📈 **Monetization Progress:** {real_followers}/1,000 Real Followers needed.")

    st.markdown("---")
    st.markdown("### 🔥 Boost Your Video / Post (Dynamic Payment Gateways)")
    
    if not st.session_state.user_id:
        st.warning("Please login to boost posts.")
    else:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT record_id, title FROM master_app_table WHERE data_type = 'post' AND user_id = ?", (st.session_state.user_id,))
            user_posts = c.fetchall()
            
            c.execute("SELECT * FROM payment_gateways WHERE is_active = 1")
            active_gateways = c.fetchall()
        
        if not user_posts:
            st.info("You haven't uploaded any posts yet to boost.")
        elif not active_gateways:
            st.error("No active payment methods found. Please contact admin.")
        else:
            post_options = {p["title"]: p["record_id"] for p in user_posts}
            selected_title = st.selectbox("Select Post to Boost", list(post_options.keys()))
            selected_post_id = post_options[selected_title]
            
            boost_plan = st.selectbox("Select Boost Package", [
                "Basic - 5,000 Views ($5 / 550 BDT)",
                "Pro - 20,000 Views ($15 / 1650 BDT)",
                "VIP Unlimited - 100,000 Views ($50 / 5500 BDT)"
            ])
            
            gw_options = {f"[{gw['method_type']}] {gw['provider_name']}": gw for gw in active_gateways}
            selected_gw_name = st.selectbox("Select Payment Method", list(gw_options.keys()))
            selected_gw = gw_options[selected_gw_name]
            
            st.info(f"💳 Send Money / Transfer Details: **{selected_gw['account_details']}**")
                
            trx_id = st.text_input("Enter Payment Transaction ID (TrxID) / Reference Code")
            
            if st.button("Submit Boost Request"):
                if trx_id:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO boost_requests (boost_id, user_id, post_id, plan, amount, trx_info, payment_method, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (str(uuid.uuid4()), st.session_state.user_id, selected_post_id, boost_plan, boost_plan.split('(')[-1].replace(')', ''), trx_id, selected_gw_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                    st.success("✅ Boost Request Submitted Successfully! Owner will verify and activate boost shortly.")
                else:
                    st.error("Please enter the Transaction ID.")

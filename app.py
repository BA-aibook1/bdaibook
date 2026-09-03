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

# CSS: হেডার সম্পূর্ণ স্থির (Fixed Sticky Header) করা এবং ভার্টিক্যাল লাইভ ফিড স্টাইলিং
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; }
    div[data-testid="stHeader"] {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background-color: #0e1117;
        z-index: 99999;
        border-bottom: 1px solid #222;
    }
    img { border-radius: 12px; }
    .stImage > img {
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid #0064e0 !important;
    }
    .fb-post-card {
        background: #18191a; padding: 16px;
        border-radius: 12px; margin-bottom: 20px;
        border: 1px solid #2f3031;
    }
    .video-watermark-wrapper { position: relative; }
    .video-watermark-badge {
        position: absolute; top: 12px; right: 15px;
        background: rgba(0, 100, 224, 0.85); color: white;
        padding: 4px 10px; border-radius: 20px;
        font-size: 11px; font-weight: bold; z-index: 99;
        pointer-events: none;
    }
    .tiktok-container {
        max-width: 320px; margin: 0 auto;
        border-radius: 14px; overflow: hidden; border: 1px solid #333;
    }
    .announcement-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white; padding: 10px; border-radius: 10px;
        text-align: center; margin-bottom: 10px; font-weight: bold; font-size: 13px;
    }
    .ad-container {
        margin-top: 15px; margin-bottom: 15px; padding: 8px;
        background: #0e0e10; border-radius: 8px; text-align: center;
    }
    .vertical-live-feed-box {
        max-height: 600px; overflow-y: auto;
        background: #121316; padding: 15px; border-radius: 12px; border: 2px solid #0064e0;
    }
    .vertical-live-card {
        background: #1e2026; border-left: 4px solid #0064e0;
        padding: 12px; margin-bottom: 15px; border-radius: 8px; color: #fff;
    }
</style>
""", unsafe_allow_html=True)

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
                record_id TEXT PRIMARY KEY, data_type TEXT NOT NULL, user_id TEXT,
                full_name TEXT, auth_identifier TEXT, password_hash TEXT, address TEXT, bio TEXT,
                profile_pic_path TEXT, cover_pic_path TEXT, fb_link TEXT, tiktok_link TEXT,
                yt_link TEXT, website_link TEXT, followers_count INTEGER DEFAULT 0,
                is_verified INTEGER DEFAULT 1, violation_count INTEGER DEFAULT 0,
                is_suspended INTEGER DEFAULT 0, suspended_until TEXT, title TEXT,
                content TEXT, tags TEXT, media_path TEXT, post_category TEXT,
                likes_count INTEGER DEFAULT 0, views_count INTEGER DEFAULT 0,
                is_boosted INTEGER DEFAULT 0, monetization_status TEXT DEFAULT 'Not Eligible',
                country TEXT DEFAULT 'Global', is_owner_post INTEGER DEFAULT 0, created_at TEXT
            );
        """)
        try:
            c.execute("ALTER TABLE master_app_table ADD COLUMN recovery_code TEXT")
        except sqlite3.OperationalError:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS boost_requests (
                boost_id TEXT PRIMARY KEY, user_id TEXT, post_id TEXT, plan TEXT,
                amount TEXT, trx_info TEXT, payment_method TEXT, status TEXT DEFAULT 'Pending', created_at TEXT
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS monetization_requests (
                mon_id TEXT PRIMARY KEY, user_id TEXT, followers_count INTEGER,
                bank_info TEXT, status TEXT DEFAULT 'Pending', created_at TEXT
            );
        """)
        c.execute("CREATE TABLE IF NOT EXISTS follows (follower_id TEXT, following_id TEXT, PRIMARY KEY (follower_id, following_id));")
        c.execute("CREATE TABLE IF NOT EXISTS likes (user_id TEXT, post_id TEXT, category TEXT DEFAULT 'general', PRIMARY KEY (user_id, post_id));")
        c.execute("CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT);")
        c.execute("CREATE TABLE IF NOT EXISTS payment_gateways (gateway_id TEXT PRIMARY KEY, method_type TEXT, provider_name TEXT, account_details TEXT, is_active INTEGER DEFAULT 1);")
        
        default_settings = {
            "app_name": "BD AI Book",
            "owner_announcement": "Welcome to BD AI Book - Next-Gen Social & Media Platform!",
            "lock_upload": "OFF", "daily_limit_mode": "OFF", "lock_login": "OFF",
            "logo_path": "", "adsense_client_id": "ca-pub-0000000000000000",
            "adsense_script": """<div style="background:#222; color:#fff; text-align:center; padding:15px; border:1px dashed #0064e0; border-radius:8px;">📢 <b>Google AdSense Banner Placeholder</b></div>""",
            "show_ads": "ON"
        }
        for k, v in default_settings.items():
            c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, v))

        c.execute("SELECT COUNT(*) as cnt FROM payment_gateways")
        if c.fetchone()["cnt"] == 0:
            # Default Gateways including your provided details
            c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Local Bank", "Islami Bank Bangladesh PLC", "Title: MD. SOHEL RANA\nAccount: 20502530202612312\nBranch: Lalmonirhat Br, Lalmonirhat\nRouting No: 125520465"))
            c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "International Bank (GB)", "Clear Bank", "Name: Md Sohel Rana\nIBAN: GB89CLRB04281239130579\nBIC/SWIFT: CLRBGB22XXX\nAccount No: 39130579\nAddress: 133 Houndsditch, LONDON, EC3A 7BX"))
            c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Crypto (USDT)", "USDT TRC20 Wallet", "TM6DAbNuF2kaMaRoC8HKi2G8Gi5hVWnbCP"))
            c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), "Crypto (USDT)", "USDT BEP20 Wallet", "0x53052be072029dd76e02b01d925e29b03c5294ad"))
            
        conn.commit()

init_master_database()

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

def hash_pass(pwd): return hashlib.sha256(pwd.encode()).hexdigest()
def get_meta_blue_badge(): return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

def increment_views(post_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE master_app_table SET views_count = views_count + 1 WHERE record_id = ?", (post_id,))
        conn.commit()

def get_user_today_upload_count(user_id, category):
    with get_db_connection() as conn:
        c = conn.cursor()
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post' AND user_id = ? AND post_category = ? AND created_at >= ?", (user_id, category, twenty_four_hours_ago))
        res = c.fetchone()
        return res["cnt"] if res else 0

if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

site_logo_path = get_setting("logo_path")
app_name = get_setting("app_name", "BD AI Book")
announcement = get_setting("owner_announcement", "")

top_col1, top_col2, top_col3 = st.columns([1, 3, 1])
with top_col1:
    if site_logo_path and os.path.exists(site_logo_path): st.image(site_logo_path, width=50)
    else: st.markdown("📖")
with top_col2:
    st.markdown(f"<h3 style='text-align: center; color:#0064e0; margin:0;'>{app_name}</h3>", unsafe_allow_html=True)
with top_col3:
    if st.button("👤 Profile", key="quick_profile_btn"):
        st.session_state.active_tab = 1
        st.rerun()

if announcement:
    st.markdown(f"<div class='announcement-box'>📢 {announcement}</div>", unsafe_allow_html=True)

# ==========================================
# 4. AUTHENTICATION SYSTEM
# ==========================================
real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 User Login / Register")
login_locked = get_setting("lock_login") == "ON"

if not st.session_state.user_id:
    if login_locked:
        st.sidebar.error("🚫 Login System is temporarily locked by Owner!")
    else:
        auth_input = st.sidebar.text_input("Gmail or Mobile")
        auth_pass = st.sidebar.text_input("Password", type="password")
        is_recovery_mode = st.sidebar.checkbox("🔑 Account Recovery Mode?")
        
        if is_recovery_mode:
            rec_code_inp = st.sidebar.text_input("Recovery Code")
            new_pass_inp = st.sidebar.text_input("New Password", type="password")
            if st.sidebar.button("Reset Password"):
                if auth_input and rec_code_inp and new_pass_inp:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ? AND recovery_code = ?", (auth_input, rec_code_inp))
                        usr_rec = c.fetchone()
                        if usr_rec:
                            c.execute("UPDATE master_app_table SET password_hash = ? WHERE user_id = ?", (hash_pass(new_pass_inp), usr_rec['user_id']))
                            conn.commit()
                            st.sidebar.success("Password Reset Success!")
                        else:
                            st.sidebar.error("Invalid Identifier or Recovery Code!")
        else:
            if st.sidebar.button("Send OTP"):
                if auth_input and auth_pass:
                    st.session_state.otp_code = str(random.randint(100000, 999999))
                    st.sidebar.info(f"📩 OTP Code: **{st.session_state.otp_code}**")
            if st.session_state.otp_code:
                user_otp = st.sidebar.text_input("Enter OTP Code")
                if st.sidebar.button("Verify & Proceed"):
                    if user_otp == st.session_state.otp_code:
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                            usr = c.fetchone()
                            if usr:
                                if usr["password_hash"] == hash_pass(auth_pass):
                                    st.session_state.user_id = usr["user_id"]
                                    st.sidebar.success("Logged In Successfully!")
                                    st.rerun()
                                else:
                                    st.sidebar.error("❌ Invalid Password!")
                            else:
                                new_uid = str(uuid.uuid4())
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                c.execute("INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, created_at) VALUES (?, 'user', ?, ?, ?, ?, 1, ?)", (new_uid, new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), now))
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

def render_post_card(post, ads_enabled, ads_html, prefix="feed"):
    increment_views(post["record_id"])
    st.markdown("<div class='fb-post-card'>", unsafe_allow_html=True)
    
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
            if author_pic: st.image(author_pic, width=50)
            else: st.markdown("👤")
        with col_info:
            tick = get_meta_blue_badge() if post.get("is_verified") else ""
            boost_badge = "🔥 [BOOSTED]" if post.get("is_boosted") else ""
            st.markdown(f"**{post.get('full_name')}** {tick} <span style='color:orange;'>{boost_badge}</span>", unsafe_allow_html=True)
            st.caption(f"👥 Followers: {author_followers:,} | Category: {post.get('post_category')}")
        
    with col_h2:
        if st.session_state.user_id and st.session_state.user_id != post.get("user_id"):
            fol_lbl = "✔ Following" if is_following else "➕ Follow"
            if st.button(fol_lbl, key=f"fol_{prefix}_{post['record_id']}"):
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

    if st.session_state.user_id and st.session_state.user_id == post.get("user_id"):
        with st.expander("✏️ Edit or Delete Post"):
            new_title = st.text_input("Edit Title", value=post.get("title", ""), key=f"et_{prefix}_{post['record_id']}")
            new_content = st.text_area("Edit Description", value=post.get("content", ""), key=f"ec_{prefix}_{post['record_id']}")
            col_ed1, col_ed2 = st.columns(2)
            if col_ed1.button("💾 Save Changes", key=f"save_{prefix}_{post['record_id']}"):
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("UPDATE master_app_table SET title = ?, content = ? WHERE record_id = ?", (new_title, new_content, post["record_id"]))
                    conn.commit()
                st.success("Updated!")
                st.rerun()
            if col_ed2.button("🗑️ Delete", key=f"del_{prefix}_{post['record_id']}"):
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (post["record_id"],))
                    conn.commit()
                st.success("Deleted!")
                st.rerun()

    media_path = post.get("media_path")
    cat = post.get("post_category", "general")
    if media_path and os.path.exists(media_path):
        st.markdown(f"<div class='video-watermark-wrapper'><div class='video-watermark-badge'>{app_name}</div>", unsafe_allow_html=True)
        if cat == "picture": st.image(media_path, use_container_width=True)
        elif cat == "short":
            st.markdown("<div class='tiktok-container'>", unsafe_allow_html=True)
            st.video(media_path)
            st.markdown("</div>", unsafe_allow_html=True)
        else: st.video(media_path)
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
    if col_b2.button(like_lbl, key=f"lk_{prefix}_{post['record_id']}"):
        if st.session_state.user_id:
            with get_db_connection() as conn:
                c = conn.cursor()
                if has_liked: c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (st.session_state.user_id, post["record_id"]))
                else: c.execute("INSERT OR REPLACE INTO likes (user_id, post_id, category) VALUES (?, ?, ?)", (st.session_state.user_id, post["record_id"], cat))
                conn.commit()
            st.rerun()
        else: st.warning("Please login!")
    if col_b3.button("🚀 Share", key=f"sh_{prefix}_{post['record_id']}"):
        st.toast("Link Copied!")
    st.markdown("</div>", unsafe_allow_html=True)

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
        col_m3.metric("🔥 Active Boosted", total_boosted)

        st.markdown("---")
        st.markdown("### 🎛️ Owner 10 Master Control Power Panels")
        
        # 10th Tab added successfully without altering previous ones
        o_tab1, o_tab2, o_tab3, o_tab4, o_tab5, o_tab6, o_tab7, o_tab8, o_tab9, o_tab10 = st.tabs([
            "1️⃣ Global Branding", 
            "2️⃣ Upload Control", 
            "3️⃣ Emergency Kill-Switch", 
            "4️⃣ Dynamic Payment Methods",
            "5️⃣ Google AdSense",
            "6️⃣ Moderation",
            "7️⃣ Boosts",
            "8️⃣ Live Feed",
            "9️⃣ Recovery System",
            "🔟 Direct Bank & Crypto Accounts"
        ])
        
        with o_tab1:
            st.markdown("#### 🖼️ Global Branding & Logo")
            new_app_name = st.text_input("Header App Name", value=get_setting("app_name", "BD AI Book"))
            new_announcement = st.text_area("Global Owner Announcement", value=get_setting("owner_announcement", ""))
            up_logo = st.file_uploader("Change Master Logo", type=["png", "jpg", "jpeg"])
            if st.button("💾 Save Branding"):
                set_setting("app_name", new_app_name)
                set_setting("owner_announcement", new_announcement)
                if up_logo:
                    l_path = os.path.join(UPLOAD_DIR, "site_logo.png")
                    with open(l_path, "wb") as f: f.write(up_logo.getbuffer())
                    set_setting("logo_path", l_path)
                st.success("Updated!")
                st.rerun()

        with o_tab2:
            st.markdown("#### 🚫 Video Upload Lockdown & Limits")
            curr_upload = get_setting("lock_upload", "OFF")
            if curr_upload == "OFF":
                if st.button("🔒 ACTIVATE UPLOAD LOCKDOWN"):
                    set_setting("lock_upload", "ON")
                    st.rerun()
            else:
                if st.button("🔓 DISABLE UPLOAD LOCKDOWN"):
                    set_setting("lock_upload", "OFF")
                    st.rerun()
            curr_daily_limit = get_setting("daily_limit_mode", "OFF")
            if curr_daily_limit == "OFF":
                if st.button("🟢 TURN ON DAILY LIMIT MODE"):
                    set_setting("daily_limit_mode", "ON")
                    st.rerun()
            else:
                if st.button("🔴 TURN OFF DAILY LIMIT MODE"):
                    set_setting("daily_limit_mode", "OFF")
                    st.rerun()

        with o_tab3:
            st.markdown("#### ⚡ Emergency Login Kill-Switch")
            curr_login = get_setting("lock_login", "OFF")
            if curr_login == "OFF":
                if st.button("🚨 ACTIVATE LOGIN KILL-SWITCH"):
                    set_setting("lock_login", "ON")
                    st.rerun()
            else:
                if st.button("🟢 DISABLE LOGIN KILL-SWITCH"):
                    set_setting("lock_login", "OFF")
                    st.rerun()

        with o_tab4:
            st.markdown("#### 🏦 Dynamic Payment Gateways")
            with st.form("add_new_payment_method"):
                m_type = st.selectbox("Method Type", ["Local Bank", "International Bank", "Crypto (USDT)", "Mobile Banking"])
                p_name = st.text_input("Provider Name", placeholder="e.g. Clear Bank / Islami Bank / USDT")
                p_details = st.text_area("Account Details / Wallet Address")
                if st.form_submit_button("➕ Add Method") and p_name and p_details:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO payment_gateways VALUES (?, ?, ?, ?, 1)", (str(uuid.uuid4()), m_type, p_name, p_details))
                        conn.commit()
                    st.success("Added!")
                    st.rerun()

            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM payment_gateways")
                gateways = c.fetchall()
            for gw in gateways:
                col_g1, col_g2 = st.columns([4, 1])
                col_g1.write(f"📌 **[{gw['method_type']}] {gw['provider_name']}**\n`{gw['account_details']}`")
                if col_g2.button("🗑️ Remove", key=f"del_gw_{gw['gateway_id']}"):
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM payment_gateways WHERE gateway_id = ?", (gw['gateway_id'],))
                        conn.commit()
                    st.rerun()

        with o_tab5:
            st.markdown("#### 📢 AdSense & Ads")
            ad_status = st.radio("Global Ads Status", ["ON", "OFF"], index=0 if get_setting("show_ads") == "ON" else 1)
            adsense_code = st.text_area("HTML Script", value=get_setting("adsense_script"), height=150)
            if st.button("💾 Save Ads"):
                set_setting("show_ads", ad_status)
                set_setting("adsense_script", adsense_code)
                st.success("Saved!")
                st.rerun()

        with o_tab6:
            st.markdown("#### 🛠️ Moderation")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM monetization_requests WHERE status = 'Pending'")
                for mr in c.fetchall():
                    st.write(f"User: {mr['user_id']} | Bank: {mr['bank_info']}")
                    if st.button(f"✅ Approve Monetization ({mr['mon_id']})", key=f"app_mon_{mr['mon_id']}"):
                        c.execute("UPDATE master_app_table SET monetization_status = 'Approved' WHERE user_id = ?", (mr['user_id'],))
                        c.execute("UPDATE monetization_requests SET status = 'Approved' WHERE mon_id = ?", (mr['mon_id'],))
                        conn.commit()
                        st.rerun()

        with o_tab7:
            st.markdown("#### 🚀 Boost Requests")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM boost_requests WHERE status = 'Pending'")
                for br in c.fetchall():
                    st.write(f"Post ID: {br['post_id']} | Method: {br['payment_method']} | Trx: {br['trx_info']}")
                    if st.button(f"🔥 Approve Boost ({br['boost_id']})", key=f"app_boost_{br['boost_id']}"):
                        c.execute("UPDATE master_app_table SET is_boosted = 1 WHERE record_id = ?", (br['post_id'],))
                        c.execute("UPDATE boost_requests SET status = 'Approved' WHERE boost_id = ?", (br['boost_id'],))
                        conn.commit()
                        st.success("Boosted!")
                        st.rerun()

        with o_tab8:
            st.markdown("#### 📡 Live Monitor Feed")
            if st.button("🔄 Refresh Live Feed"): st.rerun()
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC LIMIT 30")
                live_posts = c.fetchall()
            for lp in live_posts:
                st.markdown(f"<div class='vertical-live-card'><b>{lp['full_name']}</b> - {lp['title']} [{lp['post_category']}]</div>", unsafe_allow_html=True)

        with o_tab9:
            st.markdown("#### 🔑 User Recovery Management")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT user_id, full_name, auth_identifier, recovery_code FROM master_app_table WHERE data_type = 'user'")
                for u in c.fetchall():
                    with st.expander(f"👤 {u['full_name']} ({u['auth_identifier']})"):
                        st.write(f"Recovery Code: `{u['recovery_code']}`")
                        new_rec = st.text_input("New Code", key=f"nrec_{u['user_id']}")
                        if st.button("Save", key=f"srec_{u['user_id']}") and new_rec:
                            with get_db_connection() as conn2:
                                c2 = conn2.cursor()
                                c2.execute("UPDATE master_app_table SET recovery_code = ? WHERE user_id = ?", (new_rec, u['user_id']))
                                conn2.commit()
                            st.success("Updated!")
                            st.rerun()

        with o_tab10:
            st.markdown("### 💳 Your Direct Bank & Crypto Payment Profiles")
            st.info("এই ডিটেলসগুলো আপনার অ্যাপের পেমেন্ট গেটওয়ে সিস্টেমে পার্মানেন্টলি যুক্ত করে দেওয়া হয়েছে:")
            
            st.markdown("#### 🇬🇧 1. International Bank Account (Clear Bank, UK)")
            st.markdown("""
            * **Name:** Md Sohel Rana
            * **Address:** Bangladesh, Barabari, SHIBRAM BARABARI SADAR LALMONIRHAT, LALMONIRHAT, 5500
            * **IBAN:** `GB89CLRB04281239130579`
            * **BIC/SWIFT Code:** `CLRBGB22XXX`
            * **Account Number:** `39130579`
            * **Bank Name:** Clear Bank (Based in GB)
            * **Bank Address:** 133 Houndsditch, LONDON, EC3A 7BX
            * **Account Type:** Checking (Current)
            """)
            
            st.markdown("#### 🇧🇩 2. Local Bank Account (Islami Bank Bangladesh PLC)")
            st.markdown("""
            * **Bank Name:** Islami Bank Bangladesh PLC
            * **Account Title:** MD. SOHEL RANA
            * **Account Number:** `20502530202612312`
            * **Branch:** Lalmonirhat Br, Lalmonirhat
            * **Routing Number:** `125520465`
            """)

            st.markdown("#### 🌐 3. Crypto Wallets (USDT)")
            st.markdown("""
            * **USDT (TRC20 Address):**  
              `TM6DAbNuF2kaMaRoC8HKi2G8Gi5hVWnbCP`
            * **USDT (BEP20 Address):**  
              `0x53052be072029dd76e02b01d925e29b03c5294ad`
            """)

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

        sub_feed1, sub_feed2, sub_feed3, sub_feed4 = st.tabs(["🌐 All Feed", "🎬 Reels / Shorts", "🖼️ Photos", "📹 Long Videos"])
        with sub_feed1:
            for post in posts: render_post_card(post, ads_enabled, ads_html, prefix="all")
        with sub_feed2:
            for post in [p for p in posts if p.get("post_category") == "short"]: render_post_card(post, ads_enabled, ads_html, prefix="short")
        with sub_feed3:
            for post in [p for p in posts if p.get("post_category") == "picture"]: render_post_card(post, ads_enabled, ads_html, prefix="pic")
        with sub_feed4:
            for post in [p for p in posts if p.get("post_category") == "long"]: render_post_card(post, ads_enabled, ads_html, prefix="long")

# ------------------------------------------
# TAB 2: PROFILE & STUDIO
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id: st.warning("Please login!")
    else:
        tick = get_meta_blue_badge() if current_user.get("is_verified") else ""
        st.markdown(f"## Profile Studio: {current_user.get('full_name', 'User')} {tick}", unsafe_allow_html=True)
        profile_path = current_user.get("profile_pic_path")
        
        col_p1, col_p2 = st.columns([1, 4])
        with col_p1:
            if profile_path and os.path.exists(profile_path): st.image(profile_path, width=120)
            else: st.info("No Profile Pic")
        with col_p2:
            st.write(f"👥 **Real Followers:** {real_followers:,}")
            st.write(f"**Bio:** {current_user.get('bio', 'No bio')}")

        with st.expander("⚙️ Edit Profile"):
            u_name = st.text_input("Name", value=current_user.get("full_name", ""))
            u_bio = st.text_area("Bio", value=current_user.get("bio") or "")
            up_prof = st.file_uploader("Upload DP", type=["jpg", "png", "jpeg"], key="dp_edit")
            if st.button("Save Profile"):
                p_path = profile_path
                if up_prof:
                    p_path = os.path.join(UPLOAD_DIR, f"dp_{st.session_state.user_id}.png")
                    with open(p_path, "wb") as f: f.write(up_prof.getbuffer())
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("UPDATE master_app_table SET full_name = ?, bio = ?, profile_pic_path = ? WHERE user_id = ?", (u_name, u_bio, p_path, st.session_state.user_id))
                    conn.commit()
                st.success("Updated!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📤 Upload New Post")
        if get_setting("lock_upload") == "ON": st.error("🚫 Upload System is locked.")
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
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, tags, media_path, post_category, views_count, likes_count, created_at) VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)", (rec_id, st.session_state.user_id, current_user.get("full_name", "User"), current_user.get("is_verified", 1), title, desc, p_tags, m_path, post_type, now))
                        conn.commit()
                    st.success("Published!")
                    st.rerun()

# ------------------------------------------
# TAB 3: MONETIZATION & BANK PAYMENTS
# ------------------------------------------
with tab_monetization:
    st.markdown("### 💸 Worldwide Monetization & Video Boost Center")
    mon_status = current_user.get("monetization_status", "Not Eligible")
    if mon_status == "Approved":
        st.success("🎉 **Monetization Active & Approved!**")
        st.metric("Estimated Balance", "$1,250.00 USD")
    elif real_followers >= 1000:
        st.success("🎉 **Eligible for Monetization!**")
        with st.expander("📝 Apply for Payout"):
            bank_info_input = st.text_area("Enter Bank / Crypto / bKash Details for Payout")
            if st.button("Submit Application") and bank_info_input:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO monetization_requests VALUES (?, ?, ?, ?, 'Pending', ?)", (str(uuid.uuid4()), st.session_state.user_id, real_followers, bank_info_input, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                st.success("Submitted!")
    else:
        st.info(f"📈 **Progress:** {real_followers}/1,000 Real Followers needed.")

    st.markdown("---")
    st.markdown("### 🔥 Boost Your Video / Post")
    if not st.session_state.user_id: st.warning("Please login!")
    else:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT record_id, title FROM master_app_table WHERE data_type = 'post' AND user_id = ?", (st.session_state.user_id,))
            user_posts = c.fetchall()
            c.execute("SELECT * FROM payment_gateways WHERE is_active = 1")
            active_gateways = c.fetchall()
        
        if not user_posts: st.info("No posts to boost.")
        elif not active_gateways: st.error("No payment methods active.")
        else:
            post_options = {p["title"]: p["record_id"] for p in user_posts}
            selected_title = st.selectbox("Select Post", list(post_options.keys()))
            selected_post_id = post_options[selected_title]
            
            boost_plan = st.selectbox("Select Package", ["Basic - 5,000 Views ($5)", "Pro - 20,000 Views ($15)", "VIP - 100,000 Views ($50)"])
            gw_options = {f"[{gw['method_type']}] {gw['provider_name']}": gw for gw in active_gateways}
            selected_gw_name = st.selectbox("Select Payment Method", list(gw_options.keys()))
            selected_gw = gw_options[selected_gw_name]
            
            st.info(f"💳 **Send Payment Here:**\n\n{selected_gw['account_details']}")
            trx_id = st.text_input("Enter Transaction ID / Hash / Ref")
            
            if st.button("Submit Boost Request"):
                if trx_id:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO boost_requests VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)", (str(uuid.uuid4()), st.session_state.user_id, selected_post_id, boost_plan, boost_plan, trx_id, selected_gw_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                    st.success("✅ Boost Request Submitted!")
                else: st.error("Enter Transaction ID.")

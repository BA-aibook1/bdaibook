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

# CSS Styling
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; }
    div[data-testid="stHeader"] {
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #0e1117; z-index: 99999; border-bottom: 1px solid #222;
    }
    img { border-radius: 12px; }
    .stImage > img {
        border-radius: 50% !important; object-fit: cover !important; border: 2px solid #0064e0 !important;
    }
    .fb-post-card {
        background: #18191a; padding: 16px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #2f3031;
    }
    .video-watermark-wrapper { position: relative; }
    .video-watermark-badge {
        position: absolute; top: 12px; right: 15px; background: rgba(0, 100, 224, 0.85);
        color: white; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; z-index: 99;
    }
    .tiktok-container { max-width: 320px; margin: 0 auto; border-radius: 14px; overflow: hidden; border: 1px solid #333; }
    .announcement-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); color: white;
        padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; font-weight: bold; font-size: 13px;
    }
    .ad-container { margin-top: 10px; margin-bottom: 15px; padding: 5px; background: #0e0e10; border-radius: 8px; text-align: center; }
    .vertical-live-feed-box { max-height: 600px; overflow-y: auto; background: #121316; padding: 15px; border-radius: 12px; border: 2px solid #0064e0; }
    .vertical-live-card { background: #1e2026; border-left: 4px solid #0064e0; padding: 12px; margin-bottom: 15px; border-radius: 8px; color: #fff; }
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
                record_id TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                user_id TEXT,
                full_name TEXT,
                auth_identifier TEXT,
                password_hash TEXT,
                recovery_code TEXT,
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
        
        # dynamic recovery_code column add if missing
        try:
            c.execute("ALTER TABLE master_app_table ADD COLUMN recovery_code TEXT")
        except:
            pass

        c.execute("""
            CREATE TABLE IF NOT EXISTS boost_requests (
                boost_id TEXT PRIMARY KEY, user_id TEXT, post_id TEXT, plan TEXT, amount TEXT, trx_info TEXT, payment_method TEXT, status TEXT DEFAULT 'Pending', created_at TEXT
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS monetization_requests (
                mon_id TEXT PRIMARY KEY, user_id TEXT, followers_count INTEGER, bank_info TEXT, status TEXT DEFAULT 'Pending', created_at TEXT
            );
        """)
        c.execute("""CREATE TABLE IF NOT EXISTS follows (follower_id TEXT, following_id TEXT, PRIMARY KEY (follower_id, following_id));""")
        c.execute("""CREATE TABLE IF NOT EXISTS likes (user_id TEXT, post_id TEXT, category TEXT DEFAULT 'general', PRIMARY KEY (user_id, post_id));""")
        c.execute("""CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT);""")
        c.execute("""CREATE TABLE IF NOT EXISTS payment_gateways (gateway_id TEXT PRIMARY KEY, method_type TEXT, provider_name TEXT, account_details TEXT, is_active INTEGER DEFAULT 1);""")
        
        default_settings = {
            "app_name": "BD AI Book",
            "owner_announcement": "Welcome to BD AI Book - Next-Gen Social & Media Platform!",
            "lock_upload": "OFF", "daily_limit_mode": "OFF", "lock_login": "OFF", "logo_path": "",
            "adsense_client_id": "ca-pub-0000000000000000",
            "adsense_script": """<div style="background:#222; color:#0064e0; text-align:center; padding:10px; border:1px dashed #0064e0; border-radius:8px;">📢 <b>Ad Banner Placeholder</b></div>""",
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
        c.execute("""SELECT COUNT(*) as cnt FROM master_app_table WHERE data_type = 'post' AND user_id = ? AND post_category = ? AND created_at >= ?""", (user_id, category, twenty_four_hours_ago))
        res = c.fetchone()
        return res["cnt"] if res else 0

if "user_id" not in st.session_state: st.session_state.user_id = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

site_logo_path = get_setting("logo_path")
app_name = get_setting("app_name", "BD AI Book")
announcement = get_setting("owner_announcement", "")

top_col1, top_col2, top_col3 = st.columns([1, 3, 1])
with top_col1:
    if site_logo_path and os.path.exists(site_logo_path):
        st.image(site_logo_path, width=50)
    else:
        st.markdown("📖")

with top_col2:
    st.markdown(f"<h3 style='text-align: center; color:#0064e0; margin:0;'>{app_name}</h3>", unsafe_allow_html=True)

with top_col3:
    if st.button("👤 Profile", key="quick_profile_btn"):
        st.session_state.active_tab = 1
        st.rerun()

if announcement:
    st.markdown(f"<div class='announcement-box'>📢 {announcement}</div>", unsafe_allow_html=True)

# ==========================================
# 4. AUTHENTICATION & RECOVERY SYSTEM
# ==========================================
real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 User Auth / Recovery")

login_locked = get_setting("lock_login") == "ON"

if not st.session_state.user_id:
    if login_locked:
        st.sidebar.error("🚫 System Maintenance!")
    else:
        is_recovery = st.sidebar.checkbox("🔑 Forgot Password / Recovery Mode?")
        
        if is_recovery:
            st.sidebar.subheader(" Account Recovery")
            rec_phone = st.sidebar.text_input("Enter Registered Phone/Gmail")
            rec_code = st.sidebar.text_input("Enter 6-Digit WhatsApp/SMS Code")
            new_pass = st.sidebar.text_input("Enter New Password", type="password")
            
            if st.sidebar.button("Recover & Unlock Account"):
                if rec_phone and rec_code and new_pass:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ? AND recovery_code = ?", (rec_phone, rec_code))
                        match_user = c.fetchone()
                        
                        if match_user:
                            # Password update & Login Auto-Unlocks
                            c.execute("UPDATE master_app_table SET password_hash = ?, recovery_code = NULL WHERE user_id = ?", (hash_pass(new_pass), match_user["user_id"]))
                            conn.commit()
                            st.session_state.user_id = match_user["user_id"]
                            st.sidebar.success("🎉 Account Recovered & Logged In!")
                            st.rerun()
                        else:
                            st.sidebar.error("❌ Invalid Phone Number or Recovery Code!")
                else:
                    st.sidebar.warning("Fill in all fields!")
        else:
            auth_input = st.sidebar.text_input("Mobile Number or Gmail")
            auth_pass = st.sidebar.text_input("Password", type="password")
            
            if st.sidebar.button("Login / Register"):
                if auth_input and auth_pass:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                        usr = c.fetchone()
                        
                        if usr:
                            if usr["password_hash"] == hash_pass(auth_pass):
                                st.session_state.user_id = usr["user_id"]
                                st.sidebar.success("Logged In!")
                                st.rerun()
                            else:
                                st.sidebar.error("❌ Incorrect Password!")
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
                else:
                    st.sidebar.warning("Provide Phone/Gmail and Password!")
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
    st.sidebar.markdown(f"📱 Contact: **{current_user.get('auth_identifier', '')}**")
    st.sidebar.markdown(f"👥 Followers: **{real_followers:,}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.is_owner_session = False
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
                    if is_following: c.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, post.get("user_id")))
                    else: c.execute("INSERT OR REPLACE INTO follows VALUES (?, ?)", (st.session_state.user_id, post.get("user_id")))
                    conn.commit()
                st.rerun()

    if post.get("title"): st.subheader(post["title"])
    if post.get("content"): st.write(post["content"])
    if post.get("tags"): st.markdown(f"<span style='color:#0064e0;'>{post['tags']}</span>", unsafe_allow_html=True)

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
        else: st.warning("Login first!")

    if col_b3.button("🚀 Share", key=f"sh_{prefix}_{post['record_id']}"): st.toast("Link Copied!")
    st.markdown("</div>", unsafe_allow_html=True)

# TAB 1: FEED & OWNER PANEL
with tab_feed:
    search_input = st.text_input("🔍 Search Users, Videos, Hashtags or Secret Code...")
    
    if search_input.strip() in SECRET_CODES:
        st.session_state.is_owner_session = True
        st.success("👑 MASTER OWNER COMMAND CENTER UNLOCKED!")
        
        o_tab1, o_tab2, o_tab3, o_tab4, o_tab5, o_tab6, o_tab7, o_tab8 = st.tabs([
            "1️⃣ Global Branding", "2️⃣ Upload Control", "3️⃣ Emergency Kill-Switch", 
            "4️⃣ Dynamic Payment Methods", "5️⃣ Google AdSense Settings", 
            "6️⃣ Content Moderation", "7️⃣ Boost Requests", "8️⃣ Live Monitor Feed"
        ])
        
        with o_tab1: st.write("Branding Settings Available")
        with o_tab2: st.write("Upload Limits Available")
        with o_tab3: st.write("Kill-Switch Available")
        with o_tab4: st.write("Payment Gateways Available")
        with o_tab5: st.write("AdSense Settings Available")
        with o_tab6: st.write("Moderation Tools Available")
        with o_tab7: st.write("Boost Requests Available")

        # 8️⃣ LIVE MONITOR & RECOVERY CONTROL PANEL
        with o_tab8:
            st.markdown("#### 📡 Registered User Accounts & Live Recovery Hub")
            st.caption("এখান থেকে সকল ইউজারের ফোন নাম্বার/জিমেইল দেখতে পাবেন এবং হোয়াটসঅ্যাপে পাঠানো কোড সেট করতে পারবেন:")
            
            if st.button("🔄 Refresh User Activity"): st.rerun()
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' ORDER BY created_at DESC")
                all_registered_users = c.fetchall()

            if not all_registered_users:
                st.info("কোনো রেজিস্টার্ড ইউজার পাওয়া যায়নি।")
            else:
                st.markdown("<div class='vertical-live-feed-box'>", unsafe_allow_html=True)
                for usr in all_registered_users:
                    st.markdown(f"""
                    <div class='vertical-live-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span>👤 <b>{usr['full_name']}</b> (ID: {usr['user_id'][:8]}...)</span>
                            <span style='color:#888; font-size:12px;'>⏱️ {usr['created_at']}</span>
                        </div>
                        <div style='background: #2a2d35; padding: 6px 10px; border-radius: 6px; margin: 8px 0; border: 1px dashed #0064e0;'>
                            📱/📧 <b>Phone Number / Gmail:</b> <span style='color: #00ffcc; font-size: 16px; font-weight: bold;'>{usr['auth_identifier']}</span><br>
                            🔑 <b>Active Recovery Code:</b> <span style='color: orange;'>{usr['recovery_code'] if usr['recovery_code'] else 'None Set'}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Manual Recovery Code Set Box for Owner
                    col_rec1, col_rec2 = st.columns([3, 1])
                    set_code_input = col_rec1.text_input(f"Enter 6-Digit WhatsApp/SMS Code for {usr['full_name']}", key=f"rec_in_{usr['user_id']}")
                    if col_rec2.button("💾 Set Code", key=f"btn_rec_{usr['user_id']}"):
                        if set_code_input:
                            with get_db_connection() as conn:
                                c = conn.cursor()
                                c.execute("UPDATE master_app_table SET recovery_code = ? WHERE user_id = ?", (set_code_input, usr['user_id']))
                                conn.commit()
                            st.success(f"Recovery Code Set to {set_code_input}!")
                            st.rerun()
                        else:
                            st.warning("Enter a 6-digit code first!")
                    st.markdown("---")
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
            posts = [dict(r) for r in c.fetchall()]

        ads_enabled = get_setting("show_ads") == "ON"
        ads_html = get_setting("adsense_script")

        for post in posts:
            render_post_card(post, ads_enabled, ads_html, prefix="all")

# TAB 2: PROFILE & TAB 3: MONETIZATION
with tab_profile: st.write("Profile Page Ready")
with tab_monetization: st.write("Monetization & Boost Page Ready")

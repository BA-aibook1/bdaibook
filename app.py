import base64
from datetime import datetime, timedelta
import hashlib
import os
import sqlite3
import uuid

import streamlit as st

# ==========================================
# 1. APPLICATION CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Global Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Environment Variables
SECRET_OWNER_KEY = os.environ.get("SECRET_OWNER_KEY", "S$s123456789112233")
DATABASE_URL = os.environ.get("DATABASE_URL", None)
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", None)

LOCAL_DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"

for folder in [VIDEO_DIR, IMAGE_DIR]:
    os.makedirs(folder, exist_ok=True)

# ==========================================
# 2. DATABASE ENGINE
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

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_master_database_system():
    conn, db_type = get_db_connection()
    cursor = conn.cursor()

    if db_type == "postgresql":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(30) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                country VARCHAR(60) DEFAULT 'Global / Other',
                profile_pic_base64 TEXT,
                is_verified BOOLEAN DEFAULT TRUE,
                is_suspended BOOLEAN DEFAULT FALSE,
                suspended_until TIMESTAMP,
                watch_time_hours REAL DEFAULT 0.0,
                followers_count INT DEFAULT 0,
                is_monetized BOOLEAN DEFAULT FALSE,
                payout_method VARCHAR(50),
                payout_account_details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS posts (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(255),
                content TEXT,
                media_url TEXT,
                category VARCHAR(50) DEFAULT 'general',
                likes_count INT DEFAULT 0,
                views_count INT DEFAULT 0,
                is_published BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone_number TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                country TEXT DEFAULT 'Global / Other',
                profile_pic_base64 TEXT,
                is_verified INTEGER DEFAULT 1,
                is_suspended INTEGER DEFAULT 0,
                suspended_until TEXT,
                watch_time_hours REAL DEFAULT 0.0,
                followers_count INTEGER DEFAULT 0,
                is_monetized INTEGER DEFAULT 0,
                payout_method TEXT,
                payout_account_details TEXT,
                created_at TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                content TEXT,
                media_url TEXT,
                category TEXT DEFAULT 'general',
                likes_count INTEGER DEFAULT 0,
                views_count INTEGER DEFAULT 0,
                is_published INTEGER DEFAULT 1,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

    conn.commit()
    conn.close()

init_master_database_system()

# ==========================================
# 3. CONTENT MODERATION & USER ENGINE
# ==========================================
BANNED_KEYWORDS = ["sex", "porn", "nude", "adult", "gaalaagali", "গালাগালি", "খারাপ", "অশ্লীল", "১৮+"]

def check_ai_content_safety(text_to_check: str) -> bool:
    if not text_to_check:
        return True
    lowered = text_to_check.lower()
    return not any(word in lowered for word in BANNED_KEYWORDS)

def suspend_user_account(user_id: str, days: int = 30):
    conn, db_type = get_db_connection()
    c = conn.cursor()
    until_date = datetime.now() + timedelta(days=days)
    
    if db_type == "postgresql":
        c.execute("UPDATE users SET is_suspended = TRUE, suspended_until = %s WHERE id = %s", (until_date, user_id))
    else:
        c.execute("UPDATE users SET is_suspended = 1, suspended_until = ? WHERE id = ?", (until_date.strftime("%Y-%m-%d %H:%M:%S"), user_id))
    
    conn.commit()
    conn.close()

def is_user_suspended(user_id: str) -> tuple[bool, str]:
    if user_id == "owner_admin":
        return False, ""
        
    conn, _ = get_db_connection()
    c = conn.cursor()
    q = "SELECT is_suspended, suspended_until FROM users WHERE id = %s" if DATABASE_URL else "SELECT is_suspended, suspended_until FROM users WHERE id = ?"
    c.execute(q, (user_id,))
    usr = c.fetchone()
    conn.close()

    if not usr or not usr["is_suspended"]:
        return False, ""

    until_dt = datetime.strptime(usr["suspended_until"], "%Y-%m-%d %H:%M:%S") if isinstance(usr["suspended_until"], str) else usr["suspended_until"]

    if datetime.now() < until_dt:
        return True, until_dt.strftime("%b %d, %Y")
    return False, ""

def get_daily_upload_count(user_id: str, category: str) -> int:
    conn, _ = get_db_connection()
    c = conn.cursor()
    one_day_ago = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    q = "SELECT COUNT(*) as cnt FROM posts WHERE user_id = %s AND category = %s AND created_at >= %s" if DATABASE_URL else "SELECT COUNT(*) as cnt FROM posts WHERE user_id = ? AND category = ? AND created_at >= ?"
    c.execute(q, (user_id, category, one_day_ago))
    res = c.fetchone()
    conn.close()
    return res["cnt"] if res else 0

# ==========================================
# 4. STORAGE & MONETIZATION ENGINE
# ==========================================
def save_media_file(uploaded_file, file_prefix, extension):
    filename = f"{file_prefix}{extension}"
    if GCS_BUCKET_NAME:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET_NAME)
            blob = bucket.blob(filename)
            blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
            return blob.public_url
        except Exception as e:
            st.error(f"Cloud Storage Error: {e}")
            return ""
    else:
        target_dir = IMAGE_DIR if extension in [".jpg", ".png", ".jpeg"] else VIDEO_DIR
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filepath

def check_and_update_monetization(user_id: str):
    if user_id == "owner_admin":
        return
    conn, db_type = get_db_connection()
    c = conn.cursor()
    q = "SELECT watch_time_hours, followers_count, is_monetized FROM users WHERE id = %s" if DATABASE_URL else "SELECT watch_time_hours, followers_count, is_monetized FROM users WHERE id = ?"
    c.execute(q, (user_id,))
    usr = c.fetchone()

    if usr and not usr["is_monetized"] and (usr["watch_time_hours"] or 0) >= 3000.0 and (usr["followers_count"] or 0) >= 300:
        up_q = "UPDATE users SET is_monetized = TRUE WHERE id = %s" if db_type == "postgresql" else "UPDATE users SET is_monetized = 1 WHERE id = ?"
        c.execute(up_q, (user_id,))
        conn.commit()
    conn.close()

# ==========================================
# 5. UI COMPONENTS & RENDERING
# ==========================================
ALLOWED_COUNTRIES = ["United States", "United Kingdom", "Canada", "Australia", "India", "Bangladesh", "Global / Other"]
PAYMENT_METHODS = ["bKash (বাংলাদেশ)", "Nagad (বাংলাদেশ)", "PayPal (International)", "Mastercard / Visa Card"]

def show_verified_profile(user_id, subtitle="Member"):
    conn, _ = get_db_connection()
    c = conn.cursor()
    q = "SELECT full_name, is_verified, country, profile_pic_base64, is_monetized FROM users WHERE id = %s" if DATABASE_URL else "SELECT full_name, is_verified, country, profile_pic_base64, is_monetized FROM users WHERE id = ?"
    c.execute(q, (user_id,))
    u_data = c.fetchone()
    conn.close()
    
    display_name = u_data["full_name"] if u_data else "Global User"
    user_country = u_data["country"] if u_data and u_data["country"] else "Global HQ"
    b64_img = u_data["profile_pic_base64"] if u_data and u_data["profile_pic_base64"] else None
    
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:40px; height:40px; border-radius:50%; object-fit:cover;">' if b64_img else '<div style="width:40px; height:40px; border-radius:50%; background:#333; color:#fff; display:flex; align-items:center; justify-content:center;">👤</div>'
    monetized_badge = '<span style="background:#ffd700; color:#000; font-size:10px; font-weight:bold; padding:2px 5px; border-radius:4px; margin-left:6px;">💰 MONETIZED</span>' if u_data and u_data["is_monetized"] else ''
    
    card_html = f"""<div style="display:flex; align-items:center; gap:10px; background: #1e1e1e; padding: 8px 12px; border-radius: 8px; margin-bottom: 10px;">
        {img_html}
        <div>
            <div style="font-weight:bold; color:#fff; font-size: 14px;">{display_name} {monetized_badge}</div>
            <div style="color:#aaa; font-size:11px;">{subtitle} • 🌐 {user_country}</div>
        </div>
    </div>"""
    st.markdown(card_html, unsafe_allow_html=True)

# Custom Styling
st.markdown("<style>.stApp { background-color: #121212; color: #e4e6eb; } .feed-card { background: #1e1e1e; border-radius: 10px; padding: 15px; margin-bottom: 15px; }</style>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #00c853;'>🛡️ Global AI Book Enterprise Platform 🛡️</h2>", unsafe_allow_html=True)
st.divider()

# Session States
if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "active_tab" not in st.session_state: st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 6. SIDEBAR & AUTHENTICATION
# ==========================================
st.sidebar.markdown("### 🔍 System Access")
search_query = st.sidebar.text_input("Passcode / Search...", key="search_query")

if search_query.strip() == SECRET_OWNER_KEY:
    st.session_state.user_id = "owner_admin"
    st.session_state.user_name = "System Owner"
    st.session_state.active_tab = "👑 Owner Control Center"

st.sidebar.markdown("---")
mode = st.sidebar.radio("Select Access Mode", ["📱 Secure Login", "📝 New Registration"])

if mode == "📱 Secure Login":
    login_phone = st.sidebar.text_input("Mobile Number")
    login_pass = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        if login_phone.strip() and login_pass:
            conn, _ = get_db_connection()
            c = conn.cursor()
            q = "SELECT * FROM users WHERE phone_number = %s AND password_hash = %s" if DATABASE_URL else "SELECT * FROM users WHERE phone_number = ? AND password_hash = ?"
            c.execute(q, (login_phone.strip(), hash_password(login_pass)))
            usr = c.fetchone()
            conn.close()
            
            if usr:
                st.session_state.user_id = usr["id"]
                st.session_state.user_name = usr["full_name"]
                st.sidebar.success(f"✅ Welcome {usr['full_name']}!")
                check_and_update_monetization(usr["id"])
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid Credentials!")

elif mode == "📝 New Registration":
    reg_name = st.sidebar.text_input("Full Name")
    reg_phone = st.sidebar.text_input("Mobile Number")
    reg_pass = st.sidebar.text_input("Password", type="password")
    reg_country = st.sidebar.selectbox("Country", ALLOWED_COUNTRIES)
    
    if st.sidebar.button("Register Account"):
        if reg_name and reg_phone and reg_pass:
            user_uuid = str(uuid.uuid4())
            conn, db_type = get_db_connection()
            c = conn.cursor()
            try:
                q = "INSERT INTO users (id, full_name, phone_number, password_hash, country, created_at) VALUES (%s, %s, %s, %s, %s, %s)" if db_type == "postgresql" else "INSERT INTO users (id, full_name, phone_number, password_hash, country, created_at) VALUES (?, ?, ?, ?, ?, ?)"
                c.execute(q, (user_uuid, reg_name, reg_phone, hash_password(reg_pass), reg_country, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.session_state.user_id = user_uuid
                st.session_state.user_name = reg_name
                st.sidebar.success("🎉 Account created!")
                st.rerun()
            except Exception:
                st.sidebar.error("❌ Phone number already registered!")
            finally:
                conn.close()

if st.session_state.user_id:
    st.sidebar.markdown(f"Authenticated: **{st.session_state.user_name}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id, st.session_state.user_name = None, None
        st.session_state.active_tab = "🌍 World Feed"
        st.rerun()

nav_tabs = ["🌍 World Feed", "📱 TikTok Shorts Feed", "📺 Direct Long Videos", "📤 Upload Studio", "💵 Monetization Hub"]
if st.session_state.user_id == "owner_admin":
    nav_tabs.append("👑 Owner Control Center")

current_index = nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0
tab = st.sidebar.radio("Navigation", nav_tabs, index=current_index)
st.session_state.active_tab = tab

# ==========================================
# 7. CONTENT FEEDS & UPLOAD STUDIO
# ==========================================
if tab == "🌍 World Feed":
    st.markdown("### 🌍 World Feed")
    conn, _ = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE category = 'general' AND is_published = TRUE ORDER BY created_at DESC" if DATABASE_URL else "SELECT * FROM posts WHERE category = 'general' AND is_published = 1 ORDER BY created_at DESC")
    posts = [dict(r) for r in c.fetchall()]
    conn.close()

    for item in posts:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(item["user_id"], subtitle=f"Posted {item.get('created_at')}")
        if item.get("title"): st.markdown(f"#### {item['title']}")
        st.write(item.get("content", ""))
        if item.get("media_url"): st.image(item["media_url"], use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif tab in ["📱 TikTok Shorts Feed", "📺 Direct Long Videos"]:
    cat_type = "short" if tab == "📱 TikTok Shorts Feed" else "long"
    st.markdown(f"### {'📱 TikTok Shorts Feed' if cat_type == 'short' else '📺 Direct Long Videos'}")
    
    conn, _ = get_db_connection()
    c = conn.cursor()
    q = "SELECT * FROM posts WHERE category = %s AND is_published = TRUE ORDER BY created_at DESC" if DATABASE_URL else "SELECT * FROM posts WHERE category = ? AND is_published = 1 ORDER BY created_at DESC"
    c.execute(q, (cat_type,))
    vids = [dict(r) for r in c.fetchall()]
    conn.close()

    for vid in vids:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        show_verified_profile(vid["user_id"], subtitle=f"Uploaded {vid.get('created_at')}")
        if vid.get("title"): st.subheader(vid['title'])
        st.write(vid.get('content', ''))
        if vid.get("media_url"): st.video(vid["media_url"])
        st.markdown('</div>', unsafe_allow_html=True)

elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Upload Studio")
    if not st.session_state.user_id:
        st.warning("⚠️ Please login to publish content.")
    else:
        suspended, until_date = is_user_suspended(st.session_state.user_id)
        if suspended:
            st.error(f"🚫 ACCOUNT SUSPENDED UNTIL {until_date} (Community Policy Violation).")
        else:
            cat = st.selectbox("Category", ["General Post (Photo/Text)", "TikTok Short Video", "Direct Long Video"])
            title_in = st.text_input("Title")
            desc_in = st.text_area("Description")
            post_uuid = str(uuid.uuid4())
            created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if cat == "General Post (Photo/Text)":
                f_up = st.file_uploader("Select Photo", type=["jpg", "png", "jpeg"])
                if st.button("Publish Post"):
                    if not check_ai_content_safety(title_in) or not check_ai_content_safety(desc_in):
                        suspend_user_account(st.session_state.user_id, days=30)
                        st.error("🚨 Violating Content Detected! Account suspended for 30 days.")
                        st.rerun()
                    elif get_daily_upload_count(st.session_state.user_id, "general") >= 15:
                        st.warning("⚠️ Daily limit reached (Max 15 posts).")
                    else:
                        media_link = save_media_file(f_up, post_uuid, ".jpg") if f_up else ""
                        conn, db_type = get_db_connection()
                        c = conn.cursor()
                        q = "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (%s, %s, %s, %s, %s, 'general', %s)" if db_type == "postgresql" else "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (?, ?, ?, ?, ?, 'general', ?)"
                        c.execute(q, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, created_time))
                        conn.commit()
                        conn.close()
                        st.success("✅ Post published!")
                        st.rerun()
            else:
                cat_code = "short" if cat == "TikTok Short Video" else "long"
                v_up = st.file_uploader("Select Video", type=["mp4", "mov"])
                if st.button("Publish Video"):
                    if not v_up:
                        st.warning("⚠️ Please attach a video file.")
                    elif not check_ai_content_safety(title_in) or not check_ai_content_safety(desc_in):
                        suspend_user_account(st.session_state.user_id, days=30)
                        st.error("🚨 Bad Content Detected! Account suspended.")
                        st.rerun()
                    elif get_daily_upload_count(st.session_state.user_id, cat_code) >= 1:
                        st.warning("⚠️ Daily limit reached (Max 1 video per day).")
                    else:
                        media_link = save_media_file(v_up, post_uuid, ".mp4")
                        conn, db_type = get_db_connection()
                        c = conn.cursor()
                        q = "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)" if db_type == "postgresql" else "INSERT INTO posts (id, user_id, title, content, media_url, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                        c.execute(q, (post_uuid, st.session_state.user_id, title_in, desc_in, media_link, cat_code, created_time))
                        conn.commit()
                        conn.close()
                        st.success("✅ Video uploaded successfully!")
                        st.rerun()

elif tab == "💵 Monetization Hub":
    st.markdown("### 💵 Monetization Hub")
    if not st.session_state.user_id:
        st.warning("⚠️ Please log in.")
    elif st.session_state.user_id == "owner_admin":
        st.info("👑 Owner Account — Monetization Active.")
    else:
        conn, _ = get_db_connection()
        c = conn.cursor()
        q = "SELECT watch_time_hours, followers_count, is_monetized, payout_method, payout_account_details FROM users WHERE id = %s" if DATABASE_URL else "SELECT watch_time_hours, followers_count, is_monetized, payout_method, payout_account_details FROM users WHERE id = ?"
        c.execute(q, (st.session_state.user_id,))
        u_info = c.fetchone()
        conn.close()

        w_hours = u_info["watch_time_hours"] if u_info and u_info["watch_time_hours"] else 0.0
        followers = u_info["followers_count"] if u_info and u_info["followers_count"] else 0
        is_monetized = u_info["is_monetized"] if u_info else False

        col1, col2 = st.columns(2)
        with col1:
            st.metric("⏱️ Watch Time (Goal: 3,000 Hours)", f"{w_hours:.1f} Hours")
            st.progress(min(w_hours / 3000.0, 1.0))
        with col2:
            st.metric("👥 Followers (Goal: 300)", f"{followers}")
            st.progress(min(followers / 300.0, 1.0))

        if is_monetized or (w_hours >= 3000.0 and followers >= 300):
            st.success("🎉 **MONETIZATION APPROVED!**")
            p_method = st.selectbox("Payout Method", PAYMENT_METHODS)
            p_details = st.text_input("Account Details", value=u_info["payout_account_details"] if u_info else "")
            if st.button("Save Settings"):
                conn, db_type = get_db_connection()
                c = conn.cursor()
                q = "UPDATE users SET payout_method = %s, payout_account_details = %s, is_monetized = TRUE WHERE id = %s" if db_type == "postgresql" else "UPDATE users SET payout_method = ?, payout_account_details = ?, is_monetized = 1 WHERE id = ?"
                c.execute(q, (p_method, p_details, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("✅ Saved!")
                st.rerun()

elif tab == "👑 Owner Control Center":
    st.markdown("### 👑 Master Control Center")
    st.success("Authenticated as Platform Owner!")

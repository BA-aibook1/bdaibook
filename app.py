import os
import sqlite3
import uuid
import hashlib
import random
import json
import base64
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 0. SECURITY & ENVIRONMENT CONFIGURATION
# ==========================================
NEW_OWNER_SECRET_KEY = os.getenv("OWNER_SECRET", "S$s123456789112233BDAIBOOK@MDSOHELRANA")
SECRET_CODES = [NEW_OWNER_SECRET_KEY]

# ==========================================
# AUTO VIDEO COMPRESSION ENGINE
# ==========================================
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

def compress_video_automatically(input_path, output_path):
    """
    Auto compression logic to reduce large video size (MB) and ensure fast upload.
    """
    if not MOVIEPY_AVAILABLE:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            f_out.write(f_in.read())
        return output_path

    try:
        clip = VideoFileClip(input_path)
        if clip.size[1] > 720:
            clip = clip.resize(height=720)
        
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            bitrate="1000k",
            preset="ultrafast",
            logger=None
        )
        clip.close()
        return output_path
    except Exception as e:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            f_out.write(f_in.read())
        return output_path

# ==========================================
# GOOGLE VISION AI AUTO-MODERATION ENGINE
# ==========================================
try:
    from google.cloud import vision
    VISION_AI_AVAILABLE = True
except ImportError:
    VISION_AI_AVAILABLE = False

def check_image_safety_with_ai(image_path):
    if not VISION_AI_AVAILABLE:
        return True, "Vision AI Library Not Installed"
    
    try:
        client = vision.ImageAnnotatorClient()
        with open(image_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.safe_search_detection(image=image)
        safe = response.safe_search_annotation

        if safe.adult >= 4 or safe.violence >= 4 or safe.racy >= 4:
            return False, "Inappropriate Content Detected by AI (Adult/Violence/Racy)"
        return True, "Safe"
    except Exception as e:
        return True, f"AI Check Skipped/Error: {str(e)}"

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

AUTO_VAULT_BASE = "app_vault_storage"
PERIOD_1_DIR = os.path.join(AUTO_VAULT_BASE, "days_1_to_15")
PERIOD_2_DIR = os.path.join(AUTO_VAULT_BASE, "days_16_to_30")

os.makedirs(PERIOD_1_DIR, exist_ok=True)
os.makedirs(PERIOD_2_DIR, exist_ok=True)

LOCAL_DB_FILE = "bd_ai_book_master.db"
BANNED_KEYWORDS = ["nude", "sex", "adult", "porn", "xrated", "18+"]

def get_db_connection():
    conn = sqlite3.connect(LOCAL_DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def save_to_internal_vault(data_dict):
    try:
        now = datetime.now()
        day = now.day
        target_dir = PERIOD_1_DIR if 1 <= day <= 15 else PERIOD_2_DIR
        
        file_id = str(uuid.uuid4())[:8]
        file_name = f"vault_{now.strftime('%Y%m%d_%H%M%S')}_{file_id}.json"
        file_path = os.path.join(target_dir, file_name)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def auto_restore_from_internal_vault():
    restored_count = 0
    for folder in [PERIOD_1_DIR, PERIOD_2_DIR]:
        if not os.path.exists(folder):
            continue
        for file in os.listdir(folder):
            if file.endswith(".json"):
                fp = os.path.join(folder, file)
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            keys = [k for k in data.keys() if k in [
                                'record_id', 'data_type', 'user_id', 'full_name', 'auth_identifier',
                                'password_hash', 'address', 'bio', 'profile_pic_path', 'cover_pic_path',
                                'fb_link', 'tiktok_link', 'yt_link', 'website_link', 'followers_count',
                                'is_verified', 'violation_count', 'is_suspended', 'suspended_until',
                                'title', 'content', 'tags', 'media_path', 'post_category', 'likes_count',
                                'views_count', 'is_boosted', 'monetization_status', 'country',
                                'is_owner_post', 'created_at', 'recovery_code', 'user_status', 'meta_bluetooth_permission',
                                'user_role'
                            ]]
                            values = [data[k] for k in keys]
                            placeholders = ", ".join(["?"] * len(keys))
                            cols = ", ".join(keys)
                            c.execute(f"INSERT OR REPLACE INTO master_app_table ({cols}) VALUES ({placeholders})", values)
                            conn.commit()
                            restored_count += 1
                except Exception:
                    pass
    return restored_count

# ==========================================
# MODERN UI / CSS ENHANCEMENTS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .block-container { 
        padding-top: 1.5rem !important; 
        max-width: 1200px;
    }
    div[data-testid="stHeader"] {
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: rgba(14, 17, 23, 0.95);
        backdrop-filter: blur(10px);
        z-index: 99999; border-bottom: 1px solid #1f2937;
    }
    
    .app-header-title {
        color: #1877F2 !important;
        font-weight: 800;
        font-size: 1.8rem;
        text-align: center;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    img { border-radius: 12px; }
    .stImage > img {
        border-radius: 50% !important; 
        object-fit: cover !important; 
        border: 2px solid #1877F2 !important;
        box-shadow: 0 4px 12px rgba(24, 119, 242, 0.25);
    }
    
    .fb-post-card {
        background: #111827; 
        padding: 20px; 
        border-radius: 16px; 
        margin-bottom: 24px; 
        border: 1px solid #1f2937;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .fb-post-card:hover {
        border-color: #374151;
    }
    
    .video-watermark-wrapper { position: relative; border-radius: 12px; overflow: hidden; }
    .video-watermark-badge {
        position: absolute; top: 12px; right: 15px; 
        background: rgba(24, 119, 242, 0.9);
        backdrop-filter: blur(4px);
        color: white; padding: 4px 12px; border-radius: 20px; 
        font-size: 11px; font-weight: 700; z-index: 99; pointer-events: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .tiktok-container { 
        max-width: 380px; margin: 0 auto; border-radius: 16px; 
        overflow: hidden; border: 1px solid #1f2937; background: #000; 
    }
    .announcement-box {
        background: linear-gradient(135deg, #1877F2 0%, #0d5cb6 100%); 
        color: #ffffff; padding: 12px 20px; border-radius: 12px; 
        text-align: center; margin-bottom: 20px; font-weight: 600; font-size: 14px;
        box-shadow: 0 4px 12px rgba(24, 119, 242, 0.25);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .ad-container { 
        margin-top: 15px; margin-bottom: 15px; padding: 12px; 
        background: #0b0f17; border-radius: 12px; text-align: center; 
        border: 1px dashed #374151;
    }
    .vertical-live-feed-box { 
        max-height: 600px; overflow-y: auto; background: #0b0f17; 
        padding: 18px; border-radius: 16px; border: 1px solid #1f2937; 
    }
    .vertical-live-card { 
        background: #111827; border-left: 4px solid #1877F2; 
        padding: 14px; margin-bottom: 15px; border-radius: 8px; color: #fff; 
    }
    .duplicate-card { 
        background: #1f1315; border-left: 4px solid #ef4444; 
        padding: 14px; margin-bottom: 12px; border-radius: 8px; color: #fff; 
    }
    .meta-control-box { 
        background: #0d1527; border: 1px solid #1877F2; 
        padding: 20px; border-radius: 16px; margin-bottom: 20px; 
    }

    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MASTER DATABASE ENGINE & CONFIG SYSTEM
# ==========================================
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
        
        # Schema Alterations
        for col_def in [
            ("recovery_code", "TEXT"),
            ("user_status", "TEXT DEFAULT 'REAL'"),
            ("meta_bluetooth_permission", "INTEGER DEFAULT 0"),
            ("user_role", "TEXT DEFAULT 'EMPLOYEE'") # Role Management Schema Addition
        ]:
            try:
                c.execute(f"ALTER TABLE master_app_table ADD COLUMN {col_def[0]} {col_def[1]}")
            except sqlite3.OperationalError:
                pass

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

        c.execute("""
            CREATE TABLE IF NOT EXISTS sponsor_video_requests (
                request_id TEXT PRIMARY KEY,
                user_id TEXT,
                sponsor_name TEXT,
                trx_id_10digit TEXT,
                bank_details_used TEXT,
                video_link TEXT,
                video_file_path TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT
            );
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS music_library (
                song_id TEXT PRIMARY KEY,
                title TEXT,
                artist TEXT,
                file_path TEXT,
                created_at TEXT
            );
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS amazon_products (
                product_id TEXT PRIMARY KEY,
                title TEXT,
                price TEXT,
                affiliate_link TEXT,
                image_url TEXT,
                category TEXT,
                created_at TEXT
            );
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_messages (
                msg_id TEXT PRIMARY KEY,
                sender_id TEXT,
                receiver_id TEXT,
                message TEXT,
                media_path TEXT,
                created_at TEXT
            );
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS owner_uploads (
                upload_id TEXT PRIMARY KEY,
                user_id TEXT,
                user_name TEXT,
                note TEXT,
                file_path TEXT,
                created_at TEXT
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
            "adsense_script": """<div style="background:#222; color:#fff; text-align:center; padding:15px; border:1px dashed #1877F2; border-radius:8px;">📢 <b>Google AdSense Banner Placeholder</b><br><small>Replace code in Owner Panel</small></div>""",
            "show_ads": "ON",
            "global_notify_msg": "System Active Globally",
            "auto_duplicate_detector": "ON",
            "site_verification_code": "",
            "is_global_meta_active": "true",
            "meta_mode": "SELECTED_USERS"
        }
        
        for k, v in default_settings.items():
            c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, str(v)))

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

site_ver_code = get_setting("site_verification_code")
if site_ver_code:
    components.html(f"<head>{site_ver_code}</head>", height=0, width=0)

def hash_pass(pwd): 
    return hashlib.sha256(pwd.encode()).hexdigest()

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px; display: inline-block; flex-shrink: 0;">
        <path fill="#1877F2" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.668.258-.955.088-2.025-.508-2.822-.797-.797-1.867-.967-2.822-.508C16.31 4.233 14.94 3.5 13.36 3.5c-1.58 0-2.95.875-3.668 2.148-.955-.258-2.025-.088-2.822.508-.797.797-.967 1.867-.508 2.822C5.108 9.69 4.375 11.06 4.375 12.64c0 1.58.875 2.95 2.148 3.668-.258.955-.088 2.025.508 2.822.797.797 1.867.967 2.822.508 1.16 1.13 2.53 1.863 4.11 1.863 1.58 0 2.95-.875 3.668-2.148.955.258 2.025.088 2.822-.508.797-.797.967-1.867.508-2.822 1.273-.718 2.048-2.088 2.048-3.668z"/>
        <path fill="#FFFFFF" d="M10.25 15.75l-3.5-3.5 1.41-1.41 2.09 2.08 5.67-5.67 1.41 1.41z"/>
    </svg>"""

def increment_views(post_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE master_app_table SET views_count = views_count + 1 WHERE record_id = ?", (post_id,))
        conn.commit()

def check_user_meta_bluetooth_permission(user_id):
    is_global_active = get_setting("is_global_meta_active", "true") == "true"
    if not is_global_active:
        return False
    
    meta_mode = get_setting("meta_mode", "SELECTED_USERS")
    if meta_mode == "DISABLED":
        return False
    elif meta_mode == "ALL":
        return True
    elif meta_mode == "SELECTED_USERS":
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT meta_bluetooth_permission FROM master_app_table WHERE user_id = ? AND data_type = 'user'", (user_id,))
            res = c.fetchone()
            if res and res["meta_bluetooth_permission"] == 1:
                return True
    return False

if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False
if "user_role" not in st.session_state: st.session_state.user_role = "EMPLOYEE"
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

site_logo_path = get_setting("logo_path")
app_name = get_setting("app_name", "BD AI Book")
announcement = get_setting("owner_announcement", "")

top_col1, top_col2, top_col3 = st.columns([1, 3, 1])
with top_col1:
    if site_logo_path and os.path.exists(site_logo_path):
        st.image(site_logo_path, width=50)
    else:
        st.markdown("<h2 style='margin:0;'>📖</h2>", unsafe_allow_html=True)

with top_col2:
    st.markdown(f"<h3 class='app-header-title'>{app_name}</h3>", unsafe_allow_html=True)

with top_col3:
    if st.button("👤 Profile", key="quick_profile_btn", use_container_width=True):
        st.session_state.active_tab = 1
        st.rerun()

if announcement:
    st.markdown(f"<div class='announcement-box'>📢 {announcement}</div>", unsafe_allow_html=True)

real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 Authentication Panel")
login_locked = get_setting("lock_login") == "ON"

if not st.session_state.user_id:
    if login_locked:
        st.sidebar.error("🚫 Login System is temporarily locked by Owner for maintenance!")
    else:
        auth_input = st.sidebar.text_input("Phone Number or Gmail")
        auth_pass = st.sidebar.text_input("Password", type="password")
        
        is_recovery_mode = st.sidebar.checkbox("🔑 Account Recovery Mode?")
        
        if is_recovery_mode:
            rec_code_inp = st.sidebar.text_input("Recovery Code")
            new_pass_inp = st.sidebar.text_input("New Password", type="password")
            if st.sidebar.button("Reset Password", use_container_width=True):
                if auth_input and rec_code_inp and new_pass_inp:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ? AND recovery_code = ?", (auth_input, rec_code_inp))
                        usr_rec = c.fetchone()
                        if usr_rec:
                            c.execute("UPDATE master_app_table SET password_hash = ? WHERE user_id = ?", (hash_pass(new_pass_inp), usr_rec['user_id']))
                            conn.commit()
                            st.sidebar.success("Password Reset Success! Login with new password.")
                        else:
                            st.sidebar.error("Invalid Identifier or Recovery Code!")
                else:
                    st.sidebar.warning("Fill all details.")
        else:
            if st.sidebar.button("Send OTP", use_container_width=True):
                if auth_input and auth_pass:
                    generated_otp = str(random.randint(100000, 999999))
                    st.session_state.otp_code = generated_otp
                    st.sidebar.success(f"🔑 Auto Verification Code: **{generated_otp}**")
                else:
                    st.sidebar.warning("Please provide both Gmail/Phone and Password!")
                    
            if st.session_state.otp_code:
                user_otp = st.sidebar.text_input("Enter 6-Digit OTP Code")
                if st.sidebar.button("Verify & Proceed", use_container_width=True):
                    if user_otp == st.session_state.otp_code:
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                            usr = c.fetchone()
                            
                            if usr:
                                if usr["password_hash"] == hash_pass(auth_pass):
                                    st.session_state.user_id = usr["user_id"]
                                    st.session_state.user_role = usr["user_role"] if "user_role" in usr.keys() and usr["user_role"] else "EMPLOYEE"
                                    if st.session_state.user_role == "OWNER":
                                        st.session_state.is_owner_session = True
                                    st.sidebar.success("Logged In Successfully!")
                                    st.rerun()
                                else:
                                    st.sidebar.error("❌ Invalid Password!")
                            else:
                                new_uid = str(uuid.uuid4())
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                role = "EMPLOYEE"
                                
                                user_data_map = {
                                    "record_id": new_uid,
                                    "data_type": "user",
                                    "user_id": new_uid,
                                    "full_name": f"User_{new_uid[:4]}",
                                    "auth_identifier": auth_input,
                                    "password_hash": hash_pass(auth_pass),
                                    "is_verified": 1,
                                    "user_status": "REAL",
                                    "meta_bluetooth_permission": 0,
                                    "user_role": role,
                                    "created_at": now
                                }

                                c.execute("""
                                    INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, user_status, meta_bluetooth_permission, user_role, created_at)
                                    VALUES (?, 'user', ?, ?, ?, ?, 1, 'REAL', 0, ?, ?)
                                """, (new_uid, new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), role, now))
                                conn.commit()
                                
                                save_to_internal_vault(user_data_map)
                                st.session_state.user_id = new_uid
                                st.session_state.user_role = role
                                st.sidebar.success("Registered & Logged In!")
                                st.rerun()
                    else:
                        st.sidebar.error("❌ Invalid OTP Code!")
else:
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
        raw_user = c.fetchone()
        
        c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (st.session_state.user_id,))
        f_res = c.fetchone()
        real_followers = f_res["cnt"] if f_res else 0
        
        current_user = dict(raw_user) if raw_user else {}
        if current_user.get("user_role"):
            st.session_state.user_role = current_user.get("user_role")
    
    if current_user.get("is_suspended"):
        sus_until = current_user.get("suspended_until", "")
        if datetime.now().strftime("%Y-%m-%d %H:%M:%S") < sus_until:
            st.error(f"🚫 Account Suspended until: {sus_until}")
            st.stop()

    st.sidebar.markdown(f"User: **{current_user.get('full_name', 'User')}**")
    st.sidebar.markdown(f"🎭 Current Role: **{st.session_state.user_role}**")
    st.sidebar.markdown(f"👥 Real Followers: **{real_followers:,}**")
    
    user_bt_permission = check_user_meta_bluetooth_permission(st.session_state.user_id)
    if user_bt_permission:
        st.sidebar.success("🔵 Meta Bluetooth Access: ACTIVE")
    else:
        st.sidebar.info("🔴 Meta Bluetooth Access: DISABLED")

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.is_owner_session = False
        st.session_state.user_role = "EMPLOYEE"
        st.session_state.otp_code = None
        st.rerun()

tab_feed, tab_profile, tab_messages, tab_monetization = st.tabs([
    "📺 Public Live Feed", 
    "👤 Profile & Studio", 
    "💬 Messages & Chat", 
    "🌍 Global Monetization & Boost"
])

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
            if author_pic: 
                st.image(author_pic, width=50)
            else:
                st.markdown("<div style='font-size:2rem;'>👤</div>", unsafe_allow_html=True)
        with col_info:
            tick = get_meta_blue_badge() if post.get("is_verified") else ""
            boost_badge = "🔥 [BOOSTED]" if post.get("is_boosted") else ""
            st.markdown(f"<div style='display: flex; align-items: center; flex-wrap: wrap;'><b>{post.get('full_name')}</b>{tick} <span style='color:orange; margin-left: 6px;'>{boost_badge}</span></div>", unsafe_allow_html=True)
            st.caption(f"👥 Followers: {author_followers:,} | Category: {post.get('post_category')}")
        
    with col_h2:
        if st.session_state.user_id and st.session_state.user_id != post.get("user_id"):
            fol_lbl = "✔ Following" if is_following else "➕ Follow"
            if st.button(fol_lbl, key=f"fol_{prefix}_{post['record_id']}", use_container_width=True):
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
    if post.get("tags"): st.markdown(f"<span style='color:#1877F2;'>{post['tags']}</span>", unsafe_allow_html=True)

    if st.session_state.user_id and st.session_state.user_id == post.get("user_id"):
        with st.expander("✏ Edit or Delete Post"):
            new_title = st.text_input("Edit Title", value=post.get("title", ""), key=f"et_{prefix}_{post['record_id']}")
            new_content = st.text_area("Edit Description", value=post.get("content", ""), key=f"ec_{prefix}_{post['record_id']}")
            
            col_ed1, col_ed2 = st.columns(2)
            if col_ed1.button("💾 Save Changes", key=f"save_{prefix}_{post['record_id']}", use_container_width=True):
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("UPDATE master_app_table SET title = ?, content = ? WHERE record_id = ?", (new_title, new_content, post["record_id"]))
                    conn.commit()
                st.success("Post updated successfully!")
                st.rerun()
                
            if col_ed2.button("🗑 Delete Post", key=f"del_{prefix}_{post['record_id']}", use_container_width=True):
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (post["record_id"],))
                    conn.commit()
                st.success("Post deleted!")
                st.rerun()

    media_path = post.get("media_path")
    cat = post.get("post_category", "general")
    
    if media_path and cat != "text":
        if media_path.startswith("http://") or media_path.startswith("https://"):
            st.video(media_path)
        elif os.path.exists(media_path):
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

    st.markdown("<hr style='margin:12px 0; border-color:#1f2937;'>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.write(f"👁️ **{(post.get('views_count', 0) + 1):,}** Views")
    
    like_lbl = f"❤ Liked ({real_likes})" if has_liked else f"👍 Like ({real_likes})"
    if col_b2.button(like_lbl, key=f"lk_{prefix}_{post['record_id']}", use_container_width=True):
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

    if col_b3.button("🚀 Share", key=f"sh_{prefix}_{post['record_id']}", use_container_width=True):
        st.toast("Sharing Link Copied!")
        
    st.markdown("</div>", unsafe_allow_html=True)

with tab_feed:
    search_input = st.text_input("🔍 Search Users, Videos, Hashtags or Secret Code...")
    
    if search_input.strip() in SECRET_CODES:
        st.session_state.is_owner_session = True
        st.session_state.user_role = "OWNER"
        st.success("👑 MASTER OWNER COMMAND CENTER UNLOCKED!")
        st.markdown("---")

    # ROLE-BASED VISIBILITY FILTERING (OWNER VS EMPLOYEE)
    st.markdown("### 👁️ Content & Data Filtering Engine")
    
    if st.session_state.user_role == "OWNER" or st.session_state.is_owner_session:
        view_filter = st.selectbox(
            "👑 Select View Scope (Owner Mode)", 
            ["ALL (OWNER VIEW - FULL CONTROL)", "EMPLOYEE ONLY VIEW", "OWNER ONLY VIEW"]
        )
    else:
        view_filter = "EMPLOYEE ONLY VIEW"
        st.info("🔒 Employee Mode Active: You can see all Employee content and your own postings.")

    # Execute DB query according to the role filter
    with get_db_connection() as conn:
        c = conn.cursor()
        
        if view_filter == "ALL (OWNER VIEW - FULL CONTROL)":
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC")
        elif view_filter == "EMPLOYEE ONLY VIEW":
            c.execute("""
                SELECT p.* FROM master_app_table p 
                LEFT JOIN master_app_table u ON p.user_id = u.user_id AND u.data_type = 'user'
                WHERE p.data_type = 'post' AND (u.user_role = 'EMPLOYEE' OR u.user_role IS NULL OR p.user_id = ?)
                ORDER BY p.created_at DESC
            """, (st.session_state.user_id,))
        elif view_filter == "OWNER ONLY VIEW":
            c.execute("""
                SELECT p.* FROM master_app_table p 
                LEFT JOIN master_app_table u ON p.user_id = u.user_id AND u.data_type = 'user'
                WHERE p.data_type = 'post' AND u.user_role = 'OWNER'
                ORDER BY p.created_at DESC
            """)
            
        posts_to_render = c.fetchall()

    ads_enabled = get_setting("show_ads") == "ON"
    ads_html = get_setting("adsense_script")

    if not posts_to_render:
        st.info("No posts available under current view scope.")
    else:
        for p_item in posts_to_render:
            render_post_card(p_item, ads_enabled, ads_html, prefix="main_feed")

    # OWNER PANELS (IF AUTHORIZED)
    if st.session_state.is_owner_session or st.session_state.user_role == "OWNER":
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
        st.markdown("### 🎛 Owner Master Control Power Panels (1 to 18)")
        
        o_tabs = st.tabs([
            "1️⃣ Global Branding", 
            "2️⃣ Upload Control", 
            "3️⃣ Emergency Kill-Switch", 
            "4️⃣ Dynamic Payment Methods",
            "5️⃣ Google AdSense Settings",
            "6️⃣ Content Moderation",
            "7️⃣ Boost Requests",
            "8️⃣ Live Monitor Feed",
            "9️⃣ User Recovery & Roles",
            "🔟 Sponsor Video Approvals",
            "1️⃣1️⃣ System Optimization",
            "1️⃣2️⃣ Anti-Duplicate Account Switch",
            "1️⃣3️⃣ Master Vault & Auto-Backup",
            "1️⃣4️⃣ Control & Analytics",
            "1️⃣5️⃣ Free Copyright-Free Music Library",
            "1️⃣6️⃣ Amazon E-Commerce & Meta Target Hub",
            "1️⃣7️⃣ Message & Direct Owner Upload Hub",
            "1️⃣8️⃣ Advanced Video Analytics & Monetization Hub"
        ])
        
        o_tab1, o_tab2, o_tab3, o_tab4, o_tab5, o_tab6, o_tab7, o_tab8, o_tab9, o_tab10, o_tab11, o_tab12, o_tab13, o_tab14, o_tab15, o_tab16, o_tab17, o_tab18 = o_tabs
        
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
            st.markdown("#### ⚙ Global Daily Limit Switch")
            curr_daily_limit = get_setting("daily_limit_mode", "OFF")
            st.write(f"Global Daily Limit Status: **{'ACTIVE' if curr_daily_limit == 'ON' else 'UNLIMITED'}**")

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
            st.markdown("#### 🏦 Dynamic Payment Gateway Control")
            with st.form("add_new_payment_method"):
                m_type = st.selectbox("Method Type", ["Mobile Banking", "Bank Transfer (Foreign)", "Bank Transfer (BD)", "Crypto / International"])
                p_name = st.text_input("Provider / Bank Name", placeholder="e.g. Clear Bank / Islami Bank / USDT TRC20")
                p_details = st.text_area("Account Details / Number", placeholder="e.g. Account No / IBAN / Crypto Address")
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
                col_g1.write(f"📌 **[{gw['method_type']}] {gw['provider_name']}** —\n```\n{gw['account_details']}\n```")
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
                    if st.button(f"✅ Approve ({mr['mon_id']})", key=f"app_mon_{mr['mon_id']}"):
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
                    if st.button(f"🔥 Approve & Boost ({br['boost_id']})", key=f"app_boost_{br['boost_id']}"):
                        c.execute("UPDATE master_app_table SET is_boosted = 1 WHERE record_id = ?", (br['post_id'],))
                        c.execute("UPDATE boost_requests SET status = 'Approved' WHERE boost_id = ?", (br['boost_id'],))
                        conn.commit()
                        st.success("Post Boosted!")
                        st.rerun()

        with o_tab8:
            st.markdown("#### 📡 Vertical Live Activity Monitor Feed")
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC LIMIT 30")
                live_posts = c.fetchall()

            if not live_posts:
                st.info("No activity found.")
            else:
                st.markdown("<div class='vertical-live-feed-box'>", unsafe_allow_html=True)
                for lp in live_posts:
                    st.markdown(f"""
                    <div class='vertical-live-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span>👤 <b>{lp['full_name']}</b> (ID: {lp['user_id'][:8]}...)</span>
                            <span style='color:#888; font-size:12px;'>⏱ {lp['created_at']}</span>
                        </div>
                        <p style='margin: 8px 0; font-size:15px;'><b>{lp['title']}</b> - <span style='color:#1877F2;'>[{lp['post_category'].upper()}]</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with o_tab9:
            st.markdown("#### 🔑 9th Screen: User Management & Role Assignment (Owner vs Employee)")
            st.caption("Manage User Roles, Assign Owner/Employee Permissions, and Set Recovery Codes:")
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT user_id, full_name, auth_identifier, recovery_code, user_role FROM master_app_table WHERE data_type = 'user'")
                all_registered_users = c.fetchall()

            if not all_registered_users:
                st.info("No registered users found.")
            else:
                for u in all_registered_users:
                    u_role = u['user_role'] if 'user_role' in u.keys() and u['user_role'] else 'EMPLOYEE'
                    with st.expander(f"👤 {u['full_name']} ({u['auth_identifier']}) - Current Role: [{u_role}]"):
                        st.write(f"**User ID:** `{u['user_id']}`")
                        st.write(f"**Current Recovery Code:** `{u['recovery_code'] if u['recovery_code'] else 'Not Set'}`")
                        
                        col_r1, col_r2, col_r3 = st.columns(3)
                        new_role = col_r1.selectbox("Set Role", ["EMPLOYEE", "OWNER"], index=0 if u_role == "EMPLOYEE" else 1, key=f"srole_{u['user_id']}")
                        new_rec = col_r2.text_input("New Recovery Code", key=f"nrec_{u['user_id']}")
                        
                        if col_r3.button("💾 Save User Role & Code", key=f"srec_{u['user_id']}"):
                            with get_db_connection() as conn:
                                c = conn.cursor()
                                if new_rec:
                                    c.execute("UPDATE master_app_table SET recovery_code = ?, user_role = ? WHERE user_id = ?", (new_rec, new_role, u['user_id']))
                                else:
                                    c.execute("UPDATE master_app_table SET user_role = ? WHERE user_id = ?", (new_role, u['user_id']))
                                conn.commit()
                            st.success("Updated Successfully!")
                            st.rerun()

        with o_tab10:
            st.markdown("#### 💼 10th Screen: Sponsor Video Approvals")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM sponsor_video_requests WHERE status = 'Pending' ORDER BY created_at DESC")
                pending_sponsors = c.fetchall()

            if not pending_sponsors:
                st.info("No pending sponsor videos or payments found.")

        with o_tab11:
            st.markdown("#### 🏔️ 11th Screen: System Optimization & Security Shield")
            if st.button("🛡️ Execute System Self-Healing & Health Check"):
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("VACUUM;")
                    conn.commit()
                st.success("✅ System Health Check Complete!")

        with o_tab12:
            st.markdown("#### 🕵‍♂️ 12th Screen: Auto-Duplicate Account Detector")
            curr_dup_switch = get_setting("auto_duplicate_detector", "ON")
            st.write(f"Detector Status: **{curr_dup_switch}**")

        with o_tab13:
            st.markdown("#### 📦 13th Screen: Master Vault, Data Backup & One-Click Restore Engine")
            if st.button("⚡ One-Click Internal Auto-Restore"):
                rc = auto_restore_from_internal_vault()
                st.success(f"Restored {rc} items.")

        with o_tab14:
            st.markdown("#### 🌟 14th Screen: Master Control & Regional Analytics")
            st.write("Regional operations status connected.")

        with o_tab15:
            st.markdown("#### 🎵 15th Screen: Free Copyright-Free Music Library")
            st.write("Music library control panel operational.")

        with o_tab16:
            st.markdown("#### 🛒 16th Screen: Amazon E-Commerce & Meta Hub")
            st.write("E-commerce & Meta Hub online.")

        with o_tab17:
            st.markdown("#### 💬 17th Screen: Direct Owner Messages")
            st.write("Owner direct messages active.")

        with o_tab18:
            st.markdown("#### 📊 18th Screen: Advanced Video Analytics")
            st.write("Video analytics engine active.")

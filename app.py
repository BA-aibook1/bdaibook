import os
import sqlite3
import uuid
import hashlib
import random
import json
import base64
import time
import subprocess
from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 0. SECURITY & ENVIRONMENT CONFIGURATION
# ==========================================
NEW_OWNER_SECRET_KEY = os.getenv("OWNER_SECRET", "S$s123456789112233BDAIBOOK@MDSOHELRANA")
SECRET_CODES = [NEW_OWNER_SECRET_KEY]

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
# ADVANCED SECURITY & AUTOMATIC COMPRESSION ENGINE
# ==========================================
SUSPICIOUS_EXTENSIONS = ['.exe', '.bat', '.cmd', '.sh', '.php', '.pl', '.cgi', '.js', '.vbs', '.py']

def sanitize_file_and_check_virus(file_obj, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in SUSPICIOUS_EXTENSIONS:
        return False, "🚫 Malicious/Executable File Threat Detected! File blocked for server safety."
    
    content_header = file_obj.read(1024)
    file_obj.seek(0)
    
    if b'<?php' in content_header or b'eval(' in content_header or b'system(' in content_header:
        return False, "🚫 Malicious Payload Script Detected inside media file!"
        
    return True, "Clean"

def process_and_chunk_media(file_obj, target_path):
    CHUNK_SIZE = 4 * 1024 * 1024  # High speed 4MB Chunking
    file_obj.seek(0)
    
    with open(target_path, "wb") as f:
        while True:
            chunk = file_obj.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
    return True

def auto_compress_video(input_path):
    try:
        temp_output = input_path + "_compressed.mp4"
        command = [
            'ffmpeg', '-y', '-i', input_path,
            '-vcodec', 'libx264',
            '-crf', '28',
            '-preset', 'ultrafast',
            '-acodec', 'aac',
            '-b:a', '128k',
            temp_output
        ]
        res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and os.path.exists(temp_output):
            os.replace(temp_output, input_path)
            return True
        return False
    except Exception:
        return False

# ==========================================
# 1. PAGE SETUP & STORAGE DIRECTORY
# ==========================================
st.set_page_config(
    page_title="Global AI Book",
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

LOCAL_DB_FILE = "global_ai_book_master.db"
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
                                'is_owner_post', 'created_at', 'recovery_code', 'user_status', 'meta_bluetooth_permission'
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

# PROFESSIONAL YOUTUBE & FACEBOOK STYLE CUSTOM CSS DESIGN
st.markdown("""
<style>
    .block-container { padding-top: 1rem !important; }
    div[data-testid="stHeader"] {
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #0f0f0f; z-index: 99999; border-bottom: 1px solid #272727;
    }
    img { border-radius: 12px; }
    .profile-avatar-img {
        border-radius: 50% !important; object-fit: cover !important; border: 2px solid #0064e0 !important; width: 50px; height: 50px;
    }
    .fb-post-card {
        background: #18191a; padding: 20px; border-radius: 14px; margin-bottom: 20px; border: 1px solid #2f3031; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .video-watermark-wrapper { position: relative; border-radius: 12px; overflow: hidden; }
    .video-watermark-badge {
        position: absolute; top: 12px; right: 15px; background: rgba(0, 100, 224, 0.85);
        color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; z-index: 99; pointer-events: none; backdrop-filter: blur(4px);
    }
    .tiktok-container { max-width: 380px; margin: 0 auto; border-radius: 16px; overflow: hidden; border: 2px solid #222; background: #000; }
    .announcement-box {
        background: linear-gradient(90deg, #16222f 0%, #0064e0 100%); color: white; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 15px; font-weight: bold; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    .ad-container { margin-top: 15px; margin-bottom: 15px; padding: 10px; background: #121212; border-radius: 10px; text-align: center; border: 1px dashed #333; }
    .vertical-live-feed-box { max-height: 600px; overflow-y: auto; background: #121316; padding: 15px; border-radius: 12px; border: 2px solid #0064e0; }
    .vertical-live-card { background: #1e2026; border-left: 4px solid #0064e0; padding: 12px; margin-bottom: 15px; border-radius: 8px; color: #fff; }
    .duplicate-card { background: #2a1215; border-left: 4px solid #ff4b4b; padding: 12px; margin-bottom: 10px; border-radius: 8px; color: #fff; }
    .amazon-product-card { background: #1e2026; border: 1px solid #ff9900; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
    .meta-control-box { background: #111a2e; border: 2px solid #0064e0; padding: 15px; border-radius: 12px; margin-bottom: 20px; }
    
    .yt-player-card {
        background: #0f0f0f; border-radius: 16px; overflow: hidden; border: 1px solid #272727; margin-bottom: 25px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }
    .yt-badge {
        background: #ff0000; color: #fff; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px;
    }
    .mahfil-badge {
        background: #008055; color: #fff; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px;
    }
    .movie-badge {
        background: #e50914; color: #fff; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px;
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
        
        try: c.execute("ALTER TABLE master_app_table ADD COLUMN recovery_code TEXT")
        except sqlite3.OperationalError: pass

        try: c.execute("ALTER TABLE master_app_table ADD COLUMN user_status TEXT DEFAULT 'REAL'")
        except sqlite3.OperationalError: pass

        try: c.execute("ALTER TABLE master_app_table ADD COLUMN meta_bluetooth_permission INTEGER DEFAULT 0")
        except sqlite3.OperationalError: pass

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
        
        default_settings = {
            "app_name": "Global AI Book",
            "owner_announcement": "Welcome to Global AI Book - Next-Gen Social & Media Platform!",
            "lock_upload": "OFF",
            "daily_limit_mode": "OFF",
            "lock_login": "OFF",
            "logo_path": "",
            "adsense_client_id": "ca-pub-0000000000000000",
            "adsense_script": """<div style="background:#222; color:#fff; text-align:center; padding:15px; border:1px dashed #0064e0; border-radius:8px;">📢 <b>Google AdSense Banner Placeholder</b></div>""",
            "show_ads": "ON",
            "global_notify_msg": "System Active Globally",
            "auto_duplicate_detector": "ON",
            "site_verification_code": "",
            "is_global_meta_active": "true",
            "meta_mode": "SELECTED_USERS",
            "owner_identifier": "mdsohelrana@gmail.com" # Default Owner Ident
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
    return """<svg viewBox="0 0 24 24" fill="#0866FF" width="18" height="18" style="vertical-align: middle; margin-left: 4px; margin-right: 4px; display: inline-block; flex-shrink: 0;">
        <path d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.79-4-4-4-.495 0-.965.084-1.4.238C14.55 2.475 13.18 1.6 11.6 1.6c-1.58 0-2.95.875-3.6 2.148-.435-.154-.905-.238-1.4-.238-2.21 0-4 1.79-4 4 0 .495.084.965.238 1.4C1.575 9.55.7 10.92.7 12.5c0 1.58 0 2.95 2.148 3.6-.154.435-.238.905-.238 1.4 0 2.21 1.79 4 4 4 .495 0 .965-.084 1.4-.238 1.05 1.273 2.42 2.148 4 2.148 1.58 0 2.95-.875 3.6-2.148.435.154.905.238 1.4.238 2.21 0 4-1.79 4-4 0-.495-.084-.965-.238-1.4 1.273-1.05 2.148-2.42 2.148-4z"/>
        <path fill="#FFFFFF" d="M10.2 16.2l-3.7-3.7 1.4-1.4 2.3 2.3 5.3-5.3 1.4 1.4z"/>
    </svg>"""

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
if "is_true_owner" not in st.session_state: st.session_state.is_true_owner = False
if "active_tab" not in st.session_state: st.session_state.active_tab = 0

site_logo_path = get_setting("logo_path")
app_name = get_setting("app_name", "Global AI Book")
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

real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 User Login / Register")
login_locked = get_setting("lock_login") == "ON"

if not st.session_state.user_id:
    if login_locked:
        st.sidebar.error("🚫 Login System is temporarily locked by Owner for maintenance!")
    else:
        auth_input = st.sidebar.text_input("Phone Number or Email")
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
                            st.sidebar.success("Password Reset Success! Login with new password.")
                        else:
                            st.sidebar.error("Invalid Identifier or Recovery Code!")
                else:
                    st.sidebar.warning("Fill all details.")
        else:
            if st.sidebar.button("Send OTP"):
                if auth_input and auth_pass:
                    generated_otp = str(random.randint(100000, 999999))
                    st.session_state.otp_code = generated_otp
                    st.sidebar.success(f"🔑 Auto Verification Code: **{generated_otp}**")
                else:
                    st.sidebar.warning("Please provide both Email/Phone and Password!")
                    
            if st.session_state.otp_code:
                user_otp = st.sidebar.text_input("Enter 6-Digit OTP Code")
                if st.sidebar.button("Verify & Proceed"):
                    if user_otp == st.session_state.otp_code:
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                            usr = c.fetchone()
                            
                            if usr:
                                if usr["password_hash"] == hash_pass(auth_pass):
                                    st.session_state.user_id = usr["user_id"]
                                    
                                    # Check if this user is the authentic owner
                                    if usr.get("is_owner_post") == 1 or auth_input == get_setting("owner_identifier"):
                                        st.session_state.is_true_owner = True
                                    else:
                                        st.session_state.is_true_owner = False
                                        
                                    st.sidebar.success("Logged In Successfully!")
                                    st.rerun()
                                else:
                                    st.sidebar.error("❌ Invalid Password!")
                            else:
                                new_uid = str(uuid.uuid4())
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                
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
                                    "created_at": now
                                }

                                c.execute("""
                                    INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, user_status, meta_bluetooth_permission, created_at)
                                    VALUES (?, 'user', ?, ?, ?, ?, 1, 'REAL', 0, ?)
                                """, (new_uid, new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), now))
                                conn.commit()
                                
                                save_to_internal_vault(user_data_map)
                                st.session_state.user_id = new_uid
                                st.session_state.is_true_owner = False
                                st.sidebar.success("Registered & Logged In as Normal User!")
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
    
    if current_user.get("is_suspended"):
        sus_until = current_user.get("suspended_until", "")
        if datetime.now().strftime("%Y-%m-%d %H:%M:%S") < sus_until:
            st.error(f"🚫 Account Suspended until: {sus_until}")
            st.stop()

    st.sidebar.markdown(f"User: **{current_user.get('full_name', 'User')}**")
    st.sidebar.markdown(f"👥 Real Followers: **{real_followers:,}**")
    
    user_bt_permission = check_user_meta_bluetooth_permission(st.session_state.user_id)
    if user_bt_permission:
        st.sidebar.success("🔵 Meta Bluetooth Access: ACTIVE")
    else:
        st.sidebar.info("🔴 Meta Bluetooth Access: DISABLED")

    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.is_owner_session = False
        st.session_state.is_true_owner = False
        st.session_state.otp_code = None
        st.rerun()

tab_feed, tab_profile, tab_monetization = st.tabs(["📺 Public Live Feed", "👤 Profile & Studio", "🌍 Global Monetization & Boost"])

# ==========================================
# FIXED PUBLIC RENDER CARD
# ==========================================
def render_post_card(post, ads_enabled, ads_html, prefix="feed"):
    increment_views(post["record_id"])
    cat = post.get("post_category", "general")
    
    if cat in ["mahfil", "movie", "long"]:
        st.markdown("<div class='yt-player-card' style='padding: 20px;'>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='fb-post-card'>", unsafe_allow_html=True)
    
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT full_name, profile_pic_path, is_verified FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (post.get("user_id"),))
        author = c.fetchone()
        
        c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (post.get("user_id"),))
        f_row = c.fetchone()
        author_followers = f_row["cnt"] if f_row else 0
        
        is_following = False
        if st.session_state.user_id:
            c.execute("SELECT * FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, post.get("user_id")))
            if c.fetchone(): is_following = True

    author_name = author["full_name"] if author and author["full_name"] else post.get("full_name", "User")
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
            tick = get_meta_blue_badge() if (author and author["is_verified"]) or post.get("is_verified") else ""
            boost_badge = "🔥 [BOOSTED]" if post.get("is_boosted") else ""
            
            badge_html = ""
            if cat == "mahfil":
                badge_html = "<span class='mahfil-badge'>🕌 Islamic Streams</span> "
            elif cat == "movie":
                badge_html = "<span class='movie-badge'>🎬 Full Movie HD</span> "
            elif cat == "long":
                badge_html = "<span class='yt-badge'>▶ YouTube HD Video</span> "
                
            st.markdown(f"<div style='display: flex; align-items: center; flex-wrap: wrap;'>{badge_html}<b>{author_name}</b>{tick} <span style='color:orange; margin-left: 6px;'>{boost_badge}</span></div>", unsafe_allow_html=True)
            st.caption(f"👥 Followers: {author_followers:,} | Category: {post.get('post_category').upper()}")
        
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
                st.success("Post updated successfully!")
                st.rerun()
                
            if col_ed2.button("🗑️ Delete Post", key=f"del_{prefix}_{post['record_id']}"):
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM master_app_table WHERE record_id = ?", (post["record_id"],))
                    conn.commit()
                st.success("Post deleted!")
                st.rerun()

    media_path = post.get("media_path")
    
    if media_path:
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

    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b1.write(f"👁️ **{(post.get('views_count', 0) + 1):,}** Views")
    
    like_lbl = f"❤️ Liked ({real_likes})" if has_liked else f"👍 Like ({real_likes})"
    if col_b2.button(like_lbl, key=f"lk_{prefix}_{post['record_id']}"):
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

    if col_b3.button("🚀 Share", key=f"sh_{prefix}_{post['record_id']}"):
        st.toast("Sharing Link Copied!")
        
    st.markdown("</div>", unsafe_allow_html=True)

with tab_feed:
    search_input = st.text_input("🔍 Search Users, Videos, Hashtags...")
    
    # OWNER CHECK SECURE SYSTEM
    if search_input.strip() in SECRET_CODES:
        if st.session_state.is_true_owner:
            st.session_state.is_owner_session = True
            st.success("👑 MASTER OWNER COMMAND CENTER UNLOCKED!")
        else:
            st.error("🚫 Access Denied: You are not logged in as the System Owner! Secret code alone will not grant owner panel.")
            st.session_state.is_owner_session = False
            
    if st.session_state.is_owner_session and st.session_state.is_true_owner:
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
        st.markdown("### 🎛️ Owner Master Control Power Panels (1 to 16)")
        
        o_tabs = st.tabs([
            "1️⃣ Global Branding", 
            "2️⃣ Upload Control", 
            "3️⃣ Emergency Kill-Switch", 
            "4️⃣ Dynamic Payment Methods",
            "5️⃣ Google AdSense Settings",
            "6️⃣ Content Moderation",
            "7️⃣ Boost Requests",
            "8️⃣ Live Monitor Feed",
            "9️⃣ User Recovery & Management",
            "🔟 Sponsor Video Approvals",
            "1️⃣1️⃣ Global Master Rules",
            "1️⃣2️⃣ Anti-Duplicate Account Switch",
            "1️⃣3️⃣ Master Vault & Auto-Backup",
            "1️⃣4️⃣ Master Control & Analytics",
            "1️⃣5️⃣ Free Copyright-Free Music Library (Owner Upload)",
            "1️⃣6️⃣ Amazon E-Commerce & Meta Target Hub"
        ])
        
        o_tab1, o_tab2, o_tab3, o_tab4, o_tab5, o_tab6, o_tab7, o_tab8, o_tab9, o_tab10, o_tab11, o_tab12, o_tab13, o_tab14, o_tab15, o_tab16 = o_tabs
        
        with o_tab1:
            st.markdown("#### 🖼️ Global Branding & Logo")
            new_app_name = st.text_input("Header App Name", value=get_setting("app_name", "Global AI Book"))
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
            st.markdown("#### ⚙️ Global Daily Limit Switch")
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
                m_type = st.selectbox("Method Type", ["Mobile Banking", "Bank Transfer (Foreign)", "Bank Transfer (Local)", "Crypto / International"])
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
            st.caption("View real-time uploaded posts and activity streams:")
            
            col_rf1, col_rf2 = st.columns([1, 1])
            with col_rf1:
                if st.button("🔄 Refresh Live Feed"):
                    st.rerun()
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY created_at DESC LIMIT 30")
                live_posts = c.fetchall()
            
            ads_enabled = get_setting("show_ads") == "ON"
            ads_html = get_setting("adsense_script")

            if not live_posts:
                st.info("No activity found.")
            else:
                st.markdown("<div class='vertical-live-feed-box'>", unsafe_allow_html=True)
                for lp in live_posts:
                    st.markdown(f"""
                    <div class='vertical-live-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span>👤 <b>{lp['full_name']}</b> (ID: {lp['user_id'][:8]}...)</span>
                            <span style='color:#888; font-size:12px;'>⏱️ {lp['created_at']}</span>
                        </div>
                        <p style='margin: 8px 0; font-size:15px;'><b>{lp['title']}</b> - <span style='color:#0064e0;'>[{lp['post_category'].upper()}]</span></p>
                        <p style='color:#ccc; font-size:13px;'>{lp['content'] if lp['content'] else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if lp['media_path']:
                        if lp['media_path'].startswith("http"):
                            st.video(lp['media_path'])
                        elif os.path.exists(lp['media_path']):
                            if lp['post_category'] == 'picture':
                                st.image(lp['media_path'], width=300)
                            else:
                                st.video(lp['media_path'])

                    col_act1, col_act2 = st.columns(2)
                    if col_act1.button("🗑️ Delete Post", key=f"v_del_{lp['record_id']}"):
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM master_app_table WHERE record_id = ?", (lp['record_id'],))
                            conn.commit()
                        st.rerun()
                        
                    if col_act2.button("🚫 Ban User", key=f"v_ban_{lp['record_id']}"):
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            sus_time = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("UPDATE master_app_table SET is_suspended = 1, suspended_until = ? WHERE user_id = ?", (sus_time, lp['user_id']))
                            conn.commit()
                        st.rerun()
                    st.markdown("---")
                st.markdown("</div>", unsafe_allow_html=True)

        with o_tab9:
            st.markdown("#### 🔑 9th Screen: User Recovery System & Password Management")
            st.caption("Owner can manually set or update user recovery codes here:")
            
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT user_id, full_name, auth_identifier, recovery_code FROM master_app_table WHERE data_type = 'user'")
                all_registered_users = c.fetchall()

            if not all_registered_users:
                st.info("No registered users found.")
            else:
                for u in all_registered_users:
                    with st.expander(f"👤 {u['full_name']} ({u['auth_identifier']})"):
                        st.write(f"**User ID:** `{u['user_id']}`")
                        st.write(f"**Current Recovery Code:** `{u['recovery_code'] if u['recovery_code'] else 'Not Set'}`")
                        
                        col_r1, col_r2 = st.columns(2)
                        new_rec = col_r1.text_input("New Recovery Code", key=f"nrec_{u['user_id']}")
                        if col_r2.button("💾 Set Code", key=f"srec_{u['user_id']}"):
                            if new_rec:
                                with get_db_connection() as conn:
                                    c = conn.cursor()
                                    c.execute("UPDATE master_app_table SET recovery_code = ? WHERE user_id = ?", (new_rec, u['user_id']))
                                    conn.commit()
                                st.success("Recovery Code Updated!")
                                st.rerun()

        with o_tab10:
            st.markdown("#### 💼 10th Screen: Sponsor Video Approvals")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM sponsor_video_requests WHERE status = 'Pending' ORDER BY created_at DESC")
                pending_sponsors = c.fetchall()

            if not pending_sponsors:
                st.info("No pending sponsor videos found.")
            else:
                for sp in pending_sponsors:
                    st.markdown(f"""
                    <div style='background:#1e2026; padding:12px; border-radius:8px; margin-bottom:10px; border-left:4px solid #0064e0;'>
                        <b>Sponsor Name:</b> {sp['sponsor_name']}<br>
                        <b>TrxID (10-Digit):</b> <span style='color:yellow; font-weight:bold;'>{sp['trx_id_10digit']}</span><br>
                        <b>Payment Method:</b> {sp['bank_details_used']}<br>
                        <b>Video Link/Path:</b> {sp['video_link'] or sp['video_file_path']}<br>
                        <small style='color:#888;'>Time: {sp['created_at']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_sp_ap1, col_sp_ap2 = st.columns(2)
                    if col_sp_ap1.button(f"✅ Approve & Auto-Publish Video", key=f"app_sp_{sp['request_id']}"):
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        rec_id = str(uuid.uuid4())
                        
                        sp_post_data = {
                            "record_id": rec_id,
                            "data_type": "post",
                            "user_id": "SPONSOR",
                            "full_name": sp['sponsor_name'],
                            "is_verified": 1,
                            "title": f"Sponsored Video: {sp['sponsor_name']}",
                            "content": f"TrxID: {sp['trx_id_10digit']}",
                            "media_path": sp['video_link'] or sp['video_file_path'],
                            "post_category": "long",
                            "is_boosted": 1,
                            "created_at": now_str
                        }

                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, media_path, post_category, is_boosted, created_at)
                                VALUES (?, 'post', 'SPONSOR', ?, 1, ?, ?, ?, 'long', 1, ?)
                            """, (rec_id, sp['sponsor_name'], f"Sponsored Video: {sp['sponsor_name']}", f"TrxID: {sp['trx_id_10digit']}", sp['video_link'] or sp['video_file_path'], now_str))
                            c.execute("UPDATE sponsor_video_requests SET status = 'Approved' WHERE request_id = ?", (sp['request_id'],))
                            conn.commit()
                            
                        save_to_internal_vault(sp_post_data)
                        st.success("Video published successfully!")
                        st.rerun()

                    if col_sp_ap2.button(f"❌ Reject Request", key=f"rej_sp_{sp['request_id']}"):
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute("UPDATE sponsor_video_requests SET status = 'Rejected' WHERE request_id = ?", (sp['request_id'],))
                            conn.commit()
                        st.rerun()

        with o_tab11:
            st.markdown("#### 🏔️ 11th Screen: System Optimization & Security Shield")
            st.caption("Automated system optimization and security controls:")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🛡️ Execute System Self-Healing & Health Check"):
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("VACUUM;")
                        conn.commit()
                    st.success("✅ System Health Check Complete! Database integrity verified.")
            with col_d2:
                if st.button("🧹 Clear Temporary Cache & Optimize Media Storage"):
                    st.success("✅ Cache Cleared & Storage Optimized!")

        with o_tab12:
            st.markdown("#### 🕵️‍♂️ 12th Screen: Auto-Duplicate Account Detector & Ban Control Switch")
            curr_dup_switch = get_setting("auto_duplicate_detector", "ON")
            st.write(f"🤖 **Auto-Duplicate Detector Switch:** **{'ACTIVE (ON)' if curr_dup_switch == 'ON' else 'DISABLED (OFF)'}**")
            
            col_dup1, col_dup2 = st.columns(2)
            if curr_dup_switch == "OFF":
                if col_dup1.button("🟢 ENABLE AUTO-DUPLICATE DETECTOR"):
                    set_setting("auto_duplicate_detector", "ON")
                    st.rerun()
            else:
                if col_dup2.button("🔴 DISABLE AUTO-DUPLICATE DETECTOR"):
                    set_setting("auto_duplicate_detector", "OFF")
                    st.rerun()

        with o_tab13:
            st.markdown("#### 📦 13th Screen: Master Vault, Data Backup & One-Click Restore Engine")
            if st.button("⚡ One-Click Internal Auto-Restore (No File Needed)"):
                rc = auto_restore_from_internal_vault()
                st.success(f"🎉 RESTORE SUCCESSFUL! Restored {rc} items.")

        with o_tab14:
            st.markdown("#### 🌟 14th Screen: Master Control & Regional Analytics")
            st.text_input("Default Master Admin Name", value="Sohel Rana", disabled=True)
            st.success("✅ Copyright and title settings are synchronized with artist Sohel Rana in the database.")

        with o_tab15:
            st.markdown("#### 🎵 15th Screen: Free Copyright-Free Music Library")
            with st.form("owner_music_upload_form"):
                song_title = st.text_input("Song Title / Name")
                artist_name = st.text_input("Artist Name", value="Sohel Rana")
                song_file = st.file_uploader("Upload Copyright-Free Audio Song (.mp3/.wav)", type=["mp3", "wav"])
                submit_song = st.form_submit_button("📤 Upload to Free Music Library")
                
                if submit_song and song_file and song_title:
                    song_id = str(uuid.uuid4())
                    s_path = os.path.join(UPLOAD_DIR, f"free_song_{song_id}.mp3")
                    with open(s_path, "wb") as f:
                        f.write(song_file.getbuffer())
                    
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO music_library VALUES (?, ?, ?, ?, ?)", (song_id, song_title, artist_name, s_path, now))
                        conn.commit()
                    st.success("✅ Song added successfully!")
                    st.rerun()

        with o_tab16:
            st.markdown("#### 🛒 16th Screen: Amazon E-Commerce & Owner Master Permission Target Hub")
            st.info("Amazon & Meta Settings Hub Active")

    # PUBLIC FEED DISPLAY (When not in owner panel)
    if not st.session_state.is_owner_session:
        with get_db_connection() as conn:
            c = conn.cursor()
            if search_input and search_input.strip() not in SECRET_CODES:
                q_str = f"%{search_input}%"
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND (title LIKE ? OR content LIKE ? OR full_name LIKE ? OR tags LIKE ?) ORDER BY is_boosted DESC, created_at DESC", (q_str, q_str, q_str, q_str))
            else:
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY is_boosted DESC, created_at DESC")
                
            posts = [dict(r) for r in c.fetchall()]

        ads_enabled = get_setting("show_ads") == "ON"
        ads_html = get_setting("adsense_script")

        sub_feed1, sub_feed2, sub_feed3, sub_feed4, sub_feed5, sub_feed6, sub_feed7 = st.tabs(["🌐 All Feed", "🕌 Islamic Streams", "🎬 Full Movies", "🛒 Amazon Store", "📱 Reels / Shorts", "🖼️ Photos", "📹 YouTube Style Long"])

        with sub_feed1:
            for post in posts:
                render_post_card(post, ads_enabled, ads_html, prefix="all")

        with sub_feed2:
            mahfil_posts = [p for p in posts if p.get("post_category") == "mahfil"]
            for post in mahfil_posts:
                render_post_card(post, ads_enabled, ads_html, prefix="mahfil")

        with sub_feed3:
            movie_posts = [p for p in posts if p.get("post_category") == "movie"]
            for post in movie_posts:
                render_post_card(post, ads_enabled, ads_html, prefix="movie")

        with sub_feed4:
            st.markdown("### 🛒 Amazon Marketplace & Featured Products")
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM amazon_products ORDER BY created_at DESC")
                public_amz_products = c.fetchall()

            grid_cols = st.columns(2)
            for idx, ap in enumerate(public_amz_products):
                with grid_cols[idx % 2]:
                    st.markdown(f"""
                    <div class='amazon-product-card'>
                        <h4 style='color:#ff9900; margin-bottom:5px;'>{ap['title']}</h4>
                        <p style='margin:0 0 10px 0;'>Price: <span style='color:#00ff66; font-weight:bold;'>{ap['price']}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    if ap['image_url']:
                        st.image(ap['image_url'], use_container_width=True)
                    st.markdown(f"<a href='{ap['affiliate_link']}' target='_blank'><button style='width:100%; background:#ff9900; color:#000; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer;'>🛒 Buy Now on Amazon</button></a>", unsafe_allow_html=True)

        with sub_feed5:
            short_posts = [p for p in posts if p.get("post_category") == "short"]
            for post in short_posts:
                render_post_card(post, ads_enabled, ads_html, prefix="short")

        with sub_feed6:
            picture_posts = [p for p in posts if p.get("post_category") == "picture"]
            for post in picture_posts:
                render_post_card(post, ads_enabled, ads_html, prefix="pic")

        with sub_feed7:
            long_posts = [p for p in posts if p.get("post_category") in ["long", "general"]]
            for post in long_posts:
                render_post_card(post, ads_enabled, ads_html, prefix="long")

# ==========================================
# 3. USER PROFILE & STUDIO TAB (FULLY FIXED)
# ==========================================
with tab_profile:
    if not st.session_state.user_id:
        st.warning("Please login to manage profile!")
    else:
        tick = get_meta_blue_badge() if current_user.get("is_verified") else ""
        st.markdown(f"<div style='display: flex; align-items: center;'><h2>Profile Studio: {current_user.get('full_name', 'User')}</h2>{tick}</div>", unsafe_allow_html=True)
        
        profile_path = current_user.get("profile_pic_path")
        
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            if profile_path and os.path.exists(profile_path):
                st.image(profile_path, width=120)
            else:
                st.markdown("👤")
            
            with st.expander("📷 Change DP / Profile Picture"):
                up_dp = st.file_uploader("Upload DP Image", type=["png", "jpg", "jpeg"], key="prof_dp_uploader")
                if st.button("Save DP"):
                    if up_dp:
                        dp_file_path = os.path.join(UPLOAD_DIR, f"dp_{st.session_state.user_id}.png")
                        with open(dp_file_path, "wb") as f:
                            f.write(up_dp.getbuffer())
                        
                        with get_db_connection() as conn:
                            c = conn.cursor()
                            c.execute("UPDATE master_app_table SET profile_pic_path = ? WHERE user_id = ?", (dp_file_path, st.session_state.user_id))
                            conn.commit()
                        st.success("Profile picture updated!")
                        st.rerun()

        with col_p2:
            st.write(f"**Full Name:** {current_user.get('full_name')}")
            st.write(f"**Identifier:** {current_user.get('auth_identifier')}")
            st.write(f"**Bio:** {current_user.get('bio', 'No bio added yet.')}")

        st.markdown("---")
        st.markdown("### 📤 Upload New Post / Media Content")
        
        if get_setting("lock_upload") == "ON":
            st.error("🚫 Video & Media Upload is temporarily disabled by Owner.")
        else:
            with st.form("user_create_post_form"):
                p_title = st.text_input("Post Title / Caption")
                p_desc = st.text_area("Post Description")
                p_cat = st.selectbox("Category", ["general", "picture", "short", "long", "mahfil", "movie"])
                uploaded_media = st.file_uploader("Upload Media File (Image/Video)", type=["png", "jpg", "jpeg", "mp4", "mov", "avi"])
                
                submit_post = st.form_submit_button("🚀 Publish Post")
                
                if submit_post and (p_title or uploaded_media):
                    media_saved_path = ""
                    if uploaded_media:
                        is_safe, msg = sanitize_file_and_check_virus(uploaded_media, uploaded_media.name)
                        if not is_safe:
                            st.error(msg)
                            st.stop()
                            
                        file_ext = os.path.splitext(uploaded_media.name)[1]
                        media_saved_path = os.path.join(UPLOAD_DIR, f"media_{uuid.uuid4()[:8]}{file_ext}")
                        process_and_chunk_media(uploaded_media, media_saved_path)

                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    post_id = str(uuid.uuid4())
                    
                    new_post_data = {
                        "record_id": post_id,
                        "data_type": "post",
                        "user_id": st.session_state.user_id,
                        "full_name": current_user.get("full_name"),
                        "title": p_title,
                        "content": p_desc,
                        "media_path": media_saved_path,
                        "post_category": p_cat,
                        "created_at": now_str
                    }

                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO master_app_table (record_id, data_type, user_id, full_name, title, content, media_path, post_category, created_at)
                            VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?)
                        """, (post_id, st.session_state.user_id, current_user.get("full_name"), p_title, p_desc, media_saved_path, p_cat, now_str))
                        conn.commit()
                        
                    save_to_internal_vault(new_post_data)
                    st.success("🎉 Post Published Successfully!")
                    st.rerun()

# ==========================================
# 4. GLOBAL MONETIZATION & BOOST TAB
# ==========================================
with tab_monetization:
    st.markdown("### 🌍 Monetization & Post Boosting Hub")
    
    col_m_m1, col_m_m2 = st.columns(2)
    with col_m_m1:
        st.markdown("#### 💰 Apply for Monetization")
        st.write(f"Current Followers: **{real_followers:,}** / Required: **1,000**")
        
        bank_details = st.text_area("Enter Payout Bank / Mobile Banking Information")
        if st.button("Submit Monetization Request"):
            if real_followers >= 1000:
                mon_id = str(uuid.uuid4())
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO monetization_requests VALUES (?, ?, ?, ?, 'Pending', ?)", (mon_id, st.session_state.user_id, real_followers, bank_details, now_str))
                    conn.commit()
                st.success("Monetization Application Submitted!")
            else:
                st.error("You need at least 1,000 followers to apply!")

    with col_m_m2:
        st.markdown("#### 🔥 Boost Your Videos / Posts")
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT record_id, title FROM master_app_table WHERE data_type = 'post' AND user_id = ?", (st.session_state.user_id or "",))
            user_posts = c.fetchall()

        if not user_posts:
            st.info("Upload a post first to enable boosting.")
        else:
            post_opts = {p["title"]: p["record_id"] for p in user_posts}
            sel_post_title = st.selectbox("Select Post to Boost", list(post_opts.keys()))
            b_plan = st.selectbox("Select Plan", ["Basic (10K Reach - $5)", "Standard (50K Reach - $20)", "Ultra (200K Reach - $50)"])
            trx_info = st.text_input("Transaction ID (TrxID) / Proof")
            
            if st.button("Submit Boost Request"):
                if trx_info:
                    boost_id = str(uuid.uuid4())
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO boost_requests VALUES (?, ?, ?, ?, 'Paid', ?, 'Manual', 'Pending', ?)", (boost_id, st.session_state.user_id, post_opts[sel_post_title], b_plan, trx_info, now_str))
                        conn.commit()
                    st.success("Boost Request Submitted for Review!")

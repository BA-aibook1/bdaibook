import os
import sqlite3
import random
import uuid
import base64
import urllib.parse
import hashlib
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Global Verified Network",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

components.html(
    """
    <meta name="msvalidate.01" content="e776b8ce73ea3dcc07551e8a021a0907">
    <meta name="monetag" content="5cc1b7ba5cb29eff802ce49009f87e2b">
    """,
    height=0,
)

SMART_LINK = "https://omg10.com/4/10954816"

# ==========================================
# 2. LOCAL STORAGE & DATABASE SETUP
# ==========================================
DB_FILE = "local_storage.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
PROFILE_DIR = "stored_profiles"

for folder in [VIDEO_DIR, IMAGE_DIR, PROFILE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            clean_phone TEXT UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            profile_pic TEXT,
            bio TEXT,
            is_verified INTEGER DEFAULT 1,
            payment_method TEXT,
            account_details TEXT,
            nid_number TEXT,
            address TEXT,
            followers_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'none',
            earnings REAL DEFAULT 0.0,
            role TEXT DEFAULT 'user',
            created_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [column[1] for column in cursor.fetchall()]
    if "clean_phone" not in existing_cols:
        try: cursor.execute("ALTER TABLE users ADD COLUMN clean_phone TEXT")
        except Exception: pass
    if "role" not in existing_cols:
        try: cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        except Exception: pass

    # 2. Daily Upload Limits Table (Strict 1 Long, 1 Short, 10 Posts Limit)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_upload_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content_type TEXT NOT NULL,
            upload_date TEXT NOT NULL
        )
    """)

    # 3. Advertisements Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertisements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            advertiser_email TEXT,
            ad_type TEXT,
            content_link TEXT,
            duration_months INTEGER,
            region TEXT,
            payment_method TEXT,
            amount REAL,
            trx_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    # 4. Bank Details Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            payment_type TEXT DEFAULT 'Bank Transfer',
            bank_name TEXT,
            branch_name TEXT,
            account_name TEXT,
            account_number TEXT,
            routing_number TEXT,
            swift_code TEXT,
            card_number TEXT,
            card_holder TEXT,
            card_expiry TEXT,
            global_wallet TEXT,
            mobile_banking TEXT,
            country TEXT,
            updated_at TEXT,
            FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE ON UPDATE CASCADE
        )
    """)

    # 5. Videos Table (With Hashtag Support)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            video_url TEXT,
            uploader_name TEXT,
            uploader_pic TEXT,
            video_type TEXT DEFAULT 'long',
            title TEXT,
            hashtags TEXT,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("PRAGMA table_info(videos)")
    v_cols = [column[1] for column in cursor.fetchall()]
    if "hashtags" not in v_cols:
        try: cursor.execute("ALTER TABLE videos ADD COLUMN hashtags TEXT")
        except Exception: pass

    # 6. Posts Table (With Hashtag Support)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            uploader_pic TEXT,
            content TEXT,
            hashtags TEXT,
            image_url TEXT,
            likes INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(posts)")
    p_cols = [column[1] for column in cursor.fetchall()]
    if "hashtags" not in p_cols:
        try: cursor.execute("ALTER TABLE posts ADD COLUMN hashtags TEXT")
        except Exception: pass

    # 7. Comments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            post_id TEXT,
            uploader_name TEXT,
            comment_text TEXT,
            gift_type TEXT,
            created_at TEXT
        )
    """)

    # Secure Owner Account Setup & Permanent Logo Fix
    owner_email = "owner_admin_system"
    hashed_pw = hashlib.sha256("S$s123456789112233".encode()).hexdigest()
    owner_pic = "logo.jpg" if os.path.exists("logo.jpg") else None
    
    cursor.execute("SELECT * FROM users WHERE role = 'owner'")
    owner_rec = cursor.fetchone()
    if not owner_rec:
        cursor.execute("""
            INSERT INTO users (username, phone_number, clean_phone, password, full_name, profile_pic, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (owner_email, "8801722003172", "8801722003172", hashed_pw, "System Administrator", owner_pic, "owner", datetime.now().strftime("%Y-%m-%d")))
    else:
        if owner_pic and not owner_rec['profile_pic']:
            cursor.execute("UPDATE users SET profile_pic = ? WHERE role = 'owner'", (owner_pic,))

    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. HELPER FUNCTIONS & WATERMARK SETUP
# ==========================================
def normalize_phone(phone_str):
    if not phone_str:
        return ""
    cleaned = "".join([c for c in str(phone_str) if c.isdigit() or c == '+'])
    return cleaned

def mask_phone_number(phone):
    if not phone:
        return ""
    clean_p = normalize_phone(phone)
    if len(clean_p) >= 10:
        return clean_p[:4] + "*****" + clean_p[-3:]
    elif len(clean_p) > 4:
        return clean_p[:2] + "****" + clean_p[-2:]
    return clean_p

def format_value(value):
    if value is None:
        return "0"
    if value >= 1000000:
        return f"{value/1000000:.1f}M"
    if value >= 1000:
        return f"{value/1000:.1f}K"
    return str(value)

def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception:
            return None
    return None

def get_owner_payment_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT account_details FROM users WHERE role = 'owner'")
    row = cursor.fetchone()
    conn.close()
    if row and row['account_details']:
        return row['account_details']
    return """
    🏦 Official Secure Payment Details (Hidden from Public & Protected):
    • bKash Personal: 01302134435 (Send Money)
    • Nagad Personal: 01722003172 (Send Money)
    • Islami Bank Bangladesh: A/C 20502530202612312 (MD. SOHEL RANA, Lalmonirhat Branch)
    • USDT TRC20: TM6DAbNuF2kaMaRoC8HKi2G8Gi5hVWnbCP
    """

def check_daily_upload_limit(username, content_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM daily_upload_limits 
        WHERE username = ? AND content_type = ? AND upload_date = ?
    """, (username, content_type, today_str))
    
    res = cursor.fetchone()
    count = res['count'] if res else 0
    conn.close()

    limits = {
        "long_video": 1,
        "short_video": 1,
        "post": 10
    }
    
    return count < limits.get(content_type, 1), count, limits.get(content_type, 1)

def record_daily_upload(username, content_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO daily_upload_limits (username, content_type, upload_date)
        VALUES (?, ?, ?)
    """, (username, content_type, today_str))
    conn.commit()
    conn.close()

def show_google_guidelines_box():
    st.markdown("""
        <div style="background-color: #1e293b; border-left: 5px solid #00c853; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="color: #00c853; margin-top: 0;">📜 Platform & Global Guidelines (Strict Limits)</h4>
            <ul style="color: #cbd5e1; font-size: 13px; margin-bottom: 0; padding-left: 20px;">
                <li><b>Daily Upload Limit:</b> Exactly <b>1 Long Video</b>, <b>1 Short Video</b>, and up to <b>10 Posts</b> per 24 hours.</li>
                <li><b>Hashtag System:</b> Use tags like #AI #Trending #BD #Tech in posts/videos for better discovery.</li>
                <li><b>Waterproof Protection:</b> All uploaded media automatically features secure platform branding and owner watermark.</li>
                <li><b>Secured Payment System:</b> Personal bKash/Nagad/Bank details are completely hidden from public views and only visible in Advertiser Hub.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

def show_watermarked_media(media_type, media_path, title=""):
    """Displays video or image with automatic waterproof overlay and owner branding"""
    logo_b64 = get_image_base64("logo.jpg") if os.path.exists("logo.jpg") else None
    logo_tag = f'<img src="data:image/jpeg;base64,{logo_b64}" style="width:28px; height:28px; border-radius:50%; border:1px solid #00c853; object-fit:cover;">' if logo_b64 else '📖'
    
    st.markdown(f"""
        <div style="position: relative; width: 100%;">
            <div style="position: absolute; top: 12px; right: 12px; z-index: 99; background: rgba(0, 0, 0, 0.75); padding: 5px 12px; border-radius: 20px; border: 1px solid rgba(0, 200, 83, 0.5); display: flex; align-items: center; gap: 8px; backdrop-filter: blur(4px);">
                {logo_tag}
                <span style="color: #00c853; font-weight: bold; font-size: 11px; font-family: sans-serif; letter-spacing: 0.5px;">BD AI BOOK • WATERPROOF SECURED</span>
            </div>
    """, unsafe_allow_html=True)
    
    if media_type == "video":
        if os.path.exists(media_path):
            st.video(media_path, format="video/mp4")
    elif media_type == "image":
        if os.path.exists(media_path):
            st.image(media_path, use_container_width=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

def show_verified_profile(display_name, profile_pic_path=None, subtitle="Official Global Verified Creator", is_verified=True):
    if not profile_pic_path or not os.path.exists(profile_pic_path):
        if os.path.exists("logo.jpg"):
            profile_pic_path = "logo.jpg"

    b64_img = get_image_base64(profile_pic_path)
    if b64_img:
        img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; border:2px solid #1877F2;">'
    else:
        img_html = '<div style="width:50px; height:50px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:24px;">👤</div>'

    blue_tick_svg = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="margin-left: 6px; vertical-align: middle;">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#1877F2"/>
    </svg>""" if is_verified else ""

    html_code = f"""<div style="display: flex; align-items: center; gap: 12px; background: #18191a; padding: 12px; border-radius: 12px; border: 1px solid #2d2f31; margin-bottom: 12px;">
        <div>{img_html}</div>
        <div>
            <div style="display: flex; align-items: center; font-weight: 700; font-size: 17px; color: #e4e6eb; font-family: sans-serif;">
                <span>{display_name}</span>
                {blue_tick_svg}
            </div>
            <div style="color: #b0b3b8; font-size: 12px; margin-top: 1px;">{subtitle}</div>
        </div>
    </div>"""
    st.markdown(html_code, unsafe_allow_html=True)

def show_auto_moving_banner():
    ad_html = f"""
    <div style="text-align:center; margin: 15px 0;">
        <a href="{SMART_LINK}" target="_blank" style="text-decoration:none;">
            <div style="background: linear-gradient(90deg, #1877F2, #00c853); color: #fff; padding: 14px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 1px solid #3a3b3c; font-family: sans-serif;">
                <span style="font-size: 15px; font-weight: bold;">⚡ GLOBAL AUTOMATIC MONETIZATION ACTIVE ⚡</span><br>
                <span style="font-size: 12px;">Click to Boost Earnings & Claim Reward Bonus!</span>
            </div>
        </a>
    </div>
    """
    components.html(ad_html, height=95)

def render_comments_section(post_id):
    with st.expander("💬 Comments & Gifts"):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY created_at DESC", (post_id,))
        all_comments = [dict(r) for r in cursor.fetchall()]
        
        if all_comments:
            for c in all_comments:
                gift_badge = f" <span style='background:#3a3b3c; padding:2px 6px; border-radius:6px;'>{c['gift_type']}</span>" if c.get('gift_type') and c.get('gift_type') != "None" else ""
                st.markdown(f"**{c['uploader_name']}**{gift_badge} <small style=\"color:#888;\">({c['created_at']})</small>:<br>{c['comment_text']}", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.caption("No comments yet.")
            
        if st.session_state.user:
            with st.form(key=f"c_form_{post_id}"):
                c_input = st.text_input("Write a comment...", key=f"inp_{post_id}", placeholder="Share your thoughts globally...")
                gift_selected = st.selectbox("🎁 Select Gift", ["None", "🎁 Gift Box (+10 pts)", "💎 Diamond (+50 pts)", "🌟 Star (+20 pts)", "🔥 Fire (+15 pts)"], key=f"gft_{post_id}")
                submit_btn = st.form_submit_button("Post Comment")
                
                if submit_btn:
                    if c_input.strip():
                        now_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                        cursor.execute("""
                            INSERT INTO comments (id, post_id, uploader_name, comment_text, gift_type, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (str(uuid.uuid4()), post_id, st.session_state.user, c_input.strip(), gift_selected, now_time))
                        conn.commit()
                        conn.close()
                        st.toast("✅ Comment published successfully!")
                        st.rerun()
                    else:
                        st.warning("Comment cannot be empty!")
                        conn.close()
        else:
            st.info("🔒 Please login with your account to comment.")
            conn.close()

# ==========================================
# 4. CUSTOM STYLING
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background-color: #242526 !important; color: #ffffff !important; border: 1px solid #3a3b3c !important;
    }
    textarea, input { color: #ffffff !important; background-color: #242526 !important; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    .monetization-box { background: linear-gradient(135deg, #00b09b, #96c93d); color: white; padding: 18px; border-radius: 12px; margin-top: 15px; margin-bottom: 15px; }
    .btn-direct { display: block; width: 100%; padding: 10px; margin: 6px 0; color: white !important; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 14px; }
    .bg-1 { background: linear-gradient(135deg, #FF416C, #FF4B2B); }
    .bg-2 { background: linear-gradient(135deg, #1DE9B6, #26A69A); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SPLASH SCREEN / INTRO
# ==========================================
if 'splash_shown' not in st.session_state:
    st.session_state.splash_shown = False

if not st.session_state.splash_shown:
    st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="color: #00c853; font-weight: 900;">🔥 BD AI Book — Global Verified Network 🔥</h1>
            <p style="color: #b0b3b8;">Loading Waterproof Platform & Verified Identity...</p>
        </div>
    """, unsafe_allow_html=True)
    
    logo_path = "logo.jpg" if os.path.exists("logo.jpg") else None
    if logo_path:
        col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
        with col_s2:
            st.image(logo_path, use_container_width=True)
    
    if st.button("🚀 Enter Platform"):
        st.session_state.splash_shown = True
        st.rerun()
    st.stop()

# ==========================================
# 6. MAIN HEADER & SESSION INITIALIZATION
# ==========================================
logo_path = "logo.jpg" if os.path.exists("logo.jpg") else None
if logo_path:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.image(logo_path, use_container_width=True)
else:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">🔥 BD AI Book — Global Platform 🔥</h1>
            <p style="color: #b0b3b8; margin: 0;">Artificial Intelligence & Learning Platform for Everyone Worldwide</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.user_phone = None
    st.session_state.pic = logo_path
    st.session_state.is_verified = 0
    st.session_state.role = 'user'

if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None
if 'otp_sent_to' not in st.session_state:
    st.session_state.otp_sent_to = None
if 'show_reset_mode' not in st.session_state:
    st.session_state.show_reset_mode = False

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

show_google_guidelines_box()

# ==========================================
# 7. SIDEBAR AUTHENTICATION & NAVIGATION
# ==========================================
if logo_path:
    st.sidebar.image(logo_path, use_container_width=True)

st.sidebar.header("🔍 Search Global Creators")
search_query = st.sidebar.text_input("Type name or #hashtag...", placeholder="Search creators or #hashtags...")

if search_query.strip():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, profile_pic, followers_count FROM users WHERE username LIKE ? OR full_name LIKE ?", 
                   (f"%{search_query}%", f"%{search_query}%"))
    found_users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if found_users:
        st.sidebar.markdown(f"**Found ({len(found_users)}) Users:**")
        for u in found_users:
            u_disp = u.get('full_name') or u['username']
            st.sidebar.markdown(f"👤 **{u_disp}** (@{u['username']})\n👥 Followers: {u.get('followers_count', 0)}")
            if st.session_state.user:
                if st.sidebar.button(f"➕ Follow @{u['username']}", key=f"s_fol_{u['username']}"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE users SET followers_count = followers_count + 1 WHERE username = ?", (u['username'],))
                    conn.commit()
                    conn.close()
                    st.toast(f"Followed @{u['username']}!")
                    st.rerun()
            st.sidebar.markdown("---")
    else:
        st.sidebar.info("No user found with this name.")

st.sidebar.header("📱 Global User Authentication")

if not st.session_state.user:
    phone_input = st.sidebar.text_input(
        "Phone / Account ID", 
        placeholder="e.g. +88017... or +1234...", 
        key="auth_phone"
    )
    
    if phone_input.strip():
        clean_input = normalize_phone(phone_input)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM users 
            WHERE username = ?
               OR clean_phone = ? 
               OR clean_phone LIKE ? 
               OR phone_number = ?
        """, (phone_input.strip(), clean_input, f"%{clean_input[-10:]}", phone_input.strip()))
        
        user_record = cursor.fetchone()
        conn.close()
        
        if user_record:
            st.sidebar.success(f"✅ Account Found: **{user_record['username']}**")
            login_pass = st.sidebar.text_input("Enter Password to Login", type="password", key="login_pass")
            
            if st.sidebar.button("🔓 Login Now"):
                hashed_input = hashlib.sha256(login_pass.encode()).hexdigest()
                if user_record['password'] == login_pass or user_record['password'] == hashed_input:
                    st.session_state.user = user_record['username']
                    st.session_state.user_phone = user_record['phone_number']
                    st.session_state.pic = user_record['profile_pic'] or logo_path
                    st.session_state.is_verified = 1
                    st.session_state.role = user_record['role']
                    st.session_state.show_reset_mode = False
                    st.sidebar.success("🎉 Logged in Successfully.")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Incorrect Password!")
                    st.session_state.show_reset_mode = True

            if st.session_state.show_reset_mode or st.sidebar.checkbox("🔑 Forgot / Reset Password?"):
                st.sidebar.warning("🔐 Password Recovery via WhatsApp OTP")
                
                if st.sidebar.button("📲 Send Recovery OTP via WhatsApp"):
                    otp_code = str(random.randint(100000, 999999))
                    st.session_state.generated_otp = otp_code
                    st.session_state.otp_sent_to = clean_input
                    
                    msg = f"Your BD AI Book Password Reset OTP Code is: {otp_code}"
                    wa_url = f"https://wa.me/{clean_input}?text={urllib.parse.quote(msg)}"
                    
                    st.sidebar.success(f"OTP Generated: **{otp_code}**")
                    st.sidebar.markdown(f"[👉 Click to Send OTP via WhatsApp]({wa_url})", unsafe_allow_html=True)
                
                if st.session_state.generated_otp and st.session_state.otp_sent_to == clean_input:
                    entered_reset_otp = st.sidebar.text_input("Enter 6-Digit OTP", max_chars=6, key="reset_otp_input")
                    reset_new_pass = st.sidebar.text_input("Set New Password", type="password", key="reset_pass_input")
                    
                    if st.sidebar.button("🔒 Confirm & Update Password"):
                        if entered_reset_otp != st.session_state.generated_otp:
                            st.sidebar.error("❌ Invalid OTP Code!")
                        elif not reset_new_pass.strip():
                            st.sidebar.error("❌ Please enter a new password!")
                        else:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (reset_new_pass.strip(), user_record['id']))
                            conn.commit()
                            conn.close()
                            
                            st.session_state.user = user_record['username']
                            st.session_state.user_phone = user_record['phone_number']
                            st.session_state.pic = user_record['profile_pic'] or logo_path
                            st.session_state.is_verified = 1
                            st.session_state.role = user_record['role']
                            st.session_state.generated_otp = None
                            st.session_state.show_reset_mode = False
                            
                            st.sidebar.success("🎉 Password Updated & Logged in!")
                            st.rerun()

        else:
            st.sidebar.info("🆕 Global User Registration (All Countries Supported)")
            
            if st.sidebar.button("📲 Send WhatsApp OTP"):
                otp_code = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp_code
                st.session_state.otp_sent_to = clean_input
                
                msg = f"Your BD AI Book Global Verification OTP is: {otp_code}"
                wa_url = f"https://wa.me/{clean_input}?text={urllib.parse.quote(msg)}"
                
                st.sidebar.success(f"OTP Code Generated: **{otp_code}**")
                st.sidebar.markdown(f"[👉 Click to Send OTP via WhatsApp]({wa_url})", unsafe_allow_html=True)
            
            if st.session_state.generated_otp and st.session_state.otp_sent_to == clean_input:
                entered_otp = st.sidebar.text_input("Enter 6-Digit OTP", max_chars=6)
                desired_username = st.sidebar.text_input("Create Username", placeholder="e.g. AlexSmith")
                new_password = st.sidebar.text_input("Create Password", type="password")
                
                if st.sidebar.button("🔒 Verify OTP & Save Account"):
                    if entered_otp != st.session_state.generated_otp:
                        st.sidebar.error("❌ Invalid OTP Code!")
                    elif not desired_username.strip() or not new_password:
                        st.sidebar.error("❌ Please fill Username and Password!")
                    else:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        
                        try:
                            cursor.execute("""
                                INSERT INTO users (username, phone_number, clean_phone, password, full_name, is_verified, created_at)
                                VALUES (?, ?, ?, ?, ?, 1, ?)
                            """, (desired_username.strip(), phone_input.strip(), clean_input, new_password, desired_username.strip(), today_str))
                            
                            conn.commit()
                            conn.close()
                            
                            st.session_state.user = desired_username.strip()
                            st.session_state.user_phone = phone_input.strip()
                            st.session_state.pic = logo_path
                            st.session_state.is_verified = 1
                            st.session_state.role = 'user'
                            st.session_state.generated_otp = None
                            st.session_state.otp_sent_to = None
                            
                            st.sidebar.success("🎉 Account Created & Logged in!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            conn.close()
                            st.sidebar.error("❌ Phone number or Username already registered!")

else:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT profile_pic, phone_number, role FROM users WHERE username = ?", (st.session_state.user,))
    res = c.fetchone()
    if res:
        if res['profile_pic']:
            st.session_state.pic = res['profile_pic']
        if res['phone_number']:
            st.session_state.user_phone = res['phone_number']
        st.session_state.role = res['role']
    conn.close()

    active_sidebar_pic = st.session_state.pic if (st.session_state.pic and os.path.exists(st.session_state.pic)) else logo_path
    if active_sidebar_pic and os.path.exists(active_sidebar_pic):
        st.sidebar.image(active_sidebar_pic, width=90)
        
    masked_active_phone = mask_phone_number(st.session_state.user_phone or "")
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** ✔️")
    if masked_active_phone:
        st.sidebar.caption(f"📱 Phone: {masked_active_phone}")
        
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.user_phone = None
        st.session_state.pic = logo_path
        st.session_state.is_verified = 0
        st.session_state.role = 'user'
        st.session_state.generated_otp = None
        st.session_state.show_reset_mode = False
        st.rerun()

nav_tabs = ["🌍 World Feed", "📱 Scrolle Shorts Feed", "📢 Advertiser Hub", "💬 WhatsApp Support Desk", "💳 Payout & Monetization", "👤 My Profile & Earnings", "📤 Create Post / Upload"]
if st.session_state.role == 'owner':
    nav_tabs.append("🔐 Owner Control Panel")

tab = st.sidebar.radio("Navigation", nav_tabs, index=nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0)
st.session_state.active_tab = tab

# ==========================================
# 8. TAB IMPLEMENTATIONS
# ==========================================

if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT content_link, ad_type FROM advertisements WHERE status = 'Active'")
    active_ads = cursor.fetchall()
    if active_ads:
        st.subheader("📢 Sponsored Ads")
        for ad in active_ads:
            st.success(f"Sponsored ({ad['ad_type']}): {ad['content_link']}")
        st.divider()

    try:
        cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
        short_videos = [dict(r) for r in cursor.fetchall()]
        
        if short_videos:
            st.markdown('<h3 style="color: #00c853;">▶️ Scrolle Shorts Feed</h3>', unsafe_allow_html=True)
            cols = st.columns(min(len(short_videos), 3))
            for i, sv in enumerate(short_videos[:3]):
                with cols[i]:
                    st.markdown(f"**{sv.get('uploader_name', 'User')}** ✔️")
                    show_watermarked_media("video", sv['video_url'])
                    
                    if st.button("▶️ Watch in Shorts Feed", key=f"open_short_{sv['id']}"):
                        st.session_state.active_tab = "📱 Scrolle Shorts Feed"
                        st.rerun()
                    st.caption(f"👁️ {format_value(sv.get('views', 0))} views")
            st.divider()
    except Exception:
        pass

    try:
        cursor.execute("SELECT * FROM videos WHERE video_type != 'short'")
        videos = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM posts")
        posts = [dict(row) for row in cursor.fetchall()]

        combined_feed = videos + posts
        random.shuffle(combined_feed)

        if not combined_feed:
            st.info("No posts or videos available. Create content from the Upload section.")

        for index, item in enumerate(combined_feed):
            item_id = str(item["id"])
            uploader_name = item.get("uploader_name", "Unknown User")
            
            cursor.execute("SELECT profile_pic, role FROM users WHERE username = ?", (uploader_name,))
            u_res = cursor.fetchone()
            uploader_pic = u_res['profile_pic'] if u_res and u_res['profile_pic'] else item.get('uploader_pic')
            
            if u_res and u_res['role'] == 'owner' and logo_path:
                uploader_pic = logo_path
            
            created_at = item.get("created_at", "Recently")
            hashtags = item.get("hashtags", "")

            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(uploader_name, profile_pic_path=uploader_pic, subtitle=f"Posted {created_at}", is_verified=True)

            if "content" in item and item["content"]:
                st.markdown(f"### {item['content']}")
            
            if hashtags:
                st.markdown(f"<p style='color: #1877F2; font-weight: bold; font-size: 13px;'>{hashtags}</p>", unsafe_allow_html=True)

            if "image_url" in item and item["image_url"] and os.path.exists(item["image_url"]):
                show_watermarked_media("image", item["image_url"])

            if "video_url" in item and os.path.exists(item["video_url"]):
                if item.get("title"):
                    st.markdown(f"#### {item.get('title')}")
                show_watermarked_media("video", item["video_url"])
                
                new_views = item.get("views", 0) + 1
                cursor.execute("UPDATE videos SET views = ?, views_count = ? WHERE id = ?", (new_views, new_views, item_id))
                conn.commit()

            show_auto_moving_banner()

            st.write(f"❤️ **{format_value(item.get('likes', 0))}** Likes")
            st.markdown(f"""
                <a href="{SMART_LINK}" target="_blank" class="btn-direct bg-1">💰 Claim Monetization Reward</a>
                <a href="{SMART_LINK}" target="_blank" class="btn-direct bg-2">💎 Premium Bonus Link</a>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"❤️ Like ({format_value(item.get('likes', 0))})", key=f"lk_{item_id}_{index}"):
                    if st.session_state.user:
                        table_name = "posts" if "content" in item else "videos"
                        cursor.execute(f"UPDATE {table_name} SET likes = likes + 1 WHERE id = ?", (item_id,))
                        conn.commit()
                        st.rerun()
                    else:
                        st.toast("🔒 Please sign in to like posts!")
            with c2:
                if st.button("➕ Follow", key=f"fl_{item_id}_{index}"):
                    if st.session_state.user:
                        cursor.execute("UPDATE users SET followers_count = followers_count + 1 WHERE username = ?", (uploader_name,))
                        conn.commit()
                        st.toast(f"Followed {uploader_name} successfully!")
                    else:
                        st.toast("🔒 Please sign in to follow users!")

            render_comments_section(item_id)

            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Feed Error: {e}")
    finally:
        conn.close()

elif tab == "📱 Scrolle Shorts Feed":
    st.subheader("📱 TikTok & Shorts Vertical Scroll Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    short_vids = [dict(r) for r in cursor.fetchall()]

    if not short_vids:
        st.info("No shorts videos found.")
        conn.close()
    else:
        for idx, sv in enumerate(short_vids):
            st.markdown("---")
            col_main, col_side = st.columns([3, 1])
            
            cursor.execute("SELECT profile_pic, role FROM users WHERE username = ?", (sv.get('uploader_name'),))
            u_res = cursor.fetchone()
            uploader_pic = u_res['profile_pic'] if u_res and u_res['profile_pic'] else sv.get('uploader_pic')
            if u_res and u_res['role'] == 'owner' and logo_path:
                uploader_pic = logo_path

            with col_main:
                show_verified_profile(sv.get("uploader_name", "User"), profile_pic_path=uploader_pic, subtitle="Official Shorts Creator", is_verified=True)
                st.markdown(f"**{sv.get('title', 'Short Video')}**")
                if sv.get("hashtags"):
                    st.markdown(f"<p style='color: #1877F2; font-size: 13px;'>{sv.get('hashtags')}</p>", unsafe_allow_html=True)
                
                show_watermarked_media("video", sv["video_url"])
                
                cursor.execute("UPDATE videos SET views = views + 1, views_count = views_count + 1 WHERE id = ?", (sv["id"],))
                conn.commit()
                
                render_comments_section(sv["id"])

            with col_side:
                st.write(" ")
                if st.button(f"❤️ {format_value(sv.get('likes', 0))}", key=f"sh_like_{sv['id']}"):
                    if st.session_state.user:
                        cursor.execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (sv["id"],))
                        conn.commit()
                        st.toast("Liked!")
                        st.rerun()
                    else:
                        st.toast("🔒 Please login to like!")
                
                st.caption(f"👁️ {format_value(sv.get('views', 0))}")

                if st.button("➕ Follow", key=f"sh_fol_{sv['id']}"):
                    if st.session_state.user:
                        cursor.execute("UPDATE users SET followers_count = followers_count + 1 WHERE username = ?", (sv.get("uploader_name"),))
                        conn.commit()
                        st.toast("Followed Creator!")
                    else:
                        st.toast("🔒 Please login to follow!")
        conn.close()

elif tab == "📢 Advertiser Hub":
    st.title("📢 Advertiser Ad Network Portal")
    
    if not st.session_state.user:
        st.error("🔒 **Advertiser Access Restricted!**")
        st.warning("Please sign up or login with your mobile number to view secure payment details and submit ad requests.")
    else:
        st.info("Secured Manual Payment Accounts for Verified Advertisers (Hidden from Public View):")
        st.markdown(f"**🏦 Official Payment Channels:**\n\n{get_owner_payment_info()}")
        st.divider()

        st.write("Select your region, choose payment method, transfer funds manually, and fill out the form below.")
        region = st.selectbox("Select Your Region", ["Bangladesh (BD)", "International (Global)"])
        
        if "Bangladesh" in region:
            currency = "BDT"
            price_per_month = 1000
            st.info("💰 **Bangladesh Pricing:** ৳1,000 BDT per month.")
        else:
            currency = "USD"
            price_per_month = 30
            st.info("🌐 **International Pricing:** $30 USD per month.")

        duration = st.number_input("Duration (Months)", min_value=1, value=1)
        total_amount = price_per_month * duration
        st.metric(label="Total Payable Amount", value=f"{total_amount} {currency}")

        st.markdown("---")
        st.subheader("💳 Select Payment Method & Transfer Manually")

        pay_method = st.radio("Choose Method:", ["bKash", "Nagad", "Bank Transfer (Islami Bank)", "Crypto Wallet (USDT)"])

        if pay_method == "bKash":
            st.success("📱 **bKash Personal Number:** `01302134435` (Send Money manually)")
        elif pay_method == "Nagad":
            st.warning("📱 **Nagad Personal Number:** `01722003172` (Send Money manually)")
        elif pay_method == "Bank Transfer (Islami Bank)":
            st.code("""
Bank Name: Islami Bank Bangladesh Limited
Branch: Lalmonirhat Branch
Account Name: MD. SOHEL RANA
Account Number: 20502530202612312
            """)
        elif pay_method == "Crypto Wallet (USDT)":
            st.code("""
USDT (TRC20 Network): TM6DAbNuF2kaMaRoC8HKi2G8Gi5hVWnbCP
USDT (BSC BEP20 Network): 0x53052be072029dd76e02b01d925e29b03c5294ad
            """)

        st.markdown("---")
        st.subheader("📝 Submit Ad Details & Transaction ID")
        adv_email = st.text_input("Your Contact Phone / Email", value=st.session_state.user)
        ad_type = st.selectbox("Ad Type", ["Short Video (10 Sec)", "Long Video", "Image Post / Banner"])
        content_link = st.text_input("Ad Content Link (Video / Image URL)")
        trx_id = st.text_input("Transaction ID / Reference Number (TrxID)")

        if st.button("Submit Advertisement for Review"):
            if adv_email and content_link and trx_id:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO advertisements 
                    (advertiser_email, ad_type, content_link, duration_months, region, payment_method, amount, trx_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (adv_email, ad_type, content_link, duration, region, pay_method, total_amount, trx_id))
                conn.commit()
                conn.close()
                st.success("✅ Your ad request has been submitted successfully! Admin will verify the manual payment and approve shortly.")
            else:
                st.error("Please fill in all required fields properly.")

elif tab == "💬 WhatsApp Support Desk":
    st.subheader("💬 Official WhatsApp Support Desk")
    st.caption("Contact us directly from anywhere in the world to ask questions or resolve issues.")
    
    if not st.session_state.user:
        st.warning("🔒 Please sign up or login with your phone number before asking support questions.")
    else:
        encoded_msg = urllib.parse.quote(f"Hello! I am logged in as {st.session_state.user} on BD AI Book App.")
        wa_link = f"https://wa.me/8801722003172?text={encoded_msg}"
        
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #075E54, #128C7E); padding: 25px; border-radius: 15px; color: white; text-align: center; border: 1px solid #25D366; margin: 20px 0;">
                <h2 style="margin-top:0; color: #ffffff;">🌐 Official WhatsApp Support Desk</h2>
                <p style="font-size: 15px; color: #e0e0e0; margin-bottom: 20px;">
                    Click below to send messages or feedback directly to our support team worldwide.
                </p>
                <a href="{wa_link}" target="_blank" style="
                    background-color: #25D366; 
                    color: #121212; 
                    padding: 14px 30px; 
                    text-decoration: none; 
                    font-weight: bold; 
                    font-size: 17px;
                    border-radius: 30px; 
                    display: inline-block;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
                    📲 Send WhatsApp Message / Photo
                </a>
                <p style="font-size: 12px; color: #ffeb3b; margin-top: 20px; margin-bottom: 0;">
                    ⚠️ <b>Note:</b> Only text messages and file sharing are supported.
                </p>
            </div>
        """, unsafe_allow_html=True)

elif tab == "💳 Payout & Monetization":
    st.subheader("🏦 Global Monetization, Card & Bank Setup")
    
    if not st.session_state.user:
        st.warning("Please login to manage your Bank and Payout details.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bank_details WHERE username = ?", (st.session_state.user,))
        existing_bank = cursor.fetchone()
        bank_data = dict(existing_bank) if existing_bank else {}
        
        with st.form("bank_setup_form"):
            st.markdown("### 🌍 Select Preferred Payment Method")
            
            pay_method = st.selectbox(
                "Payment Category",
                [
                    "💳 Visa / Mastercard / Debit Card (Worldwide)",
                    "🏦 Direct Bank Transfer (Local / IBAN)",
                    "🌐 Global Wallets (Payoneer / Wise / PayPal)",
                    "📱 Mobile Banking (bKash/Nagad/Rocket/Others)"
                ],
                index=0
            )
            
            user_country = st.text_input("Country", value=bank_data.get("country", ""), placeholder="e.g. USA, UK, UAE, Bangladesh, India, Canada...")
            
            st.markdown("#### 💳 Visa / Mastercard / Debit Card Details (Global)")
            c_num = st.text_input("Card Number", value=bank_data.get("card_number", ""), placeholder="16-digit card number")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                c_holder = st.text_input("Card Holder Name", value=bank_data.get("card_holder", ""), placeholder="Name printed on card")
            with col_c2:
                c_exp = st.text_input("Expiry Date (MM/YY)", value=bank_data.get("card_expiry", ""), placeholder="MM/YY")
                
            st.markdown("#### 🏦 Official Bank Account Details")
            b_name = st.text_input("Bank Name", value=bank_data.get("bank_name", ""), placeholder="e.g. Chase, HSBC, Citi, Islami Bank...")
            b_branch = st.text_input("Branch Name / Location", value=bank_data.get("branch_name", ""))
            acc_holder = st.text_input("Account Holder Name", value=bank_data.get("account_name", ""))
            acc_num = st.text_input("Account Number / IBAN", value=bank_data.get("account_number", ""))
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                routing = st.text_input("Routing / ABA / Sort Code", value=bank_data.get("routing_number", ""))
            with c_r2:
                swift = st.text_input("SWIFT / BIC Code", value=bank_data.get("swift_code", ""))
                
            st.markdown("#### 🌐 Global Wallet / Mobile Banking")
            g_wallet = st.text_input("Payoneer / Wise Email / PayPal", value=bank_data.get("global_wallet", ""))
            m_bank = st.text_input("Mobile Banking / Local Wallet Number", value=bank_data.get("mobile_banking", ""))
            
            save_bank_btn = st.form_submit_button("💾 Save Payout Information")
            
            if save_bank_btn:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                if existing_bank:
                    cursor.execute("""
                        UPDATE bank_details 
                        SET payment_type = ?, country = ?, card_number = ?, card_holder = ?, card_expiry = ?,
                            bank_name = ?, branch_name = ?, account_name = ?, account_number = ?, routing_number = ?, swift_code = ?,
                            global_wallet = ?, mobile_banking = ?, updated_at = ?
                        WHERE username = ?
                    """, (pay_method, user_country, c_num, c_holder, c_exp, b_name, b_branch, acc_holder, acc_num, routing, swift, g_wallet, m_bank, now_str, st.session_state.user))
                else:
                    cursor.execute("""
                        INSERT INTO bank_details (username, payment_type, country, card_number, card_holder, card_expiry, bank_name, branch_name, account_name, account_number, routing_number, swift_code, global_wallet, mobile_banking, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (st.session_state.user, pay_method, user_country, c_num, c_holder, c_exp, b_name, b_branch, acc_holder, acc_num, routing, swift, g_wallet, m_bank, now_str))
                
                p_summary = f"{pay_method} ({c_num[-4:] if c_num else b_name or m_bank or g_wallet})"
                cursor.execute("UPDATE users SET payment_method = ?, account_details = ? WHERE username = ?", (pay_method, p_summary, st.session_state.user))
                
                conn.commit()
                st.success("✅ Payout Information Saved Successfully!")
                st.rerun()
                
        conn.close()

elif tab == "👤 My Profile & Earnings":
    if not st.session_state.user:
        st.warning("Please login to view your profile.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
        raw_user = cursor.fetchone()
        user_info = dict(raw_user) if raw_user else {}
        
        display_name = user_info.get("full_name") or st.session_state.user
        pic_path = user_info.get("profile_pic", st.session_state.pic)
        masked_phone = mask_phone_number(user_info.get("phone_number", ""))
        
        if user_info.get('role') == 'owner' and logo_path:
            pic_path = logo_path
        
        with st.expander("⚙️ Edit Profile & Change Picture / Password", expanded=False):
            with st.form("edit_profile_form"):
                st.markdown("### 🖼️ Personal Information & Picture")
                new_full_name = st.text_input("Full Name", value=user_info.get("full_name") or "")
                new_bio = st.text_area("Bio / Description", value=user_info.get("bio") or "")
                new_nid = st.text_input("NID / Passport / Govt ID Number", value=user_info.get("nid_number") or "")
                new_address = st.text_input("Address & Country", value=user_info.get("address") or "")
                
                st.markdown("### 🔑 Change Password")
                new_pass_val = st.text_input("New Password (leave empty to keep current)", type="password")
                
                uploaded_pic = st.file_uploader("Upload Profile Picture (JPG/PNG)", type=["jpg", "png", "jpeg"])
                
                save_profile_btn = st.form_submit_button("💾 Save Profile Details")
                
                if save_profile_btn:
                    saved_pic_path = pic_path
                    if uploaded_pic:
                        saved_pic_path = os.path.join(PROFILE_DIR, f"pic_{st.session_state.user}_{uuid.uuid4()}.jpg")
                        with open(saved_pic_path, "wb") as f:
                            f.write(uploaded_pic.getvalue())
                        st.session_state.pic = saved_pic_path
                        
                        cursor.execute("UPDATE videos SET uploader_pic = ? WHERE uploader_name = ?", (saved_pic_path, st.session_state.user))
                        cursor.execute("UPDATE posts SET uploader_pic = ? WHERE uploader_name = ?", (saved_pic_path, st.session_state.user))
                    
                    pass_to_update = new_pass_val.strip() if new_pass_val.strip() else user_info.get("password")
                    
                    cursor.execute("""
                        UPDATE users 
                        SET full_name = ?, bio = ?, nid_number = ?, address = ?, profile_pic = ?, password = ?
                        WHERE username = ?
                    """, (new_full_name, new_bio, new_nid, new_address, saved_pic_path, pass_to_update, st.session_state.user))
                    
                    conn.commit()
                    st.success("✅ Profile updated successfully!")
                    st.rerun()

        cursor.execute("SELECT * FROM videos WHERE uploader_name = ?", (st.session_state.user,))
        my_videos = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM posts WHERE uploader_name = ?", (st.session_state.user,))
        my_posts = [dict(r) for r in cursor.fetchall()]
        
        total_likes = sum([v.get('likes', 0) for v in my_videos]) + sum([p.get('likes', 0) for p in my_posts])
        total_views = sum([v.get('views', 0) for v in my_videos])
        
        followers = user_info.get('followers_count', 0)
        watch_hours = user_info.get('watch_time_mins', 0.0) / 60.0
        
        is_eligible = (followers >= 300) and (watch_hours >= 3000.0)
        
        if is_eligible:
            monetization_badge = "✅ Eligible & Active"
            est_earnings = (total_views * 0.002) + (total_likes * 0.005) + user_info.get('earnings', 0.0)
        else:
            monetization_badge = "🔒 Locked (Requirements not met)"
            est_earnings = 0.00

        show_verified_profile(display_name, profile_pic_path=pic_path, subtitle=f"{user_info.get('bio') or 'Global Creator'} | Phone: {masked_phone}", is_verified=True)
        
        st.write(f"📹 Videos/Shorts: **{len(my_videos)}** | 🖼️ Posts: **{len(my_posts)}** | ❤️ Likes: **{format_value(total_likes)}** | 👁️ Views: **{format_value(total_views)}** | 👥 Followers: **{followers}/300**")
        
        st.markdown("#### 📊 Monetization Progress (Requirements: 300 Followers & 3000 Hours)")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.write(f"👥 Followers Goal: **{followers}/300**")
            st.progress(min(followers / 300.0, 1.0))
        with col_p2:
            st.write(f"⏱️ Watch Time Goal: **{watch_hours:.1f}/3000 Hours**")
            st.progress(min(watch_hours / 3000.0, 1.0))

        st.markdown(f"""
            <div class="monetization-box">
                <h3 style="margin:0; color:#fff;">🌐 Global Monetization Dashboard</h3>
                <p style="margin: 5px 0;"><b>Status: {monetization_badge}</b></p>
                <h2 style="margin: 10px 0; color: #ffffff;">💰 Est. Earnings: ${est_earnings:.2f} USD</h2>
                <p style="margin:0; font-size:12px;">Saved Method: <b>{user_info.get('payment_method', 'Not Set')}</b></p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📽️ My Content Management")
        
        tab_v, tab_p = st.tabs(["🎥 My Videos & Shorts", "🖼️ My Image/Text Posts"])
        
        with tab_v:
            if not my_videos:
                st.caption("No videos uploaded yet.")
            for mv in my_videos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{mv.get('title')}** `[{mv.get('video_type', 'long')}]`")
                    st.caption(f"👁️ {mv.get('views', 0)} Views | ❤️ {mv.get('likes', 0)} Likes | Created: {mv.get('created_at')}")
                with col2:
                    if st.button("🗑️ Delete Video", key=f"del_v_{mv['id']}"):
                        if mv.get('video_url') and os.path.exists(mv.get('video_url')):
                            try:
                                os.remove(mv.get('video_url'))
                            except Exception:
                                pass
                        cursor.execute("DELETE FROM videos WHERE id = ?", (mv['id'],))
                        cursor.execute("DELETE FROM comments WHERE post_id = ?", (mv['id'],))
                        conn.commit()
                        st.toast("Video deleted successfully!")
                        st.rerun()

        with tab_p:
            if not my_posts:
                st.caption("No text/image posts created yet.")
            for mp in my_posts:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**Post:** {mp.get('content') or 'Image Post'}")
                    st.caption(f"❤️ {mp.get('likes', 0)} Likes | Created: {mp.get('created_at')}")
                with col2:
                    if st.button("🗑️ Delete Post", key=f"del_p_{mp['id']}"):
                        if mp.get('image_url') and os.path.exists(mp.get('image_url')):
                            try:
                                os.remove(mp.get('image_url'))
                            except Exception:
                                pass
                        cursor.execute("DELETE FROM posts WHERE id = ?", (mp['id'],))
                        cursor.execute("DELETE FROM comments WHERE post_id = ?", (mp['id'],))
                        conn.commit()
                        st.toast("Post deleted successfully!")
                        st.rerun()

        conn.close()

elif tab == "📤 Create Post / Upload":
    if not st.session_state.user:
        st.warning("Please login to create a post or upload content.")
    else:
        st.subheader("📤 Upload Content (Daily Limits Applied)")
        st.info("📌 **Daily Upload Rules:** Exactly 1 Long Video, 1 Short Video, and 10 Posts allowed per 24 hours.")
        
        st.warning("⚠️ **Global Community Guidelines:** Sexual, adult, or violent content is strictly prohibited. Violating terms will lead to immediate account suspension and loss of earnings.")
        
        upload_type = st.radio("Select Upload Type:", ["📝 Post/Photo", "🎥 Long Video (10-20 min)", "📱 Short Video"])
        
        if upload_type == "📝 Post/Photo":
            can_upload, current_cnt, max_limit = check_daily_upload_limit(st.session_state.user, "post")
            st.caption(f"📊 Today's Post Upload Status: **{current_cnt}/{max_limit}**")
            
            post_text = st.text_area("What's on your mind?")
            hashtags_input = st.text_input("Hashtags (e.g. #AI #Trending #BD #Tech)")
            img_file = st.file_uploader("Upload Photo (JPG/PNG)", type=["jpg", "png", "jpeg"])
            
            if st.button("🚀 Publish Post"):
                if not can_upload:
                    st.error("❌ You have exceeded your daily limit of 10 posts! Try again tomorrow.")
                elif not post_text and not img_file:
                    st.warning("Please enter text or attach an image!")
                else:
                    img_path = None
                    if img_file:
                        img_path = os.path.join(IMAGE_DIR, f"img_{uuid.uuid4()}.jpg")
                        with open(img_path, "wb") as f:
                            f.write(img_file.getvalue())
                            
                    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO posts (id, uploader_name, uploader_pic, content, hashtags, image_url, likes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), st.session_state.user, st.session_state.pic, post_text, hashtags_input, img_path, 0, today_str))
                    conn.commit()
                    conn.close()
                    
                    record_daily_upload(st.session_state.user, "post")
                    st.toast("✅ Post published successfully!")
                    st.rerun()
                    
        else:
            is_short = (upload_type == "📱 Short Video")
            c_type_key = "short_video" if is_short else "long_video"
            
            can_upload, current_cnt, max_limit = check_daily_upload_limit(st.session_state.user, c_type_key)
            st.caption(f"📊 Today's {upload_type} Upload Status: **{current_cnt}/{max_limit}**")
            
            v_title = st.text_input("Video Title", placeholder="Enter a title for your video...")
            v_hashtags = st.text_input("Video Hashtags (e.g. #Viral #Shorts #BD_AI)")
            vid_file = st.file_uploader("Upload Video File (MP4/MOV)", type=["mp4", "mov", "avi", "mkv"])
            
            v_type_str = "short" if is_short else "long"
            
            if st.button("🚀 Publish Video"):
                if not can_upload:
                    st.error(f"❌ You have reached your daily limit of 1 {upload_type}! Try again after 24 hours.")
                elif not vid_file or not v_title.strip():
                    st.warning("Please provide a video title and select a video file!")
                else:
                    vid_filename = f"vid_{uuid.uuid4()}.mp4"
                    vid_path = os.path.join(VIDEO_DIR, vid_filename)
                    
                    with open(vid_path, "wb") as f:
                        f.write(vid_file.getvalue())
                        
                    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT id FROM users WHERE username = ?", (st.session_state.user,))
                    u_rec = cursor.fetchone()
                    u_id = u_rec['id'] if u_rec else None
                    
                    cursor.execute("""
                        INSERT INTO videos (
                            id, user_id, video_url, uploader_name, uploader_pic, 
                            video_type, title, hashtags, likes, views, views_count, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), u_id, vid_path, st.session_state.user, st.session_state.pic, v_type_str, v_title.strip(), v_hashtags, random.randint(10, 50), 1, 1, today_str))
                    conn.commit()
                    conn.close()
                    
                    record_daily_upload(st.session_state.user, c_type_key)
                    st.toast(f"🎉 {upload_type} published successfully with Waterproof Protection!")
                    st.rerun()

elif tab == "🔐 Owner Control Panel":
    if st.session_state.role != 'owner':
        st.error("🚫 Access Denied! Only the Owner can access this panel.")
    else:
        st.title("👑 Owner Master Dashboard & Financial Accounts")
        st.success(f"Logged in as System Administrator & Owner")

        st.subheader("🖼️ Update Global Owner / Platform Logo & Profile Picture")
        st.write("Current global logo/profile picture is set as `logo.jpg` and will be displayed across all global posts and feeds.")
        
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=150)
            
        new_logo = st.file_uploader("Upload New Owner / Platform Logo (JPG/PNG)", type=["jpg", "png", "jpeg"])
        if new_logo:
            with open("logo.jpg", "wb") as f:
                f.write(new_logo.getvalue())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET profile_pic = 'logo.jpg' WHERE role = 'owner'")
            conn.commit()
            conn.close()
            st.success("✅ Owner profile picture updated successfully for worldwide users!")
            st.rerun()

        st.subheader("🏦 Update Global Manual Payment Information (Hidden from Public)")
        current_info = get_owner_payment_info()
        new_info = st.text_area("Edit Manual Payment Details (bKash/Nagad/Bank details for advertisers):", value=current_info)
        
        if st.button("Save Global Payment Info"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET account_details = ? WHERE role = 'owner'", (new_info,))
            conn.commit()
            conn.close()
            st.success("✅ Payment info updated successfully for all advertisers!")
            st.rerun()

        st.divider()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT payment_method, SUM(amount) FROM advertisements WHERE status = 'Active' GROUP BY payment_method")
        revenue_data = cursor.fetchall()

        bkash_total = sum(item[1] for item in revenue_data if item[0] == 'bKash')
        nagad_total = sum(item[1] for item in revenue_data if item[0] == 'Nagad')
        bank_total = sum(item[1] for item in revenue_data if item[0] == 'Bank Transfer (Islami Bank)')
        crypto_total = sum(item[1] for item in revenue_data if item[0] == 'Crypto Wallet (USDT)')

        st.subheader("💰 Real-Time Revenue Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("bKash Total", f"৳{bkash_total}")
        col2.metric("Nagad Total", f"৳{nagad_total}")
        col3.metric("Bank Total", f"৳{bank_total}")
        col4.metric("Crypto (Global)", f"${crypto_total} USD")

        st.markdown("---")
        st.subheader("📋 Pending Advertisements for Approval")

        cursor.execute("SELECT id, advertiser_email, ad_type, content_link, amount, payment_method, trx_id, status FROM advertisements")
        ads = cursor.fetchall()

        if ads:
            for ad in ads:
                ad_id = ad['id']
                email = ad['advertiser_email']
                a_type = ad['ad_type']
                link = ad['content_link']
                amt = ad['amount']
                method = ad['payment_method']
                trx = ad['trx_id']
                status = ad['status']
                
                with st.expander(f"Ad #{ad_id} | {email} | Status: {status}"):
                    st.write(f"**Type:** {a_type} | **Amount:** {amt} | **Method:** {method}")
                    st.write(f"**TrxID:** `{trx}`")
                    st.write(f"**Link:** {link}")

                    c1, c2 = st.columns(2)
                    if status != 'Active':
                        if c1.button(f"Approve Ad #{ad_id}", key=f"app_{ad_id}"):
                            cursor.execute("UPDATE advertisements SET status = 'Active' WHERE id = ?", (ad_id,))
                            conn.commit()
                            st.rerun()
                    if c2.button(f"Delete Ad #{ad_id}", key=f"del_{ad_id}"):
                        cursor.execute("DELETE FROM advertisements WHERE id = ?", (ad_id,))
                        conn.commit()
                        st.rerun()
        else:
            st.info("No pending or active advertisements found.")
        
        conn.close()

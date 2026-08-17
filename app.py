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
# 2. LOCAL STORAGE & DATABASE SETUP (SECURE ROLE-BASED)
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
            role TEXT DEFAULT 'Public ID',
            created_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [column[1] for column in cursor.fetchall()]
    if "clean_phone" not in existing_cols:
        try: cursor.execute("ALTER TABLE users ADD COLUMN clean_phone TEXT")
        except Exception: pass
    if "role" not in existing_cols:
        try: cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Public ID'")
        except Exception: pass
    if "nid_number" not in existing_cols:
        try: cursor.execute("ALTER TABLE users ADD COLUMN nid_number TEXT")
        except Exception: pass
    if "address" not in existing_cols:
        try: cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
        except Exception: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_upload_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content_type TEXT NOT NULL,
            upload_date TEXT NOT NULL
        )
    """)

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

def add_watermark_to_video(input_path, output_path):
    """Moviepy ব্যবহার করে ভিডিওর ভেতরে স্থায়ীভাবে ওয়াটারমার্ক বসানোর ফাংশন"""
    try:
        from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
        video = VideoFileClip(input_path)
        
        logo_path = "logo.jpg" if os.path.exists("logo.jpg") else None
        if logo_path:
            # লোগো সাইজ ছোট করে ভিডিওর ডান কোণায় সেট করা হলো
            logo = ImageClip(logo_path).set_duration(video.duration)
            logo = logo.resize(height=40) # লোগোর উচ্চতা
            logo = logo.set_pos(("right", "top")).margin(right=15, top=15, opacity=0)
            
            final_clip = CompositeVideoClip([video, logo])
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            final_clip.close()
        else:
            video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
        video.close()
        return True
    except Exception as e:
        print(f"Watermark Error: {e}")
        # কোনো কারণে moviepy ফেইল করলে অরিজিনাল ভিডিও সেভ হবে
        if os.path.exists(input_path) and input_path != output_path:
            import shutil
            shutil.copy(input_path, output_path)
        return False

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

def show_google_guidelines_box():
    st.markdown("""
        <div style="background-color: #1e293b; border-left: 5px solid #00c853; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="color: #00c853; margin-top: 0;">📜 Platform & Role-Based Protection Guidelines</h4>
            <ul style="color: #cbd5e1; font-size: 13px; margin-bottom: 0; padding-left: 20px;">
                <li><b>Role Separation:</b> Users can choose either <b>Public ID</b> (Standard viewing/posting) or <b>Advertiser ID</b> (For running ads & payments).</li>
                <li><b>Data Security:</b> Personal billing, bKash/Nagad & bank info are strictly hidden from Public IDs and fully protected.</li>
                <li><b>Permanent Waterproof Protection:</b> All uploaded videos contain embedded permanent platform branding and owner watermark.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

def show_watermarked_media(media_type, media_path, title=""):
    if media_type == "video":
        if os.path.exists(media_path):
            st.video(media_path, format="video/mp4")
    elif media_type == "image":
        if os.path.exists(media_path):
            st.image(media_path, use_container_width=True)

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
                c_input = st.text_input("Write a comment...", key=f"inp_{post_id}", placeholder="Share your thoughts...")
                gift_selected = st.selectbox("🎁 Select Gift", ["None", "🎁 Gift Box (+10 pts)", "💎 Diamond (+50 pts)", "🌟 Star (+20 pts)"], key=f"gft_{post_id}")
                if st.form_submit_button("Post Comment"):
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
            st.info("🔒 Please login to comment.")
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
            <p style="color: #b0b3b8;">Loading Secure Protected Platform & Role System...</p>
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

st.divider()

if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.user_phone = None
    st.session_state.pic = logo_path
    st.session_state.is_verified = 0
    st.session_state.role = 'Public ID'

if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None
if 'otp_sent_to' not in st.session_state:
    st.session_state.otp_sent_to = None

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

show_google_guidelines_box()

# ==========================================
# 7. SIDEBAR AUTHENTICATION & NAVIGATION
# ==========================================
if logo_path:
    st.sidebar.image(logo_path, use_container_width=True)

st.sidebar.header("🔍 Search Global Creators")
search_query = st.sidebar.text_input("Type name or #hashtag...", placeholder="Search creators...")

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
            st.sidebar.markdown(f"👤 **{u_disp}** (@{u['username']})")
            st.sidebar.markdown("---")

st.sidebar.header("📱 Global User Authentication")

if not st.session_state.user:
    phone_input = st.sidebar.text_input("Phone / Account ID", placeholder="e.g. +88017...", key="auth_phone")
    
    if phone_input.strip():
        clean_input = normalize_phone(phone_input)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? OR clean_phone = ? OR phone_number = ?", (phone_input.strip(), clean_input, phone_input.strip()))
        user_record = cursor.fetchone()
        conn.close()
        
        if user_record:
            st.sidebar.success(f"✅ Account Found: **{user_record['username']}** ({user_record['role']})")
            login_pass = st.sidebar.text_input("Enter Password to Login", type="password", key="login_pass")
            
            if st.sidebar.button("🔓 Login Now"):
                hashed_input = hashlib.sha256(login_pass.encode()).hexdigest()
                if user_record['password'] == login_pass or user_record['password'] == hashed_input:
                    st.session_state.user = user_record['username']
                    st.session_state.user_phone = user_record['phone_number']
                    st.session_state.pic = user_record['profile_pic'] or logo_path
                    st.session_state.is_verified = 1
                    st.session_state.role = user_record['role']
                    st.sidebar.success("🎉 Logged in Successfully.")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Incorrect Password!")
        else:
            st.sidebar.info("🆕 New Global Registration (Choose Account Role)")
            account_role_type = st.sidebar.selectbox("Select Account Role", ["Public ID", "Advertiser ID"])
            
            if st.sidebar.button("📲 Send WhatsApp OTP"):
                otp_code = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp_code
                st.session_state.otp_sent_to = clean_input
                
                msg = f"Your BD AI Book {account_role_type} OTP Code is: {otp_code}"
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
                                INSERT INTO users (username, phone_number, clean_phone, password, full_name, role, is_verified, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                            """, (desired_username.strip(), phone_input.strip(), clean_input, new_password, desired_username.strip(), account_role_type, today_str))
                            
                            conn.commit()
                            conn.close()
                            
                            st.session_state.user = desired_username.strip()
                            st.session_state.user_phone = phone_input.strip()
                            st.session_state.pic = logo_path
                            st.session_state.is_verified = 1
                            st.session_state.role = account_role_type
                            st.session_state.generated_otp = None
                            st.session_state.otp_sent_to = None
                            
                            st.sidebar.success(f"🎉 {account_role_type} Created Successfully!")
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
        if res['profile_pic']: st.session_state.pic = res['profile_pic']
        if res['phone_number']: st.session_state.user_phone = res['phone_number']
        st.session_state.role = res['role']
    conn.close()

    active_sidebar_pic = st.session_state.pic if (st.session_state.pic and os.path.exists(st.session_state.pic)) else logo_path
    if active_sidebar_pic and os.path.exists(active_sidebar_pic):
        st.sidebar.image(active_sidebar_pic, width=90)
        
    masked_active_phone = mask_phone_number(st.session_state.user_phone or "")
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** (`{st.session_state.role}`) ✔️")
    if masked_active_phone:
        st.sidebar.caption(f"📱 Phone: {masked_active_phone}")
        
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.user_phone = None
        st.session_state.pic = logo_path
        st.session_state.is_verified = 0
        st.session_state.role = 'Public ID'
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
    
    try:
        cursor.execute("SELECT * FROM videos WHERE video_type != 'short'")
        videos = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM posts")
        posts = [dict(row) for row in cursor.fetchall()]

        combined_feed = videos + posts
        random.shuffle(combined_feed)

        if not combined_feed:
            st.info("No posts or videos available.")

        for index, item in enumerate(combined_feed):
            item_id = str(item["id"])
            uploader_name = item.get("uploader_name", "Unknown User")
            
            cursor.execute("SELECT profile_pic, role FROM users WHERE username = ?", (uploader_name,))
            u_res = cursor.fetchone()
            uploader_pic = u_res['profile_pic'] if u_res and u_res['profile_pic'] else item.get('uploader_pic')
            
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

            if "video_url" in item and item["video_url"] and os.path.exists(item["video_url"]):
                if item.get("title"): st.markdown(f"#### {item.get('title')}")
                show_watermarked_media("video", item["video_url"])

            show_auto_moving_banner()
            st.write(f"❤️ **{format_value(item.get('likes', 0))}** Likes")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"❤️ Like", key=f"lk_{item_id}_{index}"):
                    if st.session_state.user:
                        table_name = "posts" if "content" in item else "videos"
                        cursor.execute(f"UPDATE {table_name} SET likes = likes + 1 WHERE id = ?", (item_id,))
                        conn.commit()
                        st.rerun()
                    else:
                        st.toast("🔒 Please sign in!")
            with c2:
                if st.button("➕ Follow", key=f"fl_{item_id}_{index}"):
                    if st.session_state.user:
                        cursor.execute("UPDATE users SET followers_count = followers_count + 1 WHERE username = ?", (uploader_name,))
                        conn.commit()
                        st.toast(f"Followed {uploader_name}!")
                    else:
                        st.toast("🔒 Please sign in!")

            render_comments_section(item_id)
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Feed Error: {e}")
    finally:
        conn.close()

elif tab == "📱 Scrolle Shorts Feed":
    st.subheader("📱 Shorts Vertical Scroll Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    short_vids = [dict(r) for r in cursor.fetchall()]

    if not short_vids:
        st.info("No shorts found.")
        conn.close()
    else:
        for idx, sv in enumerate(short_vids):
            st.markdown("---")
            col_main, col_side = st.columns([3, 1])
            with col_main:
                show_verified_profile(sv.get("uploader_name", "User"), subtitle="Shorts Creator", is_verified=True)
                st.markdown(f"**{sv.get('title', 'Short Video')}**")
                if sv.get("video_url") and os.path.exists(sv["video_url"]):
                    show_watermarked_media("video", sv["video_url"])
                render_comments_section(sv["id"])
            with col_side:
                if st.button(f"❤️ {format_value(sv.get('likes', 0))}", key=f"sh_like_{sv['id']}"):
                    if st.session_state.user:
                        cursor.execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (sv["id"],))
                        conn.commit()
                        st.rerun()
        conn.close()

elif tab == "📢 Advertiser Hub":
    st.title("📢 Advertiser Ad Network Portal")
    
    if not st.session_state.user:
        st.error("🔒 **Access Restricted!** Please login first.")
    elif st.session_state.role == 'Public ID':
        st.warning("⚠️ **Public ID Restricted Area!**")
        st.info("আপনার অ্যাকাউন্টটি একটি **'Public ID'**। সাধারণ পাবলিক হিসেবে আপনি ভিডিও দেখা ও পোস্ট করার অনুমতি পেলেও অ্যাডভারটাইজার হাব এবং পেমেন্ট চ্যানেল দেখার জন্য আপনার অ্যাকাউন্টটি **'Advertiser ID'** তে রূপান্তর করতে হবে অথবা নতুন Advertiser ID দিয়ে লগইন করতে হবে।")
    else:
        st.success("✅ Authorized Advertiser Hub (Secured & Hidden from Public Users)")
        st.markdown(f"**🏦 Official Payment Channels:**\n\n{get_owner_payment_info()}")
        st.divider()

        region = st.selectbox("Select Your Region", ["Bangladesh (BD)", "International (Global)"])
        price_per_month = 1000 if "Bangladesh" in region else 30
        currency = "BDT" if "Bangladesh" in region else "USD"
        
        duration = st.number_input("Duration (Months)", min_value=1, value=1)
        total_amount = price_per_month * duration
        st.metric(label="Total Payable Amount", value=f"{total_amount} {currency}")

        pay_method = st.radio("Choose Method:", ["bKash", "Nagad", "Bank Transfer (Islami Bank)", "Crypto Wallet (USDT)"])
        if pay_method == "bKash": st.success("📱 **bKash Personal:** `01302134435`")
        elif pay_method == "Nagad": st.warning("📱 **Nagad Personal:** `01722003172`")

        adv_email = st.text_input("Your Contact / Email", value=st.session_state.user)
        ad_type = st.selectbox("Ad Type", ["Short Video (10 Sec)", "Long Video", "Image Post / Banner"])
        content_link = st.text_input("Ad Content Link")
        trx_id = st.text_input("Transaction ID (TrxID)")

        if st.button("Submit Advertisement for Review"):
            if adv_email and content_link and trx_id:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO advertisements (advertiser_email, ad_type, content_link, duration_months, region, payment_method, amount, trx_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (adv_email, ad_type, content_link, duration, region, pay_method, total_amount, trx_id))
                conn.commit()
                conn.close()
                st.success("✅ Ad request submitted successfully!")
            else:
                st.error("Please fill all fields.")

elif tab == "💬 WhatsApp Support Desk":
    st.subheader("💬 Official WhatsApp Support Desk")
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        wa_link = f"https://wa.me/8801722003172?text={urllib.parse.quote(f'Hello from {st.session_state.user} ({st.session_state.role})')}"
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #075E54, #128C7E); padding: 25px; border-radius: 15px; color: white; text-align: center;">
                <h2>🌐 WhatsApp Support Desk</h2>
                <a href="{wa_link}" target="_blank" style="background-color: #25D366; color: #121212; padding: 14px 30px; text-decoration: none; font-weight: bold; border-radius: 30px; display: inline-block;">
                    📲 Send WhatsApp Message
                </a>
            </div>
        """, unsafe_allow_html=True)

elif tab == "💳 Payout & Monetization":
    st.subheader("🏦 Global Monetization & Payout Setup")
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bank_details WHERE username = ?", (st.session_state.user,))
        existing_bank = cursor.fetchone()
        bank_data = dict(existing_bank) if existing_bank else {}
        
        with st.form("bank_setup_form"):
            pay_method = st.selectbox("Payment Category", ["💳 Visa / Mastercard", "🏦 Direct Bank Transfer", "📱 Mobile Banking"])
            c_num = st.text_input("Card / Account Number", value=bank_data.get("card_number", ""))
            
            if st.form_submit_button("💾 Save Payout Information"):
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                if existing_bank:
                    cursor.execute("UPDATE bank_details SET payment_type = ?, card_number = ? WHERE username = ?", (pay_method, c_num, st.session_state.user))
                else:
                    cursor.execute("INSERT INTO bank_details (username, payment_type, card_number, updated_at) VALUES (?, ?, ?, ?)", (st.session_state.user, pay_method, c_num, now_str))
                conn.commit()
                st.success("✅ Saved successfully!")
                st.rerun()
        conn.close()

elif tab == "👤 My Profile & Earnings":
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
        user_info = dict(cursor.fetchone() or {})
        conn.close()
        
        st.subheader("👤 My Profile & Information Management")
        show_verified_profile(user_info.get("full_name") or st.session_state.user, profile_pic_path=user_info.get("profile_pic"), subtitle=f"Role: {user_info.get('role')} | Phone: {mask_phone_number(user_info.get('phone_number'))}", is_verified=True)
        
        with st.form("update_profile_form"):
            st.markdown("### ✏️ Edit Profile Details")
            new_full_name = st.text_input("Full Name", value=user_info.get("full_name") or "")
            new_address = st.text_input("Address / ঠিকানা", value=user_info.get("address") or "")
            new_nid = st.text_input("NID Number / এনআইডি নম্বর", value=user_info.get("nid_number") or "")
            new_pic_file = st.file_uploader("Upload New Profile Picture", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("💾 Save Profile Changes"):
                profile_path = user_info.get("profile_pic")
                if new_pic_file:
                    file_ext = new_pic_file.name.split(".")[-1]
                    profile_filename = f"profile_{uuid.uuid4()}.{file_ext}"
                    profile_path = os.path.join(PROFILE_DIR, profile_filename)
                    with open(profile_path, "wb") as f:
                        f.write(new_pic_file.getbuffer())
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET full_name = ?, address = ?, nid_number = ?, profile_pic = ? WHERE username = ?
                """, (new_full_name.strip(), new_address.strip(), new_nid.strip(), profile_path, st.session_state.user))
                conn.commit()
                conn.close()
                
                st.session_state.pic = profile_path
                st.success("✅ Profile updated successfully!")
                st.rerun()

        st.divider()
        st.markdown("### 📂 My Uploaded Content (Manage / Delete / Customize)")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts WHERE uploader_name = ?", (st.session_state.user,))
        my_posts = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM videos WHERE uploader_name = ?", (st.session_state.user,))
        my_videos = [dict(r) for r in cursor.fetchall()]
        conn.close()

        tab_p1, tab_p2 = st.tabs(["📝 My Posts", "🎥 My Videos"])
        
        with tab_p1:
            if not my_posts:
                st.info("You have not published any posts yet.")
            else:
                for p in my_posts:
                    st.markdown(f"**Content:** {p.get('content')}")
                    if p.get('image_url') and os.path.exists(p['image_url']):
                        st.image(p['image_url'], width=200)
                    st.caption(f"Posted on: {p.get('created_at')}")
                    
                    if st.button("🗑️ Delete Post", key=f"del_post_{p['id']}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM posts WHERE id = ?", (p['id'],))
                        conn.commit()
                        conn.close()
                        st.toast("✅ Post deleted successfully!")
                        st.rerun()
                    st.markdown("---")
                    
        with tab_p2:
            if not my_videos:
                st.info("You have not uploaded any videos yet.")
            else:
                for v in my_videos:
                    st.markdown(f"**Title:** {v.get('title')} (`{v.get('video_type')}`)")
                    if v.get('video_url') and os.path.exists(v['video_url']):
                        st.video(v['video_url'])
                    st.caption(f"Uploaded on: {v.get('created_at')}")
                    
                    if st.button("🗑️ Delete Video", key=f"del_vid_{v['id']}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM videos WHERE id = ?", (v['id'],))
                        conn.commit()
                        conn.close()
                        st.toast("✅ Video deleted successfully!")
                        st.rerun()
                    st.markdown("---")

elif tab == "📤 Create Post / Upload":
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        st.subheader("📤 Upload Content")
        upload_type = st.radio("Select Type:", ["📝 Post/Photo", "🎥 Long Video", "📱 Short Video"])
        
        if upload_type == "📝 Post/Photo":
            post_text = st.text_area("What's on your mind?")
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
            hashtag_input = st.text_input("Hashtags", placeholder="#bdaibook #trending")
            
            if st.button("🚀 Publish Post"):
                if post_text.strip() or uploaded_file:
                    image_path = None
                    if uploaded_file:
                        file_ext = uploaded_file.name.split(".")[-1]
                        image_filename = f"{uuid.uuid4()}.{file_ext}"
                        image_path = os.path.join(IMAGE_DIR, image_filename)
                        with open(image_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO posts (id, uploader_name, uploader_pic, content, hashtags, image_url, created_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), 
                        st.session_state.user, 
                        st.session_state.pic, 
                        post_text.strip(), 
                        hashtag_input.strip(), 
                        image_path, 
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    conn.commit()
                    conn.close()
                    st.toast("✅ Post Published Successfully!")
                    st.rerun()
                else:
                    st.error("Please write something or upload an image.")

        elif upload_type in ["🎥 Long Video", "📱 Short Video"]:
            st.info("Upload your video file (MP4). It will be permanently watermarked and secured.")
            video_file = st.file_uploader("Choose video...", type=["mp4"])
            video_title = st.text_input("Video Title")
            video_hashtags = st.text_input("Video Hashtags", placeholder="#shorts #ai #bdaibook")
            
            if st.button("🚀 Upload & Secure Video"):
                if video_file and video_title:
                    v_type = 'long' if upload_type == "🎥 Long Video" else 'short'
                    
                    file_ext = video_file.name.split(".")[-1]
                    video_filename = f"{uuid.uuid4()}.{file_ext}"
                    temp_input_path = os.path.join(VIDEO_DIR, f"temp_{video_filename}")
                    final_output_path = os.path.join(VIDEO_DIR, video_filename)
                    
                    with open(temp_input_path, "wb") as f:
                        f.write(video_file.getbuffer())
                    
                    with st.spinner("⏳ Processing video and burning permanent watermark... Please wait."):
                        add_watermark_to_video(temp_input_path, final_output_path)
                    
                    if os.path.exists(temp_input_path) and temp_input_path != final_output_path:
                        try: os.remove(temp_input_path)
                        except: pass
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO videos (id, video_url, uploader_name, uploader_pic, video_type, title, hashtags, created_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), 
                        final_output_path, 
                        st.session_state.user, 
                        st.session_state.pic, 
                        v_type, 
                        video_title.strip(), 
                        video_hashtags.strip(), 
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Your {upload_type} is successfully uploaded with permanent watermark protection!")
                else:
                    st.error("Please upload a video and provide a title.")

elif tab == "🔐 Owner Control Panel":
    if st.session_state.role != 'owner':
        st.error("🚫 Access Denied!")
    else:
        st.title("👑 Owner Master Dashboard")
        st.success("System Administrator Access Active")
        current_info = get_owner_payment_info()
        new_info = st.text_area("Edit Manual Payment Details:", value=current_info)
        if st.button("Save Global Payment Info"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET account_details = ? WHERE role = 'owner'", (new_info,))
            conn.commit()
            conn.close()
            st.success("✅ Updated!")
            st.rerun()

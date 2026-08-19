import base64
from datetime import datetime
import hashlib
import os
import random
import sqlite3
import urllib.parse
import uuid
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & META
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Enterprise Master Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

components.html("""
    <meta name="msvalidate.01" content="e776b8ce73ea3dcc07551e8a021a0907">
    <meta name="monetag" content="5cc1b7ba5cb29eff802ce49009f87e2b">
""", height=0)

SMART_LINK = "https://omg10.com/4/10954816"
OWNER_GMAIL = "md4695090@gmail.com"
OWNER_PHONE = "01722003172"

# Folders Setup
DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
PROFILE_DIR = "stored_profiles"

for folder in [VIDEO_DIR, IMAGE_DIR, PROFILE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# ==========================================
# 2. FULL DATABASE INITIALIZATION
# ==========================================
def init_all_16_servers_and_vault():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vault & Users
    cursor.execute("CREATE TABLE IF NOT EXISTS global_sovereign_vault (vault_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, phone_number TEXT UNIQUE, gmail_address TEXT UNIQUE, hashed_password TEXT NOT NULL, biometric_face_hash TEXT, security_tier INTEGER DEFAULT 1, created_at TEXT)")
    
    # 16 Base Servers
    tables = [
        "tb_01_users", "tb_02_interactions", "tb_03_image_posts", "tb_04_long_videos", 
        "tb_05_short_videos", "tb_06_islamic_short_videos", "tb_07_islamic_long_videos", 
        "tb_08_news_contents", "tb_09_blog_contents", "tb_10_educational_contents", 
        "tb_11_entertainment_contents", "tb_12_tech_contents", "tb_13_live_streams", 
        "tb_14_advertisements", "tb_15_bank_details"
    ]
    for table in tables:
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, username TEXT NOT NULL, content_title TEXT, media_path TEXT, ai_verified INT DEFAULT 0, created_at TEXT)")
    
    # Central Pipeline
    cursor.execute("CREATE TABLE IF NOT EXISTS tb_16_global_central_pipeline (pipeline_id TEXT PRIMARY KEY, source_table TEXT NOT NULL, record_id TEXT NOT NULL, username TEXT NOT NULL, owner_approval_status TEXT DEFAULT 'Pending Owner Approval', transferred_at TEXT)")
    
    # Messaging & Legacy
    cursor.execute("CREATE TABLE IF NOT EXISTS direct_messages (id TEXT PRIMARY KEY, sender TEXT, receiver TEXT, message TEXT, created_at TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, phone_number TEXT UNIQUE, full_name TEXT, profile_pic TEXT, is_verified INTEGER DEFAULT 1, payment_method TEXT, account_details TEXT, nid_number TEXT, address TEXT, followers_count INTEGER DEFAULT 0, watch_time_mins REAL DEFAULT 0.0, monetization_status TEXT DEFAULT 'none', earnings REAL DEFAULT 0.0, created_at TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS videos (id TEXT PRIMARY KEY, user_id INTEGER, video_url TEXT, uploader_name TEXT, uploader_pic TEXT, video_type TEXT DEFAULT 'long', title TEXT, likes INTEGER DEFAULT 0, views INTEGER DEFAULT 0, views_count INTEGER DEFAULT 0, followers INTEGER DEFAULT 0, created_at TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS posts (id TEXT PRIMARY KEY, uploader_name TEXT, uploader_pic TEXT, content TEXT, image_url TEXT, likes INTEGER DEFAULT 0, created_at TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS comments (id TEXT PRIMARY KEY, post_id TEXT, uploader_name TEXT, comment_text TEXT, gift_type TEXT, created_at TEXT)")

    # Owner Account Setup
    cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner'")
    if not cursor.fetchone():
        owner_pass = hashlib.sha256("OwnerMasterKey2026#".encode()).hexdigest()
        cursor.execute("INSERT INTO global_sovereign_vault (vault_id, username, phone_number, gmail_address, hashed_password, security_tier, created_at) VALUES ('vault_owner_01', 'system_owner', ?, ?, ?, 999, ?)", (OWNER_PHONE, OWNER_GMAIL, owner_pass, datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()

init_all_16_servers_and_vault()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def ai_content_security_guard(file_name):
    banned_keywords = ["tiktok", "instagram_dl", "facebook_video", "adult", "x_rated", "pirated", "hack"]
    for keyword in banned_keywords:
        if keyword in file_name.lower():
            return False, f"🚨 AI Security Block: Copyright/Third-party content ('{keyword}') is strictly prohibited!"
    return True, "✅ AI Verified: Original Content Approved."

def format_value(value):
    if value is None: return "0"
    if value >= 1000000: return f"{value/1000000:.1f}M"
    if value >= 1000: return f"{value/1000:.1f}K"
    return str(value)

def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return None
    return None

def show_verified_profile(display_name, profile_pic_path=None, subtitle="BD AI Book Verified Creator", is_verified=True):
    b64_img = get_image_base64(profile_pic_path)
    img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">' if b64_img else '<div style="width:50px; height:50px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:24px;">👤</div>'
    blue_tick_svg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="margin-left: 6px; vertical-align: middle;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#00c853"/></svg>' if is_verified else ""
    
    st.markdown(f"""<div style="display: flex; align-items: center; gap: 12px; background: #18191a; padding: 12px; border-radius: 12px; border: 1px solid #2d2f31; margin-bottom: 12px;">
        <div>{img_html}</div>
        <div>
            <div style="display: flex; align-items: center; font-weight: 700; font-size: 17px; color: #e4e6eb; font-family: sans-serif;">
                <span>{display_name}</span>{blue_tick_svg}
            </div>
            <div style="color: #b0b3b8; font-size: 12px; margin-top: 1px;">{subtitle}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def show_auto_moving_banner():
    ad_html = f"""
    <div style="text-align:center; margin: 15px 0;">
        <a href="{SMART_LINK}" target="_blank" style="text-decoration:none;">
            <div style="background: linear-gradient(90deg, #00c853, #1e88e5); color: #fff; padding: 14px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 1px solid #3a3b3c; font-family: sans-serif;">
                <span style="font-size: 15px; font-weight: bold;">⚡ BD AI BOOK MONETIZATION ACTIVE ⚡</span><br>
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
                gift_badge = f" <span style='background:#3a3b3c; padding:2px 6px; border-radius:6px;'>{c['gift_type']}</span>" if c.get("gift_type") and c.get("gift_type") != "None" else ""
                st.markdown(f"**{c['uploader_name']}**{gift_badge} <small style=\"color:#888;\">({c['created_at']})</small>:<br>{c['comment_text']}", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.caption("No comments yet.")
            
        if st.session_state.user:
            with st.form(key=f"c_form_{post_id}"):
                c_input = st.text_input("Write a comment...", key=f"inp_{post_id}")
                gift_selected = st.selectbox("🎁 Select Gift", ["None", "🎁 Gift Box (+10 pts)", "💎 Diamond (+50 pts)", "🌟 Star (+20 pts)"], key=f"gft_{post_id}")
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
            st.info("Please log in to leave a comment.")
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
    .btn-direct { display: block; width: 100%; padding: 10px; margin: 6px 0; color: white !important; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 14px; }
    .bg-1 { background: linear-gradient(135deg, #FF416C, #FF4B2B); }
    .bg-2 { background: linear-gradient(135deg, #1DE9B6, #26A69A); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. MAIN HEADER LOGO SECTION
# ==========================================
LOGO_PATH = "logo.jpg"
if os.path.exists(LOGO_PATH):
    b64_logo = get_image_base64(LOGO_PATH)
    st.markdown(f"""
        <div style="text-align: center; padding: 15px 0;">
            <img src="data:image/jpeg;base64,{b64_logo}" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #00c853; box-shadow: 0 0 20px rgba(0,200,83,0.5);">
            <h1 style="color: #00c853; font-weight: 900; margin-top: 10px;">📖 BD AI Book — Enterprise Master Hub 📖</h1>
            <p style="color: #b0b3b8; margin: 0;">Official Gmail: {OWNER_GMAIL} | WhatsApp: {OWNER_PHONE}</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">📖 BD AI Book — Enterprise Master Hub 📖</h1>
            <p style="color: #b0b3b8; margin: 0;">Official Gmail: {OWNER_GMAIL} | WhatsApp: {OWNER_PHONE}</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.pic = None
    st.session_state.is_verified = 1

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

if "otp_code" not in st.session_state:
    st.session_state.otp_code = None

if "pending_reg" not in st.session_state:
    st.session_state.pending_reg = None

# ==========================================
# 6. SIDEBAR NAVIGATION, AUTH & SEARCH
# ==========================================
if os.path.exists(LOGO_PATH):
    b64_sidebar_logo = get_image_base64(LOGO_PATH)
    st.sidebar.markdown(f"""
        <div style="text-align: center; margin-bottom: 15px;">
            <img src="data:image/jpeg;base64,{b64_sidebar_logo}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #00c853;">
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("### 🔍 BD AI Book Search")
search_query = st.sidebar.text_input("Search posts, videos, creators...", key="search_query")
if search_query and st.sidebar.button("❌ Clear Search"):
    st.session_state.search_query = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🔐 Portal Access & Auth")

mode = st.sidebar.radio("Select Mode", [
    "Login (Phone & Password)", 
    "Register (OTP & Face Verification)", 
    "👑 Owner Exclusive Portal"
])

# Owner Exclusive Portal
if mode == "👑 Owner Exclusive Portal":
    st.sidebar.markdown("### 🔒 Owner Secure Chamber")
    owner_phone_input = st.sidebar.text_input("Owner Phone Number", value=OWNER_PHONE)
    owner_pass_input = st.sidebar.text_input("Owner Master Password", type="password")
    owner_face_capture = st.sidebar.camera_input("Owner Biometric Face Lock Verification")
    
    if st.sidebar.button("Enter Owner Chamber"):
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_owner_pass = hashlib.sha256(owner_pass_input.encode()).hexdigest()
        cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner' AND phone_number = ? AND hashed_password = ?", (owner_phone_input, hashed_owner_pass))
        owner_vault_match = cursor.fetchone()
        conn.close()
        
        if owner_vault_match and owner_face_capture:
            st.session_state.user = "system_owner"
            st.session_state.is_verified = 1
            st.sidebar.success("👑 BD AI Book Owner Verified Successfully!")
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Owner Credentials or Face Lock!")

elif mode == "Login (Phone & Password)":
    login_phone = st.sidebar.text_input("Mobile Number")
    login_pass = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        if login_phone and login_pass:
            conn = get_db_connection()
            cursor = conn.cursor()
            hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
            cursor.execute("SELECT * FROM global_sovereign_vault WHERE phone_number = ? AND hashed_password = ?", (login_phone, hashed_pass))
            vault_user = cursor.fetchone()
            conn.close()
            
            if vault_user:
                st.session_state.user = vault_user["username"]
                st.session_state.pic = None
                st.session_state.is_verified = 1
                st.sidebar.success(f"✅ Welcome back to BD AI Book, {vault_user['username']}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid Mobile Number or Password!")
        else:
            st.sidebar.warning("Please enter phone number and password.")

elif mode == "Register (OTP & Face Verification)":
    st.sidebar.markdown("#### 📧 6-Digit OTP Registration")
    reg_user = st.sidebar.text_input("Full Name / Username")
    reg_phone = st.sidebar.text_input("Mobile Number")
    reg_gmail = st.sidebar.text_input("Gmail Address (For OTP)")
    reg_pass = st.sidebar.text_input("Password", type="password")
    face_capture = st.sidebar.camera_input("Capture Face Lock")
    
    if st.session_state.otp_code is None:
        if st.sidebar.button("Send 6-Digit OTP"):
            if reg_user and reg_phone and reg_gmail and reg_pass and face_capture:
                generated_otp = str(random.randint(100000, 999999))
                st.session_state.otp_code = generated_otp
                
                face_fname = os.path.join(PROFILE_DIR, f"p_{uuid.uuid4()}.jpg")
                with open(face_fname, "wb") as f:
                    f.write(face_capture.getvalue())
                    
                st.session_state.pending_reg = {
                    "username": reg_user, "phone": reg_phone, "gmail": reg_gmail, 
                    "pass": reg_pass, "pic": face_fname
                }
                
                st.sidebar.success(f"✅ OTP Generated for BD AI Book Registration! (Demo Code: {generated_otp})")
            else:
                st.sidebar.error("Please fill all details & capture face.")
    else:
        user_otp_input = st.sidebar.text_input("Enter 6-Digit OTP Code received on Gmail", max_chars=6)
        if st.sidebar.button("Verify OTP & Complete Registration"):
            if user_otp_input == st.session_state.otp_code:
                p_data = st.session_state.pending_reg
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    hashed_pass = hashlib.sha256(p_data["pass"].encode()).hexdigest()
                    vault_id = f"vault_{uuid.uuid4().hex[:8]}"
                    
                    cursor.execute("""
                        INSERT INTO global_sovereign_vault 
                        (vault_id, username, phone_number, gmail_address, hashed_password, security_tier, created_at)
                        VALUES (?, ?, ?, ?, ?, 1, ?)
                    """, (vault_id, p_data["username"], p_data["phone"], p_data["gmail"], hashed_pass, datetime.now().strftime("%Y-%m-%d")))
                    
                    cursor.execute("""
                        INSERT INTO users (username, phone_number, full_name, profile_pic, is_verified, created_at)
                        VALUES (?, ?, ?, ?, 1, ?)
                    """, (p_data["username"], p_data["phone"], p_data["username"], p_data["pic"], datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    conn.close()
                    
                    st.session_state.otp_code = None
                    st.session_state.pending_reg = None
                    st.sidebar.success("🎉 Registered on BD AI Book Successfully! Please Login.")
                except Exception as e:
                    st.sidebar.error("Error: Username or Phone already registered!")
                    conn.close()
            else:
                st.sidebar.error("❌ Invalid OTP Code! Please try again.")

if st.session_state.user and st.session_state.user != "system_owner":
    if st.session_state.pic and os.path.exists(st.session_state.pic):
        st.sidebar.image(st.session_state.pic, width=90)
    st.sidebar.markdown(f"Welcome to BD AI Book, **{st.session_state.user}** ✔️")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.pic = None
        st.session_state.is_verified = 1
        st.rerun()
elif st.session_state.user == "system_owner":
    st.sidebar.markdown("👑 **BD AI Book Owner Active**")
    if st.sidebar.button("Owner Logout"):
        st.session_state.user = None
        st.rerun()

nav_tabs = [
    "🌍 World Feed", 
    "📱 Scrolle Shorts Feed", 
    "💬 WhatsApp Support Desk", 
    "💳 Payout & Monetization", 
    "👤 My Profile & Earnings", 
    "📤 Create Post / Upload"
]
tab = st.sidebar.radio("Navigation", nav_tabs, index=nav_tabs.index(st.session_state.active_tab) if st.session_state.active_tab in nav_tabs else 0)
st.session_state.active_tab = tab

# ==========================================
# 7. TAB IMPLEMENTATIONS
# ==========================================

# --- World Feed ---
if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search_query:
        st.info(f"🔍 BD AI Book Search: **{search_query}**")
        
    try:
        if search_query:
            cursor.execute("SELECT * FROM videos WHERE video_type = 'short' AND (title LIKE ? OR uploader_name LIKE ?) ORDER BY created_at DESC", (f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
        short_videos = [dict(r) for r in cursor.fetchall()]
        
        if short_videos:
            st.markdown('<h3 style="color: #00c853;">▶️ BD AI Book Shorts Feed</h3>', unsafe_allow_html=True)
            cols = st.columns(min(len(short_videos), 3))
            for i, sv in enumerate(short_videos[:3]):
                with cols[i]:
                    st.markdown(f"**{sv.get('uploader_name', 'User')}** ✔️")
                    if os.path.exists(sv["video_url"]):
                        st.video(sv["video_url"], format="video/mp4")
                    if st.button("▶️ Watch in Shorts Feed", key=f"open_short_{sv['id']}"):
                        st.session_state.active_tab = "📱 Scrolle Shorts Feed"
                        st.rerun()
                    st.caption(f"👁️ {format_value(sv.get('views', 0))} views")
            st.divider()
    except Exception:
        pass

    try:
        if search_query:
            cursor.execute("SELECT * FROM videos WHERE video_type != 'short' AND (title LIKE ? OR uploader_name LIKE ?)", (f"%{search_query}%", f"%{search_query}%"))
            videos = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM posts WHERE (content LIKE ? OR uploader_name LIKE ?)", (f"%{search_query}%", f"%{search_query}%"))
            posts = [dict(row) for row in cursor.fetchall()]
        else:
            cursor.execute("SELECT * FROM videos WHERE video_type != 'short'")
            videos = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM posts")
            posts = [dict(row) for row in cursor.fetchall()]
            
        combined_feed = videos + posts
        if not search_query:
            random.shuffle(combined_feed)
            
        if not combined_feed:
            st.info("No BD AI Book posts or videos available. Create content from the Upload section.")
            
        for index, item in enumerate(combined_feed):
            item_id = str(item["id"])
            uploader_name = item.get("uploader_name", "Unknown User")
            uploader_pic = item.get("uploader_pic", None)
            created_at = item.get("created_at", "Recently")
            
            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(uploader_name, profile_pic_path=uploader_pic, subtitle=f"BD AI Book Post • {created_at}", is_verified=True)
            
            if "content" in item and item["content"]:
                st.markdown(f"### {item['content']}")
                
            if "image_url" in item and item["image_url"] and os.path.exists(item["image_url"]):
                st.image(item["image_url"], use_container_width=True)
                
            if "video_url" in item and os.path.exists(item["video_url"]):
                if item.get("title"):
                    st.markdown(f"#### {item.get('title')}")
                st.video(item["video_url"], format="video/mp4")
                
                new_views = item.get("views", 0) + 1
                cursor.execute("UPDATE videos SET views = ?, views_count = ? WHERE id = ?", (new_views, new_views, item_id))
                conn.commit()
                
            show_auto_moving_banner()
            
            st.write(f"❤️ **{format_value(item.get('likes', 0))}** Likes")
            st.markdown(f"""
                <a href="{SMART_LINK}" target="_blank" class="btn-direct bg-1">💰 Claim BD AI Book Reward</a>
                <a href="{SMART_LINK}" target="_blank" class="btn-direct bg-2">💎 Premium Bonus Link</a>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"❤️ Like ({format_value(item.get('likes', 0))})", key=f"lk_{item_id}_{index}"):
                    table_name = "posts" if "content" in item else "videos"
                    cursor.execute(f"UPDATE {table_name} SET likes = likes + 1 WHERE id = ?", (item_id,))
                    conn.commit()
                    st.rerun()
            with c2:
                if st.button("➕ Follow", key=f"fl_{item_id}_{index}"):
                    cursor.execute("UPDATE users SET followers_count = followers_count + 1 WHERE username = ?", (uploader_name,))
                    conn.commit()
                    st.toast(f"Followed {uploader_name} on BD AI Book!")
                    
            render_comments_section(item_id)
            st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"BD AI Book Feed Error: {e}")
    finally:
        conn.close()

# --- Shorts Feed ---
elif tab == "📱 Scrolle Shorts Feed":
    st.subheader("📱 BD AI Book Vertical Shorts Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if search_query:
        cursor.execute("SELECT * FROM videos WHERE video_type = 'short' AND (title LIKE ? OR uploader_name LIKE ?) ORDER BY created_at DESC", (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    short_vids = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if not short_vids:
        st.info("No shorts videos found on BD AI Book.")
    else:
        for idx, sv in enumerate(short_vids):
            st.markdown("---")
            col_main, col_side = st.columns([3, 1])
            with col_main:
                show_verified_profile(sv.get("uploader_name", "User"), profile_pic_path=sv.get("uploader_pic"), subtitle="BD AI Book Shorts Creator", is_verified=True)
                st.markdown(f"**{sv.get('title', 'Short Video')}**")
                if os.path.exists(sv["video_url"]):
                    st.video(sv["video_url"], format="video/mp4")
                    
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE videos SET views = views + 1, views_count = views_count + 1 WHERE id = ?", (sv["id"],))
                conn.commit()
                conn.close()
                
                render_comments_section(sv["id"])
                
            with col_side:
                st.write(" ")
                if st.button(f"❤️ {format_value(sv.get('likes', 0))}", key=f"sh_like_{sv['id']}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (sv["id"],))
                    conn.commit()
                    conn.close()
                    st.toast("Liked!")
                    st.rerun()
                    
                st.caption(f"👁️ {format_value(sv.get('views', 0))}")
                
                if st.button("➕ Follow", key=f"sh_fol_{sv['id']}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET followers_count = followers_count + 1 WHERE username = ?", (sv.get("uploader_name"),))
                    conn.commit()
                    conn.close()
                    st.toast("Followed Creator!")

# --- WhatsApp Support Desk ---
elif tab == "💬 WhatsApp Support Desk":
    st.subheader("💬 BD AI Book WhatsApp Support Desk")
    st.caption(f"Contact us directly via WhatsApp ({OWNER_PHONE}) for help.")
    
    HIDDEN_WA_NUMBER = "8801722003172"
    default_msg = "Hello! I am contacting you from BD AI Book App."
    encoded_msg = urllib.parse.quote(default_msg)
    wa_link = f"https://wa.me/{HIDDEN_WA_NUMBER}?text={encoded_msg}"
    
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #075E54, #128C7E); padding: 25px; border-radius: 15px; color: white; text-align: center; border: 1px solid #25D366; margin: 20px 0;">
            <h2 style="margin-top:0; color: #ffffff;">📖 BD AI Book WhatsApp Helpdesk</h2>
            <p style="font-size: 15px; color: #e0e0e0; margin-bottom: 20px;">
                Click below to send messages, feedback, or screenshots directly to our team.
            </p>
            <a href="{wa_link}" target="_blank" style="
                background-color: #25D366; color: #121212; padding: 14px 30px; text-decoration: none; 
                font-weight: bold; font-size: 17px; border-radius: 30px; display: inline-block;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
                📲 Send WhatsApp Message
            </a>
            <p style="font-size: 12px; color: #ffeb3b; margin-top: 20px; margin-bottom: 0;">
                ⚠️ <b>WhatsApp Helpline:</b> +{OWNER_PHONE} | Gmail: {OWNER_GMAIL}
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- Payout & Monetization ---
elif tab == "💳 Payout & Monetization":
    st.subheader("🏦 BD AI Book Payout & Bank Setup")
    pay_method = st.selectbox("Select Payment Method:", ["📱 bKash", "📱 Nagad", "📱 Rocket", "🌐 PayPal", "💳 Mastercard / Visa Card", "🏦 Bank Transfer"])
    acc_num = st.text_input("Account Number / Email / Card Number")
    holder_name = st.text_input("Account Holder Name")
    
    if st.button("💾 Save Payment Details"):
        if acc_num and holder_name and st.session_state.user:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET payment_method = ?, account_details = ? WHERE username = ?", (pay_method, f"{holder_name} - {acc_num}", st.session_state.user))
            conn.commit()
            conn.close()
            st.success("✅ BD AI Book Payment account details saved!")
        else:
            st.warning("Please log in and fill in all details.")

# --- My Profile & Earnings ---
elif tab == "👤 My Profile & Earnings":
    st.subheader("👤 BD AI Book Creator Profile")
    if not st.session_state.user:
        st.info("Please log in to view your profile & earnings.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
        usr = cursor.fetchone()
        conn.close()
        
        if usr:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Username:** {usr['username']}")
                st.write(f"**Phone:** {usr['phone_number']}")
                st.write(f"**Followers:** {format_value(usr['followers_count'])}")
            with col2:
                st.write(f"**Monetization:** {usr['monetization_status'].upper()}")
                st.write(f"**Total Earnings:** ${usr['earnings']:.2f}")
                st.write(f"**Payment Details:** {usr['account_details'] or 'Not Set'}")

# --- Create Post / Upload ---
elif tab == "📤 Create Post / Upload":
    st.subheader("📤 BD AI Book — Upload Content")
    if not st.session_state.user:
        st.warning("Please log in to upload content.")
    else:
        u_type = st.selectbox("Select Upload Type", ["📝 Text / Image Post", "🎥 Long Video", "📱 Short Video"])
        
        if u_type == "📝 Text / Image Post":
            with st.form("post_form"):
                post_text = st.text_area("What's on your mind?")
                post_img = st.file_uploader("Upload Image (Optional)", type=["jpg", "png", "jpeg"])
                submit_post = st.form_submit_button("Publish Post")
                
                if submit_post:
                    img_path = None
                    if post_img:
                        is_safe, msg = ai_content_security_guard(post_img.name)
                        if not is_safe:
                            st.error(msg)
                            st.stop()
                        img_path = os.path.join(IMAGE_DIR, f"{uuid.uuid4().hex[:8]}_{post_img.name}")
                        with open(img_path, "wb") as f:
                            f.write(post_img.getbuffer())
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO posts (id, uploader_name, uploader_pic, content, image_url, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), st.session_state.user, st.session_state.pic, post_text, img_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    st.success("🎉 Published on BD AI Book successfully!")

        elif u_type in ["🎥 Long Video", "📱 Short Video"]:
            with st.form("video_form"):
                v_title = st.text_input("Video Title")
                v_file = st.file_uploader("Upload Video File (MP4)", type=["mp4", "mov"])
                submit_v = st.form_submit_button("Upload Video")
                
                if submit_v:
                    if v_file and v_title:
                        is_safe, msg = ai_content_security_guard(v_file.name)
                        if not is_safe:
                            st.error(msg)
                            st.stop()
                            
                        v_path = os.path.join(VIDEO_DIR, f"{uuid.uuid4().hex[:8]}_{v_file.name}")
                        with open(v_path, "wb") as f:
                            f.write(v_file.getbuffer())
                            
                        video_type_str = "short" if u_type == "📱 Short Video" else "long"
                        
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO videos (id, uploader_name, uploader_pic, title, video_type, video_url, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (str(uuid.uuid4()), st.session_state.user, st.session_state.pic, v_title, video_type_str, v_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        conn.close()
                        st.success("🎉 Video uploaded to BD AI Book successfully!")
                    else:
                        st.warning("Please provide both a title and a video file.")

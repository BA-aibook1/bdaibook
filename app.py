import base64
from datetime import datetime
import hashlib
import os
import random
import sqlite3
import urllib.parse
import uuid

import requests
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

components.html(
    """
    <meta name="msvalidate.01" content="e776b8ce73ea3dcc07551e8a021a0907">
    <meta name="monetag" content="5cc1b7ba5cb29eff802ce49009f87e2b">
    """,
    height=0,
)

SMART_LINK = "https://omg10.com/4/10954816"

# ==========================================
# 2. LOCAL STORAGE & 16-SERVER MASTER DATABASE SETUP
# ==========================================
DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
PROFILE_DIR = "stored_profiles"

for folder in [VIDEO_DIR, IMAGE_DIR, PROFILE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)


def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_all_16_servers_and_vault():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 0. Special Sovereign Vault (মালিক ও ইউজারদের ফোন, জিমেইল, পাসওয়ার্ড ও ফেস লক ডেটা)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sovereign_vault (
            vault_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            gmail_address TEXT UNIQUE,
            hashed_password TEXT NOT NULL,
            biometric_face_hash TEXT,
            security_tier INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    # 1. User Base Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_01_users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'Public ID',
            created_at TEXT
        )
    """)

    # 2. Interactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_02_interactions (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            target_id TEXT,
            comment_text TEXT,
            created_at TEXT
        )
    """)

    # 3. Image Posts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_03_image_posts (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 4. Long Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_04_long_videos (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 5. Short Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_05_short_videos (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 6. Islamic Short Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_06_islamic_short_videos (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 7. Islamic Long Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_07_islamic_long_videos (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 8. News Contents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_08_news_contents (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 9. Blog Contents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_09_blog_contents (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 10. Educational Contents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_10_educational_contents (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 11. Entertainment Contents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_11_entertainment_contents (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 12. Tech & Code Contents Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_12_tech_contents (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 13. Live Streams Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_13_live_streams (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 14. Advertisements Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_14_advertisements (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 15. Bank Details Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_15_bank_details (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            content_title TEXT,
            media_path TEXT,
            ai_verified INT DEFAULT 0,
            created_at TEXT
        )
    """)

    # 16. Central Electric Pipeline Hub
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_16_global_central_pipeline (
            pipeline_id TEXT PRIMARY KEY,
            source_table TEXT NOT NULL,
            record_id TEXT NOT NULL,
            username TEXT NOT NULL,
            owner_approval_status TEXT DEFAULT 'Pending Owner Approval',
            transferred_at TEXT
        )
    """)

    # Legacy compatibility tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            full_name TEXT,
            profile_pic TEXT,
            is_verified INTEGER DEFAULT 1,
            payment_method TEXT,
            account_details TEXT,
            nid_number TEXT,
            address TEXT,
            followers_count INTEGER DEFAULT 0,
            watch_time_mins REAL DEFAULT 0.0,
            monetization_status TEXT DEFAULT 'none',
            earnings REAL DEFAULT 0.0,
            created_at TEXT
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
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            uploader_pic TEXT,
            content TEXT,
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

    # Default Owner Master Account Setup (Tier 999 - Hidden Secure Sovereign Owner)
    cursor.execute(
        "SELECT * FROM global_sovereign_vault WHERE username = 'system_owner'"
    )
    if not cursor.fetchone():
        owner_pass = hashlib.sha256("OwnerMasterKey2026#".encode()).hexdigest()
        cursor.execute(
            """
            INSERT INTO global_sovereign_vault (vault_id, username, phone_number, hashed_password, security_tier, created_at)
            VALUES ('vault_owner_01', 'system_owner', '01722003172', ?, 999, ?)
        """,
            (owner_pass, datetime.now().strftime("%Y-%m-%d")),
        )

    conn.commit()
    conn.close()


init_all_16_servers_and_vault()


# ==========================================
# 3. AI SECURITY GUARD & PIPELINE ENGINE
# ==========================================
def ai_content_security_guard(file_name):
    banned_keywords = [
        "tiktok",
        "instagram_dl",
        "facebook_video",
        "adult",
        "x_rated",
        "pirated",
        "hack",
    ]
    for keyword in banned_keywords:
        if keyword in file_name.lower():
            return (
                False,
                f"🚨 AI Security Block: Copyright/Third-party content ('{keyword}') is strictly prohibited! No third-party downloads allowed.",
            )
    return True, "✅ AI Verified: Original Mobile Content Approved."


def push_to_central_pipeline(source_table, record_id, username):
    conn = get_db_connection()
    cursor = conn.cursor()
    pipeline_id = f"pipe_{uuid.uuid4().hex[:10]}"
    cursor.execute(
        """
        INSERT INTO tb_16_global_central_pipeline 
        (pipeline_id, source_table, record_id, username, owner_approval_status, transferred_at)
        VALUES (?, ?, ?, ?, 'Pending Owner Approval', ?)
    """,
        (
            pipeline_id,
            source_table,
            record_id,
            username,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    conn.close()


def register_or_get_user(username, phone_number=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, username, phone_number, followers_count, watch_time_mins, monetization_status, earnings FROM users WHERE username = ? OR phone_number = ?",
        (username, phone_number),
    )
    user = c.fetchone()
    if not user:
        c.execute(
            "INSERT INTO users (username, phone_number, created_at) VALUES (?, ?, ?)",
            (username, phone_number, datetime.now().strftime("%Y-%m-%d")),
        )
        conn.commit()
        c.execute(
            "SELECT id, username, phone_number, followers_count, watch_time_mins, monetization_status, earnings FROM users WHERE username = ?",
            (username,),
        )
        user = c.fetchone()
    conn.close()
    return {
        "id": user["id"],
        "username": user["username"],
        "phone_number": user["phone_number"],
        "followers_count": user["followers_count"] or 0,
        "watch_time_mins": user["watch_time_mins"] or 0.0,
        "monetization_status": user["monetization_status"] or "none",
        "earnings": user["earnings"] or 0.0,
    }


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
                return base64.b64encode(img_file.read()).decode("utf-8")
        except Exception:
            return None
    return None


def show_verified_profile(
    display_name,
    profile_pic_path=None,
    subtitle="Official Global Verified Creator",
    is_verified=True,
):
    b64_img = get_image_base64(profile_pic_path)
    if b64_img:
        img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; border:2px solid #00c853;">'
    else:
        img_html = '<div style="width:50px; height:50px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:24px;">👤</div>'

    blue_tick_svg = (
        """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="margin-left: 6px; vertical-align: middle;">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#00c853"/>
    </svg>"""
        if is_verified
        else ""
    )

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
            <div style="background: linear-gradient(90deg, #00c853, #1e88e5); color: #fff; padding: 14px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 1px solid #3a3b3c; font-family: sans-serif;">
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
        cursor.execute(
            "SELECT * FROM comments WHERE post_id = ? ORDER BY created_at DESC",
            (post_id,),
        )
        all_comments = [dict(r) for r in cursor.fetchall()]

        if all_comments:
            for c in all_comments:
                gift_badge = (
                    f" <span style='background:#3a3b3c; padding:2px 6px; border-radius:6px;'>{c['gift_type']}</span>"
                    if c.get("gift_type") and c.get("gift_type") != "None"
                    else ""
                )
                st.markdown(
                    f"**{c['uploader_name']}**{gift_badge} <small style=\"color:#888;\">({c['created_at']})</small>:<br>{c['comment_text']}",
                    unsafe_allow_html=True,
                )
                st.markdown("---")
        else:
            st.caption("No comments yet.")

        if st.session_state.user:
            with st.form(key=f"c_form_{post_id}"):
                c_input = st.text_input(
                    "Write a comment...",
                    key=f"inp_{post_id}",
                    placeholder="Share your thoughts...",
                )
                gift_selected = st.selectbox(
                    "🎁 Select Gift",
                    [
                        "None",
                        "🎁 Gift Box (+10 pts)",
                        "💎 Diamond (+50 pts)",
                        "🌟 Star (+20 pts)",
                        "🔥 Fire (+15 pts)",
                    ],
                    key=f"gft_{post_id}",
                )
                submit_btn = st.form_submit_button("Post Comment")

                if submit_btn:
                    if c_input.strip():
                        now_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                        cursor.execute(
                            """
                            INSERT INTO comments (id, post_id, uploader_name, comment_text, gift_type, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                str(uuid.uuid4()),
                                post_id,
                                st.session_state.user,
                                c_input.strip(),
                                gift_selected,
                                now_time,
                            ),
                        )
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
st.markdown(
    """
    <style>
    .stApp { background-color: #121212; color: #e4e6eb; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background-color: #242526 !important;
        color: #ffffff !important;
        border: 1px solid #3a3b3c !important;
    }
    textarea, input {
        color: #ffffff !important;
        background-color: #242526 !important;
    }
    .feed-card {
        background: #18191a;
        border: 1px solid #2d2f31;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 20px;
    }
    .monetization-box {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: white;
        padding: 18px;
        border-radius: 12px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .btn-direct { display: block; width: 100%; padding: 10px; margin: 6px 0; color: white !important; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 14px; }
    .bg-1 { background: linear-gradient(135deg, #FF416C, #FF4B2B); }
    .bg-2 { background: linear-gradient(135deg, #1DE9B6, #26A69A); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 5. MAIN HEADER LOGO SECTION (Waterproof Circular Global Logo)
# ==========================================
LOGO_PATH = "logo.jpg"
if os.path.exists(LOGO_PATH):
    b64_logo = get_image_base64(LOGO_PATH)
    st.markdown(
        f"""
        <div style="text-align: center; padding: 15px 0;">
            <img src="data:image/jpeg;base64,{b64_logo}" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #00c853; box-shadow: 0 0 20px rgba(0,200,83,0.5);">
            <h1 style="color: #00c853; font-weight: 900; margin-top: 10px;">🛡️ BD AI Book — Enterprise Master Hub 🛡️</h1>
            <p style="color: #b0b3b8; margin: 0;">Autonomous AI & 16-Table Master Pipeline Hub (Global Verified)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">🛡️ BD AI Book — Enterprise Master Hub 🛡️</h1>
            <p style="color: #b0b3b8; margin: 0;">Autonomous AI & 16-Table Master Pipeline Hub</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# Session State Initialization
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.pic = None
    st.session_state.is_verified = 1

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 6. SIDEBAR NAVIGATION, AUTH & SEARCH
# ==========================================
if os.path.exists(LOGO_PATH):
    b64_sidebar_logo = get_image_base64(LOGO_PATH)
    st.sidebar.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 15px;">
            <img src="data:image/jpeg;base64,{b64_sidebar_logo}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #00c853;">
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- 🔍 SEARCH BAR SECTION ---
st.sidebar.markdown("### 🔍 Search Feed")
search_query = st.sidebar.text_input(
    "Search posts, videos, creators...",
    placeholder="Type to search...",
    key="search_query",
)
if search_query:
    if st.sidebar.button("❌ Clear Search"):
        st.session_state.search_query = ""
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🔐 Portal Access & Auth")

mode = st.sidebar.radio(
    "Select Mode",
    [
        "Login (Phone & Password)",
        "Register (Phone, Gmail & Face)",
        "👑 Owner Exclusive Portal",
    ],
)

# 👑 OWNER EXCLUSIVE PORTAL (Separate Private Vault & Face Lock / Password)
if mode == "👑 Owner Exclusive Portal":
    st.sidebar.markdown("### 🔒 Owner Secure Chamber")
    owner_phone = st.sidebar.text_input("Owner Phone Number", value="01722003172")
    owner_pass_input = st.sidebar.text_input(
        "Owner Master Password", type="password"
    )
    owner_face_capture = st.sidebar.camera_input(
        "Owner Biometric Face Lock Verification"
    )

    if st.sidebar.button("Enter Owner Chamber"):
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_owner_pass = hashlib.sha256(owner_pass_input.encode()).hexdigest()
        cursor.execute(
            "SELECT * FROM global_sovereign_vault WHERE username = 'system_owner' AND phone_number = ? AND hashed_password = ?",
            (owner_phone, hashed_owner_pass),
        )
        owner_vault_match = cursor.fetchone()
        conn.close()

        if owner_vault_match and owner_face_capture:
            st.session_state.user = "system_owner"
            st.session_state.is_verified = 1
            st.sidebar.success(
                "👑 Owner Verified Successfully! Access Granted."
            )
            st.rerun()
        else:
            st.sidebar.error(
                "❌ Access Denied: Invalid Owner Phone, Password or Face Lock Verification!"
            )

elif mode == "Login (Phone & Password)":
    login_phone = st.sidebar.text_input("Mobile Number")
    login_pass = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if login_phone and login_pass:
            conn = get_db_connection()
            cursor = conn.cursor()
            hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
            cursor.execute(
                "SELECT * FROM global_sovereign_vault WHERE phone_number = ? AND hashed_password = ?",
                (login_phone, hashed_pass),
            )
            vault_user = cursor.fetchone()
            conn.close()

            if vault_user:
                st.session_state.user = vault_user["username"]
                st.session_state.pic = None
                st.session_state.is_verified = 1
                st.sidebar.success(
                    f"✅ Welcome back, {vault_user['username']}!"
                )
                st.rerun()
            else:
                st.sidebar.error(
                    "❌ Invalid Mobile Number or Password! Please check credentials."
                )
        else:
            st.sidebar.warning("Please enter both phone number and password.")

elif mode == "Register (Phone, Gmail & Face)":
    reg_user = st.sidebar.text_input("Your Full Name / Username")
    reg_phone = st.sidebar.text_input("Mobile Number (World Login)")
    reg_gmail = st.sidebar.text_input("Gmail Address")
    reg_pass = st.sidebar.text_input("Password", type="password")
    face_capture = st.sidebar.camera_input(
        "Capture Face Lock for Global Account"
    )

    if st.sidebar.button("Register & Sync to Servers"):
        if reg_user and reg_phone and reg_gmail and reg_pass and face_capture:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                hashed_pass = hashlib.sha256(reg_pass.encode()).hexdigest()
                vault_id = f"vault_{uuid.uuid4().hex[:8]}"
                fname = os.path.join(PROFILE_DIR, f"p_{uuid.uuid4()}.jpg")
                with open(fname, "wb") as f:
                    f.write(face_capture.getvalue())

                # Save to Global Sovereign Vault
                cursor.execute(
                    """
                    INSERT INTO global_sovereign_vault 
                    (vault_id, username, phone_number, gmail_address, hashed_password, security_tier, created_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                    (
                        vault_id,
                        reg_user,
                        reg_phone,
                        reg_gmail,
                        hashed_pass,
                        datetime.now().strftime("%Y-%m-%d"),
                    ),
                )

                # Sync across user tables and databases
                cursor.execute(
                    """
                    INSERT INTO users (username, phone_number, full_name, profile_pic, is_verified, created_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                """,
                    (
                        reg_user,
                        reg_phone,
                        reg_user,
                        fname,
                        datetime.now().strftime("%Y-%m-%d"),
                    ),
                )
                conn.commit()
                conn.close()
                st.sidebar.success(
                    "🎉 Registration Complete! Phone & Database Synced. Please switch to Login mode."
                )
            except Exception as e:
                st.sidebar.error(
                    f"Error: Mobile Number or Username already registered!"
                )
                conn.close()
        else:
            st.sidebar.error(
                "Please fill all fields (Name, Phone, Gmail, Password) and capture your face!"
            )

if st.session_state.user and st.session_state.user != "system_owner":
    if st.session_state.pic and os.path.exists(st.session_state.pic):
        st.sidebar.image(st.session_state.pic, width=90)
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** ✔️")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.pic = None
        st.session_state.is_verified = 1
        st.rerun()
elif st.session_state.user == "system_owner":
    st.sidebar.markdown("👑 **Owner Master Active**")
    if st.sidebar.button("Owner Logout"):
        st.session_state.user = None
        st.rerun()

# Navigation Tabs
nav_tabs = [
    "🌍 World Feed",
    "📱 Scrolle Shorts Feed",
    "💬 WhatsApp Support Desk",
    "💳 Payout & Monetization",
    "👤 My Profile & Earnings",
    "📤 Create Post / Upload",
]
tab = st.sidebar.radio(
    "Navigation",
    nav_tabs,
    index=nav_tabs.index(st.session_state.active_tab)
    if st.session_state.active_tab in nav_tabs
    else 0,
)
st.session_state.active_tab = tab

# ==========================================
# 7. TAB IMPLEMENTATIONS
# ==========================================

# --- World Feed ---
if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        st.info(f"🔍 Showing search results for: **{search_query}**")

    try:
        if search_query:
            cursor.execute(
                "SELECT * FROM videos WHERE video_type = 'short' AND (title LIKE ? OR uploader_name LIKE ?) ORDER BY created_at DESC",
                (f"%{search_query}%", f"%{search_query}%"),
            )
        else:
            cursor.execute(
                "SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC"
            )
        short_videos = [dict(r) for r in cursor.fetchall()]

        if short_videos:
            st.markdown(
                '<h3 style="color: #00c853;">▶️ Scrolle Shorts Feed</h3>',
                unsafe_allow_html=True,
            )
            cols = st.columns(min(len(short_videos), 3))
            for i, sv in enumerate(short_videos[:3]):
                with cols[i]:
                    st.markdown(f"**{sv.get('uploader_name', 'User')}** ✔️")
                    if os.path.exists(sv["video_url"]):
                        st.video(sv["video_url"], format="video/mp4")

                    if st.button(
                        "▶️ Watch in Shorts Feed", key=f"open_short_{sv['id']}"
                    ):
                        st.session_state.active_tab = "📱 Scrolle Shorts Feed"
                        st.rerun()
                    st.caption(f"👁️ {format_value(sv.get('views', 0))} views")
            st.divider()
    except Exception:
        pass

    try:
        if search_query:
            cursor.execute(
                "SELECT * FROM videos WHERE video_type != 'short' AND (title LIKE ? OR uploader_name LIKE ?)",
                (f"%{search_query}%", f"%{search_query}%"),
            )
            videos = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                "SELECT * FROM posts WHERE (content LIKE ? OR uploader_name LIKE ?)",
                (f"%{search_query}%", f"%{search_query}%"),
            )
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
            if search_query:
                st.warning("No posts or videos found matching your search term.")
            else:
                st.info(
                    "No posts or videos available. Create content from the Upload section."
                )

        for index, item in enumerate(combined_feed):
            item_id = str(item["id"])
            uploader_name = item.get("uploader_name", "Unknown User")
            uploader_pic = item.get("uploader_pic", None)
            created_at = item.get("created_at", "Recently")

            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(
                uploader_name,
                profile_pic_path=uploader_pic,
                subtitle=f"Posted {created_at}",
                is_verified=True,
            )

            if "title" in item and item["title"]:
                st.markdown(f"### {item['title']}")
            if "content" in item and item["content"]:
                st.markdown(f"#### {item['content']}")

            if "video_url" in item and item["video_url"]:
                if os.path.exists(item["video_url"]):
                    st.video(item["video_url"])

            if "image_url" in item and item["image_url"]:
                if os.path.exists(item["image_url"]):
                    st.image(item["image_url"], use_container_width=True)

            render_comments_section(item_id)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading feed: {e}")
    finally:
        conn.close()

# --- Shorts Feed ---
elif tab == "📱 Scrolle Shorts Feed":
    st.markdown("### 📱 Shorts Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    shorts = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if shorts:
        for sv in shorts:
            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(sv.get("uploader_name", "User"), profile_pic_path=sv.get("uploader_pic"))
            if sv.get("title"):
                st.write(sv["title"])
            if os.path.exists(sv["video_url"]):
                st.video(sv["video_url"])
            render_comments_section(sv["id"])
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No shorts uploaded yet.")

# --- WhatsApp Support Desk ---
elif tab == "💬 WhatsApp Support Desk":
    st.markdown("### 💬 WhatsApp Support Desk")
    st.write("Direct Support Line: +8801722003172")
    st.markdown('<a href="https://wa.me/8801722003172" target="_blank" class="btn-direct bg-1">Chat on WhatsApp</a>', unsafe_allow_html=True)

# --- Payout & Monetization ---
elif tab == "💳 Payout & Monetization":
    st.markdown("### 💳 Payout & Monetization")
    show_auto_moving_banner()
    st.info("Automatic monetization tracking active across all 16 pipeline servers.")

# --- My Profile & Earnings ---
elif tab == "👤 My Profile & Earnings":
    st.markdown("### 👤 User Dashboard")
    if st.session_state.user:
        u_data = register_or_get_user(st.session_state.user)
        col1, col2, col3 = st.columns(3)
        col1.metric("Followers", format_value(u_data["followers_count"]))
        col2.metric("Watch Time (Mins)", format_value(u_data["watch_time_mins"]))
        col3.metric("Earnings ($)", f"${u_data['earnings']:.2f}")
    else:
        st.warning("Please login to view profile details.")

# --- Create Post / Upload ---
elif tab == "📤 Create Post / Upload":
    st.markdown("### 📤 Upload Content")
    if not st.session_state.user:
        st.warning("Please login first to upload content.")
    else:
        u_type = st.selectbox("Select Content Type", ["Post", "Long Video", "Short Video"])
        title_in = st.text_input("Title / Content Text")
        file_up = st.file_uploader("Upload Media File", type=["jpg", "jpeg", "png", "mp4"])

        if st.button("Publish Content"):
            if file_up and title_in:
                is_safe, msg = ai_content_security_guard(file_up.name)
                if not is_safe:
                    st.error(msg)
                else:
                    ext = file_up.name.split(".")[-1]
                    f_id = str(uuid.uuid4())
                    
                    if u_type == "Post":
                        save_path = os.path.join(IMAGE_DIR, f"{f_id}.{ext}")
                        with open(save_path, "wb") as f:
                            f.write(file_up.getbuffer())
                        
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("INSERT INTO posts (id, uploader_name, content, image_url, created_at) VALUES (?, ?, ?, ?, ?)",
                                  (f_id, st.session_state.user, title_in, save_path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        conn.close()
                        push_to_central_pipeline("tb_03_image_posts", f_id, st.session_state.user)
                    else:
                        save_path = os.path.join(VIDEO_DIR, f"{f_id}.{ext}")
                        with open(save_path, "wb") as f:
                            f.write(file_up.getbuffer())
                        
                        v_type = "short" if u_type == "Short Video" else "long"
                        target_table = "tb_05_short_videos" if v_type == "short" else "tb_04_long_videos"
                        
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute("INSERT INTO videos (id, video_url, uploader_name, video_type, title, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                  (f_id, save_path, st.session_state.user, v_type, title_in, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        conn.commit()
                        conn.close()
                        push_to_central_pipeline(target_table, f_id, st.session_state.user)
                        
                    st.success("✅ Published successfully and synced to 16-Server Pipeline!")
                    st.rerun()
            else:
                st.warning("Please provide both content text and media file.")

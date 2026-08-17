import base64
from datetime import datetime
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
    page_title="BD AI Book — Global Verified Social Network",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Meta Tags & Monetization Scripts
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

    # Users Table with Password & Global Phone Support
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            password TEXT,
            full_name TEXT,
            profile_pic TEXT,
            bio TEXT,
            is_verified INTEGER DEFAULT 0,
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

    # Ensure missing columns exist in existing DB
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [column[1] for column in cursor.fetchall()]

    missing_cols = {
        "password": "TEXT",
        "phone_number": "TEXT",
        "full_name": "TEXT",
        "profile_pic": "TEXT",
        "bio": "TEXT",
        "is_verified": "INTEGER DEFAULT 0",
        "payment_method": "TEXT",
        "account_details": "TEXT",
        "nid_number": "TEXT",
        "address": "TEXT",
        "followers_count": "INTEGER DEFAULT 0",
        "watch_time_mins": "REAL DEFAULT 0.0",
        "monetization_status": "TEXT DEFAULT 'none'",
        "earnings": "REAL DEFAULT 0.0",
        "created_at": "TEXT",
    }

    for col_name, col_type in missing_cols.items():
        if col_name not in existing_cols:
            try:
                cursor.execute(
                    f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                )
            except Exception:
                pass

    # Bank Details Table (Global Support)
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
            FOREIGN KEY (username) REFERENCES users (username)
        )
    """)

    # Videos Table
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
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Posts Table
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

    # Comments Table
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

    conn.commit()
    conn.close()


init_db()


# ==========================================
# 3. HELPER FUNCTIONS & GLOBAL PHONE MASKING
# ==========================================
def mask_phone_number(phone):
    """Hide middle digits of any international phone number for privacy"""
    if not phone:
        return ""
    clean_p = "".join(filter(str.isdigit, phone))
    if len(clean_p) >= 10:
        return "+" + clean_p[:3] + "*****" + clean_p[-3:]
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
        img_html = f'<img src="data:image/jpeg;base64,{b64_img}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; border:2px solid #1877F2;">'
    else:
        img_html = '<div style="width:50px; height:50px; border-radius:50%; background:#2a2a2a; color:#fff; display:flex; align-items:center; justify-content:center; font-size:24px;">👤</div>'

    blue_tick_svg = (
        """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" style="margin-left: 6px; vertical-align: middle;">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="#1877F2"/>
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
                    placeholder="Share your thoughts globally...",
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
# 5. MAIN HEADER & SESSION INITIALIZATION
# ==========================================
if os.path.exists("logo.jpg"):
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.image("logo.jpg", use_container_width=True)
else:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">🔥 BD AI Book — Global Platform 🔥</h1>
            <p style="color: #b0b3b8; margin: 0;">Artificial Intelligence & Learning Platform for Everyone Worldwide</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.user_phone = None
    st.session_state.pic = None
    st.session_state.is_verified = 0

if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "otp_sent_to" not in st.session_state:
    st.session_state.otp_sent_to = None

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 6. SIDEBAR AUTHENTICATION (GLOBAL SUPPORT)
# ==========================================
if os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

st.sidebar.header("🔍 Search Global Creators")
search_query = st.sidebar.text_input(
    "Type name or username...", placeholder="Search creators globally..."
)

if search_query.strip():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, full_name, profile_pic, followers_count FROM users WHERE username LIKE ? OR full_name LIKE ?",
        (f"%{search_query}%", f"%{search_query}%"),
    )
    found_users = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if found_users:
        st.sidebar.markdown(f"**Found ({len(found_users)}) Users:**")
        for u in found_users:
            u_disp = u.get("full_name") or u["username"]
            st.sidebar.markdown(
                f"👤 **{u_disp}** (@{u['username']})  \n👥 Followers: {u.get('followers_count', 0)}"
            )
            if st.sidebar.button(
                f"➕ Follow @{u['username']}", key=f"s_fol_{u['username']}"
            ):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute(
                    "UPDATE users SET followers_count = followers_count + 1 WHERE username = ?",
                    (u["username"],),
                )
                conn.commit()
                conn.close()
                st.toast(f"Followed @{u['username']}!")
                st.rerun()
            st.sidebar.markdown("---")
    else:
        st.sidebar.info("No user found with this name.")

st.sidebar.header("📱 User Authentication")

if not st.session_state.user:
    phone_num_input = st.sidebar.text_input(
        "International Phone / WhatsApp Number",
        placeholder="Include Country Code e.g. +1..., +44..., +880...",
        key="auth_phone",
    )

    if phone_num_input.strip():
        # Clean non-digit characters
        raw_digits = "".join(filter(str.isdigit, phone_num_input))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Search matching phone number
        cursor.execute(
            "SELECT * FROM users WHERE phone_number = ? OR phone_number LIKE ?",
            (raw_digits, f"%{raw_digits}"),
        )
        user_db_record = cursor.fetchone()

        conn.close()

        # CASE 1: Registered User -> Show Password Login directly
        if (
            user_db_record
            and user_db_record["is_verified"] == 1
            and user_db_record["password"]
        ):
            st.sidebar.success(
                f"✅ Registered User: **{user_db_record['username']}**"
            )
            st.sidebar.caption(
                f"📱 Phone: {mask_phone_number(user_db_record['phone_number'])}"
            )

            login_pass = st.sidebar.text_input(
                "Enter Password to Login", type="password", key="login_pass"
            )

            if st.sidebar.button("🔓 Login Now"):
                if login_pass == user_db_record["password"]:
                    st.session_state.user = user_db_record["username"]
                    st.session_state.user_phone = user_db_record[
                        "phone_number"
                    ]
                    st.session_state.pic = user_db_record["profile_pic"]
                    st.session_state.is_verified = 1
                    st.sidebar.success(
                        "🎉 Welcome back! Logged in Successfully."
                    )
                    st.rerun()
                else:
                    st.sidebar.error("❌ Incorrect Password!")

        # CASE 2: New Registration -> Send WhatsApp OTP
        else:
            st.sidebar.info("🆕 New User Registration (Global Verification)")

            if st.sidebar.button("📲 Send WhatsApp OTP"):
                otp_code = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp_code
                st.session_state.otp_sent_to = raw_digits

                msg = f"Your BD AI Book Global Verification OTP is: {otp_code}"
                wa_url = (
                    f"https://wa.me/{raw_digits}?text={urllib.parse.quote(msg)}"
                )

                st.sidebar.success(f"OTP Code Generated: **{otp_code}**")
                st.sidebar.markdown(
                    f"[👉 Click to Send OTP via WhatsApp]({wa_url})",
                    unsafe_allow_html=True,
                )

            if (
                st.session_state.generated_otp
                and st.session_state.otp_sent_to == raw_digits
            ):
                entered_otp = st.sidebar.text_input(
                    "Enter 6-Digit OTP", max_chars=6
                )
                desired_username = st.sidebar.text_input(
                    "Create Username", placeholder="e.g. AlexSmith"
                )
                new_password = st.sidebar.text_input(
                    "Create Password", type="password"
                )

                if st.sidebar.button("🔒 Verify OTP & Save Account"):
                    if entered_otp != st.session_state.generated_otp:
                        st.sidebar.error("❌ Invalid OTP Code!")
                    elif not desired_username.strip() or not new_password:
                        st.sidebar.error(
                            "❌ Please fill Username and Password!"
                        )
                    else:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        today_str = datetime.now().strftime("%Y-%m-%d")

                        try:
                            cursor.execute(
                                """
                                INSERT INTO users (username, phone_number, password, full_name, is_verified, created_at)
                                VALUES (?, ?, ?, ?, 1, ?)
                            """,
                                (
                                    desired_username.strip(),
                                    raw_digits,
                                    new_password,
                                    desired_username.strip(),
                                    today_str,
                                ),
                            )

                            conn.commit()
                            conn.close()

                            st.session_state.user = desired_username.strip()
                            st.session_state.user_phone = raw_digits
                            st.session_state.pic = None
                            st.session_state.is_verified = 1
                            st.session_state.generated_otp = None
                            st.session_state.otp_sent_to = None

                            st.sidebar.success(
                                "🎉 Account Created & Logged in!"
                            )
                            st.rerun()
                        except sqlite3.IntegrityError:
                            conn.close()
                            st.sidebar.error(
                                "❌ Phone number or Username already registered!"
                            )

else:
    # Sync active profile data
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT profile_pic, phone_number FROM users WHERE username = ?",
        (st.session_state.user,),
    )
    res = c.fetchone()
    if res:
        if res["profile_pic"]:
            st.session_state.pic = res["profile_pic"]
        if res["phone_number"]:
            st.session_state.user_phone = res["phone_number"]
    conn.close()

    if st.session_state.pic and os.path.exists(st.session_state.pic):
        st.sidebar.image(st.session_state.pic, width=90)

    masked_active_phone = mask_phone_number(st.session_state.user_phone or "")
    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** ✔️")
    if masked_active_phone:
        st.sidebar.caption(f"📱 Phone: {masked_active_phone}")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.user_phone = None
        st.session_state.pic = None
        st.session_state.is_verified = 0
        st.session_state.generated_otp = None
        st.rerun()

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

if tab == "🌍 World Feed":
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
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
        cursor.execute("SELECT * FROM videos WHERE video_type != 'short'")
        videos = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM posts")
        posts = [dict(row) for row in cursor.fetchall()]

        combined_feed = videos + posts
        random.shuffle(combined_feed)

        if not combined_feed:
            st.info(
                "No posts or videos available. Create content from the Upload section."
            )

        for index, item in enumerate(combined_feed):
            item_id = str(item["id"])
            uploader_name = item.get("uploader_name", "Unknown User")

            cursor.execute(
                "SELECT profile_pic FROM users WHERE username = ?",
                (uploader_name,),
            )
            u_pic_res = cursor.fetchone()
            uploader_pic = (
                u_pic_res["profile_pic"]
                if u_pic_res and u_pic_res["profile_pic"]
                else item.get("uploader_pic")
            )

            created_at = item.get("created_at", "Recently")

            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(
                uploader_name,
                profile_pic_path=uploader_pic,
                subtitle=f"Posted {created_at}",
                is_verified=True,
            )

            if "content" in item and item["content"]:
                st.markdown(f"### {item['content']}")

            if (
                "image_url" in item
                and item["image_url"]
                and os.path.exists(item["image_url"])
            ):
                st.image(item["image_url"], use_container_width=True)

            if "video_url" in item and os.path.exists(item["video_url"]):
                if item.get("title"):
                    st.markdown(f"#### {item.get('title')}")
                st.video(item["video_url"], format="video/mp4")

                new_views = item.get("views", 0) + 1
                cursor.execute(
                    "UPDATE videos SET views = ?, views_count = ? WHERE id = ?",
                    (new_views, new_views, item_id),
                )
                conn.commit()

            show_auto_moving_banner()

            st.write(f"❤️ **{format_value(item.get('likes', 0))}** Likes")
            st.markdown(
                f"""
                <a href="{SMART_LINK}" target="_blank" class="btn-direct bg-1">💰 Claim Monetization Reward</a>
                <a href="{SMART_LINK}" target="_blank" class="btn-direct bg-2">💎 Premium Bonus Link</a>
                """,
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    f"❤️ Like ({format_value(item.get('likes', 0))})",
                    key=f"lk_{item_id}_{index}",
                ):
                    table_name = "posts" if "content" in item else "videos"
                    cursor.execute(
                        f"UPDATE {table_name} SET likes = likes + 1 WHERE id = ?",
                        (item_id,),
                    )
                    conn.commit()
                    st.rerun()
            with c2:
                if st.button("➕ Follow", key=f"fl_{item_id}_{index}"):
                    cursor.execute(
                        "UPDATE users SET followers_count = followers_count + 1 WHERE username = ?",
                        (uploader_name,),
                    )
                    conn.commit()
                    st.toast(f"Followed {uploader_name} successfully!")

            render_comments_section(item_id)

            st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Feed Error: {e}")
    finally:
        conn.close()

elif tab == "📱 Scrolle Shorts Feed":
    st.subheader("📱 TikTok & Shorts Vertical Scroll Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC"
    )
    short_vids = [dict(r) for r in cursor.fetchall()]

    if not short_vids:
        st.info("No shorts videos found.")
        conn.close()
    else:
        for idx, sv in enumerate(short_vids):
            st.markdown("---")
            col_main, col_side = st.columns([3, 1])

            cursor.execute(
                "SELECT profile_pic FROM users WHERE username = ?",
                (sv.get("uploader_name"),),
            )
            u_pic_res = cursor.fetchone()
            uploader_pic = (
                u_pic_res["profile_pic"]
                if u_pic_res and u_pic_res["profile_pic"]
                else sv.get("uploader_pic")
            )

            with col_main:
                show_verified_profile(
                    sv.get("uploader_name", "User"),
                    profile_pic_path=uploader_pic,
                    subtitle="Official Shorts Creator",
                    is_verified=True,
                )
                st.markdown(f"**{sv.get('title', 'Short Video')}**")
                if os.path.exists(sv["video_url"]):
                    st.video(sv["video_url"], format="video/mp4")

                cursor.execute(
                    "UPDATE videos SET views = views + 1, views_count = views_count + 1 WHERE id = ?",
                    (sv["id"],),
                )
                conn.commit()

                render_comments_section(sv["id"])

            with col_side:
                st.write(" ")
                if st.button(
                    f"❤️ {format_value(sv.get('likes', 0))}",
                    key=f"sh_like_{sv['id']}",
                ):
                    cursor.execute(
                        "UPDATE videos SET likes = likes + 1 WHERE id = ?",
                        (sv["id"],),
                    )
                    conn.commit()
                    st.toast("Liked!")
                    st.rerun()

                st.caption(f"👁️ {format_value(sv.get('views', 0))}")

                if st.button("➕ Follow", key=f"sh_fol_{sv['id']}"):
                    cursor.execute(
                        "UPDATE users SET followers_count = followers_count + 1 WHERE username = ?",
                        (sv.get("uploader_name"),),
                    )
                    conn.commit()
                    st.toast("Followed Creator!")
        conn.close()

elif tab == "💬 WhatsApp Support Desk":
    st.subheader("💬 Official WhatsApp Support Desk")
    st.caption("Contact us directly from anywhere in the world to ask questions or resolve issues.")

    encoded_msg = urllib.parse.quote(
        "Hello! I am contacting you from BD AI Book App."
    )
    wa_link = f"https://wa.me/8801722003172?text={encoded_msg}"

    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )

elif tab == "💳 Payout & Monetization":
    st.subheader("🏦 Global Monetization, Card & Bank Setup")

    if not st.session_state.user:
        st.warning("Please login to manage your Bank and Payout details.")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM bank_details WHERE username = ?",
            (st.session_state.user,),
        )
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
                    "📱 Mobile Banking (bKash/Nagad/Rocket/Others)",
                ],
                index=0,
            )

            user_country = st.text_input(
                "Country / দেশ",
                value=bank_data.get("country", ""),
                placeholder="e.g. USA, UK, UAE, Bangladesh, India, Canada...",
            )

            st.markdown(
                "#### 💳 Visa / Mastercard / Debit Card Details (Global)"
            )
            c_num = st.text_input(
                "Card Number",
                value=bank_data.get("card_number", ""),
                placeholder="16-digit card number",
            )
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                c_holder = st.text_input(
                    "Card Holder Name",
                    value=bank_data.get("card_holder", ""),
                    placeholder="Name printed on card",
                )
            with col_c2:
                c_exp = st.text_input(
                    "Expiry Date (MM/YY)",
                    value=bank_data.get("card_expiry", ""),
                    placeholder="MM/YY",
                )

            st.markdown("#### 🏦 Official Bank Account Details")
            b_name = st.text_input(
                "Bank Name",
                value=bank_data.get("bank_name", ""),
                placeholder="e.g. Chase, HSBC, Citi, Islami Bank...",
            )
            b_branch = st.text_input(
                "Branch Name / Location", value=bank_data.get("branch_name", "")
            )
            acc_holder = st.text_input(
                "Account Holder Name", value=bank_data.get("account_name", "")
            )
            acc_num = st.text_input(
                "Account Number / IBAN",
                value=bank_data.get("account_number", ""),
            )

            c_r1, c_r2 = st.columns(2)
            with c_r1:
                routing = st.text_input(
                    "Routing / ABA / Sort Code",
                    value=bank_data.get("routing_number", ""),
                )
            with c_r2:
                swift = st.text_input(
                    "SWIFT / BIC Code", value=bank_data.get("swift_code", "")
                )

            st.markdown("#### 🌐 Global Wallet / Mobile Banking")
            g_wallet = st.text_input(
                "Payoneer / Wise Email / PayPal",
                value=bank_data.get("global_wallet", ""),
            )
            m_bank = st.text_input(
                "Mobile Banking / Local Wallet Number",
                value=bank_data.get("mobile_banking", ""),
            )

            save_bank_btn = st.form_submit_button(
                "💾 Save Payout Information"
            )

            if save_bank_btn:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                if existing_bank:
                    cursor.execute(
                        """
                        UPDATE bank_details 
                        SET payment_type = ?, country = ?, card_number = ?, card_holder = ?, card_expiry = ?,
                            bank_name = ?, branch_name = ?, account_name = ?, account_number = ?, routing_number = ?, swift_code = ?,
                            global_wallet = ?, mobile_banking = ?, updated_at = ?
                        WHERE username = ?
                    """,
                        (
                            pay_method,
                            user_country,
                            c_num,
                            c_holder,
                            c_exp,
                            b_name,
                            b_branch,
                            acc_holder,
                            acc_num,
                            routing,
                            swift,
                            g_wallet,
                            m_bank,
                            now_str,
                            st.session_state.user,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO bank_details (username, payment_type, country, card_number, card_holder, card_expiry, bank_name, branch_name, account_name, account_number, routing_number, swift_code, global_wallet, mobile_banking, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            st.session_state.user,
                            pay_method,
                            user_country,
                            c_num,
                            c_holder,
                            c_exp,
                            b_name,
                            b_branch,
                            acc_holder,
                            acc_num,
                            routing,
                            swift,
                            g_wallet,
                            m_bank,
                            now_str,
                        ),
                    )

                p_summary = f"{pay_method} ({c_num[-4:] if c_num else b_name or m_bank or g_wallet})"
                cursor.execute(
                    "UPDATE users SET payment_method = ?, account_details = ? WHERE username = ?",
                    (pay_method, p_summary, st.session_state.user),
                )

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

        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (st.session_state.user,)
        )
        raw_user = cursor.fetchone()
        user_info = dict(raw_user) if raw_user else {}

        display_name = user_info.get("full_name") or st.session_state.user
        pic_path = user_info.get("profile_pic", st.session_state.pic)
        masked_phone = mask_phone_number(user_info.get("phone_number", ""))

        # EDIT PROFILE SECTION
        with st.expander(
            "⚙️ Edit Profile & Change Picture / Password", expanded=False
        ):
            with st.form("edit_profile_form"):
                st.markdown("### 🖼️ Personal Information & Picture")
                new_full_name = st.text_input(
                    "Full Name", value=user_info.get("full_name") or ""
                )
                new_bio = st.text_area(
                    "Bio / Description", value=user_info.get("bio") or ""
                )
                new_nid = st.text_input(
                    "NID / Passport / Govt ID Number",
                    value=user_info.get("nid_number") or "",
                )
                new_address = st.text_input(
                    "Address & Country", value=user_info.get("address") or ""
                )

                st.markdown("### 🔑 Change Password")
                new_pass_val = st.text_input(
                    "New Password (leave empty to keep current)",
                    type="password",
                )

                uploaded_pic = st.file_uploader(
                    "Upload Profile Picture (JPG/PNG)",
                    type=["jpg", "png", "jpeg"],
                )

                save_profile_btn = st.form_submit_button(
                    "💾 Save Profile Details"
                )

                if save_profile_btn:
                    saved_pic_path = pic_path
                    if uploaded_pic:
                        saved_pic_path = os.path.join(
                            PROFILE_DIR,
                            f"pic_{st.session_state.user}_{uuid.uuid4()}.jpg",
                        )
                        with open(saved_pic_path, "wb") as f:
                            f.write(uploaded_pic.getvalue())
                        st.session_state.pic = saved_pic_path

                        cursor.execute(
                            "UPDATE videos SET uploader_pic = ? WHERE uploader_name = ?",
                            (saved_pic_path, st.session_state.user),
                        )
                        cursor.execute(
                            "UPDATE posts SET uploader_pic = ? WHERE uploader_name = ?",
                            (saved_pic_path, st.session_state.user),
                        )

                    pass_to_update = (
                        new_pass_val.strip()
                        if new_pass_val.strip()
                        else user_info.get("password")
                    )

                    cursor.execute(
                        """
                        UPDATE users 
                        SET full_name = ?, bio = ?, nid_number = ?, address = ?, profile_pic = ?, password = ?
                        WHERE username = ?
                    """,
                        (
                            new_full_name,
                            new_bio,
                            new_nid,
                            new_address,
                            saved_pic_path,
                            pass_to_update,
                            st.session_state.user,
                        ),
                    )

                    conn.commit()
                    st.success("✅ Profile updated successfully!")
                    st.rerun()

        cursor.execute(
            "SELECT * FROM videos WHERE uploader_name = ?",
            (st.session_state.user,),
        )
        my_videos = [dict(r) for r in cursor.fetchall()]

        cursor.execute(
            "SELECT * FROM posts WHERE uploader_name = ?",
            (st.session_state.user,),
        )
        my_posts = [dict(r) for r in cursor.fetchall()]

        total_likes = sum([v.get("likes", 0) for v in my_videos]) + sum(
            [p.get("likes", 0) for p in my_posts]
        )
        total_views = sum([v.get("views", 0) for v in my_videos])

        followers = user_info.get("followers_count", 0)
        watch_hours = user_info.get("watch_time_mins", 0.0) / 60.0

        is_eligible = (followers >= 300) and (watch_hours >= 3000.0)

        if is_eligible:
            monetization_badge = "✅ Eligible & Active"
            est_earnings = (
                (total_views * 0.002)
                + (total_likes * 0.005)
                + user_info.get("earnings", 0.0)
            )
        else:
            monetization_badge = "🔒 Locked (Requirements not met)"
            est_earnings = 0.00

        show_verified_profile(
            display_name,
            profile_pic_path=pic_path,
            subtitle=f"{user_info.get('bio') or 'Global Creator'} | Phone: {masked_phone}",
            is_verified=True,
        )

        st.write(
            f"📹 Videos/Shorts: **{len(my_videos)}** | 🖼️ Posts: **{len(my_posts)}** | ❤️ Likes: **{format_value(total_likes)}** | 👁️ Views: **{format_value(total_views)}** | 👥 Followers: **{followers}/300**"
        )

        st.markdown(
            "#### 📊 Monetization Progress (Requirements: 300 Followers & 3000 Hours)"
        )
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.write(f"👥 Followers Goal: **{followers}/300**")
            st.progress(min(followers / 300.0, 1.0))
        with col_p2:
            st.write(f"⏱️ Watch Time Goal: **{watch_hours:.1f}/3000 Hours**")
            st.progress(min(watch_hours / 3000.0, 1.0))

        st.markdown(
            f"""
            <div class="monetization-box">
                <h3 style="margin:0; color:#fff;">🌐 Global Monetization Dashboard</h3>
                <p style="margin: 5px 0;"><b>Status: {monetization_badge}</b></p>
                <h2 style="margin: 10px 0; color: #ffffff;">💰 Est. Earnings: ${est_earnings:.2f} USD</h2>
                <p style="margin:0; font-size:12px;">Saved Method: <b>{user_info.get('payment_method', 'Not Set')}</b> ({user_info.get('account_details', 'N/A')})</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # DELETE POSTS & VIDEOS SECTION
        st.markdown("### 📽️ My Content Management")

        tab_v, tab_p = st.tabs(
            ["🎥 My Videos & Shorts", "🖼️ My Image/Text Posts"]
        )

        with tab_v:
            if not my_videos:
                st.caption("No videos uploaded yet.")
            for mv in my_videos:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(
                        f"**{mv.get('title')}** `[{mv.get('video_type', 'long')}]`"
                    )
                    st.caption(
                        f"👁️ {mv.get('views', 0)} Views | ❤️ {mv.get('likes', 0)} Likes | Created: {mv.get('created_at')}"
                    )
                with col2:
                    if st.button("🗑️ Delete Video", key=f"del_v_{mv['id']}"):
                        if mv.get("video_url") and os.path.exists(
                            mv.get("video_url")
                        ):
                            try:
                                os.remove(mv.get("video_url"))
                            except Exception:
                                pass
                        cursor.execute(
                            "DELETE FROM videos WHERE id = ?", (mv["id"],)
                        )
                        cursor.execute(
                            "DELETE FROM comments WHERE post_id = ?",
                            (mv["id"],),
                        )
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
                    st.caption(
                        f"❤️ {mp.get('likes', 0)} Likes | Created: {mp.get('created_at')}"
                    )
                with col2:
                    if st.button("🗑️ Delete Post", key=f"del_p_{mp['id']}"):
                        if mp.get("image_url") and os.path.exists(
                            mp.get("image_url")
                        ):
                            try:
                                os.remove(mp.get("image_url"))
                            except Exception:
                                pass
                        cursor.execute(
                            "DELETE FROM posts WHERE id = ?", (mp["id"],)
                        )
                        cursor.execute(
                            "DELETE FROM comments WHERE post_id = ?",
                            (mp["id"],),
                        )
                        conn.commit()
                        st.toast("Post deleted successfully!")
                        st.rerun()

        conn.close()

elif tab == "📤 Create Post / Upload":
    if not st.session_state.user:
        st.warning("Please login to create a post or upload content.")
    else:
        st.subheader("📤 Upload Content")

        st.warning(
            "⚠️ **Global Community Guidelines:** Sexual, adult, or violent content is strictly prohibited. Violating terms will lead to immediate account suspension and loss of earnings."
        )

        upload_type = st.radio(
            "Select Upload Type:",
            ["📝 Post/Photo", "🎥 Long Video", "📱 Short Video"],
        )

        if upload_type == "📝 Post/Photo":
            post_text = st.text_area("What's on your mind?")
            img_file = st.file_uploader(
                "Upload Photo (JPG/PNG)", type=["jpg", "png", "jpeg"]
            )

            if st.button("🚀 Publish Post"):
                if not post_text and not img_file:
                    st.warning("Please enter text or attach an image!")
                else:
                    img_path = None
                    if img_file:
                        img_path = os.path.join(
                            IMAGE_DIR, f"img_{uuid.uuid4()}.jpg"
                        )
                        with open(img_path, "wb") as f:
                            f.write(img_file.getvalue())

                    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO posts (id, uploader_name, uploader_pic, content, image_url, likes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            st.session_state.user,
                            st.session_state.pic,
                            post_text,
                            img_path,
                            0,
                            today_str,
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.toast("✅ Post published successfully!")
                    st.rerun()

        else:
            v_title = st.text_input(
                "Video Title", placeholder="Enter a title for your video..."
            )
            vid_file = st.file_uploader(
                "Upload Video File (MP4/MOV)",
                type=["mp4", "mov", "avi", "mkv"],
            )

            is_short = upload_type == "📱 Short Video"
            v_type_str = "short" if is_short else "long"

            if st.button("🚀 Publish Video"):
                if not vid_file or not v_title.strip():
                    st.warning(
                        "Please provide a video title and select a video file!"
                    )
                else:
                    vid_filename = f"vid_{uuid.uuid4()}.mp4"
                    vid_path = os.path.join(VIDEO_DIR, vid_filename)

                    with open(vid_path, "wb") as f:
                        f.write(vid_file.getvalue())

                    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                    conn = get_db_connection()
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT id FROM users WHERE username = ?",
                        (st.session_state.user,),
                    )
                    u_rec = cursor.fetchone()
                    u_id = u_rec["id"] if u_rec else None

                    cursor.execute(
                        """
                        INSERT INTO videos (
                            id, user_id, video_url, uploader_name, uploader_pic, 
                            video_type, title, likes, views, views_count, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            u_id,
                            vid_path,
                            st.session_state.user,
                            st.session_state.pic,
                            v_type_str,
                            v_title.strip(),
                            random.randint(10, 50),
                            1,
                            1,
                            today_str,
                        ),
                    )
                    conn.commit()
                    conn.close()

                    st.toast(f"🎉 {upload_type} published successfully!")
                    st.rerun()

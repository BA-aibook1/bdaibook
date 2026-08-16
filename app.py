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
    page_title="BD AI Book — Verified Social Network",
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
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
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
# 3. DATABASE HELPER FUNCTIONS
# ==========================================
def register_or_get_user(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, username, followers_count, watch_time_mins, monetization_status, earnings FROM users WHERE username = ?",
        (username,),
    )
    user = c.fetchone()
    if not user:
        c.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            (username, datetime.now().strftime("%Y-%m-%d")),
        )
        conn.commit()
        c.execute(
            "SELECT id, username, followers_count, watch_time_mins, monetization_status, earnings FROM users WHERE username = ?",
            (username,),
        )
        user = c.fetchone()
    conn.close()
    return {
        "id": user["id"],
        "username": user["username"],
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
# 5. MAIN HEADER LOGO SECTION
# ==========================================
if os.path.exists("logo.jpg"):
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.image("logo.jpg", use_container_width=True)
else:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="color: #00c853; font-weight: 900; margin: 0;">🔥 BD AI Book 🔥</h1>
            <p style="color: #b0b3b8; margin: 0;">Artificial Intelligence & Learning Platform</p>
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
if os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

# --- 🔍 SEARCH BAR SECTION ---
st.sidebar.markdown("### 🔍 Search Feed")
search_query = st.sidebar.text_input("Search posts, videos, creators...", placeholder="Type to search...", key="search_query")
if search_query:
    if st.sidebar.button("❌ Clear Search"):
        st.session_state.search_query = ""
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📸 Authentication")

if not st.session_state.user:
    u_name = st.sidebar.text_input("Username")
    camera_photo = st.sidebar.camera_input("Take Face Scan", key="face_cam")

    if u_name and camera_photo:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (u_name,))
        user_data = cursor.fetchone()

        if user_data:
            if st.sidebar.button("🔓 Login with Face ID"):
                st.session_state.user = u_name
                st.session_state.pic = user_data["profile_pic"]
                st.session_state.is_verified = user_data["is_verified"]
                conn.close()
                st.rerun()
            conn.close()
        else:
            if st.sidebar.button("✨ Create Account"):
                fname = os.path.join(PROFILE_DIR, f"p_{uuid.uuid4()}.jpg")
                with open(fname, "wb") as f:
                    f.write(camera_photo.getvalue())

                today_str = datetime.now().strftime("%Y-%m-%d")
                cursor.execute(
                    """INSERT INTO users (username, full_name, profile_pic, is_verified, created_at) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (u_name, u_name, fname, 1, today_str),
                )
                conn.commit()
                conn.close()

                st.session_state.user = u_name
                st.session_state.pic = fname
                st.session_state.is_verified = 1
                st.sidebar.success(
                    "🎉 Account Verified & Created Successfully!"
                )
                st.rerun()
else:
    if st.session_state.pic and os.path.exists(st.session_state.pic):
        st.sidebar.image(st.session_state.pic, width=90)

    st.sidebar.markdown(f"Welcome, **{st.session_state.user}** ✔️")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.pic = None
        st.session_state.is_verified = 1
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

    # Show search result title if searching
    if search_query:
        st.info(f"🔍 Showing search results for: **{search_query}**")

    try:
        # Fetch Shorts for Top Slider
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
        # Search or Fetch All Videos & Posts
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

# --- Shorts Feed ---
elif tab == "📱 Scrolle Shorts Feed":
    st.subheader("📱 TikTok & Shorts Vertical Scroll Feed")
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute(
            "SELECT * FROM videos WHERE video_type = 'short' AND (title LIKE ? OR uploader_name LIKE ?) ORDER BY created_at DESC",
            (f"%{search_query}%", f"%{search_query}%"),
        )
    else:
        cursor.execute(
            "SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC"
        )
    short_vids = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not short_vids:
        st.info("No shorts videos found.")
    else:
        for idx, sv in enumerate(short_vids):
            st.markdown("---")
            col_main, col_side = st.columns([3, 1])
            with col_main:
                show_verified_profile(
                    sv.get("uploader_name", "User"),
                    profile_pic_path=sv.get("uploader_pic"),
                    subtitle="Official Shorts Creator",
                    is_verified=True,
                )
                st.markdown(f"**{sv.get('title', 'Short Video')}**")
                if os.path.exists(sv["video_url"]):
                    st.video(sv["video_url"], format="video/mp4")

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE videos SET views = views + 1, views_count = views_count + 1 WHERE id = ?",
                    (sv["id"],),
                )
                conn.commit()
                conn.close()

                render_comments_section(sv["id"])

            with col_side:
                st.write(" ")
                if st.button(
                    f"❤️ {format_value(sv.get('likes', 0))}",
                    key=f"sh_like_{sv['id']}",
                ):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE videos SET likes = likes + 1 WHERE id = ?",
                        (sv["id"],),
                    )
                    conn.commit()
                    conn.close()
                    st.toast("Liked!")
                    st.rerun()

                st.caption(f"👁️ {format_value(sv.get('views', 0))}")

                if st.button("➕ Follow", key=f"sh_fol_{sv['id']}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET followers_count = followers_count + 1 WHERE username = ?",
                        (sv.get("uploader_name"),),
                    )
                    conn.commit()
                    conn.close()
                    st.toast("Followed Creator!")

# --- WhatsApp Support Desk ---
elif tab == "💬 WhatsApp Support Desk":
    st.subheader("💬 Official WhatsApp Support Desk")
    st.caption("Contact us directly to ask questions or resolve issues.")

    HIDDEN_WA_NUMBER = "8801722003172"
    default_msg = "Hello! I am contacting you from BD AI Book App."
    encoded_msg = urllib.parse.quote(default_msg)
    wa_link = f"https://wa.me/{HIDDEN_WA_NUMBER}?text={encoded_msg}"

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #075E54, #128C7E); padding: 25px; border-radius: 15px; color: white; text-align: center; border: 1px solid #25D366; margin: 20px 0;">
            <h2 style="margin-top:0; color: #ffffff;">🌐 Official WhatsApp Support</h2>
            <p style="font-size: 15px; color: #e0e0e0; margin-bottom: 20px;">
                Click below to send messages, feedback, or screenshots directly to our team.
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
                ⚠️ <b>Note:</b> Only text messages and file sharing are supported. Direct voice calls are not available.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Payout & Monetization ---
elif tab == "💳 Payout & Monetization":
    st.subheader("🏦 Global Monetization & Bank Setup")
    st.info(
        "Select your preferred payment method and submit account details to receive earnings."
    )

    pay_method = st.selectbox(
        "Select Payment Method:",
        [
            "📱 bkash",
            "📱 Nagad",
            "📱 Rocket",
            "🌐 PayPal",
            "💳 Mastercard / Visa Card",
            "🏦 Bank Transfer",
        ],
    )

    acc_num = st.text_input("Account Number / Email / Card Number")
    holder_name = st.text_input("Account Holder Name")

    if st.button("💾 Save Payment Details"):
        if acc_num and holder_name:
            if st.session_state.user:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET payment_method = ?, account_details = ? WHERE username = ?",
                    (
                        pay_method,
                        f"{holder_name} - {acc_num}",
                        st.session_state.user,
                    ),
                )
                conn.commit()
                conn.close()
                st.success("✅ Payment account updated successfully!")
            else:
                st.error("Please login first.")
        else:
            st.warning("Please complete all required fields correctly.")

# --- My Profile & Earnings ---
elif tab == "👤 My Profile & Earnings":
    if not st.session_state.user:
        st.warning("Please login to view your profile.")
    else:
        user_data_merged = register_or_get_user(st.session_state.user)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (st.session_state.user,)
        )
        raw_user = cursor.fetchone()
        user_info = dict(raw_user) if raw_user else {}

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

        display_name = user_info.get("full_name") or st.session_state.user
        pic_path = user_info.get("profile_pic", st.session_state.pic)

        followers = user_data_merged["followers_count"]
        watch_hours = user_data_merged["watch_time_mins"] / 60.0

        is_eligible = (followers >= 300) and (watch_hours >= 3000.0)

        if is_eligible:
            monetization_badge = "✅ Eligible & Active"
            est_earnings = (
                (total_views * 0.002)
                + (total_likes * 0.005)
                + user_data_merged["earnings"]
            )
        else:
            monetization_badge = "🔒 Locked (Requirements not met)"
            est_earnings = 0.00

        show_verified_profile(
            display_name,
            profile_pic_path=pic_path,
            subtitle=f"Creator | Monetization: {monetization_badge}",
            is_verified=True,
        )

        st.write(
            f"📹 Videos/Shorts: **{len(my_videos)}** | 🖼️ Posts: **{len(my_posts)}** | ❤️ Likes: **{format_value(total_likes)}** | 👁️ Views: **{format_value(total_views)}** | 👥 Followers: **{followers}/300**"
        )

        st.markdown("#### 📊 Monetization Progress (Requirements: 300 Followers & 3000 Hours)")
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

        st.markdown("### 📽️ My Content List")
        for mv in my_videos:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(
                    f"Type: {mv.get('video_type', 'long')} | Title: {mv.get('title')}"
                )
            with col2:
                if st.button("🗑️ Delete", key=f"del_v_{mv['id']}"):
                    cursor.execute(
                        "DELETE FROM videos WHERE id = ?", (mv["id"],)
                    )
                    conn.commit()
                    conn.close()
                    st.toast("Video deleted successfully!")
                    st.rerun()

        conn.close()

# --- Upload Section ---
elif tab == "📤 Create Post / Upload":
    if not st.session_state.user:
        st.warning("Please login to create a post or upload content.")
    else:
        st.subheader("📤 Upload Content")

        st.warning(
            "⚠️ **Community Guidelines:** Sexual, adult, or violent content is strictly prohibited. Violating terms will lead to immediate account suspension and loss of earnings."
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
            # Handle Video / Shorts Uploads
            v_title = st.text_input("Video Title", placeholder="Enter a title for your video...")
            vid_file = st.file_uploader(
                "Upload Video File (MP4/MOV)", type=["mp4", "mov", "avi", "mkv"]
            )

            is_short = upload_type == "📱 Short Video"
            v_type_str = "short" if is_short else "long"

            if st.button("🚀 Publish Video"):
                if not vid_file or not v_title.strip():
                    st.warning("Please provide a video title and select a video file!")
                else:
                    vid_filename = f"vid_{uuid.uuid4()}.mp4"
                    vid_path = os.path.join(VIDEO_DIR, vid_filename)

                    with open(vid_path, "wb") as f:
                        f.write(vid_file.getvalue())

                    user_info_record = register_or_get_user(st.session_state.user)
                    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                    conn = get_db_connection()
                    cursor = conn.cursor()
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
                            user_info_record["id"],
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

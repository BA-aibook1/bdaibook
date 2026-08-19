import base64
from datetime import datetime
import os
import random
import sqlite3
import uuid

import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & AD ENGINE
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Universal Master Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global Ad Insertion Script (Monetag / Ad Network)
components.html(
    """
    <meta name="msvalidate.01" content="e776b8ce73ea3dcc07551e8a021a0907">
    <meta name="monetag" content="5cc1b7ba5cb29eff802ce49009f87e2b">
    <script src="https://alwingulla.com/88/tag.min.js" data-zone="12345" async data-cfasync="false"></script>
    """,
    height=0,
)

SECRET_OWNER_KEY = "S$s123456789112233"

# ==========================================
# 2. LOCAL STORAGE & DATABASE SETUP
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

def init_clean_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # ১. ইউজার টেবিল
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            full_name TEXT,
            country TEXT DEFAULT 'Bangladesh',
            profile_pic TEXT,
            followers_count INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # ২. পোস্ট ও ছবি
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            content TEXT,
            title TEXT,
            image_url TEXT,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            gifts INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # ৩. ভিডিও টেবিল (Shorts & Long Videos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            uploader_name TEXT,
            video_type TEXT, -- 'short' or 'long'
            video_url TEXT,
            title TEXT,
            description TEXT,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            gifts INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # ৪. কমেন্ট টেবিল
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT,
            user_name TEXT,
            comment_text TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

init_clean_database()

# ==========================================
# 3. HELPER FUNCTIONS & ALGORITHM
# ==========================================
def generate_algorithm_views():
    # ডেমো অ্যালগরিদম: ১,১০,০০০ থেকে ১০,০০,০০০ ভিউ জেনারেট করে
    return random.randint(110000, 10000000)

def show_ads_banner():
    st.markdown("""
        <div style="background:#222; padding:10px; text-align:center; border:1px dashed #00c853; margin:10px 0; border-radius:8px;">
            <p style="color:#00c853; margin:0; font-size:12px;">📢 Sponsored Advertisement (Monetag Auto Ad Engine Active)</p>
            <a href="https://www.google.com" target="_blank" style="color:#fff; text-decoration:none; font-weight:bold;">👉 Click Here To Check Special Offers</a>
        </div>
    """, unsafe_allow_html=True)

def render_comments(content_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM comments WHERE content_id = ? ORDER BY id DESC", (content_id,))
    comments = c.fetchall()
    conn.close()

    with st.expander(f"💬 Comments ({len(comments)})"):
        for cm in comments:
            st.markdown(f"**{cm['user_name']}**: {cm['comment_text']}")
        
        if st.session_state.get("user"):
            new_comment = st.text_input("Add a comment...", key=f"in_{content_id}")
            if st.button("Post Comment", key=f"btn_cm_{content_id}"):
                if new_comment.strip():
                    conn = get_db_connection()
                    conn.cursor().execute("INSERT INTO comments (content_id, user_name, comment_text, created_at) VALUES (?, ?, ?, ?)",
                                          (content_id, st.session_state.user, new_comment, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    conn.close()
                    st.rerun()

# ==========================================
# 4. SESSION & SIDEBAR AUTHENTICATION
# ==========================================
if "user" not in st.session_state:
    st.session_state.user = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "📱 TikTok Shorts Feed"

st.sidebar.markdown("### 🔍 Search Feed")
search_q = st.sidebar.text_input("Search or Secret Code...", key="search_query")
if search_q.strip() == SECRET_OWNER_KEY:
    st.session_state.user = "system_owner"

st.sidebar.markdown("---")
if not st.session_state.user:
    st.sidebar.subheader("Login / Register")
    u_name = st.sidebar.text_input("Username / Name")
    u_phone = st.sidebar.text_input("Phone Number")
    if st.sidebar.button("Quick Enter"):
        if u_name and u_phone:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE phone_number = ?", (u_phone,))
            usr = c.fetchone()
            if not usr:
                c.execute("INSERT INTO users (username, phone_number, full_name, created_at) VALUES (?, ?, ?, ?)",
                          (u_name, u_phone, u_name, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
            conn.close()
            st.session_state.user = u_name
            st.rerun()
else:
    st.sidebar.write(f"👤 Logged in as: **{st.session_state.user}**")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

nav_tabs = ["📱 TikTok Shorts Feed", "📺 Long Video Feed", "🖼️ Photo Feed", "📤 Upload Studio"]
tab = st.sidebar.radio("Navigation", nav_tabs)
st.session_state.active_tab = tab

# ==========================================
# 5. FEEDS & CONTENT SYSTEM
# ==========================================

# --- ১. শর্টস ভিডিও ফিড (Shorts Feed) ---
if tab == "📱 TikTok Shorts Feed":
    st.markdown("### 📱 TikTok Style Shorts Feed")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    shorts = [dict(r) for r in c.fetchall()]
    conn.close()

    # ফিডের উপরে ছোট আকারে প্রিভিউ লিস্ট
    if shorts:
        st.markdown("**🔥 Top Trending Shorts Preview**")
        cols = st.columns(min(len(shorts), 4))
        for idx, s_vid in enumerate(shorts[:4]):
            with cols[idx]:
                if os.path.exists(s_vid["video_url"]):
                    st.video(s_vid["video_url"])
                st.caption(f"👁️ {s_vid['views']} Views")

    st.divider()

    # মূল প্লেয়ার ফিড
    for vid in shorts:
        st.markdown(f"#### {vid['title']}")
        st.caption(f"Uploaded by: **{vid['uploader_name']}** | 👁️ **{vid['views']:,}** Views (Algorithm Boosted)")
        if os.path.exists(vid["video_url"]):
            st.video(vid["video_url"])

        # ইন্টারঅ্যাকশন কলাম
        c1, c2, c3, c4 = st.columns(4)
        if c1.button(f"❤️ Like ({vid['likes']})", key=f"lk_s_{vid['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if c2.button(f"➕ Follow Creator", key=f"fl_s_{vid['id']}"):
            st.toast(f"You followed {vid['uploader_name']}!")

        if c3.button(f"🎁 Send Gift ({vid['gifts']})", key=f"gf_s_{vid['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET gifts = gifts + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.toast("Gift Sent!")
            st.rerun()

        render_comments(vid['id'])
        show_ads_banner()
        st.divider()

# --- ২. লং ভিডিও ফিড (Long Video Feed) ---
elif tab == "📺 Long Video Feed":
    st.markdown("### 📺 Direct Long Videos Feed")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM videos WHERE video_type = 'long' ORDER BY created_at DESC")
    vids = [dict(r) for r in c.fetchall()]
    conn.close()

    for vid in vids:
        st.markdown(f"### {vid['title']}")
        st.caption(f"Channel: **{vid['uploader_name']}** | 👁️ **{vid['views']:,}** Views")
        st.write(vid['description'])
        if os.path.exists(vid["video_url"]):
            st.video(vid["video_url"])

        c1, c2, c3 = st.columns(3)
        if c1.button(f"👍 Like ({vid['likes']})", key=f"lk_l_{vid['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET likes = likes + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if c2.button(f"➕ Follow", key=f"fl_l_{vid['id']}"):
            st.toast(f"Followed {vid['uploader_name']}!")

        if c3.button(f"🎁 Gift ({vid['gifts']})", key=f"gf_l_{vid['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE videos SET gifts = gifts + 1 WHERE id = ?", (vid['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        render_comments(vid['id'])
        show_ads_banner()
        st.divider()

# --- ৩. ফটো পোস্ট ফিড (Photo Feed) ---
elif tab == "🖼️ Photo Feed":
    st.markdown("### 🖼️ World Photo & Image Feed")
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = [dict(r) for r in c.fetchall()]
    conn.close()

    for p in posts:
        st.markdown(f"**{p['uploader_name']}**")
        if p['title']:
            st.subheader(p['title'])
        st.write(p['content'])
        if p['image_url'] and os.path.exists(p['image_url']):
            st.image(p['image_url'], use_container_width=True)
        st.caption(f"👁️ {p['views']:,} Impressions")

        c1, c2, c3 = st.columns(3)
        if c1.button(f"❤️ Like ({p['likes']})", key=f"lk_p_{p['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (p['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        if c2.button("➕ Follow", key=f"fl_p_{p['id']}"):
            st.toast("Followed!")

        if c3.button(f"🎁 Gift ({p['gifts']})", key=f"gf_p_{p['id']}"):
            conn = get_db_connection()
            conn.cursor().execute("UPDATE posts SET gifts = gifts + 1 WHERE id = ?", (p['id'],))
            conn.commit()
            conn.close()
            st.rerun()

        render_comments(p['id'])
        show_ads_banner()
        st.divider()

# --- ৪. আপলোড স্টুডিও (Upload Studio) ---
elif tab == "📤 Upload Studio":
    st.markdown("### 📤 Global Upload Studio")
    if not st.session_state.user:
        st.warning("Please login first to upload content.")
    else:
        ctype = st.selectbox("Content Type", ["📱 Short Video (TikTok Style)", "📺 Direct Long Video", "🖼️ Photo Post"])
        title = st.text_input("Title")
        desc = st.text_area("Description / Caption")

        if ctype in ["📱 Short Video (TikTok Style)", "📺 Direct Long Video"]:
            v_file = st.file_uploader("Upload Video File", type=["mp4", "mov", "avi"])
            if st.button("Publish Video"):
                if v_file:
                    v_id = str(uuid.uuid4())
                    save_path = os.path.join(VIDEO_DIR, f"{v_id}.mp4")
                    with open(save_path, "wb") as f:
                        f.write(v_file.getbuffer())

                    v_type = "short" if ctype == "📱 Short Video (TikTok Style)" else "long"
                    auto_views = generate_algorithm_views()

                    conn = get_db_connection()
                    conn.cursor().execute("""
                        INSERT INTO videos (id, uploader_name, video_type, video_url, title, description, views, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (v_id, st.session_state.user, v_type, save_path, title, desc, auto_views, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()

                    st.success(f"🎉 Published with {auto_views:,} initial algorithm views!")
                    st.rerun()

        elif ctype == "🖼️ Photo Post":
            img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
            if st.button("Publish Photo"):
                p_id = str(uuid.uuid4())
                save_path = ""
                if img_file:
                    save_path = os.path.join(IMAGE_DIR, f"{p_id}.jpg")
                    with open(save_path, "wb") as f:
                        f.write(img_file.getbuffer())

                auto_views = generate_algorithm_views()

                conn = get_db_connection()
                conn.cursor().execute("""
                    INSERT INTO posts (id, uploader_name, content, title, image_url, views, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (p_id, st.session_state.user, desc, title, save_path, auto_views, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()

                st.success("🎉 Photo published successfully!")
                st.rerun()

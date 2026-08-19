import os
import re
import sqlite3
import random
import hashlib
from datetime import datetime
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM STYLES
# ==========================================
st.set_page_config(
    page_title="Global Sovereign Social & Video Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #e0e6ed;
    }
    .feed-card {
        background-color: #161f30;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        border: 1px solid #223049;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .verified-badge {
        color: #00c853;
        font-weight: bold;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Setup Media Folders
MEDIA_DIR = "uploaded_media"
os.makedirs(MEDIA_DIR, exist_ok=True)
DB_FILE = "sovereign_platform.db"

# ==========================================
# 2. DATABASE MANAGEMENT & HELPER FUNCTIONS
# ==========================================
def get_db_connection():
    """Establishes safe connection with SQLite db using timeout to prevent database lock issues."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes necessary database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vault / Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sovereign_vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_id TEXT UNIQUE,
            username TEXT UNIQUE,
            phone_number TEXT,
            gmail_address TEXT,
            hashed_password TEXT,
            profile_pic TEXT,
            security_tier INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    
    # Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploader_name TEXT,
            uploader_pic TEXT,
            title TEXT,
            video_type TEXT,
            video_url TEXT,
            views INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    
    # Posts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploader_name TEXT,
            uploader_pic TEXT,
            content TEXT,
            image_url TEXT,
            video_url TEXT,
            created_at TEXT
        )
    """)
    
    # Comments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            commenter_name TEXT,
            comment_text TEXT,
            created_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

def hash_password(password: str) -> str:
    """Hashes passwords securely using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def format_value(val):
    """Formats numeric values safely for UI display."""
    try:
        val = int(val)
        if val >= 1000000:
            return f"{val/1000000:.1f}M"
        if val >= 1000:
            return f"{val/1000:.1f}K"
        return str(val)
    except:
        return "0"

def show_verified_profile(display_name, profile_pic_path=None, subtitle=""):
    """Renders user profile header in feed items."""
    col1, col2 = st.columns([1, 8])
    with col1:
        if profile_pic_path and os.path.exists(profile_pic_path):
            st.image(profile_pic_path, width=50)
        else:
            st.markdown("👤")
    with col2:
        st.markdown(f"**{display_name}** <span class='verified-badge'>✔️</span>", unsafe_allow_html=True)
        if subtitle:
            st.caption(subtitle)

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "otp_code" not in st.session_state:
    st.session_state.otp_code = None
if "pending_user" not in st.session_state:
    st.session_state.pending_user = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🌍 World Feed"

# ==========================================
# 4. AUTHENTICATION (LOGIN & REGISTRATION)
# ==========================================
def render_auth_panel():
    st.title("🛡️ Global Sovereign Vault Authentication")
    
    auth_mode = st.radio("Choose Action:", ["Login", "Register"], horizontal=True)
    
    if auth_mode == "Register":
        st.subheader("📝 Create New Sovereign Account")
        with st.form("reg_form"):
            username = st.text_input("Username")
            phone = st.text_input("Phone Number")
            gmail = st.text_input("Gmail Address")
            password = st.text_input("Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            
            submit_reg = st.form_submit_button("Generate Verification OTP")
            
            if submit_reg:
                if not username or not password or not gmail:
                    st.error("❌ Please fill in all required fields!")
                elif password != confirm_pass:
                    st.error("❌ Passwords do not match!")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", gmail):
                    st.error("❌ Invalid Gmail Address format!")
                else:
                    generated_otp = str(random.randint(100000, 999999))
                    st.session_state.otp_code = generated_otp
                    st.session_state.pending_user = {
                        "username": username,
                        "phone": phone,
                        "gmail": gmail,
                        "pass": password
                    }
                    st.success(f"🔑 Verification OTP generated! (For testing: **{generated_otp}**)")
        
        # Verification Section
        if st.session_state.pending_user:
            st.divider()
            st.subheader("🔢 Enter Verification OTP")
            entered_otp = st.text_input("6-Digit OTP", max_chars=6)
            if st.button("Verify & Complete Registration"):
                if entered_otp == st.session_state.otp_code:
                    p_data = st.session_state.pending_user
                    vault_id = f"SOV-{random.randint(10000, 99999)}"
                    hashed_pass = hash_password(p_data["pass"])
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO global_sovereign_vault 
                            (vault_id, username, phone_number, gmail_address, hashed_password, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (vault_id, p_data["username"], p_data["phone"], p_data["gmail"], hashed_pass, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("🎉 Account created successfully! Please login.")
                        st.session_state.pending_user = None
                        st.session_state.otp_code = None
                    except sqlite3.IntegrityError:
                        st.error("❌ Username or Vault ID already exists!")
                    finally:
                        conn.close()
                else:
                    st.error("❌ Invalid OTP Code!")

    elif auth_mode == "Login":
        st.subheader("🔑 Sign In to Vault")
        with st.form("login_form"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Access Vault")
            
            if submit_login:
                hashed_pass = hash_password(login_pass)
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM global_sovereign_vault 
                    WHERE username = ? AND hashed_password = ?
                """, (login_user, hashed_pass))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_info = dict(user)
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username or Password!")

if not st.session_state.authenticated:
    render_auth_panel()
    st.stop()

# ==========================================
# 5. SIDEBAR & NAVIGATION (LOGGED IN STATE)
# ==========================================
with st.sidebar:
    st.title("🎬 Sovereign Hub")
    st.markdown(f"Welcome, **{st.session_state.user_info['username']}**! ✨")
    
    # Navigation Radio Button
    menu = ["🌍 World Feed", "📱 Scrolle Shorts Feed", "📤 Upload Center", "👤 My Vault"]
    tab = st.radio("Navigation:", menu, index=menu.index(st.session_state.active_tab) if st.session_state.active_tab in menu else 0)
    st.session_state.active_tab = tab

    search_query = st.text_input("🔍 Global Search")
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()

# Helper function to render comment box
def render_comments_section(item_id):
    st.markdown("##### 💬 Comments")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY id DESC", (item_id,))
    comments = cursor.fetchall()
    
    for c in comments:
        st.caption(f"**{c['commenter_name']}**: {c['comment_text']}")
        
    with st.form(key=f"comment_form_{item_id}"):
        new_comment = st.text_input("Write a comment...", key=f"input_{item_id}")
        if st.form_submit_button("Post Comment"):
            if new_comment.strip():
                cursor.execute("""
                    INSERT INTO comments (post_id, commenter_name, comment_text, created_at)
                    VALUES (?, ?, ?, ?)
                """, (item_id, st.session_state.user_info['username'], new_comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Comment added!")
                st.rerun()
    conn.close()

# ==========================================
# 6. TAB IMPLEMENTATIONS
# ==========================================

# ---------------- Tab 1: World Feed ----------------
if tab == "🌍 World Feed":
    st.title("🌍 Global World Feed")
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        st.info(f"🔍 Showing search results for: **{search_query}**")

    # Short Videos Render Section
    try:
        if search_query:
            cursor.execute(
                "SELECT * FROM videos WHERE video_type = 'short' AND (title LIKE ? OR uploader_name LIKE ?) ORDER BY created_at DESC",
                (f"%{search_query}%", f"%{search_query}%"),
            )
        else:
            cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
        
        short_videos = [dict(r) for r in cursor.fetchall()]

        if short_videos:
            st.markdown('<h3 style="color: #00c853;">▶️ Shorts Highlight</h3>', unsafe_allow_html=True)
            cols = st.columns(min(len(short_videos), 3))
            for i, sv in enumerate(short_videos[:3]):
                with cols[i]:
                    st.markdown(f"**{sv.get('uploader_name', 'User')}** ✔️")
                    if sv.get("video_url") and os.path.exists(sv["video_url"]):
                        st.video(sv["video_url"])
                    if st.button("▶️ Watch in Shorts", key=f"open_short_{sv['id']}"):
                        st.session_state.active_tab = "📱 Scrolle Shorts Feed"
                        st.rerun()
                    st.caption(f"👁️ {format_value(sv.get('views', 0))} views")
            st.divider()
    except Exception as e:
        st.error(f"Error loading shorts preview: {e}")

    # Main Feed (Videos & Posts) Section
    try:
        if search_query:
            cursor.execute(
                "SELECT * FROM videos WHERE video_type != 'short' AND (title LIKE ? OR uploader_name LIKE ?) ORDER BY created_at DESC",
                (f"%{search_query}%", f"%{search_query}%"),
            )
            videos = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                "SELECT * FROM posts WHERE (content LIKE ? OR uploader_name LIKE ?) ORDER BY created_at DESC",
                (f"%{search_query}%", f"%{search_query}%"),
            )
            posts = [dict(row) for row in cursor.fetchall()]
        else:
            cursor.execute("SELECT * FROM videos WHERE video_type != 'short' ORDER BY created_at DESC")
            videos = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
            posts = [dict(row) for row in cursor.fetchall()]

        all_feed = sorted(videos + posts, key=lambda x: x.get('created_at', ''), reverse=True)

        if not all_feed:
            st.info("No post or video feeds available right now. Upload something first!")
        else:
            for item in all_feed:
                st.markdown('<div class="feed-card">', unsafe_allow_html=True)
                show_verified_profile(
                    display_name=item.get("uploader_name", "Anonymous"),
                    profile_pic_path=item.get("uploader_pic"),
                    subtitle=item.get("created_at", ""),
                )
                
                # Title / Content Text
                if "title" in item and item["title"]:
                    st.markdown(f"### {item['title']}")
                if "content" in item and item["content"]:
                    st.write(item["content"])
                
                # Video / Image Media Rendering
                if "video_url" in item and item["video_url"] and os.path.exists(item["video_url"]):
                    st.video(item["video_url"])
                elif "image_url" in item and item["image_url"] and os.path.exists(item["image_url"]):
                    st.image(item["image_url"], use_column_width=True)
                
                # Render Comments
                if "id" in item:
                    render_comments_section(item["id"])
                    
                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading main feed: {e}")
    finally:
        conn.close()

# ---------------- Tab 2: Shorts Feed ----------------
elif tab == "📱 Scrolle Shorts Feed":
    st.title("📱 Scrolle Shorts Feed")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE video_type = 'short' ORDER BY created_at DESC")
    shorts = cursor.fetchall()
    conn.close()

    if not shorts:
        st.info("No shorts uploaded yet. Upload short vertical videos from Upload Center!")
    else:
        for s in shorts:
            st.markdown('<div class="feed-card">', unsafe_allow_html=True)
            show_verified_profile(s["uploader_name"], s["uploader_pic"], s["created_at"])
            st.subheader(s["title"])
            if os.path.exists(s["video_url"]):
                st.video(s["video_url"])
            st.caption(f"👁️ Views: {format_value(s['views'])}")
            render_comments_section(s["id"])
            st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Tab 3: Upload Center ----------------
elif tab == "📤 Upload Center":
    st.title("📤 Upload Content")
    
    upload_type = st.selectbox("Select Upload Type", ["Text / Image Post", "Video / Short Video"])
    
    if upload_type == "Text / Image Post":
        with st.form("post_upload_form"):
            content = st.text_area("What's on your mind?")
            image_file = st.file_uploader("Upload Image (Optional)", type=["jpg", "png", "jpeg"])
            submit = st.form_submit_button("Publish Post")
            
            if submit:
                img_path = None
                if image_file:
                    img_path = os.path.join(MEDIA_DIR, f"{random.randint(1000,9999)}_{image_file.name}")
                    with open(img_path, "wb") as f:
                        f.write(image_file.getbuffer())
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO posts (uploader_name, uploader_pic, content, image_url, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    st.session_state.user_info["username"],
                    st.session_state.user_info.get("profile_pic"),
                    content,
                    img_path,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()
                conn.close()
                st.success("Post published successfully!")

    elif upload_type == "Video / Short Video":
        with st.form("video_upload_form"):
            title = st.text_input("Video Title")
            v_type = st.selectbox("Video Category", ["regular", "short"])
            video_file = st.file_uploader("Upload MP4 Video", type=["mp4", "mov"])
            submit_v = st.form_submit_button("Upload Video")
            
            if submit_v:
                if video_file and title:
                    v_path = os.path.join(MEDIA_DIR, f"{random.randint(1000,9999)}_{video_file.name}")
                    with open(v_path, "wb") as f:
                        f.write(video_file.getbuffer())
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO videos (uploader_name, uploader_pic, title, video_type, video_url, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        st.session_state.user_info["username"],
                        st.session_state.user_info.get("profile_pic"),
                        title,
                        v_type,
                        v_path,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    conn.commit()
                    conn.close()
                    st.success("Video uploaded successfully!")
                else:
                    st.error("Please provide both a title and a video file.")

# ---------------- Tab 4: My Vault / Profile ----------------
elif tab == "👤 My Vault":
    st.title("👤 My Vault Profile")
    user = st.session_state.user_info
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if user.get("profile_pic") and os.path.exists(user["profile_pic"]):
            st.image(user["profile_pic"], width=150)
        else:
            st.markdown("# 👤")
            
        uploaded_pic = st.file_uploader("Update Profile Picture", type=["jpg", "png"])
        if uploaded_pic:
            p_path = os.path.join(MEDIA_DIR, f"profile_{user['id']}_{uploaded_pic.name}")
            with open(p_path, "wb") as f:
                f.write(uploaded_pic.getbuffer())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE global_sovereign_vault SET profile_pic = ? WHERE id = ?", (p_path, user["id"]))
            conn.commit()
            conn.close()
            
            st.session_state.user_info["profile_pic"] = p_path
            st.success("Profile picture updated!")
            st.rerun()

    with col2:
        st.markdown(f"### Vault ID: `{user['vault_id']}`")
        st.markdown(f"**Username:** {user['username']}")
        st.markdown(f"**Gmail:** {user['gmail_address']}")
        st.markdown(f"**Phone:** {user['phone_number']}")
        st.markdown(f"**Member Since:** {user['created_at']}")

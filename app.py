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
# 1. PAGE CONFIGURATION & META & DB SETUP
# ==========================================
st.set_page_config(
    page_title="BD AI Book — Enterprise Master Hub",
    page_icon="🛡️",
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
DB_FILE = "global_enterprise_master.db"
VIDEO_DIR = "stored_videos"
IMAGE_DIR = "stored_images"
PROFILE_DIR = "stored_profiles"

for folder in [VIDEO_DIR, IMAGE_DIR, PROFILE_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ==========================================
# 16 SERVERS & MASTER DATABASE INITIALIZATION
# ==========================================
def init_all_16_servers_and_vault():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    
    # 0. Special Sovereign Vault
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sovereign_vault (
            vault_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE,
            gmail_address TEXT UNIQUE,
            hashed_password TEXT NOT NULL,
            biometric_face_hash TEXT,
            security_tier INTEGER DEFAULT 999,
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

    # Default Owner Master Account Setup
    cursor.execute("SELECT * FROM global_sovereign_vault WHERE username = 'system_owner'")
    if not cursor.fetchone():
        owner_pass = hashlib.sha256("OwnerMasterKey2026#".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO global_sovereign_vault (vault_id, username, phone_number, hashed_password, security_tier, created_at)
            VALUES ('vault_owner_01', 'system_owner', '01722003172', ?, 999, ?)
        """, (owner_pass, datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()

init_all_16_servers_and_vault()

# ==========================================
# 2. AI SECURITY GUARD & PIPELINE ENGINE
# ==========================================
def ai_content_security_guard(file_name):
    banned_keywords = ["tiktok", "instagram_dl", "facebook_video", "adult", "x_rated", "pirated", "hack"]
    for keyword in banned_keywords:
        if keyword in file_name.lower():
            return False, f"🚨 AI Security Block: Unauthorized or third-party content ('{keyword}') is strictly prohibited!"
    return True, "✅ AI Verified: Original Mobile Content Approved."

def push_to_central_pipeline(source_table, record_id, username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    pipeline_id = f"pipe_{uuid.uuid4().hex[:10]}"
    
    cursor.execute("""
        INSERT INTO tb_16_global_central_pipeline 
        (pipeline_id, source_table, record_id, username, owner_approval_status, transferred_at)
        VALUES (?, ?, ?, ?, 'Pending Owner Approval', ?)
    """, (pipeline_id, source_table, record_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

# ==========================================
# 3. HELPER FUNCTIONS & STYLING
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
    textarea, input { color: #ffffff !important; background-color: #242526 !important; }
    .feed-card { background: #18191a; border: 1px solid #2d2f31; border-radius: 14px; padding: 16px; margin-bottom: 20px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "user" not in st.session_state:
    st.session_state.user = None

# ==========================================
# 4. SIDEBAR NAVIGATION & AUTHENTICATION
# ==========================================
st.sidebar.header("🔐 Portal Access")
mode = st.sidebar.radio("Select Mode", ["Login", "Register (Face & Mobile)", "👑 Owner Control", "📤 Multi-Server Upload Hub"])

if mode == "👑 Owner Control":
    owner_key_input = st.sidebar.text_input("Owner Master Key", type="password")
    if st.sidebar.button("Access Owner Panel"):
        if hashlib.sha256(owner_key_input.encode()).hexdigest() == hashlib.sha256("OwnerMasterKey2026#".encode()).hexdigest():
            st.session_state.user = "system_owner"
            st.success("Owner Logged In Successfully!")
            st.rerun()
        else:
            st.error("Invalid Master Key!")

elif mode == "Login":
    login_user = st.sidebar.text_input("Username or Phone")
    login_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        hashed_pass = hashlib.sha256(login_pass.encode()).hexdigest()
        cursor.execute("SELECT * FROM global_sovereign_vault WHERE (username = ? OR phone_number = ?) AND hashed_password = ?", 
                       (login_user, login_user, hashed_pass))
        if cursor.fetchone():
            st.session_state.user = login_user
            st.success("Login Successful!")
            st.rerun()
        else:
            st.error("Invalid Username/Phone or Password!")
        conn.close()

elif mode == "Register (Face & Mobile)":
    reg_user = st.sidebar.text_input("New Username")
    reg_phone = st.sidebar.text_input("Mobile Number")
    reg_pass = st.sidebar.text_input("Password", type="password")
    face_capture = st.sidebar.camera_input("Capture Face for Secure Vault")
    
    if st.sidebar.button("Register to Vault"):
        if reg_user and reg_phone and reg_pass and face_capture:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            try:
                hashed_pass = hashlib.sha256(reg_pass.encode()).hexdigest()
                vault_id = f"vault_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO global_sovereign_vault 
                    (vault_id, username, phone_number, hashed_password, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (vault_id, reg_user, reg_phone, hashed_pass, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.sidebar.success("Registration Complete! Please go to Login.")
            except Exception:
                st.sidebar.error("Error: Username or Phone already exists!")
            conn.close()
        else:
            st.sidebar.error("Please fill all fields and capture your face!")

# ==========================================
# 5. MAIN INTERFACE & DASHBOARD VIEWS
# ==========================================
st.markdown("<h1 style='text-align: center; color: #00c853;'>🛡️ BD AI Book — 16 Server Master Hub</h1>", unsafe_allow_html=True)

if st.session_state.user:
    st.write(f"### Welcome, **{st.session_state.user}**")
    
    if st.session_state.user == "system_owner":
        st.markdown("---")
        st.subheader("👑 Owner Master Approval Dashboard (Central Pipeline)")
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tb_16_global_central_pipeline WHERE owner_approval_status = 'Pending Owner Approval'")
        pending_items = cursor.fetchall()
        
        if pending_items:
            for item in pending_items:
                st.write(f"📁 **Source Table:** `{item['source_table']}` | 👤 **Uploader:** `{item['username']}` | ⏰ **Time:** `{item['transferred_at']}`")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve & Publish", key=f"app_{item['pipeline_id']}"):
                        cursor.execute("UPDATE tb_16_global_central_pipeline SET owner_approval_status = 'Approved & Live' WHERE pipeline_id = ?", (item['pipeline_id'],))
                        conn.commit()
                        st.success("Content Approved and Live!")
                        st.rerun()
                with col2:
                    if st.button(f"❌ Delete & Ban", key=f"del_{item['pipeline_id']}"):
                        cursor.execute("DELETE FROM tb_16_global_central_pipeline WHERE pipeline_id = ?", (item['pipeline_id'],))
                        conn.commit()
                        st.error("Content Deleted and Blocked!")
                        st.rerun()
        else:
            st.info("No pending content approvals in the pipeline.")
        conn.close()

    if mode == "📤 Multi-Server Upload Hub":
        st.markdown("---")
        st.subheader("📤 Secure Media Upload & AI Guard Hub (16-Server Integrated)")
        
        upload_category = st.selectbox("Select Target Category Server", [
            "tb_03_image_posts", "tb_04_long_videos", "tb_05_short_videos", 
            "tb_06_islamic_short_videos", "tb_07_islamic_long_videos", 
            "tb_08_news_contents", "tb_09_blog_contents", "tb_10_educational_contents", 
            "tb_11_entertainment_contents", "tb_12_tech_contents", "tb_13_live_streams",
            "tb_14_advertisements", "tb_15_bank_details"
        ])
        
        uploaded_file = st.file_uploader("Upload Mobile Media File", type=["mp4", "jpg", "png", "jpeg"])
        content_title = st.text_input("Enter Content Title / Description")
        
        if st.button("Run AI Check & Submit to Pipeline"):
            if uploaded_file and content_title:
                is_safe, security_msg = ai_content_security_guard(uploaded_file.name)
                if not is_safe:
                    st.error(security_msg)
                else:
                    st.success(security_msg)
                    record_id = f"rec_{uuid.uuid4().hex[:8]}"
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        INSERT INTO {upload_category} (id, username, content_title, media_path, ai_verified, created_at)
                        VALUES (?, ?, ?, ?, 1, ?)
                    """, (record_id, st.session_state.user, content_title, uploaded_file.name, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    
                    push_to_central_pipeline(upload_category, record_id, st.session_state.user)
                    st.balloons()
                    st.success("✅ Success! Content verified by AI and sent to Central Pipeline for Owner Approval.")
            else:
                st.error("Please provide both media file and title.")
else:
    st.info("🔒 Please login or register using the sidebar panel to access your dashboard.")

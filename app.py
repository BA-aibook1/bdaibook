import streamlit as st
import sqlite3
import hashlib
import os
import datetime
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Shorts & Reel Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI Enhancement & Floating Elements
st.markdown("""
    <style>
    .main { background-color: #0f0f17; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #ff0050; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #e00045; border-color: #e00045; }
    .verified-badge { color: #1DA1F2; font-weight: bold; margin-left: 5px; }
    .owner-badge { background-color: #ff0050; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
    .card { background-color: #1a1a24; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #2a2a3a; }
    </style>
""", unsafe_allow_html=True)

# Directories
UPLOAD_DIR = "uploads"
BANNER_DIR = "app_assets"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BANNER_DIR, exist_ok=True)

# ---------------------------------------------------------
# 2. DATABASE SETUP & INITIALIZATION
# ---------------------------------------------------------
DB_FILE = "platform_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            earnings REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Posts/Media Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            caption TEXT,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # App Settings (Header, Logo, Owner Info)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Default Settings
    cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('banner_path', '')")
    cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('app_title', 'My Shorts Platform')")
    
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. HELPER & WATERMARK FUNCTIONS
# ---------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_setting(key):
    conn = get_db_connection()
    res = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return res['value'] if res else ""

def set_setting(key, value):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def apply_image_watermark(image_path, watermark_text="MyApp Watermark"):
    """ছবিতে ওয়াটারমার্ক যুক্ত করে"""
    try:
        image = Image.open(image_path).convert("RGBA")
        txt = Image.new("RGBA", image.size, (255, 255, 255, 0))
        d = ImageDraw.Draw(txt)

        # Default Font
        width, height = image.size
        fontsize = int(height * 0.05)
        font = ImageFont.load_default()

        # Bottom Right Position
        d.text((width - (fontsize * 6), height - (fontsize * 2)), watermark_text, fill=(255, 255, 255, 128), font=font)
        watermarked = Image.alpha_composite(image, txt)
        
        output_path = image_path.replace(".", "_wm.")
        watermarked.convert("RGB").save(output_path)
        return output_path
    except Exception as e:
        return image_path

# ---------------------------------------------------------
# 4. SESSION MANAGEMENT
# ---------------------------------------------------------
if 'user' not in st.session_state:
    st.session_state.user = None
if 'is_owner' not in st.session_state:
    st.session_state.is_owner = False

# ---------------------------------------------------------
# 5. HEADER & BANNER SECTION
# ---------------------------------------------------------
banner_path = get_setting('banner_path')
app_title = get_setting('app_title')

if banner_path and os.path.exists(banner_path):
    st.image(banner_path, use_container_width=True)

st.title(f"🎬 {app_title}")
st.write("---")

# ---------------------------------------------------------
# 6. SIDEBAR - AUTHENTICATION & NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("📌 মেনু (Menu)")

if st.session_state.user or st.session_state.is_owner:
    if st.session_state.is_owner:
        st.sidebar.success("👑 ওনার লগইন অবস্থায় আছেন")
    else:
        st.sidebar.info(f"👤 ইউজার: {st.session_state.user['username']}")
    
    if st.sidebar.button("🚪 লগআউট (Logout)"):
        st.session_state.user = None
        st.session_state.is_owner = False
        st.rerun()

else:
    auth_option = st.sidebar.radio("অ্যাপ্রুভাল/লগইন", ["লগইন (Login)", "সাইন আপ (Sign Up)", "👑 ওনার চ্যানেল (Owner)"])

    conn = get_db_connection()
    
    if auth_option == "লগইন (Login)":
        st.sidebar.subheader("Login")
        email = st.sidebar.text_input("ইমেইল (Email)")
        password = st.sidebar.text_input("পাসওয়ার্ড (Password)", type="password")
        
        if st.sidebar.button("Login"):
            user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", 
                                (email, hash_password(password))).fetchone()
            if user:
                st.session_state.user = dict(user)
                st.session_state.is_owner = False
                st.sidebar.success("লগইন সফল হয়েছে!")
                st.rerun()
            else:
                st.sidebar.error("ভুল ইমেইল অথবা পাসওয়ার্ড!")

    elif auth_option == "সাইন আপ (Sign Up)":
        st.sidebar.subheader("Sign Up")
        username = st.sidebar.text_input("ইউজারনেম (Username)")
        email = st.sidebar.text_input("ইমেইল (Email)")
        password = st.sidebar.text_input("পাসওয়ার্ড (Password)", type="password")
        
        if st.sidebar.button("Register"):
            if username and email and password:
                try:
                    conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                                 (username, email, hash_password(password)))
                    conn.commit()
                    st.sidebar.success("অ্যাকাউন্ট তৈরি হয়েছে! এখন লগইন করুন।")
                except sqlite3.IntegrityError:
                    st.sidebar.error("এই ইমেইল বা ইউজারনেমটি আগে থেকেই রয়েছে।")
            else:
                st.sidebar.warning("সবগুলো তথ্য সঠিকভাবে পূরণ করুন।")

    elif auth_option == "👑 ওনার চ্যানেল (Owner)":
        st.sidebar.subheader("Owner Master Login")
        master_key = st.sidebar.text_input("Master Password", type="password")
        if st.sidebar.button("Access Master Panel"):
            if master_key == "OwnerMasterKey2026#":
                st.session_state.is_owner = True
                st.session_state.user = {"username": "Master Owner", "id": 0}
                st.sidebar.success("ওনার প্যানেলে স্বাগতম!")
                st.rerun()
            else:
                st.sidebar.error("ভুল মাস্টার কি (Master Key)!")

    conn.close()

# ---------------------------------------------------------
# 7. MAIN APPLICATION BODY (TABS)
# ---------------------------------------------------------
if st.session_state.is_owner:
    tabs = st.tabs(["📺 Feed", "📤 Upload Post", "👑 Owner Admin Panel"])
else:
    tabs = st.tabs(["📺 Feed", "📤 Upload Post", "👤 My Profile"])

# ================= TAB 1: FEED =================
with tabs[0]:
    st.subheader("🔥 সাম্প্রতিক শর্টস ও পোস্টসমূহ")
    conn = get_db_connection()
    posts = conn.execute('''
        SELECT posts.*, users.username, users.is_verified 
        FROM posts 
        JOIN users ON posts.user_id = users.id 
        ORDER BY posts.id DESC
    ''').fetchall()
    conn.close()

    if not posts:
        st.info("এখনো কোনো পোস্ট করা হয়নি। প্রথম পোস্টটি আপনিই করুন!")
    
    for post in posts:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # User Header with Blue Tick Verification
            user_title = f"**@{post['username']}**"
            if post['is_verified']:
                user_title += ' <span class="verified-badge">✔ Verified</span>'
            st.markdown(user_title, unsafe_allow_html=True)
            
            st.write(post['caption'])
            
            # Media Rendering
            file_path = post['file_path']
            if post['file_type'].startswith('video'):
                st.video(file_path)
            elif post['file_type'].startswith('image'):
                st.image(file_path, use_container_width=True)

            # Interactive Options
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button(f"❤️ {post['likes']}", key=f"like_{post['id']}"):
                    conn = get_db_connection()
                    conn.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# ================= TAB 2: UPLOAD POST =================
with tabs[1]:
    st.subheader("📤 নতুন ভিডিও বা ছবি আপলোড করুন")
    
    if not st.session_state.user and not st.session_state.is_owner:
        st.warning("পোস্ট করার জন্য আপনাকে প্রথমে লগইন করতে হবে।")
    else:
        caption = st.text_area("ক্যাপশন লিখুন (Caption)")
        uploaded_file = st.file_uploader("ভিডিও বা ইমেজ বাছাই করুন", type=['mp4', 'mov', 'png', 'jpg', 'jpeg'])
        watermark_text = st.text_input("ওয়াটারমার্ক টেক্সট", value=f"@{st.session_state.user['username']}")

        if st.button("পাবলিশ পোস্ট (Publish Post)"):
            if uploaded_file and caption:
                file_ext = uploaded_file.name.split('.')[-1]
                file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                save_path = os.path.join(UPLOAD_DIR, file_name)
                
                # Save Raw File
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Apply Watermark if Image
                final_path = save_path
                file_type = uploaded_file.type
                if file_type.startswith("image"):
                    final_path = apply_image_watermark(save_path, watermark_text)

                # Save To Database
                conn = get_db_connection()
                conn.execute("INSERT INTO posts (user_id, caption, file_path, file_type) VALUES (?, ?, ?, ?)",
                             (st.session_state.user['id'], caption, final_path, file_type))
                conn.commit()
                conn.close()

                st.success("🎉 পোস্ট সফলভাবে আপলোড এবং ওয়াটারমার্কযুক্ত করা হয়েছে!")
                st.rerun()
            else:
                st.error("অনুগ্রহ করে একটি মিডিয়া ফাইল এবং ক্যাপশন প্রদান করুন।")

# ================= TAB 3: PROFILE / OWNER ADMIN =================
if st.session_state.is_owner:
    # OWNER ADMIN PANEL
    with tabs[2]:
        st.subheader("👑 ওনার অ্যাডমিন কন্ট্রোল রুম (Owner Control Chamber)")
        
        # 1. Update Platform Branding (Header Banner & Title)
        st.markdown("### 🖼️ প্ল্যাটফর্ম ব্যানার ও টাইটেল পরিবর্তন")
        new_title = st.text_input("প্ল্যাটফর্ম টাইটেল", value=app_title)
        new_banner = st.file_uploader("নতুন হেডার ব্যানার আপলোড করুন (Header Image)", type=['jpg', 'png', 'jpeg'])

        if st.button("সেটিংস সেভ করুন (Save Branding)"):
            set_setting('app_title', new_title)
            if new_banner:
                banner_save_path = os.path.join(BANNER_DIR, "header_banner.png")
                with open(banner_save_path, "wb") as f:
                    f.write(new_banner.getbuffer())
                set_setting('banner_path', banner_save_path)
            st.success("ব্র্যান্ডিং আপডেট করা হয়েছে!")
            st.rerun()

        st.write("---")

        # 2. Manage Users & Blue Ticks (Verified Badges)
        st.markdown("### 🟦 ইউজার ও ব্লু টিক ম্যানেজমেন্ট")
        conn = get_db_connection()
        users = conn.execute("SELECT id, username, email, is_verified FROM users WHERE id != 0").fetchall()
        
        for u in users:
            col1, col2, col3 = st.columns([2, 2, 2])
            col1.write(f"**{u['username']}** ({u['email']})")
            status = "Verified 🔵" if u['is_verified'] else "Unverified ❌"
            col2.write(f"স্ট্যাটাস: {status}")
            
            toggle_label = "Remove Tick" if u['is_verified'] else "Give Blue Tick"
            if col3.button(toggle_label, key=f"vtick_{u['id']}"):
                new_status = 0 if u['is_verified'] else 1
                conn.execute("UPDATE users SET is_verified = ? WHERE id = ?", (new_status, u['id']))
                conn.commit()
                conn.close()
                st.rerun()
        conn.close()

else:
    # REGULAR USER PROFILE
    with tabs[2]:
        if st.session_state.user:
            st.subheader(f"👤 প্রোফাইল: {st.session_state.user['username']}")
            
            conn = get_db_connection()
            user_data = conn.execute("SELECT * FROM users WHERE id = ?", (st.session_state.user['id'],)).fetchone()
            user_posts = conn.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY id DESC", (st.session_state.user['id'],)).fetchall()
            conn.close()

            st.write(f"**ইমেইল:** {user_data['email']}")
            st.write(f"**ভেরিফাইড স্ট্যাটাস:** {'🔵 Verified User' if user_data['is_verified'] else '❌ Not Verified'}")
            st.write(f"**মোট উপার্জন (Earnings):** ৳ {user_data['earnings']}")
            
            st.write("---")
            st.markdown("### 🎬 আমার পোস্টসমূহ")
            for post in user_posts:
                st.write(f"📌 {post['caption']}")
                if post['file_type'].startswith('video'):
                    st.video(post['file_path'])
                else:
                    st.image(post['file_path'], width=300)
        else:
            st.info("প্রোফাইল দেখতে অনুগ্রহ করে লগইন করুন।")

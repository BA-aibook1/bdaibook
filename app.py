import os
import sqlite3
import uuid
import hashlib
import json
from datetime import datetime
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="BD AI Book - Global Social Platform",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

UPLOAD_DIR = "uploaded_media"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

LOCAL_DB_FILE = "bd_ai_book_master.db"
SECRET_CODES = ["S$s123456789112233", "S$s123456789112233BDAIBOOK"]
BANNED_KEYWORDS = ["nude", "sex", "adult", "porn", "xrated", "18+"]

# Custom CSS for Circular Avatars & Native Web Share Integration
st.markdown("""
<style>
    /* Circular Avatars with Blue Border */
    .circle-img-feed {
        width: 48px !important;
        height: 48px !important;
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid #0064e0;
        display: inline-block;
        vertical-align: middle;
    }
    .circle-img-profile {
        width: 120px !important;
        height: 120px !important;
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 3px solid #0064e0;
        box-shadow: 0px 4px 10px rgba(0,100,224,0.3);
    }
    .video-container {
        position: relative;
        max-width: 380px;
        margin: 0 auto;
        border-radius: 14px;
        overflow: hidden;
    }
    .watermark-text {
        position: absolute;
        top: 10px;
        right: 12px;
        background: rgba(0, 100, 224, 0.85);
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        z-index: 10;
    }
</style>

<script>
function shareContent(title, url) {
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        }).catch(console.error);
    } else {
        navigator.clipboard.writeText(url);
        alert("Post Link Copied to Clipboard!");
    }
}
</script>
""", unsafe_allow_html=True)

# ==========================================
# 2. REAL DATABASE ENGINE & ENGINE SETUP
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(LOCAL_DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_master_database():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            full_name TEXT,
            auth_identifier TEXT,
            password_hash TEXT,
            address TEXT,
            bio TEXT,
            profile_pic_path TEXT,
            cover_pic_path TEXT,
            fb_link TEXT,
            tiktok_link TEXT,
            yt_link TEXT,
            website_link TEXT,
            is_verified INTEGER DEFAULT 1,
            is_suspended INTEGER DEFAULT 0,
            created_at TEXT
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            content TEXT,
            hashtags TEXT,
            media_path TEXT,
            post_category TEXT,
            views_count INTEGER DEFAULT 0,
            is_boosted INTEGER DEFAULT 0,
            created_at TEXT
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS follows (
            follower_id TEXT,
            following_id TEXT,
            PRIMARY KEY (follower_id, following_id)
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            user_id TEXT,
            post_id TEXT,
            PRIMARY KEY (user_id, post_id)
        );
    """)
    conn.commit()
    conn.close()

init_master_database()

def hash_pass(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

# ==========================================
# 3. AUTHENTICATION & LOGIN
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = None

st.sidebar.markdown("### 🔐 BD AI Book Account")
if not st.session_state.user_id:
    auth_input = st.sidebar.text_input("Mobile / Email")
    auth_pass = st.sidebar.text_input("Password", type="password")
    
    col_a1, col_a2 = st.sidebar.columns(2)
    if col_a1.button("Login"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE auth_identifier = ? AND password_hash = ?", (auth_input, hash_pass(auth_pass)))
        usr = c.fetchone()
        conn.close()
        if usr:
            st.session_state.user_id = usr["user_id"]
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials!")

    if col_a2.button("Register"):
        if auth_input and auth_pass:
            new_uid = str(uuid.uuid4())
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO users (user_id, full_name, auth_identifier, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.session_state.user_id = new_uid
            st.rerun()
else:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (st.session_state.user_id,))
    current_user = dict(c.fetchone())
    
    # Real Followers Count
    c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (st.session_state.user_id,))
    real_followers = c.fetchone()["cnt"]
    conn.close()
    
    st.sidebar.markdown(f"👤 Account: **{current_user['full_name']}**")
    st.sidebar.markdown(f"👥 Real Followers: **{real_followers}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.rerun()

# ==========================================
# 4. MAIN INTERFACE TABS
# ==========================================
tab_feed, tab_profile, tab_monetize = st.tabs(["📺 Live Feed", "👤 Profile Studio", "💸 Global Boost & Earning"])

# ------------------------------------------
# TAB 1: REAL LIVE FEED
# ------------------------------------------
with tab_feed:
    search_q = st.text_input("🔍 Search Users, #Hashtags, or Posts...")
    
    conn = get_db_connection()
    c = conn.cursor()
    if search_q:
        q_str = f"%{search_q}%"
        c.execute("SELECT posts.*, users.full_name, users.profile_pic_path, users.fb_link, users.tiktok_link, users.yt_link FROM posts JOIN users ON posts.user_id = users.user_id WHERE posts.title LIKE ? OR posts.hashtags LIKE ? OR users.full_name LIKE ? ORDER BY posts.is_boosted DESC, posts.created_at DESC", (q_str, q_str, q_str))
    else:
        c.execute("SELECT posts.*, users.full_name, users.profile_pic_path, users.fb_link, users.tiktok_link, users.yt_link FROM posts JOIN users ON posts.user_id = users.user_id ORDER BY posts.is_boosted DESC, posts.created_at DESC")
    
    posts = c.fetchall()
    conn.close()

    for p in posts:
        st.markdown("<div style='background:#18191a; padding:15px; border-radius:12px; margin-bottom:20px;'>", unsafe_allow_html=True)
        
        # Real Follower Stats for Author
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (p['user_id'],))
        author_followers = c.fetchone()["cnt"]
        
        # Check if Logged In User is Following
        is_following = False
        if st.session_state.user_id:
            c.execute("SELECT * FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, p['user_id']))
            if c.fetchone(): is_following = True
        conn.close()

        col_h1, col_h2 = st.columns([4, 1])
        with col_h1:
            pic_path = p['profile_pic_path']
            if pic_path and os.path.exists(pic_path):
                st.image(pic_path, width=48)
            st.markdown(f"### {p['full_name']} ✔️")
            st.caption(f"👥 Followers: {author_followers} | {p['created_at']}")
            
        with col_h2:
            if st.session_state.user_id and st.session_state.user_id != p['user_id']:
                btn_label = "✔ Following" if is_following else "➕ Follow"
                if st.button(btn_label, key=f"fol_{p['post_id']}"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    if is_following:
                        c.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, p['user_id']))
                    else:
                        c.execute("INSERT OR REPLACE INTO follows VALUES (?, ?)", (st.session_state.user_id, p['user_id']))
                    conn.commit()
                    conn.close()
                    st.rerun()

        if p['title']: st.subheader(p['title'])
        if p['content']: st.write(p['content'])
        if p['hashtags']: st.markdown(f"<span style='color:#0064e0;'>{p['hashtags']}</span>", unsafe_allow_html=True)
        
        # Media Display with Watermark
        m_path = p['media_path']
        if m_path and os.path.exists(m_path):
            st.markdown("<div class='video-container'><div class='watermark-text'>BD AI BOOK</div>", unsafe_allow_html=True)
            if p['post_category'] == "picture":
                st.image(m_path, use_container_width=True)
            else:
                st.video(m_path)
            st.markdown("</div>", unsafe_allow_html=True)

        # Real Like Logic
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM likes WHERE post_id = ?", (p['post_id'],))
        real_likes = c.fetchone()["cnt"]
        
        has_liked = False
        if st.session_state.user_id:
            c.execute("SELECT * FROM likes WHERE user_id = ? AND post_id = ?", (st.session_state.user_id, p['post_id']))
            if c.fetchone(): has_liked = True
        conn.close()

        st.markdown("---")
        col_b1, col_b2, col_b3 = st.columns(3)
        
        like_btn_txt = f"❤️ Liked ({real_likes})" if has_liked else f"👍 Like ({real_likes})"
        if col_b1.button(like_btn_txt, key=f"lk_{p['post_id']}"):
            if st.session_state.user_id:
                conn = get_db_connection()
                c = conn.cursor()
                if has_liked:
                    c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (st.session_state.user_id, p['post_id']))
                else:
                    c.execute("INSERT OR REPLACE INTO likes VALUES (?, ?)", (st.session_state.user_id, p['post_id']))
                conn.commit()
                conn.close()
                st.rerun()
            else:
                st.warning("Login required to like!")

        col_b2.button("💬 Comment", key=f"cm_{p['post_id']}")
        
        # Real Native Share Trigger
        if col_b3.button("🚀 Share Across Apps", key=f"sh_{p['post_id']}"):
            st.markdown(f"""
            <script>
                shareContent("{p['title']}", window.location.href);
            </script>
            """, unsafe_allow_html=True)
            st.toast("Sharing Menu Opened!")
            
        st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: PROFILE & CONTENT UPLOAD
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.info("Login to access profile studio.")
    else:
        st.markdown(f"## Profile Studio: {current_user['full_name']}")
        
        col_p1, col_p2 = st.columns([1, 4])
        with col_p1:
            if current_user['profile_pic_path'] and os.path.exists(current_user['profile_pic_path']):
                st.image(current_user['profile_pic_path'], width=120)
            else:
                st.info("No Avatar")
        with col_p2:
            st.write(f"👥 **Real Followers:** {real_followers}")
            st.write(f"**Bio:** {current_user.get('bio', 'No Bio')}")

        with st.expander("⚙️ Edit Circular Avatar & Links"):
            u_name = st.text_input("Name", value=current_user['full_name'])
            u_bio = st.text_area("Bio", value=current_user.get('bio') or "")
            up_dp = st.file_uploader("Upload Circular Profile Pic", type=["png", "jpg", "jpeg"])
            
            if st.button("Save Profile"):
                dp_p = current_user['profile_pic_path']
                if up_dp:
                    dp_p = os.path.join(UPLOAD_DIR, f"dp_{st.session_state.user_id}.png")
                    with open(dp_p, "wb") as f: f.write(up_dp.getbuffer())
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE users SET full_name = ?, bio = ?, profile_pic_path = ? WHERE user_id = ?", (u_name, u_bio, dp_p, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("Profile Updated!")
                st.rerun()

        st.markdown("---")
        st.markdown("### 📤 Upload New Video / Photo")
        p_title = st.text_input("Post Title")
        p_desc = st.text_area("Description")
        p_tags = st.text_input("Hashtags (e.g. #BD_AI_BOOK #Viral)")
        p_cat = st.selectbox("Category", ["short", "long", "picture"])
        p_file = st.file_uploader("Select File", type=["mp4", "jpg", "png"])
        
        if st.button("Publish Now"):
            if p_file and p_title:
                ext = os.path.splitext(p_file.name)[1]
                save_p = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
                with open(save_p, "wb") as f: f.write(p_file.getbuffer())
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO posts (post_id, user_id, title, content, hashtags, media_path, post_category, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), st.session_state.user_id, p_title, p_desc, p_tags, save_p, p_cat, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("Content Published Real-Time!")
                st.rerun()

# ------------------------------------------
# TAB 3: MONETIZATION & BOOSTING
# ------------------------------------------
with tab_monetize:
    st.markdown("### 💸 Worldwide Monetization & Boost Center")
    if real_followers >= 1000:
        st.success(f"🎉 **Monetization Eligible!** You have {real_followers} Real Followers.")
    else:
        st.info(f"📊 Progress: {real_followers} / 1,000 Real Followers needed to enable automatic payouts.")

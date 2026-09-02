import os
import sqlite3
import uuid
import hashlib
import random
from datetime import datetime, timedelta
import streamlit as st

# ==========================================
# 1. PAGE SETUP & STORAGE DIRECTORY
# ==========================================
st.set_page_config(
    page_title="BD AI Book",
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

BANK_DETAILS = """
🏦 **International Payment Wire Gateway (Boost & Payout)**
- **Account Name:** Md Sohel Rana
- **Recipient Address:** Bangladesh, Barabari, SHIBRAM BARABARI SADAR LALMONIRHAT, 5500
- **IBAN:** GB89CLRB04281239130579
- **BIC/SWIFT code:** CLRBGB22XXX
- **Account number:** 39130579
- **Bank Name:** Clear Bank (133 Houndsditch, LONDON, EC3A 7BX)
- **Account type:** Checking (Current)
"""

# ==========================================
# 2. MASTER DATABASE ENGINE & MIGRATION
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(LOCAL_DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_master_database():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS master_app_table (
            record_id TEXT PRIMARY KEY,
            data_type TEXT NOT NULL,
            user_id TEXT,
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
            followers_count INTEGER DEFAULT 0,
            is_verified INTEGER DEFAULT 1,
            violation_count INTEGER DEFAULT 0,
            is_suspended INTEGER DEFAULT 0,
            suspended_until TEXT,
            title TEXT,
            content TEXT,
            tags TEXT,
            media_path TEXT,
            post_category TEXT,
            likes_count INTEGER DEFAULT 0,
            views_count INTEGER DEFAULT 0,
            is_boosted INTEGER DEFAULT 0,
            country TEXT DEFAULT 'Global',
            is_owner_post INTEGER DEFAULT 0,
            created_at TEXT
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS boost_requests (
            boost_id TEXT PRIMARY KEY,
            user_id TEXT,
            post_id TEXT,
            plan TEXT,
            amount TEXT,
            trx_info TEXT,
            status TEXT DEFAULT 'Pending',
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    
    conn.commit()
    conn.close()

init_master_database()

# ==========================================
# 3. HELPER & CUSTOM CSS (CIRCULAR AVATARS & WATERMARK)
# ==========================================
def hash_pass(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

def get_meta_blue_badge():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" style="vertical-align: middle; margin-left: 4px;"><path fill="#0064e0" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.66.425-1.55-.008-3.25-1.196-4.438-1.187-1.188-2.887-1.62-4.437-1.196C13.95 1.875 12.58 1 11.5 1s-2.45.875-3.16 2.148c-1.55-.425-3.25.008-4.438 1.196-1.188 1.187-1.62 2.887-1.196 4.437C1.875 9.55 1 10.92 1 12s.875 2.45 2.148 3.16c-.425 1.55.008 3.25 1.196 4.438 1.187 1.188 2.887 1.62 4.437 1.196C9.55 22.125 10.92 23 12 23s2.45-.875 3.16-2.148c1.55.425-.008 4.438-1.196 1.188-1.187 1.62-2.887 1.196-4.437 1.273-.71 2.148-2.08 2.148-3.66z"/><path fill="#ffffff" d="M9.8 17.3l-4.2-4.2 1.4-1.4 2.8 2.8 7.4-7.4 1.4 1.4z"/></svg>"""

st.markdown("""
<style>
    /* Circular Avatars Styling */
    img {
        border-radius: 12px;
    }
    .stImage > img {
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid #0064e0 !important;
    }
    .video-watermark-wrapper {
        position: relative;
    }
    .video-watermark-badge {
        position: absolute;
        top: 12px;
        right: 15px;
        background: rgba(0, 100, 224, 0.75);
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        z-index: 99;
        pointer-events: none;
    }
    .tiktok-container {
        max-width: 360px;
        margin: 0 auto;
        border-radius: 14px;
        overflow: hidden;
    }
</style>

<script>
function shareContent(title, url) {
    if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(console.error);
    } else {
        navigator.clipboard.writeText(url);
        alert("Post Link Copied!");
    }
}
</script>
""", unsafe_allow_html=True)

# Session Setup
if "user_id" not in st.session_state: st.session_state.user_id = None
if "otp_code" not in st.session_state: st.session_state.otp_code = None
if "is_owner_session" not in st.session_state: st.session_state.is_owner_session = False

# Render Logo Header
conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT value FROM site_settings WHERE key = 'logo_path'")
logo_row = c.fetchone()
site_logo_path = logo_row["value"] if logo_row else None
conn.close()

if site_logo_path and os.path.exists(site_logo_path):
    col_l1, col_l2, col_l3 = st.columns([2, 1, 2])
    with col_l2: st.image(site_logo_path, width=120)

st.markdown("<h1 style='text-align: center; color:#0064e0;'>BD AI Book</h1>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Next-Gen Global Social & Media Platform</p>", unsafe_allow_html=True)

# ==========================================
# 4. AUTHENTICATION & LOGIN
# ==========================================
real_followers = 0
current_user = {}

st.sidebar.markdown("### 🔐 User Login")
if not st.session_state.user_id:
    auth_input = st.sidebar.text_input("Gmail or Mobile")
    auth_pass = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Send OTP"):
        if auth_input and auth_pass:
            st.session_state.otp_code = str(random.randint(100000, 999999))
            st.sidebar.info(f"📩 OTP Code: **{st.session_state.otp_code}**")
            
    if st.session_state.otp_code:
        user_otp = st.sidebar.text_input("Enter OTP Code")
        if st.sidebar.button("Verify & Login"):
            if user_otp == st.session_state.otp_code:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND auth_identifier = ?", (auth_input,))
                usr = c.fetchone()
                if usr:
                    st.session_state.user_id = usr["user_id"]
                    st.sidebar.success("Logged In!")
                    st.rerun()
                else:
                    new_uid = str(uuid.uuid4())
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("""
                        INSERT INTO master_app_table (record_id, data_type, user_id, full_name, auth_identifier, password_hash, is_verified, created_at)
                        VALUES (?, 'user', ?, ?, ?, ?, 1, ?)
                    """, (new_uid, new_uid, f"User_{new_uid[:4]}", auth_input, hash_pass(auth_pass), now))
                    conn.commit()
                    st.session_state.user_id = new_uid
                    st.sidebar.success("Registered & Logged In!")
                    st.rerun()
                conn.close()
else:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (st.session_state.user_id,))
    raw_user = c.fetchone()
    
    # Real Followers Calculation
    c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (st.session_state.user_id,))
    f_res = c.fetchone()
    real_followers = f_res["cnt"] if f_res else 0
    conn.close()
    
    current_user = dict(raw_user) if raw_user else {}
    
    if current_user.get("is_suspended"):
        sus_until = current_user.get("suspended_until", "")
        if datetime.now().strftime("%Y-%m-%d %H:%M:%S") < sus_until:
            st.error(f"🚫 Account Suspended for community guidelines violation until: {sus_until}")
            st.stop()

    st.sidebar.markdown(f"User: **{current_user.get('full_name', 'User')}**")
    st.sidebar.markdown(f"👥 Real Followers: **{real_followers:,}**")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.is_owner_session = False
        st.rerun()

# ==========================================
# 5. TABS INTERFACE
# ==========================================
tab_feed, tab_profile, tab_monetization = st.tabs(["📺 Public Live Feed", "👤 Profile & Studio", "🌍 Global Monetization & Boost"])

# ------------------------------------------
# TAB 1: PUBLIC LIVE FEED
# ------------------------------------------
with tab_feed:
    search_input = st.text_input("🔍 Search Users, Videos, Hashtags or Secret Code...")
    
    # OWNER COMMAND ACCESS
    if search_input.strip() in SECRET_CODES:
        st.session_state.is_owner_session = True
        st.success("👑 MASTER OWNER COMMAND CENTER UNLOCKED!")
        st.markdown("---")
        
        st.markdown("### 🚀 Pending Boost Requests")
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM boost_requests WHERE status = 'Pending'")
        b_reqs = c.fetchall()
        if b_reqs:
            for br in b_reqs:
                st.write(f"Post ID: {br['post_id']} | Plan: {br['plan']} | Payment Info: {br['trx_info']}")
                if st.button(f"Approve Boost {br['boost_id']}"):
                    c.execute("UPDATE master_app_table SET is_boosted = 1 WHERE record_id = ?", (br['post_id'],))
                    c.execute("UPDATE boost_requests SET status = 'Approved' WHERE boost_id = ?", (br['boost_id'],))
                    conn.commit()
                    st.success("Boost Approved!")
                    st.rerun()
        else:
            st.info("No pending boost requests.")
        conn.close()

    # FEED DISPLAY
    else:
        conn = get_db_connection()
        c = conn.cursor()
        if search_input:
            q_str = f"%{search_input}%"
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' AND (title LIKE ? OR content LIKE ? OR full_name LIKE ? OR tags LIKE ?) ORDER BY is_boosted DESC, created_at DESC", (q_str, q_str, q_str, q_str))
        else:
            c.execute("SELECT * FROM master_app_table WHERE data_type = 'post' ORDER BY is_boosted DESC, created_at DESC")
            
        posts = [dict(r) for r in c.fetchall()]
        conn.close()

        for post in posts:
            st.markdown("<div style='background:#18191a; padding:15px; border-radius:12px; margin-bottom:20px;'>", unsafe_allow_html=True)
            
            # Real Follower Count & Status
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT profile_pic_path, fb_link, tiktok_link, yt_link, website_link FROM master_app_table WHERE data_type = 'user' AND user_id = ?", (post.get("user_id"),))
            author = c.fetchone()
            
            c.execute("SELECT COUNT(*) as cnt FROM follows WHERE following_id = ?", (post.get("user_id"),))
            author_followers = c.fetchone()["cnt"]
            
            is_following = False
            if st.session_state.user_id:
                c.execute("SELECT * FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, post.get("user_id")))
                if c.fetchone(): is_following = True
            conn.close()
            
            author_pic = author["profile_pic_path"] if author and author["profile_pic_path"] and os.path.exists(author["profile_pic_path"]) else None
            
            col_h1, col_h2 = st.columns([4, 1])
            with col_h1:
                tick = get_meta_blue_badge() if post.get("is_verified") else ""
                boost_badge = "🔥 [BOOSTED]" if post.get("is_boosted") else ""
                
                if author_pic:
                    st.image(author_pic, width=50)
                st.markdown(f"### {post.get('full_name')} {tick} <span style='color:orange;'>{boost_badge}</span>", unsafe_allow_html=True)
                st.caption(f"👥 Real Followers: {author_followers:,} | Category: {post.get('post_category')}")
                
            with col_h2:
                if st.session_state.user_id and st.session_state.user_id != post.get("user_id"):
                    fol_lbl = "✔ Following" if is_following else "➕ Follow"
                    if st.button(fol_lbl, key=f"fol_{post['record_id']}"):
                        conn = get_db_connection()
                        c = conn.cursor()
                        if is_following:
                            c.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (st.session_state.user_id, post.get("user_id")))
                        else:
                            c.execute("INSERT OR REPLACE INTO follows VALUES (?, ?)", (st.session_state.user_id, post.get("user_id")))
                        conn.commit()
                        conn.close()
                        st.rerun()

            if post.get("title"): st.subheader(post["title"])
            if post.get("content"): st.write(post["content"])
            if post.get("tags"): st.markdown(f"<span style='color:#0064e0;'>{post['tags']}</span>", unsafe_allow_html=True)
            
            # Video / Photo with Watermark Overlay
            media_path = post.get("media_path")
            cat = post.get("post_category")
            
            if media_path and os.path.exists(media_path):
                st.markdown("<div class='video-watermark-wrapper'><div class='video-watermark-badge'>BD AI BOOK</div>", unsafe_allow_html=True)
                if cat == "picture":
                    st.image(media_path, use_container_width=True)
                elif cat == "short":
                    st.markdown("<div class='tiktok-container'>", unsafe_allow_html=True)
                    st.video(media_path)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.video(media_path)
                st.markdown("</div>", unsafe_allow_html=True)

            # Real Likes Logic
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM likes WHERE post_id = ?", (post["record_id"],))
            real_likes = c.fetchone()["cnt"]
            
            has_liked = False
            if st.session_state.user_id:
                c.execute("SELECT * FROM likes WHERE user_id = ? AND post_id = ?", (st.session_state.user_id, post["record_id"]))
                if c.fetchone(): has_liked = True
            conn.close()

            # Interactive Stats
            st.markdown("---")
            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
            col_b1.write(f"👁️ **{post.get('views_count', 0):,}** Views")
            
            like_lbl = f"❤️ Liked ({real_likes})" if has_liked else f"👍 Like ({real_likes})"
            if col_b2.button(like_lbl, key=f"lk_{post['record_id']}"):
                if st.session_state.user_id:
                    conn = get_db_connection()
                    c = conn.cursor()
                    if has_liked:
                        c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (st.session_state.user_id, post["record_id"]))
                    else:
                        c.execute("INSERT OR REPLACE INTO likes VALUES (?, ?)", (st.session_state.user_id, post["record_id"]))
                    conn.commit()
                    conn.close()
                    st.rerun()
                else:
                    st.warning("Please login to like!")

            col_b3.button("💬 Comment", key=f"cm_{post['record_id']}")
            
            if col_b4.button("🚀 Share", key=f"sh_{post['record_id']}"):
                st.markdown(f"<script>shareContent('{post.get('title', '')}', window.location.href);</script>", unsafe_allow_html=True)
                st.toast("Sharing Window Opened!")
                
            st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: PROFILE & CREATOR STUDIO
# ------------------------------------------
with tab_profile:
    if not st.session_state.user_id:
        st.warning("Please login to manage profile!")
    else:
        tick = get_meta_blue_badge() if current_user.get("is_verified") else ""
        st.markdown(f"## Profile Studio: {current_user.get('full_name', 'User')} {tick}", unsafe_allow_html=True)
        
        profile_path = current_user.get("profile_pic_path")
        cover_path = current_user.get("cover_pic_path")
        
        if cover_path and os.path.exists(cover_path):
            st.image(cover_path, use_container_width=True)
            
        col_p1, col_p2 = st.columns([1, 4])
        with col_p1:
            if profile_path and os.path.exists(profile_path):
                st.image(profile_path, width=120)
            else:
                st.info("No Profile Pic")
        with col_p2:
            st.write(f"👥 **Real Followers:** {real_followers:,}")
            st.write(f"**Bio:** {current_user.get('bio', 'No bio added')}")
            st.write(f"**Address:** {current_user.get('address', 'Not set')}")

        # Edit Profile Panel
        with st.expander("⚙️ Edit Profile & Social Links"):
            u_name = st.text_input("Name", value=current_user.get("full_name", ""))
            u_addr = st.text_input("Address", value=current_user.get("address") or "")
            u_bio = st.text_area("Bio", value=current_user.get("bio") or "")
            
            u_fb = st.text_input("Facebook Profile URL", value=current_user.get("fb_link") or "")
            u_tiktok = st.text_input("TikTok Profile URL", value=current_user.get("tiktok_link") or "")
            u_yt = st.text_input("YouTube Channel URL", value=current_user.get("yt_link") or "")
            u_web = st.text_input("Website Link", value=current_user.get("website_link") or "")
            
            up_prof = st.file_uploader("Upload Profile Picture (Circular Avatar)", type=["jpg", "png", "jpeg"], key="dp_edit")
            up_cov = st.file_uploader("Upload Cover Photo", type=["jpg", "png", "jpeg"], key="cov_edit")
            
            if st.button("Save Profile"):
                p_path = profile_path
                c_path = cover_path
                
                if up_prof:
                    p_path = os.path.join(UPLOAD_DIR, f"dp_{st.session_state.user_id}.png")
                    with open(p_path, "wb") as f: f.write(up_prof.getbuffer())
                if up_cov:
                    c_path = os.path.join(UPLOAD_DIR, f"cov_{st.session_state.user_id}.png")
                    with open(c_path, "wb") as f: f.write(up_cov.getbuffer())
                    
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    UPDATE master_app_table 
                    SET full_name = ?, address = ?, bio = ?, profile_pic_path = ?, cover_pic_path = ?,
                        fb_link = ?, tiktok_link = ?, yt_link = ?, website_link = ? 
                    WHERE user_id = ?
                """, (u_name, u_addr, u_bio, p_path, c_path, u_fb, u_tiktok, u_yt, u_web, st.session_state.user_id))
                conn.commit()
                conn.close()
                st.success("Profile Updated!")
                st.rerun()

        # Publish Media
        st.markdown("---")
        st.markdown("### 📤 Upload New Post")
        post_type = st.selectbox("Format", ["short", "long", "picture"])
        title = st.text_input("Title")
        desc = st.text_area("Description")
        p_tags = st.text_input("Hashtags (e.g. #BD_AI_BOOK #Viral)")
        uploaded_media = st.file_uploader("Media File", type=["mp4", "jpg", "png"])
        
        if st.button("Publish Post"):
            if uploaded_media and title:
                if any(w in (title + " " + desc).lower() for w in BANNED_KEYWORDS):
                    conn = get_db_connection()
                    c = conn.cursor()
                    sus_time = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("UPDATE master_app_table SET is_suspended = 1, suspended_until = ? WHERE user_id = ?", (sus_time, st.session_state.user_id))
                    conn.commit()
                    conn.close()
                    st.error("🚫 Inappropriate Content Detected! Account suspended for 30 days.")
                    st.rerun()
                    st.stop()

                ext = os.path.splitext(uploaded_media.name)[1]
                m_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
                with open(m_path, "wb") as f: f.write(uploaded_media.getbuffer())
                
                rec_id = str(uuid.uuid4())
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO master_app_table (record_id, data_type, user_id, full_name, is_verified, title, content, tags, media_path, post_category, views_count, likes_count, created_at)
                    VALUES (?, 'post', ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)
                """, (rec_id, st.session_state.user_id, current_user.get("full_name", "User"), current_user.get("is_verified", 1), title, desc, p_tags, m_path, post_type, now))
                conn.commit()
                conn.close()
                st.success("Published Successfully!")
                st.rerun()

# ------------------------------------------
# TAB 3: GLOBAL MONETIZATION & BOOSTING
# ------------------------------------------
with tab_monetization:
    st.markdown("### 💸 Worldwide Monetization & Video Boost Center")
    
    if real_followers >= 1000:
        st.success(f"🎉 **Monetization Active!** You have {real_followers:,} Real Followers (Requirement: 1,000).")
        st.metric("Estimated Earning Balance", "$1,250.00 USD")
    else:
        st.info(f"📈 **Monetization Progress:** {real_followers}/1,000 Real Followers needed to start earning.")
        
    st.markdown("---")
    st.markdown("### 🚀 Global Video Boosting (Promote Content)")
    st.caption("Boost videos worldwide to reach millions of viewers instantly.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("#### 📌 Option 1: 30 Days Global Boost")
        st.write("**Cost:** $30 USD")
        st.write("Target Views: 100,000+")
    with col_b2:
        st.markdown("#### 📌 Option 2: 60 Days Global Boost")
        st.write("**Cost:** $60 USD")
        st.write("Target Views: 300,000+")
        
    with st.expander("💳 Send Payment & Submit Boost Request"):
        st.markdown(BANK_DETAILS)
        b_plan = st.selectbox("Select Plan", ["30 Days ($30)", "60 Days ($60)"])
        b_post_id = st.text_input("Enter Video Record ID / Title to Boost")
        b_trx = st.text_area("Enter Payment Reference / Transaction ID")
        
        if st.button("Submit Boost Request"):
            if b_post_id and b_trx:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO boost_requests (boost_id, user_id, plan, amount, trx_info, post_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), st.session_state.get("user_id"), b_plan, "$30" if "30" in b_plan else "$60", b_trx, b_post_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("Boost Request Submitted! Admin will review and activate within 1 hour.")

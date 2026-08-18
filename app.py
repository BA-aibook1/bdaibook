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

# ইমেইল ও রিকোয়েস্ট লাইব্রেরি
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Global Sovereign Enterprise Vault",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Global SMTP Configuration (অটোমেটিক ইমেইল পাঠানোর জন্য)
# ---------------------------------------------------------
DEFAULT_SENDER_EMAIL = "md4695090@gmail.com"
DEFAULT_SENDER_APP_PASSWORD = ""  # এখানে আপনার ১৬ ডিজিটের Gmail App Password বসিয়ে দিন

# ---------------------------------------------------------
# Custom Styling & Meta Tags Injection
# ---------------------------------------------------------
meta_html = """
<meta name="msvalidate.01" content="MONETAG_VERIFICATION_CODE" />
<script src="https://omg10.com/script.js" data-ad="global_monetization"></script>
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { background-color: #ff4b4b; color: white; border-radius: 8px; border: none; font-weight: bold; }
    .vault-card { background: #1f2937; padding: 20px; border-radius: 10px; border: 1px solid #374151; margin-bottom: 15px; }
    .bank-card { background: #111827; padding: 20px; border-radius: 12px; border: 2px solid #10b981; margin-top: 15px; }
</style>
"""
components.html(meta_html, height=0)

# ---------------------------------------------------------
# Global Master Database Setup (All 18 Tables)
# ---------------------------------------------------------
DB_FILE = "global_enterprise_master.db"

def init_master_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # ১. ইউজার টেবিল
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_01_users (
        vault_id TEXT PRIMARY KEY, username TEXT, email TEXT, phone TEXT, password_hash TEXT, role TEXT, balance REAL
    )""")
    # ২. গ্লোবাল পোস্ট
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_02_global_posts (
        post_id TEXT PRIMARY KEY, vault_id TEXT, content TEXT, media_url TEXT, category TEXT, created_at TEXT
    )""")
    # ৩. শর্টস ফিড
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_03_shorts_feed (
        short_id TEXT PRIMARY KEY, vault_id TEXT, video_url TEXT, caption TEXT, likes INTEGER
    )""")
    # ৪. হোয়াটসঅ্যাপ সাপোর্ট
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_04_whatsapp_desk (
        ticket_id TEXT PRIMARY KEY, vault_id TEXT, message TEXT, status TEXT
    )""")
    # ৫. পে-আউটস
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_05_payouts (
        payout_id TEXT PRIMARY KEY, vault_id TEXT, amount REAL, method TEXT, status TEXT
    )""")
    # ৬. মনিটাইজেশন
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_06_monetization (
        vault_id TEXT PRIMARY KEY, impressions INTEGER, earnings REAL
    )""")
    # ৭. প্রোফাইল
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_07_user_profiles (
        vault_id TEXT PRIMARY KEY, bio TEXT, avatar_url TEXT
    )""")
    # ৮. সিকিউরিটি লগ
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_08_content_security (
        log_id TEXT PRIMARY KEY, vault_id TEXT, content TEXT, flag_reason TEXT
    )""")
    # ৯. ইমেইল লগ
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_09_email_logs (
        email_id TEXT PRIMARY KEY, recipient TEXT, subject TEXT, sent_at TEXT
    )""")
    # ১০. ক্রিপ্টো ভল্ট
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_10_crypto_vault (
        tx_id TEXT PRIMARY KEY, vault_id TEXT, amount REAL, currency TEXT
    )""")
    # ১১. সার্ভার হেলথ
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_11_server_health (
        node_id TEXT PRIMARY KEY, status TEXT, last_ping TEXT
    )""")
    # ১২. এড নেটওয়ার্ক
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_12_ad_network (
        ad_id TEXT PRIMARY KEY, impression_count INTEGER, revenue REAL
    )""")
    # ১৩. অডিট ট্রেইল
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_13_audit_trails (
        audit_id TEXT PRIMARY KEY, action TEXT, timestamp TEXT
    )""")
    # ১৪. নোটিফিকেশন
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_14_notifications (
        notif_id TEXT PRIMARY KEY, vault_id TEXT, message TEXT, is_read INTEGER
    )""")
    # ১৫. এপিআই কি
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_15_api_keys (
        key_id TEXT PRIMARY KEY, vault_id TEXT, api_key TEXT
    )""")
    # ১৬. সেন্ট্রাল পাইপলাইন
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_16_global_central_pipeline (
        pipeline_id TEXT PRIMARY KEY, source TEXT, status TEXT, payload TEXT
    )""")
    # ১৭. পাসওয়ার্ড রিসেট পিন / ওটিপি টেবিল
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_17_password_resets (
        email TEXT PRIMARY KEY, reset_pin TEXT, created_at TEXT
    )""")
    
    # ১৮. অ্যাডভাইজার ও ওনার ব্যাঙ্ক অ্যাকাউন্ট টেবিল (New Table Added)
    cursor.execute("""CREATE TABLE IF NOT EXISTS tb_18_bank_accounts (
        account_id TEXT PRIMARY KEY,
        owner_name TEXT,
        recipient_address TEXT,
        iban TEXT,
        bic_swift TEXT,
        account_number TEXT,
        bank_name TEXT,
        bank_address TEXT,
        account_type TEXT,
        monthly_payout_usd REAL
    )""")

    # ডিফল্ট অ্যাডভাইজার ব্যাঙ্ক ডিটেইলস ডাটাবেসে সেভ করা (যদি আগে না থাকে)
    cursor.execute("SELECT COUNT(*) FROM tb_18_bank_accounts")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO tb_18_bank_accounts VALUES (
                'BANK_OWNER_01',
                'Md Sohel Rana',
                'Bangladesh, Barabari, SHIBRAM BARABARI SADAR LALMONIRHAT, LALMONIRHAT, 5500',
                'GB89CLRB04281239130579',
                'CLRBGB22XXX',
                '39130579',
                'Clear Bank (Based in GB)',
                '133 Houndsditch, LONDON, EC3A 7BX',
                'Checking (Current)',
                20.00
            )
        """)
    
    conn.commit()
    conn.close()

init_master_database()

# ---------------------------------------------------------
# SMTP Real Email Dispatch Engine
# ---------------------------------------------------------
def send_real_email(sender_email, sender_app_password, recipient_email, subject, body_text):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        email_id = str(uuid.uuid4())[:8]
        cursor.execute(
            "INSERT INTO tb_09_email_logs VALUES (?, ?, ?, ?)",
            (email_id, recipient_email, subject, str(datetime.now()))
        )
        conn.commit()
        conn.close()

        return True, "ইমেইল সফলভাবে পাঠানো হয়েছে!"
    except Exception as e:
        return False, f"ইমেইল পাঠাতে ব্যর্থ: {str(e)}"

# ---------------------------------------------------------
# Security Guard & Utility Functions
# ---------------------------------------------------------
def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def ai_content_security_guard(text_content):
    banned_words = ["hack", "scam", "fraud", "illegal", "exploit"]
    for word in banned_words:
        if word in text_content.lower():
            return False, f"Banned keyword detected: {word}"
    return True, "Passed"

# ---------------------------------------------------------
# Streamlit UI Navigation
# ---------------------------------------------------------
st.sidebar.title("🛡️ Enterprise Vault")
st.sidebar.write("Owner Support: md4695090@gmail.com")

menu = st.sidebar.radio("Navigation Menu", [
    "World Feed", "Shorts Feed", "WhatsApp Support", 
    "Email Notification", "Payout & Monetization", "Profile", "Register & Security"
])

# ---------------------------------------------------------
# Feature Modules
# ---------------------------------------------------------

if menu == "Register & Security":
    tab1, tab2 = st.tabs(["📝 Register New Vault", "🔑 Forgot Password"])

    with tab1:
        st.subheader("Register New Sovereign Vault Account")
        username = st.text_input("Username", key="reg_user")
        email = st.text_input("Email Address", key="reg_email")
        phone = st.text_input("Phone Number", key="reg_phone")
        password = st.text_input("Password", type="password", key="reg_pass")
        
        with st.expander("⚙️ System Email Credentials (For Sending Welcome Email)"):
            sys_sender = st.text_input("System Sender Email", value=DEFAULT_SENDER_EMAIL, key="reg_sys_email")
            sys_pass = st.text_input("Gmail App Password", value=DEFAULT_SENDER_APP_PASSWORD, type="password", key="reg_sys_pass")
        
        if st.button("Create Vault Account"):
            if username and email and phone and password:
                vault_id = str(uuid.uuid4())[:8]
                p_hash = hash_pass(password)
                
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tb_01_users (vault_id, username, email, phone, password_hash, role, balance) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (vault_id, username, email, phone, p_hash, "User", 0.0)
                )
                conn.commit()
                conn.close()
                st.success(f"Vault account created successfully! Your Vault ID: {vault_id}")

                if sys_sender and sys_pass:
                    with st.spinner("পাঠানো হচ্ছে অটোমেটিক ওয়েলকাম ইমেইল..."):
                        welcome_subject = "Welcome to Global Sovereign Enterprise Vault!"
                        welcome_body = (
                            f"Hello {username},\n\n"
                            f"Welcome to Global Sovereign Enterprise Vault!\n"
                            f"Your account has been successfully created.\n\n"
                            f"Your Vault ID: {vault_id}\n"
                            f"Registered Email: {email}\n\n"
                            f"Thank you for joining us.\n"
                            f"Best regards,\n"
                            f"Global Enterprise Team"
                        )
                        email_sent, email_msg = send_real_email(sys_sender, sys_pass, email, welcome_subject, welcome_body)
                        if email_sent:
                            st.info(f"📩 আপনার ইমেইলে ({email}) একটি ওয়েলকাম কনফার্মেশন পাঠানো হয়েছে!")
                        else:
                            st.warning(f"অটোমেটিক ইমেইল পাঠানো সম্ভব হয়নি। কারণ: {email_msg}")
            else:
                st.error("Please fill in all fields.")

    with tab2:
        st.subheader("Password Recovery Via Email OTP")
        st.write("আপনার একাউন্টের রেজিস্টার্ড ইমেইল প্রবেশ করালে একটি ৬ ডিজিটের সিকিউরিটি পিন (OTP) পাঠানো হবে।")
        
        recovery_email = st.text_input("Registered Email Address")
        
        with st.expander("⚙️ System Email Credentials (For Sending OTP)"):
            otp_sender = st.text_input("System Sender Email", value=DEFAULT_SENDER_EMAIL, key="otp_sys_email")
            otp_pass = st.text_input("Gmail App Password", value=DEFAULT_SENDER_APP_PASSWORD, type="password", key="otp_sys_pass")

        if st.button("Send Reset PIN"):
            if recovery_email:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM tb_01_users WHERE email=?", (recovery_email,))
                user_found = cursor.fetchone()
                
                if user_found:
                    reset_pin = str(random.randint(100000, 999999))
                    cursor.execute("REPLACE INTO tb_17_password_resets (email, reset_pin, created_at) VALUES (?, ?, ?)",
                                   (recovery_email, reset_pin, str(datetime.now())))
                    conn.commit()
                    conn.close()

                    if otp_sender and otp_pass:
                        with st.spinner("ইমেইলে রিসেট পিন পাঠানো হচ্ছে..."):
                            subject = "Password Reset PIN - Global Enterprise Vault"
                            body = (
                                f"Hello {user_found[0]},\n\n"
                                f"Your Password Reset PIN is: {reset_pin}\n\n"
                                f"Please use this PIN to set a new password for your account.\n\n"
                                f"If you did not request this, please ignore this message."
                            )
                            sent, msg = send_real_email(otp_sender, otp_pass, recovery_email, subject, body)
                            if sent:
                                st.success(f"✅ রিসেট পিন পাঠানো হয়েছে: {recovery_email}")
                            else:
                                st.error(f"পিন পাঠাতে সমস্যা হয়েছে: {msg}")
                    else:
                        st.error("সিস্টেম ইমেইল বা অ্যাপ পাসওয়ার্ড অনুপস্থিত।")
                else:
                    conn.close()
                    st.error("এই ইমেইল দিয়ে কোনো অ্যাকাউন্ট খুঁজে পাওয়া যায়নি।")
            else:
                st.warning("অনুগ্রহ করে আপনার ইমেইল ঠিকানা দিন।")

        st.divider()
        st.write("### 🔐 Set New Password Using PIN")
        entered_pin = st.text_input("Enter 6-Digit PIN", max_chars=6)
        new_password = st.text_input("Enter New Password", type="password")

        if st.button("Reset Password Now"):
            if recovery_email and entered_pin and new_password:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT reset_pin FROM tb_17_password_resets WHERE email=?", (recovery_email,))
                pin_row = cursor.fetchone()

                if pin_row and pin_row[0] == entered_pin:
                    new_hash = hash_pass(new_password)
                    cursor.execute("UPDATE tb_01_users SET password_hash=? WHERE email=?", (new_hash, recovery_email))
                    cursor.execute("DELETE FROM tb_17_password_resets WHERE email=?", (recovery_email,))
                    conn.commit()
                    conn.close()
                    st.success("🎉 আপনার পাসওয়ার্ড সফলভাবে পরিবর্তিত হয়েছে! এখন নতুন পাসওয়ার্ড দিয়ে লগইন করুন।")
                else:
                    conn.close()
                    st.error("পিনটি ভুল অথবা সঠিক ইমেইল দেননি।")
            else:
                st.warning("পাসওয়ার্ড পরিবর্তন করতে ইমেইল, পিন এবং নতুন পাসওয়ার্ড সবকটি পূরণ করুন।")

elif menu == "Email Notification":
    st.subheader("📧 SMTP Real Email Dispatcher")
    sender_email = st.text_input("Sender Gmail Address", value=DEFAULT_SENDER_EMAIL)
    sender_password = st.text_input("Gmail App Password (16-Digit)", value=DEFAULT_SENDER_APP_PASSWORD, type="password")
    
    st.divider()
    recipient_email = st.text_input("Recipient Email Address")
    email_subject = st.text_input("Email Subject")
    email_body = st.text_area("Email Message / Body")

    if st.button("🚀 Send Email Now"):
        if sender_email and sender_password and recipient_email and email_subject and email_body:
            with st.spinner("ইমেইল পাঠানো হচ্ছে..."):
                success, msg = send_real_email(sender_email, sender_password, recipient_email, email_subject, email_body)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
        else:
            st.warning("অনুগহ করে সবকটি ঘর পূরণ করুন।")

elif menu == "World Feed":
    st.subheader("🌐 Global World Feed")
    with st.expander("➕ Create New Post"):
        user_vault = st.text_input("Your Vault ID")
        post_text = st.text_area("Post Content")
        media_link = st.text_input("Media URL (Optional)")
        
        if st.button("Publish Post"):
            is_safe, msg = ai_content_security_guard(post_text)
            if not is_safe:
                st.error(f"Security Alert: {msg}")
            else:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                post_id = str(uuid.uuid4())[:8]
                cursor.execute(
                    "INSERT INTO tb_02_global_posts VALUES (?, ?, ?, ?, ?, ?)",
                    (post_id, user_vault, post_text, media_link, "General", str(datetime.now()))
                )
                conn.commit()
                conn.close()
                st.success("Post published to global feed!")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT vault_id, content, created_at FROM tb_02_global_posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    conn.close()
    
    for p in posts:
        st.markdown(f"""
        <div class="vault-card">
            <small>Vault ID: {p[0]} | {p[2]}</small>
            <p style="font-size: 16px; margin-top: 5px;">{p[1]}</p>
        </div>
        """, unsafe_allow_html=True)

elif menu == "Shorts Feed":
    st.subheader("🎬 Global Shorts Feed")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT video_url, caption FROM tb_03_shorts_feed")
    shorts = cursor.fetchall()
    conn.close()
    
    if shorts:
        for s in shorts:
            st.video(s[0])
            st.caption(s[1])
    else:
        st.info("No shorts available right now.")

elif menu == "WhatsApp Support":
    st.subheader("💬 WhatsApp Support Desk")
    st.write("Need help? Contact our central engine team directly via WhatsApp.")
    msg = st.text_area("Type your inquiry...")
    if st.button("Send to WhatsApp"):
        encoded_msg = urllib.parse.quote(msg)
        whatsapp_url = f"https://wa.me/8801700000000?text={encoded_msg}"
        st.markdown(f"[👉 Click here to open WhatsApp]({whatsapp_url})", unsafe_allow_html=True)

# ---------------------------------------------------------
# Payout & Monetization (আপডেট করা সেকশন)
# ---------------------------------------------------------
elif menu == "Payout & Monetization":
    st.subheader("💰 Monetization & Payouts")
    
    v_id = st.text_input("Enter Vault ID for Earnings")
    if st.button("Check Balance"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM tb_01_users WHERE vault_id=?", (v_id,))
        res = cursor.fetchone()
        conn.close()
        if res:
            st.metric(label="Available Balance", value=f"${res[0]:.2f}")
        else:
            st.error("Vault ID not found.")

    st.divider()
    
    # অ্যাডভাইজার / অনার ব্যাঙ্ক ডিটেইলস কার্ড
    st.subheader("🏦 Owner & Advisor Bank Details ($20/Month Auto-Payout)")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tb_18_bank_accounts WHERE account_id='BANK_OWNER_01'")
    bank_data = cursor.fetchone()
    conn.close()

    if bank_data:
        st.markdown(f"""
        <div class="bank-card">
            <h3 style="color: #10b981; margin-top: 0;">💳 Automatic Monthly Deposit Account</h3>
            <p><strong>Name:</strong> {bank_data[1]}</p>
            <p><strong>Address:</strong> {bank_data[2]}</p>
            <p><strong>IBAN:</strong> <code>{bank_data[3]}</code></p>
            <p><strong>BIC / SWIFT Code:</strong> <code>{bank_data[4]}</code></p>
            <p><strong>Account Number:</strong> <code>{bank_data[5]}</code></p>
            <p><strong>Bank Name:</strong> {bank_data[6]}</p>
            <p><strong>Bank Address:</strong> {bank_data[7]}</p>
            <p><strong>Account Type:</strong> {bank_data[8]}</p>
            <hr style="border-color: #374151;">
            <p style="font-size: 18px; color: #f59e0b;">💵 <strong>Monthly Deposit Amount:</strong> ${bank_data[9]:.2f} USD / Month</p>
            <small style="color: #9ca3af;">* এই অ্যাকাউন্টে প্রতি মাসে ২০ ডলার স্বয়ংক্রিয়ভাবে প্রদান করার জন্য কনফিগার করা আছে।</small>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Profile Section
# ---------------------------------------------------------
elif menu == "Profile":
    st.subheader("👤 User Profile & Owner Info")
    st.write("Manage your vault settings and view registered system profiles.")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT owner_name, account_number, bank_name FROM tb_18_bank_accounts WHERE account_id='BANK_OWNER_01'")
    b_info = cursor.fetchone()
    conn.close()

    if b_info:
        st.info(f"🔑 Vault Advisor / Owner: **{b_info[0]}** | Bank: **{b_info[2]}** (Acc: `{b_info[1]}`)")

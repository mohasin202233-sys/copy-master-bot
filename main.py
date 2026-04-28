import os
import telebot
from flask import Flask
from threading import Thread
import sqlite3
from datetime import datetime, timedelta
from telebot import types

# --- Flask Server (বটকে ২৪ ঘণ্টা লাইভ রাখার জন্য) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- আপনার বটের তথ্য ---
API_TOKEN = '8770587499:AAE9WrB_G0Ugz2dyNkL8bSPyWCiIXq27uoM'
ADMIN_ID = 8155493482 
MY_WALLET = "0x22b4907dc3bc250e92ffa402c47f2776faaadf64"

bot = telebot.TeleBot(API_TOKEN)

# ডাটাবেস সেটআপ
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
        "📜 **বটের নিয়মাবলী ও শর্তাবলী:**\n"
        "১. 💵 **ডিপোজিট:** সর্বনিম্ন ১০$ (USDT-BEP20) ইনভেস্ট করতে পারবেন।\n"
        "২. ⏳ **সময়সীমা:** আপনার ডলার ৩০ দিনের জন্য লক থাকবে।\n"
        "৩. 📈 **প্রফিট:** মাস শেষে মূল লভ্যাংশের ৭৫% আপনার ব্যালেন্সে যোগ হবে।\n"
        "৪. ✅ **ভেরিফিকেশন:** সঠিক TxID বা স্ক্রিনশট দিতে হবে।\n"
        "৫. 🎁 **রেফার বোনাস:** প্রতি জন রেফারেল ইনভেস্টমেন্টে ৫.০$ বোনাস।\n\n"
        f"🆔 **আপনার আইডি:** `{message.chat.id}`"
    )
    bot.send_message(message.chat.id, full_rules, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '📊 My Balance')
def check_balance(message):
    conn = sqlite3.connect('trading_master_v12.db')
    c = conn.cursor()
    c.execute("SELECT total_balance, profit, dep_date FROM users WHERE user_id = ?", (message.chat.id,))
    data = c.fetchone()
    conn.close()

    if data:
        msg = f"📊 **ব্যালেন্স ডিটেইলস**\n\n💵 ইনভেস্টমেন্ট: {data[0]}$\n📈 মোট প্রফিট: {data[1]}$\n📅 শুরুর তারিখ: {data[2]}"
    else:
        msg = "❌ আপনার কোনো সক্রিয় ইনভেস্টমেন্ট রেকর্ড পাওয়া যায়নি।"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    if message.text == '💰 Deposit':
        bot.send_message(message.chat.id, f"💰 **ডিপোজিট করার নিয়ম:**\n\nনিচের অ্যাড্রেসে USDT (BEP20) পাঠান:\n`{MY_WALLET}`\n\nপাঠানোর পর আপনার TxID অথবা পেমেন্টের স্ক্রিনশট এখানে পাঠান।", parse_mode="Markdown")
    elif message.text == '💳 Withdraw':
        bot.send_message(message.chat.id, "⚠️ উইথড্র করার জন্য আপনার প্রফিট অন্তত ১০$ হতে হবে। বর্তমানে আপনার উইথড্র রিকোয়েস্ট প্রসেস করা সম্ভব নয়।")
    elif message.chat.id != ADMIN_ID:
        # ইউজার যদি কোনো স্ক্রিনশট বা TxID পাঠায় তা অ্যাডমিনের কাছে যাবে
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "⏳ আপনার তথ্য অ্যাডমিনের কাছে পাঠানো হয়েছে। ভেরিফাই হতে কিছুটা সময় লাগতে পারে। ধন্যবাদ।")

# --- রান করার মেইন পার্ট ---
if __name__ == "__main__":
    init_db()
    keep_alive() 
    print("বট সফলভাবে চালু হয়েছে...")
    bot.infinity_polling()

import os
import telebot
from flask import Flask
from threading import Thread
import sqlite3
from datetime import datetime
from telebot import types

# --- Flask Server ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- আপনার বটের তথ্য ---
API_TOKEN = '8770587499:AAE9WrB_G0Ugz2dyNkL8bSPyWCiIXq27uoM'
ADMIN_ID = 8155493482 
MY_WALLET = "0x22b4907dc3bc250e92ffa402c47f2776faaadf64"

bot = telebot.TeleBot(API_TOKEN)

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

# --- অ্যাডমিন কমান্ড: ব্যালেন্স অ্যাড করা ---
@bot.message_handler(commands=['add'])
def add_balance(message):
    if message.chat.id == ADMIN_ID:
        try:
            # কমান্ড ফরম্যাট: /add 12345678 10
            args = message.text.split()
            target_id = int(args[1])
            amount = float(args[2])
            date_now = datetime.now().strftime("%Y-%m-%d")

            conn = sqlite3.connect('trading_master_v12.db')
            c = conn.cursor()
            
            # ইউজার আগে থেকে আছে কি না চেক করা
            c.execute("SELECT total_balance FROM users WHERE user_id = ?", (target_id,))
            user = c.fetchone()

            if user:
                new_balance = user[0] + amount
                c.execute("UPDATE users SET total_balance = ?, dep_date = ? WHERE user_id = ?", (new_balance, date_now, target_id))
            else:
                c.execute("INSERT INTO users (user_id, total_balance, profit, dep_date) VALUES (?, ?, ?, ?)", (target_id, amount, 0.0, date_now))
            
            conn.commit()
            conn.close()

            bot.send_message(ADMIN_ID, f"✅ সফল হয়েছে!\n🆔 আইডি: `{target_id}`\n💵 অ্যাড হয়েছে: {amount}$")
            bot.send_message(target_id, f"🎉 **অভিনন্দন!**\nআপনার ডিপোজিট সফলভাবে অনুমোদিত হয়েছে।\n💰 পরিমাণ: {amount}$")
        
        except Exception as e:
            bot.send_message(ADMIN_ID, "❌ ভুল ফরম্যাট! এভাবে লিখুন: `/add 123456 10`", parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    full_rules = (
        "👋 **আসসালামু আলাইকুম!**\n\n"
        "📜 **বটের নিয়মাবলী:**\n"
        "১. 💵 সর্বনিম্ন ২০$ (USDT-BEP20) ডিপোজিট।\n"
        "২. ⏳ ডলার ৩০ দিনের জন্য লক থাকবে।\n"
        "৩. 📈 মাস শেষে লাভের ৭০% আপনার।\n"
        "৪. ✅ সঠিক TxID বা স্ক্রিনশট দিতে হবে।\n\n"
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
        bot.send_message(message.chat.id, f"💰 **ডিপোজিট নিয়ম:**\nঅ্যাড্রেস: `{MY_WALLET}`\n\nপাঠানোর পর TxID বা স্ক্রিনশট এখানে দিন।", parse_mode="Markdown")
    elif message.text == '💳 Withdraw':
        bot.send_message(message.chat.id, "⚠️ উইথড্র করার জন্য আপনার প্রফিট অন্তত ১০$ হতে হবে।")
    elif message.chat.id != ADMIN_ID:
        user_info = f"🚀 **নতুন ডিপোজিট রিকোয়েস্ট!**\n👤 নাম: {message.from_user.first_name}\n🆔 আইডি: `{message.chat.id}`"
        bot.send_message(ADMIN_ID, user_info, parse_mode="Markdown")
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "⏳ আপনার তথ্য পাঠানো হয়েছে। অ্যাডমিন চেক করে ব্যালেন্স অ্যাড করে দিবে।")

if __name__ == "__main__":
    init_db()
    keep_alive() 
    bot.infinity_polling()

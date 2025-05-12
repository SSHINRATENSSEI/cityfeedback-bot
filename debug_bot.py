import vk_api
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Токен и настройки
TOKEN = os.getenv("VK_TOKEN")
GROUP_CHAT_PEER_ID = int(os.getenv("GROUP_CHAT_PEER_ID"))

# Создание сессии для работы с API
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()

def debug_send_message(peer_id, message):
    try:
        print(f"Отправка сообщения в чат с peer_id: {peer_id}...")

        # Проверка токена доступа
        try:
            user_info = vk.users.get()  # Пробуем получить информацию о пользователе
            print(f"Токен доступа действителен. Информация о пользователе: {user_info}")
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка при проверке токена: {e}")
            return

        # Проверка peer_id
        print(f"Используем peer_id: {peer_id} для отправки сообщения.")
        
        # Отправка сообщения в чат
        response = vk.messages.send(
            peer_id=peer_id,
            message=message,
            random_id=0
        )
        
        print(f"Сообщение отправлено, response: {response}")
        return response

    except vk_api.exceptions.ApiError as e:
        print(f"Произошла ошибка при отправке сообщения: {e}")
        print(f"Ошибка: {e.args[0]}")  # Подробная информация о причине ошибки
        return None

def check_chat_access(peer_id):
    # Пробуем получить информацию о чате (включая его участника)
    try:
        response = vk.messages.getConversations(filter="all", count=10)  # Получаем список диалогов
        print(f"Получено {len(response['items'])} диалогов.")

        for conversation in response['items']:
            chat_peer_id = conversation["conversation"]["peer"]["id"]
            print(f"Найден peer_id чата: {chat_peer_id}")

            if chat_peer_id == peer_id:
                print(f"Бот имеет доступ к чату с peer_id: {peer_id}")
                return True
        
        print(f"Чат с peer_id: {peer_id} не найден или бот не имеет доступа.")
        return False

    except vk_api.exceptions.ApiError as e:
        print(f"Ошибка при получении диалогов: {e}")
        return False

if __name__ == "__main__":
    message = "Тестовое сообщение от бота"
    
    # Печатаем peer_id для отладки
    print(f"Отправка сообщения в чат с peer_id: {GROUP_CHAT_PEER_ID}")
    
    # Проверим, есть ли у бота доступ к чату
    if check_chat_access(GROUP_CHAT_PEER_ID):
        debug_send_message(GROUP_CHAT_PEER_ID, message)
    else:
        print("У бота нет доступа к чату. Проверь настройки чата и его права.")

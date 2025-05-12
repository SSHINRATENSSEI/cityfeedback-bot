import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from dotenv import load_dotenv
import os
import requests
from typing import Dict, Optional
import pandas as pd

from models import User, UserState, Report
from keyboards import Keyboards
from storage import save_report, mark_report_status
from group_chat import notify_group_chat
from logger import logger

class CityFeedbackBot:
    """
    Основной класс бота для обработки обращений граждан.
    Управляет взаимодействием с пользователями, обработкой сообщений и состоянием диалогов.
    
    Attributes:
        token: Токен доступа к API VK
        group_id: ID группы VK
        group_chat_peer_id: ID группового чата для администраторов
        vk_session: Сессия VK API
        vk: API клиент VK
        longpoll: Объект для получения обновлений от VK
        users: Словарь активных пользователей
    """

    def __init__(self):
        """
        Инициализация бота.
        Загружает настройки из .env файла и создает необходимые объекты для работы с VK API.
        """
        load_dotenv()
        self.token = os.getenv("VK_TOKEN")
        self.group_id = int(os.getenv("GROUP_ID"))
        self.group_chat_peer_id = int(os.getenv("GROUP_CHAT_PEER_ID"))
        
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)
        
        self.users: Dict[int, User] = {}
        logger.info("✅ CityFeedback Bot запущен...")

    def handle_new_user(self, user_id: int):
        """
        Обработка нового пользователя.
        Создает объект пользователя и отправляет приветственное сообщение.
        
        Args:
            user_id: ID пользователя в VK
        """
        self.users[user_id] = User(user_id)
        self.vk.messages.send(
            user_id=user_id,
            message="Привет! Я бот для обратной связи. Нажмите 'Начать', чтобы продолжить.",
            random_id=0,
            keyboard=Keyboards.get_start_keyboard()
        )

    def handle_start(self, user_id: int):
        """
        Обработка команды 'Начать'.
        Отправляет приветственное сообщение с инструкциями и главное меню.
        
        Args:
            user_id: ID пользователя в VK
        """
        user_info = self.vk.users.get(user_ids=user_id)[0]
        first_name = user_info['first_name']
        welcome_message = (
            f"Здравствуйте, {first_name}! 👋\n"
            "Я бот для обратной связи.\n\n"
            "Вы можете:\n— 📷 Загрузить фото\n— 📝 Написать обращение\n👇 Выберите действие:"
        )
        self.vk.messages.send(
            user_id=user_id,
            message=welcome_message,
            random_id=0,
            keyboard=Keyboards.get_main_keyboard()
        )
        self.users[user_id].update_state(UserState.WAIT_ACTION)

    def handle_photo(self, user_id: int, attachments):
        """
        Обработка загрузки фото.
        Проверяет тип вложения и сохраняет URL фото.
        
        Args:
            user_id: ID пользователя в VK
            attachments: Список вложений из сообщения
        """
        if attachments:
            photo = attachments[0]
            if photo["type"] == "photo":
                sizes = photo["photo"]["sizes"]
                largest = sorted(sizes, key=lambda s: s["width"])[-1]
                self.users[user_id].update_data(photo_url=largest["url"])
                self.users[user_id].update_state(UserState.WAIT_MESSAGE)
                self.vk.messages.send(
                    user_id=user_id,
                    message="✅ Фото получено. ✍️ Теперь опишите, что вы заметили.",
                    random_id=0
                )
            else:
                self.vk.messages.send(
                    user_id=user_id,
                    message="❗ Пришлите именно фото.",
                    random_id=0
                )
        else:
            self.vk.messages.send(
                user_id=user_id,
                message="❗ Фото не получено. Попробуйте снова.",
                random_id=0
            )

    def handle_message(self, user_id: int, text: str):
        """
        Обработка текстового сообщения.
        Сохраняет текст обращения и запрашивает адрес.
        
        Args:
            user_id: ID пользователя в VK
            text: Текст сообщения
        """
        if text:
            self.users[user_id].update_data(message=text)
            self.users[user_id].update_state(UserState.WAIT_ADDRESS)
            self.vk.messages.send(
                user_id=user_id,
                message="📍 Введите адрес вручную или нажмите кнопку, чтобы отправить геопозицию.",
                keyboard=Keyboards.get_geo_keyboard(),
                random_id=0
            )

    def handle_address(self, user_id: int, text: Optional[str] = None, geo: Optional[dict] = None):
        """
        Обработка адреса или геолокации.
        Создает отчет и отправляет его администраторам.
        
        Args:
            user_id: ID пользователя в VK
            text: Текст адреса (если введен вручную)
            geo: Данные геолокации (если отправлена геопозиция)
        """
        if geo:
            lat = geo["coordinates"]["latitude"]
            lon = geo["coordinates"]["longitude"]
            address = f"Геолокация: {lat}, {lon}"
        elif text:
            address = text
        else:
            return

        self.users[user_id].update_data(address=address)
        self.users[user_id].update_state(UserState.DONE)

        # Создаем и сохраняем отчет
        user_data = self.users[user_id].data.__dict__
        logger.info(f"📊 Отправляем данные в save_report: {user_data}")
        ticket_number, report_date = save_report(user_id, user_data)
        ticket_number = int(ticket_number)  # Убеждаемся, что номер - целое число

        # Получаем сохраненные данные из CSV
        csv_path = "data/reports.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            report_data = df[df['ticket_number'] == ticket_number].iloc[0].to_dict()
            logger.info(f"📄 Данные из CSV: {report_data}")
        else:
            report_data = user_data
            report_data.update({
                'ticket_number': ticket_number,
                'date': report_date
            })

        # Уведомляем администраторов
        notify_group_chat(
            self.vk,
            self.group_chat_peer_id,
            user_id,
            report_data
        )

        # Отправляем подтверждение пользователю
        self.vk.messages.send(
            user_id=user_id,
            message=f"✅ Спасибо! Обращение №{ticket_number} принято и передано в работу!\n\nВы можете отправить ещё одно обращение:",
            keyboard=Keyboards.get_main_keyboard(),
            random_id=0
        )

        # Сбрасываем состояние пользователя
        self.users[user_id].reset()

    def handle_callback(self, event):
        """
        Обработка callback-кнопок от администраторов.
        Обновляет статус обращения и отправляет уведомления.
        
        Args:
            event: Событие callback-кнопки
        """
        payload = event.object["payload"]
        user_id = payload["user_id"]
        ticket_number = payload["ticket_number"]
        action_type = payload["type"]
        
        # Получаем информацию об администраторе, который нажал кнопку
        admin_id = event.object["user_id"]
        admin_info = self.vk.users.get(user_ids=admin_id)[0]
        admin_name = f"{admin_info['first_name']} {admin_info['last_name']}"

        if action_type == "mark_in_progress":
            mark_report_status(ticket_number, "в работе", admin_id, admin_name)
            self.vk.messages.send(
                peer_id=self.group_chat_peer_id,
                message=f"🛠 Обращение №{ticket_number} помечено как 'В работе' администратором {admin_name} (id: {admin_id})",
                random_id=0
            )
        elif action_type == "mark_done":
            mark_report_status(ticket_number, "исполнено", admin_id, admin_name)
            self.vk.messages.send(
                peer_id=self.group_chat_peer_id,
                message=f"✅ Обращение №{ticket_number} помечено как 'Исполнено' администратором {admin_name} (id: {admin_id})",
                random_id=0
            )

    def run(self):
        """
        Основной цикл бота.
        Обрабатывает все входящие события от VK API.
        """
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                user_id = event.message.from_id
                text = event.message.text.strip().lower() if event.message.text else ""
                attachments = event.message.attachments
                geo = event.message.geo

                logger.info(f"📨 Получено сообщение от {user_id}: {text}")

                # Инициализация нового пользователя
                if user_id not in self.users:
                    self.handle_new_user(user_id)
                    continue

                # Обработка команды "Начать"
                if text == "начать":
                    self.handle_start(user_id)
                    continue

                user = self.users[user_id]

                # Обработка в зависимости от состояния пользователя
                if user.state == UserState.WAIT_ACTION:
                    if text == "фото":
                        user.update_state(UserState.WAIT_PHOTO)
                        self.vk.messages.send(
                            user_id=user_id,
                            message="📸 Отправьте фотографию:",
                            random_id=0
                        )
                    elif text == "обращение":
                        user.update_state(UserState.WAIT_MESSAGE)
                        self.vk.messages.send(
                            user_id=user_id,
                            message="✍️ Опишите ваше обращение:",
                            random_id=0
                        )
                    else:
                        self.vk.messages.send(
                            user_id=user_id,
                            message="Пожалуйста, используйте кнопки меню.",
                            random_id=0,
                            keyboard=Keyboards.get_main_keyboard()
                        )

                elif user.state == UserState.WAIT_PHOTO:
                    if attachments:
                        self.handle_photo(user_id, attachments)
                    else:
                        self.vk.messages.send(
                            user_id=user_id,
                            message="❗ Пожалуйста, отправьте фотографию.",
                            random_id=0
                        )

                elif user.state == UserState.WAIT_MESSAGE:
                    self.handle_message(user_id, text)

                elif user.state == UserState.WAIT_ADDRESS:
                    if geo:
                        self.handle_address(user_id, geo=geo)
                    elif text:
                        self.handle_address(user_id, text=text)
                    else:
                        self.vk.messages.send(
                            user_id=user_id,
                            message="❗ Пожалуйста, укажите адрес или отправьте геолокацию.",
                            random_id=0,
                            keyboard=Keyboards.get_geo_keyboard()
                        )

            elif event.type == VkBotEventType.MESSAGE_EVENT:
                self.handle_callback(event)

if __name__ == "__main__":
    bot = CityFeedbackBot()
    bot.run()
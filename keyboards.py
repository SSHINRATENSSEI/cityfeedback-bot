import json
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

class Keyboards:
    """
    Класс для управления клавиатурами бота.
    Содержит статические методы для создания различных типов клавиатур.
    """

    @staticmethod
    def get_start_keyboard():
        """Клавиатура для начала работы"""
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Начать', color=VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()

    @staticmethod
    def get_main_keyboard():
        """Основная клавиатура с выбором действия"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('📷 Фото', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('📝 Обращение', color=VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()

    @staticmethod
    def get_geo_keyboard():
        """Клавиатура для отправки геолокации"""
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_location_button()
        keyboard.add_line()
        keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)
        return keyboard.get_keyboard()

    @staticmethod
    def get_admin_keyboard(user_id: int, ticket_number: int):
        """Клавиатура для администраторов"""
        keyboard = {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "callback",
                            "payload": json.dumps({
                                "type": "mark_in_progress",
                                "user_id": user_id,
                                "ticket_number": ticket_number
                            }),
                            "label": "🛠 В работу"
                        },
                        "color": "primary"
                    },
                    {
                        "action": {
                            "type": "callback",
                            "payload": json.dumps({
                                "type": "mark_done",
                                "user_id": user_id,
                                "ticket_number": ticket_number
                            }),
                            "label": "✅ Исполнено"
                        },
                        "color": "positive"
                    }
                ]
            ]
        }
        return json.dumps(keyboard) 
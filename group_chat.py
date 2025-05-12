from vk_api import VkApi
from keyboards import Keyboards
from logger import logger

def notify_group_chat(vk: VkApi, chat_id: int, user_id: int, report_data: dict):
    """
    Отправляет уведомление в групповой чат администраторов о новом обращении.
    
    Args:
        vk: API клиент VK
        chat_id: ID группового чата
        user_id: ID пользователя
        report_data: Данные обращения
    """
    try:
        # Получаем информацию о пользователе
        user_info = vk.users.get(user_ids=user_id)[0]
        user_name = f"{user_info['first_name']} {user_info['last_name']}"
        
        # Формируем сообщение
        message = (
            f"📨 Новое обращение №{report_data['ticket_number']}\n\n"
            f"👤 От: {user_name} (id: {user_id})\n"
            f"📅 Дата: {report_data['date']}\n"
            f"📍 Адрес: {report_data['address']}\n"
            f"📝 Текст: {report_data['message']}\n"
        )
        
        # Если есть фото, добавляем его
        if report_data.get('photo_url'):
            message += f"\n📸 Фото: {report_data['photo_url']}"
        
        # Отправляем сообщение с клавиатурой
        vk.messages.send(
            peer_id=chat_id,
            message=message,
            random_id=0,
            keyboard=Keyboards.get_admin_keyboard(user_id, report_data['ticket_number'])
        )
        
        logger.info(f"✅ Уведомление о обращении №{report_data['ticket_number']} отправлено в групповой чат")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомления в групповой чат: {str(e)}")

def notify_user(vk: VkApi, user_id: int, ticket_number: int, status: str, admin_name: str):
    """
    Отправляет уведомление пользователю об изменении статуса обращения.
    
    Args:
        vk: API клиент VK
        user_id: ID пользователя
        ticket_number: Номер обращения
        status: Новый статус
        admin_name: Имя администратора
    """
    try:
        message = (
            f"ℹ️ Статус вашего обращения №{ticket_number} изменен:\n"
            f"📊 Новый статус: {status}\n"
            f"👤 Администратор: {admin_name}"
        )
        
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=0
        )
        
        logger.info(f"✅ Уведомление о изменении статуса обращения №{ticket_number} отправлено пользователю")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке уведомления пользователю: {str(e)}")



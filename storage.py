import pandas as pd
import os
import numpy as np
from datetime import datetime
import requests
from urllib.parse import urlparse
import hashlib
from logger import logger
from typing import Tuple, Optional

def ensure_data_directory():
    """Создает директорию для хранения данных, если она не существует"""
    if not os.path.exists("data"):
        os.makedirs("data")

def get_next_ticket_number() -> int:
    """
    Получает следующий номер обращения.
    
    Returns:
        int: Номер следующего обращения
    """
    ensure_data_directory()
    csv_path = "data/reports.csv"
    
    if not os.path.exists(csv_path):
        return 1
    
    df = pd.read_csv(csv_path)
    if df.empty:
        return 1
    
    return df["ticket_number"].max() + 1

def save_report(user_id: int, data: dict) -> Tuple[int, str]:
    """
    Сохраняет обращение в CSV файл.
    
    Args:
        user_id: ID пользователя
        data: Данные обращения
        
    Returns:
        Tuple[int, str]: Номер обращения и дата создания
    """
    ensure_data_directory()
    csv_path = "data/reports.csv"
    
    # Получаем следующий номер обращения
    ticket_number = get_next_ticket_number()
    
    # Добавляем номер и дату
    data["ticket_number"] = ticket_number
    data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Создаем DataFrame
    df_new = pd.DataFrame([data])
    
    # Сохраняем или обновляем CSV
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    
    df.to_csv(csv_path, index=False)
    logger.info(f"✅ Обращение №{ticket_number} сохранено")
    
    return ticket_number, data["date"]

def mark_report_status(ticket_number: int, status: str, admin_id: int, admin_name: str):
    """
    Обновляет статус обращения.
    
    Args:
        ticket_number: Номер обращения
        status: Новый статус
        admin_id: ID администратора
        admin_name: Имя администратора
    """
    csv_path = "data/reports.csv"
    if not os.path.exists(csv_path):
        logger.error(f"❌ Файл {csv_path} не найден")
        return
    
    df = pd.read_csv(csv_path)
    mask = df["ticket_number"] == ticket_number
    
    if not any(mask):
        logger.error(f"❌ Обращение №{ticket_number} не найдено")
        return
    
    df.loc[mask, "status"] = status
    df.loc[mask, "admin_id"] = admin_id
    df.loc[mask, "admin_name"] = admin_name
    df.loc[mask, "status_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    df.to_csv(csv_path, index=False)
    logger.info(f"✅ Статус обращения №{ticket_number} обновлен на '{status}'")

def download_photo(url: str, ticket_number: int) -> Optional[str]:
    """
    Скачивает фото по URL и сохраняет его локально.
    
    Args:
        url: URL фотографии
        ticket_number: Номер обращения
        
    Returns:
        Optional[str]: Путь к сохраненному файлу или None в случае ошибки
    """
    try:
        ensure_data_directory()
        filename = f"data/photo_{ticket_number}.jpg"
        
        response = requests.get(url)
        response.raise_for_status()
        
        with open(filename, "wb") as f:
            f.write(response.content)
        
        logger.info(f"✅ Фото для обращения №{ticket_number} сохранено")
        return filename
    
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении фото: {str(e)}")
        return None

def get_report_data(ticket_number: int) -> Optional[dict]:
    """
    Получает данные обращения по номеру.
    
    Args:
        ticket_number: Номер обращения
        
    Returns:
        Optional[dict]: Данные обращения или None, если обращение не найдено
    """
    csv_path = "data/reports.csv"
    if not os.path.exists(csv_path):
        return None
    
    df = pd.read_csv(csv_path)
    report = df[df["ticket_number"] == ticket_number]
    
    if report.empty:
        return None
    
    return report.iloc[0].to_dict()

def get_reports_by_status(status: str) -> pd.DataFrame:
    """
    Получает все обращения с указанным статусом.
    
    Args:
        status: Статус обращений
        
    Returns:
        pd.DataFrame: DataFrame с обращениями
    """
    csv_path = "data/reports.csv"
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    
    df = pd.read_csv(csv_path)
    return df[df["status"] == status]

def get_reports_by_date_range(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Получает обращения за указанный период.
    
    Args:
        start_date: Начальная дата (YYYY-MM-DD)
        end_date: Конечная дата (YYYY-MM-DD)
        
    Returns:
        pd.DataFrame: DataFrame с обращениями
    """
    csv_path = "data/reports.csv"
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    
    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    return df[mask]

def ensure_photo_directory():
    """
    Создает директорию для хранения фотографий, если она не существует.
    
    Returns:
        str: Путь к директории с фотографиями
    """
    photo_dir = "data/photos"
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
    return photo_dir

def save_photo(photo_url: str) -> str:
    """
    Сохраняет фото из URL в локальную директорию.
    
    Args:
        photo_url: URL фотографии
        
    Returns:
        str: Путь к сохраненному файлу относительно директории data
    """
    try:
        logger.info(f"📸 Начинаем сохранение фото из URL: {photo_url}")
        # Создаем директорию для фото, если её нет
        photo_dir = ensure_photo_directory()
        logger.info(f"📁 Директория для фото: {photo_dir}")
        
        # Генерируем уникальное имя файла на основе URL и текущего времени
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = hashlib.md5(photo_url.encode()).hexdigest()[:8]
        file_extension = os.path.splitext(urlparse(photo_url).path)[1]
        if not file_extension:
            file_extension = '.jpg'
        
        filename = f"photo_{timestamp}_{url_hash}{file_extension}"
        filepath = os.path.join(photo_dir, filename)
        logger.info(f"📄 Сохраняем фото в файл: {filepath}")
        
        # Скачиваем фото
        response = requests.get(photo_url)
        response.raise_for_status()
        
        # Сохраняем фото
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Возвращаем относительный путь к файлу
        relative_path = os.path.join("photos", filename)
        logger.info(f"✅ Фото успешно сохранено: {relative_path}")
        return relative_path
    
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении фото: {e}")
        return None

def get_new_ticket_number(csv_path):
    """
    Получить следующий номер для нового обращения.
    
    Args:
        csv_path: Путь к файлу CSV
        
    Returns:
        int: Следующий доступный номер обращения
    """
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        if not df.empty and not df["ticket_number"].isna().all():
            max_number = df["ticket_number"].max()
            if pd.notna(max_number):  # Проверяем, что значение не NaN
                return int(max_number + 1)
    return 1  # Если файл пустой или все значения NaN, начинаем с 1

def save_report(user_id, user_data):
    """
    Сохраняем новое обращение в CSV, присваиваем ему номер.
    
    Args:
        user_id: ID пользователя
        user_data: Данные обращения
        
    Returns:
        tuple: (номер обращения, дата создания)
    """
    csv_path = "data/reports.csv"
    new_ticket_number = int(get_new_ticket_number(csv_path))  # Преобразуем в int
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"📝 Сохранение отчета для пользователя {user_id}")
    logger.info(f"📊 Данные пользователя: {user_data}")

    # Сохраняем фото, если оно есть
    photo_filename = None
    if "photo_url" in user_data and user_data["photo_url"]:
        logger.info(f"🖼️ Найдено фото в данных пользователя: {user_data['photo_url']}")
        photo_filename = save_photo(user_data["photo_url"])
        logger.info(f"📸 Сохранено фото: {photo_filename}")
    else:
        logger.info("⚠️ Фото не найдено в данных пользователя")

    # Создаем данные в правильном порядке колонок
    new_data = {
        "ticket_number": new_ticket_number,  # Уже int
        "date": current_date,
        "user_id": int(user_id),
        "photo_filename": photo_filename,
        "message": user_data.get("message"),
        "address": user_data.get("address"),
        "status": "новое"
    }
    logger.info(f"📋 Подготовленные данные для сохранения: {new_data}")

    # Проверка, существует ли файл CSV
    if not os.path.exists(csv_path):
        logger.info("📄 Создаем новый CSV файл")
        df = pd.DataFrame([new_data])
        df = df[["ticket_number", "date", "user_id", "photo_filename", "message", "address", "status"]]
        # Устанавливаем тип данных для ticket_number как int
        df["ticket_number"] = df["ticket_number"].astype(int)
    else:
        logger.info("📄 Добавляем данные в существующий CSV файл")
        df = pd.read_csv(csv_path)
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df = df[["ticket_number", "date", "user_id", "photo_filename", "message", "address", "status"]]
        # Устанавливаем тип данных для ticket_number как int
        df["ticket_number"] = df["ticket_number"].astype(int)

    # Сохраняем обновленный DataFrame обратно в CSV
    df.to_csv(csv_path, index=False)
    logger.info(f"🟢 Обращение с номером {new_ticket_number} сохранено.")
    
    return new_ticket_number, current_date

def mark_report_status(ticket_number, status, admin_id=None, admin_name=None):
    """
    Обновляет статус обращения в базе данных (CSV).
    
    Args:
        ticket_number: Номер обращения
        status: Новый статус обращения (например, "в работе", "исполнено")
        admin_id: ID администратора, изменившего статус
        admin_name: Имя администратора, изменившего статус
    """
    csv_path = "data/reports.csv"
    
    try:
        df = pd.read_csv(csv_path)
        
        # Ищем запись с нужным номером обращения
        mask = df['ticket_number'] == int(ticket_number)  # Преобразуем в Python int
        if mask.any():
            df.loc[mask, 'status'] = status  # Обновляем статус обращения
            
            # Добавляем колонки для информации об администраторе, если их нет
            if 'last_modified_by_id' not in df.columns:
                df['last_modified_by_id'] = None
            if 'last_modified_by_name' not in df.columns:
                df['last_modified_by_name'] = None
            if 'last_modified_date' not in df.columns:
                df['last_modified_date'] = None
            
            # Обновляем информацию об администраторе
            if admin_id and admin_name:
                df.loc[mask, 'last_modified_by_id'] = admin_id
                df.loc[mask, 'last_modified_by_name'] = admin_name
                df.loc[mask, 'last_modified_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Сохраняем изменения обратно в CSV
            df.to_csv(csv_path, index=False)
            logger.info(f"✅ Статус обращения №{ticket_number} обновлен на '{status}'.")
            if admin_id and admin_name:
                logger.info(f"👤 Изменено администратором: {admin_name} (id: {admin_id})")
        else:
            logger.warning(f"⚠️ Обращение с номером {ticket_number} не найдено.")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении статуса обращения: {e}")

# auth_tg/bot.py
import os
import django
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async
import requests

# --- Настройка Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avezov_university.settings")
django.setup()

# --- Импорт функции для создания ссылки ---
from .utils import create_telegram_auth_link

# --- Логирование ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Настройка бота ---
API_TOKEN = "8437488119:AAFRIacDxPZa7zxySi52IL3c_WeQL0ozWzI"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- Кнопка для отправки контакта ---
phone_button = KeyboardButton('Отправить номер телефона', request_contact=True)
keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(phone_button)

# --- Команда /start ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    logging.info(f"Пользователь {message.from_user.id} запустил бота.")
    await message.answer("Отправьте номер телефона 👇", reply_markup=keyboard)

# --- Обработка контакта ---
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def contact_handler(message: types.Message):
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    first_name = message.contact.first_name
    last_name = message.contact.last_name or ""

    # Отправляем данные на Django
    r = requests.post(
        "http://127.0.0.1:8000/api/auth_tg/create_code-pg/",
        json={
            "phone": phone,
            "telegram_id": telegram_id,
            "first_name": first_name,
            "last_name": last_name
        }
    )

    if r.status_code != 200:
        await message.answer(f"Ошибка генерации кода: {r.text}")
        return

    data = r.json()
    link = data.get("link")

    if not link:
        await message.answer("Ошибка: ссылка не получена")
        return

    # Отправка кнопки с публичным URL
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="🔐 Перейти на сайт", url=link)
    )

    await message.answer(
        "Можно авторизоваться на сайте по ссылке 👇",
        reply_markup=keyboard
    )

# --- Функция запуска бота ---
async def main():
    logging.info("Бот запущен и начинает опрос...")
    await dp.start_polling(bot)

# --- Точка входа ---
if __name__ == "__main__":
    asyncio.run(main())
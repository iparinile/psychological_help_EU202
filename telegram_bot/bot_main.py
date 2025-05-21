import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import aiosqlite
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


# Функция для сохранения пользователя в базе данных
async def save_user(user_id, username):
    async with aiosqlite.connect('users.db') as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, dialogs TEXT)")
        await db.execute("INSERT OR REPLACE INTO users (id, username, dialogs) VALUES (?, ?, ?)",
                         (user_id, username, ''))
        await db.commit()
    logger.info(f"Пользователь {username} сохранён в базе данных")


# Получение токена из переменной окружения
bot_token = os.getenv('BOT_TOKEN')
if bot_token is None:
    raise ValueError("Токен бота не найден в переменных окружения")

# Инициализация бота и диспетчера
bot = Bot(token=bot_token)
dp = Dispatcher(storage=MemoryStorage())

# Создание роутера
router = Router()


# Команда для начала взаимодействия с ботом
@router.message(CommandStart())
async def start(message: types.Message) -> None:
    user = message.from_user
    await save_user(user.id, user.username)
    kb_list = [
        [KeyboardButton(text='Я чувствую себя подавленным')],
        [KeyboardButton(text='Мне нужна поддержка')],
        [KeyboardButton(text='Я хочу поговорить о своих чувствах')]
    ]
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:"
    )
    await message.answer("Привет! Я бот психологической поддержки. Выбери один из вариантов ниже, чтобы начать.",
                         reply_markup=reply_keyboard)


# Обработчик выбора промпта
@router.message()
async def choose_prompt(message: types.Message):
    if message.text in ['Я чувствую себя подавленным', 'Мне нужна поддержка', 'Я хочу поговорить о своих чувствах']:
        user_choice = message.text
        logger.info(f"Пользователь выбрал: {user_choice}")
        await message.answer(f"Ты выбрал '{user_choice}'. Теперь можешь рассказать подробнее.")


# Обработчик диалога
@router.message()
async def talk(message: types.Message):
    user_text = message.text
    logger.info(f"Пользователь сказал: {user_text}")
    await message.answer("Я слушаю тебя. Продолжай.")


async def main():
    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())

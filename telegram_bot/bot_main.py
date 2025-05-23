import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from dotenv import load_dotenv
import os
import json

# Импортируем функции из ai_service(относительный импорт)
from ..ai_service import initialize_dialogue, get_llm_response, get_book_recommendations

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем состояния для FSM
class UserStates(StatesGroup):
    choosing_issue = State()
    in_dialogue = State()

# Словарь для хранения активных диалогов пользователей
user_dialogues = {}

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
async def start(message: types.Message, state: FSMContext) -> None:
    user = message.from_user
    await save_user(user.id, user.username)
    
    kb_list = [
        [KeyboardButton(text='Я чувствую себя подавленным')],
        [KeyboardButton(text='Мне нужна поддержка на работе')],
        [KeyboardButton(text='У меня проблемы в отношениях')]
    ]
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите тип проблемы:"
    )
    
    await state.set_state(UserStates.choosing_issue)
    await message.answer("Привет! Я бот психологической поддержки. Выбери один из вариантов ниже, чтобы начать консультацию.",
                         reply_markup=reply_keyboard)

# Обработчик выбора проблемы
@router.message(UserStates.choosing_issue)
async def choose_issue(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    # Определяем issue_id на основе выбора пользователя
    issue_mapping = {
        'Я чувствую себя подавленным': '1',
        'Мне нужна поддержка на работе': '2', 
        'У меня проблемы в отношениях': '3'
    }
    
    issue_id = issue_mapping.get(message.text)
    
    if issue_id:
        logger.info(f"Пользователь {user_id} выбрал проблему: {message.text} (ID: {issue_id})")
        
        # Инициализируем диалог с AI сервисом
        try:
            dialogue_id = initialize_dialogue(issue_id, user_id)
            user_dialogues[user_id] = {
                'dialogue_id': dialogue_id,
                'issue_id': issue_id,
                'messages': []
            }
            
            # Получаем начальное сообщение от AI
            with open('ai_service/system_prompts.json', 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            initial_message = prompts[issue_id]["initial_message"]
            
            await state.set_state(UserStates.in_dialogue)
            await message.answer(initial_message, reply_markup=ReplyKeyboardRemove())
            
        except Exception as e:
            logger.error(f"Ошибка инициализации диалога: {e}")
            await message.answer("Произошла ошибка. Попробуйте начать заново с команды /start")
            await state.clear()
    else:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")

# Обработчик диалога с AI
@router.message(UserStates.in_dialogue) 
async def handle_dialogue(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user_text = message.text
    
    if user_id not in user_dialogues:
        await message.answer("Сессия завершена. Начните заново с команды /start")
        await state.clear()
        return
    
    dialogue_info = user_dialogues[user_id]
    issue_id = dialogue_info['issue_id']
    
    # Добавляем сообщение пользователя в историю
    dialogue_info['messages'].append({
        "role": "user",
        "content": user_text
    })
    
    logger.info(f"Пользователь {user_id} сказал: {user_text}")
    
    try:
        # Получаем ответ от AI
        # Формируем полную историю диалога (ограничиваем контекст для стабильности)
        with open('ai_service/system_prompts.json', 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        # Берем последние 10 сообщений чтобы не перегружать контекст
        recent_messages = dialogue_info['messages'][-10:] if len(dialogue_info['messages']) > 10 else dialogue_info['messages']
        
        full_messages = [
            {"role": "system", "content": prompts[issue_id]["system_prompt"]},
            {"role": "assistant", "content": prompts[issue_id]["initial_message"]}
        ] + recent_messages
        
        ai_response = get_llm_response(full_messages, user_id, issue_id)
        
        # Усиленная проверка корректности ответа от AI
        if (not ai_response or 
            ai_response.strip() in ['', '.', '...'] or 
            len(ai_response.strip()) < 10 or
            ai_response.startswith('.') or
            ai_response.count('?') > 5):  # Слишком много вопросов подряд
            
            logger.warning(f"AI вернул некорректный ответ: '{ai_response[:100]}'")
            ai_response = "Понимаю ваши переживания. Расскажите, пожалуйста, что сейчас вас больше всего беспокоит?"
        
        # Проверка на странные повторы и обрезанные ответы
        lines = ai_response.split('\n')
        if (len(lines) > 1 and 
            any(line.strip() == '.' for line in lines) or
            'Хорошо, давайте попробуем' in ai_response):
            
            logger.warning(f"AI дал странный/обрезанный ответ: {ai_response[:100]}")
            ai_response = "Понимаю, что вам сейчас непросто. Давайте сосредоточимся на ваших ощущениях. Что сейчас вас больше всего тревожит?"
        
        # Проверка на выход из роли (если AI начинает говорить о себе как о модели)
        problematic_phrases = [
            "языковая модель", "модель google", "я ai", "я искусственный", 
            "я бот", "я не психолог", "я не имею квалификации", "я всего лишь"
        ]
        
        if any(phrase in ai_response.lower() for phrase in problematic_phrases):
            logger.warning(f"AI вышел из роли психолога: {ai_response[:100]}")
            ai_response = "Давайте сосредоточимся на ваших переживаниях. Что сейчас вас больше всего беспокоит?"
        
        # Добавляем ответ AI в историю
        dialogue_info['messages'].append({
            "role": "assistant", 
            "content": ai_response
        })
        
        await message.answer(ai_response)
        
        # Если AI сам предложил книги в ответе, добавляем кнопку
        books_trigger_phrases = ["могу порекомендовать", "есть отличные книги", "полезные книги", "книги по этой теме"]
        if any(phrase in ai_response.lower() for phrase in books_trigger_phrases):
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 Да, покажите рекомендации", callback_data=f"books_{user_id}")]
            ])
            await message.answer("Хотите получить персональные рекомендации?", reply_markup=inline_kb)
        
        # Предлагаем кнопку с рекомендациями после 3-4 сообщений (когда пользователь уже рассказал о проблеме)  
        else:
            user_messages_count = len([msg for msg in dialogue_info['messages'] if msg['role'] == 'user'])
            
            if user_messages_count == 3:  # После 3-го сообщения пользователя
                inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📚 Получить рекомендации книг", callback_data=f"books_{user_id}")]
                ])
                await message.answer("💡 Кстати, если хотите, я могу подобрать для вас полезные книги и ресурсы по вашей теме", reply_markup=inline_kb)
        
    except Exception as e:
        logger.error(f"Ошибка получения ответа от AI: {e}")
        await message.answer("Извините, произошла техническая ошибка. Я психолог-бот и хочу вам помочь. Можете повторить ваш вопрос или попробовать начать заново с /start")

# Обработчик inline кнопки для рекомендаций книг
@router.callback_query(lambda callback: callback.data.startswith('books_'))
async def handle_books_callback(callback: types.CallbackQuery):
    await callback.answer()  # Убираем "часики" на кнопке
    
    user_id = callback.data.split('_')[1]
    
    # Проверяем, есть ли активный диалог
    if user_id not in user_dialogues:
        await callback.message.answer("Сессия завершена. Начните заново с команды /start")
        return
    
    dialogue_info = user_dialogues[user_id]
    issue_id = dialogue_info['issue_id']
    
    try:
        # Формируем полную историю диалога для рекомендаций
        with open('ai_service/system_prompts.json', 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        full_messages = [
            {"role": "system", "content": prompts[issue_id]["system_prompt"]},
            {"role": "assistant", "content": prompts[issue_id]["initial_message"]}
        ] + dialogue_info['messages']
        
        # Получаем рекомендации
        recommendations = get_book_recommendations(
            dialogue_info['dialogue_id'],
            user_id,
            issue_id,
            full_messages
        )
        
        # Проверяем, что рекомендации не пустые
        if recommendations and (recommendations.get("books") or recommendations.get("resources")):
            from ai_service.ai_books import format_recommendations
            formatted_recs = format_recommendations(recommendations)
            
            # Проверяем, что форматированные рекомендации не пустые
            if len(formatted_recs.strip()) > 50:
                await callback.message.answer(f"📚 Персональные рекомендации для вас:\n\n{formatted_recs}")
            else:
                # Предлагаем повторить попытку
                retry_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data=f"books_{user_id}")]
                ])
                await callback.message.answer("К сожалению, не удалось сформировать рекомендации. Это может быть временная проблема с сервисом.", reply_markup=retry_kb)
        else:
            # Предлагаем повторить попытку  
            retry_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать еще раз", callback_data=f"books_{user_id}")]
            ])
            await callback.message.answer("К сожалению, не удалось получить рекомендации. Это может быть временная проблема с AI сервисом.", reply_markup=retry_kb)
        
    except Exception as e:
        logger.error(f"Ошибка получения рекомендаций по кнопке: {e}")
        await callback.message.answer("Извините, произошла ошибка при получении рекомендаций.")

async def main():
    dp.include_router(router)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())

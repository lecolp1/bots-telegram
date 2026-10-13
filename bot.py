import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv  
from google import genai  # Импортируем библиотеку ИИ от Google

# Импортируем наш модуль базы данных
import database as db  

# Загружаем переменные окружения из .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализируем клиента ИИ (если ключ добавлен)
ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# Промпт — жесткая инструкция для ИИ, как себя вести с клиентом
AI_INSTRUCTION = (
    "Ты — дружелюбный ИИ-менеджер по продажам для нашего сервиса услуг. "
    "Твоя задача — отвечать на вопросы клиентов вежливо, кратко и помогать им определиться с выбором. "
    "Вот наш актуальный прайс-лист: 1) Поиграть в фортнайт — 300 грн, 2) Посмотреть видео — 200 грн, "
    "3) Посидеть в дискорде (дс) — 450 грн. Наш адрес: ул. Пушкина, дом Колотушкина, 1. "
    "Если клиент хочет сделать заказ, вежливо напомни ему нажать на кнопку 'Оставить заявку' в меню. "
    "Отвечай всегда на русском языке, используй эмодзи, пиши емко (не более 3-4 предложений)."
)

# Главное меню бота
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Прайс"), KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="📝 Оставить заявку")],
    ],
    resize_keyboard=True,
)

class Form(StatesGroup):
    name = State()
    phone = State()


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Я твой умный ИИ-помощник. Выбери пункт меню или просто задай мне любой вопрос чате!", reply_markup=menu)


@dp.message(F.text == "📝 Оставить заявку")
async def request(message: types.Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Как вас зовут?", reply_markup=ReplyKeyboardRemove())


@dp.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.phone)
    await message.answer("Напишите ваш номер телефона:")


@dp.message(Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    phone = message.text
    username = message.from_user.username or "нет username"
    
    db.add_request(user_id=message.from_user.id, username=username, name=name, phone=phone)
    await state.clear()

    if ADMIN_ID:
        text = f"🔔 Новая заявка в базе данных!\nИмя: {name}\nТелефон: {phone}\nTelegram: @{username}"
        await bot.send_message(ADMIN_ID, text)
        
    await message.answer("Спасибо! Мы скоро свяжемся с вами.", reply_markup=menu)


@dp.message(F.text == "💰 Прайс")
async def price(message: types.Message):
    await message.answer("Поиграть в фортнайт — 300 грн\nпосмотреть видео — 200 грн\nпосидеть в дсе — 450 грн")


@dp.message(F.text == "📞 Контакты")
async def contacts(message: types.Message):
    await message.answer("Адрес: ул. пушкина дом колотушкина, 1\nТелефон: не знаю")


@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для выполнения этой команды. ❌")
        return

    requests = db.get_all_requests()
    if not requests:
        await message.answer("📭 База данных заявок пока пуста.")
        return
    
    response = "📊 **СПИСОК ВСЕХ ЗАЯВОК ИЗ БАЗЫ:**\n\n"
    for req in requests:
        req_id, username, name, phone, date = req
        clean_date = date.split(".") if "." in date else date
        response += f"🆔 Заявка №{req_id} ({clean_date})\n👤 Имя: {name}\n📞 Тел: {phone}\n🔗 TG: @{username}\n\n"
    await message.answer(response)


# ОБРАБОТЧИК ЛЮБЫХ ТЕКСТОВЫХ СООБЩЕНИЙ (ИНТЕГРАЦИЯ ИИ)
@dp.message(F.text)
async def ai_chat_handler(message: types.Message):
    if not ai_client:
        await message.answer("Извините, модуль искусственного интеллекта сейчас отключен. 😔")
        return

    # Отправляем анимацию «Бот печатает...», чтобы пользователь видел, что ИИ думает
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        # Делаем асинхронный вызов к нейросети в отдельном потоке, чтобы бот не зависал
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=message.text,
                config=genai.types.GenerateContentConfig(
                    system_instruction=AI_INSTRUCTION, # Наш промпт-роль
                    temperature=0.7 # Уровень креативности ИИ
                )
            )
        )
        await message.answer(response.text)
        
    except Exception as e:
        await message.answer("Упс, у меня возникла небольшая ошибка при обработке мыслей. Попробуйте еще раз! 🤖")
        print(f"Ошибка ИИ: {e}")


async def main():
    db.init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

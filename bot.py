import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv  

import database as db  

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню бота
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Прайс"), KeyboardButton(text="📞 Contacts")],
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
    await message.answer("Привет! Выбери, что тебя интересует:", reply_markup=menu)


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
    
    db.add_request(
        user_id=message.from_user.id,
        username=username,
        name=name,
        phone=phone
    )
    
    await state.clear()

    if ADMIN_ID:
        text = (
            "🔔 Новая заявка в базе данных!\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Telegram: @{username}"
        )
        await bot.send_message(ADMIN_ID, text)
        
    await message.answer("Спасибо! Мы скоро свяжемся с вами.", reply_markup=menu)


@dp.message(F.text == "💰 Прайс")
async def price(message: types.Message):
    await message.answer("Поиграть в фортнайт — 300 грн\nпосмотреть видео — 200 грн\nпосидеть в дсе — 450 грн")


@dp.message(F.text == "📞 Contacts")
async def contacts(message: types.Message):
    await message.answer("Адрес: ул. пушкина дом колотушкина, 1\nТелефон: не знаю")


# 3. СЕКРЕТНАЯ КОМАНДА ДЛЯ АДМИНИСТРАТОРА
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
        clean_date = date.split(".")[0] if "." in date else date
        response += f"🆔 Заявка №{req_id} ({clean_date})\n👤 Имя: {name}\n📞 Тел: {phone}\n🔗 TG: @{username}\n\n"
        
    await message.answer(response)


async def main():
    db.init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

TOKEN = "8794866032:AAH1QDNsaTPZdvN8AdRh42Lq25DeKdQ_dRg"
ADMIN_ID = 945758539  # ваш ID, число без кавычек

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
    await message.answer("Привет! Выбери, что тебя интересует:", reply_markup=menu)


@dp.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.phone)
    await message.answer("Напишите ваш номер телефона:")


@dp.message(Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    text = (
        "🔔 Новая заявка!\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {message.text}\n"
        f"Telegram: @{message.from_user.username or 'нет username'}"
    )
    await bot.send_message(ADMIN_ID, text)
    await message.answer("Спасибо! Мы скоро свяжемся с вами.", reply_markup=menu)


@dp.message(F.text == "💰 Прайс")
async def price(message: types.Message):
    await message.answer("Поиграть в фортнайт — 300 грн\nпосмотреть видео — 200 грн\nпосидеть в дсе — 450 грн")


@dp.message(F.text == "📞 Контакты")
async def contacts(message: types.Message):
    await message.answer("Адрес: ул. пушкина дом колотушкина, 1\nТелефон: не знаю")


@dp.message(F.text == "📝 Оставить заявку")
async def request(message: types.Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Как вас зовут?", reply_markup=ReplyKeyboardRemove())


async def main():
    await dp.start_polling(bot)


asyncio.run(main())
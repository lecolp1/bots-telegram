import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice
from dotenv import load_dotenv  
from google import genai  

import database as db  

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PAY_TOKEN = os.getenv("PAYMENT_TOKEN") # Наш токен оплаты

bot = Bot(token=TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

AI_INSTRUCTION = (
    "Ты — дружелюбный ИИ-менеджер по продажам для нашего сервиса услуг. "
    "Твоя задача — отвечать на вопросы клиентов вежливо, кратко и помогать им определиться с выбором. "
    "Вот наш актуальный прайс-лист: 1) Поиграть в фортнайт — 300 грн, 2) Посмотреть видео — 200 грн, "
    "3) Посидеть в дискорде (дс) — 450 грн. Наш адрес: ул. Пушкина, дом Колотушкина, 1. "
    "Если клиент хочет сделать заказ, вежливо напомни ему нажать на кнопку 'Оставить заявку' в меню. "
    "Отвечай всегда на русском языке, используй эмодзи, пиши емко (не более 3-4 предложений)."
)

# Меню с кнопкой быстрой покупки
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Прайс"), KeyboardButton(text="🛒 Купить услугу")],
        [KeyboardButton(text="📝 Оставить заявку"), KeyboardButton(text="📞 Контакты")],
    ],
    resize_keyboard=True,
)

# Инлайн-клавиатура для выбора товара при покупке
products_keyboard = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [types.InlineKeyboardButton(text="🎮 Фортнайт (300 грн)", callback_data="buy_fortnite")],
        [types.InlineKeyboardButton(text="🎬 Посмотреть видео (200 грн)", callback_data="buy_video")],
        [types.InlineKeyboardButton(text="🎧 Посидеть в ДС (450 грн)", callback_data="buy_ds")],
    ]
)

class Form(StatesGroup):
    name = State()
    phone = State()


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Я твой умный ИИ-помощник. Выбери пункт меню или задай вопрос!", reply_markup=menu)


# КНОПКА КУПИТЬ УСЛУГУ — ВЫВОДИТ ИНЛАЙН-КНОПКИ
@dp.message(F.text == "🛒 Купить услугу")
async def show_shop(message: types.Message):
    await message.answer("Выбери услугу, которую хочешь оплатить прямо сейчас:", reply_markup=products_keyboard)


# ОБРАБОТКА НАЖАТИЯ НА ИНЛАЙН-КНОПКИ ОПЛАТЫ
@dp.callback_query(F.data.startswith("buy_"))
async def send_payment_invoice(callback: types.CallbackQuery):
    if not PAY_TOKEN:
        await callback.answer("Настройка платежной системы не завершена.", show_alert=True)
        return

    # Определяем товар и цену в зависимости от нажатой кнопки
    if callback.data == "buy_fortnite":
        title, desc, price_amount = "Игра в Fortnite", "Час совместной игры в Фортнайт", 300
    elif callback.data == "buy_video":
        title, desc, price_amount = "Просмотр видео", "Совместный просмотр вашего видеоролика", 200
    else:
        title, desc, price_amount = "Сессия в Discord", "Час общения в голосовом канале Discord", 450

    await callback.message.answer("Генерирую счет на оплату... ⏳")
    
    # Отправляем официальный счет (Инвойс) в чат
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title,
        description=desc,
        payload=f"payload_{callback.data}", # Скрытые данные для проверки платежа
        provider_token=PAY_TOKEN,
        currency="UAH", # Валюта (можно поменять на RUB, USD и т.д.)
        prices=[LabeledPrice(label=title, amount=price_amount * 100)], # Сумма в копейках (300 * 100)
        start_parameter="bot-service-payment"
    )
    await callback.answer()


# ОБЯЗАТЕЛЬНЫЙ ЭТАП: Сервер Telegram спрашивает бота, всё ли в порядке перед списанием денег
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery):
    # Здесь можно провести финальную проверку наличия товара. Если всё ок — подтверждаем:
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


# ХЭНДЛЕР УСПЕШНОЙ ОПЛАТЫ (Срабатывает сразу после ввода карты)
@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    payment_info = message.successful_payment
    
    # Определяем, какой именно товар был оплачен по payload
    payload = payment_info.invoice_payload
    item_name = "Неизвестный товар"
    if "fortnite" in payload: item_name = "Игра в Fortnite"
    elif "video" in payload: item_name = "Просмотр видео"
    elif "ds" in payload: item_name = "Сессия в Discord"

    price_paid = payment_info.total_amount // 100 # Переводим обратно из копеек

    # 1. ЗАПИСЫВАЕМ ПОКУПКУ В БАЗУ ДАННЫХ СО СТАТУСОМ ОПЛАЧЕНО (is_paid=1)
    db.add_request(
        user_id=message.from_user.id,
        username=message.from_user.username or "нет username",
        name=message.from_user.first_name,
        phone="Оплачено через TG",
        item_name=item_name,
        price=price_paid,
        is_paid=1
    )

    await message.answer(f"🎉 Оплата прошла успешно! Вы приобрели: **{item_name}**.\nАдминистратор уже уведомлен и скоро свяжется с вами!", reply_markup=menu)

    # 2. УВЕДОМЛЯЕМ АДМИНА О РЕАЛЬНЫХ ДЕНЬГАХ
    if ADMIN_ID:
        text = (
            "💰💸 **ПОСТУПИЛА ОПЛАТА!** 💸💰\n\n"
            f"🛒 Товар: {item_name}\n"
            f"💵 Сумма: {price_paid} UAH\n"
            f"👤 Покупатель: {message.from_user.first_name}\n"
            f"🔗 TG: @{message.from_user.username or 'нет username'}"
        )
        await bot.send_message(ADMIN_ID, text)


# ОСТАЛЬНЫЕ КНОПКИ (Оставить заявку, Прайс, Контакты)
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
    
    # Обычная заявка (не оплаченная, цена 0)
    db.add_request(user_id=message.from_user.id, username=username, name=name, phone=phone, item_name="Обычная заявка", price=0, is_paid=0)
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
    
    response = "📊 **СПИСОК ВСЕХ ЗАЯВОК И ОПЛАТ ИЗ БАЗЫ:**\n\n"
    for req in requests:
        req_id, username, name, phone, item_name, price, is_paid, date = req
        status = "✅ ОПЛАЧЕНО" if is_paid == 1 else "⏳ Заявка"
        clean_date = date.split(".") if "." in date else date
        response += f"🆔 №{req_id} [{status}] ({clean_date})\n🛒 Услуга: {item_name} ({price} UAH)\n👤 Клиент: {name}\n📞 Тел: {phone}\n🔗 TG: @{username}\n\n"
    await message.answer(response)


# ОБРАБОТЧИК ИИ
@dp.message(F.text)
async def ai_chat_handler(message: types.Message):
    if not ai_client:
        await message.answer("Извините, модуль искусственного интеллекта сейчас отключен. 😔")
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    for attempt in range(3):
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: ai_client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=message.text,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=AI_INSTRUCTION,
                        temperature=0.7
                    )
                )
            )
            await message.answer(response.text)
            return
            
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                await asyncio.sleep(1.5)
                continue
            await message.answer("Упс, сервера ИИ сейчас перегружены. Попробуйте написать через минутку! 🤖")
            print(f"Ошибка ИИ: {e}")
            break


async def main():
    db.init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

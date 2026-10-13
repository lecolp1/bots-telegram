# 🤖 Асинхронный Telegram-бот с ИИ-ассистентом и платежной системой

Профессиональный Telegram-бот на **aiogram 3** для автоматизации продаж, объединяющий прайс-лист, ИИ-менеджера (Google Gemini) и прием платежей.

## 🛠 Технологии
* **Python 3.12+**, **aiogram 3.x**, **google-genai (Gemini)**, **SQLite3**, **python-dotenv**

## 🚀 Основной функционал
* 🧠 **ИИ-Менеджер** (Gemini) для живого диалога с клиентами.
* 💳 **Встроенная оплата** через ЮKassa и счета в чате.
* 📝 **FSM** для сбора контактов.
* 📊 **SQLite** для учета заявок и транзакций с отметками об оплате.
* 👑 **Админ-панель** (`/admin`) для просмотра заказов.

## 💻 Установка и запуск
1. Клонирование и настройка окружения:
   ```bash
   git clone https://github.com
   cd bots-telegram
   python -m venv venv && source venv/bin/activate  # или venv\Scripts\activate для Windows
   pip install -r requirements.txt
   ```
2. Создайте `.env` с ключами `BOT_TOKEN`, `ADMIN_ID`, `GEMINI_API_KEY`, `PAYMENT_TOKEN`.
3. Запуск: `python bot.py`

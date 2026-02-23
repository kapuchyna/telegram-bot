import os
import time
import telebot
from telebot import types, apihelper

# ================= НАСТРОЙКИ =================

TOKEN = "8358989018:AAH67ZtDtR5d_sv-DjfAZN76ZkDOkhY4LmM" # Railway Variable
ADMIN_ID = 617404776

CHANNEL_USERNAME = "@yerimbetde"  # ← ВСТАВЬ СВОЙ КАНАЛ

apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

pending_users = {}

# ================= ТЕКСТЫ =================

START_TEXT = """
Здравствуйте! 👋

Это бот для покупки брифа для дизайнеров.

Вы получаете готовый рабочий документ, который поможет
четко ставить задачи, фиксировать пожелания клиента
и экономить часы на правках.

Одна покупка — и бриф навсегда у Вас в Google Docs / PDF.
"""

PRICE_TEXT = """
📦 <b>Тариф:</b> «Стандарт»
💰 <b>Цена:</b> 30 000 тг (единоразово)

📄 <b>Состав:</b>
— Готовый шаблон брифа
— Доступ на редактирование/скачивание
— Можно использовать для любого количества проектов

⏳ <b>Срок доступа:</b> бессрочно
"""

PAY_TEXT = """
💳 <b>Как оплатить:</b>

Перевод на карту Казахстан

🏦 <b>Реквизиты:</b>
Карта: <code>4400 4303 3800 4382</code>
Получатель: <b>NAGYZKHAN YERIMBET</b>

📝 В комментарии к переводу укажите:
<code>@ваш_telegram_username</code>

📸 После оплаты отправьте скриншот чека сюда.
"""

SUCCESS_TEXT = """
✅ Оплата подтверждена!

Вот Ваша одноразовая ссылка для доступа:

{link}

Если ссылка не откроется — напишите администратору.
"""

WAIT_TEXT = """
Спасибо! ✅

Ваш чек отправлен на проверку.
После подтверждения оплаты Вы получите ссылку автоматически.
"""

# ================= МЕНЮ =================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💰 Прайс", "💳 Оплата")
    kb.add("❓ Вопрос")
    return kb


# ================= СТАРТ =================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, START_TEXT, reply_markup=main_menu())


# ================= КНОПКИ =================

@bot.message_handler(func=lambda m: m.text == "💰 Прайс")
def price(message):
    bot.send_message(message.chat.id, PRICE_TEXT)


@bot.message_handler(func=lambda m: m.text == "💳 Оплата")
def pay(message):
    bot.send_message(message.chat.id, PAY_TEXT)


@bot.message_handler(func=lambda m: m.text == "❓ Вопрос")
def question(message):
    bot.send_message(
        ADMIN_ID,
        f"❓ Вопрос от @{message.from_user.username}:\n{message.text}"
    )
    bot.send_message(message.chat.id, "Ваш вопрос отправлен администратору.")


# ================= ПОЛУЧЕНИЕ ЧЕКА =================

@bot.message_handler(content_types=['photo'])
def receipt(message):

    user_id = message.from_user.id
    username = message.from_user.username or "нет username"
    name = message.from_user.first_name

    pending_users[user_id] = True

    caption = (
        f"🧾 Новый чек\n"
        f"Имя: {name}\n"
        f"Username: @{username}\n"
        f"ID: {user_id}"
    )

    markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton(
        "✅ Подтвердить",
        callback_data=f"approve_{user_id}"
    )
    markup.add(approve_btn)

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=markup
    )

    bot.send_message(message.chat.id, WAIT_TEXT)


# ================= ПОДТВЕРЖДЕНИЕ АДМИНОМ =================

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_payment(call):

    if call.from_user.id != ADMIN_ID:
        return

    user_id = int(call.data.split("_")[1])

    try:
        chat = bot.get_chat(CHANNEL_USERNAME)

        invite = bot.create_chat_invite_link(
            chat.id,
            member_limit=1
        )

        link = invite.invite_link

        bot.send_message(
            user_id,
            SUCCESS_TEXT.format(link=link)
        )

        bot.answer_callback_query(call.id, "Ссылка отправлена")

    except Exception as e:
        bot.send_message(ADMIN_ID, f"Ошибка: {e}")


# ================= ЗАПУСК =================

print("Bot started...")

bot.infinity_polling()

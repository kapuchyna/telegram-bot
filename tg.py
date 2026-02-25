import re
import time
import telebot
from telebot import types, apihelper

# ================== НАСТРОЙКИ ==================
TOKEN = "8358989018:AAH67ZtDtR5d_sv-DjfAZN76ZkDOkhY4LmM"
ADMIN_ID = 617404776  # ваш новый admin id (число)

PRICE = 30000

CARD_NUMBER = "4400430338004382"
CARD_HOLDER = "NAGYZKHAN YERIMBET"

# Если хотите вести в канал после подтверждения:
# 1) если канал публичный: "@yourchannel"
# 2) если приватный: "https://t.me/+XXXXXXXXXXXX" (инвайт-ссылка)
CHANNEL_LINK = "https://t.me/+_8uSxwltJ_piYWQ6"  # поменяйте на свой реальный линк

# Таймауты (чтобы меньше таймаутов)
apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Состояния: ждём чек от пользователя
pending_users = {}  # user_id -> True


# ================== УТИЛИТЫ ==================
def norm(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    # убрать эмодзи/символы в начале (например "📄 " / "💰 ")
    t = re.sub(r"^[^\wа-яё]+", "", t, flags=re.IGNORECASE)
    # убрать лишние пробелы
    t = re.sub(r"\s+", " ", t)
    return t


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 Прайс", "📄 Оплата и условия")
    kb.row("✅ Я оплатил(-а)")
    return kb


START_TEXT = (
    "Здравствуйте! 👋\n\n"
    "Это бот для покупки брифа для дизайнеров.\n\n"
    "Выберите действие в меню ниже:"
)

PRICE_TEXT = (
    "💰 <b>Прайс</b>\n\n"
    "📦 <b>Тариф:</b> «Стандарт»\n"
    f"💵 <b>Цена:</b> {PRICE} тг (единоразово)\n\n"
    "📄 <b>Состав:</b>\n"
    "— Готовый шаблон брифа (ссылка на документ)\n"
    "— Доступ на редактирование и скачивание\n"
    "— Можно использовать для любого количества проектов\n\n"
    "⏳ <b>Срок доступа:</b> бессрочно"
)

PAYMENT_TEXT = (
    "📄 <b>Оплата и условия</b>\n\n"
    f"💳 Реквизиты: <code>{CARD_NUMBER}</code>\n"
    f"👤 Получатель: <b>{CARD_HOLDER}</b>\n"
    f"💰 Сумма: <b>{PRICE} тг</b>\n\n"
    "После оплаты нажмите <b>✅ Я оплатил(-а)</b> и отправьте чек (скрин/фото)."
)

# ================== КОМАНДЫ ==================
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, START_TEXT, reply_markup=main_menu())


# ================== КНОПКИ (ВАЖНО: ВЫШЕ ОБЩЕГО HANDLER) ==================
@bot.message_handler(func=lambda m: norm(m.text) in ["прайс"])
def price(m):
    bot.send_message(m.chat.id, PRICE_TEXT, reply_markup=main_menu())


@bot.message_handler(func=lambda m: norm(m.text) in ["оплата и условия", "оплата", "условия"])
def pay_conditions(m):
    bot.send_message(m.chat.id, PAYMENT_TEXT, reply_markup=main_menu())


@bot.message_handler(func=lambda m: norm(m.text) in ["я оплатил(-а)", "я оплатил", "я оплатила"])
def i_paid(m):
    pending_users[m.from_user.id] = True
    bot.send_message(
        m.chat.id,
        "Спасибо! ✅\nПожалуйста, отправьте <b>чек/скрин оплаты</b> (фото).",
        reply_markup=main_menu()
    )


# ================== ЧЕК (ФОТО) ==================
@bot.message_handler(content_types=["photo"])
def handle_receipt(m):
    # принимаем фото только если пользователь нажал "Я оплатил(-а)"
    if not pending_users.get(m.from_user.id):
        bot.send_message(
            m.chat.id,
            "Если это чек, сначала нажмите <b>✅ Я оплатил(-а)</b>.",
            reply_markup=main_menu()
        )
        return

    user = m.from_user
    username = f"@{user.username}" if user.username else "нет username"

    caption = (
        "🧾 <b>Новый чек</b>\n"
        f"👤 Пользователь: <b>{user.first_name}</b>\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"💰 Сумма: <b>{PRICE} тг</b>\n\n"
        "✅ Статус: <i>ожидает подтверждения</i>\n\n"
        "Чтобы подтвердить — ответьте пользователю вручную или напишите ему в ЛС."
    )

    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=caption)
    bot.send_message(m.chat.id, "Спасибо! Сообщение передано администратору ✅", reply_markup=main_menu())

    pending_users.pop(m.from_user.id, None)


# ================== ПОДТВЕРЖДЕНИЕ (ТОЛЬКО ДЛЯ АДМИНА) ==================
# Админ пишет: /approve 123456789
@bot.message_handler(commands=["approve"])
def approve(m):
    if m.from_user.id != ADMIN_ID:
        return

    parts = m.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.send_message(m.chat.id, "Использование: <code>/approve USER_ID</code>")
        return

    user_id = int(parts[1])
    bot.send_message(
        user_id,
        "✅ Оплата подтверждена!\n\n"
        f"Вот ваш доступ: {CHANNEL_LINK}\n\n"
        "Если ссылка не открывается — напишите, пожалуйста, администратору.",
    )
    bot.send_message(m.chat.id, f"Готово ✅ Пользователю отправлен доступ: <code>{user_id}</code>")


# ================== ОБЩИЙ HANDLER (ПОСЛЕДНИМ!) ==================
@bot.message_handler(content_types=["text"])
def other_text(m):
    # Если человек пишет что-то другое — пересылаем админу как вопрос
    user = m.from_user
    username = f"@{user.username}" if user.username else "нет username"

    caption = (
        "📩 <b>Сообщение от пользователя</b>\n"
        f"👤 {user.first_name}\n"
        f"🔗 {username}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"💬 Текст: {m.text}"
    )

    bot.send_message(ADMIN_ID, caption)
    bot.send_message(m.chat.id, "Спасибо! Сообщение передано администратору ✅", reply_markup=main_menu())


# ================== ЗАПУСК ==================
if __name__ == "__main__":
    print("Bot started...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)
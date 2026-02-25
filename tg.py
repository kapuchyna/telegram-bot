import time
import telebot
from telebot import types, apihelper

# ================== НАСТРОЙКИ ==================
TOKEN = "8358989018:AAH67ZtDtR5d_sv-DjfAZN76ZkDOkhY4LmM"  # 123456:ABC...
ADMIN_ID = 617404776                 # ваш Telegram ID

# Канал:
# Если приватный — лучше CHANNEL_ID = -100...
# Если публичный — CHANNEL_USERNAME = "@..."
CHANNEL_ID = -1003637167736
CHANNEL_USERNAME = "@yerimbetde"

PAYMENT_REQUISITES = "4400430338004382\nNAGYZKHAN YERIMBET"
PRICE = 30000

apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================== СОСТОЯНИЯ ==================
accepted_terms = set()
waiting_receipt = set()
pending = {}  # uid -> {"chat_id": ...}

# ================== ТЕКСТЫ ==================
START_TEXT = (
    "Здравствуйте! 👋\n\n"
    "Выберите действие кнопками ниже."
)

PRICE_TEXT = (
    f"<b>💰 Прайс</b>\n\n"
    f"📦 Тариф: <b>Стандарт</b>\n"
    f"💵 Цена: <b>{PRICE} тг</b> (единоразово)\n\n"
    f"<b>Состав:</b>\n"
    f"— Готовый шаблон брифа (ссылка на документ)\n"
    f"— Доступ на редактирование и скачивание\n"
    f"— Можно использовать для любого количества проектов\n"
    f"⏳ Срок доступа: бессрочно"
)

TERMS_TEXT = (
    "<b>📄 Условия</b>\n\n"
    "1) Оплата производится единоразово.\n"
    "2) После подтверждения оплаты вы получаете доступ.\n"
    "3) Доступ предоставляется только одному аккаунту.\n"
    "4) Возврат средств не предусмотрен.\n\n"
    "Нажмите кнопку ниже, чтобы подтвердить согласие."
)

PAYMENT_TEXT = (
    "<b>💳 Оплата</b>\n\n"
    f"Сумма к оплате: <b>{PRICE} тг</b>\n\n"
    "<b>Реквизиты:</b>\n"
    f"<code>{PAYMENT_REQUISITES}</code>\n\n"
    "После оплаты нажмите <b>✅ Я оплатил(-а)</b> и отправьте чек (скриншот)."
)

# ================== КЛАВИАТУРЫ ==================
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💳 Оплата и условия", "💰 Прайс")
    kb.row("✅ Я оплатил(-а)")
    return kb

def accept_terms_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Принимаю условия", callback_data="accept_terms_and_show_payment"))
    return kb

def admin_review_kb(user_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve:{user_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{user_id}")
    )
    return kb

def channel_target():
    return CHANNEL_ID if CHANNEL_ID else CHANNEL_USERNAME

# ================== КОМАНДЫ ==================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, START_TEXT, reply_markup=main_menu_kb())

# Прайс
@bot.message_handler(func=lambda m: (m.text or "").strip().lower() in ["прайс", "💰 прайс"])
def show_price(message):
    bot.send_message(message.chat.id, PRICE_TEXT, reply_markup=main_menu_kb())

# ОПЛАТА И УСЛОВИЯ (ОДНА КНОПКА)
@bot.message_handler(func=lambda m: "оплата" in (m.text or "").lower())
def show_terms_first(message):
    uid = message.from_user.id
    # Всегда сначала показываем условия + кнопку согласия
    bot.send_message(message.chat.id, TERMS_TEXT, reply_markup=accept_terms_kb())

# Нажали "Принимаю условия" -> отмечаем + сразу показываем оплату
@bot.callback_query_handler(func=lambda call: call.data == "accept_terms_and_show_payment")
def accept_terms_and_show_payment(call):
    uid = call.from_user.id
    accepted_terms.add(uid)
    bot.answer_callback_query(call.id, "Условия приняты ✅")
    bot.send_message(call.message.chat.id, "Спасибо! Условия приняты ✅")
    bot.send_message(call.message.chat.id, PAYMENT_TEXT, reply_markup=main_menu_kb())

# "Я оплатил(-а)" -> просим чек (без суммы, т.к. фиксированная)
@bot.message_handler(func=lambda m: (m.text or "").strip().lower() in ["✅ я оплатил(-а)", "я оплатил(-а)"])
def i_paid(message):
    uid = message.from_user.id
    if uid not in accepted_terms:
        bot.send_message(message.chat.id, "Сначала откройте <b>💳 Оплата и условия</b> и примите условия ✅")
        return

    waiting_receipt.add(uid)
    bot.send_message(message.chat.id, "Пожалуйста, отправьте чек (скриншот) одним сообщением 📸")

# Приём чека
@bot.message_handler(content_types=["photo", "document"])
def receipt(message):
    uid = message.from_user.id
    if uid not in waiting_receipt:
        return

    waiting_receipt.discard(uid)

    username = ("@" + message.from_user.username) if message.from_user.username else "(username отсутствует)"
    caption = (
        "<b>🧾 Новый чек</b>\n"
        f"Пользователь: <b>{message.from_user.first_name}</b> {username}\n"
        f"User ID: <code>{uid}</code>\n"
        f"Сумма: <b>{PRICE} тг</b>\n\n"
        "Нажмите кнопку для решения:"
    )

    pending[uid] = {"chat_id": message.chat.id}

    try:
        if message.content_type == "photo":
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=admin_review_kb(uid))
        else:
            bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=admin_review_kb(uid))

        bot.send_message(message.chat.id, "Спасибо! Сообщение передано администратору ✅")
    except Exception:
        bot.send_message(message.chat.id, "Не удалось отправить администратору. Проверьте ADMIN_ID и что админ писал боту хотя бы 1 раз.")

# Решение админа
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve:") or call.data.startswith("reject:"))
def admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет доступа.")
        return

    action, user_id_str = call.data.split(":")
    uid = int(user_id_str)

    if uid not in pending:
        bot.answer_callback_query(call.id, "Заявка не найдена/устарела.")
        return

    user_chat_id = pending[uid]["chat_id"]

    if action == "reject":
        bot.answer_callback_query(call.id, "Отклонено.")
        bot.send_message(user_chat_id, "❌ Оплата не подтверждена. Пожалуйста, отправьте чек заново.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        pending.pop(uid, None)
        return

    bot.answer_callback_query(call.id, "Подтверждено ✅")

    try:
        if CHANNEL_ID:
            invite = bot.create_chat_invite_link(chat_id=CHANNEL_ID, member_limit=1)
            link = invite.invite_link
            bot.send_message(user_chat_id, f"✅ Оплата подтверждена.\nВаша одноразовая ссылка на канал:\n{link}")
        else:
            bot.send_message(user_chat_id, f"✅ Оплата подтверждена.\nСсылка на канал:\n{CHANNEL_USERNAME}")

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        pending.pop(uid, None)
    except Exception:
        bot.send_message(user_chat_id, "✅ Оплата подтверждена.\nНо не удалось выдать доступ автоматически. Администратор добавит вас вручную.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        pending.pop(uid, None)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
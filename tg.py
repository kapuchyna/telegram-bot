import time
import telebot
from telebot import types, apihelper

# ================== НАСТРОЙКИ ==================
TOKEN = "8358989018:AAH67ZtDtR5d_sv-DjfAZN76ZkDOkhY4LmM"  # например: 123456:ABC-DEF...
ADMIN_ID = 617404776                 # ваш Telegram ID (число)

# Канал:
# 1) Если канал ПРИВАТНЫЙ — лучше использовать CHANNEL_ID (например: -1001234567890)
# 2) Если канал ПУБЛИЧНЫЙ — можно CHANNEL_USERNAME = "@yourchannel"
CHANNEL_ID = -1003637167736                    # например: -1001234567890
CHANNEL_USERNAME = "@yerimbetde"      # если публичный канал

# Платёж (ваш новый реквизит)
PAYMENT_REQUISITES = "4400430338004382\nNAGYZKHAN YERIMBET"
PRICE = 30000

# Таймауты сети
apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ================== ХРАНИЛИЩЕ СОСТОЯНИЙ ==================
accepted_terms = set()      # кто принял условия
waiting_receipt = set()     # кто сейчас должен отправить чек
pending = {}                # user_id -> данные (чек/сообщение)

# ================== ТЕКСТЫ ==================
TERMS_TEXT = (
    "<b>📄 Условия</b>\n\n"
    "1) Оплата производится единоразово.\n"
    "2) После подтверждения оплаты вы получаете доступ.\n"
    "3) Доступ предоставляется только одному аккаунту.\n"
    "4) Возврат средств не предусмотрен.\n\n"
    "Нажмите кнопку ниже, чтобы подтвердить согласие."
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

PAYMENT_TEXT = (
    "<b>💳 Оплата и условия</b>\n\n"
    f"Сумма к оплате: <b>{PRICE} тг</b>\n\n"
    "<b>Реквизиты:</b>\n"
    f"<code>{PAYMENT_REQUISITES}</code>\n\n"
    "После оплаты нажмите <b>✅ Я оплатил(-а)</b> и отправьте чек (скриншот)."
)

START_TEXT = (
    "Здравствуйте! 👋\n\n"
    "Я помогу оформить покупку и передать чек администратору.\n\n"
    "Выберите действие кнопками ниже."
)

# ================== КЛАВИАТУРЫ ==================
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💳 Оплата и условия", "💰 Прайс")
    kb.row("📄 Условия", "✅ Я оплатил(-а)")
    return kb

def accept_terms_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Принимаю условия", callback_data="accept_terms"))
    return kb

def admin_review_kb(user_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve:{user_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{user_id}")
    )
    return kb

# ================== ВСПОМОГАТЕЛЬНОЕ ==================
def channel_target():
    # приоритет: если задан CHANNEL_ID — используем его (лучше для приватного канала)
    if CHANNEL_ID:
        return CHANNEL_ID
    return CHANNEL_USERNAME

def require_terms(user_id: int):
    return user_id in accepted_terms

# ================== ХЭНДЛЕРЫ ==================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, START_TEXT, reply_markup=main_menu_kb())

@bot.message_handler(func=lambda m: (m.text or "").strip().lower() in ["прайс", "💰 прайс"])
def show_price(message):
    bot.send_message(message.chat.id, PRICE_TEXT, reply_markup=main_menu_kb())

@bot.message_handler(func=lambda m: (m.text or "").strip().lower() in ["условия", "📄 условия"])
def show_terms(message):
    bot.send_message(message.chat.id, TERMS_TEXT, reply_markup=accept_terms_kb())

@bot.message_handler(func=lambda m: "оплата" in (m.text or "").lower())
def show_payment(message):
    # Сначала попросим принять условия (если ещё не принял)
    if not require_terms(message.from_user.id):
        bot.send_message(message.chat.id, "Сначала, пожалуйста, примите условия 👇")
        bot.send_message(message.chat.id, TERMS_TEXT, reply_markup=accept_terms_kb())
        return

    bot.send_message(message.chat.id, PAYMENT_TEXT, reply_markup=main_menu_kb())

@bot.callback_query_handler(func=lambda call: call.data == "accept_terms")
def accept_terms_handler(call):
    accepted_terms.add(call.from_user.id)
    bot.answer_callback_query(call.id, "Условия приняты ✅")
    bot.send_message(call.message.chat.id, "Спасибо! Условия приняты ✅\nТеперь можете перейти к оплате.", reply_markup=main_menu_kb())

@bot.message_handler(func=lambda m: (m.text or "").strip().lower() in ["✅ я оплатил(-а)", "я оплатил(-а)"])
def i_paid(message):
    if not require_terms(message.from_user.id):
        bot.send_message(message.chat.id, "Сначала, пожалуйста, примите условия 👇")
        bot.send_message(message.chat.id, TERMS_TEXT, reply_markup=accept_terms_kb())
        return

    waiting_receipt.add(message.from_user.id)
    bot.send_message(message.chat.id, "Пожалуйста, отправьте чек (скриншот) одним сообщением 📸")

@bot.message_handler(content_types=["photo", "document"])
def receipt(message):
    uid = message.from_user.id

    # принимаем чек только если пользователь нажал "Я оплатил(-а)"
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

    # отправляем админу фото/док с кнопками
    try:
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_ID, file_id, caption=caption, reply_markup=admin_review_kb(uid))
        else:
            bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=admin_review_kb(uid))

        bot.send_message(message.chat.id, "Спасибо! Чек передан администратору ✅")
    except Exception:
        bot.send_message(message.chat.id, "Не удалось отправить администратору. Проверьте ADMIN_ID и что админ писал боту хотя бы 1 раз.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve:") or call.data.startswith("reject:"))
def admin_decision(call):
    # защита: только админ
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
        bot.send_message(user_chat_id, "❌ Оплата не подтверждена. Пожалуйста, проверьте чек и отправьте заново.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        pending.pop(uid, None)
        return

    # approve
    bot.answer_callback_query(call.id, "Подтверждено ✅")

    # выдаём доступ: либо ссылкой-приглашением (лучше для приватного канала), либо просто ссылкой на публичный канал
    try:
        if CHANNEL_ID:
            # создаём одноразовую ссылку на 1 человека
            invite = bot.create_chat_invite_link(
                chat_id=CHANNEL_ID,
                member_limit=1
            )
            link = invite.invite_link
            bot.send_message(user_chat_id, f"✅ Оплата подтверждена.\nВот ваша ссылка для доступа (одноразовая):\n{link}")
        else:
            bot.send_message(user_chat_id, f"✅ Оплата подтверждена.\nВот ссылка на канал:\n{CHANNEL_USERNAME}")

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        pending.pop(uid, None)
    except Exception:
        bot.send_message(user_chat_id, "✅ Оплата подтверждена.\nНо не удалось выдать доступ автоматически.\nАдминистратор добавит вас вручную.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        pending.pop(uid, None)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    print("Bot started...")
    # ВАЖНО: если бот на Railway, локально не запускайте одновременно (будет 409 conflict)
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
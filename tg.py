import os
import time
import telebot
from telebot import types, apihelper

# =========================
# CONFIG
# =========================
TOKEN = "8358989018:AAH67ZtDtR5d_sv-DjfAZN76ZkDOkhY4LmM"  # set in Railway Variables (TOKEN=xxxx:yyyy)
ADMIN_ID = 617404776        # new admin id (number)

# Put your channel username WITH @, e.g. "@yerimbetde"
CHANNEL_USERNAME = os.getenv("yerimbetde") or "@yerimbetde"

apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 60

if not TOKEN:
    raise ValueError("TOKEN is not set. Add TOKEN to environment variables (Railway Variables or local env).")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# user_id -> {"amount": str|None, "state": "wait_amount"/"wait_receipt"/None}
user_state = {}

def st(uid: int):
    user_state.setdefault(uid, {"amount": None, "state": None})
    return user_state[uid]

def set_state(uid: int, state: str | None):
    st(uid)["state"] = state

# =========================
# TEXTS (official)
# =========================
START_TEXT = (
    "Здравствуйте! 👋\n"
    "Это бот для покупки брифа для дизайнеров.\n\n"
    "Вы получаете готовый рабочий документ, который помогает четко формулировать задачи, "
    "фиксировать пожелания клиента и сокращать время на правки.\n\n"
    "Выберите действие ниже."
)

PRICE_TEXT = (
    "📦 <b>Тариф: «Стандарт»</b>\n"
    "💰 <b>Цена:</b> 30 000 тг (единоразово)\n\n"
    "📄 <b>Состав:</b>\n"
    "— Готовый шаблон брифа (ссылка на документ)\n"
    "— Доступ на редактирование и скачивание\n"
    "— Можно использовать для любого количества проектов\n"
    "⏳ <b>Срок доступа:</b> бессрочно"
)

OFFER_TEXT = (
    "📄 <b>Условия покупки (оферта):</b>\n\n"
    "• Вы приобретаете цифровой товар — готовый шаблон брифа.\n"
    "• Доступ предоставляется бессрочно, без абонентской платы.\n"
    "• Возврат средств за цифровые товары не производится после получения доступа к документу.\n"
    "• Запрещена перепродажа и публикация документа в открытый доступ.\n"
    "• Оплата проверяется вручную. После подтверждения оплаты Вам будет автоматически выдан доступ.\n\n"
    "Чтобы оплатить — откройте раздел «💳 Оплата»."
)

PAY_TEXT = (
    "💳 <b>Как оплатить:</b>\n"
    "Перевод на карту (Казахстан).\n\n"
    "🏦 <b>Реквизиты:</b>\n"
    "Карта: <code>4400 4303 3800 4382</code>\n"
    "Получатель: <b>NAGYZKHAN YERIMBET</b>\n\n"
    "📝 <b>В комментарии к переводу обязательно укажите:</b>\n"
    "<code>@ваш_telegram_username</code>\n\n"
    "📸 После оплаты нажмите «✅ Я оплатил(-а)» и отправьте скриншот чека."
)

ASK_AMOUNT_TEXT = "Пожалуйста, укажите сумму оплаты (например: 30000)."
ASK_RECEIPT_TEXT = "Спасибо. Теперь, пожалуйста, отправьте чек/скрин (фото или файл)."

WAIT_TEXT = (
    "Спасибо! ✅\n"
    "Чек отправлен на проверку.\n"
    "После подтверждения оплаты Вам автоматически придет одноразовая ссылка на канал."
)

REJECT_TEXT = (
    "❌ <b>Оплата не подтверждена.</b>\n"
    "Пожалуйста, проверьте перевод и отправьте чек повторно."
)

SUPPORT_PROMPT = (
    "Пожалуйста, напишите ваш вопрос одним сообщением.\n"
    "Мы передадим его администратору."
)

# =========================
# UI
# =========================
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💰 Прайс", "📄 Условия")
    kb.add("💳 Оплата", "✅ Я оплатил(-а)")
    kb.add("💬 Поддержка")
    return kb

def admin_kb(buyer_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_ok:{buyer_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_no:{buyer_id}")
    )
    return kb

# =========================
# HELPERS
# =========================
def safe_name(u):
    fn = u.first_name or ""
    ln = u.last_name or ""
    return (fn + " " + ln).strip() or "Без имени"

def get_channel_id():
    # Will raise error if CHANNEL_USERNAME is wrong or bot has no access
    chat = bot.get_chat(CHANNEL_USERNAME)
    return chat.id

def create_one_time_invite():
    channel_id = get_channel_id()
    invite = bot.create_chat_invite_link(chat_id=channel_id, member_limit=1)
    return invite.invite_link

# =========================
# COMMANDS
# =========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    st(uid)  # init
    bot.send_message(message.chat.id, START_TEXT, reply_markup=main_menu())

@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(message.chat.id, "Используйте кнопки меню или команду /start.", reply_markup=main_menu())

# =========================
# MENU HANDLERS
# =========================
@bot.message_handler(func=lambda m: (m.text or "").strip() == "💰 Прайс")
def on_price(message):
    bot.send_message(message.chat.id, PRICE_TEXT)

@bot.message_handler(func=lambda m: (m.text or "").strip() == "📄 Условия")
def on_offer(message):
    bot.send_message(message.chat.id, OFFER_TEXT)

@bot.message_handler(func=lambda m: (m.text or "").strip() == "💳 Оплата")
def on_pay(message):
    bot.send_message(message.chat.id, PAY_TEXT)

@bot.message_handler(func=lambda m: (m.text or "").strip() == "💬 Поддержка")
def on_support(message):
    set_state(message.from_user.id, None)
    bot.send_message(message.chat.id, SUPPORT_PROMPT)

@bot.message_handler(func=lambda m: (m.text or "").strip() == "✅ Я оплатил(-а)")
def on_paid(message):
    uid = message.from_user.id
    set_state(uid, "wait_amount")
    bot.send_message(message.chat.id, ASK_AMOUNT_TEXT)

# =========================
# RECEIPT FLOW: amount -> receipt
# =========================
@bot.message_handler(content_types=["text"])
def on_text(message):
    uid = message.from_user.id
    text = (message.text or "").strip()

    # ignore menu texts already handled above
    if text in {"💰 Прайс", "📄 Условия", "💳 Оплата", "✅ Я оплатил(-а)", "💬 Поддержка"}:
        return
    if text.startswith("/"):
        return

    state = st(uid)["state"]

    # step 1: amount
    if state == "wait_amount":
        st(uid)["amount"] = text
        set_state(uid, "wait_receipt")
        bot.send_message(message.chat.id, ASK_RECEIPT_TEXT)
        return

    # support messages (any other text)
    if uid != ADMIN_ID:
        try:
            username = message.from_user.username or "без_username"
            name = safe_name(message.from_user)
            bot.send_message(
                ADMIN_ID,
                "💬 <b>Сообщение в поддержку</b>\n"
                f"От: <b>{name}</b> (@{username})\n"
                f"id: <code>{uid}</code>\n\n"
                f"{text}"
            )
            bot.send_message(message.chat.id, "Спасибо! Сообщение передано администратору ✅")
        except Exception:
            bot.send_message(message.chat.id, "⚠️ Сейчас не удалось передать сообщение. Пожалуйста, попробуйте позже.")
    else:
        bot.send_message(message.chat.id, "Вы администратор. Используйте кнопки под чеками для подтверждения.")

@bot.message_handler(content_types=["photo", "document"])
def on_receipt(message):
    uid = message.from_user.id
    state = st(uid)["state"]

    if state != "wait_receipt":
        bot.send_message(message.chat.id, "Чтобы отправить чек, нажмите «✅ Я оплатил(-а)» и следуйте шагам.")
        return

    amount = st(uid)["amount"] or "-"
    username = message.from_user.username or "без_username"
    name = safe_name(message.from_user)

    caption = (
        "🧾 <b>Чек на проверку</b>\n"
        f"👤 {name} (@{username})\n"
        f"🆔 <code>{uid}</code>\n"
        f"💰 Сумма: <b>{amount}</b>\n"
        f"⏱ {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        if message.photo:
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=admin_kb(uid))
        else:
            bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=admin_kb(uid))

        bot.send_message(message.chat.id, WAIT_TEXT)

        # reset state
        st(uid)["amount"] = None
        set_state(uid, None)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Не удалось отправить чек администратору. Попробуйте ещё раз через минуту.")
        try:
            bot.send_message(ADMIN_ID, f"❗ Ошибка при пересылке чека админу: {e}")
        except Exception:
            pass

# =========================
# ADMIN CALLBACKS
# =========================
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_ok:") or c.data.startswith("admin_no:"))
def admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет доступа.")
        return

    action, buyer_id_str = call.data.split(":")
    buyer_id = int(buyer_id_str)

    if action == "admin_no":
        try:
            bot.send_message(buyer_id, REJECT_TEXT)
            bot.answer_callback_query(call.id, "Отклонено ❌")
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        except Exception as e:
            bot.answer_callback_query(call.id, "Ошибка отправки пользователю")
            try:
                bot.send_message(ADMIN_ID, f"❗ Ошибка при отклонении: {e}")
            except Exception:
                pass
        return

    # action == admin_ok: create one-time invite and send
    try:
        link = create_one_time_invite()
        text = (
            "✅ <b>Оплата подтверждена!</b>\n\n"
            "Вот Ваша одноразовая ссылка для доступа:\n"
            f"{link}\n\n"
            "Ссылка рассчитана на 1 вход. Если возникнут сложности — напишите в поддержку."
        )
        bot.send_message(buyer_id, text)

        bot.answer_callback_query(call.id, "Подтверждено ✅ Ссылка отправлена")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    except Exception as e:
        bot.answer_callback_query(call.id, "Не удалось создать/отправить ссылку")
        try:
            bot.send_message(
                ADMIN_ID,
                "❗ <b>Ошибка выдачи ссылки</b>\n"
                f"Проверьте права бота в канале и CHANNEL_USERNAME.\n"
                f"Ошибка: <code>{e}</code>"
            )
        except Exception:
            pass

# =========================
# RUN
# =========================
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

import telebot
from telebot import types, apihelper
import time

# ========= НАСТРОЙКИ =========
TOKEN = "8358989018:AAH67ZtDtR5d_sv-DjfAZN76ZkDOkhY4LmM"
ADMIN_ID = 123456789  # ВСТАВЬТЕ СВОЙ ЧИСЛОВОЙ TELEGRAM ID

# Сеть/таймауты (меньше ReadTimeout)
apihelper.CONNECT_TIMEOUT = 10
apihelper.READ_TIMEOUT = 60

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ========= ТЕКСТЫ (ОФИЦИАЛЬНЫЕ) =========

START_TEXT = (
    "Здравствуйте! 👋\n"
    "Это бот для покупки брифа для дизайнеров.\n\n"
    "Вы получаете готовый рабочий документ, который поможет четко формулировать задачи, "
    "фиксировать пожелания клиента и значительно сократить время на правки.\n\n"
    "После покупки бриф навсегда остается у вас в формате Google Docs / PDF."
)

PRICE_TEXT = (
    "📦 <b>Тариф: «Стандарт»</b>\n"
    "💰 <b>Стоимость:</b> 30 000 тг (единоразово)\n\n"
    "📄 <b>Состав:</b>\n"
    "— Готовый шаблон брифа (ссылка на документ)\n"
    "— Доступ на редактирование и скачивание\n"
    "— Возможность использования для неограниченного количества проектов\n"
    "⏳ <b>Срок доступа:</b> бессрочно\n\n"
    "❓ <b>Можно ли посмотреть пример перед покупкой?</b>\n"
    "👉 Да, доступна демо-версия: [ссылка]\n\n"
    "❓ <b>Что делать, если формат не подойдет?</b>\n"
    "👉 После оплаты вы сразу получаете доступ к документу. Это цифровой товар, возврат средств не предусмотрен, "
    "однако при технических проблемах мы обязательно поможем.\n\n"
    "❓ <b>Требуется ли ежемесячная оплата?</b>\n"
    "👉 Нет, оплата производится один раз. Пользование бессрочное.\n\n"
    "❓ <b>Можно ли передавать доступ другим лицам?</b>\n"
    "👉 Документ предназначен для личного использования. Передача третьим лицам запрещена. "
    "Если необходим доступ для команды — свяжитесь с нами."
)

TERMS_TEXT = (
    "📄 <b>Условия покупки:</b>\n\n"
    "• Вы приобретаете цифровой товар — готовый шаблон брифа.\n"
    "• Доступ предоставляется бессрочно, без абонентской платы.\n"
    "• Возврат средств за цифровые товары не производится после получения доступа к документу.\n"
    "• Запрещена перепродажа и публикация документа в открытый доступ.\n"
    "• Оплата проверяется вручную. Время проверки составляет до 5–10 минут в рабочее время.\n"
    "• После подтверждения оплаты вы получите ссылку на документ.\n\n"
    "Нажмите кнопку «Я принимаю условия», чтобы перейти к оплате."
)

PAY_TEXT = (
    "💳 <b>Способ оплаты:</b>\n"
    "Перевод на карту Halyk / банковскую карту (Казахстан).\n\n"
    "🏦 <b>Реквизиты:</b>\n"
    "Компания: ИП Yerimbet Aidana\n"
    "ИИН/БИН: 930605450858\n"
    "ИИК: KZ19601A871064466291\n"
    "КБЕ: 19\n"
    "Банк: АО «Народный Банк Казахстана»\n"
    "БИК: HSBKKZKX\n"
    "Валюта: KZT\n"
    "Имя Фамилия\n\n"
    "📝 <b>В комментарии к переводу обязательно укажите:</b>\n"
    "@ваш_юзернейм_в_телеграме\n\n"
    "📸 После оплаты нажмите кнопку «Я оплатил(-а)» и отправьте скриншот чека в бот."
)

SUPPORT_TEXT = (
    "Пожалуйста, напишите ваш вопрос одним сообщением.\n"
    "Мы передадим его администратору."
)

# Вставьте ссылку на документ (постоянную или временную)
DOCUMENT_LINK = "https://ВСТАВЬТЕ_ССЫЛКУ_НА_ДОКУМЕНТ"

DELIVERY_TEXT = (
    "✅ <b>Оплата подтверждена!</b>\n\n"
    "Вот ссылка на документ:\n"
    f"{DOCUMENT_LINK}\n\n"
    "Если у вас возникнут вопросы или потребуется восстановить доступ, пожалуйста, свяжитесь с администратором."
)

REJECT_TEXT = (
    "❌ <b>Оплата не найдена.</b>\n"
    "Пожалуйста, проверьте корректность перевода и отправьте чек повторно через кнопку «Я оплатил(-а)»."
)

# ========= ПАМЯТЬ СОСТОЯНИЙ (простой FSM) =========
# user_id -> {"agreed": bool, "state": None/"wait_amount"/"wait_receipt", "amount": str|None}
user_state = {}

def init_user(uid: int):
    user_state.setdefault(uid, {"agreed": False, "state": None, "amount": None})

def set_state(uid: int, state: str | None):
    init_user(uid)
    user_state[uid]["state"] = state

def get_state(uid: int):
    init_user(uid)
    return user_state[uid]

# ========= КНОПКИ =========

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💰 Прайс")
    kb.add("📄 Оплата и условия")
    kb.add("✅ Я оплатил(-а)")
    kb.add("💬 Поддержка")
    return kb

def agree_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Я принимаю условия", callback_data="agree_terms"))
    return kb

def admin_kb(buyer_id: int):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_ok:{buyer_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_no:{buyer_id}")
    )
    return kb

# ========= /start =========

@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    init_user(uid)
    bot.send_message(message.chat.id, START_TEXT, reply_markup=main_menu())
    bot.send_message(message.chat.id, f"Ваш user_id: <code>{uid}</code>")

# ========= МЕНЮ =========

@bot.message_handler(func=lambda m: m.text == "💰 Прайс")
def on_price(message):
    bot.send_message(message.chat.id, PRICE_TEXT)

@bot.message_handler(func=lambda m: m.text == "📄 Оплата и условия")
def on_terms(message):
    bot.send_message(message.chat.id, TERMS_TEXT, reply_markup=agree_kb())

@bot.callback_query_handler(func=lambda c: c.data == "agree_terms")
def on_agree(call):
    uid = call.from_user.id
    init_user(uid)
    user_state[uid]["agreed"] = True
    bot.answer_callback_query(call.id, "Условия приняты ✅")
    bot.send_message(call.message.chat.id, PAY_TEXT)

@bot.message_handler(func=lambda m: m.text == "💬 Поддержка")
def on_support(message):
    bot.send_message(message.chat.id, SUPPORT_TEXT)

# ========= “Я оплатил(-а)” =========

@bot.message_handler(func=lambda m: m.text == "✅ Я оплатил(-а)")
def on_paid(message):
    uid = message.from_user.id
    init_user(uid)

    if not user_state[uid]["agreed"]:
        bot.send_message(message.chat.id, "Пожалуйста, сначала откройте «Оплата и условия» и нажмите «Я принимаю условия».")
        return

    set_state(uid, "wait_amount")
    bot.send_message(message.chat.id, "Пожалуйста, укажите сумму оплаты (например 30000):")

# ========= ТЕКСТОВЫЕ СООБЩЕНИЯ (FSM + поддержка) =========

@bot.message_handler(content_types=["text"])
def on_text(message):
    uid = message.from_user.id
    txt = (message.text or "").strip()

    # меню/команды не трогаем
    if txt.startswith("/") or txt in {"💰 Прайс", "📄 Оплата и условия", "✅ Я оплатил(-а)", "💬 Поддержка"}:
        return

    st = get_state(uid)

    # шаг 1: ждём сумму
    if st["state"] == "wait_amount":
        user_state[uid]["amount"] = txt
        set_state(uid, "wait_receipt")
        bot.send_message(message.chat.id, "Спасибо. Теперь, пожалуйста, отправьте чек/скрин (фото или файл).")
        return

    # иначе — поддержка
    if uid != ADMIN_ID:
        try:
            bot.send_message(
                ADMIN_ID,
                "💬 <b>Сообщение в поддержку</b>\n"
                f"От: @{message.from_user.username or 'без_username'} (id <code>{uid}</code>)\n"
                f"Текст: {txt}"
            )
            bot.send_message(message.chat.id, "Спасибо! Ваше сообщение передано администратору ✅")
        except Exception as e:
            bot.send_message(message.chat.id, "⚠️ Сейчас не удалось передать сообщение администратору. Пожалуйста, попробуйте позже.")
            print("ERROR sending support to admin:", e)

# ========= ЧЕК (Фото/Файл) =========

@bot.message_handler(content_types=["photo", "document"])
def on_receipt(message):
    uid = message.from_user.id
    st = get_state(uid)

    # чек принимаем только если ждём чек
    if st["state"] != "wait_receipt":
        bot.send_message(message.chat.id, "Если это чек, пожалуйста, нажмите «✅ Я оплатил(-а)» и следуйте шагам.")
        return

    amount = st.get("amount") or "-"
    username = message.from_user.username or "без_username"

    caption = (
        "✅ <b>Заявка на проверку оплаты</b>\n"
        f"От: @{username}\n"
        f"id: <code>{uid}</code>\n"
        f"Сумма: <b>{amount}</b>\n"
        f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        if message.photo:
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=admin_kb(uid))
        else:
            bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, reply_markup=admin_kb(uid))

        bot.send_message(message.chat.id, "Спасибо! ✅ Оплата будет проверена в течение 5–10 минут (в рабочее время).")
        set_state(uid, None)
        user_state[uid]["amount"] = None
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Сейчас не удалось отправить чек администратору. Пожалуйста, попробуйте ещё раз через 1–2 минуты.")
        print("ERROR sending receipt to admin:", e)

# ========= КНОПКИ АДМИНА =========

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_ok:") or c.data.startswith("admin_no:"))
def admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Нет доступа")
        return

    action, buyer_id_str = call.data.split(":")
    buyer_id = int(buyer_id_str)

    if action == "admin_ok":
        try:
            bot.send_message(buyer_id, DELIVERY_TEXT)
            bot.answer_callback_query(call.id, "Ссылка отправлена ✅")
        except Exception as e:
            bot.answer_callback_query(call.id, "Не удалось отправить сообщение клиенту")
            print("ERROR sending link to buyer:", e)
    else:
        try:
            bot.send_message(buyer_id, REJECT_TEXT)
            bot.answer_callback_query(call.id, "Отклонено ❌")
        except Exception as e:
            bot.answer_callback_query(call.id, "Не удалось отправить сообщение клиенту")
            print("ERROR sending reject to buyer:", e)

# ========= ЗАПУСК =========

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

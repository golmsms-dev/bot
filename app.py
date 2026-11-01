import os
import time
import threading
from flask import Flask
import telebot
from telebot import types
from gtts import gTTS
import requests

# ----------------------------------
# إعدادات سيرفر الويب (Flask) لمنع النوم على Render
# ----------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running 24/7 successfully!"

# ----------------------------------
# مفاتيح البوت و Gemini API
# ----------------------------------
BOT_TOKEN = "7241757520:AAGJOvDDlm3OrV5noyIBToX-rPx3qaGEwpQ"
GEMINI_API_KEY = "AQ.Ab8RN6IjejgJ6NynaU6fsbHI3_jvc0EGu2sR_p2r1UiyrxXjEA"
GEMINI_MODEL = "gemini-2.0-flash"

ADMIN_ID = 7186106370
bot = telebot.TeleBot(BOT_TOKEN)

bot_active = True           # حالة تشغيل/إيقاف البوت بالكامل
last_ai_reply = {}          # تخزين آخر رد للرد الصوتي
last_voice_time = {}        # تخزين توقيت آخر ضغط على الزر لكل مستخدم


# -------------------------------
# دالة الذكاء الاصطناعي Gemini
# -------------------------------
def ask_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}

    try:
        res = requests.post(url, headers=headers, json=body).json()
        return res["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "❌ حصل خطأ في الذكاء الاصطناعي."


# -------------------------------
# زر "رد صوتي" (Inline)
# -------------------------------
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    global bot_active, last_voice_time

    # زر تشغيل البوت
    if c.data == "bot_on" and c.from_user.id == ADMIN_ID:
        bot_active = True
        bot.answer_callback_query(c.id, "✅ تم تشغيل البوت")
        return

    # زر إيقاف البوت
    if c.data == "bot_off" and c.from_user.id == ADMIN_ID:
        bot_active = False
        bot.answer_callback_query(c.id, "⛔ تم إيقاف البوت تماماً")
        return

    # زر رد صوتي
    if c.data.startswith("voice_"):
        uid = int(c.data.split("_")[1])
        now = time.time()
        last_time = last_voice_time.get(uid, 0)
        diff = now - last_time

        if diff < 300:  # 5 دقائق = 300 ثانية
            remaining = int(300 - diff)
            bot.answer_callback_query(c.id, f"⏳ انتظر قبل الضغط مرة ثانية، باقي {remaining} ثواني")
            return

        last_voice_time[uid] = now
        reply = last_ai_reply.get(uid, "مافيش رد احوله صوت.")

        try:
            tts = gTTS(reply, lang="ar")
            filename = f"voice_{uid}.mp3"
            tts.save(filename)
            bot.send_voice(uid, open(filename, "rb"))
            os.remove(filename)
        except:
            bot.send_message(uid, "❌ خطأ أثناء تحويل النص لصوت.")

        bot.answer_callback_query(c.id)


# -------------------------------
# أمر /start
# -------------------------------
@bot.message_handler(commands=['start'])
def start(msg):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("▶️ تشغيل البوت", callback_data="bot_on"),
        types.InlineKeyboardButton("⛔ إيقاف البوت", callback_data="bot_off")
    )

    bot.send_message(
        msg.chat.id,
        "👋 أهلاً! اسأل أي سؤال وأنا هجاوبك.\nالمبرمج: @AbdullahMohamed2",
        reply_markup=kb
    )


# -------------------------------
# أمر /help (أدمن فقط)
# -------------------------------
@bot.message_handler(commands=['help'])
def help_admin(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("▶️ تشغيل البوت", callback_data="bot_on"),
        types.InlineKeyboardButton("⛔ إيقاف البوت", callback_data="bot_off")
    )

    bot.send_message(msg.chat.id, "🛠 أدوات التحكم:", reply_markup=kb)


# -------------------------------
# الرد على كل الرسائل
# -------------------------------
@bot.message_handler(func=lambda m: True)
def reply_user(msg):
    global bot_active

    if not bot_active:
        return

    text = msg.text.lower()

    # سؤال المبرمج
    if "المبرمج" in text:
        reply = "المبرمج: @AbdullahMohamed2"
    else:
        reply = ask_gemini(msg.text)

    # حفظ آخر رد للرد الصوتي
    last_ai_reply[msg.chat.id] = reply

    # زر رد صوتي
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🎤 رد صوتي", callback_data=f"voice_{msg.chat.id}"))

    bot.send_message(msg.chat.id, reply, reply_markup=kb)


# -------------------------------
# دالة تشغيل البوت في الخلفية
# -------------------------------
def run_bot():
    bot.infinity_polling(skip_pending=True)


# -------------------------------
# تشغيل السيرفر والبوت معاً على Render
# -------------------------------
if __name__ == '__main__':
    # تشغيل البوت في خيط منفصل (Thread)
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    
    # تشغيل سيرفر Flask على بورت 10000 (الذي يتوقعه Render)
    app.run(host='0.0.0.0', port=10000)


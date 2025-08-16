import asyncio
from datetime import datetime
from telegram import Bot, Update
from telegram.error import TelegramError
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import os
import json
import requests

load_dotenv()

TOKEN_API = os.getenv("TOKEN_API")
CHAT_ID = int(os.getenv("CHAT_ID"))
X_RAPIDAPI_KEY = os.getenv("X_RAPIDAPI_KEY")

DATA_DIR = "data"
COUNT_FILE = os.path.join(DATA_DIR, "quiz_sent_count.txt")
QUIZ_CACHE_FILE = os.path.join(DATA_DIR, "quiz_cache.json")

translator = GoogleTranslator(source="en", target="gu")
os.makedirs(DATA_DIR, exist_ok=True)

def load_txt(file_path):
    if not os.path.exists(file_path):
        return 0
    with open(file_path, "r", encoding="utf-8") as f:
        return int(f.read().strip() or 0)

def save_txt(file_path, value):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(value))

def load_json(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_daily_quiz():
    url = "https://current-affairs-of-india.p.rapidapi.com/today-quiz"
    headers = {
        "X-RapidAPI-Key": X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": "current-affairs-of-india.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

async def send_quiz(bot: Bot):
    count = load_txt(COUNT_FILE)
    if count >= 8:
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    cache = load_json(QUIZ_CACHE_FILE)

    if cache.get("date") == today_str:
        quiz = cache["quiz"]
    else:
        quizzes = fetch_daily_quiz()
        if not quizzes or not isinstance(quizzes, list):
            return
        quiz = quizzes[0]
        save_json(QUIZ_CACHE_FILE, {"date": today_str, "quiz": quiz})

    if len(quiz["question"]) > 300 or len(quiz["explanation"]) > 200:
        return

    try:
        gujarati_question = translator.translate(quiz["question"])
        gujarati_options = [translator.translate(opt) for opt in quiz["options"]]
        gujarati_explanation = translator.translate(quiz["explanation"])
    except Exception:
        gujarati_question = quiz["question"]
        gujarati_options = quiz["options"]
        gujarati_explanation = quiz["explanation"]

    await bot.send_poll(
        chat_id=CHAT_ID,
        question=gujarati_question,
        options=gujarati_options,
        correct_option_id=quiz["correctIndex"],
        type="quiz",
        explanation=gujarati_explanation,
        is_anonymous=True,
    )
    save_txt(COUNT_FILE, count + 1)

async def reset_daily_counter():
    save_txt(COUNT_FILE, 0)

async def handle_start(bot: Bot, update: Update):
    try:
        await bot.send_message(
            chat_id=update.message.chat_id,
            text="🙏 સ્વાગત છે! તમે હવે 'પ્રગતિ સેતુ ક્વિઝ બોટ' સાથે જોડાયા છો.\n"
                 "દરરોજ નવા પ્રશ્નો માટે તૈયાર રહો! 📚\n\n"
                 "📲 વધુ શૈક્ષણિક કન્ટેન્ટ માટે 'Pragati Setu' એપ ડાઉનલોડ કરો.\n"
                 "સફળ અભ્યાસ માટે શુભેચ્છાઓ! 🚀"
        )
    except TelegramError:
        pass
    
async def handle_system_messages(bot: Bot, update: Update):
    try:
        if getattr(update, "message", None):
            if getattr(update.message, "new_chat_members", None) or getattr(update.message, "left_chat_member", None):
                await update.message.delete()
    except TelegramError:
        pass

async def main_loop():
    bot = Bot(token=TOKEN_API)
    last_update_id = None  
    last_quiz_hour = None

    while True:
        updates = await bot.get_updates(offset=last_update_id, timeout=10)
        for update in updates:
            last_update_id = update.update_id + 1
            await handle_system_messages(bot, update)
            if getattr(update, "message", None) and getattr(update.message, "text", None):
                if update.message.text.startswith("/start"):
                    await handle_start(bot, update)

        now = datetime.now()

        if now.hour == 8 and last_quiz_hour != 8:
            await reset_daily_counter()

        if now.hour in range(8, 22, 2) and last_quiz_hour != now.hour:
            await send_quiz(bot)
            last_quiz_hour = now.hour

        await asyncio.sleep(30)



if __name__ == "__main__":
    asyncio.run(main_loop())

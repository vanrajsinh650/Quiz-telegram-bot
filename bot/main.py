import asyncio
from datetime import datetime
from telegram import Bot, Update
from telegram.error import TelegramError, Conflict
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import os
import json
import requests
import random
import pytz

load_dotenv()
TOKEN_API = os.getenv("TOKEN_API")
CHAT_ID = int(os.getenv("CHAT_ID"))

DATA_DIR = "data"
COUNT_FILE = os.path.join(DATA_DIR, "quiz_sent_count.txt")
USED_QUESTIONS_FILE = os.path.join(DATA_DIR, "used_questions.json")
RESET_FILE = os.path.join(DATA_DIR, "last_reset.txt")
SLOT_FILE = os.path.join(DATA_DIR, "last_slot.txt")

translator = GoogleTranslator(source="en", target="gu")
os.makedirs(DATA_DIR, exist_ok=True)

IST = pytz.timezone("Asia/Kolkata")
        
def load_txt(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None

def save_txt(file_path, value):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(value))

def load_json(file_path):
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_used_questions():
    data = load_json(USED_QUESTIONS_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    return data.get(today, [])

def save_used_question(question_text):
    data = load_json(USED_QUESTIONS_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in data:
        data[today] = []
    data[today].append(question_text)
    save_json(USED_QUESTIONS_FILE, data)

def fetch_daily_quiz():
    url = "https://the-trivia-api.com/v2/questions?limit=1&region=IN&type=multiple"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return None
        question_data = data[0]
        correct_answer = question_data.get("correctAnswer")
        incorrect_answers = question_data.get("incorrectAnswers", [])
        if not correct_answer:
            return None
        options = list(set(incorrect_answers + [correct_answer]))
        random.shuffle(options)
        if correct_answer not in options:
            return None
        return {
            "question": question_data["question"]["text"],
            "options": options,
            "correctIndex": options.index(correct_answer),
            "explanation": f"Answer: {correct_answer}"
        }
    except Exception:
        return None

async def send_quiz(bot: Bot):
    count = int(load_txt(COUNT_FILE) or 0)
    if count >= 7:
        return
    used_questions = load_used_questions()
    quiz = None
    for _ in range(5):
        candidate = fetch_daily_quiz()
        if candidate and candidate["question"] not in used_questions:
            quiz = candidate
            save_used_question(candidate["question"])
            break
    if not quiz:
        return
    try:
        gujarati_question = translator.translate(quiz["question"])
        gujarati_options = [translator.translate(opt) for opt in quiz["options"]]
        gujarati_explanation = translator.translate(quiz["explanation"])
    except Exception:
        gujarati_question = quiz["question"]
        gujarati_options = quiz["options"]
        gujarati_explanation = quiz["explanation"]
    try:
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
    except Exception:
        pass

async def reset_daily_counter():
    save_txt(COUNT_FILE, 0)

async def handle_start(bot: Bot, update: Update):
    try:
        await bot.send_message(
            chat_id=update.message.chat_id,
            text="🙏 સ્વાગત છે! તમે હવે 'પ્રગતિ સેતુ ક્વિઝ બોટ' સાથે જોડાયા છો.\nદરરોજ નવા પ્રશ્નો માટે તૈયાર રહો! 📚\n\n📲 વધુ શૈક્ષણિક કન્ટેન્ટ માટે 'Pragati Setu' એપ ડાઉનલોડ કરો.\nસફળ અભ્યાસ માટે શુભેચ્છાઓ! 🚀"
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
    await bot.delete_webhook()
    await bot.get_updates(offset=-1)
    last_update_id = None

    while True:
        now = datetime.now(IST)
        today = now.strftime("%Y-%m-%d")
        reset_done = load_txt(RESET_FILE)
        last_slot = load_txt(SLOT_FILE)

        try:
            updates = await bot.get_updates(offset=last_update_id, timeout=10)
        except Conflict:
            await asyncio.sleep(10)
            last_update_id = None
            continue
        except Exception:
            await asyncio.sleep(5)
            continue

        for update in updates:
            last_update_id = update.update_id + 1
            await handle_system_messages(bot, update)
            if getattr(update, "message", None) and getattr(update.message, "text", None):
                if update.message.text.startswith("/start"):
                    await handle_start(bot, update)

        if now.hour == 8 and reset_done != today:
            await reset_daily_counter()
            save_txt(RESET_FILE, today)

        slot_id = f"{today}_{now.hour//2}"
        if 8 <= now.hour < 22 and last_slot != slot_id:
            await send_quiz(bot)
            save_txt(SLOT_FILE, slot_id)

        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main_loop())

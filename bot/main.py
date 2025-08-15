from datetime import time, timezone, timedelta, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
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

def load_txt(file_path):
    if not os.path.exists(file_path):
        return 0
    with open(file_path, "r", encoding="utf-8") as file:
        return int(file.read().strip() or 0)

def save_txt(file_path, value):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(str(value))

def load_json(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

async def restart_quiz(update, context):
    save_txt(COUNT_FILE, 0)
    await context.bot.send_message(update.effective_chat.id, text="Quiz has been restarted.")

async def start_bot(update, context):
    await context.bot.send_message(
        update.effective_chat.id,
        text="🙏 સ્વાગત છે! તમે હવે 'પ્રગતિ સેતુ ક્વિઝ બોટ' સાથે જોડાયા છો.\nદરરોજ નવા પ્રશ્નો માટે તૈયાર રહો! 📚\n\n📲 વધુ શૈક્ષણિક કન્ટેન્ટ માટે 'Pragati Setu' એપ ડાઉનલોડ કરો.\n\nસફળ અભ્યાસ માટે શુભેચ્છાઓ! 🚀"
    )

def fetch_daily_quiz():
    url = "https://current-affairs-of-india.p.rapidapi.com/today-quiz"
    headers = {
        "X-RapidAPI-Key": X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": "current-affairs-of-india.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return []

async def send_quiz(context: ContextTypes.DEFAULT_TYPE):
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
        cache = {"date": today_str, "quiz": quiz}
        save_json(QUIZ_CACHE_FILE, cache)
    if len(quiz["question"]) > 300 or len(quiz["explanation"]) > 200:
        return
    try:
        gujarati_question = translator.translate(quiz["question"])
        gujarati_options = [translator.translate(opt) for opt in quiz["options"]]
        gujarati_explanation = translator.translate(quiz["explanation"])
    except:
        gujarati_question = quiz["question"]
        gujarati_options = quiz["options"]
        gujarati_explanation = quiz["explanation"]
    await context.bot.send_poll(
        chat_id=CHAT_ID,
        question=gujarati_question,
        options=gujarati_options,
        correct_option_id=quiz["correctIndex"],
        type="quiz",
        explanation=gujarati_explanation,
        is_anonymous=True
    )
    save_txt(COUNT_FILE, count + 1)

async def reset_daily_counter(context: ContextTypes.DEFAULT_TYPE):
    save_txt(COUNT_FILE, 0)

async def delete_system_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    application = ApplicationBuilder().token(TOKEN_API).job_queue().build()
    application.add_handler(CommandHandler('start', start_bot))
    application.add_handler(CommandHandler('restart_quiz', restart_quiz))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_system_messages))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_system_messages))
    IST = timezone(timedelta(hours=5, minutes=30))
    job_queue = application.job_queue
    job_queue.run_daily(reset_daily_counter, time(hour=8, minute=0, tzinfo=IST))
    for hour in range(8, 24, 2):
        job_queue.run_daily(send_quiz, time(hour=hour, minute=0, tzinfo=IST))
    application.run_polling()

if __name__ == "__main__":
    main()

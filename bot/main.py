from datetime import time, timezone, timedelta, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import asyncio
import os
import json
import requests
import http.client

load_dotenv()

TOKEN_API = os.getenv("TOKEN_API")
CHAT_ID = int(os.getenv("CHAT_ID"))
X_RAPIDAPI_KEY= os.getenv("X_RAPIDAPI_KEY")

DATA_DIR = "data"
COUNT_FILE = os.path.join(DATA_DIR, "quiz_sent_count.txt")

def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return int(file.read().strip() or 0)

def save_txt(file_path, value):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(str(value))

async def restart_quiz(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, text="Quiz has been restarted.")
    save_txt(COUNT_FILE, 0)

async def start_bot(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
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
        print(f"Error fetching quiz: {response.status_code}")
        return []

async def send_quiz(context: ContextTypes.DEFAULT_TYPE):
    count = load_txt(COUNT_FILE)
    if count >= 8:
        return
    
    quizzes = fetch_daily_quiz()
    if not quizzes or not isinstance(quizzes, list):
        print("No quiz available, skipping...")
        return
    
    quiz = quizzes[0]
    
    if len(quiz["question"]) > 300 or len(quiz["explanation"]) > 200:
        return
    
    await context.bot.send_poll(
        chat_id=CHAT_ID,
        question=quiz["question"],
        options=quiz["options"],
        correct_option_id=quiz["correctIndex"],
        type="quiz",
        explanation=quiz["explanation"],
        is_anonymous=True
    )
    
    save_txt(COUNT_FILE, count + 1)
    print(f"Quiz sent at: {datetime.now()} (Count: {count + 1})")

async def reset_daily_counter(context: ContextTypes.DEFAULT_TYPE):
    save_txt(COUNT_FILE, 0)
    
async def delete_system_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except:
        pass

def main():
    application = ApplicationBuilder().token(TOKEN_API).build()
    
    application.add_handler(CommandHandler('start', start_bot))
    application.add_handler(CommandHandler('restart_quiz', restart_quiz))
    
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, delete_system_messages))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER,delete_system_messages))

    
    IST = timezone(timedelta(hours=5, minutes=30))
    job_queue = application.job_queue
    
    job_queue.run_daily(reset_daily_counter, time(hour=8, minute=0, tzinfo=IST))
    
    for hour in range(8, 24, 2):
        job_queue.run_daily(send_quiz, time(hour=hour, minute=0, tzinfo=IST))
    application.run_polling()

if __name__ == "__main__":
    main()

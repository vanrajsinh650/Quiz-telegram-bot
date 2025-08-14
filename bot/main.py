from datetime import time, timezone, timedelta, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import asyncio
import os
import json

load_dotenv()

TOKEN_API = os.getenv("TOKEN_API")
CHAT_ID = int(os.getenv("CHAT_ID"))

DATA_DIR = "data"
QUESTION_FILE = os.path.join(DATA_DIR, "question.json")
LAST_POLL_FILE = os.path.join(DATA_DIR, "last_poll.txt")
COUNT_FILE = os.path.join(DATA_DIR, "quiz_sent_count.txt")

def load_question():
    with open(QUESTION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return int(file.read().strip() or 0)

def save_txt(file_path, value):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(str(value))

async def restart_quiz(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, text="Quiz has been restarted.")
    save_txt(LAST_POLL_FILE, 0)
    save_txt(COUNT_FILE, 0)

async def start_bot(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
        text="🙏 સ્વાગત છે! તમે હવે 'પ્રગતિ સેતુ ક્વિઝ બોટ' સાથે જોડાયા છો.\nદરરોજ નવા પ્રશ્નો માટે તૈયાર રહો! 📚\n\n📲 વધુ શૈક્ષણિક કન્ટેન્ટ માટે 'Pragati Setu' એપ ડાઉનલોડ કરો.\n\nસફળ અભ્યાસ માટે શુભેચ્છાઓ! 🚀"
    )

async def send_quiz(context: ContextTypes.DEFAULT_TYPE):
    count = load_txt(COUNT_FILE)
    if count >= 5:
        return
    questions = load_question()
    last_index = load_txt(LAST_POLL_FILE)
    total_questions = len(questions)
    index = last_index % total_questions
    quiz = questions[index]
    if len(quiz["question"]) > 300 or len(quiz["explanation"]) > 200:
        save_txt(LAST_POLL_FILE, index + 1)
        return
    await context.bot.send_poll(
        chat_id=CHAT_ID,
        question=quiz["question"],
        options=quiz["options"],
        correct_option_id=quiz["correct_option_id"],
        type=quiz["type"],
        explanation=quiz["explanation"],
        is_anonymous=True
    )
    save_txt(LAST_POLL_FILE, index + 1)
    save_txt(COUNT_FILE, count + 1)
    print(f"Quiz sent at: {datetime.now()} (Count: {count + 1})")

async def reset_daily_counter(context: ContextTypes.DEFAULT_TYPE):
    save_txt(COUNT_FILE, 0)

async def test_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = load_txt(COUNT_FILE)
    questions = load_question()
    last_index = load_txt(LAST_POLL_FILE)
    total_questions = len(questions)
    valid_count = 0
    i = 0
    while valid_count < 5 - count and i < total_questions:
        index = (last_index + i) % total_questions
        quiz = questions[index]
        if len(quiz["question"]) > 300 or len(quiz["explanation"]) > 200:
            i += 1
            continue
        await context.bot.send_poll(
            chat_id=CHAT_ID,
            question=quiz["question"],
            options=quiz["options"],
            correct_option_id=quiz["correct_option_id"],
            type=quiz["type"],
            explanation=quiz["explanation"],
            is_anonymous=True
        )
        await asyncio.sleep(1)
        valid_count += 1
        i += 1
    save_txt(LAST_POLL_FILE, (last_index + i) % total_questions)
    save_txt(COUNT_FILE, count + valid_count)
    print(f"Test quiz sent at: {datetime.now()} (Count: {count + valid_count})")


def main():
    application = ApplicationBuilder().token(TOKEN_API).build()
    
    application.add_handler(CommandHandler('start', start_bot))
    application.add_handler(CommandHandler('test', test_poll))
    application.add_handler(CommandHandler('restart_quiz', restart_quiz))
    
    IST = timezone(timedelta(hours=5, minutes=30))
    job_queue = application.job_queue
    
    job_queue.run_daily(reset_daily_counter, time(hour=8, minute=0, tzinfo=IST))
    
    for hour in range(8, 24, 2):
        job_queue.run_daily(send_quiz, time(hour=hour, minute=0, tzinfo=IST))
    application.run_polling()

if __name__ == "__main__":
    main()

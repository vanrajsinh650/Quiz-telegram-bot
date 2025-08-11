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

def load_question():
    with open(QUESTION_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def load_txt():
    with open(LAST_POLL_FILE, "r", encoding="utf-8") as file:
        return int(file.read().strip() or 0)

async def restart_quiz(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, text="Quiz has been restarted.")
    with open(LAST_POLL_FILE, "w") as f:
        f.write("0")

async def start_bot(update, context):
    chat_id = update.effective_chat.id
    print("Bot started")
    await context.bot.send_message(
        chat_id,
        text="🙏 સ્વાગત છે! તમે હવે 'પ્રગતિ સેતુ ક્વિઝ બોટ' સાથે જોડાયા છો.\n"
             "દરરોજ નવા પ્રશ્નો માટે તૈયાર રહો! 📚\n\n📲 વધુ શૈક્ષણિક કન્ટેન્ટ માટે 'Pragati Setu' એપ ડાઉનલોડ કરો.\n\n"
             "સફળ અભ્યાસ માટે શુભેચ્છાઓ! 🚀"
    )

async def send_polls(context: ContextTypes.DEFAULT_TYPE):
    questions = load_question()
    last_index = load_txt()
    total_questions = len(questions)
    valid_count = 0
    i = 0

    while valid_count < 5 and i < total_questions:
        index = (last_index + i) % total_questions
        quiz = questions[index]

        if len(quiz["question"]) > 300:
            print("Question too long:", quiz["question"])
            i += 1
            continue
        if len(quiz["explanation"]) > 200:
            print("Explanation too long:", quiz["explanation"])
            i += 1
            continue

        await context.bot.send_poll(
            chat_id=CHAT_ID,
            question=quiz["question"],
            options=quiz["options"],
            correct_option_id=quiz["correct_option_id"],
            type=quiz["type"],
            explanation=quiz["explanation"],
            is_anonymous=False
        )

        await asyncio.sleep(1)
        valid_count += 1
        i += 1

    new_index = (last_index + i) % total_questions
    with open(LAST_POLL_FILE, "w") as f:
        f.write(str(new_index))

    print("send_polls() called at:", datetime.now())

async def test_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = load_question()
    last_index = load_txt()
    total_questions = len(questions)
    valid_count = 0
    i = 0

    while valid_count < 5 and i < total_questions:
        index = (last_index + i) % total_questions
        quiz = questions[index]

        if len(quiz["question"]) > 300:
            print("Question too long:", quiz["question"])
            i += 1
            continue
        if len(quiz["explanation"]) > 200:
            print("Explanation too long:", quiz["explanation"])
            i += 1
            continue

        await context.bot.send_poll(
            chat_id=CHAT_ID,
            question=quiz["question"],
            options=quiz["options"],
            correct_option_id=quiz["correct_option_id"],
            type=quiz["type"],
            explanation=quiz["explanation"],
            is_anonymous=False
        )

        await asyncio.sleep(1)
        valid_count += 1
        i += 1

    new_index = (last_index + i) % total_questions
    with open(LAST_POLL_FILE, "w") as f:
        f.write(str(new_index))

def main():
    application = ApplicationBuilder().token(TOKEN_API).build()

    application.add_handler(CommandHandler('start', start_bot))
    application.add_handler(CommandHandler('test', test_poll))
    application.add_handler(CommandHandler('restart_quiz', restart_quiz))

    IST = timezone(timedelta(hours=5, minutes=30))

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(send_polls, time(hour=8, minute=0, tzinfo=IST))
    else:
        print("[WARNING] JobQueue not initialized. Use PTB with job-queue support.")

    application.run_polling()

if __name__ == "__main__":
    main()

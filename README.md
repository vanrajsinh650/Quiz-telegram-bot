# 📚 Telegram Quiz Bot

Welcome to the **Quiz Bot** — an educational Telegram bot built using Python that sends 5 daily multiple-choice quiz questions in Gujarati. The questions are delivered automatically every morning, making learning fun and consistent!

---

## ✨ Features

- ✅ Sends 5 quiz-style poll questions daily at a specific time
- ✅ Loads questions dynamically from a JSON file (`question.json`)
- ✅ Tracks quiz progress using a local file (`last_poll.txt`)
- ✅ Supports `/start`, `/restart_quiz`, and `/test` commands
- ✅ Built using `python-telegram-bot` v20+

---

## 🚫 Why This Bot Doesn’t Directly Work in Channels

Telegram **does not allow bots to send poll messages (especially quiz-type polls)** directly into **channels** — only into **chats or groups**.

> **Reason**: According to Telegram Bot API documentation and tests, `send_poll()` works only in private chats or groups, not in channels. If you try, you’ll receive an error:  
> `telegram.error.BadRequest: Polls can't be sent to the channel`

## 🛠 Installation Guide

### 1. Prerequisites

- Python 3.9+
- Telegram bot token from [BotFather](https://t.me/botfather)
- `python-telegram-bot` version 20+

### 2. Install Required Libraries

```bash
pip install python-telegram-bot==20.3

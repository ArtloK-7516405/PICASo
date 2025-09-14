# PICASo / Picture Info Catalog Authors Saving
**Телеграм-бот для организации коллекции изображений с продвинутой системой тегирования и поиска**

**A powerful Telegram bot for managing and browsing a photo database by authors, tags, and characters. Easily add, search, and navigate your collection with a beautiful, user-friendly interface.**


[![Python](https://img.shields.io/badge/Python-3.9+-yellow?logo=python)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram%20Bot-API%2020+-blue?logo=telegram)](https://core.telegram.org/bots/api)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)


---

## ✨ Features

- **Add Photos**: Upload images and assign authors, tags, and characters.
- **Smart Search**: Find images by author, tag, or character.
- **Gallery Navigation**: Scroll through search results with arrow buttons.
- **Organized Storage**: Photos are automatically sorted into author folders.
- **Automatic Backup**: The main photo folder is regularly backed up for safety.
- **Modern UI**: Clean, intuitive Telegram interface with inline buttons.

---

## 🚀 Quick Start

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set your Telegram bot token**
   - Edit `bot.py` and insert your token at `TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'`
4. **Run the bot**
   ```bash
   python -m artist_photo_bot.bot
   ```

---

## 🗂️ Project Structure

```
artist_photo_bot/
│
├── artist_photo_bot/
│   ├── __init__.py
│   ├── bot.py         # Telegram bot logic
│   └── database.py    # Database logic
│
├── photos/            # Main photo storage
├── photos_by_author/  # Photos organized by author
├── photos_backup/     # Backup of main photo storage
├── photos.json        # Database file
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 📷 What does the bot do?

Artist Photo Bot is a Telegram bot that helps you:
- **Collect and organize** your art/photo collection by author, tag, and character.
- **Quickly search** for images using natural queries.
- **Browse results** with a gallery-like experience using navigation buttons.
- **Keep your collection safe** with automatic backups and author-based folders.

Perfect for artists, collectors, and anyone who wants a smart, organized image archive in Telegram!

---

## 🛠️ Requirements
- Python 3.8+
- [python-telegram-bot](https://python-telegram-bot.org/)

---

## 📬 Feedback & Contributions

Feel free to open issues or submit pull requests to improve the bot!

---

**Made with ❤️ for the creative community.**





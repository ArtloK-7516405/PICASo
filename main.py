import json
import os
import random
from collections import Counter
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CallbackContext,
    ConversationHandler,
)
import shutil

TOKEN = 'YOUR_TOKEN'


# Класс для базы данных фотографий
class PhotoDatabase:
    def __init__(self, filename='photos.json'):
        self.filename = filename
        self.data = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self.data = json.load(f)

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def add_entry(self, file_path, authors, tags, characters):
        # Сортируем списки по алфавиту
        sorted_authors = sorted([author.strip() for author in authors], key=lambda x: x.lower())
        sorted_tags = sorted([tag.strip() for tag in tags], key=lambda x: x.lower())
        sorted_characters = sorted([character.strip() for character in characters], key=lambda x: x.lower())

        # Добавляем запись
        entry = {
            'id': len(self.data) + 1,  # Уникальный ID
            'file_path': file_path,
            'authors': sorted_authors,
            'tags': sorted_tags,
            'characters': sorted_characters
        }
        self.data.append(entry)
        self.data.sort(key=lambda x: x['id'])  # Сортировка по ID
        self.save_data()

    def update_entry(self, entry_id, new_authors=None, new_tags=None, new_characters=None):
        for entry in self.data:
            if entry['id'] == int(entry_id):
                # Обновляем авторов, если переданы
                if new_authors:
                    new_authors = [author.strip() for author in new_authors if author.strip()]
                    entry['authors'] = sorted(list(set(entry['authors'] + new_authors)), key=lambda x: x.lower())

                # Обновляем теги
                if new_tags:
                    new_tags = [tag.strip() for tag in new_tags if tag.strip()]
                    entry['tags'] = sorted(list(set(entry['tags'] + new_tags)), key=lambda x: x.lower())

                # Обновляем персонажей
                if new_characters:
                    new_characters = [character.strip() for character in new_characters if character.strip()]
                    entry['characters'] = sorted(list(set(entry['characters'] + new_characters)),
                                                 key=lambda x: x.lower())

                break
        self.data.sort(key=lambda x: x['id'])
        self.save_data()

    def search_by_author(self, author):
        return [entry for entry in self.data if any(author.lower() == a.lower() for a in entry['authors'])]

    def search_by_tag(self, tag):
        return [entry for entry in self.data if any(tag.lower() in t.lower() for t in entry['tags'])]

    def search_by_character(self, character):
        return [entry for entry in self.data if any(character.lower() in c.lower() for c in entry['characters'])]

    def get_entries(self):
        return sorted(self.data, key=lambda x: x['id'])

    def get_all_authors(self):
        authors = set()
        for entry in self.data:
            for author in entry['authors']:
                authors.add(author)
        return sorted(list(authors), key=lambda x: x.lower())


# Создаем экземпляр базы данных
db = PhotoDatabase()

# Определяем состояния для ConversationHandler
ADD_PHOTO, ADD_AUTHORS, ADD_TAGS, ADD_CHARACTERS = range(4)
UPDATE_ID, UPDATE_AUTHORS, UPDATE_TAGS, UPDATE_CHARACTERS = range(4, 8)


# Функция для создания меню команд
def create_command_menu():
    command_menu = [
        ["/add➕", "/update⬆️"],
        ["/search_author👤", "/search_tag🔖"],
        ["/search_character👥", "/display📱"],
        ["/help🆘"]
    ]
    return ReplyKeyboardMarkup(command_menu, resize_keyboard=True, one_time_keyboard=True)


# Функция для создания инлайн-кнопок для пролистывания
def create_navigation_buttons(current_index, total, prefix=None):
    keyboard = []
    if current_index > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"{prefix or ''}prev_{current_index}"))
    if current_index < total - 1:
        keyboard.append(InlineKeyboardButton("Следующая ➡️", callback_data=f"{prefix or ''}next_{current_index}"))
    return InlineKeyboardMarkup([keyboard] if keyboard else [])


# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🌟 <b>Привет! Я бот для управления базой данных фотографий.</b>\n\n"
        "Используй команды:\n"
        "/add - Добавить новую фотографию\n"
        "/update - Обновить запись\n"
        "/search_author - Найти по автору\n"
        "/search_tag - Найти по тегу\n"
        "/search_character - Найти по персонажу\n"
        "/display - Показать все записи\n"
        "/help - Показать список команд",
        parse_mode="HTML",
        reply_markup=create_command_menu()
    )


# Команда /add
async def add_entry(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("📸 Отправьте фотографию:")
    return ADD_PHOTO


async def add_photo(update: Update, context: CallbackContext) -> int:
    if not update.message.photo:
        await update.message.reply_text("❌ Пожалуйста, отправьте фотографию.")
        return ADD_PHOTO
    photo = update.message.photo[-1]  # Берем фото наибольшего размера
    file = await context.bot.get_file(photo.file_id)
    file_path = f"photos/{photo.file_unique_id}.jpg"
    os.makedirs('photos', exist_ok=True)  # Создаем папку, если не существует
    await file.download_to_drive(file_path)
    context.user_data['file_path'] = file_path
    await update.message.reply_text("👤 Введите автора (через запятую, если несколько):")
    return ADD_AUTHORS


async def add_authors(update: Update, context: CallbackContext) -> int:
    context.user_data['authors'] = [author.strip() for author in update.message.text.split(',')]
    await update.message.reply_text("🏷️ Введите теги (через запятую):")
    return ADD_TAGS


async def add_tags(update: Update, context: CallbackContext) -> int:
    context.user_data['tags'] = [tag.strip() for tag in update.message.text.split(',')]
    await update.message.reply_text("👥 Введите персонажей (через запятую):")
    return ADD_CHARACTERS


async def add_characters(update: Update, context: CallbackContext) -> int:
    context.user_data['characters'] = [character.strip() for character in update.message.text.split(',')]
    db.add_entry(
        context.user_data['file_path'],
        context.user_data['authors'],
        context.user_data['tags'],
        context.user_data['characters']
    )
    # --- NEW: Copy to author folders and duplicate main folder ---
    file_path = context.user_data['file_path']
    authors = context.user_data['authors']
    if authors:
        for author in authors:
            author_folder = os.path.join('photos_by_author', author)
            os.makedirs(author_folder, exist_ok=True)
            shutil.copy2(file_path, os.path.join(author_folder, os.path.basename(file_path)))
    # Duplicate main folder
    if os.path.exists('photos_backup'):
        shutil.rmtree('photos_backup')
    shutil.copytree('photos', 'photos_backup')
    # --- END NEW ---
    await update.message.reply_text("✅ Фотография добавлена!", parse_mode="HTML")
    return ConversationHandler.END


# Команда /update
async def update_entry(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Введите ID записи, которую хотите обновить:")
    return UPDATE_ID


async def update_id(update: Update, context: CallbackContext) -> int:
    try:
        entry_id = int(update.message.text)
        if not any(entry['id'] == entry_id for entry in db.data):
            await update.message.reply_text("❌ Запись с таким ID не найдена. Введите другой ID:")
            return UPDATE_ID
        context.user_data['id'] = entry_id
        await update.message.reply_text(
            "Введите новых авторов (через запятую, или нажмите /skip, чтобы оставить старых):")
        return UPDATE_AUTHORS
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите числовой ID:")
        return UPDATE_ID


async def update_authors(update: Update, context: CallbackContext) -> int:
    if update.message.text != "/skip":
        context.user_data['new_authors'] = [author.strip() for author in update.message.text.split(',')]
    await update.message.reply_text("Введите новые теги (через запятую, или нажмите /skip, чтобы оставить старые):")
    return UPDATE_TAGS


async def update_authors_skip(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Введите новые теги (через запятую, или нажмите /skip, чтобы оставить старые):")
    return UPDATE_TAGS


async def update_tags(update: Update, context: CallbackContext) -> int:
    if update.message.text != "/skip":
        context.user_data['new_tags'] = [tag.strip() for tag in update.message.text.split(',')]
    await update.message.reply_text(
        "Введите новых персонажей (через запятую, или нажмите /skip, чтобы оставить старых):")
    return UPDATE_CHARACTERS


async def update_tags_skip(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Введите новых персонажей (через запятую, или нажмите /skip, чтобы оставить старых):")
    return UPDATE_CHARACTERS


async def update_characters(update: Update, context: CallbackContext) -> int:
    if update.message.text != "/skip":
        context.user_data['new_characters'] = [character.strip() for character in update.message.text.split(',')]
    db.update_entry(
        context.user_data['id'],
        new_authors=context.user_data.get('new_authors'),
        new_tags=context.user_data.get('new_tags'),
        new_characters=context.user_data.get('new_characters')
    )
    await update.message.reply_text("✅ Запись обновлена!", parse_mode="HTML")
    return ConversationHandler.END


async def update_characters_skip(update: Update, context: CallbackContext) -> int:
    db.update_entry(
        context.user_data['id'],
        new_authors=context.user_data.get('new_authors'),
        new_tags=context.user_data.get('new_tags'),
        new_characters=context.user_data.get('new_characters')
    )
    await update.message.reply_text("✅ Запись обновлена!", parse_mode="HTML")
    return ConversationHandler.END


# Команда /search_author
async def search_author(update: Update, context: CallbackContext) -> int:
    authors = db.get_all_authors()
    if not authors:
        await update.message.reply_text("❌ В базе данных нет авторов.")
        return ConversationHandler.END
    random_authors = random.sample(authors, min(3, len(authors)))
    text_lines = []
    keyboard = []
    for idx, author in enumerate(random_authors, 1):
        entries = db.search_by_author(author)
        tags = [tag for entry in entries for tag in entry['tags']]
        tag_counts = Counter(tags)
        top_tags = ', '.join([f"#{t}" for t, _ in tag_counts.most_common(3)])
        line = f"{idx}. {author}"
        if top_tags:
            line += f" — {top_tags}"
        text_lines.append(line)
        keyboard.append([InlineKeyboardButton(f"{author}", callback_data=f"authorselect_{author}")])
    text = "\n".join(text_lines)
    text += "\n\nВыберите автора, нажав на кнопку, или введите имя автора вручную:"
    await update.message.reply_text(text)
    return 0


async def search_author_result(update: Update, context: CallbackContext) -> int:
    author = update.message.text
    results = db.search_by_author(author)
    if results:
        context.user_data['search_results'] = results
        context.user_data['search_index'] = 0
        entry = results[0]
        caption = (
            f"<b>ID:</b> {entry['id']}\n"
            f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
            f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
            f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
        )
        try:
            await update.message.reply_photo(
                photo=open(entry['file_path'], 'rb'),
                caption=caption,
                parse_mode="HTML",
                reply_markup=create_navigation_buttons(0, len(results), prefix='author')
            )
        except FileNotFoundError:
            await update.message.reply_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    else:
        await update.message.reply_text(f"❌ Записей с автором '{author}' не найдено.")
    return ConversationHandler.END


# Команда /search_tag
async def search_tag(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🔍 Введите тег для поиска:")
    return "search_tag"


async def search_tag_result(update: Update, context: CallbackContext) -> int:
    tag = update.message.text
    results = db.search_by_tag(tag)
    if results:
        context.user_data['search_results'] = results
        context.user_data['search_index'] = 0
        entry = results[0]
        caption = (
            f"<b>ID:</b> {entry['id']}\n"
            f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
            f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
            f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
        )
        try:
            await update.message.reply_photo(
                photo=open(entry['file_path'], 'rb'),
                caption=caption,
                parse_mode="HTML",
                reply_markup=create_navigation_buttons(0, len(results), prefix='tag')
            )
        except FileNotFoundError:
            await update.message.reply_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    else:
        await update.message.reply_text(f"❌ Записей с тегом '{tag}' не найдено.")


async def tag_button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    results = context.user_data.get('search_results', [])
    if not results:
        await query.edit_message_text("❌ Ошибка: список записей недоступен.")
        return
    current_index = context.user_data.get('search_index', 0)
    callback_data = query.data
    if callback_data.startswith("tagprev_"):
        current_index = max(0, current_index - 1)
    elif callback_data.startswith("tagnext_"):
        current_index = min(len(results) - 1, current_index + 1)
    context.user_data['search_index'] = current_index
    entry = results[current_index]
    caption = (
        f"<b>ID:</b> {entry['id']}\n"
        f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
        f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
        f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
    )
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(open(entry['file_path'], 'rb'), caption=caption, parse_mode="HTML"),
            reply_markup=create_navigation_buttons(current_index, len(results), prefix='tag')
        )
    except FileNotFoundError:
        await query.edit_message_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    except Exception as e:
        await query.edit_message_text(f"❌ Произошла ошибка при обновлении фотографии: {str(e)}")


# Команда /search_character
async def search_character(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🔍 Введите персонажа для поиска:")
    return "search_character"


async def search_character_result(update: Update, context: CallbackContext) -> int:
    character = update.message.text
    results = db.search_by_character(character)
    if results:
        context.user_data['search_results'] = results
        context.user_data['search_index'] = 0
        entry = results[0]
        caption = (
            f"<b>ID:</b> {entry['id']}\n"
            f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
            f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
            f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
        )
        try:
            await update.message.reply_photo(
                photo=open(entry['file_path'], 'rb'),
                caption=caption,
                parse_mode="HTML",
                reply_markup=create_navigation_buttons(0, len(results), prefix='character')
            )
        except FileNotFoundError:
            await update.message.reply_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    else:
        await update.message.reply_text(f"❌ Записей с персонажем '{character}' не найдено.")


async def character_button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    results = context.user_data.get('search_results', [])
    if not results:
        await query.edit_message_text("❌ Ошибка: список записей недоступен.")
        return
    current_index = context.user_data.get('search_index', 0)
    callback_data = query.data
    if callback_data.startswith("characterprev_"):
        current_index = max(0, current_index - 1)
    elif callback_data.startswith("characternext_"):
        current_index = min(len(results) - 1, current_index + 1)
    context.user_data['search_index'] = current_index
    entry = results[current_index]
    caption = (
        f"<b>ID:</b> {entry['id']}\n"
        f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
        f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
        f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
    )
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(open(entry['file_path'], 'rb'), caption=caption, parse_mode="HTML"),
            reply_markup=create_navigation_buttons(current_index, len(results), prefix='character')
        )
    except FileNotFoundError:
        await query.edit_message_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    except Exception as e:
        await query.edit_message_text(f"❌ Произошла ошибка при обновлении фотографии: {str(e)}")


# Команда /display
async def display_entries(update: Update, context: CallbackContext) -> None:
    entries = db.get_entries()
    if not entries:
        await update.message.reply_text("❌ В базе данных нет записей.")
        return

    # Отправляем первое фото с кнопками
    entry = entries[0]
    caption = (
        f"<b>ID:</b> {entry['id']}\n"
        f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
        f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
        f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
    )
    try:
        context.user_data['current_index'] = 0  # Сохраняем текущий индекс
        context.user_data['display_entries'] = entries  # Сохраняем список записей
        await update.message.reply_photo(
            photo=open(entry['file_path'], 'rb'),
            caption=caption,
            parse_mode="HTML",
            reply_markup=create_navigation_buttons(0, len(entries))
        )
    except FileNotFoundError:
        await update.message.reply_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка при отображении фотографии: {str(e)}")


# Обработчик кнопок пролистывания
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback

    entries = context.user_data.get('display_entries', [])
    if not entries:
        await query.edit_message_text("❌ Ошибка: список записей недоступен.")
        return

    current_index = context.user_data.get('current_index', 0)
    callback_data = query.data

    # Определяем новый индекс
    try:
        if callback_data.startswith("prev_"):
            current_index = max(0, current_index - 1)
        elif callback_data.startswith("next_"):
            current_index = min(len(entries) - 1, current_index + 1)
    except ValueError:
        await query.edit_message_text("❌ Ошибка: неверные данные кнопки.")
        return

    context.user_data['current_index'] = current_index
    entry = entries[current_index]

    caption = (
        f"<b>ID:</b> {entry['id']}\n"
        f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
        f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
        f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
    )

    try:
        # Обновляем сообщение с новым фото и кнопками
        await query.edit_message_media(
            media=InputMediaPhoto(open(entry['file_path'], 'rb'), caption=caption, parse_mode="HTML"),
            reply_markup=create_navigation_buttons(current_index, len(entries))
        )
    except FileNotFoundError:
        await query.edit_message_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    except Exception as e:
        await query.edit_message_text(f"❌ Произошла ошибка при обновлении фотографии: {str(e)}")


# Обработчик кнопок пролистывания по авторам
async def author_button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    results = context.user_data.get('search_results', [])
    if not results:
        await query.edit_message_text("❌ Ошибка: список записей недоступен.")
        return
    current_index = context.user_data.get('search_index', 0)
    callback_data = query.data
    if callback_data.startswith("authorprev_"):
        current_index = max(0, current_index - 1)
    elif callback_data.startswith("authornext_"):
        current_index = min(len(results) - 1, current_index + 1)
    context.user_data['search_index'] = current_index
    entry = results[current_index]
    caption = (
        f"<b>ID:</b> {entry['id']}\n"
        f"<b>👤 Авторы:</b> {', '.join(entry['authors'])}\n"
        f"<b>🏷️ Теги:</b> {', '.join(entry['tags'])}\n"
        f"<b>👥 Персонажи:</b> {', '.join(entry['characters'])}"
    )
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(open(entry['file_path'], 'rb'), caption=caption, parse_mode="HTML"),
            reply_markup=create_navigation_buttons(current_index, len(results), prefix='author')
        )
    except FileNotFoundError:
        await query.edit_message_text(f"❌ Фотография с ID {entry['id']} не найдена на сервере.")
    except Exception as e:
        await query.edit_message_text(f"❌ Произошла ошибка при обновлении фотографии: {str(e)}")


# Команда /cancel
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Операция отменена.",
        reply_markup=create_command_menu()
    )
    return ConversationHandler.END


# Команда /help
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🌟 <b>Доступные команды:</b>\n\n"
        "/add - Добавить новую фотографию\n"
        "/update - Обновить запись\n"
        "/search_author - Найти по автору\n"
        "/search_tag - Найти по тегу\n"
        "/search_character - Найти по персонажу\n"
        "/display - Показать все записи\n"
        "/help - Показать список команд",
        parse_mode="HTML",
        reply_markup=create_command_menu()
    )


def main() -> None:
    # Создаем директорию для фото
    os.makedirs('photos', exist_ok=True)

    # Создаем приложение с токеном
    application = Application.builder().token(TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик команды /add
    add_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_entry)],
        states={
            ADD_PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
            ADD_AUTHORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_authors)],
            ADD_TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_tags)],
            ADD_CHARACTERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_characters)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(add_conversation_handler)

    # Обработчик команды /update
    update_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('update', update_entry)],
        states={
            UPDATE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_id)],
            UPDATE_AUTHORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_authors),
                             CommandHandler('skip', update_authors_skip)],
            UPDATE_TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_tags),
                          CommandHandler('skip', update_tags_skip)],
            UPDATE_CHARACTERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_characters),
                                CommandHandler('skip', update_characters_skip)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(update_conversation_handler)

    # Обработчик команды /search_author
    search_author_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('search_author', search_author)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_author_result)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(search_author_conversation_handler)

    # Обработчик команды /search_tag
    search_tag_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('search_tag', search_tag)],
        states={
            "search_tag": [MessageHandler(filters.TEXT & ~filters.COMMAND, search_tag_result)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(search_tag_conversation_handler)

    # Обработчик команды /search_character
    search_character_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('search_character', search_character)],
        states={
            "search_character": [MessageHandler(filters.TEXT & ~filters.COMMAND, search_character_result)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(search_character_conversation_handler)

    # Обработчик команды /display
    application.add_handler(CommandHandler("display", display_entries))

    # Обработчик кнопок пролистывания
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(prev|next)_"))

    # Обработчик кнопок пролистывания по авторам
    application.add_handler(CallbackQueryHandler(author_button_handler, pattern="^author(prev|next)_"))

    # Обработчик кнопок пролистывания по тегам
    application.add_handler(CallbackQueryHandler(tag_button_handler, pattern="^tag(prev|next)_"))

    # Обработчик кнопок пролистывания по персонажам
    application.add_handler(CallbackQueryHandler(character_button_handler, pattern="^character(prev|next)_"))

    # Обработчик команды /help
    application.add_handler(CommandHandler("help", help_command))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":

    main()

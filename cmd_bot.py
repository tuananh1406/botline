from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
import telegram
import logging
import persistence
import socket
import subprocess
import os
import sys
import requests
import configparser
from pathlib import Path
import re
from datetime import datetime
from telegram import User


def start(update, context):
    """Chạy bot"""
    logging.info("========================= START")
    user = update.message.from_user
    user_id = user.id
    message = update.message.text
    message_chat_id = update.message.chat_id
    full_name = user.full_name
    username = user.username
    logging.info(message)
    context.bot.send_message(
        message_chat_id,
        text=f"If you want custom this bot, contact with @{admin_username}",
    )


def error_callback(update, context):
    error_description = f'Update:\n"{update}"\n caused error:\n"{context.error}"'
    logging.error(error_description)
    if update and update.message.from_user.id == admin_id:
        context.bot.send_message(chat_id=update.message.chat_id, text=error_description)


def all_dirs_keyboard(page, dir_path="./"):
    keyboard = [
        [InlineKeyboardButton(d, callback_data=f"EXPLORE goto_dir {d}")]
        for d in list_directories(dir_path)
    ]

    remove_before = page * buttons_rows_per_page
    with_previous_removed = keyboard[remove_before:]
    remaining = len(with_previous_removed)
    with_remaining_removed = with_previous_removed[:buttons_rows_per_page]

    if page > 0 and remaining <= buttons_rows_per_page:
        with_remaining_removed.append(
            [InlineKeyboardButton("<<", callback_data=f"EXPLORE list_dir {page - 1}")]
        )

    if page == 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append(
            [InlineKeyboardButton(">>", callback_data=f"EXPLORE list_dir {page + 1}")]
        )

    if page > 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append(
            [
                InlineKeyboardButton(
                    "<<", callback_data=f"EXPLORE list_dir {page - 1}"
                ),
                InlineKeyboardButton(
                    ">>", callback_data=f"EXPLORE list_dir {page + 1}"
                ),
            ]
        )

    with_remaining_removed.append(
        [InlineKeyboardButton("..", callback_data="EXPLORE goto_parent_dir")]
    )
    with_remaining_removed.append(
        [InlineKeyboardButton("Show files", callback_data="EXPLORE show_files")]
    )
    with_remaining_removed.append(
        [InlineKeyboardButton("Close", callback_data="EXPLORE close")]
    )
    return with_remaining_removed


def all_files_keyboard(page, dir_path="./"):
    keyboard = [
        [InlineKeyboardButton(f, callback_data=f"EXPLORE download {f}")]
        for f in list_files(dir_path)
    ]

    remove_before = page * buttons_rows_per_page
    with_previous_removed = keyboard[remove_before:]
    remaining = len(with_previous_removed)
    with_remaining_removed = with_previous_removed[:buttons_rows_per_page]

    if page > 0 and remaining <= buttons_rows_per_page:
        with_remaining_removed.append(
            [InlineKeyboardButton("<<", callback_data=f"EXPLORE show_files {page - 1}")]
        )

    if page == 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append(
            [InlineKeyboardButton(">>", callback_data=f"EXPLORE show_files {page + 1}")]
        )

    if page > 0 and remaining > buttons_rows_per_page:
        with_remaining_removed.append(
            [
                InlineKeyboardButton(
                    "<<", callback_data=f"EXPLORE show_files {page - 1}"
                ),
                InlineKeyboardButton(
                    ">>", callback_data=f"EXPLORE show_files {page + 1}"
                ),
            ]
        )

    with_remaining_removed.append(
        [InlineKeyboardButton("Show directory", callback_data="EXPLORE list_dir 0")]
    )
    with_remaining_removed.append(
        [InlineKeyboardButton("Close", callback_data="EXPLORE close")]
    )
    return with_remaining_removed


def list_directories(dir_path="./"):
    return [x.name for x in Path(dir_path).glob("*") if x.is_dir()]


def list_files(dir_path="./"):
    return [x.name for x in Path(dir_path).glob("*") if x.is_file()]


def parent_dir():
    path = Path(current_dir)
    return str(path.parent.absolute())


def on_explore_callback(update, context) -> None:
    # global current_dir
    current_dir = "/Volumes/Untitled - Data/TUAN_ANH"
    query = update.callback_query
    logging.info(f"data:{query.data}")
    logging.info(f"query:{query.message.text}")
    logging.info(f"message: {dir(update)}")

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    if query.data == "EXPLORE goto_parent_dir":
        logging.info(f"Explore: leave {current_dir}")
        current_dir = parent_dir()
        logging.info(f"Explore: go to {current_dir}")
        query.edit_message_text(
            text=current_dir,
            reply_markup=InlineKeyboardMarkup(all_dirs_keyboard(0, current_dir)),
        )
        return

    if query.data == "EXPLORE show_files":
        logging.info(f"Explore: show files for {current_dir}")
        query.edit_message_text(
            text=current_dir,
            reply_markup=InlineKeyboardMarkup(all_files_keyboard(0, current_dir)),
        )
        return

    if list_dir_with_page := re.search("EXPLORE list_dir (\\d+)", query.data):
        page = list_dir_with_page[1]
        logging.info(f"Explore: show dir page {page} of {current_dir}")
        query.edit_message_text(
            text=current_dir,
            reply_markup=InlineKeyboardMarkup(
                all_dirs_keyboard(int(page), current_dir)
            ),
        )
        return

    if goto_dir := re.search("EXPLORE goto_dir (.*)", query.data):
        logging.info(f"Explore: leave {current_dir}")
        current_dir = f"{current_dir}/{goto_dir[1]}"
        logging.info(f"Explore: go to {current_dir}")
        query.edit_message_text(
            text=current_dir,
            reply_markup=InlineKeyboardMarkup(all_dirs_keyboard(0, current_dir)),
        )
        return

    if show_files := re.search("EXPLORE show_files (\\d+)", query.data):
        page = show_files[1]
        logging.info(f"Explore: show files page {page} of {current_dir}")
        query.edit_message_text(
            text=current_dir,
            reply_markup=InlineKeyboardMarkup(
                all_files_keyboard(int(page), current_dir)
            ),
        )
        return

    if download_file := re.search("EXPLORE download (.*)", query.data):
        download_file_path = f"{current_dir}/{download_file[1]}"
        logging.info(f"Explore: download file {download_file_path}")
        context.bot.send_document(
            chat_id=update.callback_query.message.chat.id,
            document=open(download_file_path, "rb"),
        )
        query.edit_message_text(text=f"Uploaded: {download_file_path}")
        return

    if query.data == "EXPLORE close":
        query.edit_message_text(text=f"Current dir is now {current_dir}")
        return

    query.edit_message_text(text=f"Selected option: {query.data}")


def explore(update, context):
    """Xem thông tin thư mục"""
    logging.info(f"Explore: {current_dir}")
    keyboard = [
        [
            InlineKeyboardButton(d, callback_data=f"EXPLORE goto_dir {d}")
            for d in [current_dir, "/Volumes/Untitled - Data/ZEN8LABS"]
        ],
        [InlineKeyboardButton("Close", callback_data="EXPLORE close")],
    ]
    update.message.reply_text(
        text="Select folder",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def help_bot(update, context):
    """Xem hướng dẫn"""
    user = update.message.from_user
    user_id = user.id
    message_chat_id = update.message.chat_id
    logging.info("HELP (%s)", user_id)
    for _, command in non_args_cmds + args_cmds:
        logging.info(command.__doc__)
    with open("./README.md", "r") as file:
        context.bot.send_message(
            chat_id=message_chat_id,
            text=file.read(),
            parse_mode=telegram.ParseMode.MARKDOWN,
        )


bot_properties_file = "bot.properties"

if os.path.isfile(bot_properties_file):
    logging.info(f"Using {bot_properties_file}")
    config = configparser.ConfigParser()
    config.read("bot.properties")
    token = config["bot_config"]["token"]
    handle = config["bot_config"]["handle"]
    current_dir = "/Volumes/Untitled - Data/TUAN_ANH"
    broadcast_unkown_messages = config["cmds_config"]["broadcast_unkown_messages"]
    buttons_rows_per_page = int(config["cmds_config"]["buttons_rows_per_page"])
else:
    logging.info("Missing bot.properties file")
    sys.exit(0)

current_dir = str(Path(current_dir).absolute())

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


updater = Updater(token, use_context=True)
dispatcher = updater.dispatcher
non_args_cmds = [
    ("start", start),
    ("help", help_bot),
]
args_cmds = [
    ("explore", explore),
]
for alias, cmd in non_args_cmds:
    dispatcher.add_handler(CommandHandler(alias, cmd))
for alias, cmd in args_cmds:
    dispatcher.add_handler(CommandHandler(alias, cmd, pass_args=True))

updater.dispatcher.add_handler(
    CallbackQueryHandler(on_explore_callback, pattern="^EXPLORE .*$")
)

# dispatcher.add_error_handler(error_callback)

logging.info("Starting bot")
updater.start_polling()

updater_bot = updater.bot
admin_id = 1107739626
admin_username = "huuanh93"
updater_bot.send_message(
    admin_id,
    text=f'Bot {handle} started {datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}',
)

from aiogram import Dispatcher

from create_bot import bot
from data_base import sqlite_db


# new user in group
async def new_member(message):
    new_user = message.new_chat_members[0]
    user_id = new_user['id']
    if new_user['username']:
        user_name = new_user['username']
    elif new_user['first_name']:
        user_name = new_user['first_name']
    elif new_user['last_name']:
        user_name = new_user['last_name']
    else:
        user_name = 'Пользователь без имени'
    await sqlite_db.sql_add_user_to_db(user_id, user_name)
    await bot.send_message(message.chat.id, f'Добро пожаловать, {user_name}!\nКоманда - /start переход'
                                            f' в пользовательское меню.\nКоманда - /help помощь по командам бота.')


# left user from group
async def left_member(message):
    left_user = message.left_chat_member
    user_name = await sqlite_db.sql_get_user_name(left_user['id'])
    user_name = user_name[0][0]
    await sqlite_db.sql_del_user_from_db(left_user['id'])
    await bot.send_message(message.chat.id, f'Будем рады Вас видеть, {user_name}! Возвращайтесь!')


def register_handlers_for_other(dp: Dispatcher):
    dp.register_message_handler(new_member, content_types=["new_chat_members"])
    dp.register_message_handler(left_member, content_types=["left_chat_member"])

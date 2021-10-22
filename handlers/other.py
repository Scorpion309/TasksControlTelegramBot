from aiogram import types, Dispatcher

from create_bot import bot
from data_base import sqlite_db


# new user in group
async def new_member(message):
    new_user = message.new_chat_members[0]
    await sqlite_db.sql_add_user_to_db(new_user)
    await bot.send_message(message.chat.id, "Добро пожаловать, {user}!".format(user=new_user['username']))


# left user from group
async def left_member(message):
    left_user = message.left_chat_member
    await sqlite_db.sql_del_user_from_db(left_user)
    await bot.send_message(message.chat.id,
                           "Будем рады Вас видеть, {user}! Возвращайтесь!".format(user=left_user['username']))


async def echo_send(message: types.Message):
    await message.reply('message.text')


def register_handlers_for_other(dp: Dispatcher):
    dp.register_message_handler(new_member, content_types=["new_chat_members"])
    dp.register_message_handler(left_member, content_types=["left_chat_member"])
    dp.register_message_handler(echo_send)

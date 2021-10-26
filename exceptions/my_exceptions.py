from create_bot import bot
from data_base import sqlite_db


async def send_link_to_user_for_chat_from_admin(user_id, to_user_id):
    user_name = await sqlite_db.sql_get_user_name(to_user_id)
    user_name = user_name[0][0]
    await bot.send_message(user_id, f'Невозможно информировать пользователя "{user_name}".'
                                    f' Бот не может начать беседу самостоятельно.'
                                    f' Отправьте ссылку-приглашение пользователю:\nhttp://t.me/JobControlBot')

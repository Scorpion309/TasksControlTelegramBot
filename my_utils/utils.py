from create_bot import bot
from data_base import sqlite_db
from exceptions import my_exceptions

async def add_task_to_user(user_id, task_id, from_user, from_user_id, task_title, task, time_delta):
    await sqlite_db.sql_add_task_to_user(user_id, task_id, from_user_id)
    # if this task was empty before adding -> delete empty task
    sqlite_db.sql_del_empty_task_if_there_is(task_id, from_user_id)
    try:
        await bot.send_message(user_id, f'Вы получили новое задание: "{task_title}"!\n'
                                        f'От пользователя: {from_user}\n\n'
                                        f'Задание: {task}\n\n'
                                        f'До конца срока выполнения осталось: {time_delta}.')
    except Exception:
        await my_exceptions.send_link_to_user_for_chat_from_admin(from_user_id, user_id)


async def del_task_from_user(user_id, task_id, from_user, from_user_id, task_title):
    await sqlite_db.sql_del_task_from_user(task_id, user_id)
    try:
        await bot.send_message(user_id, f'Задание: "{task_title}"!\nбыло удалено пользователем: {from_user}')
    except Exception:
        await my_exceptions.send_link_to_user_for_chat_from_admin(from_user_id, user_id)


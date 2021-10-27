from datetime import datetime
from functools import wraps

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from data_base import sqlite_db
from handlers import admin
from my_utils import messages


async def add_task_to_user(user_id, task_id, from_user, from_user_id, task_title, task, time_delta):
    # adding task to user
    await sqlite_db.sql_add_task_to_user(user_id, task_id, from_user_id)
    # if this task was empty before adding -> delete empty task
    sqlite_db.sql_del_empty_task_if_there_is(task_id, from_user_id)
    # sending message to user who got new task
    await messages.message_to_user_new_task(user_id, from_user, from_user_id, task_title, task, time_delta)


async def del_task_from_user(user_id, task_id, from_user_id, task_title):
    # deleting task from user
    await sqlite_db.sql_del_task_from_user(task_id, user_id)
    # sending message to user who had this task
    await messages.message_to_user_delete_task(user_id, from_user_id, task_title)


async def check_time_format(input_time):
    try:
        input_time = datetime.strptime(input_time, '%H:%M')
        new_time = datetime.time(input_time)
        return new_time
    except ValueError:
        return False


def check_access_call(func):
    @wraps(func)
    async def wrapper(call: CallbackQuery, state: FSMContext):
        if call.from_user.id == admin.ID:
            return await func(call, state)
        else:
            await call.message.reply('Доступ запрещен!!! Для начала работы отправьте команду /moderator в группе!')
        return

    return wrapper


def check_access_message(func):
    @wraps(func)
    async def wrapper(message: Message, state: FSMContext):
        if message.from_user.id == admin.ID:
            result = await func(message, state)
            return result
        else:
            await message.reply('Доступ запрещен!!! Для начала работы отправьте команду /moderator в группе!')
        return

    return wrapper

from datetime import datetime
from functools import wraps

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from create_bot import bot
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


async def send_report(task_id, from_user_id, report):
    user_name = await sqlite_db.sql_get_user_name(from_user_id)
    user_name = user_name[0][0]
    task_info = await sqlite_db.sql_get_task_info(task_id, from_user_id)
    task_title, task, user_id_for_report, _ = task_info[0]
    report_message = await messages.message_for_report(user_name, task_title, task, report)
    confirm_kb = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton(text='Принять', callback_data=f'Choice_accept;{task_id};{from_user_id};'
                                                                             f'{task_title}',)
    decline_button = types.InlineKeyboardButton(text='Отказать', callback_data=f'Choice_decline;{task_id};{from_user_id};'
                                                                               f'{task_title}')
    confirm_kb.add(accept_button).insert(decline_button)
    await bot.send_message(user_id_for_report, report_message, reply_markup=confirm_kb)


async def send_cause_to_change_time(task_id, from_user_id, cause):
    user_name = await sqlite_db.sql_get_user_name(from_user_id)
    user_name = user_name[0][0]
    task_info = await sqlite_db.sql_get_task_info(task_id, from_user_id)
    task_title, task, user_id_for_report, execute_time = task_info[0]
    report_message = await messages.message_for_cause(user_name, task_title, task, cause)
    confirm_kb = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton(text='Продлить срок', callback_data=f'Time_accept;{task_id};'
                                                                                   f'{from_user_id};'f'{task_title}', )
    decline_button = types.InlineKeyboardButton(text='Отказать',
                                                callback_data=f'Time_decline;{task_id};{from_user_id};'
                                                              f'{task_title}')
    confirm_kb.add(accept_button).insert(decline_button)
    await bot.send_message(user_id_for_report, report_message, reply_markup=confirm_kb)

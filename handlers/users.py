from datetime import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram_calendar import simple_cal_callback, SimpleCalendar

from create_bot import bot
from data_base import sqlite_db
from my_utils import messages, utils


class FSMTasks(StatesGroup):
    action_choice = State()
    task = State()
    report = State()
    cause = State()


class FSMNewTime(StatesGroup):
    date = State()
    time = State()


async def look_for_my_tasks(message: types.Message):
    task_choice_kb = types.InlineKeyboardMarkup()
    look_for_tasks_button = types.InlineKeyboardButton(text='Просмотреть все активные задания',
                                                       callback_data='Look_for_tasks')
    finish_task_button = types.InlineKeyboardButton(text='Завершить задание', callback_data='Finish_task')
    change_execute_time_button = types.InlineKeyboardButton(text='Продлить задание', callback_data='Change_time')
    task_choice_kb.add(look_for_tasks_button).add(finish_task_button).insert(change_execute_time_button)
    await message.reply('Выберите необходимое действие:', reply_markup=task_choice_kb)
    await FSMTasks.action_choice.set()


async def processing_user_choice(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    command = call.data
    user_id = call.from_user.id
    tasks = await sqlite_db.sql_get_id_active_tasks_to_user(user_id)
    if tasks:
        if command == 'Look_for_tasks':
            for task_id, task_title, task, execute_time in tasks:
                await messages.print_tasks_for_user(user_id, task_title, task, execute_time)
            await state.finish()
            return
        else:
            choice_task_kb = types.InlineKeyboardMarkup()
            for task_id, task_title, task, execute_time in tasks:
                if command == 'Finish_task':
                    inline_btn = types.InlineKeyboardButton(text=task_title, callback_data=f'Finish_task;{task_id}')
                else:
                    inline_btn = types.InlineKeyboardButton(text=task_title, callback_data=f'Change_time;{task_id}')
                choice_task_kb.insert(inline_btn)
            await call.message.answer(f'Выберите задание:', reply_markup=choice_task_kb)
        await FSMTasks.task.set()
    else:
        await call.message.reply('У Вас нет активных заданий.')
        await state.finish()


async def get_comment_to_choice(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    command_line = call.data.split(';')
    command = command_line[0]
    task_id = command_line[1]
    async with state.proxy() as data:
        data['task_id'] = task_id
    if command == 'Finish_task':
        await call.message.reply('Напишите отчет по заданию:')
        await FSMTasks.report.set()
    else:
        await call.message.reply('Укажите причину продления срока:')
        await FSMTasks.cause.set()


async def send_report(message: types.Message, state: FSMContext):
    report = message.text
    user_id = message.from_user.id
    async with state.proxy() as data:
        task_id = data['task_id']
        await utils.send_report(task_id, user_id, report)
    await state.finish()


async def send_cause(message: types.Message, state: FSMContext):
    cause = message.text
    user_id = message.from_user.id
    async with state.proxy() as data:
        task_id = data['task_id']
        await utils.send_cause_to_change_time(task_id, user_id, cause)
    await state.finish()


async def start_command(message: types.Message):
    await messages.user_start_message(message)


async def help_command(message: types.Message):
    await messages.user_help_message(message)


async def confirm_report(call: types.CallbackQuery):
    await call.message.edit_reply_markup()
    command_line = call.data.split(';')
    command = command_line[0]
    task_id = command_line[1]
    user_id = command_line[2]
    task_title = await sqlite_db.sql_get_title_task_by_id(task_id)
    task_title = task_title[0][0]
    if command == 'Choice_accept':
        await sqlite_db.sql_del_task_from_user(task_id, user_id)
        await bot.send_message(user_id, f'Отчет по заданию "{task_title}" принят.')
        message = 'Принято'
    else:
        await bot.send_message(user_id, f'Отчет по заданию "{task_title}" не принят. Доработайте задание!')
        message = 'Отказано'
    await call.message.reply(message)


async def confirm_cause(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    command_line = call.data.split(';')
    command = command_line[0]
    task_id = command_line[1]
    user_id = command_line[2]
    task_title = await sqlite_db.sql_get_title_task_by_id(task_id)
    task_title = task_title[0][0]
    if command == 'Time_accept':
        user_name = await sqlite_db.sql_get_user_name(user_id)
        async with state.proxy() as data:
            data['task_id'] = task_id
            data['task_title'] = task_title
            data['user_id'] = user_id
            data['user_name'] = user_name[0][0]
        await bot.send_message(call.from_user.id, 'Выберите дату:',
                               reply_markup=await SimpleCalendar().start_calendar())
        await FSMNewTime.date.set()
    else:
        await bot.send_message(user_id, f'В продлении срока задания "{task_title}" отказано!')
        message = 'Отказано'
        await call.message.reply(message)
        return


async def process_simple_calendar_to_change_time(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(call, callback_data)
    if selected:
        await call.message.answer(f'Вы выбрали {date.strftime("%d-%m-%Y")}.\n'
                                  f'Введите время в формате: HH:MM')
        async with state.proxy() as data:
            data['date'] = date.strftime("%Y-%m-%d")
        await FSMNewTime.time.set()


async def get_date_time(message: types.Message, state: FSMContext):
    if await utils.check_time_format(message.text):
        time = await utils.check_time_format(message.text)
        async with state.proxy() as data:
            data['hours'] = time
            user_name = data['user_name']
            execute_time = datetime.strptime(f'{data["date"]} {data["hours"]}', '%Y-%m-%d %H:%M:%S')
            await sqlite_db.sql_change_execute_time_for_task(data['task_id'], execute_time, data['user_id'])
            await message.reply(f'Срок задания для пользователя "{user_name}" успешно изменен.')
            await bot.send_message(data['user_id'], f'Срок выполнения задания изменен на:'
                                                    f' {execute_time.strftime("%d-%m-%Y %H:%M")}.')
    await state.finish()


def register_handlers_for_users(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(help_command, commands=['help'])

    dp.register_message_handler(look_for_my_tasks, commands=['Мои_задания'], state=None)
    dp.register_callback_query_handler(processing_user_choice, state=FSMTasks.action_choice)
    dp.register_callback_query_handler(get_comment_to_choice, state=FSMTasks.task)
    dp.register_message_handler(send_report, state=FSMTasks.report)
    dp.register_message_handler(send_cause, state=FSMTasks.cause)

    dp.register_callback_query_handler(confirm_report, text_contains='Choice_')
    dp.register_callback_query_handler(confirm_cause, text_contains='Time_')
    dp.register_callback_query_handler(process_simple_calendar_to_change_time, simple_cal_callback.filter(),
                                       state=FSMNewTime.date)
    dp.register_message_handler(get_date_time, state=FSMNewTime.time)

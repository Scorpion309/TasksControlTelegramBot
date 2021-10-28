from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from data_base import sqlite_db
from my_utils import messages, utils


class FSMTasks(StatesGroup):
    action_choice = State()
    task = State()
    report = State()
    report_confirm = State()
    cause = State()
    cause_confirm = State()


async def look_for_my_tasks(message: types.Message):
    task_choice_kb = types.InlineKeyboardMarkup()
    look_for_tasks_button = types.InlineKeyboardButton(text='Просмотреть все активные задания',
                                                       callback_data='Look_for_tasks')
    finish_task_button = types.InlineKeyboardButton(text='Завершить задание', callback_data='Finish_task')
    change_execute_time_button = types.InlineKeyboardButton(text='Нужно больше времени', callback_data='Change_time')
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
    await FSMTasks.report_confirm.set()


async def send_cause(message: types.Message, state: FSMContext):
    cause = message.text
    user_id = message.from_user.id
    async with state.proxy() as data:
        task_id = data['task_id']
        await utils.send_cause_to_change_time(task_id, user_id, cause)
    await FSMTasks.cause_confirm.set()


async def start_command(message: types.Message):
    await messages.user_start_message(message)


async def help_command(message: types.Message):
    await messages.user_help_message(message)


async def confirm_report(call: types.CallbackQuery, state: FSMContext):
    print(call.data)


async def confirm_cause(call: types.CallbackQuery, state: FSMContext):
    print(call.data)


def register_handlers_for_users(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(help_command, commands=['help'])

    dp.register_message_handler(look_for_my_tasks, commands=['Просмотреть_задания'], state=None)
    dp.register_callback_query_handler(processing_user_choice, state=FSMTasks.action_choice)
    dp.register_callback_query_handler(get_comment_to_choice, state=FSMTasks.task)
    dp.register_message_handler(send_report, state=FSMTasks.report)
    dp.register_message_handler(send_cause, state=FSMTasks.cause)

    dp.register_callback_query_handler(confirm_report, state=FSMTasks.report_confirm)
    dp.register_callback_query_handler(confirm_cause, state=FSMTasks.cause_confirm)

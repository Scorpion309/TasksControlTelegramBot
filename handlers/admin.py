import time
from datetime import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import bot
from data_base import sqlite_db
from keyboards import admin_kb

ID = None
GROUP_ID = 0


class FSMAdmin(StatesGroup):
    task_title = State()
    task = State()
    to_user = State()
    to_time = State()


class FSMAddNewGroup(StatesGroup):
    name = State()


class FSMDelGroup(StatesGroup):
    confirm = State()
    group_name = State()


class FSMEditGroup(StatesGroup):
    choise = State()
    element = State()
    group_name = State()
    user_name = State()


# Is the user administrator?
# command=['moderator'], is_chat_admin=True
async def make_changes_command(message: types.Message):
    global ID, GROUP_ID
    GROUP_ID = message.chat.id
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, 'Что надо, хозяин???', reply_markup=admin_kb.kb_admin)
    await message.delete()


async def active_tasks_show(message: types.Message):
    if message.from_user.id == ID:
        tasks = await sqlite_db.sql_get_active_tasks()
        now_time = datetime.now().replace(microsecond=0)
        for task in tasks:
            deadline_time = datetime.strptime(task[5], '%Y-%m-%d %H:%M:%S')
            if deadline_time < now_time:
                time_delta = 'срок выполения задания истек!!!'
            else:
                time_delta = deadline_time - now_time
            await bot.send_message(message.from_user.id,
                                   'Название задания: {title}\n'
                                   'Отправлено: {user_name}\n'
                                   'Задание: {task_text}\n'
                                   'До конца срока осталось: {time_delta}.\n'.format(title=task[2],
                                                                                     task_text=task[3],
                                                                                     time_delta=time_delta,
                                                                                     user_name=task[1]))


async def delete_group(message: types.Message):
    if message.from_user.id == ID:
        groups_in_db = await sqlite_db.sql_get_groups_from_db()
        del_group_markup_kb = types.InlineKeyboardMarkup()
        for group, id_group in groups_in_db:
            inline_btn = types.InlineKeyboardButton(text=group, callback_data=group)
            del_group_markup_kb.add(inline_btn)

        await message.reply('Выберите группу, которую хотите удалить:',
                            reply_markup=del_group_markup_kb)
        await FSMDelGroup.group_name.set()


async def get_del_group(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        confirm_delete_kb = types.InlineKeyboardMarkup()
        confirm_button = types.InlineKeyboardButton(text='Да', callback_data=call.data)
        cancel_button = types.InlineKeyboardButton(text='Отмена', callback_data='Cancel')
        confirm_delete_kb.add(confirm_button).insert(cancel_button)
        await call.message.answer('Вы действительно хотите удалить группу {group_name}?'.format(group_name=call.data),
                                  reply_markup=confirm_delete_kb)
        await FSMDelGroup.confirm.set()


async def get_del_group_confirm(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        if call.data == 'Cancel':
            await call.message.answer('Удаление выбранной группы отменено')
        else:
            await sqlite_db.sql_del_group_from_db(call.data)
            await call.message.answer('Группа {group_name} успешно удалена из базы'.format(group_name=call.data))
        await state.finish()


async def edit_group(message: types.Message):
    if message.from_user.id == ID:
        groups_in_db = await sqlite_db.sql_get_groups_from_db()
        edit_group_markup_kb = types.InlineKeyboardMarkup()
        for group, group_id in groups_in_db:
            inline_btn = types.InlineKeyboardButton(text=group, callback_data=str(group_id) + ';' + group)
            edit_group_markup_kb.add(inline_btn)

        await message.reply('Выберите группу, которую хотите отредактировать:',
                            reply_markup=edit_group_markup_kb)
        await FSMEditGroup.group_name.set()


async def get_edit_group(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        group_id = call.data.split(';')[0]
        group = call.data.split(';')[1]
        what_edit_kb = types.InlineKeyboardMarkup()
        edit_title_button = types.InlineKeyboardButton(text='Изменить название группы',
                                                       callback_data='Change_group_name;' + str(group_id) + ';' + group)
        add_user_button = types.InlineKeyboardButton(text='Добавить пользователя',
                                                     callback_data='Add_user;' + str(group_id) + ';' + group)
        del_user_button = types.InlineKeyboardButton(text='Удалить пользователя',
                                                     callback_data='Del_user;' + str(group_id) + ';' + group)
        what_edit_kb.add(edit_title_button).add(add_user_button).insert(del_user_button)
        await call.message.answer('Выберите необходимое действие:',
                                  reply_markup=what_edit_kb)
        await FSMEditGroup.choise.set()


async def get_element_to_change(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        command_list = call.data.split(';')
        command = command_list[0]
        group_id = command_list[1]
        group_name = command_list[2]
        if command == 'Change_group_name':
            await call.message.answer('Введите новое название для выбранной группы:')

        elif command == 'Add_user':
            users_from_all_users_group = await sqlite_db.sql_get_users_group('1')
            add_user_markup_kb = types.InlineKeyboardMarkup()
            for user_name, user_id in users_from_all_users_group:
                inline_btn = types.InlineKeyboardButton(text=user_name,
                                                        callback_data='Add_user;' + str(user_id) + ';' + user_name)
                add_user_markup_kb.add(inline_btn)
            await call.message.answer('Выберите пользователя, которого хотите добавить в группу {group_name}:'
                                      ''.format(group_name=group_name), reply_markup=add_user_markup_kb)
            await sqlite_db.sql_add_user_to_group('338356618', group_id)

        else:
            users_from_group = await sqlite_db.sql_get_users_group(group_id)
            del_user_markup_kb = types.InlineKeyboardMarkup()
            for user_name, user_id in users_from_group:
                inline_btn = types.InlineKeyboardButton(text=user_name,
                                                        callback_data='Del_user;' + str(user_id) + ';' + user_name)
                del_user_markup_kb.add(inline_btn)
            await call.message.answer('Выберите пользователя, которого хотите удалить из группы {group_name}:'
                                      ''.format(group_name=group_name), reply_markup=del_user_markup_kb)
            # await sqlite_db.sql_del_user_from_group('338356618')

        await FSMEditGroup.element.set()

        await state.finish()


async def refresh_admins(message: types.Message):
    if message.from_user.id == ID:
        users = {}
        chat_admins = await message.bot.get_chat_administrators(GROUP_ID)
        if isinstance(chat_admins, list):
            for admin in chat_admins:
                users[admin['user']['id']] = {'username': admin['user']['username'], 'admin_status': True}
        else:
            users[chat_admins['user']['id']] = {'username': chat_admins['user']['username'], 'admin_status': True}
        await sqlite_db.sql_add_admins_to_db(users)
        await bot.send_message(message.from_user.id, 'Выполнено')


# Dialog for new group
async def add_new_group(message: types.Message):
    if message.from_user.id == ID:
        await FSMAddNewGroup.name.set()
        await message.reply('Введите название группы')


# Exit from FSMGroup
async def cancel_handler_new_group(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply('OK')


# Get first answer and put it into dict
async def get_group_name(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['name'] = message.text
        await sqlite_db.sql_add_group_to_db(state)
        await bot.send_message(message.from_user.id, 'Группа успешно создана')
        await state.finish()


# Dialog for add new task
async def add_new_task(message: types.Message):
    if message.from_user.id == ID:
        await FSMAdmin.task_title.set()
        await message.reply('Введите название задания')


# Exit from FSMAdmin
async def cancel_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply('OK')


# Get first answer and put it into dict
async def get_task_title(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['task_title'] = message.text
        await FSMAdmin.next()
        await message.reply('Теперь введите текст задания')


# Get second answer and put it into dict
async def get_task(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['task'] = message.text
        await FSMAdmin.next()
        await message.reply('Выберите кому Вы хотите отправить задание')


# Get third answer and put it into dict
async def get_to_user(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['to_user'] = message.text.split()
        await FSMAdmin.next()
        await message.reply('Введите срок исполнения')


# Get four's answer and put it into dict
async def get_to_time(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['to_time'] = message.text
            data['from_user'] = message.from_user.id

        await sqlite_db.sql_add_task_to_db(state)
        await bot.send_message(message.from_user.id, 'Задание успешно добавлено')
        async with state.proxy() as data:
            if isinstance(data['to_user'], list):
                for user in data['to_user']:
                    user_id = user.strip('.,;')
                    await bot.send_message(user_id, 'Вы получили новое задание!\n'
                                                    'От пользователя: {from_user}\n'
                                                    'Задание: {task}\n'
                                                    'Время выполнения: {time_delta}ч.'.format(
                        from_user=data['from_user'],
                        task=data['task'],
                        time_delta=data['to_time']))
            else:
                await bot.send_message(data['to_user'], 'Вы получили новое задание!\n'
                                                        'От пользователя: {from_user}\n'
                                                        'Задание: {task}\n'
                                                        'Время выполнения: {time_delta}ч.'.format(
                    from_user=data['from_user'],
                    task=data['task'],
                    time_delta=data['to_time']))
        time.sleep(3)
        await state.finish()


# Registering handlers
def register_handler_for_admin(dp: Dispatcher):
    dp.register_message_handler(make_changes_command, commands=['moderator'], is_chat_admin=True)

    dp.register_message_handler(refresh_admins, commands=['Обновить_список_администраторов'])

    dp.register_message_handler(active_tasks_show, commands=['Активные_задания'])

    dp.register_message_handler(add_new_group, commands=['Создать_группу'], state=None)
    dp.register_message_handler(cancel_handler_new_group, commands='отмена', state="*")
    dp.register_message_handler(cancel_handler_new_group, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(get_group_name, state=FSMAddNewGroup.name)

    dp.register_message_handler(delete_group, commands=['Удалить_группу'], state=None)
    dp.register_callback_query_handler(get_del_group, state=FSMDelGroup.group_name)
    dp.register_callback_query_handler(get_del_group_confirm, state=FSMDelGroup.confirm)

    dp.register_message_handler(edit_group, commands=['Редактировать_группу'], state=None)
    dp.register_callback_query_handler(get_edit_group, state=FSMEditGroup.group_name)
    dp.register_callback_query_handler(get_element_to_change, state=FSMEditGroup.choise)

    dp.register_message_handler(add_new_task, commands=['Новое_задание'], state=None)
    dp.register_message_handler(cancel_handler, commands='отмена', state="*")
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(get_task_title, state=FSMAdmin.task_title)
    dp.register_message_handler(get_task, state=FSMAdmin.task)
    dp.register_message_handler(get_to_user, state=FSMAdmin.to_user)
    dp.register_message_handler(get_to_time, state=FSMAdmin.to_time)

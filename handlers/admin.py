from datetime import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram_calendar import simple_cal_callback, SimpleCalendar

from create_bot import bot
from data_base import sqlite_db
from keyboards import admin_kb
from my_utils import messages
from my_utils import utils

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
    choice = State()
    element = State()
    group_name = State()


class FSMEditTask(StatesGroup):
    del_confirm = State()
    choice = State()
    element = State()
    task_title = State()
    change_recipient = State()
    users = State()
    date = State()
    time = State()


# Is the user administrator?
# command=['moderator'], is_chat_admin=True
async def make_changes_command(message: types.Message):
    global ID
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, 'Что надо, хозяин???', reply_markup=admin_kb.kb_admin)
    await message.delete()


async def active_tasks_show(message: types.Message):
    if message.from_user.id == ID:
        tasks = await sqlite_db.sql_get_active_tasks(message.from_user.id)
        now_time = datetime.now().replace(microsecond=0)
        for task in tasks:
            deadline_time = datetime.strptime(task[5], '%Y-%m-%d %H:%M:%S')
            if deadline_time < now_time:
                time_delta = 'срок выполения задания истек!!!'
            else:
                time_delta = deadline_time - now_time
            task_title = task[2]
            task_text = task[3]
            to_user = task[1]
            await messages.message_print_tasks_for_sender(message.from_user.id, task_title, to_user, task_text, time_delta)


async def delete_group(message: types.Message):
    if message.from_user.id == ID:
        groups_in_db = await sqlite_db.sql_get_groups_from_db()
        del_group_markup_kb = types.InlineKeyboardMarkup()
        for group, id_group in groups_in_db:
            inline_btn = types.InlineKeyboardButton(text=group, callback_data=str(id_group) + ';' + group)
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
        group_name = call.data.split(';')[1]
        await call.message.answer('Вы действительно хотите удалить группу {group_name}?'.format(group_name=group_name),
                                  reply_markup=confirm_delete_kb)
        await FSMDelGroup.confirm.set()


async def get_del_group_confirm(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        if call.data == 'Cancel':
            await call.message.answer('Удаление выбранной группы отменено.')
        else:
            call_data_list = call.data.split(';')
            group_id = call_data_list[0]
            group_name = call_data_list[1]
            users_in_group = await sqlite_db.sql_get_users_from_group(group_id)
            for user_name, user_id in users_in_group:
                await sqlite_db.sql_del_user_from_group(user_id)
            await sqlite_db.sql_del_group_from_db(group_id)
            await call.message.answer('Группа {group_name} успешно удалена из базы'.format(group_name=group_name))
        await state.finish()


async def edit_group(message: types.Message):
    if message.from_user.id == ID:
        groups_in_db = await sqlite_db.sql_get_groups_from_db()
        if groups_in_db:
            edit_group_markup_kb = types.InlineKeyboardMarkup()
            for group, group_id in groups_in_db:
                inline_btn = types.InlineKeyboardButton(text=group, callback_data=str(group_id) + ';' + group)
                edit_group_markup_kb.insert(inline_btn)
            await message.reply('Выберите группу, которую хотите отредактировать:',
                                reply_markup=edit_group_markup_kb)
            await FSMEditGroup.group_name.set()
        else:
            await message.reply('Невозможно выполнить команду. В базе отсутствуют группы. Попробуйте создать новую.')


async def get_edit_group(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        group_id = call.data.split(';')[0]
        group = call.data.split(';')[1]
        what_edit_kb = types.InlineKeyboardMarkup()
        edit_title_button = types.InlineKeyboardButton(text='Изменить название группы',
                                                       callback_data='Change_group_name;' + str(group_id) + ';' + group)
        look_for_user_button = types.InlineKeyboardButton(text='Просмотреть список пользователей',
                                                          callback_data='Look_for_user;' + str(group_id) + ';' + group)
        add_user_button = types.InlineKeyboardButton(text='Добавить пользователя',
                                                     callback_data='Add_user;' + str(group_id) + ';' + group)
        del_user_button = types.InlineKeyboardButton(text='Удалить пользователя',
                                                     callback_data='Del_user;' + str(group_id) + ';' + group)
        what_edit_kb.add(edit_title_button).add(look_for_user_button).add(add_user_button).insert(del_user_button)
        await call.message.answer('Выберите необходимое действие:',
                                  reply_markup=what_edit_kb)
        await FSMEditGroup.choice.set()


async def get_element_to_change(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        command_list = call.data.split(';')
        command = command_list[0]
        group_id = command_list[1]
        group_name = command_list[2]
        if command == 'Change_group_name':
            await call.message.answer('Введите новое название для выбранной группы:')
            async with state.proxy() as data:
                data['group_id'] = group_id
        elif command == 'Add_user':
            users_from_all_users_group = await sqlite_db.sql_get_users_from_group('1')
            if users_from_all_users_group:
                add_user_markup_kb = types.InlineKeyboardMarkup()
                for user_name, user_id in users_from_all_users_group:
                    inline_btn = types.InlineKeyboardButton(text=user_name,
                                                            callback_data='Add_user;' +
                                                                          str(group_id) + ';' + group_name +
                                                                          ';' + str(user_id) + ';' + user_name)
                    add_user_markup_kb.row(inline_btn)
                await call.message.answer('Выберите пользователя, которого хотите добавить в группу {group_name}:'
                                          ''.format(group_name=group_name), reply_markup=add_user_markup_kb)
            else:
                await call.message.answer('Нет пользователей, которых можно было бы добавить в группу.')
                await state.finish()
                return
        else:
            users_from_group = await sqlite_db.sql_get_users_from_group(group_id)
            if users_from_group:
                if command == 'Look_for_user':
                    users = ''
                    for user_name, _ in users_from_group:
                        users = users + user_name + '; '
                    await call.message.answer(users)
                    await state.finish()
                    return
                else:
                    del_user_markup_kb = types.InlineKeyboardMarkup()
                    for user_name, user_id in users_from_group:
                        inline_btn = types.InlineKeyboardButton(text=user_name,
                                                                callback_data='Del_user;' + str(group_id) +
                                                                              ';' + group_name +
                                                                              ';' + str(user_id) + ';' + user_name)
                        del_user_markup_kb.add(inline_btn)
                    await call.message.answer('Выберите пользователя, которого хотите удалить из группы {group_name}:'
                                              ''.format(group_name=group_name), reply_markup=del_user_markup_kb)
            else:
                await call.message.answer('В группе нет пользователей.')
                await state.finish()
                return
        await FSMEditGroup.element.set()


async def change_group_name(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['new_name'] = message.text
            new_name = message.text
            group_id = data['group_id']
            await sqlite_db.sql_change_group_name(group_id, new_name)
            await bot.send_message(message.from_user.id, 'Название группы успешно изменено на {group_name}'
                                                         ''.format(group_name=new_name))
        await state.finish()


async def change_group(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        command_list = call.data.split(';')
        command = command_list[0]
        group_id = command_list[1]
        group_name = command_list[2]
        user_id = command_list[3]
        user_name = command_list[4]
        if command == 'Add_user':
            await sqlite_db.sql_add_user_to_group(user_id, group_id)
            await call.message.answer('Пользователь {user_name} успешно добавлен в группу {group_name}.'
                                      ''.format(group_name=group_name, user_name=user_name))
        else:
            await sqlite_db.sql_del_user_from_group(user_id)
            await call.message.answer('Пользователь {user_name} успешно удален из группы {group_name}.'
                                      ''.format(group_name=group_name, user_name=user_name))
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
        await message.reply('Введите название для задания:')


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
        await message.reply('Теперь введите текст задания:')


# Get second answer and put it into dict
async def get_task(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['task'] = message.text
        await FSMAdmin.next()
        await message.reply('Выберите кому Вы хотите отправить задание:')


# Get third answer and put it into dict
async def get_to_user(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['to_user'] = message.text.split()
        await FSMAdmin.next()
        await message.reply('Введите срок исполнения:')


# Get four's answer and put it into dict
async def get_to_time(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        from_user_id = message.from_user.id
        from_user = message.from_user.username
        async with state.proxy() as data:
            data['to_time'] = message.text
            data['from_user'] = from_user_id
            data['from_user_username'] = from_user
            task_title = data['task_title']
            task = data['task']
            time_delta = data['to_time']
            # sending message to users
            if isinstance(data['to_user'], list):
                for user in data['to_user']:
                    user_id = user.strip('.,;')
                    await messages.message_to_user_new_task(user_id, from_user, from_user_id, task_title, task,
                                                            time_delta)
            else:
                await messages.message_to_user_new_task(data['to_user'], from_user, ID, task_title, task, time_delta)
        await sqlite_db.sql_add_task_to_db(state)
        await bot.send_message(message.from_user.id, 'Задание успешно добавлено')
        await state.finish()


async def edit_task(message: types.Message):
    if message.from_user.id == ID:
        active_tasks = set(await sqlite_db.sql_get_id_active_tasks(message.from_user.id))
        if active_tasks:
            tasks_markup_kb = types.InlineKeyboardMarkup()
            for task_id, task_title in active_tasks:
                inline_btn = types.InlineKeyboardButton(text=task_title, callback_data=f'{str(task_id)};'
                                                                                       f'{task_title}')
                tasks_markup_kb.insert(inline_btn)
            await message.reply('Выберите задание, которое хотите отредактировать:',
                                reply_markup=tasks_markup_kb)
            await FSMEditTask.task_title.set()
        else:
            await message.reply('В базе отсутствуют активные задания. Сначала необходимо добавить новое!')


async def choice_action_to_task(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        task_info = call.data.split(';')
        async with state.proxy() as data:
            data['task_id'] = task_info[0]
            data['task_title'] = task_info[1]
        which_action_kb = types.InlineKeyboardMarkup()
        edit_task_button = types.InlineKeyboardButton(text='Изменить задание', callback_data=f'Edit_task')
        del_task_button = types.InlineKeyboardButton(text='Удалить задание', callback_data=f'Del_task')
        change_recipient_button = types.InlineKeyboardButton(text='Изменить получателя', callback_data=f'Edit_users')
        change_execute_time_button = types.InlineKeyboardButton(text='Изменить срок выполнения задания',
                                                                callback_data=f'Edit_data')
        which_action_kb.insert(edit_task_button).insert(del_task_button)
        which_action_kb.insert(change_recipient_button).insert(change_execute_time_button)
        await call.message.answer('Выберите необходимое действие:', reply_markup=which_action_kb)
        await FSMEditTask.choice.set()


async def process_chosen_action_to_task(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        command = call.data
        if command == 'Edit_task':
            await call.message.answer('Введите новый текст для задания:')
            await FSMEditTask.element.set()
        elif command == 'Del_task':
            confirm_delete_kb = types.InlineKeyboardMarkup()
            confirm_button = types.InlineKeyboardButton(text='Да', callback_data='Yes')
            cancel_button = types.InlineKeyboardButton(text='Отмена', callback_data='Cancel')
            confirm_delete_kb.add(confirm_button).insert(cancel_button)
            await call.message.answer('Вы действительно хотите удалить задание?', reply_markup=confirm_delete_kb)
            await FSMEditTask.del_confirm.set()
        elif command == 'Edit_users':
            edit_user_kb = types.InlineKeyboardMarkup()
            add_user_button = types.InlineKeyboardButton(text='Добавить задание пользователю',
                                                         callback_data=f'Add_task_to_user')
            del_user_button = types.InlineKeyboardButton(text='Удалить задание у пользователя',
                                                         callback_data=f'Del_task_from_user')
            add_to_group_button = types.InlineKeyboardButton(text='Добавить задание группе пользователей',
                                                             callback_data=f'Add_task_to_user_group')
            del_from_group_button = types.InlineKeyboardButton(text='Удалить задание у группы пользователей',
                                                               callback_data=f'Del_task_from_user_group')
            edit_user_kb.add(add_user_button).add(del_user_button).add(add_to_group_button).add(del_from_group_button)
            await call.message.answer('Выберите необходимое действие:', reply_markup=edit_user_kb)
            await FSMEditTask.change_recipient.set()
        else:
            await call.message.answer('Выберите дату:', reply_markup=await SimpleCalendar().start_calendar())
            await FSMEditTask.date.set()


async def process_simple_calendar(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(call, callback_data)
    if selected:
        await call.message.answer(f'Вы выбрали {date.strftime("%d-%m-%Y")}.\n'
                                  f'Введите время в формате: HH:MM')
        async with state.proxy() as data:
            data['date'] = date.strftime("%Y-%m-%d")
        await FSMEditTask.time.set()


async def get_change_time(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['hours'] = message.text
            task_id = data['task_id']
            deadline_time = datetime.strptime(f'{data["date"]} {data["hours"]}:00', '%Y-%m-%d %H:%M:%S')
            await sqlite_db.sql_change_execute_time_for_task(task_id, deadline_time)
        await message.reply('Срок выполнения задания изменен.')
        await state.finish()


async def change_task_text(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        new_text = message.text
        async with state.proxy() as data:
            data['new_text'] = new_text
            task_id = data['task_id']
            users_which_have_task = await sqlite_db.sql_get_users_which_have_this_task(task_id)
            task_title = data['task_title']
            await sqlite_db.sql_change_task_text(task_id, new_text)
            await bot.send_message(message.from_user.id, 'Задание успешно изменено.')
            if users_which_have_task:
                for user_name, user_id in users_which_have_task:
                    await messages.message_to_user_change_task(user_id, ID, task_title)
        await state.finish()


async def del_task(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        if call.data == 'Cancel':
            await call.message.answer('Удаление задания отменено.')
        else:
            async with state.proxy() as data:
                task_id = data['task_id']
                task_title = data['task_title']
                users_which_have_task = await sqlite_db.sql_get_users_which_have_this_task(task_id)
                await sqlite_db.sql_del_task_from_db(task_id)
                if users_which_have_task:
                    for user_name, user_id in users_which_have_task:
                        await messages.message_to_user_delete_task(user_id, ID, task_title)
            await call.message.answer('Задание успешно удалено из базы')
        await state.finish()


async def edit_recipients_for_task(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        command = call.data
        async with state.proxy() as data:
            task_id = data['task_id']
            if command == 'Add_task_to_user':
                users_from_db_which_have_task = set(await sqlite_db.sql_get_users_which_have_this_task(task_id))
                all_user_from_db = set(await sqlite_db.sql_get_user_from_db_without_admins())
                users_for_add = all_user_from_db.difference(users_from_db_which_have_task)
                if users_for_add:
                    add_user_markup_kb = types.InlineKeyboardMarkup()
                    for user_name, user_id in users_for_add:
                        inline_btn = types.InlineKeyboardButton(text=user_name, callback_data=f'Add_to_user;{user_id}')
                        add_user_markup_kb.insert(inline_btn)
                    await call.message.answer(f'Выберите пользователя, которому хотите отправить задание:',
                                              reply_markup=add_user_markup_kb)
                    await FSMEditTask.users.set()
                else:
                    await call.message.answer('Нет пользователей, которым можно отправить задание.')
                    await state.finish()
                    return
            elif command == 'Del_task_from_user':
                users_from_db_which_have_task = set(await sqlite_db.sql_get_users_which_have_this_task(task_id))
                if users_from_db_which_have_task:
                    del_user_markup_kb = types.InlineKeyboardMarkup()
                    for user_name, user_id in users_from_db_which_have_task:
                        inline_btn = types.InlineKeyboardButton(text=user_name, callback_data=f'Del_from_user;'
                                                                                              f'{user_id}')
                        del_user_markup_kb.insert(inline_btn)
                    await call.message.answer(f'Выберите пользователя у которого хотите удалить задание:',
                                              reply_markup=del_user_markup_kb)
                    await FSMEditTask.users.set()
                else:
                    await call.message.answer('Нет пользователей, у которых можно удалить задание.')
                    await state.finish()
                    return
            elif command == 'Add_task_to_user_group':
                groups_from_db = await sqlite_db.sql_get_groups_from_db()
                if groups_from_db:
                    add_to_group_markup_kb = types.InlineKeyboardMarkup()
                    for group_name, group_id in groups_from_db:
                        inline_btn = types.InlineKeyboardButton(text=group_name, callback_data=f'Add_to_group;'
                                                                                               f'{group_id}')
                        add_to_group_markup_kb.insert(inline_btn)
                    await call.message.answer(f'Выберите группу, в которую хотите отправить задание:',
                                              reply_markup=add_to_group_markup_kb)
                    await FSMEditTask.users.set()
                else:
                    await call.message.answer('Нет групп, которым можно добавить задание.')
                    await state.finish()
                    return
            else:
                groups_with_users = set(await sqlite_db.sql_get_groups_from_which_users_have_this_task(task_id))
                if groups_with_users:
                    del_from_group_markup_kb = types.InlineKeyboardMarkup()
                    for group_name, group_id in groups_with_users:
                        inline_btn = types.InlineKeyboardButton(text=group_name, callback_data=f'Del_from_group;'
                                                                                               f'{group_id}')
                        del_from_group_markup_kb.insert(inline_btn)
                    await call.message.answer(f'Выберите группу, из которой хотите удалить задание:',
                                              reply_markup=del_from_group_markup_kb)
                    await FSMEditTask.users.set()
                else:
                    await call.message.answer('Нет таких групп.')
                    await state.finish()
                    return


async def change_task(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id == ID:
        await call.message.edit_reply_markup()
        command_list = call.data.split(';')
        command = command_list[0]
        from_user = call.from_user.username
        now_time = datetime.now().replace(microsecond=0)
        async with state.proxy() as data:
            task_id = data['task_id']
            task_data = await sqlite_db.sql_get_task_data(task_id)
            task_title = task_data[0][0]
            task = task_data[0][1]
            deadline_time = datetime.strptime(task_data[0][2], '%Y-%m-%d %H:%M:%S')
            time_delta = deadline_time - now_time

            if command == 'Add_to_user':
                user_id = command_list[1]
                await utils.add_task_to_user(user_id, task_id, from_user, ID, task_title, task, time_delta)
                await call.message.reply(f'Задание "{task_title}" успешно отправлено пользователю.')
            elif command == 'Del_from_user':
                user_id = command_list[1]
                await utils.del_task_from_user(user_id, task_id, ID, task_title)
                await call.message.reply(f'Задание "{task_title}" успешно удалено у пользователя.')
                users = await sqlite_db.sql_get_users_which_have_this_task(task_id)
                #  if there are no users who have this task -> add empty task to find it later.
                if not users:
                    await sqlite_db.sql_add_empty_task(task_id, ID)
            else:
                group_id = command_list[1]
                users_from_group = set(await sqlite_db.sql_get_users_from_group(group_id))
                users_which_have_this_task = set(await sqlite_db.sql_get_users_which_have_this_task(task_id))
                if command == 'Add_to_group':
                    users_from_group = users_from_group - users_which_have_this_task
                    if users_from_group:
                        for user_name, user_id in users_from_group:
                            await utils.add_task_to_user(user_id, task_id, from_user, ID, task_title, task, time_delta)
                        await call.message.reply(f'Задание "{task_title}" успешно отправлено пользователям группы.')
                    else:
                        await call.message.reply('В группе все пользователи уже получили это задание,'
                                                 ' либо пользователи отсутствуют вовсе.')
                else:
                    users_from_group = users_from_group & users_which_have_this_task
                    if users_from_group:
                        for user_name, user_id in users_which_have_this_task:
                            await utils.del_task_from_user(user_id, task_id, ID, task_title)
                        users = await sqlite_db.sql_get_users_which_have_this_task(task_id)
                        # if there are no users who have this task -> add empty task to find it later.
                        if not users:
                            await sqlite_db.sql_add_empty_task(task_id, ID)
                    else:
                        await call.message.reply('В выбранной группе нет пользователей с таким заданием.')
            await state.finish()


# Registering handlers
def register_handler_for_admin(dp: Dispatcher):
    dp.register_message_handler(make_changes_command, commands=['moderator'], is_chat_admin=True)

    dp.register_message_handler(refresh_admins, commands=['Обновить_список_администраторов'])

    dp.register_message_handler(active_tasks_show, commands=['Активные_задания'])

    dp.register_message_handler(edit_task, commands=['Изменить_задание'], state=None)
    dp.register_callback_query_handler(choice_action_to_task, state=FSMEditTask.task_title)
    dp.register_callback_query_handler(process_chosen_action_to_task, state=FSMEditTask.choice)
    dp.register_message_handler(change_task_text, state=FSMEditTask.element)
    dp.register_callback_query_handler(del_task, state=FSMEditTask.del_confirm)
    dp.register_callback_query_handler(edit_recipients_for_task, state=FSMEditTask.change_recipient)
    dp.register_callback_query_handler(change_task, state=FSMEditTask.users)
    dp.register_callback_query_handler(process_simple_calendar, simple_cal_callback.filter(), state=FSMEditTask.date)
    dp.register_message_handler(get_change_time, state=FSMEditTask.time)

    dp.register_message_handler(add_new_group, commands=['Создать_группу'], state=None)
    dp.register_message_handler(get_group_name, state=FSMAddNewGroup.name)

    dp.register_message_handler(delete_group, commands=['Удалить_группу'], state=None)
    dp.register_callback_query_handler(get_del_group, state=FSMDelGroup.group_name)
    dp.register_callback_query_handler(get_del_group_confirm, state=FSMDelGroup.confirm)

    dp.register_message_handler(edit_group, commands=['Редактировать_группу'], state=None)
    dp.register_callback_query_handler(get_edit_group, state=FSMEditGroup.group_name)
    dp.register_message_handler(change_group_name, state=FSMEditGroup.element)
    dp.register_callback_query_handler(get_element_to_change, state=FSMEditGroup.choice)
    dp.register_callback_query_handler(change_group, state=FSMEditGroup.element)

    dp.register_message_handler(add_new_task, commands=['Новое_задание'], state=None)
    dp.register_message_handler(cancel_handler, commands='отмена', state="*")
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(get_task_title, state=FSMAdmin.task_title)
    dp.register_message_handler(get_task, state=FSMAdmin.task)
    dp.register_message_handler(get_to_user, state=FSMAdmin.to_user)
    dp.register_message_handler(get_to_time, state=FSMAdmin.to_time)

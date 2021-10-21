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


# Is the user administrator?
# command=['moderator'], is_chat_admin=True
async def make_changes_command(message: types.Message):
    global ID, GROUP_ID
    GROUP_ID = message.chat.id
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, 'Что надо, хозяин???', reply_markup=admin_kb.kb_admin)
    await message.delete()


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
            await state.finish()
        else:
            await sqlite_db.sql_del_group_from_db(call.data)
            await call.message.answer('Группа {group_name} успешно удалена из базы'.format(group_name=call.data))
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


# Get first answer and put it into dict
async def get_task_title(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['task_title'] = message.text
        await FSMAdmin.next()
        await message.reply('Теперь введите текст задания')


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
            data['to_user'] = message.text
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
        await state.finish()


# Registering handlers
def register_handler_for_admin(dp: Dispatcher):
    dp.register_message_handler(make_changes_command, commands=['moderator'], is_chat_admin=True)

    dp.register_message_handler(refresh_admins, commands=['Обновить_список_администраторов'])

    dp.register_message_handler(add_new_group, commands=['Создать_группу'], state=None)
    dp.register_message_handler(cancel_handler_new_group, commands='отмена', state="*")
    dp.register_message_handler(cancel_handler_new_group, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(get_group_name, state=FSMAddNewGroup.name)

    dp.register_message_handler(delete_group, commands=['Удалить_группу'], state=None)
    dp.register_callback_query_handler(get_del_group, state=FSMDelGroup.group_name)
    dp.register_callback_query_handler(get_del_group_confirm, state=FSMDelGroup.confirm)

    dp.register_message_handler(add_new_task, commands=['Новое_задание'], state=None)
    dp.register_message_handler(cancel_handler, commands='отмена', state="*")
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(get_task_title, state=FSMAdmin.task_title)
    dp.register_message_handler(get_task, state=FSMAdmin.task)
    dp.register_message_handler(get_to_user, state=FSMAdmin.to_user)
    dp.register_message_handler(get_to_time, state=FSMAdmin.to_time)

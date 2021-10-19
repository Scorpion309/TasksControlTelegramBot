from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import bot
from data_base import sqlite_db
from keyboards import admin_kb

ID = None
GROUP_ID = None
NEW_USERS = {}
LEFT_USERS = {}

class FSMAdmin(StatesGroup):
    task_title = State()
    task = State()
    to_user = State()
    to_time = State()


# Is the user administrator?
# command=['moderator'], is_chat_admin=True
async def make_changes_command(message: types.Message):
    global ID, GROUP_ID
    GROUP_ID = message.chat.id
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, 'Что надо, хозяин???', reply_markup=admin_kb.kb_admin)
    await message.delete()


# new user in group
async def new_member(message):
    global NEW_USERS
    new_user = message.new_chat_members[0]
    NEW_USERS[new_user['id']] = {'username': new_user['username'], 'admin_status': False}
    await bot.send_message(message.chat.id, "Добро пожаловать, {user}!".format(user=new_user['username']))

# left user from group
async def left_member(message):
    global LEFT_USERS
    left_user = message.left_chat_member
    LEFT_USERS[left_user['id']] = {'username': left_user['username'], 'admin_status': False}
    await bot.send_message(message.chat.id, "Будем рады Вас видеть, {user}! Возвращайтесь!".format(user=left_user['username']))

# command=['Обновить список пользователей']
async def refresh_users(message: types.Message):
    if message.from_user.id == ID:
        users = {}
        chat_admins = await message.bot.get_chat_administrators(GROUP_ID)
        for admin in chat_admins:
            users[admin['user']['id']] = {'username': admin['user']['username'], 'admin_status': True}
        print(NEW_USERS)
        print(LEFT_USERS)


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
        await state.finish()


# Registering handlers
def register_handler_for_admin(dp: Dispatcher):
    dp.register_message_handler(new_member, content_types=["new_chat_members"])
    dp.register_message_handler(left_member, content_types=["left_chat_member"])
    dp.register_message_handler(make_changes_command, commands=['moderator'], is_chat_admin=True)
    dp.register_message_handler(refresh_users, commands=['Обновить_список_пользователей'])
    dp.register_message_handler(add_new_task, commands=['Новое_задание'], state=None)
    dp.register_message_handler(cancel_handler, commands='отмена', state="*")
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(get_task_title, state=FSMAdmin.task_title)
    dp.register_message_handler(get_task, state=FSMAdmin.task)
    dp.register_message_handler(get_to_user, state=FSMAdmin.to_user)
    dp.register_message_handler(get_to_time, state=FSMAdmin.to_time)



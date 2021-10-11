from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp


class FSMAdmin(StatesGroup):
    task_title = State()
    task = State()
    to_user = State()
    to_time = State()


# Dialog for add new task
async def add_new_task(message: types.Message, state=None):
    await FSMAdmin.task_title.set()
    await message.reply('Введите название задания')


# Get first answer and put it into dict
async def get_task_title(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['task_title'] = message.text
    await FSMAdmin.next()
    await message.reply('Теперь введите текст задания')


# Get second answer and put it into dict
async def get_task(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['task'] = message.text
    await FSMAdmin.next()
    await message.reply('Выберите кому Вы хотите отправить задание')


# Get third answer and put it into dict
async def get_to_user(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['to_user'] = message.text
    await FSMAdmin.next()
    await message.reply('Введите срок исполнения')


# Get four's answer and put it into dict
async def get_to_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['to_time'] = message.text
    async with state.proxy() as data:
        await message.reply(str(data))
    await state.finish()


# Registering handlers
def register_handler_for_admin(dp: Dispatcher):
    dp.register_message_handler(add_new_task, commands=['Новое_задание'], state=None)
    dp.register_message_handler(get_task_title, state=FSMAdmin.task_title)
    dp.register_message_handler(get_task, state=FSMAdmin.task)
    dp.register_message_handler(get_to_user, state=FSMAdmin.to_user)
    dp.register_message_handler(get_to_time, state=FSMAdmin.to_time)

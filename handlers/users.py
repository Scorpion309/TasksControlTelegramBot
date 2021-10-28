from aiogram import types, Dispatcher

from my_utils import messages


async def start_command(message: types.Message):
    await messages.user_start_message(message)


async def help_command(message: types.Message):
    await messages.user_help_message(message)


def register_handlers_for_users(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(help_command, commands=['help'])

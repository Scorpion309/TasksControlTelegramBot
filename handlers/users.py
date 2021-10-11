from aiogram import types, Dispatcher

from create_bot import bot
from keyboards import kb_client


# @dp.message_handler(commands=['start', 'help'])
async def command_start(message: types.Message):
    try:
        await bot.send_message(message.from_user.id, 'My message', reply_markup=kb_client)
        await message.delete()
    except Exception:
        await message.reply('Общение с ботом только через ЛС, напишите ему:\nhttp://t.me/JobControlBot')


def register_handlers_for_users(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start', 'help'])


from aiogram import types, Dispatcher


async def echo_send(message: types.Message):
    # chat_admins = await message.chat.get_administrators()
    # for admin in chat_admins:
    #     print(admin)

    await message.reply('message.text')


def register_handlers_for_other(dp: Dispatcher):
    dp.register_message_handler(echo_send)

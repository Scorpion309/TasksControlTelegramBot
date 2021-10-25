from create_bot import bot


async def send_link_to_user_for_chat(user_id):
    await bot.send_message(user_id, 'Невозможно информировать пользователя о новом задании. Бот не может начать беседу'
                                    ' самостоятельно. Отправьте ссылку-приглашение пользователю:\n'
                                    'http://t.me/JobControlBot')

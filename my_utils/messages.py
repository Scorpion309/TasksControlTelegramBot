from aiogram import types

from create_bot import bot
from exceptions import my_exceptions
from keyboards import kb_users


async def message_to_user_new_task(user_id, from_user, from_user_id, task_title, task, time_delta):
    try:
        await bot.send_message(user_id, f'Вы получили новое задание: "{task_title}"!\n'
                                        f'От пользователя: {from_user}\n\n'
                                        f'Задание: {task}\n\n'
                                        f'До конца срока выполнения осталось: {time_delta}.')
    except Exception:
        # if user have not chat with bot
        await my_exceptions.send_user_link_for_chat_to_admin(from_user_id, user_id)


async def message_to_user_delete_task(user_id, from_user_id, task_title):
    try:
        await bot.send_message(user_id, f'Задание: "{task_title}" было удалено создателем.')
    except Exception:
        # if user have not chat with bot
        await my_exceptions.send_user_link_for_chat_to_admin(from_user_id, user_id)


async def message_to_user_change_task(user_id, from_user_id, task_title):
    try:
        await bot.send_message(user_id, f'Задание "{task_title}" было изменено создателем.\n'
                                        f' Проверьте задание!')
    except Exception:
        await my_exceptions.send_user_link_for_chat_to_admin(from_user_id, user_id)


async def print_tasks_for_sender(user_id, task_title, to_user, task, time_delta):
    try:
        await bot.send_message(user_id, f'Название задания: "{task_title}"\n'
                                        f'Отправлено: "{to_user}"\n\n'
                                        f'Задание: {task}\n\n'
                                        f'До конца срока осталось: {time_delta}.\n')
    except Exception:
        pass


async def user_start_message(message: types.Message):
    try:
        await bot.send_message(message.from_user.id, 'Выберите необходимую команду в меню', reply_markup=kb_users)
        await message.delete()
    except Exception:
        await message.reply('Общение с ботом только через ЛС, напишите ему:\nhttp://t.me/JobControlBot')


async def user_help_message(message: types.Message):
    pass

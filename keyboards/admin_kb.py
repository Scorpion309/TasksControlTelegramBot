from aiogram.types import ReplyKeyboardMarkup, KeyboardButton  # , ReplyKeyboardRemove

new_task_button = KeyboardButton('/Новое_задание')
all_active_tasks_button = KeyboardButton('/Активные задания')
change_task_button = KeyboardButton('/Изменить_задание')
reload_users_button = KeyboardButton('/Обновить_список_пользователей')

kb_admin = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_admin.add(new_task_button).insert(all_active_tasks_button).insert(change_task_button)
kb_admin.add(reload_users_button)

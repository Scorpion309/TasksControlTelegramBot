from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

my_active_tasks_button = KeyboardButton('/Просмотреть_задания')
change_execute_time_button = KeyboardButton('/Продлить_срок')

kb_users = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_users.add(my_active_tasks_button).insert(change_execute_time_button)

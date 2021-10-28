from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

my_active_tasks_button = KeyboardButton('/Мои_задания')

kb_users = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_users.add(my_active_tasks_button)

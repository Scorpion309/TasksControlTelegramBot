from aiogram.types import ReplyKeyboardMarkup, KeyboardButton#, ReplyKeyboardRemove

start_button = KeyboardButton('/start')
new_task_button = KeyboardButton('/Новое_задание')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_client.add(start_button).insert(new_task_button)

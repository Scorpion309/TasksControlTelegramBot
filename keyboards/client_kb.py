from aiogram.types import ReplyKeyboardMarkup, KeyboardButton  # , ReplyKeyboardRemove
from data_base import sqlite_db

my_active_tasks_button = KeyboardButton('/Просмотреть задания')
change_execute_time_button = KeyboardButton('/Продлить срок')



kb_client = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_client.add(my_active_tasks_button).insert(change_execute_time_button)

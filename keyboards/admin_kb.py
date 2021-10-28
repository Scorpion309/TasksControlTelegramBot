from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

new_task_button = KeyboardButton('/Новое_задание')
all_active_tasks_button = KeyboardButton('/Активные_задания')
change_task_button = KeyboardButton('/Изменить_задание')
create_new_group = KeyboardButton('/Создать_группу')
edit_group = KeyboardButton('/Редактировать_группу')
delete_group = KeyboardButton('/Удалить_группу')
reload_users_button = KeyboardButton('/Обновить_список_администраторов')

kb_admin = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb_admin.add(new_task_button).insert(all_active_tasks_button).insert(change_task_button)
kb_admin.add(create_new_group).insert(edit_group).insert(delete_group)
kb_admin.add(reload_users_button)

from data_base import sqlite_db
from my_utils import messages


async def add_task_to_user(user_id, task_id, from_user, from_user_id, task_title, task, time_delta):
    # adding task to user
    await sqlite_db.sql_add_task_to_user(user_id, task_id, from_user_id)
    # if this task was empty before adding -> delete empty task
    sqlite_db.sql_del_empty_task_if_there_is(task_id, from_user_id)
    # sending message to user who got new task
    await messages.message_to_user_new_task(user_id, from_user, from_user_id, task_title, task, time_delta)


async def del_task_from_user(user_id, task_id, from_user_id, task_title):
    # deleting task from user
    await sqlite_db.sql_del_task_from_user(task_id, user_id)
    # sending message to user who had this task
    await messages.message_to_user_delete_task(user_id, from_user_id, task_title)

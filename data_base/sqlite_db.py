import sqlite3 as sq
from datetime import datetime, timedelta, timezone


def sql_start():
    global base, cur
    base = sq.connect('tasks.db')
    cur = base.cursor()
    if base:
        print('Data base connected!')
    base.execute('CREATE TABLE IF NOT EXISTS groups('
                 'id INTEGER PRIMARY KEY,'
                 'group_name VARCHAR(255) NOT NULL);')

    base.execute('CREATE TABLE IF NOT EXISTS users('
                 'user_id INTEGER PRIMARY KEY,'
                 'group_id INTEGER,'
                 'user_name VARCHAR(255) NOT NULL,'
                 'admin BOOLEAN NOT NULL,'
                 'FOREIGN KEY(group_id) REFERENCES groups(id));')

    base.execute('CREATE TABLE IF NOT EXISTS tasks('
                 'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                 'task VARCHAR(255) NOT NULL,'
                 'start_time DATETIME,'
                 'execute_time DATETIME);')

    base.execute('CREATE TABLE IF NOT EXISTS task('
                 'from_user_id INTEGER,'
                 'to_user_id INTEGER,'
                 'task_id INTEGER,'
                 'active BOOLEAN NOT NULL,'
                 'FOREIGN KEY(from_user_id) REFERENCES users(user_id),'
                 'FOREIGN KEY(to_user_id) REFERENCES users(user_id),'
                 'FOREIGN KEY(task_id) REFERENCES tasks(id));')
    base.commit()


async def sql_add_task_to_db(state):
    async with state.proxy() as data:
        start_time = datetime.now(timezone.utc)
        to_time = start_time + timedelta(hours=int(data['to_time']))
        cur.execute('INSERT INTO tasks (task, start_time, execute_time)'
                    ' VALUES (?, ?, ?)', (data['task'], start_time, to_time))
        task_id = cur.lastrowid
        for user in data['to_user']:
            cur.execute('INSERT INTO task (from_user_id, to_user_id, task_id, active)'
                        ' VALUES (?, ?, ?, ?)', (data['from_user'], user, task_id, True))
        base.commit()


async def sql_bd():
    print('Print DataBase:')
    cur.execute('SELECT * FROM tasks;')
    result = cur.fetchall()
    print('tasks:', result)
    cur.execute('SELECT * FROM task;')
    result = cur.fetchall()
    print('task:', result)
    cur.execute('SELECT * FROM users;')
    result = cur.fetchall()
    print('users:', result)
    cur.execute('SELECT * FROM groups;')
    result = cur.fetchall()
    print('groups:', result)
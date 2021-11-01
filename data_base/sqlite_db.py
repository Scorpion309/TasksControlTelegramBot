import sqlite3 as sq


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
                 'task_title VARCHAR(255) NOT NULL,'
                 'task VARCHAR(255) NOT NULL,'
                 'start_time DATETIME,'
                 'execute_time DATETIME);')

    base.execute('CREATE TABLE IF NOT EXISTS task('
                 'from_user_id INTEGER,'
                 'to_user_id INTEGER,'
                 'task_id INTEGER,'
                 'active BOOLEAN NOT NULL,'
                 'deadline DATETIME,'
                 'FOREIGN KEY(from_user_id) REFERENCES users(user_id),'
                 'FOREIGN KEY(to_user_id) REFERENCES users(user_id),'
                 'FOREIGN KEY(task_id) REFERENCES tasks(id));')
    base.commit()


async def sql_add_task_to_db(state):
    async with state.proxy() as data:
        cur.execute('INSERT INTO tasks (task_title, task, start_time, execute_time)'
                    ' VALUES (?, ?, ?, ?)', (data['task_title'], data['task'], data['start_time'],
                                             data['execute_time']))
        task_id = cur.lastrowid

        if isinstance(data['to_user'], list):
            for user_id in data['to_user']:
                cur.execute('INSERT INTO task (from_user_id, to_user_id, task_id, active, deadline)'
                            ' VALUES (?, ?, ?, ?, ?)', (data['from_user_id'], user_id, task_id, True,
                                                        data['execute_time']))
        else:
            cur.execute('INSERT INTO task (from_user_id, to_user_id, task_id, active,  deadline)'
                        ' VALUES (?, ?, ?, ?, ?)', (data['from_user_id'], data['to_user'], task_id, True,
                                                    data['execute_time']))
        base.commit()


async def sql_add_task_to_user(user_id, task_id, from_user_id, deadline):
    cur.execute('INSERT INTO task (to_user_id, task_id, from_user_id, active, deadline) VALUES (?, ?, ?, ?, ?)',
                (user_id, task_id, from_user_id, True, deadline))
    base.commit()


async def sql_add_empty_task(task_id, from_user_id):
    cur.execute('INSERT INTO task (to_user_id, task_id, from_user_id, active) VALUES (?, ?, ?, ?)',
                (from_user_id, task_id, from_user_id, True))
    base.commit()


async def sql_add_user_to_db(user_id, user_name):
    cur.execute('INSERT OR REPLACE INTO groups (id, group_name) VALUES (1, "All_users")')
    group_id = cur.lastrowid
    cur.execute('INSERT OR REPLACE INTO users (user_id, user_name, group_id, admin)'
                ' VALUES (?, ?, ?, ?)', (user_id, user_name, group_id, False))
    base.commit()


async def sql_add_user_to_group(user_id, group_id):
    cur.execute('UPDATE users SET group_id = ? WHERE user_id = ?', (group_id, user_id))
    base.commit()


async def sql_add_group_to_db(state):
    async with state.proxy() as group:
        cur.execute('INSERT INTO groups (group_name) VALUES (?)', (group['name'],))
        base.commit()


async def sql_add_admins_to_db(admins):
    cur.execute('INSERT OR REPLACE INTO groups (id, group_name) VALUES (2, "Administrator")')
    cur.execute('SELECT user_id FROM users WHERE admin = TRUE')
    admins_in_base = cur.fetchall()
    admins_in_base = [admin_id[0] for admin_id in admins_in_base]
    group_id = cur.lastrowid
    # add admin if not in base
    for admin_id in admins:
        if admin_id not in admins_in_base:
            print('User ', admin_id, 'added to administrator group')
            cur.execute('INSERT OR REPLACE INTO users (user_id, user_name, group_id, admin)'
                        ' VALUES (?, ?, ?, ?)',
                        (admin_id, admins[admin_id]['username'], group_id, admins[admin_id]['admin_status']))
    # del admin from base
    for admin_id_in_base in admins_in_base:
        if admin_id_in_base not in admins:
            print('User ', admin_id_in_base, 'deleted from administrator group')
            cur.execute('UPDATE users SET admin = FALSE, group_id = 1 WHERE user_id = ?', (admin_id_in_base,))
    base.commit()


async def sql_change_group_name(group_id, new_name):
    cur.execute('UPDATE groups SET group_name = ? WHERE id = ?', (new_name, group_id))
    base.commit()


async def sql_change_execute_time_for_task(task_id, execute_time, to_user_id=None):
    if not to_user_id:
        cur.execute('UPDATE task SET deadline = ? WHERE task_id = ?', (execute_time, task_id))
        cur.execute('UPDATE tasks SET execute_time = ? WHERE id = ?', (execute_time, task_id))
    else:
        cur.execute('UPDATE task SET deadline = ? WHERE task_id = ? AND to_user_id = ?', (execute_time, task_id,
                                                                                          to_user_id))
    base.commit()


async def sql_change_task_text(task_id, task_text):
    cur.execute('UPDATE tasks SET task = ? WHERE id = ?', (task_text, task_id))
    base.commit()


async def sql_change_task_activity_to_inactive(task_id):
    cur.execute('UPDATE task SET active = FALSE WHERE task_id = ?', (task_id,))
    base.commit()


async def sql_get_active_tasks(admin_id):
    cur.execute('SELECT to_user_id, user_name, task_title, task, start_time, deadline, task_id  FROM task '
                'LEFT JOIN users '
                'ON users.user_id = task.to_user_id '
                'LEFT JOIN tasks '
                'ON tasks.id = task.task_id '
                'WHERE task.active = TRUE '
                'AND from_user_id = ?;', (admin_id,))
    active_tasks = cur.fetchall()
    base.commit()
    return active_tasks


async def get_task_text(task_id):
    cur.execute('SELECT task_title FROM tasks WHERE id = ?;', (task_id,))
    task = cur.fetchall()
    base.commit()
    return task


async def get_execute_time(task_id):
    cur.execute('SELECT execute_time FROM tasks WHERE id = ?;', (task_id,))
    deadline = cur.fetchall()
    base.commit()
    return deadline


async def sql_get_title_tasks():
    cur.execute('SELECT id, task_title FROM tasks; ')
    tasks = cur.fetchall()
    base.commit()
    return tasks


async def sql_get_task_data(task_id):
    cur.execute('SELECT task_title, task, execute_time FROM tasks WHERE id = ?;', (task_id,))
    task_data = cur.fetchall()
    base.commit()
    return task_data


async def sql_get_user_name(user_id):
    cur.execute('SELECT user_name FROM users WHERE user_id = ?;', (user_id,))
    user_name = cur.fetchall()
    base.commit()
    return user_name


async def sql_get_title_task_by_id(task_id):
    cur.execute('SELECT task_title FROM tasks WHERE id = ?;', (task_id,))
    task_title = cur.fetchall()
    base.commit()
    return task_title


async def sql_get_task_info(task_id, to_user):
    cur.execute('SELECT task_title, task, from_user_id, deadline FROM tasks '
                'LEFT JOIN task '
                'ON tasks.id = task.task_id '
                'WHERE to_user_id = ? '
                'AND task.task_id = ? '
                'GROUP BY task_title;', (to_user, task_id))
    task_info = cur.fetchall()
    base.commit()
    return task_info


async def sql_get_id_active_tasks_from_user(from_user_id):
    cur.execute('SELECT task_id, task_title FROM tasks '
                'LEFT JOIN task '
                'ON tasks.id = task.task_id '
                'WHERE task.active = TRUE '
                'AND from_user_id = ?'
                'GROUP BY task_title;', (from_user_id,))
    active_tasks = cur.fetchall()
    base.commit()
    return active_tasks


async def sql_get_id_active_tasks_to_user(to_user_id):
    cur.execute('SELECT task_id, task_title, task, deadline FROM tasks '
                'LEFT JOIN task '
                'ON tasks.id = task.task_id '
                'WHERE task.active = TRUE '
                'AND to_user_id = ?'
                'GROUP BY task_title;', (to_user_id,))
    active_tasks = cur.fetchall()
    base.commit()
    return active_tasks


async def sql_get_users_which_have_this_task(task_id):
    cur.execute('SELECT user_name, user_id FROM users '
                'LEFT JOIN task '
                'ON task.to_user_id = users.user_id '
                'WHERE task_id = ?;', (task_id,))
    users = cur.fetchall()
    base.commit()
    return users


async def sql_get_groups_from_which_users_have_this_task(task_id):
    cur.execute('SELECT group_name, group_id FROM users '
                'LEFT JOIN task '
                'ON task.to_user_id = users.user_id '
                'LEFT JOIN groups '
                'ON groups.id = users.group_id '
                'WHERE task_id = ?;', (task_id,))
    groups = cur.fetchall()
    base.commit()
    return groups


async def sql_get_user_from_db_without_admins():
    cur.execute('SELECT user_name, user_id FROM users WHERE group_id <> 2;')
    users = cur.fetchall()
    base.commit()
    return users


async def sql_get_users_from_group(group_id):
    cur.execute('SELECT user_name, user_id FROM users WHERE group_id = ?', (group_id,))
    users_in_group = cur.fetchall()
    base.commit()
    return users_in_group


async def sql_get_groups_from_db():
    cur.execute('SELECT group_name, id FROM groups WHERE id NOT IN (1, 2)')
    groups_in_base = cur.fetchall()
    base.commit()
    return groups_in_base


async def sql_del_user_from_group(user_id):
    group_id = 1
    cur.execute('UPDATE users SET group_id = ? WHERE user_id = ?', (group_id, user_id))
    base.commit()


async def sql_del_user_from_db(user_id):
    cur.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    base.commit()


async def sql_del_task_from_db(task_id):
    cur.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    cur.execute('DELETE FROM task WHERE task_id = ?', (task_id,))
    base.commit()


async def sql_del_task_from_user(task_id, user_id):
    cur.execute('DELETE FROM task WHERE task_id = ? AND to_user_id = ?', (task_id, user_id))
    base.commit()


def sql_del_empty_task_if_there_is(task_id, user_id):
    cur.execute('DELETE FROM task WHERE task_id = ? AND to_user_id = ? AND from_user_id = ?',
                (task_id, user_id, user_id))
    base.commit()


async def sql_del_group_from_db(group_id):
    cur.execute('DELETE FROM groups WHERE id = ?', (group_id,))
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

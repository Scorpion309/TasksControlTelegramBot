from aiogram.utils import executor
from create_bot import dp
from handlers import users, admin, other
from data_base import sqlite_db

if __name__ == '__main__':
    async def on_startup(_):
        print('Bot online')
        sqlite_db.sql_start()
        await sqlite_db.sql_bd()


    admin.register_handler_for_admin(dp)
    users.register_handlers_for_users(dp)
    other.register_handlers_for_other(dp)


    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

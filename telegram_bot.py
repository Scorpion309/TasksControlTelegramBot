from aiogram.utils import executor

from create_bot import dp
from data_base import sqlite_db
from handlers import users, admin, other

if __name__ == '__main__':
    async def on_startup(_):
        print('Bot online')
        sqlite_db.sql_start()
        await sqlite_db.sql_bd()


    async def on_shutdown(_):
        print('Bot offline')
        dp.stop_polling()
        # sqlite_db.sql_stop()


    admin.register_handler_for_admin(dp)
    users.register_handlers_for_users(dp)
    other.register_handlers_for_other(dp)

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

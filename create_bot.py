from aiogram import Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher

storage = MemoryStorage()
# Get token from file and create dispatcher
with open('TOKEN.txt', 'r') as token_file:
    token = token_file.readline()
bot = Bot(token=token)
dp = Dispatcher(bot, storage=storage)

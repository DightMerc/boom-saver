import asyncio
import logging
import os
import sys

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode

from bot.api.saver import saver_router
from bot.api.system import system_router
from db import models

dispatcher = Dispatcher()

dispatcher.include_router(system_router)
dispatcher.include_router(saver_router)


async def main() -> None:
    bot = Bot(os.environ.get("TELEGRAM_TOKEN"), parse_mode=ParseMode.HTML)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

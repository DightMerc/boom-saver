from aiogram.types import Message

from bot.application import BaseController


class CommandStartController(BaseController):
    def __init__(self, message: Message):
        super(CommandStartController, self).__init__(message)

    async def _call(self):
        await self.message.answer("Hello!")

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.application.controllers.system import CommandStartController

system_router = Router(name=__name__)


@system_router.message(CommandStart())
async def start_command_handler(message: Message) -> None:
    return await CommandStartController(message=message).call()

from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message, InlineQuery, ChosenInlineResult

from bot.application.controllers.inline_saver import InlineSaverController
from bot.application.controllers.inline_selector import InlineSelectorController
from bot.application.controllers.saver import SaverController

saver_router = Router(name=__name__)


class HttpFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text.strip().startswith("http")


@saver_router.message(HttpFilter())
async def link_message_handler(message: Message) -> None:
    return await SaverController(message=message).call()


@saver_router.inline_query()
async def inline_query_handler(query: InlineQuery) -> None:
    return await InlineSelectorController(query=query).call()


@saver_router.chosen_inline_result()
async def inline_link_query_handler(result: ChosenInlineResult) -> None:
    return await InlineSaverController(result=result).call()

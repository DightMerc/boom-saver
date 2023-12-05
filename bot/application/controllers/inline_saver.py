from aiogram.types import ChosenInlineResult

from bot.application import (
    BaseInlineResultController,
)


class InlineSaverController(BaseInlineResultController):
    def __init__(self, result: ChosenInlineResult):
        super(InlineSaverController, self).__init__(result=result)

    async def _call(self):
        pass

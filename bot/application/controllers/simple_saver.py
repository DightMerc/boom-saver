import os

from aiogram.types import Message

from backends.async_backends import AsyncSaverBackend
from backends.exceptions import (
    ObjectNotFound,
    EntityTooLarge,
    UnsupportedMediaType,
    UnsupportedLinkOrigin,
)
from backends.selector import AsyncBackendSelector
from bot.application import BaseController
from bot.exceptions import BehaviorException


class SimpleSaverController(BaseController):
    def __init__(self, message: Message):
        super(SimpleSaverController, self).__init__(message)

    async def _call(self):
        self.link = self.message.text
        await self._validate_link(link=self.link)
        result = await self._prepare_file(link=self.link)
        await self.message.answer_video(video=result)

    @staticmethod
    async def _prepare_file(link: str) -> str:
        try:
            result = await AsyncSaverBackend(
                backend=await AsyncBackendSelector(
                    link=link, path=os.environ["TEMP_DIR"]
                ).backend
            ).get_link()
            return result
        except ObjectNotFound:
            raise BehaviorException(
                message=dict(en="File not found", ru="Чот я не нашел ничего 🥺")
            )
        except EntityTooLarge:
            raise BehaviorException(
                message=dict(
                    en="Entity too large", ru="Ай... Он слишком большой, семпай 👉👈"
                )
            )
        except UnsupportedMediaType:
            raise BehaviorException(
                message=dict(en="Unsupported media type", ru="Я в картинки не могу 😓")
            )
        except UnsupportedLinkOrigin:
            raise BehaviorException(
                message=dict(
                    en="Unsupported link origin",
                    ru="Чот я не вкурил чо от меня хотят 🤬",
                )
            )

    @staticmethod
    async def _validate_link(link: str) -> None:
        if "http" not in link:
            raise BehaviorException(
                message=dict(en="Wrong link format", ru="Неправильный формат ссылки")
            )

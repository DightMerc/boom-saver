import hashlib
import os

from aiogram.types import (
    FSInputFile,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.utils.chat_action import ChatActionSender

from backends import AbstractBackendResult
from backends.async_backends import AsyncSaverBackend
from backends.exceptions import (
    ObjectNotFound,
    EntityTooLarge,
    UnsupportedMediaType,
    UnsupportedLinkOrigin,
)
from backends.selector import AsyncBackendSelector
from bot.application import BaseInlineController
from bot.exceptions import BehaviorException


class InlineSelectorController(BaseInlineController):
    def __init__(self, query: InlineQuery):
        super(InlineSelectorController, self).__init__(query)

    async def _call(self):
        link = self.query.query
        if not link:
            return
        await self._validate_link(link=link)
        result_id: str = hashlib.md5(link.encode()).hexdigest()
        await self.query.answer(
            [
                InlineQueryResultArticle(
                    id=result_id,
                    title="Test",
                    input_message_content=InputTextMessageContent(message_text=link),
                )
            ],
            cache_time=1,
        )
        # result = await self._prepare_file(link=link)
        # self.logger.info(result.__dict__)
        # fmt = os.path.splitext(result.file)[1].replace(".", "")
        # if fmt == "mp3":
        #     await self._make_audio_response(file=result.file)
        # else:
        #     await self._make_video_response(file=result.file)

    async def _make_audio_response(self, file):
        async with ChatActionSender.upload_voice(
            bot=self.message.bot, chat_id=self.message.chat.id
        ):
            response_file = FSInputFile(path=file)
            await self.message.answer_document(document=response_file)

    async def _make_video_response(self, file):
        async with ChatActionSender.upload_video(
            bot=self.message.bot, chat_id=self.message.chat.id
        ):
            response_file = FSInputFile(path=file)
            await self.message.answer_document(document=response_file)

    @staticmethod
    async def _validate_link(link: str) -> None:
        if "http" not in link:
            raise BehaviorException(
                message=dict(en="Wrong link format", ru="Неправильный формат ссылки")
            )

    @staticmethod
    async def _prepare_file(link: str) -> AbstractBackendResult:
        try:
            result = await AsyncSaverBackend(
                backend=await AsyncBackendSelector(
                    link=link,
                    path=os.environ["TEMP_DIR"],
                ).backend
            ).get()
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

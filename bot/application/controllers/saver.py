import os.path
import uuid
from datetime import datetime
from typing import Dict, Optional

from aiogram.types import Message, FSInputFile, BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender
from hachoir.metadata import extractMetadata
from hachoir.metadata.video import MP4Metadata
from hachoir.parser import createParser
from moviepy.video.io.VideoFileClip import VideoFileClip
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from yandex_music import Track

from backends import AbstractBackendResult
from backends.async_backends import AsyncSaverBackend
from backends.exceptions import (
    ObjectNotFound,
    EntityTooLarge,
    UnsupportedMediaType,
    UnsupportedLinkOrigin,
)
from backends.selector import AsyncBackendSelector
from bot.application import BaseController
from bot.application.models import File
from bot.exceptions import BehaviorException


class SaverController(BaseController):
    def __init__(self, message: Message):
        super(SaverController, self).__init__(message)

    async def _call(self):
        self.link = self.message.text
        await self._validate_link(link=self.link)
        async with ChatActionSender.typing(
            bot=self.message.bot, chat_id=self.message.chat.id
        ):
            message: Message = await self.message.answer(
                dict(en="Search...", ru="Искаю... ")[self.user.language_code],
            )
            file_id = await self._get_file_by_link()
            if file_id:
                await self.message.bot.delete_message(
                    chat_id=self.message.chat.id, message_id=message.message_id
                )
                await self.message.answer(
                    dict(en="Found in database.", ru="Нашов в истории")[
                        self.user.language_code
                    ],
                )
                await self.message.answer_document(
                    document=file_id,
                    caption="captured by @bsaverbot",
                )
            else:
                result = await self._prepare_file(link=self.link)
                await self.message.bot.edit_message_text(
                    text=dict(en="Found.", ru="Нашов.")[self.user.language_code],
                    chat_id=self.message.chat.id,
                    message_id=message.message_id,
                )
                self.logger.debug(result.__dict__)
                fmt = os.path.splitext(result.file)[1].replace(".", "")
                file_info = dict(format=fmt)
                if fmt == "mp3":
                    file_response: Message = await self._make_audio_response(
                        result=result,
                    )
                    json_file = file_response.model_dump()
                    file_info["file_unique_id"] = file_response.audio.file_unique_id
                    file_info["file_id"] = file_response.audio.file_id
                    file_info["file_info"] = json_file["audio"]
                else:
                    file_response: Message = await self._make_video_response(
                        result=result
                    )
                    print(file_response.model_dump())
                    json_file = file_response.model_dump()
                    file_info["file_unique_id"] = file_response.video.file_unique_id
                    file_info["file_id"] = file_response.video.file_id
                    file_info["file_info"] = json_file["video"]

                await self._create_file(file_info=file_info)

                await self.message.bot.delete_message(
                    chat_id=self.message.chat.id, message_id=message.message_id
                )

    async def _make_audio_response(self, result):
        async with ChatActionSender.upload_voice(
            bot=self.message.bot, chat_id=self.message.chat.id
        ):
            response_file = FSInputFile(path=result.file)
            track: Track = result.track
            return await self.message.answer_audio(
                audio=response_file,
                caption="captured by @bsaverbot",
                duration=int(track.duration_ms / 1000),
                performer=(
                    str([artist["name"] for artist in track.artists])
                    .replace("[", "")
                    .replace("]", "")
                    .replace("'", "")
                ),
                title=track.title,
                thumbnail=BufferedInputFile(
                    track.download_cover_bytes(), filename=f"{track.title}-thumb.jpg"
                ),
            )

    async def _make_video_response(self, result):
        async with ChatActionSender.upload_video(
            bot=self.message.bot, chat_id=self.message.chat.id
        ):
            meta: Dict = await self.generate_meta(file=result.file)
            thumbnail: bytes = await self.generate_thumbnail(file=result.file)
            response_file = FSInputFile(path=result.file)
            return await self.message.answer_video(
                video=response_file,
                caption="captured by @bsaverbot",
                duration=meta["duration"],
                width=meta["width"],
                height=meta["height"],
                thumbnail=(
                    BufferedInputFile(
                        thumbnail,
                        filename=f"{str(uuid.uuid4())}-thumb.jpg",
                    )
                ),
            )

    @staticmethod
    async def generate_thumbnail(file: str) -> bytes:
        clip = VideoFileClip(file)
        thumbnail_path = f"{file}-thumbnail.jpg"
        clip.save_frame(thumbnail_path, t=1.00)
        return open(thumbnail_path, "rb").read()

    @staticmethod
    async def _validate_link(link: str) -> None:
        if "http" not in link:
            raise BehaviorException(
                message=dict(en="Wrong link format", ru="Неправильный формат ссылки")
            )

    @staticmethod
    async def generate_meta(file: str):
        file_metadata: MP4Metadata = extractMetadata(createParser(file))
        duration = datetime.strptime(
            str(file_metadata.get("duration")), "%H:%M:%S.%f"
        ).second
        return dict(
            duration=duration,
            width=file_metadata.get("width"),
            height=file_metadata.get("height"),
        )

    @staticmethod
    async def _prepare_file(link: str) -> AbstractBackendResult:
        try:
            result = await AsyncSaverBackend(
                backend=await AsyncBackendSelector(
                    link=link, path=os.environ["TEMP_DIR"]
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

    async def _create_file(self, file_info: Dict):
        async with self.session() as session:
            query = insert(File).values(
                account_id=self.account.id,
                link=self.link,
                file_id=file_info["file_id"],
                file_info=str(file_info),
                created_at=datetime.now(),
            )
            await session.execute(query)
            await session.commit()

    async def _get_file_by_link(self) -> Optional[str]:
        async with self.session() as session:
            session: AsyncSession
            file: File = (
                await session.scalars(select(File).filter(File.link == self.link))
            ).first()
            if file:
                return file.file_id

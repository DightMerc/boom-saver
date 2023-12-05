import os
from typing import Dict, Callable

from pytube import YouTube, Stream
from pytube.exceptions import VideoUnavailable

from backends import AbstractBackendResult, AsyncAbstractBackend
from backends.exceptions import ObjectNotFound, EntityTooLarge


class YoutubeBackendResult(AbstractBackendResult):
    def __init__(
        self, link: str, file: str, title: str, extension: str, file_size: int
    ):
        self.link = link
        self.file = file
        self.title = title
        self.extension = extension
        self.file_size = file_size


class AsyncYoutubeBackend(AsyncAbstractBackend):

    BACKEND_URIS = ["youtube", "yt", "youtu"]

    def __init__(
        self,
        link: str,
        path: str = os.environ["TEMP_DIR"],
        progressive: bool = True,
        extension: str = "mp4",
    ):
        self.link = link
        self.backend = YouTube
        self.progressive = progressive
        self.extension = extension.replace(".", "")
        self.path = path

    async def _get_file(self, stream: Stream) -> Dict:
        title = stream.title
        self.file_path = stream.download(output_path=self.path)
        return dict(file_path=self.file_path, title=title, extension=self.extension)

    async def _find_object(self) -> Stream:
        try:
            return (
                self.backend(self.link)
                .streams.filter(
                    progressive=self.progressive, file_extension=self.extension
                )
                .order_by("resolution")
                .desc()
                .first()
            )
        except VideoUnavailable:
            raise ObjectNotFound

    async def get(self) -> YoutubeBackendResult:
        stream: Stream = await self._find_object()
        await self.validate_file_size(stream=stream)
        downloaded: Dict = await self._get_file(stream=stream)
        return YoutubeBackendResult(
            link=self.link,
            file=downloaded["file_path"],
            title=downloaded.get("title", "unknown"),
            extension=downloaded["extension"],
            file_size=int(stream.filesize_mb),
        )

    async def validate_file_size(self, stream: Stream):
        if int(stream.filesize_mb) > int(os.environ.get("MAX_FILE_SIZE")):
            raise EntityTooLarge
